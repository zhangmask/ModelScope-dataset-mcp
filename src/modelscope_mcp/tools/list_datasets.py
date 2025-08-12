"""列出数据集工具

实现list_datasets MCP工具，用于列出可用的数据集。
"""

import json
from typing import Dict, Any, List, Optional

from ..core.logger import LoggerMixin
from ..services.database import DatabaseService
from ..services.cache import CacheService
from ..models.dataset import Dataset


class ListDatasetsHandler(LoggerMixin):
    """列出数据集工具处理器"""
    
    def __init__(self, db_service: DatabaseService, cache_service: CacheService):
        """初始化处理器
        
        Args:
            db_service: 数据库服务
            cache_service: 缓存服务
        """
        self.db_service = db_service
        self.cache_service = cache_service
    
    async def handle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理list_datasets请求
        
        Args:
            arguments: 工具参数
            
        Returns:
            数据集列表结果
        """
        try:
            # 解析参数
            category = arguments.get("category")
            source = arguments.get("source", "all")
            search = arguments.get("search")
            limit = arguments.get("limit", 50)
            offset = arguments.get("offset", 0)
            
            self.logger.info(
                f"列出数据集: category={category}, source={source}, "
                f"search={search}, limit={limit}, offset={offset}"
            )
            
            # 生成缓存键
            cache_key = self._generate_cache_key(category, source, search, limit, offset)
            
            # 尝试从缓存获取
            cached_result = await self.cache_service.get("list_datasets", cache_key)
            if cached_result:
                self.logger.debug("从缓存返回数据集列表")
                return cached_result
            
            # 从数据库查询
            datasets = await self.db_service.get_datasets(
                category=category,
                source=source,
                search=search,
                limit=limit,
                offset=offset
            )
            
            # 转换为响应格式
            result = await self._format_response(datasets, arguments)
            
            # 缓存结果
            await self.cache_service.set("list_datasets", cache_key, result, ttl=300)  # 5分钟缓存
            
            return result
            
        except Exception as e:
            self.logger.error(f"列出数据集失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "datasets": [],
                "total": 0
            }
    
    def _generate_cache_key(self, category: Optional[str], source: str, 
                          search: Optional[str], limit: int, offset: int) -> str:
        """生成缓存键
        
        Args:
            category: 分类
            source: 来源
            search: 搜索关键词
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            缓存键字符串
        """
        key_parts = [
            f"cat:{category or 'all'}",
            f"src:{source}",
            f"search:{search or 'none'}",
            f"limit:{limit}",
            f"offset:{offset}"
        ]
        return ":".join(key_parts)
    
    async def _format_response(self, datasets: List[Dataset], 
                             arguments: Dict[str, Any]) -> Dict[str, Any]:
        """格式化响应数据
        
        Args:
            datasets: 数据集列表
            arguments: 原始参数
            
        Returns:
            格式化的响应
        """
        formatted_datasets = []
        
        for dataset in datasets:
            dataset_info = {
                "id": dataset.id,
                "name": dataset.name,
                "display_name": dataset.display_name or dataset.name,
                "description": dataset.description,
                "source": dataset.source,
                "source_id": dataset.source_id,
                "category": dataset.category,
                "tags": dataset.tags or [],
                "total_samples": dataset.total_samples,
                "size_bytes": dataset.size_bytes,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "last_accessed": dataset.last_accessed
            }
            
            # 如果有子集信息，也包含进来
            try:
                if hasattr(dataset, 'subsets') and dataset.subsets:
                    dataset_info["subsets"] = [
                        {
                            "name": subset.name,
                            "split": subset.split,
                            "sample_count": subset.sample_count
                        }
                        for subset in dataset.subsets
                    ]
            except Exception:
                # 忽略Session绑定问题，不包含子集信息
                pass
            
            formatted_datasets.append(dataset_info)
        
        # 构建响应
        response = {
            "success": True,
            "datasets": formatted_datasets,
            "total": len(formatted_datasets),
            "query_info": {
                "category": arguments.get("category"),
                "source": arguments.get("source", "all"),
                "search": arguments.get("search"),
                "limit": arguments.get("limit", 50),
                "offset": arguments.get("offset", 0)
            }
        }
        
        # 添加分类统计
        if not arguments.get("category"):
            response["category_stats"] = await self._get_category_stats(datasets)
        
        # 添加来源统计
        if arguments.get("source", "all") == "all":
            response["source_stats"] = await self._get_source_stats(datasets)
        
        return response
    
    async def _get_category_stats(self, datasets: List[Dataset]) -> Dict[str, int]:
        """获取分类统计
        
        Args:
            datasets: 数据集列表
            
        Returns:
            分类统计字典
        """
        stats = {}
        for dataset in datasets:
            category = dataset.category or "unknown"
            stats[category] = stats.get(category, 0) + 1
        return stats
    
    async def _get_source_stats(self, datasets: List[Dataset]) -> Dict[str, int]:
        """获取来源统计
        
        Args:
            datasets: 数据集列表
            
        Returns:
            来源统计字典
        """
        stats = {}
        for dataset in datasets:
            source = dataset.source
            stats[source] = stats.get(source, 0) + 1
        return stats
    
    async def get_available_categories(self) -> List[str]:
        """获取可用的分类列表
        
        Returns:
            分类列表
        """
        try:
            # 尝试从缓存获取
            cached_categories = await self.cache_service.get("categories", "all")
            if cached_categories:
                return cached_categories
            
            # 从数据库查询所有数据集的分类
            datasets = await self.db_service.get_datasets(limit=1000)  # 获取更多数据集
            
            categories = set()
            for dataset in datasets:
                if dataset.category:
                    categories.add(dataset.category)
            
            category_list = sorted(list(categories))
            
            # 缓存结果
            await self.cache_service.set("categories", "all", category_list, ttl=3600)  # 1小时缓存
            
            return category_list
            
        except Exception as e:
            self.logger.error(f"获取分类列表失败: {e}")
            return []
    
    async def get_available_sources(self) -> List[str]:
        """获取可用的来源列表
        
        Returns:
            来源列表
        """
        try:
            # 尝试从缓存获取
            cached_sources = await self.cache_service.get("sources", "all")
            if cached_sources:
                return cached_sources
            
            # 从数据库查询所有数据集的来源
            datasets = await self.db_service.get_datasets(limit=1000)  # 获取更多数据集
            
            sources = set()
            for dataset in datasets:
                sources.add(dataset.source)
            
            source_list = sorted(list(sources))
            
            # 缓存结果
            await self.cache_service.set("sources", "all", source_list, ttl=3600)  # 1小时缓存
            
            return source_list
            
        except Exception as e:
            self.logger.error(f"获取来源列表失败: {e}")
            return []