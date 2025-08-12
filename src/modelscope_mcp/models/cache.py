"""缓存模型

定义缓存条目的数据库模型，用于管理Redis缓存的元数据。
"""

from typing import Optional, Dict, Any

from sqlalchemy import String, Text, Integer, Float, Boolean, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class CacheEntry(BaseModel):
    """缓存条目模型"""
    
    __tablename__ = "cache_entries"
    
    # 缓存键信息
    cache_key: Mapped[str] = mapped_column(
        String(512),
        unique=True,
        nullable=False,
        index=True,
        comment="缓存键"
    )
    
    cache_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        comment="缓存类型：dataset_info, query_result, sample_data"
    )
    
    # 数据信息
    dataset_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        index=True,
        comment="关联的数据集名称"
    )
    
    subset_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="关联的子集名称"
    )
    
    # 缓存元数据
    data_size: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="缓存数据大小（字节）"
    )
    
    item_count: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="缓存项目数量"
    )
    
    # 访问统计
    hit_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        comment="命中次数"
    )
    
    last_accessed: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="最后访问时间"
    )
    
    # 过期信息
    ttl_seconds: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
        comment="生存时间（秒）"
    )
    
    expires_at: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        comment="过期时间"
    )
    
    # 状态信息
    is_valid: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        comment="是否有效"
    )
    
    # 查询信息
    query_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        comment="查询哈希值"
    )
    
    query_params: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="查询参数"
    )
    
    # 性能信息
    generation_time: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="生成时间（秒）"
    )
    
    compression_ratio: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        comment="压缩比"
    )
    
    def __repr__(self) -> str:
        return f"<CacheEntry(key='{self.cache_key}', type='{self.cache_type}')>"
    
    def is_expired(self) -> bool:
        """检查缓存是否过期"""
        if not self.expires_at:
            return False
        
        from datetime import datetime
        try:
            expires_at = datetime.fromisoformat(self.expires_at)
            return datetime.now() > expires_at
        except (ValueError, TypeError):
            return True
    
    def increment_hit_count(self) -> None:
        """增加命中次数"""
        self.hit_count += 1
        from datetime import datetime
        self.last_accessed = datetime.now().isoformat()