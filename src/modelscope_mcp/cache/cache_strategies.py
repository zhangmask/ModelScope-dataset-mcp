"""缓存策略

定义不同的缓存策略和算法。
"""

import time
import heapq
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class EvictionPolicy(Enum):
    """驱逐策略枚举"""
    LRU = "lru"          # 最近最少使用
    LFU = "lfu"          # 最少使用频率
    FIFO = "fifo"        # 先进先出
    TTL = "ttl"          # 基于生存时间
    RANDOM = "random"    # 随机驱逐


@dataclass
class CacheItem:
    """缓存项"""
    key: str
    value: Any
    created_at: float
    accessed_at: float
    access_count: int
    size_bytes: int
    ttl: Optional[float] = None
    
    def is_expired(self) -> bool:
        """检查是否过期"""
        if self.ttl is None:
            return False
        return time.time() - self.created_at > self.ttl
    
    def update_access(self):
        """更新访问信息"""
        self.accessed_at = time.time()
        self.access_count += 1


class CacheStrategy(ABC):
    """缓存策略抽象基类"""
    
    def __init__(self, max_size: int, max_entries: int):
        """初始化策略
        
        Args:
            max_size: 最大缓存大小（字节）
            max_entries: 最大缓存条目数
        """
        self.max_size = max_size
        self.max_entries = max_entries
        self.current_size = 0
        self.items: Dict[str, CacheItem] = {}
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            缓存值或None
        """
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 生存时间（秒）
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def remove(self, key: str) -> bool:
        """移除缓存项
        
        Args:
            key: 缓存键
            
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def evict(self) -> List[str]:
        """驱逐缓存项
        
        Returns:
            被驱逐的键列表
        """
        pass
    
    def clear(self):
        """清空缓存"""
        self.items.clear()
        self.current_size = 0
    
    def size(self) -> int:
        """获取当前缓存大小"""
        return len(self.items)
    
    def get_size_bytes(self) -> int:
        """获取当前缓存字节大小"""
        return self.current_size
    
    def cleanup_expired(self) -> List[str]:
        """清理过期项
        
        Returns:
            被清理的键列表
        """
        expired_keys = []
        
        for key, item in list(self.items.items()):
            if item.is_expired():
                expired_keys.append(key)
                self.current_size -= item.size_bytes
                del self.items[key]
        
        return expired_keys
    
    def _estimate_size(self, value: Any) -> int:
        """估算值的大小"""
        try:
            import sys
            return sys.getsizeof(value)
        except Exception:
            if isinstance(value, str):
                return len(value.encode('utf-8'))
            elif isinstance(value, (list, tuple)):
                return sum(self._estimate_size(item) for item in value)
            elif isinstance(value, dict):
                return sum(self._estimate_size(k) + self._estimate_size(v) for k, v in value.items())
            else:
                return 1024  # 默认1KB


class LRUStrategy(CacheStrategy):
    """LRU（最近最少使用）缓存策略"""
    
    def __init__(self, max_size: int, max_entries: int):
        super().__init__(max_size, max_entries)
        self.access_order: List[str] = []  # 访问顺序列表
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self.items:
            return None
        
        item = self.items[key]
        
        # 检查是否过期
        if item.is_expired():
            self.remove(key)
            return None
        
        # 更新访问信息
        item.update_access()
        
        # 更新访问顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return item.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项"""
        size_bytes = self._estimate_size(value)
        
        # 检查是否需要驱逐
        while (len(self.items) >= self.max_entries or 
               self.current_size + size_bytes > self.max_size):
            evicted = self.evict()
            if not evicted:
                break
        
        # 如果键已存在，更新
        if key in self.items:
            old_item = self.items[key]
            self.current_size -= old_item.size_bytes
        
        # 创建新项
        item = CacheItem(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=ttl
        )
        
        self.items[key] = item
        self.current_size += size_bytes
        
        # 更新访问顺序
        if key in self.access_order:
            self.access_order.remove(key)
        self.access_order.append(key)
        
        return True
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self.items:
            return False
        
        item = self.items[key]
        self.current_size -= item.size_bytes
        del self.items[key]
        
        if key in self.access_order:
            self.access_order.remove(key)
        
        return True
    
    def evict(self) -> List[str]:
        """驱逐最近最少使用的项"""
        if not self.access_order:
            return []
        
        # 驱逐最旧的项
        key = self.access_order[0]
        self.remove(key)
        return [key]


class LFUStrategy(CacheStrategy):
    """LFU（最少使用频率）缓存策略"""
    
    def __init__(self, max_size: int, max_entries: int):
        super().__init__(max_size, max_entries)
        self.frequency_heap: List[Tuple[int, float, str]] = []  # (频率, 时间戳, 键)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self.items:
            return None
        
        item = self.items[key]
        
        # 检查是否过期
        if item.is_expired():
            self.remove(key)
            return None
        
        # 更新访问信息
        item.update_access()
        
        # 更新频率堆
        heapq.heappush(self.frequency_heap, (item.access_count, time.time(), key))
        
        return item.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项"""
        size_bytes = self._estimate_size(value)
        
        # 检查是否需要驱逐
        while (len(self.items) >= self.max_entries or 
               self.current_size + size_bytes > self.max_size):
            evicted = self.evict()
            if not evicted:
                break
        
        # 如果键已存在，更新
        if key in self.items:
            old_item = self.items[key]
            self.current_size -= old_item.size_bytes
        
        # 创建新项
        item = CacheItem(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=ttl
        )
        
        self.items[key] = item
        self.current_size += size_bytes
        
        # 添加到频率堆
        heapq.heappush(self.frequency_heap, (1, time.time(), key))
        
        return True
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self.items:
            return False
        
        item = self.items[key]
        self.current_size -= item.size_bytes
        del self.items[key]
        
        return True
    
    def evict(self) -> List[str]:
        """驱逐使用频率最低的项"""
        # 清理堆中无效的条目
        while self.frequency_heap:
            frequency, timestamp, key = heapq.heappop(self.frequency_heap)
            
            if key in self.items:
                # 找到有效的最低频率项
                self.remove(key)
                return [key]
        
        return []


class TTLStrategy(CacheStrategy):
    """TTL（生存时间）缓存策略"""
    
    def __init__(self, max_size: int, max_entries: int, default_ttl: float = 3600):
        super().__init__(max_size, max_entries)
        self.default_ttl = default_ttl
        self.expiry_heap: List[Tuple[float, str]] = []  # (过期时间, 键)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        # 先清理过期项
        self._cleanup_expired()
        
        if key not in self.items:
            return None
        
        item = self.items[key]
        
        # 检查是否过期
        if item.is_expired():
            self.remove(key)
            return None
        
        # 更新访问信息
        item.update_access()
        
        return item.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项"""
        # 先清理过期项
        self._cleanup_expired()
        
        size_bytes = self._estimate_size(value)
        effective_ttl = ttl or self.default_ttl
        
        # 检查是否需要驱逐
        while (len(self.items) >= self.max_entries or 
               self.current_size + size_bytes > self.max_size):
            evicted = self.evict()
            if not evicted:
                break
        
        # 如果键已存在，更新
        if key in self.items:
            old_item = self.items[key]
            self.current_size -= old_item.size_bytes
        
        # 创建新项
        item = CacheItem(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=effective_ttl
        )
        
        self.items[key] = item
        self.current_size += size_bytes
        
        # 添加到过期堆
        expiry_time = time.time() + effective_ttl
        heapq.heappush(self.expiry_heap, (expiry_time, key))
        
        return True
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self.items:
            return False
        
        item = self.items[key]
        self.current_size -= item.size_bytes
        del self.items[key]
        
        return True
    
    def evict(self) -> List[str]:
        """驱逐最早过期的项"""
        # 先尝试清理过期项
        expired = self._cleanup_expired()
        if expired:
            return expired
        
        # 如果没有过期项，驱逐最早过期的项
        while self.expiry_heap:
            expiry_time, key = heapq.heappop(self.expiry_heap)
            
            if key in self.items:
                self.remove(key)
                return [key]
        
        return []
    
    def _cleanup_expired(self) -> List[str]:
        """清理过期项"""
        current_time = time.time()
        expired_keys = []
        
        # 从堆中移除过期项
        while self.expiry_heap and self.expiry_heap[0][0] <= current_time:
            expiry_time, key = heapq.heappop(self.expiry_heap)
            
            if key in self.items and self.items[key].is_expired():
                expired_keys.append(key)
                self.remove(key)
        
        return expired_keys


class FIFOStrategy(CacheStrategy):
    """FIFO（先进先出）缓存策略"""
    
    def __init__(self, max_size: int, max_entries: int):
        super().__init__(max_size, max_entries)
        self.insertion_order: List[str] = []  # 插入顺序列表
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self.items:
            return None
        
        item = self.items[key]
        
        # 检查是否过期
        if item.is_expired():
            self.remove(key)
            return None
        
        # 更新访问信息（但不改变插入顺序）
        item.update_access()
        
        return item.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项"""
        size_bytes = self._estimate_size(value)
        
        # 检查是否需要驱逐
        while (len(self.items) >= self.max_entries or 
               self.current_size + size_bytes > self.max_size):
            evicted = self.evict()
            if not evicted:
                break
        
        # 如果键已存在，更新但不改变顺序
        if key in self.items:
            old_item = self.items[key]
            self.current_size -= old_item.size_bytes
        else:
            # 新键，添加到插入顺序
            self.insertion_order.append(key)
        
        # 创建新项
        item = CacheItem(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=ttl
        )
        
        self.items[key] = item
        self.current_size += size_bytes
        
        return True
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self.items:
            return False
        
        item = self.items[key]
        self.current_size -= item.size_bytes
        del self.items[key]
        
        if key in self.insertion_order:
            self.insertion_order.remove(key)
        
        return True
    
    def evict(self) -> List[str]:
        """驱逐最早插入的项"""
        if not self.insertion_order:
            return []
        
        # 驱逐最早插入的项
        key = self.insertion_order[0]
        self.remove(key)
        return [key]


class RandomStrategy(CacheStrategy):
    """随机驱逐缓存策略"""
    
    def __init__(self, max_size: int, max_entries: int):
        super().__init__(max_size, max_entries)
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存项"""
        if key not in self.items:
            return None
        
        item = self.items[key]
        
        # 检查是否过期
        if item.is_expired():
            self.remove(key)
            return None
        
        # 更新访问信息
        item.update_access()
        
        return item.value
    
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """放入缓存项"""
        size_bytes = self._estimate_size(value)
        
        # 检查是否需要驱逐
        while (len(self.items) >= self.max_entries or 
               self.current_size + size_bytes > self.max_size):
            evicted = self.evict()
            if not evicted:
                break
        
        # 如果键已存在，更新
        if key in self.items:
            old_item = self.items[key]
            self.current_size -= old_item.size_bytes
        
        # 创建新项
        item = CacheItem(
            key=key,
            value=value,
            created_at=time.time(),
            accessed_at=time.time(),
            access_count=1,
            size_bytes=size_bytes,
            ttl=ttl
        )
        
        self.items[key] = item
        self.current_size += size_bytes
        
        return True
    
    def remove(self, key: str) -> bool:
        """移除缓存项"""
        if key not in self.items:
            return False
        
        item = self.items[key]
        self.current_size -= item.size_bytes
        del self.items[key]
        
        return True
    
    def evict(self) -> List[str]:
        """随机驱逐一个项"""
        if not self.items:
            return []
        
        import random
        key = random.choice(list(self.items.keys()))
        self.remove(key)
        return [key]


def create_strategy(
    policy: EvictionPolicy,
    max_size: int,
    max_entries: int,
    **kwargs
) -> CacheStrategy:
    """创建缓存策略
    
    Args:
        policy: 驱逐策略
        max_size: 最大缓存大小（字节）
        max_entries: 最大缓存条目数
        **kwargs: 策略特定参数
        
    Returns:
        缓存策略实例
    """
    if policy == EvictionPolicy.LRU:
        return LRUStrategy(max_size, max_entries)
    elif policy == EvictionPolicy.LFU:
        return LFUStrategy(max_size, max_entries)
    elif policy == EvictionPolicy.TTL:
        default_ttl = kwargs.get('default_ttl', 3600)
        return TTLStrategy(max_size, max_entries, default_ttl)
    elif policy == EvictionPolicy.FIFO:
        return FIFOStrategy(max_size, max_entries)
    elif policy == EvictionPolicy.RANDOM:
        return RandomStrategy(max_size, max_entries)
    else:
        raise ValueError(f"不支持的驱逐策略: {policy}")