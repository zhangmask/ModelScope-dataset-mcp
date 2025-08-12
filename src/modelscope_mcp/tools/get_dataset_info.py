"""获取数据集信息工具

实现get_dataset_info MCP工具，用于获取指定数据集的详细信息。
"""

import json
from typing import Dict, Any, Optional, List

from ..core.logger import LoggerMixin
from ..services.database import DatabaseService
from ..services.cache import CacheService
from ..models.dataset import Dataset


class GetDatasetInfoHandler(LoggerMixin):
    """获取数据集信息工具处理器"""
    
    def __init__(self, db_service: DatabaseService, cache_service: CacheService):
        """初始化处理器
        
        Args:
            db_service: 数据库服务
            cache_service: 缓存服务
        """
        self.db_service = db_service
        self.cache_service = cache_service
    
    async def handle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理get_dataset_info请求
        
        Args:
            arguments: 工具参数
            
        Returns:
            数据集信息结果
        """
        try:
            # 解析参数
            dataset_name = arguments.get("dataset_name")
            include_schema = arguments.get("include_schema", True)
            include_samples = arguments.get("include_samples", False)
            
            if not dataset_name:
                return {
                    "success": False,
                    "error": "dataset_name参数是必需的",
                    "dataset_info": None
                }
            
            self.logger.info(
                f"获取数据集信息: {dataset_name}, "
                f"include_schema={include_schema}, include_samples={include_samples}"
            )
            
            # 生成缓存键
            cache_key = f"{dataset_name}:schema_{include_schema}:samples_{include_samples}"
            
            # 尝试从缓存获取
            cached_result = await self.cache_service.get_dataset_info(cache_key)
            if cached_result:
                self.logger.debug(f"从缓存返回数据集信息: {dataset_name}")
                return cached_result
            
            # 从数据库查询数据集
            dataset = await self.db_service.get_dataset_by_name(dataset_name)
            
            if not dataset:
                return {
                    "success": False,
                    "error": f"未找到数据集: {dataset_name}",
                    "dataset_info": None
                }
            
            # 构建数据集信息
            result = await self._build_dataset_info(
                dataset, include_schema, include_samples
            )
            
            # 缓存结果
            await self.cache_service.cache_dataset_info(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"获取数据集信息失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "dataset_info": None
            }
    
    async def _build_dataset_info(
        self,
        dataset: Dataset,
        include_schema: bool,
        include_samples: bool
    ) -> Dict[str, Any]:
        """构建数据集信息
        
        Args:
            dataset: 数据集对象
            include_schema: 是否包含结构信息
            include_samples: 是否包含样本预览
            
        Returns:
            数据集信息字典
        """
        # 基本信息
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
            "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
            "last_accessed": dataset.last_accessed,
            "is_active": dataset.is_active
        }
        
        # 添加子集信息
        if hasattr(dataset, 'subsets') and dataset.subsets:
            dataset_info["subsets"] = [
                {
                    "id": subset.id,
                    "name": subset.name,
                    "split": subset.split,
                    "sample_count": subset.sample_count,
                    "config": subset.config
                }
                for subset in dataset.subsets
            ]
        else:
            dataset_info["subsets"] = []
        
        # 添加结构信息
        if include_schema:
            dataset_info["schema"] = await self._get_schema_info(dataset)
        
        # 添加样本预览
        if include_samples:
            dataset_info["sample_preview"] = await self._get_sample_preview(dataset)
        
        # 添加统计信息
        dataset_info["statistics"] = await self._get_dataset_statistics(dataset)
        
        # 添加使用建议
        dataset_info["usage_tips"] = await self._get_usage_tips(dataset)
        
        return {
            "success": True,
            "dataset_info": dataset_info
        }
    
    async def _get_schema_info(self, dataset: Dataset) -> Dict[str, Any]:
        """获取数据集结构信息
        
        Args:
            dataset: 数据集对象
            
        Returns:
            结构信息字典
        """
        schema_info = {
            "features": dataset.features or {},
            "schema_info": dataset.schema_info or {},
            "data_types": {},
            "field_descriptions": {}
        }
        
        # 解析特征信息
        if dataset.features:
            for field_name, field_info in dataset.features.items():
                if isinstance(field_info, dict):
                    schema_info["data_types"][field_name] = field_info.get("type", "unknown")
                    if "description" in field_info:
                        schema_info["field_descriptions"][field_name] = field_info["description"]
        
        # 从schema_info中提取更多信息
        if dataset.schema_info and "features" in dataset.schema_info:
            features = dataset.schema_info["features"]
            for field_name, field_info in features.items():
                if isinstance(field_info, dict):
                    if field_name not in schema_info["data_types"]:
                        schema_info["data_types"][field_name] = field_info.get("type", "unknown")
        
        return schema_info
    
    async def _get_sample_preview(self, dataset: Dataset, limit: int = 3) -> List[Dict[str, Any]]:
        """获取样本预览
        
        Args:
            dataset: 数据集对象
            limit: 预览样本数量
            
        Returns:
            样本预览列表
        """
        try:
            # 这里应该调用实际的数据集加载逻辑
            # 暂时返回模拟数据
            sample_preview = []
            
            # 根据数据集类型生成不同的样本预览
            if dataset.category == "vision":
                sample_preview = await self._generate_vision_sample_preview(dataset, limit)
            elif dataset.category == "nlp":
                sample_preview = await self._generate_nlp_sample_preview(dataset, limit)
            elif dataset.category == "audio":
                sample_preview = await self._generate_audio_sample_preview(dataset, limit)
            else:
                sample_preview = await self._generate_generic_sample_preview(dataset, limit)
            
            return sample_preview
            
        except Exception as e:
            self.logger.error(f"获取样本预览失败: {e}")
            return []
    
    async def _generate_vision_sample_preview(self, dataset: Dataset, limit: int) -> List[Dict[str, Any]]:
        """生成视觉数据集样本预览"""
        samples = []
        for i in range(min(limit, 3)):
            sample = {
                "index": i,
                "image": f"<Image data placeholder for {dataset.name}>",
                "metadata": {
                    "width": "placeholder",
                    "height": "placeholder",
                    "format": "placeholder"
                }
            }
            
            # 根据数据集名称添加特定字段
            if "coco" in dataset.name.lower():
                sample["annotations"] = {
                    "objects": "<Object detection annotations>",
                    "categories": "<Category information>"
                }
            elif "imagenet" in dataset.name.lower():
                sample["label"] = f"<ImageNet class {i}>"
                sample["class_name"] = f"<Class name {i}>"
            
            samples.append(sample)
        
        return samples
    
    async def _generate_nlp_sample_preview(self, dataset: Dataset, limit: int) -> List[Dict[str, Any]]:
        """生成NLP数据集样本预览"""
        samples = []
        for i in range(min(limit, 3)):
            sample = {
                "index": i,
                "text": f"<Text sample {i} from {dataset.name}>",
                "metadata": {
                    "length": "placeholder",
                    "language": "placeholder"
                }
            }
            
            # 根据数据集名称添加特定字段
            if "squad" in dataset.name.lower():
                sample.update({
                    "question": f"<Question {i}>",
                    "context": f"<Context {i}>",
                    "answers": f"<Answers {i}>"
                })
            elif "sentiment" in dataset.name.lower():
                sample["label"] = f"<Sentiment label {i}>"
            
            samples.append(sample)
        
        return samples
    
    async def _generate_audio_sample_preview(self, dataset: Dataset, limit: int) -> List[Dict[str, Any]]:
        """生成音频数据集样本预览"""
        samples = []
        for i in range(min(limit, 3)):
            sample = {
                "index": i,
                "audio": f"<Audio data placeholder for {dataset.name}>",
                "metadata": {
                    "duration": "placeholder",
                    "sample_rate": "placeholder",
                    "format": "placeholder"
                }
            }
            samples.append(sample)
        
        return samples
    
    async def _generate_generic_sample_preview(self, dataset: Dataset, limit: int) -> List[Dict[str, Any]]:
        """生成通用数据集样本预览"""
        samples = []
        for i in range(min(limit, 3)):
            sample = {
                "index": i,
                "data": f"<Sample data {i} from {dataset.name}>",
                "metadata": {
                    "type": dataset.category or "unknown"
                }
            }
            samples.append(sample)
        
        return samples
    
    async def _get_dataset_statistics(self, dataset: Dataset) -> Dict[str, Any]:
        """获取数据集统计信息
        
        Args:
            dataset: 数据集对象
            
        Returns:
            统计信息字典
        """
        stats = {
            "total_samples": dataset.total_samples,
            "size_bytes": dataset.size_bytes,
            "subset_count": len(dataset.subsets) if hasattr(dataset, 'subsets') and dataset.subsets else 0
        }
        
        # 添加大小的人类可读格式
        if dataset.size_bytes:
            stats["size_human"] = self._format_bytes(dataset.size_bytes)
        
        # 添加子集统计
        if hasattr(dataset, 'subsets') and dataset.subsets:
            subset_stats = {}
            for subset in dataset.subsets:
                subset_stats[subset.name] = {
                    "split": subset.split,
                    "sample_count": subset.sample_count
                }
            stats["subsets"] = subset_stats
        
        return stats
    
    async def _get_usage_tips(self, dataset: Dataset) -> List[str]:
        """获取使用建议
        
        Args:
            dataset: 数据集对象
            
        Returns:
            使用建议列表
        """
        tips = []
        
        # 基于数据集来源的建议
        if dataset.source == "modelscope":
            tips.append("使用ModelScope SDK加载: `MsDataset.load('{}')`".format(dataset.source_id))
        elif dataset.source == "huggingface":
            tips.append("使用Datasets库加载: `load_dataset('{}')`".format(dataset.source_id))
        
        # 基于数据集大小的建议
        if dataset.size_bytes and dataset.size_bytes > 1024 * 1024 * 1024:  # > 1GB
            tips.append("数据集较大，建议使用流式加载或分批处理")
        
        # 基于数据集类型的建议
        if dataset.category == "vision":
            tips.append("图像数据集，建议预处理时注意图像尺寸和格式")
        elif dataset.category == "nlp":
            tips.append("文本数据集，建议注意tokenization和最大长度设置")
        elif dataset.category == "audio":
            tips.append("音频数据集，建议注意采样率和音频格式")
        
        # 基于子集的建议
        if hasattr(dataset, 'subsets') and dataset.subsets:
            if len(dataset.subsets) > 1:
                subset_names = [subset.name for subset in dataset.subsets]
                tips.append(f"数据集包含多个子集: {', '.join(subset_names)}")
        
        return tips
    
    def _format_bytes(self, bytes_size: int) -> str:
        """格式化字节大小为人类可读格式
        
        Args:
            bytes_size: 字节大小
            
        Returns:
            格式化的大小字符串
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"