"""数据库服务

提供数据库操作的统一接口。
"""

import asyncio
from typing import List, Optional, Dict, Any
from contextlib import asynccontextmanager

from sqlalchemy import create_engine, select, and_, or_
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError

from ..core.config import Config
from ..core.logger import get_logger, LoggerMixin
from ..models.base import Base
from ..models.dataset import Dataset, DatasetSubset
from ..models.query import QueryHistory, QueryResult
from ..models.cache import CacheEntry


class DatabaseService(LoggerMixin):
    """数据库服务类"""
    
    def __init__(self, config: Config):
        """初始化数据库服务
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """初始化数据库连接"""
        if self._initialized:
            return
        
        try:
            self.logger.info(f"正在连接数据库: {self.config.database_url}")
            
            # 创建数据库引擎
            self.engine = create_engine(
                self.config.database_url,
                echo=self.config.database_echo,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False
            )
            
            # 创建表（如果不存在）
            Base.metadata.create_all(self.engine)
            
            self._initialized = True
            self.logger.info("数据库连接初始化完成")
            
        except Exception as e:
            self.logger.error(f"数据库初始化失败: {e}")
            raise
    
    @asynccontextmanager
    async def get_session(self):
        """获取数据库会话（异步上下文管理器）"""
        if not self._initialized:
            await self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"数据库操作失败: {e}")
            raise
        finally:
            session.close()
    
    # 数据集相关操作
    async def get_datasets(
        self,
        category: Optional[str] = None,
        source: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Dataset]:
        """获取数据集列表
        
        Args:
            category: 分类过滤
            source: 来源过滤
            search: 搜索关键词
            limit: 返回数量限制
            offset: 偏移量
            
        Returns:
            数据集列表
        """
        async with self.get_session() as session:
            query = select(Dataset).where(Dataset.is_active == True)
            
            # 添加过滤条件
            if category:
                query = query.where(Dataset.category == category)
            
            if source and source != "all":
                query = query.where(Dataset.source == source)
            
            if search:
                search_pattern = f"%{search}%"
                query = query.where(
                    or_(
                        Dataset.name.ilike(search_pattern),
                        Dataset.display_name.ilike(search_pattern),
                        Dataset.description.ilike(search_pattern)
                    )
                )
            
            # 添加排序和分页
            query = query.order_by(Dataset.name).offset(offset).limit(limit)
            
            result = session.execute(query)
            datasets = result.scalars().all()
            
            # 分离对象以避免Session绑定问题
            for dataset in datasets:
                session.expunge(dataset)
            
            return datasets
    
    async def get_dataset_by_name(self, name: str) -> Optional[Dataset]:
        """根据名称获取数据集
        
        Args:
            name: 数据集名称
            
        Returns:
            数据集对象或None
        """
        async with self.get_session() as session:
            query = select(Dataset).where(
                and_(Dataset.name == name, Dataset.is_active == True)
            )
            result = session.execute(query)
            return result.scalar_one_or_none()
    
    async def create_dataset(self, dataset_data: Dict[str, Any]) -> Dataset:
        """创建数据集
        
        Args:
            dataset_data: 数据集数据
            
        Returns:
            创建的数据集对象
        """
        async with self.get_session() as session:
            dataset = Dataset(**dataset_data)
            session.add(dataset)
            session.flush()  # 获取ID
            session.refresh(dataset)
            return dataset
    
    async def update_dataset(self, dataset_id: int, update_data: Dict[str, Any]) -> Optional[Dataset]:
        """更新数据集
        
        Args:
            dataset_id: 数据集ID
            update_data: 更新数据
            
        Returns:
            更新后的数据集对象或None
        """
        async with self.get_session() as session:
            dataset = session.get(Dataset, dataset_id)
            if dataset:
                for key, value in update_data.items():
                    if hasattr(dataset, key):
                        setattr(dataset, key, value)
                session.flush()
                session.refresh(dataset)
            return dataset
    
    # 查询历史相关操作
    async def create_query_history(self, query_data: Dict[str, Any]) -> QueryHistory:
        """创建查询历史
        
        Args:
            query_data: 查询数据
            
        Returns:
            创建的查询历史对象
        """
        async with self.get_session() as session:
            query_history = QueryHistory(**query_data)
            session.add(query_history)
            session.flush()
            session.refresh(query_history)
            # 分离对象以避免Session绑定问题
            session.expunge(query_history)
            return query_history
    
    async def update_query_history(
        self, 
        query_id: int, 
        update_data: Dict[str, Any]
    ) -> Optional[QueryHistory]:
        """更新查询历史
        
        Args:
            query_id: 查询ID
            update_data: 更新数据
            
        Returns:
            更新后的查询历史对象或None
        """
        async with self.get_session() as session:
            query_history = session.get(QueryHistory, query_id)
            if query_history:
                for key, value in update_data.items():
                    if hasattr(query_history, key):
                        setattr(query_history, key, value)
                session.flush()
                session.refresh(query_history)
            return query_history
    
    async def get_query_history(
        self,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 50
    ) -> List[QueryHistory]:
        """获取查询历史
        
        Args:
            user_id: 用户ID
            session_id: 会话ID
            limit: 返回数量限制
            
        Returns:
            查询历史列表
        """
        async with self.get_session() as session:
            query = select(QueryHistory)
            
            if user_id:
                query = query.where(QueryHistory.user_id == user_id)
            
            if session_id:
                query = query.where(QueryHistory.session_id == session_id)
            
            query = query.order_by(QueryHistory.created_at.desc()).limit(limit)
            
            result = session.execute(query)
            return result.scalars().all()
    
    async def create_query_result(self, result_data: Dict[str, Any]) -> QueryResult:
        """创建查询结果
        
        Args:
            result_data: 结果数据
            
        Returns:
            创建的查询结果对象
        """
        async with self.get_session() as session:
            query_result = QueryResult(**result_data)
            session.add(query_result)
            session.flush()
            session.refresh(query_result)
            return query_result
    
    # 缓存相关操作
    async def create_cache_entry(self, cache_data: Dict[str, Any]) -> CacheEntry:
        """创建缓存条目
        
        Args:
            cache_data: 缓存数据
            
        Returns:
            创建的缓存条目对象
        """
        async with self.get_session() as session:
            cache_entry = CacheEntry(**cache_data)
            session.add(cache_entry)
            session.flush()
            session.refresh(cache_entry)
            return cache_entry
    
    async def get_cache_entry(self, cache_key: str) -> Optional[CacheEntry]:
        """获取缓存条目
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存条目对象或None
        """
        async with self.get_session() as session:
            query = select(CacheEntry).where(
                and_(CacheEntry.cache_key == cache_key, CacheEntry.is_valid == True)
            )
            result = session.execute(query)
            return result.scalar_one_or_none()
    
    async def update_cache_entry_stats(self, cache_key: str) -> None:
        """更新缓存条目统计信息
        
        Args:
            cache_key: 缓存键
        """
        async with self.get_session() as session:
            cache_entry = session.execute(
                select(CacheEntry).where(CacheEntry.cache_key == cache_key)
            ).scalar_one_or_none()
            
            if cache_entry:
                cache_entry.increment_hit_count()
    
    async def cleanup_expired_cache_entries(self) -> int:
        """清理过期的缓存条目
        
        Returns:
            清理的条目数量
        """
        async with self.get_session() as session:
            from datetime import datetime
            
            # 查找过期的缓存条目
            expired_entries = session.execute(
                select(CacheEntry).where(
                    and_(
                        CacheEntry.expires_at.isnot(None),
                        CacheEntry.expires_at < datetime.now().isoformat()
                    )
                )
            ).scalars().all()
            
            # 标记为无效
            count = 0
            for entry in expired_entries:
                entry.is_valid = False
                count += 1
            
            return count
    
    async def get_database_stats(self) -> Dict[str, Any]:
        """获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        async with self.get_session() as session:
            stats = {}
            
            # 数据集统计
            dataset_count = session.execute(
                select(Dataset).where(Dataset.is_active == True)
            ).scalars().all()
            stats["datasets_count"] = len(dataset_count)
            
            # 查询历史统计
            query_count = session.execute(select(QueryHistory)).scalars().all()
            stats["queries_count"] = len(query_count)
            
            # 缓存条目统计
            cache_count = session.execute(
                select(CacheEntry).where(CacheEntry.is_valid == True)
            ).scalars().all()
            stats["cache_entries_count"] = len(cache_count)
            
            return stats
    
    async def close(self) -> None:
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("数据库连接已关闭")
    
    def __del__(self):
        """析构函数"""
        if hasattr(self, 'engine') and self.engine:
            try:
                self.engine.dispose()
            except Exception:
                pass