"""过滤样本工具

实现filter_samples MCP工具，用于根据条件过滤数据集样本。
"""

import json
from typing import Dict, Any, Optional, List, Union
import re
from datetime import datetime

from ..core.logger import LoggerMixin
from ..services.database import DatabaseService
from ..services.cache import CacheService
from ..models.dataset import Dataset


class FilterSamplesHandler(LoggerMixin):
    """过滤样本工具处理器"""
    
    def __init__(self, db_service: DatabaseService, cache_service: CacheService):
        """初始化处理器
        
        Args:
            db_service: 数据库服务
            cache_service: 缓存服务
        """
        self.db_service = db_service
        self.cache_service = cache_service
    
    async def handle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理filter_samples请求
        
        Args:
            arguments: 工具参数
            
        Returns:
            过滤结果
        """
        try:
            # 解析参数
            dataset_name = arguments.get("dataset_name")
            filters = arguments.get("filters", {})
            subset_name = arguments.get("subset_name")
            limit = arguments.get("limit", 100)
            offset = arguments.get("offset", 0)
            sort_by = arguments.get("sort_by")
            sort_order = arguments.get("sort_order", "asc")
            
            if not dataset_name:
                return {
                    "success": False,
                    "error": "dataset_name参数是必需的",
                    "samples": [],
                    "total_count": 0,
                    "filtered_count": 0
                }
            
            self.logger.info(
                f"过滤样本: {dataset_name}, subset={subset_name}, "
                f"filters={filters}, limit={limit}, offset={offset}"
            )
            
            # 生成缓存键
            cache_key = self._generate_cache_key(
                dataset_name, subset_name, filters, limit, offset, sort_by, sort_order
            )
            
            # 尝试从缓存获取
            cached_result = await self.cache_service.get_samples(cache_key)
            if cached_result:
                self.logger.debug(f"从缓存返回过滤结果: {dataset_name}")
                return cached_result
            
            # 从数据库查询数据集
            dataset = await self.db_service.get_dataset_by_name(dataset_name)
            
            if not dataset:
                return {
                    "success": False,
                    "error": f"未找到数据集: {dataset_name}",
                    "samples": [],
                    "total_count": 0,
                    "filtered_count": 0
                }
            
            # 执行过滤
            result = await self._filter_samples(
                dataset, subset_name, filters, limit, offset, sort_by, sort_order
            )
            
            # 缓存结果
            await self.cache_service.cache_samples(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"过滤样本失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "samples": [],
                "total_count": 0,
                "filtered_count": 0
            }
    
    async def _filter_samples(
        self,
        dataset: Dataset,
        subset_name: Optional[str],
        filters: Dict[str, Any],
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_order: str
    ) -> Dict[str, Any]:
        """执行样本过滤
        
        Args:
            dataset: 数据集对象
            subset_name: 子集名称
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            过滤结果
        """
        # 获取目标子集
        target_subset = None
        if subset_name and hasattr(dataset, 'subsets') and dataset.subsets:
            for subset in dataset.subsets:
                if subset.name == subset_name:
                    target_subset = subset
                    break
        
        # 生成模拟样本数据（实际实现中应该从真实数据源加载）
        all_samples = await self._generate_sample_data(dataset, target_subset)
        
        # 应用过滤条件
        filtered_samples = await self._apply_filters(all_samples, filters)
        
        # 应用排序
        if sort_by:
            filtered_samples = await self._apply_sorting(filtered_samples, sort_by, sort_order)
        
        # 计算总数
        total_count = len(all_samples)
        filtered_count = len(filtered_samples)
        
        # 应用分页
        paginated_samples = filtered_samples[offset:offset + limit]
        
        # 构建结果
        result = {
            "success": True,
            "dataset_name": dataset.name,
            "subset_name": subset_name,
            "samples": paginated_samples,
            "total_count": total_count,
            "filtered_count": filtered_count,
            "returned_count": len(paginated_samples),
            "offset": offset,
            "limit": limit,
            "filters_applied": filters,
            "sort_by": sort_by,
            "sort_order": sort_order,
            "has_more": offset + len(paginated_samples) < filtered_count
        }
        
        return result
    
    async def _generate_sample_data(
        self,
        dataset: Dataset,
        subset: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """生成样本数据
        
        Args:
            dataset: 数据集对象
            subset: 子集对象
            
        Returns:
            样本数据列表
        """
        samples = []
        sample_count = subset.sample_count if subset else min(dataset.total_samples or 1000, 1000)
        
        # 根据数据集类型生成不同的样本
        if dataset.category == "vision":
            samples = await self._generate_vision_samples(dataset, sample_count)
        elif dataset.category == "nlp":
            samples = await self._generate_nlp_samples(dataset, sample_count)
        elif dataset.category == "audio":
            samples = await self._generate_audio_samples(dataset, sample_count)
        else:
            samples = await self._generate_generic_samples(dataset, sample_count)
        
        return samples
    
    async def _generate_vision_samples(self, dataset: Dataset, count: int) -> List[Dict[str, Any]]:
        """生成视觉数据集样本"""
        samples = []
        for i in range(min(count, 100)):  # 限制生成数量
            sample = {
                "id": f"{dataset.name}_{i}",
                "index": i,
                "image_path": f"images/{dataset.name}_{i:06d}.jpg",
                "width": 224 + (i % 100),
                "height": 224 + (i % 100),
                "format": "JPEG",
                "size_bytes": 50000 + (i * 1000),
                "created_at": datetime.now().isoformat()
            }
            
            # 根据数据集添加特定字段
            if "coco" in dataset.name.lower():
                sample.update({
                    "category_id": (i % 80) + 1,
                    "category_name": f"category_{(i % 80) + 1}",
                    "bbox_count": (i % 5) + 1,
                    "area": (i % 1000) + 100,
                    "is_crowd": i % 10 == 0
                })
            elif "imagenet" in dataset.name.lower():
                sample.update({
                    "class_id": (i % 1000),
                    "class_name": f"class_{(i % 1000)}",
                    "synset": f"n{(i % 1000):08d}"
                })
            
            samples.append(sample)
        
        return samples
    
    async def _generate_nlp_samples(self, dataset: Dataset, count: int) -> List[Dict[str, Any]]:
        """生成NLP数据集样本"""
        samples = []
        for i in range(min(count, 100)):
            sample = {
                "id": f"{dataset.name}_{i}",
                "index": i,
                "text_length": 50 + (i % 200),
                "word_count": 10 + (i % 50),
                "language": "en" if i % 3 == 0 else "zh",
                "created_at": datetime.now().isoformat()
            }
            
            # 根据数据集添加特定字段
            if "squad" in dataset.name.lower():
                sample.update({
                    "question": f"What is question {i}?",
                    "context": f"This is context {i} with some information.",
                    "answer_start": i % 20,
                    "answer_text": f"answer_{i}",
                    "is_impossible": i % 20 == 0
                })
            elif "sentiment" in dataset.name.lower():
                sample.update({
                    "text": f"This is sample text {i}",
                    "label": ["positive", "negative", "neutral"][i % 3],
                    "confidence": 0.5 + (i % 50) / 100
                })
            
            samples.append(sample)
        
        return samples
    
    async def _generate_audio_samples(self, dataset: Dataset, count: int) -> List[Dict[str, Any]]:
        """生成音频数据集样本"""
        samples = []
        for i in range(min(count, 100)):
            sample = {
                "id": f"{dataset.name}_{i}",
                "index": i,
                "audio_path": f"audio/{dataset.name}_{i:06d}.wav",
                "duration": 1.0 + (i % 10),
                "sample_rate": 16000 if i % 2 == 0 else 22050,
                "channels": 1 if i % 3 == 0 else 2,
                "format": "WAV",
                "size_bytes": 100000 + (i * 5000),
                "created_at": datetime.now().isoformat()
            }
            samples.append(sample)
        
        return samples
    
    async def _generate_generic_samples(self, dataset: Dataset, count: int) -> List[Dict[str, Any]]:
        """生成通用数据集样本"""
        samples = []
        for i in range(min(count, 100)):
            sample = {
                "id": f"{dataset.name}_{i}",
                "index": i,
                "value": f"sample_value_{i}",
                "score": (i % 100) / 100.0,
                "category": f"category_{i % 10}",
                "created_at": datetime.now().isoformat()
            }
            samples.append(sample)
        
        return samples
    
    async def _apply_filters(
        self,
        samples: List[Dict[str, Any]],
        filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """应用过滤条件
        
        Args:
            samples: 样本列表
            filters: 过滤条件
            
        Returns:
            过滤后的样本列表
        """
        if not filters:
            return samples
        
        filtered_samples = []
        
        for sample in samples:
            if await self._match_filters(sample, filters):
                filtered_samples.append(sample)
        
        return filtered_samples
    
    async def _match_filters(self, sample: Dict[str, Any], filters: Dict[str, Any]) -> bool:
        """检查样本是否匹配过滤条件
        
        Args:
            sample: 样本数据
            filters: 过滤条件
            
        Returns:
            是否匹配
        """
        for field, condition in filters.items():
            if not await self._match_condition(sample, field, condition):
                return False
        return True
    
    async def _match_condition(
        self,
        sample: Dict[str, Any],
        field: str,
        condition: Union[str, int, float, Dict[str, Any]]
    ) -> bool:
        """检查单个条件是否匹配
        
        Args:
            sample: 样本数据
            field: 字段名
            condition: 条件值
            
        Returns:
            是否匹配
        """
        # 获取字段值
        field_value = sample.get(field)
        
        if field_value is None:
            return False
        
        # 简单值匹配
        if isinstance(condition, (str, int, float, bool)):
            return field_value == condition
        
        # 复杂条件匹配
        if isinstance(condition, dict):
            return await self._match_complex_condition(field_value, condition)
        
        return False
    
    async def _match_complex_condition(
        self,
        field_value: Any,
        condition: Dict[str, Any]
    ) -> bool:
        """匹配复杂条件
        
        Args:
            field_value: 字段值
            condition: 条件字典
            
        Returns:
            是否匹配
        """
        # 范围条件
        if "min" in condition or "max" in condition:
            try:
                value = float(field_value)
                if "min" in condition and value < condition["min"]:
                    return False
                if "max" in condition and value > condition["max"]:
                    return False
                return True
            except (ValueError, TypeError):
                return False
        
        # 包含条件
        if "contains" in condition:
            return str(condition["contains"]).lower() in str(field_value).lower()
        
        # 正则表达式条件
        if "regex" in condition:
            try:
                pattern = re.compile(condition["regex"], re.IGNORECASE)
                return bool(pattern.search(str(field_value)))
            except re.error:
                return False
        
        # 列表包含条件
        if "in" in condition:
            return field_value in condition["in"]
        
        # 不等于条件
        if "not" in condition:
            return field_value != condition["not"]
        
        # 大于条件
        if "gt" in condition:
            try:
                return float(field_value) > float(condition["gt"])
            except (ValueError, TypeError):
                return False
        
        # 小于条件
        if "lt" in condition:
            try:
                return float(field_value) < float(condition["lt"])
            except (ValueError, TypeError):
                return False
        
        # 大于等于条件
        if "gte" in condition:
            try:
                return float(field_value) >= float(condition["gte"])
            except (ValueError, TypeError):
                return False
        
        # 小于等于条件
        if "lte" in condition:
            try:
                return float(field_value) <= float(condition["lte"])
            except (ValueError, TypeError):
                return False
        
        return False
    
    async def _apply_sorting(
        self,
        samples: List[Dict[str, Any]],
        sort_by: str,
        sort_order: str
    ) -> List[Dict[str, Any]]:
        """应用排序
        
        Args:
            samples: 样本列表
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            排序后的样本列表
        """
        try:
            reverse = sort_order.lower() == "desc"
            
            def sort_key(sample):
                value = sample.get(sort_by)
                if value is None:
                    return "" if isinstance(value, str) else 0
                return value
            
            return sorted(samples, key=sort_key, reverse=reverse)
            
        except Exception as e:
            self.logger.warning(f"排序失败: {e}，返回原始顺序")
            return samples
    
    def _generate_cache_key(
        self,
        dataset_name: str,
        subset_name: Optional[str],
        filters: Dict[str, Any],
        limit: int,
        offset: int,
        sort_by: Optional[str],
        sort_order: str
    ) -> str:
        """生成缓存键
        
        Args:
            dataset_name: 数据集名称
            subset_name: 子集名称
            filters: 过滤条件
            limit: 限制数量
            offset: 偏移量
            sort_by: 排序字段
            sort_order: 排序顺序
            
        Returns:
            缓存键
        """
        key_parts = [
            f"dataset:{dataset_name}",
            f"subset:{subset_name or 'all'}",
            f"filters:{json.dumps(filters, sort_keys=True)}",
            f"limit:{limit}",
            f"offset:{offset}",
            f"sort:{sort_by or 'none'}:{sort_order}"
        ]
        return ":".join(key_parts)