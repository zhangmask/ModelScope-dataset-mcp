"""缓存管理器

提供高级缓存管理功能，包括缓存策略、批量操作、统计信息等。
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Union, Callable, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum

from ..services.cache import CacheService
from ..core.logger import LoggerMixin
from ..core.config import Config


class CacheLevel(Enum):
    """缓存级别枚举"""
    L1_MEMORY = "l1_memory"  # 内存缓存
    L2_REDIS = "l2_redis"    # Redis缓存
    L3_DISK = "l3_disk"      # 磁盘缓存


@dataclass
class CacheEntry:
    """缓存条目"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int
    ttl: Optional[int]
    size_bytes: int
    metadata: Dict[str, Any]
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """更新访问信息"""
        self.accessed_at = time.time()
        self.access_count += 1


@dataclass
class CacheStats:
    """缓存统计信息"""
    total_entries: int
    total_size_bytes: int
    hit_count: int
    miss_count: int
    eviction_count: int
    memory_entries: int
    redis_entries: int
    disk_entries: int
    hit_rate: float
    average_access_time_ms: float
    
    @classmethod
    def empty(cls) -> 'CacheStats':
        """创建空的统计信息"""
        return cls(
            total_entries=0,
            total_size_bytes=0,
            hit_count=0,
            miss_count=0,
            eviction_count=0,
            memory_entries=0,
            redis_entries=0,
            disk_entries=0,
            hit_rate=0.0,
            average_access_time_ms=0.0
        )


class CacheManager(LoggerMixin):
    """缓存管理器
    
    提供多级缓存、缓存策略、批量操作等高级功能。
    """
    
    def __init__(self, config: Config, cache_service: CacheService):
        """初始化缓存管理器
        
        Args:
            config: 配置对象
            cache_service: 缓存服务
        """
        self.config = config
        self.cache_service = cache_service
        
        # L1内存缓存
        self._memory_cache: Dict[str, CacheEntry] = {}
        self._memory_max_size = config.cache.memory_max_size
        self._memory_max_entries = config.cache.memory_max_entries
        
        # 统计信息
        self._stats = CacheStats.empty()
        self._access_times: List[float] = []
        
        # 缓存策略配置
        self._cache_strategies = {
            "dataset_info": {"ttl": 3600, "level": CacheLevel.L2_REDIS},
            "dataset_list": {"ttl": 1800, "level": CacheLevel.L1_MEMORY},
            "dataset_samples": {"ttl": 7200, "level": CacheLevel.L2_REDIS},
            "query_results": {"ttl": 900, "level": CacheLevel.L1_MEMORY},
            "search_results": {"ttl": 600, "level": CacheLevel.L1_MEMORY}
        }
        
        self.logger.info("缓存管理器初始化完成")
    
    async def get(
        self,
        cache_type: str,
        key: str,
        default: Any = None
    ) -> Any:
        """获取缓存数据
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            default: 默认值
            
        Returns:
            缓存的数据或默认值
        """
        start_time = time.time()
        
        try:
            # 生成完整键
            full_key = f"{cache_type}:{key}"
            
            # 获取缓存策略
            strategy = self._cache_strategies.get(cache_type, {
                "ttl": 3600,
                "level": CacheLevel.L2_REDIS
            })
            
            # 尝试从L1内存缓存获取
            if strategy["level"] in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
                memory_result = await self._get_from_memory(full_key)
                if memory_result is not None:
                    self._record_hit(time.time() - start_time)
                    return memory_result
            
            # 尝试从L2 Redis缓存获取
            if strategy["level"] == CacheLevel.L2_REDIS:
                redis_result = await self._get_from_redis(cache_type, key)
                if redis_result is not None:
                    # 回填到内存缓存
                    await self._set_to_memory(full_key, redis_result, strategy["ttl"])
                    self._record_hit(time.time() - start_time)
                    return redis_result
            
            # 缓存未命中
            self._record_miss(time.time() - start_time)
            return default
            
        except Exception as e:
            self.logger.error(f"获取缓存失败: {cache_type}:{key}, {e}")
            self._record_miss(time.time() - start_time)
            return default
    
    async def set(
        self,
        cache_type: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置缓存数据
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            value: 要缓存的数据
            ttl: 生存时间（秒）
            
        Returns:
            是否设置成功
        """
        try:
            # 生成完整键
            full_key = f"{cache_type}:{key}"
            
            # 获取缓存策略
            strategy = self._cache_strategies.get(cache_type, {
                "ttl": 3600,
                "level": CacheLevel.L2_REDIS
            })
            
            # 使用策略中的TTL或传入的TTL
            effective_ttl = ttl or strategy["ttl"]
            
            success = True
            
            # 根据策略设置到不同级别的缓存
            if strategy["level"] in [CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS]:
                memory_success = await self._set_to_memory(full_key, value, effective_ttl)
                success = success and memory_success
            
            if strategy["level"] == CacheLevel.L2_REDIS:
                redis_success = await self._set_to_redis(cache_type, key, value, effective_ttl)
                success = success and redis_success
            
            return success
            
        except Exception as e:
            self.logger.error(f"设置缓存失败: {cache_type}:{key}, {e}")
            return False
    
    async def delete(self, cache_type: str, key: str) -> bool:
        """删除缓存数据
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        try:
            full_key = f"{cache_type}:{key}"
            
            # 从内存缓存删除
            memory_success = await self._delete_from_memory(full_key)
            
            # 从Redis缓存删除
            redis_success = await self._delete_from_redis(cache_type, key)
            
            return memory_success or redis_success
            
        except Exception as e:
            self.logger.error(f"删除缓存失败: {cache_type}:{key}, {e}")
            return False
    
    async def clear(self, cache_type: Optional[str] = None) -> bool:
        """清除缓存
        
        Args:
            cache_type: 缓存类型，如果为None则清除所有缓存
            
        Returns:
            是否清除成功
        """
        try:
            if cache_type:
                # 清除特定类型的缓存
                keys_to_remove = [k for k in self._memory_cache.keys() if k.startswith(f"{cache_type}:")]
                for key in keys_to_remove:
                    del self._memory_cache[key]
                
                # 清除Redis中的缓存（这里需要实现模式匹配删除）
                await self._clear_redis_by_pattern(f"{cache_type}:*")
            else:
                # 清除所有缓存
                self._memory_cache.clear()
                await self._clear_all_redis()
            
            self.logger.info(f"缓存清除完成: {cache_type or 'all'}")
            return True
            
        except Exception as e:
            self.logger.error(f"清除缓存失败: {e}")
            return False
    
    async def get_multi(
        self,
        cache_type: str,
        keys: List[str]
    ) -> Dict[str, Any]:
        """批量获取缓存数据
        
        Args:
            cache_type: 缓存类型
            keys: 缓存键列表
            
        Returns:
            键值对字典
        """
        results = {}
        
        # 并行获取
        tasks = [self.get(cache_type, key) for key in keys]
        values = await asyncio.gather(*tasks, return_exceptions=True)
        
        for key, value in zip(keys, values):
            if not isinstance(value, Exception) and value is not None:
                results[key] = value
        
        return results
    
    async def set_multi(
        self,
        cache_type: str,
        data: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> Dict[str, bool]:
        """批量设置缓存数据
        
        Args:
            cache_type: 缓存类型
            data: 键值对数据
            ttl: 生存时间（秒）
            
        Returns:
            设置结果字典
        """
        results = {}
        
        # 并行设置
        tasks = [self.set(cache_type, key, value, ttl) for key, value in data.items()]
        success_list = await asyncio.gather(*tasks, return_exceptions=True)
        
        for key, success in zip(data.keys(), success_list):
            results[key] = success if not isinstance(success, Exception) else False
        
        return results
    
    async def exists(self, cache_type: str, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            是否存在
        """
        result = await self.get(cache_type, key)
        return result is not None
    
    async def get_ttl(self, cache_type: str, key: str) -> Optional[int]:
        """获取缓存剩余生存时间
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            剩余生存时间（秒），如果不存在返回None
        """
        full_key = f"{cache_type}:{key}"
        
        # 检查内存缓存
        if full_key in self._memory_cache:
            entry = self._memory_cache[full_key]
            if entry.ttl is None:
                return None
            remaining = entry.ttl - (time.time() - entry.created_at)
            return max(0, int(remaining))
        
        # 检查Redis缓存
        try:
            if self.cache_service.redis_client:
                cache_key = self.cache_service._make_key(cache_type, key)
                ttl = await self.cache_service.redis_client.ttl(cache_key)
                return ttl if ttl > 0 else None
        except Exception as e:
            self.logger.error(f"获取TTL失败: {e}")
        
        return None
    
    def get_stats(self) -> CacheStats:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        # 更新统计信息
        self._stats.total_entries = len(self._memory_cache)
        self._stats.memory_entries = len(self._memory_cache)
        self._stats.total_size_bytes = sum(
            entry.size_bytes for entry in self._memory_cache.values()
        )
        
        # 计算命中率
        total_requests = self._stats.hit_count + self._stats.miss_count
        if total_requests > 0:
            self._stats.hit_rate = self._stats.hit_count / total_requests
        
        # 计算平均访问时间
        if self._access_times:
            self._stats.average_access_time_ms = sum(self._access_times) / len(self._access_times) * 1000
        
        return self._stats
    
    async def cleanup_expired(self) -> int:
        """清理过期的缓存条目
        
        Returns:
            清理的条目数量
        """
        expired_keys = []
        
        for key, entry in self._memory_cache.items():
            if entry.is_expired():
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._memory_cache[key]
            self._stats.eviction_count += 1
        
        if expired_keys:
            self.logger.debug(f"清理了{len(expired_keys)}个过期缓存条目")
        
        return len(expired_keys)
    
    async def _get_from_memory(self, key: str) -> Optional[Any]:
        """从内存缓存获取数据"""
        if key not in self._memory_cache:
            return None
        
        entry = self._memory_cache[key]
        
        # 检查是否过期
        if entry.is_expired():
            del self._memory_cache[key]
            self._stats.eviction_count += 1
            return None
        
        # 更新访问信息
        entry.update_access()
        return entry.value
    
    async def _set_to_memory(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置到内存缓存"""
        try:
            # 检查内存限制
            await self._ensure_memory_capacity()
            
            # 计算数据大小
            size_bytes = self._estimate_size(value)
            
            # 创建缓存条目
            entry = CacheEntry(
                key=key,
                value=value,
                created_at=time.time(),
                accessed_at=time.time(),
                access_count=1,
                ttl=ttl,
                size_bytes=size_bytes,
                metadata={}
            )
            
            self._memory_cache[key] = entry
            return True
            
        except Exception as e:
            self.logger.error(f"设置内存缓存失败: {e}")
            return False
    
    async def _get_from_redis(self, cache_type: str, key: str) -> Optional[Any]:
        """从Redis缓存获取数据"""
        return await self.cache_service.get(cache_type, key)
    
    async def _set_to_redis(
        self,
        cache_type: str,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """设置到Redis缓存"""
        return await self.cache_service.set(cache_type, key, value, ttl)
    
    async def _delete_from_memory(self, key: str) -> bool:
        """从内存缓存删除"""
        if key in self._memory_cache:
            del self._memory_cache[key]
            return True
        return False
    
    async def _delete_from_redis(self, cache_type: str, key: str) -> bool:
        """从Redis缓存删除"""
        return await self.cache_service.delete(cache_type, key)
    
    async def _clear_redis_by_pattern(self, pattern: str) -> bool:
        """按模式清除Redis缓存"""
        try:
            if self.cache_service.redis_client:
                # 这里需要实现模式匹配删除
                # Redis的SCAN命令可以用来实现
                pass
            return True
        except Exception as e:
            self.logger.error(f"按模式清除Redis缓存失败: {e}")
            return False
    
    async def _clear_all_redis(self) -> bool:
        """清除所有Redis缓存"""
        try:
            if self.cache_service.redis_client:
                await self.cache_service.redis_client.flushdb()
            return True
        except Exception as e:
            self.logger.error(f"清除所有Redis缓存失败: {e}")
            return False
    
    async def _ensure_memory_capacity(self):
        """确保内存缓存容量"""
        # 检查条目数量限制
        if len(self._memory_cache) >= self._memory_max_entries:
            await self._evict_memory_entries()
        
        # 检查内存大小限制
        total_size = sum(entry.size_bytes for entry in self._memory_cache.values())
        if total_size >= self._memory_max_size:
            await self._evict_memory_entries()
    
    async def _evict_memory_entries(self):
        """驱逐内存缓存条目（LRU策略）"""
        if not self._memory_cache:
            return
        
        # 按最后访问时间排序
        sorted_entries = sorted(
            self._memory_cache.items(),
            key=lambda x: x[1].accessed_at
        )
        
        # 删除最旧的25%条目
        evict_count = max(1, len(sorted_entries) // 4)
        
        for i in range(evict_count):
            key, _ = sorted_entries[i]
            del self._memory_cache[key]
            self._stats.eviction_count += 1
        
        self.logger.debug(f"驱逐了{evict_count}个内存缓存条目")
    
    def _estimate_size(self, value: Any) -> int:
        """估算数据大小"""
        try:
            import sys
            return sys.getsizeof(value)
        except Exception:
            # 简单估算
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in value.items())
            else:
                return 1024  # 默认1KB
    
    def _record_hit(self, access_time: float):
        """记录缓存命中"""
        self._stats.hit_count += 1
        self._access_times.append(access_time)
        
        # 保持访问时间列表大小
        if len(self._access_times) > 1000:
            self._access_times = self._access_times[-500:]
    
    def _record_miss(self, access_time: float):
        """记录缓存未命中"""
        self._stats.miss_count += 1
        self._access_times.append(access_time)
        
        # 保持访问时间列表大小
        if len(self._access_times) > 1000:
            self._access_times = self._access_times[-500:]