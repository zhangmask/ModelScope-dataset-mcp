"""测试配置

Pytest配置和共享fixtures。
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from typing import Generator, Dict, Any

# 设置测试环境
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["CACHE_ENABLED"] = "false"
os.environ["LOG_LEVEL"] = "WARNING"


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """临时目录fixture"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    with patch('redis.Redis') as mock_redis_class:
        mock_client = Mock()
        mock_redis_class.return_value = mock_client
        
        # 模拟Redis方法
        mock_client.ping.return_value = True
        mock_client.get.return_value = None
        mock_client.set.return_value = True
        mock_client.delete.return_value = 1
        mock_client.exists.return_value = False
        mock_client.ttl.return_value = -1
        mock_client.keys.return_value = []
        
        yield mock_client


@pytest.fixture
def mock_modelscope():
    """Mock ModelScope库"""
    with patch('modelscope.hub.api.HubApi') as mock_hub:
        mock_api = Mock()
        mock_hub.return_value = mock_api
        
        # 模拟数据集列表
        mock_api.list_datasets.return_value = {
            'Data': [
                {
                    'Name': 'test-dataset-1',
                    'Description': '测试数据集1',
                    'Tags': ['nlp', 'text'],
                    'Downloads': 100,
                    'CreatedTime': '2024-01-01T00:00:00Z'
                },
                {
                    'Name': 'test-dataset-2',
                    'Description': '测试数据集2',
                    'Tags': ['cv', 'image'],
                    'Downloads': 200,
                    'CreatedTime': '2024-01-02T00:00:00Z'
                }
            ],
            'TotalCount': 2
        }
        
        # 模拟数据集详情
        mock_api.get_dataset.return_value = {
            'Name': 'test-dataset-1',
            'Description': '测试数据集1',
            'Tags': ['nlp', 'text'],
            'Downloads': 100,
            'CreatedTime': '2024-01-01T00:00:00Z',
            'Files': [
                {'Path': 'train.json', 'Size': 1024},
                {'Path': 'test.json', 'Size': 512}
            ]
        }
        
        yield mock_api


@pytest.fixture
def mock_datasets():
    """Mock Hugging Face datasets库"""
    with patch('datasets.list_datasets') as mock_list, \
         patch('datasets.load_dataset_builder') as mock_builder:
        
        # 模拟数据集列表
        mock_list.return_value = [
            'hf-dataset-1',
            'hf-dataset-2'
        ]
        
        # 模拟数据集构建器
        mock_builder_instance = Mock()
        mock_builder_instance.info.description = '测试HF数据集'
        mock_builder_instance.info.features = {'text': 'string', 'label': 'int'}
        mock_builder_instance.info.splits = {'train': Mock(num_examples=1000)}
        mock_builder.return_value = mock_builder_instance
        
        yield mock_list, mock_builder


@pytest.fixture
def sample_config() -> Dict[str, Any]:
    """示例配置"""
    return {
        "environment": "testing",
        "debug": True,
        "database": {
            "url": "sqlite:///:memory:",
            "echo": False
        },
        "cache": {
            "enabled": False
        },
        "logging": {
            "level": "WARNING",
            "console_output": False
        },
        "mcp": {
            "name": "test-mcp",
            "version": "1.0.0"
        }
    }


@pytest.fixture
def sample_datasets():
    """示例数据集数据"""
    return [
        {
            "name": "test-dataset-1",
            "description": "测试数据集1",
            "source": "modelscope",
            "tags": ["nlp", "text"],
            "downloads": 100,
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "name": "test-dataset-2",
            "description": "测试数据集2",
            "source": "huggingface",
            "tags": ["cv", "image"],
            "downloads": 200,
            "created_at": "2024-01-02T00:00:00Z"
        }
    ]


@pytest.fixture
def sample_queries():
    """示例查询数据"""
    return [
        {
            "query": "列出所有NLP数据集",
            "intent": "list_datasets",
            "entities": {"category": "nlp"}
        },
        {
            "query": "搜索图像分类数据集",
            "intent": "search_datasets",
            "entities": {"task": "image_classification"}
        },
        {
            "query": "获取MNIST数据集信息",
            "intent": "get_dataset_info",
            "entities": {"dataset_name": "mnist"}
        }
    ]


@pytest.fixture
def mock_mcp_server():
    """Mock MCP服务器"""
    with patch('mcp.server.Server') as mock_server_class:
        mock_server = Mock()
        mock_server_class.return_value = mock_server
        
        # 模拟服务器方法
        mock_server.list_tools.return_value = []
        mock_server.call_tool.return_value = {"result": "success"}
        
        yield mock_server


@pytest.fixture(autouse=True)
def reset_singletons():
    """重置单例实例"""
    # 在每个测试前重置全局实例
    from src.modelscope_mcp.config.settings import _settings
    from src.modelscope_mcp.config.environment import _environment_config
    from src.modelscope_mcp.config.config_manager import _config_manager
    from src.modelscope_mcp.utils.logging import _logger_manager
    
    # 清除全局实例
    import src.modelscope_mcp.config.settings as settings_module
    import src.modelscope_mcp.config.environment as env_module
    import src.modelscope_mcp.config.config_manager as config_module
    import src.modelscope_mcp.utils.logging as logging_module
    
    settings_module._settings = None
    env_module._environment_config = None
    config_module._config_manager = None
    logging_module._logger_manager = None
    
    yield
    
    # 测试后清理
    settings_module._settings = None
    env_module._environment_config = None
    config_module._config_manager = None
    logging_module._logger_manager = None


# 测试标记
pytest_plugins = []


def pytest_configure(config):
    """Pytest配置"""
    config.addinivalue_line(
        "markers", "unit: 单元测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "external: 需要外部依赖的测试"
    )


def pytest_collection_modifyitems(config, items):
    """修改测试收集"""
    # 为没有标记的测试添加unit标记
    for item in items:
        if not any(item.iter_markers()):
            item.add_marker(pytest.mark.unit)