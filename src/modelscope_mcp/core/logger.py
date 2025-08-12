"""日志管理模块

提供统一的日志记录功能。
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from logging.handlers import RotatingFileHandler

from .config import Config

# 全局日志器缓存
_loggers = {}


def get_logger(name: str, config: Optional[Config] = None) -> logging.Logger:
    """获取日志器
    
    Args:
        name: 日志器名称
        config: 配置对象，如果为None则创建新的配置
        
    Returns:
        配置好的日志器
    """
    if name in _loggers:
        return _loggers[name]
    
    if config is None:
        config = Config()
    
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # 避免重复添加处理器
    if logger.handlers:
        _loggers[name] = logger
        return logger
    
    # 创建格式器
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件处理器
    if config.log_file:
        # 确保日志目录存在
        log_path = Path(config.log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = RotatingFileHandler(
            filename=config.log_file,
            maxBytes=config.log_max_size,
            backupCount=config.log_backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(getattr(logging, config.log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # 缓存日志器
    _loggers[name] = logger
    
    return logger


def setup_logging(config: Optional[Config] = None) -> None:
    """设置全局日志配置
    
    Args:
        config: 配置对象
    """
    if config is None:
        config = Config()
    
    # 设置根日志器
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # 禁用第三方库的详细日志
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("datasets").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("torch").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)


class LoggerMixin:
    """日志器混入类
    
    为类提供日志记录功能。
    """
    
    @property
    def logger(self) -> logging.Logger:
        """获取类的日志器"""
        if not hasattr(self, '_logger'):
            self._logger = get_logger(self.__class__.__name__)
        return self._logger


def log_execution_time(func):
    """装饰器：记录函数执行时间
    
    Args:
        func: 要装饰的函数
        
    Returns:
        装饰后的函数
    """
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"{func.__name__} 执行时间: {execution_time:.3f}秒")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} 执行失败 (耗时: {execution_time:.3f}秒): {e}")
            raise
    
    return wrapper


def log_method_calls(cls):
    """类装饰器：记录类方法调用
    
    Args:
        cls: 要装饰的类
        
    Returns:
        装饰后的类
    """
    import functools
    
    def log_calls(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            logger = get_logger(cls.__name__)
            logger.debug(f"调用方法: {func.__name__}")
            return func(self, *args, **kwargs)
        return wrapper
    
    # 装饰所有公共方法
    for attr_name in dir(cls):
        attr = getattr(cls, attr_name)
        if (callable(attr) and 
            not attr_name.startswith('_') and 
            not isinstance(attr, (staticmethod, classmethod))):
            setattr(cls, attr_name, log_calls(attr))
    
    return cls