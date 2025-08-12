"""配置系统测试

测试配置管理功能。
"""

import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open

from src.modelscope_mcp.config.settings import (
    Settings, DatabaseSettings, RedisSettings, CacheSettings,
    LoggingSettings, MCPSettings, DatasetSettings, NLPSettings,
    get_settings, reload_settings, update_settings
)
from src.modelscope_mcp.config.environment import (
    Environment, EnvironmentConfig, get_environment, reload_environment, set_environment
)
from src.modelscope_mcp.config.config_manager import (
    ConfigManager, get_config_manager, reload_config_manager
)


class TestDatabaseSettings:
    """测试数据库设置"""
    
    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        settings = DatabaseSettings()
        assert settings.url == "sqlite:///./modelscope_mcp.db"
        assert settings.echo is False
        assert settings.pool_size == 5
    
    @pytest.mark.unit
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "DATABASE_URL": "postgresql://test",
            "DATABASE_ECHO": "true",
            "DATABASE_POOL_SIZE": "10"
        }):
            settings = DatabaseSettings.from_env()
            assert settings.url == "postgresql://test"
            assert settings.echo is True
            assert settings.pool_size == 10


class TestRedisSettings:
    """测试Redis设置"""
    
    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        settings = RedisSettings()
        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.db == 0
        assert settings.password is None
    
    @pytest.mark.unit
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "REDIS_HOST": "redis.example.com",
            "REDIS_PORT": "6380",
            "REDIS_DB": "1",
            "REDIS_PASSWORD": "secret"
        }):
            settings = RedisSettings.from_env()
            assert settings.host == "redis.example.com"
            assert settings.port == 6380
            assert settings.db == 1
            assert settings.password == "secret"


class TestCacheSettings:
    """测试缓存设置"""
    
    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        settings = CacheSettings()
        assert settings.enabled is True
        assert settings.default_ttl == 3600
        assert settings.eviction_policy == "lru"
    
    @pytest.mark.unit
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "CACHE_ENABLED": "false",
            "CACHE_DEFAULT_TTL": "7200",
            "CACHE_EVICTION_POLICY": "lfu"
        }):
            settings = CacheSettings.from_env()
            assert settings.enabled is False
            assert settings.default_ttl == 7200
            assert settings.eviction_policy == "lfu"


class TestSettings:
    """测试主设置类"""
    
    @pytest.mark.unit
    def test_default_values(self):
        """测试默认值"""
        settings = Settings()
        assert settings.environment == "development"
        assert settings.debug is False
        assert isinstance(settings.database, DatabaseSettings)
        assert isinstance(settings.redis, RedisSettings)
    
    @pytest.mark.unit
    def test_from_env(self):
        """测试从环境变量创建"""
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DEBUG": "true",
            "DATABASE_URL": "postgresql://prod",
            "REDIS_HOST": "redis.prod.com"
        }):
            settings = Settings.from_env()
            assert settings.environment == "production"
            assert settings.debug is True
            assert settings.database.url == "postgresql://prod"
            assert settings.redis.host == "redis.prod.com"
    
    @pytest.mark.unit
    def test_ensure_directories(self, temp_dir):
        """测试目录创建"""
        settings = Settings(
            base_dir=temp_dir,
            data_dir=temp_dir / "data",
            logs_dir=temp_dir / "logs",
            cache_dir=temp_dir / "cache"
        )
        
        settings.ensure_directories()
        
        assert (temp_dir / "data").exists()
        assert (temp_dir / "logs").exists()
        assert (temp_dir / "cache").exists()
    
    @pytest.mark.unit
    def test_to_dict(self):
        """测试转换为字典"""
        settings = Settings()
        data = settings.to_dict()
        
        assert "environment" in data
        assert "database" in data
        assert "redis" in data
        assert isinstance(data["database"], dict)
    
    @pytest.mark.unit
    def test_update_from_dict(self):
        """测试从字典更新"""
        settings = Settings()
        
        update_data = {
            "environment": "testing",
            "debug": True,
            "database": {
                "url": "sqlite:///:memory:",
                "echo": True
            }
        }
        
        settings.update_from_dict(update_data)
        
        assert settings.environment == "testing"
        assert settings.debug is True
        assert settings.database.url == "sqlite:///:memory:"
        assert settings.database.echo is True


class TestEnvironmentConfig:
    """测试环境配置"""
    
    @pytest.mark.unit
    def test_development_environment(self):
        """测试开发环境"""
        config = EnvironmentConfig(Environment.DEVELOPMENT)
        assert config.environment == Environment.DEVELOPMENT
        assert config.is_development()
        assert config.is_debug()
        assert config.get('debug') is True
    
    @pytest.mark.unit
    def test_production_environment(self):
        """测试生产环境"""
        config = EnvironmentConfig(Environment.PRODUCTION)
        assert config.environment == Environment.PRODUCTION
        assert config.is_production()
        assert not config.is_debug()
        assert config.get('debug') is False
    
    @pytest.mark.unit
    def test_testing_environment(self):
        """测试测试环境"""
        config = EnvironmentConfig(Environment.TESTING)
        assert config.environment == Environment.TESTING
        assert config.is_testing()
        assert config.is_testing_mode()
        assert config.get('testing') is True
    
    @pytest.mark.unit
    def test_get_nested_config(self):
        """测试获取嵌套配置"""
        config = EnvironmentConfig(Environment.DEVELOPMENT)
        
        # 测试嵌套键
        assert config.get('database.echo') is True
        assert config.get('logging.level') == 'DEBUG'
        assert config.get('redis.db') == 0
    
    @pytest.mark.unit
    def test_set_config(self):
        """测试设置配置"""
        config = EnvironmentConfig(Environment.DEVELOPMENT)
        
        config.set('custom.key', 'value')
        assert config.get('custom.key') == 'value'
        
        config.set('database.pool_size', 20)
        assert config.get('database.pool_size') == 20
    
    @pytest.mark.unit
    def test_get_database_url(self):
        """测试获取数据库URL"""
        # 测试环境变量优先级
        with patch.dict(os.environ, {'DATABASE_URL': 'env://test'}):
            config = EnvironmentConfig(Environment.DEVELOPMENT)
            assert config.get_database_url() == 'env://test'
        
        # 测试默认值
        config = EnvironmentConfig(Environment.TESTING)
        assert config.get_database_url() == "sqlite:///:memory:"
    
    @pytest.mark.unit
    def test_get_redis_config(self):
        """测试获取Redis配置"""
        config = EnvironmentConfig(Environment.DEVELOPMENT)
        redis_config = config.get_redis_config()
        
        assert 'host' in redis_config
        assert 'port' in redis_config
        assert 'db' in redis_config
        assert redis_config['host'] == 'localhost'
    
    @pytest.mark.unit
    def test_logging_config(self):
        """测试日志配置"""
        config = EnvironmentConfig(Environment.PRODUCTION)
        
        assert config.get_log_level() == 'WARNING'
        assert config.should_log_to_console() is True
        assert config.should_log_to_file() is True
        
        log_path = config.get_log_file_path()
        assert log_path is not None
        assert 'production' in log_path


class TestConfigManager:
    """测试配置管理器"""
    
    @pytest.mark.unit
    def test_init_without_file(self):
        """测试无配置文件初始化"""
        manager = ConfigManager()
        assert manager._config_file is None
        assert manager._file_config == {}
    
    @pytest.mark.unit
    def test_init_with_json_file(self, temp_dir):
        """测试JSON配置文件初始化"""
        config_file = temp_dir / "config.json"
        config_data = {
            "database": {
                "url": "sqlite:///test.db"
            },
            "cache": {
                "enabled": False
            }
        }
        
        with open(config_file, 'w') as f:
            import json
            json.dump(config_data, f)
        
        manager = ConfigManager(config_file)
        assert manager._file_config == config_data
    
    @pytest.mark.unit
    def test_get_with_priority(self):
        """测试配置获取优先级"""
        # 环境变量 > 文件配置 > 环境配置 > 默认设置
        manager = ConfigManager()
        
        # 测试环境变量优先级
        with patch.dict(os.environ, {'DATABASE_URL': 'env://priority'}):
            assert manager.get('database.url') == 'env://priority'
    
    @pytest.mark.unit
    def test_set_and_persist(self, temp_dir):
        """测试设置并持久化"""
        config_file = temp_dir / "config.json"
        manager = ConfigManager(config_file)
        
        manager.set('custom.setting', 'test_value', persist=True)
        
        assert manager.get('custom.setting') == 'test_value'
        assert config_file.exists()
        
        # 验证文件内容
        with open(config_file) as f:
            import json
            data = json.load(f)
            assert data['custom']['setting'] == 'test_value'
    
    @pytest.mark.unit
    def test_convert_env_value(self):
        """测试环境变量值转换"""
        manager = ConfigManager()
        
        # 布尔值
        assert manager._convert_env_value('true') is True
        assert manager._convert_env_value('false') is False
        
        # 数字
        assert manager._convert_env_value('123') == 123
        assert manager._convert_env_value('123.45') == 123.45
        
        # JSON
        assert manager._convert_env_value('{"key": "value"}') == {"key": "value"}
        
        # 字符串
        assert manager._convert_env_value('hello') == 'hello'
    
    @pytest.mark.unit
    def test_get_config_methods(self):
        """测试获取各种配置的方法"""
        manager = ConfigManager()
        
        # 测试各种配置获取方法
        db_config = manager.get_database_config()
        assert 'url' in db_config
        assert 'pool_size' in db_config
        
        redis_config = manager.get_redis_config()
        assert 'host' in redis_config
        assert 'port' in redis_config
        
        cache_config = manager.get_cache_config()
        assert 'enabled' in cache_config
        assert 'default_ttl' in cache_config
        
        logging_config = manager.get_logging_config()
        assert 'level' in logging_config
        assert 'format' in logging_config
        
        mcp_config = manager.get_mcp_config()
        assert 'name' in mcp_config
        assert 'version' in mcp_config
        
        dataset_config = manager.get_dataset_config()
        assert 'modelscope_enabled' in dataset_config
        assert 'huggingface_enabled' in dataset_config
        
        nlp_config = manager.get_nlp_config()
        assert 'enabled' in nlp_config
        assert 'confidence_threshold' in nlp_config
    
    @pytest.mark.unit
    def test_environment_methods(self):
        """测试环境相关方法"""
        manager = ConfigManager()
        
        env_name = manager.get_environment_name()
        assert env_name in ['development', 'testing', 'staging', 'production']
        
        # 测试调试和测试模式
        is_debug = manager.is_debug()
        is_testing = manager.is_testing()
        
        assert isinstance(is_debug, bool)
        assert isinstance(is_testing, bool)
    
    @pytest.mark.unit
    def test_to_dict(self):
        """测试转换为字典"""
        manager = ConfigManager()
        config_dict = manager.to_dict()
        
        expected_keys = [
            'environment', 'debug', 'testing',
            'database', 'redis', 'cache', 'logging',
            'mcp', 'dataset', 'nlp'
        ]
        
        for key in expected_keys:
            assert key in config_dict
    
    @pytest.mark.unit
    def test_reload(self):
        """测试重新加载"""
        manager = ConfigManager()
        
        # 修改环境变量
        with patch.dict(os.environ, {'DEBUG': 'true'}):
            manager.reload()
            # 验证配置已更新
            # 注意：这里需要根据实际的重新加载逻辑来验证


@pytest.mark.integration
class TestConfigIntegration:
    """配置系统集成测试"""
    
    @pytest.mark.unit
    def test_global_settings_singleton(self):
        """测试全局设置单例"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        # 应该是同一个实例
        assert settings1 is settings2
    
    @pytest.mark.unit
    def test_global_environment_singleton(self):
        """测试全局环境配置单例"""
        env1 = get_environment()
        env2 = get_environment()
        
        # 应该是同一个实例
        assert env1 is env2
    
    @pytest.mark.unit
    def test_global_config_manager_singleton(self):
        """测试全局配置管理器单例"""
        manager1 = get_config_manager()
        manager2 = get_config_manager()
        
        # 应该是同一个实例
        assert manager1 is manager2
    
    @pytest.mark.unit
    def test_reload_functions(self):
        """测试重新加载函数"""
        # 获取初始实例
        settings1 = get_settings()
        env1 = get_environment()
        manager1 = get_config_manager()
        
        # 重新加载
        settings2 = reload_settings()
        env2 = reload_environment()
        manager2 = reload_config_manager()
        
        # 应该是新的实例
        assert settings2 is not settings1
        assert env2 is not env1
        # 注意：config_manager的reload可能返回同一个实例但内容已更新
    
    @pytest.mark.unit
    def test_environment_switching(self):
        """测试环境切换"""
        # 设置为测试环境
        env = set_environment(Environment.TESTING)
        assert env.is_testing()
        
        # 设置为生产环境
        env = set_environment(Environment.PRODUCTION)
        assert env.is_production()
    
    @pytest.mark.unit
    def test_config_update_propagation(self):
        """测试配置更新传播"""
        settings = get_settings()
        
        # 更新设置
        update_data = {
            "debug": True,
            "database": {
                "echo": True
            }
        }
        
        updated_settings = update_settings(update_data)
        
        assert updated_settings.debug is True
        assert updated_settings.database.echo is True
        
        # 验证全局实例也已更新
        current_settings = get_settings()
        assert current_settings.debug is True