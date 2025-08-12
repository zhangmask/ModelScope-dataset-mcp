"""配置管理器

统一管理应用程序配置。
"""

import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from .settings import Settings, get_settings
from .environment import EnvironmentConfig, get_environment


class ConfigManager:
    """配置管理器
    
    统一管理应用程序的所有配置，支持从多种来源加载配置。
    """
    
    def __init__(self, config_file: Optional[Union[str, Path]] = None):
        """初始化配置管理器
        
        Args:
            config_file: 配置文件路径
        """
        self._settings = get_settings()
        self._environment = get_environment()
        self._config_file = Path(config_file) if config_file else None
        self._file_config: Dict[str, Any] = {}
        
        # 加载文件配置
        if self._config_file and self._config_file.exists():
            self._load_config_file()
    
    def _load_config_file(self):
        """加载配置文件"""
        if not self._config_file or not self._config_file.exists():
            return
        
        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                if self._config_file.suffix.lower() in ['.yml', '.yaml']:
                    self._file_config = yaml.safe_load(f) or {}
                elif self._config_file.suffix.lower() == '.json':
                    self._file_config = json.load(f)
                else:
                    # 尝试作为JSON解析
                    content = f.read()
                    self._file_config = json.loads(content)
        except Exception as e:
            print(f"警告：无法加载配置文件 {self._config_file}: {e}")
            self._file_config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值
        
        优先级：环境变量 > 文件配置 > 环境配置 > 默认设置
        
        Args:
            key: 配置键，支持点号分隔的嵌套键
            default: 默认值
            
        Returns:
            配置值
        """
        # 1. 检查环境变量
        env_key = key.upper().replace('.', '_')
        env_value = os.getenv(env_key)
        if env_value is not None:
            return self._convert_env_value(env_value)
        
        # 2. 检查文件配置
        file_value = self._get_nested_value(self._file_config, key)
        if file_value is not None:
            return file_value
        
        # 3. 检查环境配置
        env_value = self._environment.get(key)
        if env_value is not None:
            return env_value
        
        # 4. 检查默认设置
        settings_value = self._get_settings_value(key)
        if settings_value is not None:
            return settings_value
        
        return default
    
    def set(self, key: str, value: Any, persist: bool = False):
        """设置配置值
        
        Args:
            key: 配置键
            value: 配置值
            persist: 是否持久化到文件
        """
        # 设置到环境配置
        self._environment.set(key, value)
        
        # 如果需要持久化
        if persist and self._config_file:
            self._set_nested_value(self._file_config, key, value)
            self._save_config_file()
    
    def _convert_env_value(self, value: str) -> Any:
        """转换环境变量值
        
        Args:
            value: 环境变量值
            
        Returns:
            转换后的值
        """
        # 布尔值
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # 数字
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        # JSON
        if value.startswith(('{', '[')):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass
        
        # 字符串
        return value
    
    def _get_nested_value(self, data: Dict[str, Any], key: str) -> Any:
        """获取嵌套字典值
        
        Args:
            data: 数据字典
            key: 键，支持点号分隔
            
        Returns:
            值或None
        """
        keys = key.split('.')
        value = data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return None
    
    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """设置嵌套字典值
        
        Args:
            data: 数据字典
            key: 键，支持点号分隔
            value: 值
        """
        keys = key.split('.')
        current = data
        
        # 导航到最后一级
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        
        # 设置值
        current[keys[-1]] = value
    
    def _get_settings_value(self, key: str) -> Any:
        """从设置对象获取值
        
        Args:
            key: 配置键
            
        Returns:
            值或None
        """
        try:
            keys = key.split('.')
            value = self._settings
            
            for k in keys:
                if hasattr(value, k):
                    value = getattr(value, k)
                else:
                    return None
            
            return value
        except Exception:
            return None
    
    def _save_config_file(self):
        """保存配置文件"""
        if not self._config_file:
            return
        
        try:
            # 确保目录存在
            self._config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self._config_file, 'w', encoding='utf-8') as f:
                if self._config_file.suffix.lower() in ['.yml', '.yaml']:
                    yaml.dump(self._file_config, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(self._file_config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"警告：无法保存配置文件 {self._config_file}: {e}")
    
    def reload(self):
        """重新加载配置"""
        # 重新加载设置和环境
        from .settings import reload_settings
        from .environment import reload_environment
        
        self._settings = reload_settings()
        self._environment = reload_environment()
        
        # 重新加载文件配置
        if self._config_file and self._config_file.exists():
            self._load_config_file()
    
    def get_database_config(self) -> Dict[str, Any]:
        """获取数据库配置
        
        Returns:
            数据库配置字典
        """
        return {
            "url": self.get("database.url", self._environment.get_database_url()),
            "echo": self.get("database.echo", False),
            "pool_size": self.get("database.pool_size", 5),
            "max_overflow": self.get("database.max_overflow", 10),
            "pool_timeout": self.get("database.pool_timeout", 30),
            "pool_recycle": self.get("database.pool_recycle", 3600)
        }
    
    def get_redis_config(self) -> Dict[str, Any]:
        """获取Redis配置
        
        Returns:
            Redis配置字典
        """
        env_config = self._environment.get_redis_config()
        
        return {
            "host": self.get("redis.host", env_config.get("host", "localhost")),
            "port": self.get("redis.port", env_config.get("port", 6379)),
            "db": self.get("redis.db", env_config.get("db", 0)),
            "password": self.get("redis.password", env_config.get("password")),
            "socket_timeout": self.get("redis.socket_timeout", 5.0),
            "socket_connect_timeout": self.get("redis.socket_connect_timeout", 5.0),
            "socket_keepalive": self.get("redis.socket_keepalive", True),
            "connection_pool_max_connections": self.get("redis.connection_pool_max_connections", 50),
            "retry_on_timeout": self.get("redis.retry_on_timeout", True),
            "health_check_interval": self.get("redis.health_check_interval", 30)
        }
    
    def get_cache_config(self) -> Dict[str, Any]:
        """获取缓存配置
        
        Returns:
            缓存配置字典
        """
        return {
            "enabled": self.get("cache.enabled", self._environment.is_cache_enabled()),
            "default_ttl": self.get("cache.default_ttl", self._environment.get_cache_ttl()),
            "max_memory_size": self.get("cache.max_memory_size", 100 * 1024 * 1024),
            "max_memory_entries": self.get("cache.max_memory_entries", 10000),
            "cleanup_interval": self.get("cache.cleanup_interval", 300),
            "eviction_policy": self.get("cache.eviction_policy", "lru")
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """获取日志配置
        
        Returns:
            日志配置字典
        """
        return {
            "level": self.get("logging.level", self._environment.get_log_level()),
            "format": self.get("logging.format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            "file_path": self.get("logging.file_path", self._environment.get_log_file_path()),
            "max_file_size": self.get("logging.max_file_size", 10 * 1024 * 1024),
            "backup_count": self.get("logging.backup_count", 5),
            "console_output": self.get("logging.console_output", self._environment.should_log_to_console()),
            "json_format": self.get("logging.json_format", False)
        }
    
    def get_mcp_config(self) -> Dict[str, Any]:
        """获取MCP配置
        
        Returns:
            MCP配置字典
        """
        return {
            "name": self.get("mcp.name", "modelscope-dataset-mcp"),
            "version": self.get("mcp.version", "1.0.0"),
            "description": self.get("mcp.description", "ModelScope数据集即时查询MCP服务器"),
            "max_request_size": self.get("mcp.max_request_size", 10 * 1024 * 1024),
            "request_timeout": self.get("mcp.request_timeout", 30.0),
            "max_concurrent_requests": self.get("mcp.max_concurrent_requests", 100)
        }
    
    def get_dataset_config(self) -> Dict[str, Any]:
        """获取数据集配置
        
        Returns:
            数据集配置字典
        """
        return {
            "modelscope_enabled": self.get("dataset.modelscope_enabled", True),
            "huggingface_enabled": self.get("dataset.huggingface_enabled", True),
            "cache_enabled": self.get("dataset.cache_enabled", True),
            "max_samples_per_request": self.get("dataset.max_samples_per_request", 1000),
            "default_page_size": self.get("dataset.default_page_size", 50),
            "max_page_size": self.get("dataset.max_page_size", 500),
            "search_timeout": self.get("dataset.search_timeout", 10.0)
        }
    
    def get_nlp_config(self) -> Dict[str, Any]:
        """获取NLP配置
        
        Returns:
            NLP配置字典
        """
        return {
            "enabled": self.get("nlp.enabled", True),
            "confidence_threshold": self.get("nlp.confidence_threshold", 0.6),
            "max_query_length": self.get("nlp.max_query_length", 1000),
            "cache_parsed_queries": self.get("nlp.cache_parsed_queries", True)
        }
    
    def is_debug(self) -> bool:
        """是否为调试模式"""
        return self.get("debug", self._environment.is_debug())
    
    def is_testing(self) -> bool:
        """是否为测试模式"""
        return self.get("testing", self._environment.is_testing_mode())
    
    def get_environment_name(self) -> str:
        """获取环境名称"""
        return self._environment.environment.value
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典
        
        Returns:
            配置字典
        """
        return {
            "environment": self.get_environment_name(),
            "debug": self.is_debug(),
            "testing": self.is_testing(),
            "database": self.get_database_config(),
            "redis": self.get_redis_config(),
            "cache": self.get_cache_config(),
            "logging": self.get_logging_config(),
            "mcp": self.get_mcp_config(),
            "dataset": self.get_dataset_config(),
            "nlp": self.get_nlp_config()
        }


# 全局配置管理器实例
_config_manager: Optional[ConfigManager] = None


def get_config_manager(config_file: Optional[Union[str, Path]] = None) -> ConfigManager:
    """获取全局配置管理器实例
    
    Args:
        config_file: 配置文件路径
        
    Returns:
        配置管理器实例
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager(config_file)
    
    return _config_manager


def reload_config_manager() -> ConfigManager:
    """重新加载配置管理器
    
    Returns:
        新的配置管理器实例
    """
    global _config_manager
    
    if _config_manager:
        _config_manager.reload()
    else:
        _config_manager = ConfigManager()
    
    return _config_manager