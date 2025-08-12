"""数据库模型测试

测试数据库模型和操作。
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.modelscope_mcp.database.models import (
    Base, Dataset, Query, QueryResult, CacheEntry
)
from src.modelscope_mcp.database.database import (
    DatabaseManager, get_database_manager, init_database
)


class TestDatasetModel:
    """测试数据集模型"""
    
    @pytest.mark.unit
    def test_dataset_creation(self):
        """测试数据集创建"""
        dataset = Dataset(
            id="test/dataset",
            name="Test Dataset",
            source="modelscope",
            description="A test dataset",
            tags=["test", "nlp"],
            size="1MB",
            downloads=100,
            likes=10,
            language="en",
            license="MIT",
            task_type="classification",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert dataset.id == "test/dataset"
        assert dataset.name == "Test Dataset"
        assert dataset.source == "modelscope"
        assert dataset.description == "A test dataset"
        assert dataset.tags == ["test", "nlp"]
        assert dataset.size == "1MB"
        assert dataset.downloads == 100
        assert dataset.likes == 10
        assert dataset.language == "en"
        assert dataset.license == "MIT"
        assert dataset.task_type == "classification"
        assert isinstance(dataset.created_at, datetime)
        assert isinstance(dataset.updated_at, datetime)
    
    @pytest.mark.unit
    def test_dataset_repr(self):
        """测试数据集字符串表示"""
        dataset = Dataset(
            id="test/dataset",
            name="Test Dataset",
            source="modelscope"
        )
        
        repr_str = repr(dataset)
        assert "Dataset" in repr_str
        assert "test/dataset" in repr_str
    
    @pytest.mark.unit
    def test_dataset_to_dict(self):
        """测试数据集转换为字典"""
        now = datetime.now()
        dataset = Dataset(
            id="test/dataset",
            name="Test Dataset",
            source="modelscope",
            description="A test dataset",
            tags=["test"],
            downloads=100,
            created_at=now,
            updated_at=now
        )
        
        data = dataset.to_dict()
        
        assert data["id"] == "test/dataset"
        assert data["name"] == "Test Dataset"
        assert data["source"] == "modelscope"
        assert data["description"] == "A test dataset"
        assert data["tags"] == ["test"]
        assert data["downloads"] == 100
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
    
    @pytest.mark.unit
    def test_dataset_from_dict(self):
        """测试从字典创建数据集"""
        data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope",
            "description": "A test dataset",
            "tags": ["test", "nlp"],
            "size": "1MB",
            "downloads": 100,
            "likes": 10,
            "language": "en",
            "license": "MIT",
            "task_type": "classification"
        }
        
        dataset = Dataset.from_dict(data)
        
        assert dataset.id == "test/dataset"
        assert dataset.name == "Test Dataset"
        assert dataset.source == "modelscope"
        assert dataset.description == "A test dataset"
        assert dataset.tags == ["test", "nlp"]
        assert dataset.size == "1MB"
        assert dataset.downloads == 100
        assert dataset.likes == 10
        assert dataset.language == "en"
        assert dataset.license == "MIT"
        assert dataset.task_type == "classification"


class TestQueryModel:
    """测试查询模型"""
    
    @pytest.mark.unit
    def test_query_creation(self):
        """测试查询创建"""
        query = Query(
            id="query-123",
            original_text="List all NLP datasets",
            parsed_intent="list_datasets",
            parsed_entities=[{"type": "task_type", "value": "nlp"}],
            confidence=0.9,
            execution_time=0.5,
            created_at=datetime.now()
        )
        
        assert query.id == "query-123"
        assert query.original_text == "List all NLP datasets"
        assert query.parsed_intent == "list_datasets"
        assert query.parsed_entities == [{"type": "task_type", "value": "nlp"}]
        assert query.confidence == 0.9
        assert query.execution_time == 0.5
        assert isinstance(query.created_at, datetime)
    
    @pytest.mark.unit
    def test_query_repr(self):
        """测试查询字符串表示"""
        query = Query(
            id="query-123",
            original_text="List datasets",
            parsed_intent="list_datasets"
        )
        
        repr_str = repr(query)
        assert "Query" in repr_str
        assert "query-123" in repr_str
    
    @pytest.mark.unit
    def test_query_to_dict(self):
        """测试查询转换为字典"""
        now = datetime.now()
        query = Query(
            id="query-123",
            original_text="List datasets",
            parsed_intent="list_datasets",
            parsed_entities=[{"type": "task_type", "value": "nlp"}],
            confidence=0.9,
            execution_time=0.5,
            created_at=now
        )
        
        data = query.to_dict()
        
        assert data["id"] == "query-123"
        assert data["original_text"] == "List datasets"
        assert data["parsed_intent"] == "list_datasets"
        assert data["parsed_entities"] == [{"type": "task_type", "value": "nlp"}]
        assert data["confidence"] == 0.9
        assert data["execution_time"] == 0.5
        assert isinstance(data["created_at"], str)


class TestQueryResultModel:
    """测试查询结果模型"""
    
    @pytest.mark.unit
    def test_query_result_creation(self):
        """测试查询结果创建"""
        result = QueryResult(
            id="result-123",
            query_id="query-123",
            result_type="datasets",
            result_data=[{"id": "dataset1", "name": "Dataset 1"}],
            result_count=1,
            success=True,
            error_message=None,
            created_at=datetime.now()
        )
        
        assert result.id == "result-123"
        assert result.query_id == "query-123"
        assert result.result_type == "datasets"
        assert result.result_data == [{"id": "dataset1", "name": "Dataset 1"}]
        assert result.result_count == 1
        assert result.success is True
        assert result.error_message is None
        assert isinstance(result.created_at, datetime)
    
    @pytest.mark.unit
    def test_query_result_error(self):
        """测试查询结果错误情况"""
        result = QueryResult(
            id="result-456",
            query_id="query-456",
            result_type="error",
            result_data=None,
            result_count=0,
            success=False,
            error_message="Dataset not found",
            created_at=datetime.now()
        )
        
        assert result.success is False
        assert result.error_message == "Dataset not found"
        assert result.result_count == 0
        assert result.result_data is None
    
    @pytest.mark.unit
    def test_query_result_to_dict(self):
        """测试查询结果转换为字典"""
        now = datetime.now()
        result = QueryResult(
            id="result-123",
            query_id="query-123",
            result_type="datasets",
            result_data=[{"id": "dataset1"}],
            result_count=1,
            success=True,
            created_at=now
        )
        
        data = result.to_dict()
        
        assert data["id"] == "result-123"
        assert data["query_id"] == "query-123"
        assert data["result_type"] == "datasets"
        assert data["result_data"] == [{"id": "dataset1"}]
        assert data["result_count"] == 1
        assert data["success"] is True
        assert isinstance(data["created_at"], str)


class TestCacheEntryModel:
    """测试缓存条目模型"""
    
    @pytest.mark.unit
    def test_cache_entry_creation(self):
        """测试缓存条目创建"""
        entry = CacheEntry(
            key="cache_key_123",
            value={"data": "test"},
            ttl=3600,
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=3600)
        )
        
        assert entry.key == "cache_key_123"
        assert entry.value == {"data": "test"}
        assert entry.ttl == 3600
        assert isinstance(entry.created_at, datetime)
        assert isinstance(entry.expires_at, datetime)
    
    @pytest.mark.unit
    def test_cache_entry_is_expired(self):
        """测试缓存条目过期检查"""
        # 未过期的条目
        future_time = datetime.now() + timedelta(seconds=3600)
        entry = CacheEntry(
            key="key1",
            value="value1",
            expires_at=future_time
        )
        assert not entry.is_expired()
        
        # 已过期的条目
        past_time = datetime.now() - timedelta(seconds=3600)
        expired_entry = CacheEntry(
            key="key2",
            value="value2",
            expires_at=past_time
        )
        assert expired_entry.is_expired()
    
    @pytest.mark.unit
    def test_cache_entry_to_dict(self):
        """测试缓存条目转换为字典"""
        now = datetime.now()
        expires = now + timedelta(seconds=3600)
        
        entry = CacheEntry(
            key="cache_key",
            value={"test": "data"},
            ttl=3600,
            created_at=now,
            expires_at=expires
        )
        
        data = entry.to_dict()
        
        assert data["key"] == "cache_key"
        assert data["value"] == {"test": "data"}
        assert data["ttl"] == 3600
        assert isinstance(data["created_at"], str)
        assert isinstance(data["expires_at"], str)


class TestDatabaseManager:
    """测试数据库管理器"""
    
    @pytest.fixture
    async def db_manager(self):
        """创建测试数据库管理器"""
        # 使用内存SQLite数据库进行测试
        db_url = "sqlite+aiosqlite:///:memory:"
        manager = DatabaseManager(db_url)
        await manager.init_database()
        yield manager
        await manager.close()
    
    @pytest.mark.unit
    async def test_database_manager_init(self, db_manager):
        """测试数据库管理器初始化"""
        assert db_manager._engine is not None
        assert db_manager._session_factory is not None
    
    @pytest.mark.unit
    async def test_create_dataset(self, db_manager):
        """测试创建数据集"""
        dataset_data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope",
            "description": "A test dataset",
            "tags": ["test"],
            "downloads": 100
        }
        
        dataset = await db_manager.create_dataset(dataset_data)
        
        assert dataset.id == "test/dataset"
        assert dataset.name == "Test Dataset"
        assert dataset.source == "modelscope"
        assert dataset.downloads == 100
    
    @pytest.mark.unit
    async def test_get_dataset(self, db_manager):
        """测试获取数据集"""
        # 先创建数据集
        dataset_data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope"
        }
        await db_manager.create_dataset(dataset_data)
        
        # 获取数据集
        dataset = await db_manager.get_dataset("test/dataset")
        
        assert dataset is not None
        assert dataset.id == "test/dataset"
        assert dataset.name == "Test Dataset"
    
    @pytest.mark.unit
    async def test_get_nonexistent_dataset(self, db_manager):
        """测试获取不存在的数据集"""
        dataset = await db_manager.get_dataset("nonexistent/dataset")
        assert dataset is None
    
    @pytest.mark.unit
    async def test_update_dataset(self, db_manager):
        """测试更新数据集"""
        # 先创建数据集
        dataset_data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope",
            "downloads": 100
        }
        await db_manager.create_dataset(dataset_data)
        
        # 更新数据集
        update_data = {
            "name": "Updated Dataset",
            "downloads": 200
        }
        updated_dataset = await db_manager.update_dataset("test/dataset", update_data)
        
        assert updated_dataset is not None
        assert updated_dataset.name == "Updated Dataset"
        assert updated_dataset.downloads == 200
    
    @pytest.mark.unit
    async def test_delete_dataset(self, db_manager):
        """测试删除数据集"""
        # 先创建数据集
        dataset_data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope"
        }
        await db_manager.create_dataset(dataset_data)
        
        # 删除数据集
        success = await db_manager.delete_dataset("test/dataset")
        assert success is True
        
        # 验证数据集已被删除
        dataset = await db_manager.get_dataset("test/dataset")
        assert dataset is None
    
    @pytest.mark.unit
    async def test_list_datasets(self, db_manager):
        """测试列出数据集"""
        # 创建多个数据集
        datasets_data = [
            {"id": "test/dataset1", "name": "Dataset 1", "source": "modelscope", "downloads": 100},
            {"id": "test/dataset2", "name": "Dataset 2", "source": "huggingface", "downloads": 200},
            {"id": "test/dataset3", "name": "Dataset 3", "source": "modelscope", "downloads": 300}
        ]
        
        for data in datasets_data:
            await db_manager.create_dataset(data)
        
        # 列出所有数据集
        datasets = await db_manager.list_datasets()
        assert len(datasets) == 3
        
        # 按源过滤
        modelscope_datasets = await db_manager.list_datasets(source="modelscope")
        assert len(modelscope_datasets) == 2
        
        # 限制数量
        limited_datasets = await db_manager.list_datasets(limit=2)
        assert len(limited_datasets) == 2
        
        # 排序
        sorted_datasets = await db_manager.list_datasets(order_by="downloads", desc=True)
        assert sorted_datasets[0].downloads == 300
        assert sorted_datasets[1].downloads == 200
        assert sorted_datasets[2].downloads == 100
    
    @pytest.mark.unit
    async def test_search_datasets(self, db_manager):
        """测试搜索数据集"""
        # 创建测试数据集
        datasets_data = [
            {"id": "nlp/sentiment", "name": "Sentiment Analysis", "source": "modelscope", "tags": ["nlp", "sentiment"]},
            {"id": "cv/image", "name": "Image Classification", "source": "huggingface", "tags": ["cv", "image"]},
            {"id": "nlp/qa", "name": "Question Answering", "source": "modelscope", "tags": ["nlp", "qa"]}
        ]
        
        for data in datasets_data:
            await db_manager.create_dataset(data)
        
        # 搜索包含"nlp"的数据集
        nlp_datasets = await db_manager.search_datasets("nlp")
        assert len(nlp_datasets) == 2
        
        # 搜索包含"sentiment"的数据集
        sentiment_datasets = await db_manager.search_datasets("sentiment")
        assert len(sentiment_datasets) == 1
        assert sentiment_datasets[0].id == "nlp/sentiment"
    
    @pytest.mark.unit
    async def test_create_query(self, db_manager):
        """测试创建查询"""
        query_data = {
            "id": "query-123",
            "original_text": "List NLP datasets",
            "parsed_intent": "list_datasets",
            "parsed_entities": [{"type": "task_type", "value": "nlp"}],
            "confidence": 0.9
        }
        
        query = await db_manager.create_query(query_data)
        
        assert query.id == "query-123"
        assert query.original_text == "List NLP datasets"
        assert query.parsed_intent == "list_datasets"
        assert query.confidence == 0.9
    
    @pytest.mark.unit
    async def test_get_query(self, db_manager):
        """测试获取查询"""
        # 先创建查询
        query_data = {
            "id": "query-123",
            "original_text": "List datasets",
            "parsed_intent": "list_datasets"
        }
        await db_manager.create_query(query_data)
        
        # 获取查询
        query = await db_manager.get_query("query-123")
        
        assert query is not None
        assert query.id == "query-123"
        assert query.original_text == "List datasets"
    
    @pytest.mark.unit
    async def test_create_query_result(self, db_manager):
        """测试创建查询结果"""
        # 先创建查询
        query_data = {
            "id": "query-123",
            "original_text": "List datasets",
            "parsed_intent": "list_datasets"
        }
        await db_manager.create_query(query_data)
        
        # 创建查询结果
        result_data = {
            "id": "result-123",
            "query_id": "query-123",
            "result_type": "datasets",
            "result_data": [{"id": "dataset1", "name": "Dataset 1"}],
            "result_count": 1,
            "success": True
        }
        
        result = await db_manager.create_query_result(result_data)
        
        assert result.id == "result-123"
        assert result.query_id == "query-123"
        assert result.result_type == "datasets"
        assert result.result_count == 1
        assert result.success is True
    
    @pytest.mark.unit
    async def test_get_query_results(self, db_manager):
        """测试获取查询结果"""
        # 创建查询和结果
        query_data = {
            "id": "query-123",
            "original_text": "List datasets",
            "parsed_intent": "list_datasets"
        }
        await db_manager.create_query(query_data)
        
        result_data = {
            "id": "result-123",
            "query_id": "query-123",
            "result_type": "datasets",
            "result_data": [{"id": "dataset1"}],
            "result_count": 1,
            "success": True
        }
        await db_manager.create_query_result(result_data)
        
        # 获取查询结果
        results = await db_manager.get_query_results("query-123")
        
        assert len(results) == 1
        assert results[0].id == "result-123"
        assert results[0].query_id == "query-123"
    
    @pytest.mark.unit
    async def test_cache_operations(self, db_manager):
        """测试缓存操作"""
        # 设置缓存
        await db_manager.set_cache("test_key", {"data": "test"}, ttl=3600)
        
        # 获取缓存
        value = await db_manager.get_cache("test_key")
        assert value == {"data": "test"}
        
        # 检查缓存存在性
        exists = await db_manager.cache_exists("test_key")
        assert exists is True
        
        # 删除缓存
        await db_manager.delete_cache("test_key")
        
        # 验证缓存已删除
        value = await db_manager.get_cache("test_key")
        assert value is None
    
    @pytest.mark.unit
    async def test_cache_expiration(self, db_manager):
        """测试缓存过期"""
        # 设置短TTL的缓存
        await db_manager.set_cache("temp_key", "temp_value", ttl=1)
        
        # 立即获取应该成功
        value = await db_manager.get_cache("temp_key")
        assert value == "temp_value"
        
        # 等待过期
        await asyncio.sleep(1.1)
        
        # 清理过期缓存
        await db_manager.cleanup_expired_cache()
        
        # 获取应该返回None
        value = await db_manager.get_cache("temp_key")
        assert value is None
    
    @pytest.mark.unit
    async def test_transaction_rollback(self, db_manager):
        """测试事务回滚"""
        # 这个测试模拟事务失败的情况
        with pytest.raises(Exception):
            async with db_manager.get_session() as session:
                # 创建数据集
                dataset = Dataset(
                    id="test/dataset",
                    name="Test Dataset",
                    source="modelscope"
                )
                session.add(dataset)
                await session.flush()
                
                # 模拟错误
                raise Exception("Simulated error")
        
        # 验证数据集没有被保存（事务已回滚）
        dataset = await db_manager.get_dataset("test/dataset")
        assert dataset is None
    
    @pytest.mark.unit
    async def test_concurrent_access(self, db_manager):
        """测试并发访问"""
        async def create_dataset(dataset_id):
            dataset_data = {
                "id": f"test/dataset{dataset_id}",
                "name": f"Dataset {dataset_id}",
                "source": "modelscope"
            }
            return await db_manager.create_dataset(dataset_data)
        
        # 并发创建多个数据集
        tasks = [create_dataset(i) for i in range(5)]
        datasets = await asyncio.gather(*tasks)
        
        # 验证所有数据集都被创建
        assert len(datasets) == 5
        for i, dataset in enumerate(datasets):
            assert dataset.id == f"test/dataset{i}"
        
        # 验证数据库中确实有5个数据集
        all_datasets = await db_manager.list_datasets()
        assert len(all_datasets) == 5


@pytest.mark.integration
class TestDatabaseIntegration:
    """数据库集成测试"""
    
    @pytest.mark.unit
    async def test_full_database_workflow(self):
        """测试完整数据库工作流"""
        # 创建数据库管理器
        db_url = "sqlite+aiosqlite:///:memory:"
        db_manager = DatabaseManager(db_url)
        await db_manager.init_database()
        
        try:
            # 1. 创建数据集
            dataset_data = {
                "id": "test/workflow-dataset",
                "name": "Workflow Test Dataset",
                "source": "modelscope",
                "description": "A dataset for testing workflow",
                "tags": ["test", "workflow"],
                "downloads": 100
            }
            dataset = await db_manager.create_dataset(dataset_data)
            assert dataset is not None
            
            # 2. 创建查询
            query_data = {
                "id": "workflow-query",
                "original_text": "Find workflow test datasets",
                "parsed_intent": "search_datasets",
                "parsed_entities": [{"type": "keyword", "value": "workflow"}],
                "confidence": 0.85
            }
            query = await db_manager.create_query(query_data)
            assert query is not None
            
            # 3. 创建查询结果
            result_data = {
                "id": "workflow-result",
                "query_id": "workflow-query",
                "result_type": "datasets",
                "result_data": [dataset.to_dict()],
                "result_count": 1,
                "success": True
            }
            result = await db_manager.create_query_result(result_data)
            assert result is not None
            
            # 4. 设置缓存
            cache_key = "workflow_cache"
            cache_value = {"workflow": "test", "datasets": [dataset.to_dict()]}
            await db_manager.set_cache(cache_key, cache_value, ttl=3600)
            
            # 5. 验证所有数据
            # 验证数据集
            retrieved_dataset = await db_manager.get_dataset("test/workflow-dataset")
            assert retrieved_dataset.name == "Workflow Test Dataset"
            
            # 验证查询
            retrieved_query = await db_manager.get_query("workflow-query")
            assert retrieved_query.original_text == "Find workflow test datasets"
            
            # 验证查询结果
            query_results = await db_manager.get_query_results("workflow-query")
            assert len(query_results) == 1
            assert query_results[0].success is True
            
            # 验证缓存
            cached_value = await db_manager.get_cache(cache_key)
            assert cached_value["workflow"] == "test"
            
            # 6. 搜索和过滤
            search_results = await db_manager.search_datasets("workflow")
            assert len(search_results) == 1
            assert search_results[0].id == "test/workflow-dataset"
            
        finally:
            await db_manager.close()
    
    @pytest.mark.unit
    async def test_database_error_handling(self):
        """测试数据库错误处理"""
        # 使用无效的数据库URL
        invalid_db_url = "invalid://database/url"
        
        with pytest.raises(Exception):
            db_manager = DatabaseManager(invalid_db_url)
            await db_manager.init_database()
    
    @pytest.mark.unit
    async def test_global_database_manager(self):
        """测试全局数据库管理器"""
        # 初始化全局数据库
        db_url = "sqlite+aiosqlite:///:memory:"
        await init_database(db_url)
        
        # 获取全局管理器
        manager1 = get_database_manager()
        manager2 = get_database_manager()
        
        # 应该是同一个实例
        assert manager1 is manager2
        
        # 测试基本操作
        dataset_data = {
            "id": "global/test-dataset",
            "name": "Global Test Dataset",
            "source": "modelscope"
        }
        
        dataset = await manager1.create_dataset(dataset_data)
        assert dataset is not None
        
        # 通过另一个引用获取数据集
        retrieved_dataset = await manager2.get_dataset("global/test-dataset")
        assert retrieved_dataset is not None
        assert retrieved_dataset.name == "Global Test Dataset"