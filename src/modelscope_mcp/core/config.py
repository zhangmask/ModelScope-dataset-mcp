"""配置管理模块

管理项目的所有配置参数，支持环境变量和配置文件。
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Config:
    """项目配置类"""
    
    # 项目基础配置
    project_name: str = "ModelScope MCP Server"
    version: str = "0.1.0"
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "false").lower() == "true")
    
    # 数据库配置
    database_url: str = field(
        default_factory=lambda: os.getenv(
            "DATABASE_URL", 
            f"sqlite:///{Path.cwd() / 'data' / 'modelscope_mcp.db'}"
        )
    )
    database_echo: bool = field(
        default_factory=lambda: os.getenv("DATABASE_ECHO", "false").lower() == "true"
    )
    
    # Redis缓存配置
    redis_host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    redis_port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    redis_db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    redis_password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    redis_ssl: bool = field(
        default_factory=lambda: os.getenv("REDIS_SSL", "false").lower() == "true"
    )
    
    # 缓存配置
    cache_ttl_dataset_info: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_DATASET_INFO", "3600"))
    )
    cache_ttl_query_result: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_QUERY_RESULT", "1800"))
    )
    cache_ttl_sample_data: int = field(
        default_factory=lambda: int(os.getenv("CACHE_TTL_SAMPLE_DATA", "7200"))
    )
    cache_max_size: int = field(
        default_factory=lambda: int(os.getenv("CACHE_MAX_SIZE", "1000000000"))  # 1GB
    )
    
    # ModelScope配置
    modelscope_cache_dir: str = field(
        default_factory=lambda: os.getenv(
            "MODELSCOPE_CACHE_DIR", 
            str(Path.cwd() / "cache" / "modelscope")
        )
    )
    modelscope_token: Optional[str] = field(
        default_factory=lambda: os.getenv("MODELSCOPE_TOKEN")
    )
    
    # Hugging Face配置
    hf_cache_dir: str = field(
        default_factory=lambda: os.getenv(
            "HF_CACHE_DIR", 
            str(Path.cwd() / "cache" / "huggingface")
        )
    )
    hf_token: Optional[str] = field(default_factory=lambda: os.getenv("HF_TOKEN"))
    
    # MCP服务器配置
    mcp_server_name: str = field(
        default_factory=lambda: os.getenv("MCP_SERVER_NAME", "modelscope-dataset-server")
    )
    mcp_server_version: str = field(
        default_factory=lambda: os.getenv("MCP_SERVER_VERSION", "0.1.0")
    )
    mcp_max_connections: int = field(
        default_factory=lambda: int(os.getenv("MCP_MAX_CONNECTIONS", "10"))
    )
    
    # 日志配置
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    log_file: Optional[str] = field(
        default_factory=lambda: os.getenv(
            "LOG_FILE", 
            str(Path.cwd() / "logs" / "modelscope_mcp.log")
        )
    )
    log_max_size: int = field(
        default_factory=lambda: int(os.getenv("LOG_MAX_SIZE", "10485760"))  # 10MB
    )
    log_backup_count: int = field(
        default_factory=lambda: int(os.getenv("LOG_BACKUP_COUNT", "5"))
    )
    
    # 查询配置
    max_samples_per_query: int = field(
        default_factory=lambda: int(os.getenv("MAX_SAMPLES_PER_QUERY", "1000"))
    )
    default_samples_limit: int = field(
        default_factory=lambda: int(os.getenv("DEFAULT_SAMPLES_LIMIT", "100"))
    )
    query_timeout: int = field(
        default_factory=lambda: int(os.getenv("QUERY_TIMEOUT", "300"))  # 5分钟
    )
    
    # 性能配置
    max_workers: int = field(
        default_factory=lambda: int(os.getenv("MAX_WORKERS", "4"))
    )
    chunk_size: int = field(
        default_factory=lambda: int(os.getenv("CHUNK_SIZE", "1000"))
    )
    memory_limit: int = field(
        default_factory=lambda: int(os.getenv("MEMORY_LIMIT", "2147483648"))  # 2GB
    )
    
    def __post_init__(self):
        """初始化后处理"""
        # 确保必要的目录存在
        self._ensure_directories()
        
        # 验证配置
        self._validate_config()
    
    def _ensure_directories(self) -> None:
        """确保必要的目录存在"""
        directories = [
            Path(self.modelscope_cache_dir),
            Path(self.hf_cache_dir),
            Path.cwd() / "data",
            Path.cwd() / "logs",
        ]
        
        if self.log_file:
            directories.append(Path(self.log_file).parent)
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _validate_config(self) -> None:
        """验证配置参数"""
        # 验证端口范围
        if not (1 <= self.redis_port <= 65535):
            raise ValueError(f"Redis端口必须在1-65535范围内: {self.redis_port}")
        
        # 验证数据库范围
        if not (0 <= self.redis_db <= 15):
            raise ValueError(f"Redis数据库索引必须在0-15范围内: {self.redis_db}")
        
        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"无效的日志级别: {self.log_level}")
        
        # 验证数值范围
        if self.max_samples_per_query <= 0:
            raise ValueError("max_samples_per_query必须大于0")
        
        if self.default_samples_limit <= 0:
            raise ValueError("default_samples_limit必须大于0")
        
        if self.query_timeout <= 0:
            raise ValueError("query_timeout必须大于0")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            field.name: getattr(self, field.name)
            for field in self.__dataclass_fields__.values()
        }
    
    @classmethod
    def from_env_file(cls, env_file: str = ".env") -> "Config":
        """从环境文件加载配置
        
        Args:
            env_file: 环境文件路径
            
        Returns:
            Config实例
        """
        env_path = Path(env_file)
        if env_path.exists():
            # 简单的.env文件解析
            with open(env_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip()
        
        return cls()
    
    def get_redis_url(self) -> str:
        """获取Redis连接URL"""
        if self.redis_password:
            auth = f":{self.redis_password}@"
        else:
            auth = ""
        
        protocol = "rediss" if self.redis_ssl else "redis"
        return f"{protocol}://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    def get_cache_config(self) -> Dict[str, int]:
        """获取缓存配置"""
        return {
            "dataset_info": self.cache_ttl_dataset_info,
            "query_result": self.cache_ttl_query_result,
            "sample_data": self.cache_ttl_sample_data,
            "max_size": self.cache_max_size,
        }