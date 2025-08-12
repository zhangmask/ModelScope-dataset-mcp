"""环境配置

处理不同环境的配置。
"""

import os
from enum import Enum
from typing import Dict, Any, Optional
from pathlib import Path


class Environment(Enum):
    """环境类型枚举"""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig:
    """环境配置管理器"""
    
    def __init__(self, env: Environment = None):
        """初始化环境配置
        
        Args:
            env: 环境类型，如果为None则从环境变量获取
        """
        if env is None:
            env_str = os.getenv("ENVIRONMENT", "development").lower()
            try:
                self.environment = Environment(env_str)
            except ValueError:
                self.environment = Environment.DEVELOPMENT
        else:
            self.environment = env
        
        self._config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载环境特定的配置
        
        Returns:
            配置字典
        """
        base_config = {
            "debug": False,
            "testing": False,
            "database": {
                "echo": False,
                "pool_size": 5,
                "max_overflow": 10
            },
            "cache": {
                "enabled": True,
                "default_ttl": 3600
            },
            "logging": {
                "level": "INFO",
                "console_output": True,
                "file_output": True
            },
            "redis": {
                "host": "localhost",
                "port": 6379,
                "db": 0
            },
            "dataset": {
                "cache_enabled": True,
                "max_samples_per_request": 1000
            }
        }
        
        # 环境特定配置
        env_configs = {
            Environment.DEVELOPMENT: {
                "debug": True,
                "database": {
                    "echo": True,
                    "url": "sqlite:///./dev_modelscope_mcp.db"
                },
                "logging": {
                    "level": "DEBUG"
                },
                "redis": {
                    "db": 0
                }
            },
            Environment.TESTING: {
                "debug": True,
                "testing": True,
                "database": {
                    "echo": False,
                    "url": "sqlite:///:memory:"
                },
                "cache": {
                    "enabled": False
                },
                "logging": {
                    "level": "WARNING",
                    "console_output": False,
                    "file_output": False
                },
                "redis": {
                    "db": 1
                }
            },
            Environment.STAGING: {
                "debug": False,
                "database": {
                    "echo": False,
                    "pool_size": 10,
                    "max_overflow": 20
                },
                "logging": {
                    "level": "INFO"
                },
                "redis": {
                    "db": 2
                }
            },
            Environment.PRODUCTION: {
                "debug": False,
                "database": {
                    "echo": False,
                    "pool_size": 20,
                    "max_overflow": 50
                },
                "cache": {
                    "default_ttl": 7200  # 2小时
                },
                "logging": {
                    "level": "WARNING",
                    "json_format": True
                },
                "redis": {
                    "db": 0,
                    "connection_pool_max_connections": 100
                },
                "dataset": {
                    "max_samples_per_request": 500  # 生产环境限制更严格
                }
            }
        }
        
        # 合并配置
        config = base_config.copy()
        env_config = env_configs.get(self.environment, {})
        
        self._deep_merge(config, env_config)
        
        return config
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]):
        """深度合并字典
        
        Args:
            base: 基础字典
            override: 覆盖字典
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any):
        """设置配置值
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # 设置值
        config[keys[-1]] = value
    
    def is_development(self) -> bool:
        """是否为开发环境"""
        return self.environment == Environment.DEVELOPMENT
    
    def is_testing(self) -> bool:
        """是否为测试环境"""
        return self.environment == Environment.TESTING
    
    def is_staging(self) -> bool:
        """是否为预发布环境"""
        return self.environment == Environment.STAGING
    
    def is_production(self) -> bool:
        """是否为生产环境"""
        return self.environment == Environment.PRODUCTION
    
    def is_debug(self) -> bool:
        """是否启用调试模式"""
        return self.get('debug', False)
    
    def is_testing_mode(self) -> bool:
        """是否为测试模式"""
        return self.get('testing', False)
    
    def get_database_url(self) -> str:
        """获取数据库URL"""
        # 优先使用环境变量
        env_url = os.getenv('DATABASE_URL')
        if env_url:
            return env_url
        
        # 使用配置中的URL
        config_url = self.get('database.url')
        if config_url:
            return config_url
        
        # 默认URL
        if self.is_testing():
            return "sqlite:///:memory:"
        elif self.is_development():
            return "sqlite:///./dev_modelscope_mcp.db"
        else:
            return "sqlite:///./modelscope_mcp.db"
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置"""
        config = {
            "host": os.getenv('REDIS_HOST', self.get('redis.host', 'localhost')),
            "port": int(os.getenv('REDIS_PORT', str(self.get('redis.port', 6379)))),
            "db": int(os.getenv('REDIS_DB', str(self.get('redis.db', 0)))),
            "password": os.getenv('REDIS_PASSWORD', self.get('redis.password')),
        }
        
        # 移除None值
        return {k: v for k, v in config.items() if v is not None}
    
    def get_log_level(self) -> str:
        """获取日志级别"""
        return os.getenv('LOG_LEVEL', self.get('logging.level', 'INFO')).upper()
    
    def should_log_to_console(self) -> bool:
        """是否输出日志到控制台"""
        env_value = os.getenv('LOG_CONSOLE_OUTPUT')
        if env_value is not None:
            return env_value.lower() == 'true'
        return self.get('logging.console_output', True)
    
    def should_log_to_file(self) -> bool:
        """是否输出日志到文件"""
        env_value = os.getenv('LOG_FILE_OUTPUT')
        if env_value is not None:
            return env_value.lower() == 'true'
        return self.get('logging.file_output', True)
    
    def get_log_file_path(self) -> Optional[str]:
        """获取日志文件路径"""
        env_path = os.getenv('LOG_FILE_PATH')
        if env_path:
            return env_path
        
        if self.should_log_to_file():
            base_dir = Path.cwd()
            logs_dir = base_dir / "logs"
            logs_dir.mkdir(exist_ok=True)
            
            filename = f"modelscope_mcp_{self.environment.value}.log"
            return str(logs_dir / filename)
        
        return None
    
    def is_cache_enabled(self) -> bool:
        """是否启用缓存"""
        env_value = os.getenv('CACHE_ENABLED')
        if env_value is not None:
            return env_value.lower() == 'true'
        return self.get('cache.enabled', True)
    
    def get_cache_ttl(self) -> int:
        """获取缓存TTL"""
        env_value = os.getenv('CACHE_DEFAULT_TTL')
        if env_value:
            return int(env_value)
        return self.get('cache.default_ttl', 3600)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "environment": self.environment.value,
            "config": self._config.copy()
        }


# 全局环境配置实例
_environment_config: Optional[EnvironmentConfig] = None


def get_environment() -> EnvironmentConfig:
    """获取全局环境配置实例
    
    Returns:
        环境配置实例
    """
    global _environment_config
    
    if _environment_config is None:
        _environment_config = EnvironmentConfig()
    
    return _environment_config


def reload_environment() -> EnvironmentConfig:
    """重新加载环境配置
    
    Returns:
        新的环境配置实例
    """
    global _environment_config
    
    _environment_config = EnvironmentConfig()
    
    return _environment_config


def set_environment(env: Environment) -> EnvironmentConfig:
    """设置环境
    
    Args:
        env: 环境类型
        
    Returns:
        环境配置实例
    """
    global _environment_config
    
    _environment_config = EnvironmentConfig(env)
    
    return _environment_config