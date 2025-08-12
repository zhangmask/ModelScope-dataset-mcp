"""缓存装饰器

提供方便的缓存装饰器功能。
"""

import time
import hashlib
import functools
from typing import Any, Callable, Optional, Union, Dict, List
from ..services.cache import CacheService
from .cache_manager import CacheManager


# 全局缓存管理器实例
_cache_manager: Optional[CacheManager] = None
_cache_service: Optional[CacheService] = None


def init_cache(cache_manager: CacheManager = None, cache_service: CacheService = None):
    """初始化全局缓存
    
    Args:
        cache_manager: 缓存管理器实例
        cache_service: 缓存服务实例
    """
    global _cache_manager, _cache_service
    _cache_manager = cache_manager
    _cache_service = cache_service


def get_cache_manager() -> Optional[CacheManager]:
    """获取全局缓存管理器"""
    return _cache_manager


def get_cache_service() -> Optional[CacheService]:
    """获取全局缓存服务"""
    return _cache_service


def _generate_cache_key(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: str = "",
    key_func: Optional[Callable] = None
) -> str:
    """生成缓存键
    
    Args:
        func: 函数对象
        args: 位置参数
        kwargs: 关键字参数
        prefix: 键前缀
        key_func: 自定义键生成函数
        
    Returns:
        缓存键
    """
    if key_func:
        return key_func(*args, **kwargs)
    
    # 构建基础键
    func_name = f"{func.__module__}.{func.__qualname__}"
    
    # 序列化参数
    try:
        import json
        args_str = json.dumps(args, sort_keys=True, default=str)
        kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
    except Exception:
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
    
    # 生成哈希
    content = f"{func_name}:{args_str}:{kwargs_str}"
    hash_obj = hashlib.md5(content.encode('utf-8'))
    hash_key = hash_obj.hexdigest()[:16]
    
    # 添加前缀
    if prefix:
        return f"{prefix}:{hash_key}"
    else:
        return f"func:{hash_key}"


def cached(
    ttl: Optional[float] = None,
    prefix: str = "",
    key_func: Optional[Callable] = None,
    use_memory: bool = True,
    use_redis: bool = True,
    ignore_errors: bool = True
):
    """缓存装饰器
    
    Args:
        ttl: 缓存生存时间（秒）
        prefix: 缓存键前缀
        key_func: 自定义键生成函数
        use_memory: 是否使用内存缓存
        use_redis: 是否使用Redis缓存
        ignore_errors: 是否忽略缓存错误
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 生成缓存键
            cache_key = _generate_cache_key(func, args, kwargs, prefix, key_func)
            
            # 尝试从缓存获取
            try:
                if _cache_manager:
                    # 使用缓存管理器
                    cached_result = _cache_manager.get(
                        cache_key,
                        use_memory=use_memory,
                        use_redis=use_redis
                    )
                    if cached_result is not None:
                        return cached_result
                elif _cache_service and use_redis:
                    # 使用缓存服务
                    cached_result = _cache_service.get(cache_key)
                    if cached_result is not None:
                        return cached_result
            except Exception as e:
                if not ignore_errors:
                    raise
                # 忽略缓存错误，继续执行函数
                pass
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            try:
                if _cache_manager:
                    _cache_manager.set(
                        cache_key,
                        result,
                        ttl=ttl,
                        use_memory=use_memory,
                        use_redis=use_redis
                    )
                elif _cache_service and use_redis:
                    _cache_service.set(cache_key, result, ttl=ttl)
            except Exception as e:
                if not ignore_errors:
                    raise
                # 忽略缓存错误
                pass
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_key = lambda *args, **kwargs: _generate_cache_key(
            func, args, kwargs, prefix, key_func
        )
        wrapper.invalidate = lambda *args, **kwargs: invalidate_cache(
            _generate_cache_key(func, args, kwargs, prefix, key_func)
        )
        wrapper.refresh = lambda *args, **kwargs: refresh_cache(
            func, args, kwargs, prefix, key_func, ttl, use_memory, use_redis
        )
        
        return wrapper
    
    return decorator


def cache_result(
    key: str,
    ttl: Optional[float] = None,
    use_memory: bool = True,
    use_redis: bool = True,
    ignore_errors: bool = True
):
    """缓存结果装饰器（使用固定键）
    
    Args:
        key: 固定缓存键
        ttl: 缓存生存时间（秒）
        use_memory: 是否使用内存缓存
        use_redis: 是否使用Redis缓存
        ignore_errors: 是否忽略缓存错误
        
    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 尝试从缓存获取
            try:
                if _cache_manager:
                    cached_result = _cache_manager.get(
                        key,
                        use_memory=use_memory,
                        use_redis=use_redis
                    )
                    if cached_result is not None:
                        return cached_result
                elif _cache_service and use_redis:
                    cached_result = _cache_service.get(key)
                    if cached_result is not None:
                        return cached_result
            except Exception as e:
                if not ignore_errors:
                    raise
                pass
            
            # 执行原函数
            result = func(*args, **kwargs)
            
            # 缓存结果
            try:
                if _cache_manager:
                    _cache_manager.set(
                        key,
                        result,
                        ttl=ttl,
                        use_memory=use_memory,
                        use_redis=use_redis
                    )
                elif _cache_service and use_redis:
                    _cache_service.set(key, result, ttl=ttl)
            except Exception as e:
                if not ignore_errors:
                    raise
                pass
            
            return result
        
        # 添加缓存控制方法
        wrapper.cache_key = key
        wrapper.invalidate = lambda: invalidate_cache(key)
        wrapper.refresh = lambda *args, **kwargs: refresh_cache_fixed(
            func, key, args, kwargs, ttl, use_memory, use_redis
        )
        
        return wrapper
    
    return decorator


def invalidate_cache(
    key: Union[str, List[str]],
    use_memory: bool = True,
    use_redis: bool = True
) -> bool:
    """使缓存失效
    
    Args:
        key: 缓存键或键列表
        use_memory: 是否清除内存缓存
        use_redis: 是否清除Redis缓存
        
    Returns:
        是否成功
    """
    try:
        if isinstance(key, str):
            keys = [key]
        else:
            keys = key
        
        success = True
        
        for cache_key in keys:
            if _cache_manager:
                result = _cache_manager.delete(
                    cache_key,
                    use_memory=use_memory,
                    use_redis=use_redis
                )
                success = success and result
            elif _cache_service and use_redis:
                result = _cache_service.delete(cache_key)
                success = success and result
        
        return success
    except Exception:
        return False


def refresh_cache(
    func: Callable,
    args: tuple,
    kwargs: dict,
    prefix: str = "",
    key_func: Optional[Callable] = None,
    ttl: Optional[float] = None,
    use_memory: bool = True,
    use_redis: bool = True
) -> Any:
    """刷新缓存
    
    Args:
        func: 函数对象
        args: 位置参数
        kwargs: 关键字参数
        prefix: 键前缀
        key_func: 自定义键生成函数
        ttl: 缓存生存时间
        use_memory: 是否使用内存缓存
        use_redis: 是否使用Redis缓存
        
    Returns:
        函数执行结果
    """
    # 生成缓存键
    cache_key = _generate_cache_key(func, args, kwargs, prefix, key_func)
    
    # 先删除旧缓存
    invalidate_cache(cache_key, use_memory, use_redis)
    
    # 执行函数获取新结果
    result = func(*args, **kwargs)
    
    # 缓存新结果
    try:
        if _cache_manager:
            _cache_manager.set(
                cache_key,
                result,
                ttl=ttl,
                use_memory=use_memory,
                use_redis=use_redis
            )
        elif _cache_service and use_redis:
            _cache_service.set(cache_key, result, ttl=ttl)
    except Exception:
        pass
    
    return result


def refresh_cache_fixed(
    func: Callable,
    key: str,
    args: tuple,
    kwargs: dict,
    ttl: Optional[float] = None,
    use_memory: bool = True,
    use_redis: bool = True
) -> Any:
    """刷新固定键缓存
    
    Args:
        func: 函数对象
        key: 固定缓存键
        args: 位置参数
        kwargs: 关键字参数
        ttl: 缓存生存时间
        use_memory: 是否使用内存缓存
        use_redis: 是否使用Redis缓存
        
    Returns:
        函数执行结果
    """
    # 先删除旧缓存
    invalidate_cache(key, use_memory, use_redis)
    
    # 执行函数获取新结果
    result = func(*args, **kwargs)
    
    # 缓存新结果
    try:
        if _cache_manager:
            _cache_manager.set(
                key,
                result,
                ttl=ttl,
                use_memory=use_memory,
                use_redis=use_redis
            )
        elif _cache_service and use_redis:
            _cache_service.set(key, result, ttl=ttl)
    except Exception:
        pass
    
    return result


def clear_cache(
    pattern: Optional[str] = None,
    use_memory: bool = True,
    use_redis: bool = True
) -> bool:
    """清空缓存
    
    Args:
        pattern: 键模式（可选）
        use_memory: 是否清除内存缓存
        use_redis: 是否清除Redis缓存
        
    Returns:
        是否成功
    """
    try:
        if _cache_manager:
            if pattern:
                # 清除匹配模式的缓存
                # 注意：这里需要实现模式匹配功能
                pass
            else:
                # 清除所有缓存
                _cache_manager.clear(use_memory=use_memory, use_redis=use_redis)
        elif _cache_service and use_redis:
            if pattern:
                # 使用Redis的键模式删除
                _cache_service.delete_pattern(pattern)
            else:
                # 清除所有缓存（需要谨慎使用）
                pass
        
        return True
    except Exception:
        return False


def cache_stats() -> Dict[str, Any]:
    """获取缓存统计信息
    
    Returns:
        缓存统计信息
    """
    if _cache_manager:
        return _cache_manager.get_stats()
    else:
        return {
            "memory": {"size": 0, "entries": 0},
            "redis": {"connected": False},
            "hits": 0,
            "misses": 0,
            "hit_rate": 0.0
        }


# 便捷的装饰器别名
memoize = cached  # 记忆化装饰器别名
lru_cache = lambda maxsize=128, ttl=None: cached(ttl=ttl, use_redis=False)  # LRU缓存装饰器
ttl_cache = lambda ttl=3600: cached(ttl=ttl)  # TTL缓存装饰器