"""缓存服务

提供Redis缓存操作的统一接口。
"""

import json
import hashlib
import pickle
from typing import Any, Optional, Dict, List, Union
from datetime import datetime, timedelta

import redis.asyncio as redis
from redis.asyncio import Redis

from ..core.config import Config
from ..core.logger import get_logger, LoggerMixin


class CacheService(LoggerMixin):
    """缓存服务类"""
    
    def __init__(self, config: Config):
        """初始化缓存服务
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.redis_client: Optional[Redis] = None
        self._initialized = False
        
        # 缓存键前缀
        self.key_prefix = "modelscope_mcp:"
        
        # 缓存类型配置
        self.cache_config = config.get_cache_config()
    
    async def initialize(self) -> None:
        """初始化Redis连接"""
        if self._initialized:
            return
        
        # 检查是否禁用Redis
        if self.config.redis_host.lower() in ['disabled', 'none', 'false']:
            self.logger.info("Redis已在配置中禁用，跳过连接")
            self.redis_client = None
            self._initialized = True
            return
        
        try:
            self.logger.info(f"正在连接Redis: {self.config.redis_host}:{self.config.redis_port}")
            
            # 创建Redis连接
            self.redis_client = redis.Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                ssl=self.config.redis_ssl,
                decode_responses=False,  # 保持二进制数据
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # 测试连接
            await self.redis_client.ping()
            
            self._initialized = True
            self.logger.info("Redis连接初始化完成")
            
        except Exception as e:
            self.logger.error(f"Redis初始化失败: {e}")
            # 如果Redis不可用，继续运行但禁用缓存
            self.redis_client = None
            self.logger.warning("Redis不可用，缓存功能已禁用")
            self._initialized = True  # 标记为已初始化，避免重复尝试
    
    def _make_key(self, cache_type: str, identifier: str) -> str:
        """生成缓存键
        
        Args:
            cache_type: 缓存类型
            identifier: 标识符
            
        Returns:
            完整的缓存键
        """
        return f"{self.key_prefix}{cache_type}:{identifier}"
    
    def _hash_key(self, data: Union[str, Dict, List]) -> str:
        """生成数据哈希值
        
        Args:
            data: 要哈希的数据
            
        Returns:
            哈希值字符串
        """
        if isinstance(data, (dict, list)):
            data_str = json.dumps(data, sort_keys=True, ensure_ascii=False)
        else:
            data_str = str(data)
        
        return hashlib.md5(data_str.encode('utf-8')).hexdigest()
    
    async def get(self, cache_type: str, key: str) -> Optional[Any]:
        """获取缓存数据
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            缓存的数据或None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(cache_type, key)
            data = await self.redis_client.get(cache_key)
            
            if data is None:
                return None
            
            # 反序列化数据
            try:
                return pickle.loads(data)
            except (pickle.PickleError, EOFError):
                # 如果pickle失败，尝试JSON
                try:
                    return json.loads(data.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    self.logger.warning(f"无法反序列化缓存数据: {cache_key}")
                    return None
                    
        except Exception as e:
            self.logger.error(f"获取缓存失败 {cache_type}:{key}: {e}")
            return None
    
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
            ttl: 生存时间（秒），如果为None则使用默认值
            
        Returns:
            是否设置成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(cache_type, key)
            
            # 序列化数据
            try:
                data = pickle.dumps(value)
            except (pickle.PickleError, TypeError):
                # 如果pickle失败，尝试JSON
                try:
                    data = json.dumps(value, ensure_ascii=False).encode('utf-8')
                except (TypeError, ValueError):
                    self.logger.warning(f"无法序列化缓存数据: {cache_key}")
                    return False
            
            # 确定TTL
            if ttl is None:
                ttl = self.cache_config.get(cache_type, 3600)  # 默认1小时
            
            # 设置缓存
            await self.redis_client.setex(cache_key, ttl, data)
            
            self.logger.debug(f"缓存设置成功: {cache_key} (TTL: {ttl}s)")
            return True
            
        except Exception as e:
            self.logger.error(f"设置缓存失败 {cache_type}:{key}: {e}")
            return False
    
    async def delete(self, cache_type: str, key: str) -> bool:
        """删除缓存数据
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            是否删除成功
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(cache_type, key)
            result = await self.redis_client.delete(cache_key)
            return result > 0
            
        except Exception as e:
            self.logger.error(f"删除缓存失败 {cache_type}:{key}: {e}")
            return False
    
    async def exists(self, cache_type: str, key: str) -> bool:
        """检查缓存是否存在
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            缓存是否存在
        """
        if not self.redis_client:
            return False
        
        try:
            cache_key = self._make_key(cache_type, key)
            return await self.redis_client.exists(cache_key) > 0
            
        except Exception as e:
            self.logger.error(f"检查缓存存在性失败 {cache_type}:{key}: {e}")
            return False
    
    async def get_ttl(self, cache_type: str, key: str) -> Optional[int]:
        """获取缓存剩余生存时间
        
        Args:
            cache_type: 缓存类型
            key: 缓存键
            
        Returns:
            剩余生存时间（秒）或None
        """
        if not self.redis_client:
            return None
        
        try:
            cache_key = self._make_key(cache_type, key)
            ttl = await self.redis_client.ttl(cache_key)
            return ttl if ttl > 0 else None
            
        except Exception as e:
            self.logger.error(f"获取缓存TTL失败 {cache_type}:{key}: {e}")
            return None
    
    async def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存
        
        Args:
            pattern: 匹配模式
            
        Returns:
            清除的缓存数量
        """
        if not self.redis_client:
            return 0
        
        try:
            full_pattern = f"{self.key_prefix}{pattern}"
            keys = await self.redis_client.keys(full_pattern)
            
            if keys:
                deleted = await self.redis_client.delete(*keys)
                self.logger.info(f"清除缓存: {deleted} 个键匹配模式 {pattern}")
                return deleted
            
            return 0
            
        except Exception as e:
            self.logger.error(f"清除缓存模式失败 {pattern}: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        if not self.redis_client:
            return {"status": "disabled"}
        
        try:
            info = await self.redis_client.info()
            
            # 获取我们的键数量
            our_keys = await self.redis_client.keys(f"{self.key_prefix}*")
            
            stats = {
                "status": "active",
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": info.get("db0", {}).get("keys", 0) if "db0" in info else 0,
                "our_keys_count": len(our_keys),
                "cache_config": self.cache_config
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"获取缓存统计失败: {e}")
            return {"status": "error", "error": str(e)}
    
    # 专用缓存方法
    async def cache_dataset_info(self, dataset_name: str, info: Dict[str, Any]) -> bool:
        """缓存数据集信息"""
        return await self.set("dataset_info", dataset_name, info)
    
    async def get_dataset_info(self, dataset_name: str) -> Optional[Dict[str, Any]]:
        """获取缓存的数据集信息"""
        return await self.get("dataset_info", dataset_name)
    
    async def cache_query_result(
        self,
        query_hash: str,
        result: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """缓存查询结果"""
        if ttl is None:
            ttl = self.cache_config.get("query_result", 1800)
        return await self.set("query_result", query_hash, result, ttl)
    
    async def get_query_result(self, query_hash: str) -> Optional[Any]:
        """获取缓存的查询结果"""
        return await self.get("query_result", query_hash)
    
    async def cache_sample_data(
        self,
        dataset_name: str,
        subset: str,
        samples: List[Dict[str, Any]]
    ) -> bool:
        """缓存样本数据"""
        key = f"{dataset_name}:{subset}"
        return await self.set("sample_data", key, samples)
    
    async def get_sample_data(
        self,
        dataset_name: str,
        subset: str
    ) -> Optional[List[Dict[str, Any]]]:
        """获取缓存的样本数据"""
        key = f"{dataset_name}:{subset}"
        return await self.get("sample_data", key)
    
    async def generate_query_hash(self, query_params: Dict[str, Any]) -> str:
        """生成查询参数的哈希值
        
        Args:
            query_params: 查询参数
            
        Returns:
            哈希值字符串
        """
        return self._hash_key(query_params)
    
    async def close(self) -> None:
        """关闭Redis连接"""
        if self.redis_client:
            await self.redis_client.close()
            self.logger.info("Redis连接已关闭")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'redis_client') and self.redis_client:
            try:
                import asyncio
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.redis_client.close())
            except Exception:
                pass