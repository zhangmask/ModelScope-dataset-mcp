"""MCP工具测试

测试MCP工具的功能。
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from src.modelscope_mcp.tools.list_datasets import ListDatasetsHandler
from src.modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
from src.modelscope_mcp.tools.filter_samples import FilterSamplesHandler
from src.modelscope_mcp.tools.query_dataset import QueryDatasetHandler
from src.modelscope_mcp.services.database import DatabaseService
from src.modelscope_mcp.services.cache import CacheService
from src.modelscope_mcp.core.config import Config


@pytest.fixture
def mock_db_service():
    """Mock数据库服务"""
    return Mock(spec=DatabaseService)

@pytest.fixture
def mock_cache_service():
    """Mock缓存服务"""
    return Mock(spec=CacheService)

class TestListDatasetsHandler:
    """测试数据集列表工具"""
    
    @pytest.fixture
    def handler(self, mock_db_service, mock_cache_service):
        """创建处理器实例"""
        return ListDatasetsHandler(mock_db_service, mock_cache_service)
    
    @pytest.mark.unit
    def test_init(self, handler):
        """测试初始化"""
        assert handler.name == "list_datasets"
        assert handler.description == "列出可用的数据集"
        assert "source" in handler.input_schema["properties"]
        assert "category" in handler.input_schema["properties"]
    
    @pytest.mark.unit
    async def test_call_with_default_params(self, handler, mock_modelscope, mock_datasets):
        """测试使用默认参数调用"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'):
            
            result = await handler.call({})
            
            assert "datasets" in result
            assert isinstance(result["datasets"], list)
            assert "total" in result
            assert "sources" in result
    
    @pytest.mark.unit
    async def test_call_with_modelscope_source(self, handler, mock_modelscope):
        """测试指定ModelScope源"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'):
            
            result = await handler.call({"source": "modelscope"})
            
            assert "datasets" in result
            assert all(ds["source"] == "modelscope" for ds in result["datasets"])
    
    @pytest.mark.unit
    async def test_call_with_category_filter(self, handler, mock_modelscope, mock_datasets):
        """测试分类过滤"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'):
            
            result = await handler.call({"category": "nlp"})
            
            assert "datasets" in result
            # 验证过滤逻辑
    
    @pytest.mark.unit
    async def test_call_with_cache_hit(self, handler):
        """测试缓存命中"""
        cached_data = {
            "datasets": [{"name": "cached-dataset"}],
            "total": 1,
            "sources": ["cache"]
        }
        
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=cached_data):
            
            result = await handler.call({})
            
            assert result == cached_data
    
    @pytest.mark.unit
    def test_generate_cache_key(self, handler):
        """测试缓存键生成"""
        key1 = handler._get_cache_key({"source": "modelscope", "limit": 10})
        key2 = handler._get_cache_key({"source": "huggingface", "limit": 10})
        key3 = handler._get_cache_key({"source": "modelscope", "limit": 10})
        
        assert key1 != key2
        assert key1 == key3


class TestGetDatasetInfoHandler:
    """测试数据集信息获取工具"""
    
    @pytest.fixture
    def handler(self, mock_db_service, mock_cache_service):
        """创建处理器实例"""
        return GetDatasetInfoHandler(mock_db_service, mock_cache_service)
    
    @pytest.mark.unit
    def test_init(self, handler):
        """测试初始化"""
        assert handler.name == "get_dataset_info"
        assert handler.description == "获取指定数据集的详细信息"
        assert "dataset_name" in handler.input_schema["properties"]
        assert "source" in handler.input_schema["properties"]
    
    @pytest.mark.unit
    async def test_call_with_valid_dataset(self, handler, mock_modelscope):
        """测试获取有效数据集信息"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'):
            
            result = await handler.call({"dataset_name": "test-dataset-1"})
            
            assert "basic_info" in result
            assert "structure_info" in result
            assert "sample_preview" in result
            assert "statistics" in result
            assert "usage_suggestions" in result
    
    @pytest.mark.unit
    async def test_call_with_invalid_dataset(self, handler):
        """测试获取无效数据集信息"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None):
            
            with pytest.raises(Exception):
                await handler.call({"dataset_name": "non-existent-dataset"})
    
    @pytest.mark.unit
    async def test_call_with_subset(self, handler, mock_modelscope):
        """测试获取数据集子集信息"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'):
            
            result = await handler.call({
                "dataset_name": "test-dataset-1",
                "subset": "train"
            })
            
            assert "subset_info" in result


class TestFilterSamplesHandler:
    """测试样本过滤工具"""
    
    @pytest.fixture
    def handler(self, mock_db_service, mock_cache_service):
        """创建处理器实例"""
        return FilterSamplesHandler(mock_db_service, mock_cache_service)
    
    @pytest.mark.unit
    def test_init(self, handler):
        """测试初始化"""
        assert handler.name == "filter_samples"
        assert handler.description == "根据条件过滤数据集样本"
        assert "dataset_name" in handler.input_schema["properties"]
        assert "filters" in handler.input_schema["properties"]
    
    @pytest.mark.unit
    async def test_call_with_basic_filter(self, handler):
        """测试基本过滤"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_generate_mock_samples') as mock_gen:
            
            mock_gen.return_value = [
                {"id": 1, "text": "hello", "label": "positive"},
                {"id": 2, "text": "world", "label": "negative"}
            ]
            
            result = await handler.call({
                "dataset_name": "test-dataset",
                "filters": {"label": "positive"},
                "limit": 10
            })
            
            assert "samples" in result
            assert "total_count" in result
            assert "filtered_count" in result
    
    @pytest.mark.unit
    async def test_call_with_pagination(self, handler):
        """测试分页"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_generate_mock_samples') as mock_gen:
            
            mock_gen.return_value = [f"sample_{i}" for i in range(100)]
            
            result = await handler.call({
                "dataset_name": "test-dataset",
                "limit": 10,
                "offset": 20
            })
            
            assert len(result["samples"]) <= 10
            assert "pagination" in result
    
    @pytest.mark.unit
    async def test_call_with_sorting(self, handler):
        """测试排序"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_generate_mock_samples') as mock_gen:
            
            mock_gen.return_value = [
                {"id": 3, "score": 0.8},
                {"id": 1, "score": 0.9},
                {"id": 2, "score": 0.7}
            ]
            
            result = await handler.call({
                "dataset_name": "test-dataset",
                "sort_by": "score",
                "sort_order": "desc"
            })
            
            scores = [sample["score"] for sample in result["samples"]]
            assert scores == sorted(scores, reverse=True)
    
    @pytest.mark.unit
    def test_apply_filters(self, handler):
        """测试过滤逻辑"""
        samples = [
            {"label": "positive", "score": 0.8, "length": 10},
            {"label": "negative", "score": 0.6, "length": 15},
            {"label": "positive", "score": 0.9, "length": 8}
        ]
        
        # 测试等值过滤
        filtered = handler._apply_filters(samples, {"label": "positive"})
        assert len(filtered) == 2
        
        # 测试范围过滤
        filtered = handler._apply_filters(samples, {"score": {"gte": 0.7}})
        assert len(filtered) == 2
        
        # 测试组合过滤
        filtered = handler._apply_filters(samples, {
            "label": "positive",
            "score": {"gte": 0.85}
        })
        assert len(filtered) == 1


class TestQueryDatasetHandler:
    """测试数据集查询工具"""
    
    @pytest.fixture
    def handler(self, mock_db_service, mock_cache_service):
        """创建处理器实例"""
        return QueryDatasetHandler(mock_db_service, mock_cache_service)
    
    @pytest.mark.unit
    def test_init(self, handler):
        """测试初始化"""
        assert handler.name == "query_dataset"
        assert handler.description == "使用自然语言查询数据集"
        assert "query" in handler.input_schema["properties"]
    
    @pytest.mark.unit
    async def test_call_with_list_query(self, handler):
        """测试列表查询"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_parse_query') as mock_parse:
            
            mock_parse.return_value = {
                "type": "list",
                "intent": "list_datasets",
                "entities": {"category": "nlp"},
                "confidence": 0.9
            }
            
            result = await handler.call({"query": "列出所有NLP数据集"})
            
            assert "query_type" in result
            assert "results" in result
            assert "confidence" in result
    
    @pytest.mark.unit
    async def test_call_with_search_query(self, handler):
        """测试搜索查询"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_parse_query') as mock_parse:
            
            mock_parse.return_value = {
                "type": "search",
                "intent": "search_datasets",
                "entities": {"keywords": ["图像", "分类"]},
                "confidence": 0.8
            }
            
            result = await handler.call({"query": "搜索图像分类数据集"})
            
            assert result["query_type"] == "search"
    
    @pytest.mark.unit
    async def test_call_with_info_query(self, handler):
        """测试信息查询"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_parse_query') as mock_parse:
            
            mock_parse.return_value = {
                "type": "info",
                "intent": "get_dataset_info",
                "entities": {"dataset_name": "mnist"},
                "confidence": 0.95
            }
            
            result = await handler.call({"query": "获取MNIST数据集信息"})
            
            assert result["query_type"] == "info"
    
    @pytest.mark.unit
    async def test_call_with_filter_query(self, handler):
        """测试过滤查询"""
        with patch.object(handler, '_get_cache_key', return_value="test_key"), \
             patch.object(handler, '_get_from_cache', return_value=None), \
             patch.object(handler, '_set_cache'), \
             patch.object(handler, '_parse_query') as mock_parse:
            
            mock_parse.return_value = {
                "type": "filter",
                "intent": "filter_samples",
                "entities": {
                    "dataset_name": "test-dataset",
                    "filters": {"label": "positive"}
                },
                "confidence": 0.85
            }
            
            result = await handler.call({"query": "过滤test-dataset中标签为positive的样本"})
            
            assert result["query_type"] == "filter"
    
    @pytest.mark.unit
    def test_parse_query(self, handler):
        """测试查询解析"""
        # 测试列表查询
        parsed = handler._parse_query("列出所有数据集")
        assert parsed["type"] == "list"
        
        # 测试搜索查询
        parsed = handler._parse_query("搜索图像数据集")
        assert parsed["type"] == "search"
        
        # 测试信息查询
        parsed = handler._parse_query("获取MNIST信息")
        assert parsed["type"] == "info"
        
        # 测试过滤查询
        parsed = handler._parse_query("过滤正面样本")
        assert parsed["type"] == "filter"
    
    @pytest.mark.unit
    def test_update_query_history(self, handler):
        """测试查询历史更新"""
        initial_count = len(handler.query_history)
        
        handler._update_query_history("test query", "list", {"result": "success"})
        
        assert len(handler.query_history) == initial_count + 1
        assert handler.query_history[-1]["query"] == "test query"
        assert handler.query_history[-1]["type"] == "list"


@pytest.mark.integration
class TestToolsIntegration:
    """工具集成测试"""
    
    @pytest.mark.slow
    async def test_tools_workflow(self, mock_modelscope, mock_datasets, mock_db_service, mock_cache_service):
        """测试工具工作流"""
        # 1. 列出数据集
        list_handler = ListDatasetsHandler(mock_db_service, mock_cache_service)
        datasets_result = await list_handler.call({"category": "nlp"})
        assert "datasets" in datasets_result
        
        # 2. 获取第一个数据集的信息
        if datasets_result["datasets"]:
            dataset_name = datasets_result["datasets"][0]["name"]
            info_handler = GetDatasetInfoHandler(mock_db_service, mock_cache_service)
            info_result = await info_handler.call({"dataset_name": dataset_name})
            assert "basic_info" in info_result
            
            # 3. 过滤该数据集的样本
            filter_handler = FilterSamplesHandler(mock_db_service, mock_cache_service)
            filter_result = await filter_handler.call({
                "dataset_name": dataset_name,
                "limit": 5
            })
            assert "samples" in filter_result
    
    @pytest.mark.slow
    async def test_query_tool_integration(self, mock_db_service, mock_cache_service):
        """测试查询工具集成"""
        query_handler = QueryDatasetHandler(mock_db_service, mock_cache_service)
        
        # 测试不同类型的查询
        queries = [
            "列出所有NLP数据集",
            "搜索图像分类数据集",
            "获取MNIST数据集信息",
            "过滤正面情感样本"
        ]
        
        for query in queries:
            result = await query_handler.call({"query": query})
            assert "query_type" in result
            assert "results" in result
            assert "confidence" in result