"""查询模型

定义查询历史和查询结果的数据库模型。
"""

from typing import Optional, Dict, Any, List

from sqlalchemy import String, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class QueryHistory(BaseModel):
    """查询历史模型"""
    
    __tablename__ = "query_history"
    
    # 查询信息
    query_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="原始查询文本"
    )
    
    query_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="查询类型：natural_language, filter, direct"
    )
    
    # 解析结果
    parsed_query: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="解析后的查询结构"
    )
    
    # 目标信息
    target_dataset: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="目标数据集名称"
    )
    
    target_subset: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="目标子集名称"
    )
    
    # 过滤条件
    filter_conditions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="过滤条件"
    )
    
    # 查询参数
    max_samples: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="最大样本数"
    )
    
    output_format: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="输出格式：json, arrow, pandas"
    )
    
    # 执行信息
    execution_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="执行时间（秒）"
    )
    
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
        comment="执行状态：pending, running, completed, failed"
    )
    
    error_message: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="错误信息"
    )
    
    # 结果统计
    result_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="返回结果数量"
    )
    
    cache_hit: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        comment="是否命中缓存"
    )
    
    # 用户信息
    user_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="用户ID"
    )
    
    session_id: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="会话ID"
    )
    
    # 关联关系
    results: Mapped[List["QueryResult"]] = relationship(
        "QueryResult",
        back_populates="query",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<QueryHistory(id={self.id}, status='{self.status}')>"


class QueryResult(BaseModel):
    """查询结果模型"""
    
    __tablename__ = "query_results"
    
    # 关联信息
    query_id: Mapped[int] = mapped_column(
        ForeignKey("query_history.id"),
        nullable=False,
        comment="查询历史ID"
    )
    
    # 结果信息
    sample_index: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        comment="样本索引"
    )
    
    sample_data: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        comment="样本数据"
    )
    
    # 元数据
    sample_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="样本元数据"
    )
    
    # 评分信息
    relevance_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="相关性评分"
    )
    
    # 关联关系
    query: Mapped["QueryHistory"] = relationship(
        "QueryHistory",
        back_populates="results"
    )
    
    def __repr__(self) -> str:
        return f"<QueryResult(query_id={self.query_id}, index={self.sample_index})>"