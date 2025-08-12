"""缓存系统测试

测试缓存管理功能。
"""

import pytest
import time
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta

from src.modelscope_mcp.cache.cache_manager import (
    CacheManager, CacheLevel, CacheEntry, CacheStats
)
from src.modelscope_mcp.cache.cache_strategies import (
    EvictionPolicy, CacheItem, CacheStrategy, LRUStrategy,
    LFUStrategy, TTLStrategy, FIFOStrategy, RandomStrategy,
    create_strategy
)
from src.modelscope_mcp.cache.decorators import (
    cached, cache_result, invalidate_cache, refresh_cache,
    clear_cache, cache_stats, memoize, lru_cache, ttl_cache,
    init_cache, get_cache_manager, get_cache_service
)
from src.modelscope_mcp.services.cache import CacheService


class TestCacheEntry:
    """测试缓存条目"""
    
    @pytest.mark.unit
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl=3600
        )
        
        assert entry.key == "test_key"
        assert entry.value == "test_value"
        assert entry.ttl == 3600
        assert entry.size > 0
        assert not entry.is_expired()
    
    @pytest.mark.unit
    def test_cache_entry_expiration(self):
        """测试缓存条目过期"""
        # 创建已过期的条目
        past_time = datetime.now() - timedelta(seconds=10)
        entry = CacheEntry(
            key="test_key",
            value="test_value",
            ttl=5,
            created_at=past_time
        )
        
        assert entry.is_expired()
    
    @pytest.mark.unit
    def test_cache_entry_size_estimation(self):
        """测试缓存条目大小估算"""
        small_entry = CacheEntry("key", "value")
        large_entry = CacheEntry("key", "x" * 1000)
        
        assert large_entry.size > small_entry.size


class TestCacheStats:
    """测试缓存统计"""
    
    @pytest.mark.unit
    def test_cache_stats_creation(self):
        """测试缓存统计创建"""
        stats = CacheStats()
        
        assert stats.hits == 0
        assert stats.misses == 0
        assert stats.sets == 0
        assert stats.deletes == 0
        assert stats.hit_rate == 0.0
    
    @pytest.mark.unit
    def test_cache_stats_hit_rate(self):
        """测试缓存命中率计算"""
        stats = CacheStats(hits=7, misses=3)
        assert stats.hit_rate == 0.7
        
        # 测试零除法
        empty_stats = CacheStats()
        assert empty_stats.hit_rate == 0.0


class TestCacheStrategies:
    """测试缓存策略"""
    
    @pytest.mark.unit
    def test_lru_strategy(self):
        """测试LRU策略"""
        strategy = LRUStrategy(max_size=3)
        
        # 添加项目
        strategy.put("key1", "value1")
        strategy.put("key2", "value2")
        strategy.put("key3", "value3")
        
        assert strategy.get("key1") == "value1"
        assert strategy.size() == 3
        
        # 添加第四个项目，应该驱逐最少使用的
        strategy.put("key4", "value4")
        assert strategy.size() == 3
        assert strategy.get("key2") is None  # key2应该被驱逐
    
    @pytest.mark.unit
    def test_lfu_strategy(self):
        """测试LFU策略"""
        strategy = LFUStrategy(max_size=3)
        
        # 添加项目
        strategy.put("key1", "value1")
        strategy.put("key2", "value2")
        strategy.put("key3", "value3")
        
        # 增加key1的访问频率
        strategy.get("key1")
        strategy.get("key1")
        
        # 添加第四个项目
        strategy.put("key4", "value4")
        
        # key1应该保留（频率最高），其他某个应该被驱逐
        assert strategy.get("key1") == "value1"
        assert strategy.size() == 3
    
    @pytest.mark.unit
    def test_ttl_strategy(self):
        """测试TTL策略"""
        strategy = TTLStrategy(default_ttl=1)  # 1秒TTL
        
        strategy.put("key1", "value1")
        assert strategy.get("key1") == "value1"
        
        # 等待过期
        time.sleep(1.1)
        assert strategy.get("key1") is None
    
    @pytest.mark.unit
    def test_fifo_strategy(self):
        """测试FIFO策略"""
        strategy = FIFOStrategy(max_size=2)
        
        strategy.put("key1", "value1")
        strategy.put("key2", "value2")
        strategy.put("key3", "value3")  # 应该驱逐key1
        
        assert strategy.get("key1") is None
        assert strategy.get("key2") == "value2"
        assert strategy.get("key3") == "value3"
    
    @pytest.mark.unit
    def test_random_strategy(self):
        """测试随机策略"""
        strategy = RandomStrategy(max_size=2)
        
        strategy.put("key1", "value1")
        strategy.put("key2", "value2")
        strategy.put("key3", "value3")  # 应该随机驱逐一个
        
        assert strategy.size() == 2
        # 至少有一个键存在
        keys = ["key1", "key2", "key3"]
        existing_keys = [k for k in keys if strategy.get(k) is not None]
        assert len(existing_keys) == 2
    
    @pytest.mark.unit
    def test_create_strategy(self):
        """测试策略工厂函数"""
        lru = create_strategy(EvictionPolicy.LRU, max_size=10)
        assert isinstance(lru, LRUStrategy)
        
        lfu = create_strategy(EvictionPolicy.LFU, max_size=10)
        assert isinstance(lfu, LFUStrategy)
        
        ttl = create_strategy(EvictionPolicy.TTL, default_ttl=60)
        assert isinstance(ttl, TTLStrategy)
        
        fifo = create_strategy(EvictionPolicy.FIFO, max_size=10)
        assert isinstance(fifo, FIFOStrategy)
        
        random = create_strategy(EvictionPolicy.RANDOM, max_size=10)
        assert isinstance(random, RandomStrategy)


class TestCacheManager:
    """测试缓存管理器"""
    
    @pytest.fixture
    def cache_manager(self, mock_redis_client):
        """创建缓存管理器实例"""
        cache_service = CacheService(redis_client=mock_redis_client)
        return CacheManager(
            cache_service=cache_service,
            memory_max_size=100,
            memory_strategy=EvictionPolicy.LRU
        )
    
    @pytest.mark.unit
    def test_cache_manager_init(self, cache_manager):
        """测试缓存管理器初始化"""
        assert cache_manager._memory_max_size == 100
        assert cache_manager._memory_strategy == EvictionPolicy.LRU
        assert cache_manager._stats.hits == 0
    
    @pytest.mark.unit
    async def test_memory_cache_operations(self, cache_manager):
        """测试内存缓存操作"""
        # 设置缓存
        await cache_manager.set("test_key", "test_value", level=CacheLevel.MEMORY)
        
        # 获取缓存
        value = await cache_manager.get("test_key", level=CacheLevel.MEMORY)
        assert value == "test_value"
        
        # 检查存在性
        exists = await cache_manager.exists("test_key", level=CacheLevel.MEMORY)
        assert exists is True
        
        # 删除缓存
        await cache_manager.delete("test_key", level=CacheLevel.MEMORY)
        value = await cache_manager.get("test_key", level=CacheLevel.MEMORY)
        assert value is None
    
    @pytest.mark.unit
    async def test_redis_cache_operations(self, cache_manager):
        """测试Redis缓存操作"""
        # 设置缓存
        await cache_manager.set("test_key", "test_value", level=CacheLevel.REDIS)
        
        # 获取缓存
        value = await cache_manager.get("test_key", level=CacheLevel.REDIS)
        assert value == "test_value"
        
        # 检查存在性
        exists = await cache_manager.exists("test_key", level=CacheLevel.REDIS)
        assert exists is True
    
    @pytest.mark.unit
    async def test_both_cache_operations(self, cache_manager):
        """测试双级缓存操作"""
        # 设置到两级缓存
        await cache_manager.set("test_key", "test_value", level=CacheLevel.BOTH)
        
        # 从内存获取
        value = await cache_manager.get("test_key", level=CacheLevel.MEMORY)
        assert value == "test_value"
        
        # 从Redis获取
        value = await cache_manager.get("test_key", level=CacheLevel.REDIS)
        assert value == "test_value"
    
    @pytest.mark.unit
    async def test_batch_operations(self, cache_manager):
        """测试批量操作"""
        # 批量设置
        data = {
            "key1": "value1",
            "key2": "value2",
            "key3": "value3"
        }
        await cache_manager.set_many(data, level=CacheLevel.MEMORY)
        
        # 批量获取
        keys = ["key1", "key2", "key3"]
        values = await cache_manager.get_many(keys, level=CacheLevel.MEMORY)
        
        assert values["key1"] == "value1"
        assert values["key2"] == "value2"
        assert values["key3"] == "value3"
        
        # 批量删除
        await cache_manager.delete_many(keys, level=CacheLevel.MEMORY)
        values = await cache_manager.get_many(keys, level=CacheLevel.MEMORY)
        
        assert all(v is None for v in values.values())
    
    @pytest.mark.unit
    async def test_ttl_operations(self, cache_manager):
        """测试TTL操作"""
        # 设置带TTL的缓存
        await cache_manager.set("test_key", "test_value", ttl=60, level=CacheLevel.MEMORY)
        
        # 获取TTL
        ttl = await cache_manager.get_ttl("test_key", level=CacheLevel.MEMORY)
        assert ttl > 0
        assert ttl <= 60
    
    @pytest.mark.unit
    async def test_cache_stats(self, cache_manager):
        """测试缓存统计"""
        # 执行一些操作
        await cache_manager.set("key1", "value1", level=CacheLevel.MEMORY)
        await cache_manager.get("key1", level=CacheLevel.MEMORY)  # 命中
        await cache_manager.get("key2", level=CacheLevel.MEMORY)  # 未命中
        
        stats = await cache_manager.get_stats()
        assert stats.hits >= 1
        assert stats.misses >= 1
        assert stats.sets >= 1
    
    @pytest.mark.unit
    async def test_memory_capacity_management(self, cache_manager):
        """测试内存容量管理"""
        # 填充缓存直到达到容量限制
        for i in range(150):  # 超过max_size=100
            await cache_manager.set(f"key_{i}", f"value_{i}", level=CacheLevel.MEMORY)
        
        # 验证缓存大小不超过限制
        memory_size = len(cache_manager._memory_cache)
        assert memory_size <= 100
    
    @pytest.mark.unit
    async def test_cleanup_expired(self, cache_manager):
        """测试过期清理"""
        # 设置短TTL的缓存
        await cache_manager.set("temp_key", "temp_value", ttl=1, level=CacheLevel.MEMORY)
        
        # 等待过期
        await asyncio.sleep(1.1)
        
        # 执行清理
        await cache_manager.cleanup_expired()
        
        # 验证过期项已被清理
        value = await cache_manager.get("temp_key", level=CacheLevel.MEMORY)
        assert value is None


class TestCacheDecorators:
    """测试缓存装饰器"""
    
    @pytest.fixture
    def setup_cache(self, mock_redis_client):
        """设置缓存"""
        cache_service = CacheService(redis_client=mock_redis_client)
        init_cache(cache_service=cache_service)
    
    @pytest.mark.unit
    def test_cached_decorator(self, setup_cache):
        """测试cached装饰器"""
        call_count = 0
        
        @cached(ttl=60)
        def expensive_function(x, y):
            nonlocal call_count
            call_count += 1
            return x + y
        
        # 第一次调用
        result1 = expensive_function(1, 2)
        assert result1 == 3
        assert call_count == 1
        
        # 第二次调用，应该从缓存获取
        result2 = expensive_function(1, 2)
        assert result2 == 3
        assert call_count == 1  # 没有增加
        
        # 不同参数，应该重新计算
        result3 = expensive_function(2, 3)
        assert result3 == 5
        assert call_count == 2
    
    @pytest.mark.unit
    async def test_cache_result_decorator(self, setup_cache):
        """测试cache_result装饰器"""
        call_count = 0
        
        @cache_result(ttl=60)
        async def async_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 第一次调用
        result1 = await async_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 第二次调用，应该从缓存获取
        result2 = await async_function(5)
        assert result2 == 10
        assert call_count == 1
    
    @pytest.mark.unit
    def test_memoize_decorator(self, setup_cache):
        """测试memoize装饰器"""
        call_count = 0
        
        @memoize
        def fibonacci(n):
            nonlocal call_count
            call_count += 1
            if n <= 1:
                return n
            return fibonacci(n-1) + fibonacci(n-2)
        
        result = fibonacci(10)
        assert result == 55
        # 由于记忆化，调用次数应该大大减少
        assert call_count <= 11  # 最多每个n值计算一次
    
    @pytest.mark.unit
    def test_lru_cache_decorator(self, setup_cache):
        """测试lru_cache装饰器"""
        call_count = 0
        
        @lru_cache(max_size=2)
        def cached_function(x):
            nonlocal call_count
            call_count += 1
            return x * x
        
        # 填充缓存
        cached_function(1)  # call_count = 1
        cached_function(2)  # call_count = 2
        cached_function(1)  # 缓存命中，call_count = 2
        
        # 超出缓存大小
        cached_function(3)  # call_count = 3，应该驱逐某个项
        cached_function(2)  # 可能需要重新计算
        
        assert call_count >= 3
    
    @pytest.mark.unit
    def test_ttl_cache_decorator(self, setup_cache):
        """测试ttl_cache装饰器"""
        call_count = 0
        
        @ttl_cache(ttl=1)  # 1秒TTL
        def time_sensitive_function(x):
            nonlocal call_count
            call_count += 1
            return x + 1
        
        # 第一次调用
        result1 = time_sensitive_function(5)
        assert result1 == 6
        assert call_count == 1
        
        # 立即再次调用，应该从缓存获取
        result2 = time_sensitive_function(5)
        assert result2 == 6
        assert call_count == 1
        
        # 等待过期后再次调用
        time.sleep(1.1)
        result3 = time_sensitive_function(5)
        assert result3 == 6
        assert call_count == 2  # 重新计算
    
    @pytest.mark.unit
    def test_invalidate_cache(self, setup_cache):
        """测试缓存失效"""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 2
        
        # 调用函数
        result1 = test_function(5)
        assert result1 == 10
        assert call_count == 1
        
        # 使缓存失效
        invalidate_cache(test_function, 5)
        
        # 再次调用，应该重新计算
        result2 = test_function(5)
        assert result2 == 10
        assert call_count == 2
    
    @pytest.mark.unit
    def test_clear_cache(self, setup_cache):
        """测试清除缓存"""
        call_count = 0
        
        @cached(ttl=60)
        def test_function(x):
            nonlocal call_count
            call_count += 1
            return x * 3
        
        # 调用多次
        test_function(1)
        test_function(2)
        test_function(3)
        assert call_count == 3
        
        # 清除所有缓存
        clear_cache(test_function)
        
        # 再次调用，应该重新计算
        test_function(1)
        test_function(2)
        assert call_count == 5
    
    @pytest.mark.unit
    def test_cache_stats_function(self, setup_cache):
        """测试缓存统计函数"""
        @cached(ttl=60)
        def test_function(x):
            return x * 4
        
        # 执行一些操作
        test_function(1)  # 设置
        test_function(1)  # 命中
        test_function(2)  # 设置
        
        stats = cache_stats(test_function)
        assert stats is not None
        # 验证统计信息的结构
        assert hasattr(stats, 'hits') or 'hits' in stats


@pytest.mark.integration
class TestCacheIntegration:
    """缓存系统集成测试"""
    
    @pytest.mark.unit
    async def test_cache_service_integration(self, mock_redis_client):
        """测试缓存服务集成"""
        cache_service = CacheService(redis_client=mock_redis_client)
        cache_manager = CacheManager(cache_service=cache_service)
        
        # 测试完整的缓存流程
        await cache_manager.set("integration_key", {"data": "test"}, level=CacheLevel.BOTH)
        
        # 从内存获取
        memory_value = await cache_manager.get("integration_key", level=CacheLevel.MEMORY)
        assert memory_value == {"data": "test"}
        
        # 从Redis获取
        redis_value = await cache_manager.get("integration_key", level=CacheLevel.REDIS)
        assert redis_value == {"data": "test"}
    
    @pytest.mark.unit
    def test_decorator_cache_manager_integration(self, mock_redis_client):
        """测试装饰器与缓存管理器集成"""
        cache_service = CacheService(redis_client=mock_redis_client)
        init_cache(cache_service=cache_service)
        
        @cached(ttl=60, level=CacheLevel.BOTH)
        def integrated_function(x, y):
            return {"result": x + y, "timestamp": time.time()}
        
        # 第一次调用
        result1 = integrated_function(10, 20)
        assert result1["result"] == 30
        
        # 第二次调用，应该从缓存获取
        result2 = integrated_function(10, 20)
        assert result2["result"] == 30
        assert result2["timestamp"] == result1["timestamp"]  # 时间戳应该相同
    
    @pytest.mark.unit
    async def test_cache_fallback_behavior(self, mock_redis_client):
        """测试缓存回退行为"""
        # 模拟Redis连接失败
        mock_redis_client.get.side_effect = Exception("Redis connection failed")
        
        cache_service = CacheService(redis_client=mock_redis_client)
        cache_manager = CacheManager(cache_service=cache_service)
        
        # 设置到内存缓存应该仍然工作
        await cache_manager.set("fallback_key", "fallback_value", level=CacheLevel.MEMORY)
        
        value = await cache_manager.get("fallback_key", level=CacheLevel.MEMORY)
        assert value == "fallback_value"
        
        # Redis操作应该优雅地失败
        redis_value = await cache_manager.get("fallback_key", level=CacheLevel.REDIS)
        assert redis_value is None  # 应该返回None而不是抛出异常