"""应用程序设置

定义应用程序的配置设置。
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DatabaseSettings:
    """数据库设置"""
    url: str = "sqlite:///./modelscope_mcp.db"
    echo: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    @classmethod
    def from_env(cls) -> "DatabaseSettings":
        """从环境变量创建数据库设置"""
        return cls(
            url=os.getenv("DATABASE_URL", "sqlite:///./modelscope_mcp.db"),
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true",
            pool_size=int(os.getenv("DATABASE_POOL_SIZE", "5")),
            max_overflow=int(os.getenv("DATABASE_MAX_OVERFLOW", "10")),
            pool_timeout=int(os.getenv("DATABASE_POOL_TIMEOUT", "30")),
            pool_recycle=int(os.getenv("DATABASE_POOL_RECYCLE", "3600"))
        )


@dataclass
class RedisSettings:
    """Redis设置"""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    socket_keepalive: bool = True
    socket_keepalive_options: Dict[str, Any] = field(default_factory=dict)
    connection_pool_max_connections: int = 50
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    @classmethod
    def from_env(cls) -> "RedisSettings":
        """从环境变量创建Redis设置"""
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
            socket_timeout=float(os.getenv("REDIS_SOCKET_TIMEOUT", "5.0")),
            socket_connect_timeout=float(os.getenv("REDIS_SOCKET_CONNECT_TIMEOUT", "5.0")),
            socket_keepalive=os.getenv("REDIS_SOCKET_KEEPALIVE", "true").lower() == "true",
            connection_pool_max_connections=int(os.getenv("REDIS_CONNECTION_POOL_MAX_CONNECTIONS", "50")),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30"))
        )


@dataclass
class CacheSettings:
    """缓存设置"""
    enabled: bool = True
    default_ttl: int = 3600  # 1小时
    max_memory_size: int = 100 * 1024 * 1024  # 100MB
    max_memory_entries: int = 10000
    cleanup_interval: int = 300  # 5分钟
    eviction_policy: str = "lru"  # lru, lfu, ttl, fifo, random
    
    @classmethod
    def from_env(cls) -> "CacheSettings":
        """从环境变量创建缓存设置"""
        return cls(
            enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
            default_ttl=int(os.getenv("CACHE_DEFAULT_TTL", "3600")),
            max_memory_size=int(os.getenv("CACHE_MAX_MEMORY_SIZE", str(100 * 1024 * 1024))),
            max_memory_entries=int(os.getenv("CACHE_MAX_MEMORY_ENTRIES", "10000")),
            cleanup_interval=int(os.getenv("CACHE_CLEANUP_INTERVAL", "300")),
            eviction_policy=os.getenv("CACHE_EVICTION_POLICY", "lru")
        )


@dataclass
class LoggingSettings:
    """日志设置"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file_path: Optional[str] = None
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5
    console_output: bool = True
    json_format: bool = False
    
    @classmethod
    def from_env(cls) -> "LoggingSettings":
        """从环境变量创建日志设置"""
        return cls(
            level=os.getenv("LOG_LEVEL", "INFO").upper(),
            format=os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_file_size=int(os.getenv("LOG_MAX_FILE_SIZE", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5")),
            console_output=os.getenv("LOG_CONSOLE_OUTPUT", "true").lower() == "true",
            json_format=os.getenv("LOG_JSON_FORMAT", "false").lower() == "true"
        )


@dataclass
class MCPSettings:
    """MCP服务器设置"""
    name: str = "modelscope-dataset-mcp"
    version: str = "1.0.0"
    description: str = "ModelScope数据集即时查询MCP服务器"
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    request_timeout: float = 30.0
    max_concurrent_requests: int = 100
    
    @classmethod
    def from_env(cls) -> "MCPSettings":
        """从环境变量创建MCP设置"""
        return cls(
            name=os.getenv("MCP_NAME", "modelscope-dataset-mcp"),
            version=os.getenv("MCP_VERSION", "1.0.0"),
            description=os.getenv("MCP_DESCRIPTION", "ModelScope数据集即时查询MCP服务器"),
            max_request_size=int(os.getenv("MCP_MAX_REQUEST_SIZE", str(10 * 1024 * 1024))),
            request_timeout=float(os.getenv("MCP_REQUEST_TIMEOUT", "30.0")),
            max_concurrent_requests=int(os.getenv("MCP_MAX_CONCURRENT_REQUESTS", "100"))
        )


@dataclass
class DatasetSettings:
    """数据集设置"""
    modelscope_enabled: bool = True
    huggingface_enabled: bool = True
    cache_enabled: bool = True
    max_samples_per_request: int = 1000
    default_page_size: int = 50
    max_page_size: int = 500
    search_timeout: float = 10.0
    
    @classmethod
    def from_env(cls) -> "DatasetSettings":
        """从环境变量创建数据集设置"""
        return cls(
            modelscope_enabled=os.getenv("DATASET_MODELSCOPE_ENABLED", "true").lower() == "true",
            huggingface_enabled=os.getenv("DATASET_HUGGINGFACE_ENABLED", "true").lower() == "true",
            cache_enabled=os.getenv("DATASET_CACHE_ENABLED", "true").lower() == "true",
            max_samples_per_request=int(os.getenv("DATASET_MAX_SAMPLES_PER_REQUEST", "1000")),
            default_page_size=int(os.getenv("DATASET_DEFAULT_PAGE_SIZE", "50")),
            max_page_size=int(os.getenv("DATASET_MAX_PAGE_SIZE", "500")),
            search_timeout=float(os.getenv("DATASET_SEARCH_TIMEOUT", "10.0"))
        )


@dataclass
class NLPSettings:
    """自然语言处理设置"""
    enabled: bool = True
    confidence_threshold: float = 0.6
    max_query_length: int = 1000
    cache_parsed_queries: bool = True
    
    @classmethod
    def from_env(cls) -> "NLPSettings":
        """从环境变量创建NLP设置"""
        return cls(
            enabled=os.getenv("NLP_ENABLED", "true").lower() == "true",
            confidence_threshold=float(os.getenv("NLP_CONFIDENCE_THRESHOLD", "0.6")),
            max_query_length=int(os.getenv("NLP_MAX_QUERY_LENGTH", "1000")),
            cache_parsed_queries=os.getenv("NLP_CACHE_PARSED_QUERIES", "true").lower() == "true"
        )


@dataclass
class Settings:
    """应用程序设置"""
    # 环境设置
    environment: str = "development"
    debug: bool = False
    
    # 各模块设置
    database: DatabaseSettings = field(default_factory=DatabaseSettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    cache: CacheSettings = field(default_factory=CacheSettings)
    logging: LoggingSettings = field(default_factory=LoggingSettings)
    mcp: MCPSettings = field(default_factory=MCPSettings)
    dataset: DatasetSettings = field(default_factory=DatasetSettings)
    nlp: NLPSettings = field(default_factory=NLPSettings)
    
    # 路径设置
    base_dir: Path = field(default_factory=lambda: Path.cwd())
    data_dir: Path = field(default_factory=lambda: Path.cwd() / "data")
    logs_dir: Path = field(default_factory=lambda: Path.cwd() / "logs")
    cache_dir: Path = field(default_factory=lambda: Path.cwd() / "cache")
    
    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量创建设置"""
        # 基础设置
        environment = os.getenv("ENVIRONMENT", "development")
        debug = os.getenv("DEBUG", "false").lower() == "true"
        
        # 路径设置
        base_dir = Path(os.getenv("BASE_DIR", str(Path.cwd())))
        data_dir = Path(os.getenv("DATA_DIR", str(base_dir / "data")))
        logs_dir = Path(os.getenv("LOGS_DIR", str(base_dir / "logs")))
        cache_dir = Path(os.getenv("CACHE_DIR", str(base_dir / "cache")))
        
        return cls(
            environment=environment,
            debug=debug,
            database=DatabaseSettings.from_env(),
            redis=RedisSettings.from_env(),
            cache=CacheSettings.from_env(),
            logging=LoggingSettings.from_env(),
            mcp=MCPSettings.from_env(),
            dataset=DatasetSettings.from_env(),
            nlp=NLPSettings.from_env(),
            base_dir=base_dir,
            data_dir=data_dir,
            logs_dir=logs_dir,
            cache_dir=cache_dir
        )
    
    def ensure_directories(self):
        """确保必要的目录存在"""
        directories = [self.data_dir, self.logs_dir, self.cache_dir]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {}
        
        for field_name, field_value in self.__dict__.items():
            if hasattr(field_value, '__dict__'):
                # 嵌套的dataclass
                result[field_name] = field_value.__dict__.copy()
            elif isinstance(field_value, Path):
                # Path对象转换为字符串
                result[field_name] = str(field_value)
            else:
                result[field_name] = field_value
        
        return result
    
    def update_from_dict(self, data: Dict[str, Any]):
        """从字典更新设置"""
        for key, value in data.items():
            if hasattr(self, key):
                attr = getattr(self, key)
                if hasattr(attr, '__dict__') and isinstance(value, dict):
                    # 更新嵌套的dataclass
                    for sub_key, sub_value in value.items():
                        if hasattr(attr, sub_key):
                            setattr(attr, sub_key, sub_value)
                elif key.endswith('_dir') and isinstance(value, str):
                    # 路径字段
                    setattr(self, key, Path(value))
                else:
                    setattr(self, key, value)


# 全局设置实例
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取全局设置实例
    
    Returns:
        设置实例
    """
    global _settings
    
    if _settings is None:
        _settings = Settings.from_env()
        _settings.ensure_directories()
    
    return _settings


def reload_settings() -> Settings:
    """重新加载设置
    
    Returns:
        新的设置实例
    """
    global _settings
    
    _settings = Settings.from_env()
    _settings.ensure_directories()
    
    return _settings


def update_settings(data: Dict[str, Any]) -> Settings:
    """更新设置
    
    Args:
        data: 设置数据
        
    Returns:
        更新后的设置实例
    """
    settings = get_settings()
    settings.update_from_dict(data)
    
    return settings