"""数据集集成模块

提供与ModelScope和Hugging Face datasets库的集成功能。
"""

from .modelscope_client import ModelScopeClient
from .datasets_client import DatasetsClient
from .dataset_manager import DatasetManager

__all__ = [
    "ModelScopeClient",
    "DatasetsClient",
    "DatasetManager"
]