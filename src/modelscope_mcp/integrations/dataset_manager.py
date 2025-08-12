"""数据集管理器

统一管理ModelScope和Hugging Face数据集的访问和操作。
"""

import asyncio
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .modelscope_client import ModelScopeClient, ModelScopeDatasetInfo
from .datasets_client import DatasetsClient, HuggingFaceDatasetInfo
from ..core.logger import LoggerMixin
from ..core.config import Config


class DatasetSource(Enum):
    """数据集来源枚举"""
    MODELSCOPE = "modelscope"
    HUGGINGFACE = "huggingface"
    ALL = "all"


@dataclass
class UnifiedDatasetInfo:
    """统一的数据集信息"""
    dataset_id: str
    name: str
    description: str
    category: str
    task_type: str
    source: str
    tags: List[str]
    size_bytes: Optional[int]
    sample_count: Optional[int]
    format_type: str
    language: str
    license: str
    author: str
    created_at: Optional[str]
    updated_at: Optional[str]
    download_count: int
    like_count: int
    metadata: Dict[str, Any]
    
    @classmethod
    def from_modelscope(cls, info: ModelScopeDatasetInfo) -> 'UnifiedDatasetInfo':
        """从ModelScope数据集信息创建统一格式
        
        Args:
            info: ModelScope数据集信息
            
        Returns:
            统一的数据集信息
        """
        return cls(
            dataset_id=info.dataset_id,
            name=info.name,
            description=info.description,
            category=info.category,
            task_type=info.task_type,
            source=info.source,
            tags=info.tags,
            size_bytes=info.size_bytes,
            sample_count=info.sample_count,
            format_type=info.format_type,
            language=info.language,
            license=info.license,
            author=info.author,
            created_at=info.created_at.isoformat() if info.created_at else None,
            updated_at=info.updated_at.isoformat() if info.updated_at else None,
            download_count=info.download_count,
            like_count=info.like_count,
            metadata=info.metadata
        )
    
    @classmethod
    def from_huggingface(cls, info: HuggingFaceDatasetInfo) -> 'UnifiedDatasetInfo':
        """从Hugging Face数据集信息创建统一格式
        
        Args:
            info: Hugging Face数据集信息
            
        Returns:
            统一的数据集信息
        """
        return cls(
            dataset_id=info.dataset_id,
            name=info.name,
            description=info.description,
            category=info.category,
            task_type=info.task_type,
            source=info.source,
            tags=info.tags,
            size_bytes=info.size_bytes,
            sample_count=info.sample_count,
            format_type=info.format_type,
            language=info.language,
            license=info.license,
            author=info.author,
            created_at=info.created_at.isoformat() if info.created_at else None,
            updated_at=info.updated_at.isoformat() if info.updated_at else None,
            download_count=info.download_count,
            like_count=info.like_count,
            metadata=info.metadata
        )


@dataclass
class DatasetSearchResult:
    """数据集搜索结果"""
    datasets: List[UnifiedDatasetInfo]
    total_count: int
    sources: Dict[str, int]
    categories: Dict[str, int]
    task_types: Dict[str, int]
    metadata: Dict[str, Any]


class DatasetManager(LoggerMixin):
    """数据集管理器
    
    统一管理多个数据集源的访问和操作。
    """
    
    def __init__(self, config: Config):
        """初始化管理器
        
        Args:
            config: 配置对象
        """
        self.config = config
        
        # 初始化客户端
        self.modelscope_client = ModelScopeClient(config)
        self.datasets_client = DatasetsClient(config)
        
        # 缓存
        self._dataset_cache = {}
        self._search_cache = {}
        
        self.logger.info("数据集管理器初始化完成")
    
    async def list_datasets(
        self,
        source: DatasetSource = DatasetSource.ALL,
        category: Optional[str] = None,
        task_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        sort_by: str = "download_count",
        sort_order: str = "desc"
    ) -> DatasetSearchResult:
        """列出数据集
        
        Args:
            source: 数据集来源
            category: 数据集类别
            task_type: 任务类型
            search_query: 搜索查询
            limit: 限制数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            数据集搜索结果
        """
        self.logger.debug(f"列出数据集: source={source.value}, category={category}, task_type={task_type}")
        
        # 生成缓存键
        cache_key = self._generate_cache_key(
            "list", source, category, task_type, search_query, limit, offset, sort_by, sort_order
        )
        
        # 检查缓存
        if cache_key in self._search_cache:
            self.logger.debug("从缓存返回数据集列表")
            return self._search_cache[cache_key]
        
        # 收集数据集
        all_datasets = []
        source_counts = {}
        
        # 从ModelScope获取数据集
        if source in [DatasetSource.ALL, DatasetSource.MODELSCOPE]:
            try:
                ms_datasets = await self.modelscope_client.list_datasets(
                    category=category,
                    task_type=task_type,
                    search_query=search_query,
                    limit=limit * 2,  # 获取更多数据以支持合并和排序
                    offset=0
                )
                
                for ds in ms_datasets:
                    unified_ds = UnifiedDatasetInfo.from_modelscope(ds)
                    all_datasets.append(unified_ds)
                
                source_counts["modelscope"] = len(ms_datasets)
                self.logger.debug(f"从ModelScope获取到{len(ms_datasets)}个数据集")
                
            except Exception as e:
                self.logger.error(f"从ModelScope获取数据集失败: {e}")
                source_counts["modelscope"] = 0
        
        # 从Hugging Face获取数据集
        if source in [DatasetSource.ALL, DatasetSource.HUGGINGFACE]:
            try:
                hf_datasets = await self.datasets_client.list_datasets(
                    category=category,
                    task_type=task_type,
                    search_query=search_query,
                    limit=limit * 2,  # 获取更多数据以支持合并和排序
                    offset=0
                )
                
                for ds in hf_datasets:
                    unified_ds = UnifiedDatasetInfo.from_huggingface(ds)
                    all_datasets.append(unified_ds)
                
                source_counts["huggingface"] = len(hf_datasets)
                self.logger.debug(f"从Hugging Face获取到{len(hf_datasets)}个数据集")
                
            except Exception as e:
                self.logger.error(f"从Hugging Face获取数据集失败: {e}")
                source_counts["huggingface"] = 0
        
        # 去重（基于dataset_id）
        unique_datasets = self._deduplicate_datasets(all_datasets)
        
        # 排序
        sorted_datasets = self._sort_datasets(unique_datasets, sort_by, sort_order)
        
        # 分页
        paginated_datasets = sorted_datasets[offset:offset + limit]
        
        # 生成统计信息
        categories = self._count_by_field(unique_datasets, "category")
        task_types = self._count_by_field(unique_datasets, "task_type")
        
        # 构建结果
        result = DatasetSearchResult(
            datasets=paginated_datasets,
            total_count=len(unique_datasets),
            sources=source_counts,
            categories=categories,
            task_types=task_types,
            metadata={
                "search_params": {
                    "source": source.value,
                    "category": category,
                    "task_type": task_type,
                    "search_query": search_query,
                    "limit": limit,
                    "offset": offset,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                },
                "total_before_pagination": len(unique_datasets),
                "returned_count": len(paginated_datasets)
            }
        )
        
        # 缓存结果
        self._search_cache[cache_key] = result
        
        self.logger.info(f"返回{len(paginated_datasets)}个数据集，总计{len(unique_datasets)}个")
        return result
    
    async def get_dataset_info(
        self,
        dataset_id: str,
        source: Optional[DatasetSource] = None
    ) -> Optional[UnifiedDatasetInfo]:
        """获取数据集详细信息
        
        Args:
            dataset_id: 数据集ID
            source: 指定数据集来源（可选）
            
        Returns:
            数据集信息
        """
        self.logger.debug(f"获取数据集信息: {dataset_id}, source={source}")
        
        # 检查缓存
        cache_key = f"info_{dataset_id}_{source.value if source else 'auto'}"
        if cache_key in self._dataset_cache:
            self.logger.debug("从缓存返回数据集信息")
            return self._dataset_cache[cache_key]
        
        dataset_info = None
        
        # 如果指定了来源，直接从该来源获取
        if source == DatasetSource.MODELSCOPE:
            ms_info = await self.modelscope_client.get_dataset_info(dataset_id)
            if ms_info:
                dataset_info = UnifiedDatasetInfo.from_modelscope(ms_info)
        elif source == DatasetSource.HUGGINGFACE:
            hf_info = await self.datasets_client.get_dataset_info(dataset_id)
            if hf_info:
                dataset_info = UnifiedDatasetInfo.from_huggingface(hf_info)
        else:
            # 自动检测来源
            dataset_info = await self._auto_detect_and_get_info(dataset_id)
        
        # 缓存结果
        if dataset_info:
            self._dataset_cache[cache_key] = dataset_info
            self.logger.info(f"获取到数据集信息: {dataset_id}")
        else:
            self.logger.warning(f"未找到数据集: {dataset_id}")
        
        return dataset_info
    
    async def get_dataset_samples(
        self,
        dataset_id: str,
        subset: Optional[str] = None,
        limit: int = 10,
        offset: int = 0,
        source: Optional[DatasetSource] = None
    ) -> List[Dict[str, Any]]:
        """获取数据集样本
        
        Args:
            dataset_id: 数据集ID
            subset: 子集名称
            limit: 限制数量
            offset: 偏移量
            source: 指定数据集来源（可选）
            
        Returns:
            样本数据列表
        """
        self.logger.debug(f"获取数据集样本: {dataset_id}, subset={subset}")
        
        samples = []
        
        # 如果指定了来源，直接从该来源获取
        if source == DatasetSource.MODELSCOPE:
            samples = await self.modelscope_client.get_dataset_samples(
                dataset_id, subset, limit, offset
            )
        elif source == DatasetSource.HUGGINGFACE:
            samples = await self.datasets_client.get_dataset_samples(
                dataset_id, subset, limit, offset
            )
        else:
            # 自动检测来源
            samples = await self._auto_detect_and_get_samples(
                dataset_id, subset, limit, offset
            )
        
        self.logger.info(f"获取到{len(samples)}个样本")
        return samples
    
    async def search_datasets(
        self,
        query: str,
        source: DatasetSource = DatasetSource.ALL,
        limit: int = 20
    ) -> DatasetSearchResult:
        """搜索数据集
        
        Args:
            query: 搜索查询
            source: 数据集来源
            limit: 限制数量
            
        Returns:
            数据集搜索结果
        """
        return await self.list_datasets(
            source=source,
            search_query=query,
            limit=limit
        )
    
    async def _auto_detect_and_get_info(self, dataset_id: str) -> Optional[UnifiedDatasetInfo]:
        """自动检测来源并获取数据集信息
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集信息
        """
        # 并行尝试从两个来源获取
        tasks = [
            self.modelscope_client.get_dataset_info(dataset_id),
            self.datasets_client.get_dataset_info(dataset_id)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查ModelScope结果
            if not isinstance(results[0], Exception) and results[0]:
                return UnifiedDatasetInfo.from_modelscope(results[0])
            
            # 检查Hugging Face结果
            if not isinstance(results[1], Exception) and results[1]:
                return UnifiedDatasetInfo.from_huggingface(results[1])
            
            return None
            
        except Exception as e:
            self.logger.error(f"自动检测数据集来源失败: {e}")
            return None
    
    async def _auto_detect_and_get_samples(
        self,
        dataset_id: str,
        subset: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """自动检测来源并获取样本
        
        Args:
            dataset_id: 数据集ID
            subset: 子集名称
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            样本数据列表
        """
        # 并行尝试从两个来源获取
        tasks = [
            self.modelscope_client.get_dataset_samples(dataset_id, subset, limit, offset),
            self.datasets_client.get_dataset_samples(dataset_id, subset, limit, offset)
        ]
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 检查ModelScope结果
            if not isinstance(results[0], Exception) and results[0]:
                return results[0]
            
            # 检查Hugging Face结果
            if not isinstance(results[1], Exception) and results[1]:
                return results[1]
            
            return []
            
        except Exception as e:
            self.logger.error(f"自动检测数据集来源失败: {e}")
            return []
    
    def _deduplicate_datasets(self, datasets: List[UnifiedDatasetInfo]) -> List[UnifiedDatasetInfo]:
        """去重数据集
        
        Args:
            datasets: 数据集列表
            
        Returns:
            去重后的数据集列表
        """
        seen_ids = set()
        unique_datasets = []
        
        for dataset in datasets:
            # 使用数据集名称的标准化版本作为去重键
            normalized_id = self._normalize_dataset_id(dataset.dataset_id)
            
            if normalized_id not in seen_ids:
                seen_ids.add(normalized_id)
                unique_datasets.append(dataset)
        
        return unique_datasets
    
    def _normalize_dataset_id(self, dataset_id: str) -> str:
        """标准化数据集ID用于去重
        
        Args:
            dataset_id: 原始数据集ID
            
        Returns:
            标准化的数据集ID
        """
        # 移除来源前缀
        normalized = dataset_id.lower()
        
        # 移除常见的前缀
        prefixes = ["modelscope/", "huggingface/", "datasets/"]
        for prefix in prefixes:
            if normalized.startswith(prefix):
                normalized = normalized[len(prefix):]
                break
        
        return normalized
    
    def _sort_datasets(
        self,
        datasets: List[UnifiedDatasetInfo],
        sort_by: str,
        sort_order: str
    ) -> List[UnifiedDatasetInfo]:
        """排序数据集
        
        Args:
            datasets: 数据集列表
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            排序后的数据集列表
        """
        reverse = sort_order.lower() == "desc"
        
        try:
            if sort_by == "name":
                return sorted(datasets, key=lambda x: x.name.lower(), reverse=reverse)
            elif sort_by == "download_count":
                return sorted(datasets, key=lambda x: x.download_count or 0, reverse=reverse)
            elif sort_by == "like_count":
                return sorted(datasets, key=lambda x: x.like_count or 0, reverse=reverse)
            elif sort_by == "size_bytes":
                return sorted(datasets, key=lambda x: x.size_bytes or 0, reverse=reverse)
            elif sort_by == "sample_count":
                return sorted(datasets, key=lambda x: x.sample_count or 0, reverse=reverse)
            elif sort_by == "created_at":
                return sorted(
                    datasets,
                    key=lambda x: x.created_at or "1970-01-01T00:00:00",
                    reverse=reverse
                )
            elif sort_by == "updated_at":
                return sorted(
                    datasets,
                    key=lambda x: x.updated_at or "1970-01-01T00:00:00",
                    reverse=reverse
                )
            else:
                # 默认按下载量排序
                return sorted(datasets, key=lambda x: x.download_count or 0, reverse=True)
                
        except Exception as e:
            self.logger.warning(f"排序失败，使用默认排序: {e}")
            return datasets
    
    def _count_by_field(self, datasets: List[UnifiedDatasetInfo], field: str) -> Dict[str, int]:
        """按字段统计数量
        
        Args:
            datasets: 数据集列表
            field: 统计字段
            
        Returns:
            统计结果
        """
        counts = {}
        
        for dataset in datasets:
            value = getattr(dataset, field, "unknown")
            if value:
                counts[value] = counts.get(value, 0) + 1
        
        # 按数量排序
        return dict(sorted(counts.items(), key=lambda x: x[1], reverse=True))
    
    def _generate_cache_key(self, *args) -> str:
        """生成缓存键
        
        Args:
            *args: 缓存键参数
            
        Returns:
            缓存键
        """
        return "_".join(str(arg) for arg in args if arg is not None)
    
    def clear_cache(self):
        """清除缓存"""
        self._dataset_cache.clear()
        self._search_cache.clear()
        self.logger.info("数据集缓存已清除")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息
        
        Returns:
            缓存统计信息
        """
        return {
            "dataset_cache_size": len(self._dataset_cache),
            "search_cache_size": len(self._search_cache),
            "total_cache_entries": len(self._dataset_cache) + len(self._search_cache)
        }