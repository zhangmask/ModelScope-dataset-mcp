"""数据集管理器测试

测试数据集管理功能。
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from src.modelscope_mcp.integrations.dataset_manager import (
    DatasetManager, DatasetSource, UnifiedDatasetInfo
)


class TestDatasetSource:
    """测试数据集源枚举"""
    
    @pytest.mark.unit
    def test_dataset_source_values(self):
        """测试数据集源值"""
        assert DatasetSource.MODELSCOPE.value == "modelscope"
        assert DatasetSource.HUGGINGFACE.value == "huggingface"
        assert DatasetSource.AUTO.value == "auto"


class TestUnifiedDatasetInfo:
    """测试统一数据集信息"""
    
    @pytest.mark.unit
    def test_unified_dataset_info_creation(self):
        """测试统一数据集信息创建"""
        info = UnifiedDatasetInfo(
            id="test/dataset",
            name="Test Dataset",
            source=DatasetSource.MODELSCOPE,
            description="A test dataset",
            tags=["test", "example"],
            size="1MB",
            downloads=100,
            likes=10,
            language="en",
            license="MIT",
            created_at="2024-01-01",
            updated_at="2024-01-02"
        )
        
        assert info.id == "test/dataset"
        assert info.name == "Test Dataset"
        assert info.source == DatasetSource.MODELSCOPE
        assert info.description == "A test dataset"
        assert info.tags == ["test", "example"]
        assert info.size == "1MB"
        assert info.downloads == 100
        assert info.likes == 10
        assert info.language == "en"
        assert info.license == "MIT"
        assert info.created_at == "2024-01-01"
        assert info.updated_at == "2024-01-02"
    
    @pytest.mark.unit
    def test_unified_dataset_info_to_dict(self):
        """测试转换为字典"""
        info = UnifiedDatasetInfo(
            id="test/dataset",
            name="Test Dataset",
            source=DatasetSource.MODELSCOPE
        )
        
        data = info.to_dict()
        
        assert data["id"] == "test/dataset"
        assert data["name"] == "Test Dataset"
        assert data["source"] == "modelscope"
        assert "description" in data
        assert "tags" in data
    
    @pytest.mark.unit
    def test_unified_dataset_info_from_dict(self):
        """测试从字典创建"""
        data = {
            "id": "test/dataset",
            "name": "Test Dataset",
            "source": "modelscope",
            "description": "A test dataset",
            "tags": ["test"],
            "size": "1MB",
            "downloads": 100,
            "likes": 10
        }
        
        info = UnifiedDatasetInfo.from_dict(data)
        
        assert info.id == "test/dataset"
        assert info.name == "Test Dataset"
        assert info.source == DatasetSource.MODELSCOPE
        assert info.description == "A test dataset"
        assert info.tags == ["test"]
        assert info.size == "1MB"
        assert info.downloads == 100
        assert info.likes == 10


class TestDatasetManager:
    """测试数据集管理器"""
    
    @pytest.fixture
    def mock_modelscope(self):
        """模拟ModelScope"""
        with patch('src.modelscope_mcp.integrations.dataset_manager.ModelScopeDatasets') as mock:
            mock_instance = Mock()
            mock.return_value = mock_instance
            yield mock_instance
    
    @pytest.fixture
    def mock_datasets(self):
        """模拟Hugging Face datasets"""
        with patch('src.modelscope_mcp.integrations.dataset_manager.datasets') as mock:
            yield mock
    
    @pytest.fixture
    def dataset_manager(self, mock_modelscope, mock_datasets, mock_redis_client):
        """创建数据集管理器实例"""
        from src.modelscope_mcp.services.cache import CacheService
        cache_service = CacheService(redis_client=mock_redis_client)
        
        return DatasetManager(
            cache_service=cache_service,
            modelscope_enabled=True,
            huggingface_enabled=True
        )
    
    @pytest.mark.unit
    def test_dataset_manager_init(self, dataset_manager):
        """测试数据集管理器初始化"""
        assert dataset_manager.modelscope_enabled is True
        assert dataset_manager.huggingface_enabled is True
        assert dataset_manager._cache_service is not None
    
    @pytest.mark.unit
    def test_detect_source_modelscope(self, dataset_manager):
        """测试检测ModelScope数据集源"""
        # ModelScope格式的数据集ID
        source = dataset_manager._detect_source("damo/nlp_dataset")
        assert source == DatasetSource.MODELSCOPE
        
        source = dataset_manager._detect_source("modelscope/test-dataset")
        assert source == DatasetSource.MODELSCOPE
    
    @pytest.mark.unit
    def test_detect_source_huggingface(self, dataset_manager):
        """测试检测Hugging Face数据集源"""
        # Hugging Face格式的数据集ID
        source = dataset_manager._detect_source("squad")
        assert source == DatasetSource.HUGGINGFACE
        
        source = dataset_manager._detect_source("glue")
        assert source == DatasetSource.HUGGINGFACE
        
        source = dataset_manager._detect_source("user/dataset")
        assert source == DatasetSource.HUGGINGFACE
    
    @pytest.mark.unit
    async def test_list_datasets_modelscope(self, dataset_manager, mock_modelscope):
        """测试列出ModelScope数据集"""
        # 模拟ModelScope返回数据
        mock_modelscope.list_datasets.return_value = [
            {
                "id": "damo/dataset1",
                "name": "Dataset 1",
                "description": "Test dataset 1",
                "tags": ["nlp"],
                "downloads": 100
            },
            {
                "id": "damo/dataset2",
                "name": "Dataset 2",
                "description": "Test dataset 2",
                "tags": ["cv"],
                "downloads": 200
            }
        ]
        
        datasets = await dataset_manager.list_datasets(
            source=DatasetSource.MODELSCOPE,
            limit=10
        )
        
        assert len(datasets) == 2
        assert datasets[0].id == "damo/dataset1"
        assert datasets[0].source == DatasetSource.MODELSCOPE
        assert datasets[1].id == "damo/dataset2"
        assert datasets[1].source == DatasetSource.MODELSCOPE
        
        mock_modelscope.list_datasets.assert_called_once_with(limit=10)
    
    @pytest.mark.unit
    async def test_list_datasets_huggingface(self, dataset_manager, mock_datasets):
        """测试列出Hugging Face数据集"""
        # 模拟Hugging Face返回数据
        mock_datasets.list_datasets.return_value = [
            {
                "id": "squad",
                "name": "SQuAD",
                "description": "Stanford Question Answering Dataset",
                "tags": ["question-answering"],
                "downloads": 1000
            },
            {
                "id": "glue",
                "name": "GLUE",
                "description": "General Language Understanding Evaluation",
                "tags": ["text-classification"],
                "downloads": 2000
            }
        ]
        
        datasets = await dataset_manager.list_datasets(
            source=DatasetSource.HUGGINGFACE,
            limit=10
        )
        
        assert len(datasets) == 2
        assert datasets[0].id == "squad"
        assert datasets[0].source == DatasetSource.HUGGINGFACE
        assert datasets[1].id == "glue"
        assert datasets[1].source == DatasetSource.HUGGINGFACE
        
        mock_datasets.list_datasets.assert_called_once_with(limit=10)
    
    @pytest.mark.unit
    async def test_list_datasets_auto(self, dataset_manager, mock_modelscope, mock_datasets):
        """测试自动列出所有源的数据集"""
        # 模拟两个源的返回数据
        mock_modelscope.list_datasets.return_value = [
            {
                "id": "damo/dataset1",
                "name": "Dataset 1",
                "description": "ModelScope dataset",
                "tags": ["nlp"]
            }
        ]
        
        mock_datasets.list_datasets.return_value = [
            {
                "id": "squad",
                "name": "SQuAD",
                "description": "Hugging Face dataset",
                "tags": ["qa"]
            }
        ]
        
        datasets = await dataset_manager.list_datasets(
            source=DatasetSource.AUTO,
            limit=10
        )
        
        assert len(datasets) == 2
        
        # 验证包含两个源的数据集
        sources = {d.source for d in datasets}
        assert DatasetSource.MODELSCOPE in sources
        assert DatasetSource.HUGGINGFACE in sources
    
    @pytest.mark.unit
    async def test_get_dataset_info_modelscope(self, dataset_manager, mock_modelscope):
        """测试获取ModelScope数据集信息"""
        # 模拟ModelScope返回数据
        mock_modelscope.get_dataset_info.return_value = {
            "id": "damo/test-dataset",
            "name": "Test Dataset",
            "description": "A test dataset from ModelScope",
            "tags": ["nlp", "test"],
            "size": "10MB",
            "downloads": 500,
            "likes": 25,
            "language": "zh",
            "license": "Apache-2.0",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-15"
        }
        
        info = await dataset_manager.get_dataset_info("damo/test-dataset")
        
        assert info.id == "damo/test-dataset"
        assert info.name == "Test Dataset"
        assert info.source == DatasetSource.MODELSCOPE
        assert info.description == "A test dataset from ModelScope"
        assert info.tags == ["nlp", "test"]
        assert info.size == "10MB"
        assert info.downloads == 500
        assert info.likes == 25
        
        mock_modelscope.get_dataset_info.assert_called_once_with("damo/test-dataset")
    
    @pytest.mark.unit
    async def test_get_dataset_info_huggingface(self, dataset_manager, mock_datasets):
        """测试获取Hugging Face数据集信息"""
        # 模拟Hugging Face返回数据
        mock_datasets.get_dataset_info.return_value = {
            "id": "squad",
            "name": "SQuAD",
            "description": "Stanford Question Answering Dataset",
            "tags": ["question-answering"],
            "size": "50MB",
            "downloads": 10000,
            "likes": 100,
            "language": "en",
            "license": "CC BY-SA 4.0"
        }
        
        info = await dataset_manager.get_dataset_info("squad")
        
        assert info.id == "squad"
        assert info.name == "SQuAD"
        assert info.source == DatasetSource.HUGGINGFACE
        assert info.description == "Stanford Question Answering Dataset"
        assert info.tags == ["question-answering"]
        assert info.size == "50MB"
        assert info.downloads == 10000
        assert info.likes == 100
        
        mock_datasets.get_dataset_info.assert_called_once_with("squad")
    
    @pytest.mark.unit
    async def test_get_dataset_samples_modelscope(self, dataset_manager, mock_modelscope):
        """测试获取ModelScope数据集样本"""
        # 模拟ModelScope返回数据
        mock_modelscope.get_dataset_samples.return_value = [
            {"text": "Sample 1", "label": "positive"},
            {"text": "Sample 2", "label": "negative"},
            {"text": "Sample 3", "label": "neutral"}
        ]
        
        samples = await dataset_manager.get_dataset_samples(
            "damo/sentiment-dataset",
            limit=3
        )
        
        assert len(samples) == 3
        assert samples[0]["text"] == "Sample 1"
        assert samples[0]["label"] == "positive"
        assert samples[1]["text"] == "Sample 2"
        assert samples[1]["label"] == "negative"
        
        mock_modelscope.get_dataset_samples.assert_called_once_with(
            "damo/sentiment-dataset", limit=3, offset=0
        )
    
    @pytest.mark.unit
    async def test_get_dataset_samples_huggingface(self, dataset_manager, mock_datasets):
        """测试获取Hugging Face数据集样本"""
        # 模拟Hugging Face返回数据
        mock_datasets.get_dataset_samples.return_value = [
            {"question": "What is AI?", "answer": "Artificial Intelligence"},
            {"question": "What is ML?", "answer": "Machine Learning"}
        ]
        
        samples = await dataset_manager.get_dataset_samples(
            "squad",
            limit=2
        )
        
        assert len(samples) == 2
        assert samples[0]["question"] == "What is AI?"
        assert samples[0]["answer"] == "Artificial Intelligence"
        assert samples[1]["question"] == "What is ML?"
        assert samples[1]["answer"] == "Machine Learning"
        
        mock_datasets.get_dataset_samples.assert_called_once_with(
            "squad", limit=2, offset=0
        )
    
    @pytest.mark.unit
    async def test_search_datasets_modelscope(self, dataset_manager, mock_modelscope):
        """测试搜索ModelScope数据集"""
        # 模拟ModelScope搜索结果
        mock_modelscope.search_datasets.return_value = [
            {
                "id": "damo/nlp-dataset1",
                "name": "NLP Dataset 1",
                "description": "Natural language processing dataset",
                "tags": ["nlp", "text"],
                "downloads": 300
            },
            {
                "id": "damo/nlp-dataset2",
                "name": "NLP Dataset 2",
                "description": "Another NLP dataset",
                "tags": ["nlp", "classification"],
                "downloads": 150
            }
        ]
        
        results = await dataset_manager.search_datasets(
            query="nlp",
            source=DatasetSource.MODELSCOPE,
            limit=10
        )
        
        assert len(results) == 2
        assert results[0].id == "damo/nlp-dataset1"
        assert results[0].source == DatasetSource.MODELSCOPE
        assert "nlp" in results[0].tags
        assert results[1].id == "damo/nlp-dataset2"
        assert results[1].source == DatasetSource.MODELSCOPE
        
        mock_modelscope.search_datasets.assert_called_once_with(
            query="nlp", limit=10
        )
    
    @pytest.mark.unit
    async def test_search_datasets_huggingface(self, dataset_manager, mock_datasets):
        """测试搜索Hugging Face数据集"""
        # 模拟Hugging Face搜索结果
        mock_datasets.search_datasets.return_value = [
            {
                "id": "imdb",
                "name": "IMDB Movie Reviews",
                "description": "Movie review sentiment classification",
                "tags": ["sentiment", "classification"],
                "downloads": 5000
            }
        ]
        
        results = await dataset_manager.search_datasets(
            query="sentiment",
            source=DatasetSource.HUGGINGFACE,
            limit=10
        )
        
        assert len(results) == 1
        assert results[0].id == "imdb"
        assert results[0].source == DatasetSource.HUGGINGFACE
        assert "sentiment" in results[0].tags
        
        mock_datasets.search_datasets.assert_called_once_with(
            query="sentiment", limit=10
        )
    
    @pytest.mark.unit
    async def test_search_datasets_auto(self, dataset_manager, mock_modelscope, mock_datasets):
        """测试自动搜索所有源的数据集"""
        # 模拟两个源的搜索结果
        mock_modelscope.search_datasets.return_value = [
            {
                "id": "damo/cv-dataset",
                "name": "CV Dataset",
                "description": "Computer vision dataset",
                "tags": ["cv", "image"]
            }
        ]
        
        mock_datasets.search_datasets.return_value = [
            {
                "id": "cifar10",
                "name": "CIFAR-10",
                "description": "Image classification dataset",
                "tags": ["cv", "classification"]
            }
        ]
        
        results = await dataset_manager.search_datasets(
            query="cv",
            source=DatasetSource.AUTO,
            limit=10
        )
        
        assert len(results) == 2
        
        # 验证包含两个源的结果
        sources = {r.source for r in results}
        assert DatasetSource.MODELSCOPE in sources
        assert DatasetSource.HUGGINGFACE in sources
    
    @pytest.mark.unit
    async def test_deduplication(self, dataset_manager):
        """测试去重功能"""
        datasets = [
            UnifiedDatasetInfo(id="dataset1", name="Dataset 1", source=DatasetSource.MODELSCOPE),
            UnifiedDatasetInfo(id="dataset2", name="Dataset 2", source=DatasetSource.HUGGINGFACE),
            UnifiedDatasetInfo(id="dataset1", name="Dataset 1", source=DatasetSource.MODELSCOPE),  # 重复
            UnifiedDatasetInfo(id="dataset3", name="Dataset 3", source=DatasetSource.HUGGINGFACE)
        ]
        
        deduplicated = dataset_manager._deduplicate_datasets(datasets)
        
        assert len(deduplicated) == 3
        ids = [d.id for d in deduplicated]
        assert ids.count("dataset1") == 1  # 只保留一个
        assert "dataset2" in ids
        assert "dataset3" in ids
    
    @pytest.mark.unit
    async def test_sorting(self, dataset_manager):
        """测试排序功能"""
        datasets = [
            UnifiedDatasetInfo(id="dataset1", name="Dataset 1", source=DatasetSource.MODELSCOPE, downloads=100),
            UnifiedDatasetInfo(id="dataset2", name="Dataset 2", source=DatasetSource.HUGGINGFACE, downloads=300),
            UnifiedDatasetInfo(id="dataset3", name="Dataset 3", source=DatasetSource.MODELSCOPE, downloads=200)
        ]
        
        # 按下载量降序排序
        sorted_datasets = dataset_manager._sort_datasets(datasets, sort_by="downloads", ascending=False)
        
        assert sorted_datasets[0].downloads == 300
        assert sorted_datasets[1].downloads == 200
        assert sorted_datasets[2].downloads == 100
        
        # 按名称升序排序
        sorted_datasets = dataset_manager._sort_datasets(datasets, sort_by="name", ascending=True)
        
        names = [d.name for d in sorted_datasets]
        assert names == ["Dataset 1", "Dataset 2", "Dataset 3"]
    
    @pytest.mark.unit
    async def test_pagination(self, dataset_manager):
        """测试分页功能"""
        datasets = [
            UnifiedDatasetInfo(id=f"dataset{i}", name=f"Dataset {i}", source=DatasetSource.MODELSCOPE)
            for i in range(1, 11)  # 10个数据集
        ]
        
        # 第一页，每页3个
        page1 = dataset_manager._paginate_datasets(datasets, limit=3, offset=0)
        assert len(page1) == 3
        assert page1[0].id == "dataset1"
        assert page1[2].id == "dataset3"
        
        # 第二页，每页3个
        page2 = dataset_manager._paginate_datasets(datasets, limit=3, offset=3)
        assert len(page2) == 3
        assert page2[0].id == "dataset4"
        assert page2[2].id == "dataset6"
        
        # 最后一页，可能不满
        last_page = dataset_manager._paginate_datasets(datasets, limit=3, offset=9)
        assert len(last_page) == 1
        assert last_page[0].id == "dataset10"
    
    @pytest.mark.unit
    async def test_caching(self, dataset_manager, mock_modelscope):
        """测试缓存功能"""
        # 模拟ModelScope返回数据
        mock_modelscope.list_datasets.return_value = [
            {
                "id": "damo/cached-dataset",
                "name": "Cached Dataset",
                "description": "A dataset for testing cache",
                "tags": ["test"]
            }
        ]
        
        # 第一次调用，应该调用ModelScope API
        datasets1 = await dataset_manager.list_datasets(
            source=DatasetSource.MODELSCOPE,
            limit=10
        )
        
        # 第二次调用，应该从缓存获取
        datasets2 = await dataset_manager.list_datasets(
            source=DatasetSource.MODELSCOPE,
            limit=10
        )
        
        # 验证结果相同
        assert len(datasets1) == len(datasets2)
        assert datasets1[0].id == datasets2[0].id
        
        # 验证ModelScope API只被调用一次（第二次从缓存获取）
        assert mock_modelscope.list_datasets.call_count == 1
    
    @pytest.mark.unit
    async def test_error_handling(self, dataset_manager, mock_modelscope):
        """测试错误处理"""
        # 模拟ModelScope API错误
        mock_modelscope.list_datasets.side_effect = Exception("API Error")
        
        # 应该优雅地处理错误
        datasets = await dataset_manager.list_datasets(
            source=DatasetSource.MODELSCOPE,
            limit=10
        )
        
        # 应该返回空列表而不是抛出异常
        assert datasets == []
    
    @pytest.mark.unit
    async def test_disabled_source(self, mock_redis_client):
        """测试禁用的数据源"""
        from src.modelscope_mcp.services.cache import CacheService
        cache_service = CacheService(redis_client=mock_redis_client)
        
        # 创建只启用ModelScope的管理器
        manager = DatasetManager(
            cache_service=cache_service,
            modelscope_enabled=True,
            huggingface_enabled=False
        )
        
        # 尝试从Hugging Face获取数据集应该返回空列表
        datasets = await manager.list_datasets(
            source=DatasetSource.HUGGINGFACE,
            limit=10
        )
        
        assert datasets == []


@pytest.mark.integration
class TestDatasetManagerIntegration:
    """数据集管理器集成测试"""
    
    @pytest.mark.external
    async def test_real_modelscope_integration(self):
        """测试真实ModelScope集成（需要网络连接）"""
        # 这个测试需要真实的网络连接
        # 在CI/CD环境中可能需要跳过
        pytest.skip("Requires real ModelScope API access")
        
        from src.modelscope_mcp.services.cache import CacheService
        import redis.asyncio as redis
        
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        cache_service = CacheService(redis_client=redis_client)
        
        manager = DatasetManager(
            cache_service=cache_service,
            modelscope_enabled=True,
            huggingface_enabled=False
        )
        
        # 测试列出数据集
        datasets = await manager.list_datasets(
            source=DatasetSource.MODELSCOPE,
            limit=5
        )
        
        assert len(datasets) > 0
        assert all(d.source == DatasetSource.MODELSCOPE for d in datasets)
        
        # 测试获取数据集信息
        if datasets:
            info = await manager.get_dataset_info(datasets[0].id)
            assert info is not None
            assert info.id == datasets[0].id
    
    @pytest.mark.external
    async def test_real_huggingface_integration(self):
        """测试真实Hugging Face集成（需要网络连接）"""
        # 这个测试需要真实的网络连接
        pytest.skip("Requires real Hugging Face API access")
        
        from src.modelscope_mcp.services.cache import CacheService
        import redis.asyncio as redis
        
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        cache_service = CacheService(redis_client=redis_client)
        
        manager = DatasetManager(
            cache_service=cache_service,
            modelscope_enabled=False,
            huggingface_enabled=True
        )
        
        # 测试搜索数据集
        results = await manager.search_datasets(
            query="squad",
            source=DatasetSource.HUGGINGFACE,
            limit=5
        )
        
        assert len(results) > 0
        assert all(r.source == DatasetSource.HUGGINGFACE for r in results)
        
        # 测试获取样本
        if results:
            samples = await manager.get_dataset_samples(
                results[0].id,
                limit=3
            )
            assert len(samples) > 0
            assert isinstance(samples[0], dict)