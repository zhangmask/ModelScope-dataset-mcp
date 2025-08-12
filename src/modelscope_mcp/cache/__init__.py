"""缓存模块

提供高级缓存管理功能。
"""

from .cache_manager import CacheManager
from .cache_strategies import CacheStrategy, LRUStrategy, TTLStrategy
from .cache_decorators import cached, cache_result, invalidate_cache

__all__ = [
    "CacheManager",
    "CacheStrategy",
    "LRUStrategy",
    "TTLStrategy",
    "cached",
    "cache_result",
    "invalidate_cache"
]