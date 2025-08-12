"""日志系统

提供统一的日志管理功能。
"""

import os
import sys
import json
import logging
import logging.handlers
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime


class JSONFormatter(logging.Formatter):
    """JSON格式化器"""
    
    def format(self, record: logging.LogRecord) -> str:
        """格式化日志记录为JSON
        
        Args:
            record: 日志记录
            
        Returns:
            JSON格式的日志字符串
        """
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # 添加异常信息
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # 添加额外字段
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)
        
        return json.dumps(log_data, ensure_ascii=False)


class ContextFilter(logging.Filter):
    """上下文过滤器
    
    添加上下文信息到日志记录。
    """
    
    def __init__(self, context: Optional[Dict[str, Any]] = None):
        """初始化上下文过滤器
        
        Args:
            context: 上下文信息
        """
        super().__init__()
        self.context = context or {}
    
    def filter(self, record: logging.LogRecord) -> bool:
        """过滤日志记录
        
        Args:
            record: 日志记录
            
        Returns:
            是否通过过滤
        """
        # 添加上下文信息
        if not hasattr(record, "extra_fields"):
            record.extra_fields = {}
        
        record.extra_fields.update(self.context)
        
        return True
    
    def update_context(self, context: Dict[str, Any]):
        """更新上下文
        
        Args:
            context: 新的上下文信息
        """
        self.context.update(context)
    
    def clear_context(self):
        """清空上下文"""
        self.context.clear()


class LoggerManager:
    """日志管理器"""
    
    def __init__(self):
        """初始化日志管理器"""
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: Dict[str, logging.Handler] = {}
        self._context_filter: Optional[ContextFilter] = None
        self._configured = False
    
    def configure(
        self,
        level: str = "INFO",
        format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        file_path: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        console_output: bool = True,
        json_format: bool = False,
        context: Optional[Dict[str, Any]] = None
    ):
        """配置日志系统
        
        Args:
            level: 日志级别
            format_string: 日志格式字符串
            file_path: 日志文件路径
            max_file_size: 最大文件大小
            backup_count: 备份文件数量
            console_output: 是否输出到控制台
            json_format: 是否使用JSON格式
            context: 全局上下文信息
        """
        # 设置根日志级别
        logging.getLogger().setLevel(getattr(logging, level.upper()))
        
        # 创建上下文过滤器
        if context:
            self._context_filter = ContextFilter(context)
        
        # 创建格式化器
        if json_format:
            formatter = JSONFormatter()
        else:
            formatter = logging.Formatter(format_string)
        
        # 配置控制台处理器
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(getattr(logging, level.upper()))
            console_handler.setFormatter(formatter)
            
            if self._context_filter:
                console_handler.addFilter(self._context_filter)
            
            self._handlers["console"] = console_handler
            logging.getLogger().addHandler(console_handler)
        
        # 配置文件处理器
        if file_path:
            # 确保日志目录存在
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=max_file_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(getattr(logging, level.upper()))
            file_handler.setFormatter(formatter)
            
            if self._context_filter:
                file_handler.addFilter(self._context_filter)
            
            self._handlers["file"] = file_handler
            logging.getLogger().addHandler(file_handler)
        
        self._configured = True
    
    def get_logger(self, name: str) -> logging.Logger:
        """获取日志器
        
        Args:
            name: 日志器名称
            
        Returns:
            日志器实例
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def add_handler(self, name: str, handler: logging.Handler):
        """添加处理器
        
        Args:
            name: 处理器名称
            handler: 处理器实例
        """
        if self._context_filter:
            handler.addFilter(self._context_filter)
        
        self._handlers[name] = handler
        logging.getLogger().addHandler(handler)
    
    def remove_handler(self, name: str):
        """移除处理器
        
        Args:
            name: 处理器名称
        """
        if name in self._handlers:
            handler = self._handlers[name]
            logging.getLogger().removeHandler(handler)
            handler.close()
            del self._handlers[name]
    
    def update_context(self, context: Dict[str, Any]):
        """更新全局上下文
        
        Args:
            context: 上下文信息
        """
        if self._context_filter:
            self._context_filter.update_context(context)
        else:
            self._context_filter = ContextFilter(context)
            # 为所有现有处理器添加过滤器
            for handler in self._handlers.values():
                handler.addFilter(self._context_filter)
    
    def clear_context(self):
        """清空全局上下文"""
        if self._context_filter:
            self._context_filter.clear_context()
    
    def set_level(self, level: str, logger_name: Optional[str] = None):
        """设置日志级别
        
        Args:
            level: 日志级别
            logger_name: 日志器名称，如果为None则设置根日志器
        """
        log_level = getattr(logging, level.upper())
        
        if logger_name:
            logger = self.get_logger(logger_name)
            logger.setLevel(log_level)
        else:
            logging.getLogger().setLevel(log_level)
            # 同时更新所有处理器的级别
            for handler in self._handlers.values():
                handler.setLevel(log_level)
    
    def is_configured(self) -> bool:
        """检查是否已配置
        
        Returns:
            是否已配置
        """
        return self._configured
    
    def get_handlers(self) -> Dict[str, logging.Handler]:
        """获取所有处理器
        
        Returns:
            处理器字典
        """
        return self._handlers.copy()
    
    def shutdown(self):
        """关闭日志系统"""
        # 关闭所有处理器
        for handler in self._handlers.values():
            handler.close()
        
        # 清空处理器
        self._handlers.clear()
        
        # 关闭日志系统
        logging.shutdown()
        
        self._configured = False


# 全局日志管理器实例
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """获取全局日志管理器实例
    
    Returns:
        日志管理器实例
    """
    global _logger_manager
    
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    
    return _logger_manager


def configure_logging(
    level: str = "INFO",
    format_string: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    file_path: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    console_output: bool = True,
    json_format: bool = False,
    context: Optional[Dict[str, Any]] = None
):
    """配置日志系统
    
    Args:
        level: 日志级别
        format_string: 日志格式字符串
        file_path: 日志文件路径
        max_file_size: 最大文件大小
        backup_count: 备份文件数量
        console_output: 是否输出到控制台
        json_format: 是否使用JSON格式
        context: 全局上下文信息
    """
    manager = get_logger_manager()
    manager.configure(
        level=level,
        format_string=format_string,
        file_path=file_path,
        max_file_size=max_file_size,
        backup_count=backup_count,
        console_output=console_output,
        json_format=json_format,
        context=context
    )


def get_logger(name: str) -> logging.Logger:
    """获取日志器
    
    Args:
        name: 日志器名称
        
    Returns:
        日志器实例
    """
    manager = get_logger_manager()
    
    # 如果还未配置，使用默认配置
    if not manager.is_configured():
        configure_logging()
    
    return manager.get_logger(name)


def update_log_context(context: Dict[str, Any]):
    """更新日志上下文
    
    Args:
        context: 上下文信息
    """
    manager = get_logger_manager()
    manager.update_context(context)


def clear_log_context():
    """清空日志上下文"""
    manager = get_logger_manager()
    manager.clear_context()


def set_log_level(level: str, logger_name: Optional[str] = None):
    """设置日志级别
    
    Args:
        level: 日志级别
        logger_name: 日志器名称
    """
    manager = get_logger_manager()
    manager.set_level(level, logger_name)


def shutdown_logging():
    """关闭日志系统"""
    manager = get_logger_manager()
    manager.shutdown()


# 便捷函数
def setup_logging_from_config(config: Dict[str, Any]):
    """从配置字典设置日志
    
    Args:
        config: 日志配置字典
    """
    configure_logging(
        level=config.get("level", "INFO"),
        format_string=config.get("format", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"),
        file_path=config.get("file_path"),
        max_file_size=config.get("max_file_size", 10 * 1024 * 1024),
        backup_count=config.get("backup_count", 5),
        console_output=config.get("console_output", True),
        json_format=config.get("json_format", False)
    )


# 模块级日志器
logger = get_logger(__name__)