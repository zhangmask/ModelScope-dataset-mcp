"""ModelScope数据集即时查询MCP Server

一个基于MCP协议的数据集查询服务器，支持自然语言查询ModelScope和Hugging Face数据集。
"""

__version__ = "0.1.0"
__author__ = "ModelScope Team"
__email__ = "team@modelscope.cn"

from .core.config import Config
from .core.logger import get_logger

__all__ = [
    "Config",
    "get_logger",
    "__version__",
    "__author__",
    "__email__",
]