"""数据集模型

定义数据集和数据集子集的数据库模型。
"""

from typing import Optional, Dict, Any, List

from sqlalchemy import String, Text, Integer, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class Dataset(BaseModel):
    """数据集模型"""
    
    __tablename__ = "datasets"
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="数据集名称"
    )
    
    display_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="显示名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="数据集描述"
    )
    
    # 来源信息
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="数据集来源：modelscope, huggingface"
    )
    
    source_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="在来源平台的ID"
    )
    
    # 分类信息
    category: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment="数据集分类"
    )
    
    tags: Mapped[Optional[List[str]]] = mapped_column(
        JSON,
        nullable=True,
        comment="标签列表"
    )
    
    # 统计信息
    total_samples: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="总样本数"
    )
    
    size_bytes: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="数据集大小（字节）"
    )
    
    # 结构信息
    schema_info: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="数据集结构信息"
    )
    
    features: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="特征信息"
    )
    
    # 状态信息
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否激活"
    )
    
    last_accessed: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最后访问时间"
    )
    
    # 关联关系
    subsets: Mapped[List["DatasetSubset"]] = relationship(
        "DatasetSubset",
        back_populates="dataset",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Dataset(name='{self.name}', source='{self.source}')>"


class DatasetSubset(BaseModel):
    """数据集子集模型"""
    
    __tablename__ = "dataset_subsets"
    
    # 关联信息
    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id"),
        nullable=False,
        comment="所属数据集ID"
    )
    
    # 基本信息
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="子集名称"
    )
    
    split: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="数据分割：train, test, validation"
    )
    
    # 统计信息
    sample_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="样本数量"
    )
    
    # 配置信息
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="子集配置"
    )
    
    # 关联关系
    dataset: Mapped["Dataset"] = relationship(
        "Dataset",
        back_populates="subsets"
    )
    
    def __repr__(self) -> str:
        return f"<DatasetSubset(name='{self.name}', split='{self.split}')>"