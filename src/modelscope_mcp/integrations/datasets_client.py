"""Hugging Face Datasets客户端

提供与Hugging Face datasets库的集成功能。
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, AsyncGenerator
from dataclasses import dataclass, asdict
from datetime import datetime

try:
    import datasets
    from datasets import load_dataset, list_datasets
    from huggingface_hub import HfApi, DatasetInfo
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False

from ..core.logger import LoggerMixin
from ..core.config import Config


@dataclass
class HuggingFaceDatasetInfo:
    """Hugging Face数据集信息"""
    dataset_id: str
    name: str
    description: str
    category: str
    task_type: str
    source: str = "huggingface"
    tags: List[str] = None
    size_bytes: Optional[int] = None
    sample_count: Optional[int] = None
    format_type: str = "unknown"
    language: str = "unknown"
    license: str = "unknown"
    author: str = "unknown"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    download_count: int = 0
    like_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.metadata is None:
            self.metadata = {}


class DatasetsClient(LoggerMixin):
    """Hugging Face Datasets客户端
    
    提供与Hugging Face datasets库的数据集访问和管理功能。
    """
    
    def __init__(self, config: Config):
        """初始化客户端
        
        Args:
            config: 配置对象
        """
        self.config = config
        self.api_token = config.huggingface.api_token
        self.cache_dir = config.huggingface.cache_dir
        self.timeout = config.huggingface.timeout
        
        # 检查datasets库是否可用
        if not DATASETS_AVAILABLE:
            self.logger.warning("Hugging Face datasets库未安装，将使用模拟数据")
            self._use_mock_data = True
        else:
            self._use_mock_data = False
            self._init_api_client()
    
    def _init_api_client(self):
        """初始化API客户端"""
        try:
            self.hf_api = HfApi(token=self.api_token)
            self.logger.info("Hugging Face API客户端初始化成功")
        except Exception as e:
            self.logger.error(f"初始化Hugging Face API客户端失败: {e}")
            self._use_mock_data = True
    
    async def list_datasets(
        self,
        category: Optional[str] = None,
        task_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HuggingFaceDatasetInfo]:
        """列出数据集
        
        Args:
            category: 数据集类别
            task_type: 任务类型
            search_query: 搜索查询
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            数据集信息列表
        """
        self.logger.debug(f"列出Hugging Face数据集: category={category}, task_type={task_type}, query={search_query}")
        
        if self._use_mock_data:
            return await self._get_mock_datasets(category, task_type, search_query, limit, offset)
        
        try:
            # 构建搜索过滤器
            filters = {}
            if task_type:
                filters["task_categories"] = [task_type]
            
            # 调用Hugging Face API
            datasets_info = await self._search_datasets_api(
                search=search_query,
                filter=filters,
                limit=limit + offset  # 获取更多数据以支持偏移
            )
            
            # 转换为标准格式
            datasets = []
            for i, info in enumerate(datasets_info):
                if i < offset:
                    continue
                if len(datasets) >= limit:
                    break
                
                # 过滤类别
                if category and not self._matches_category(info, category):
                    continue
                
                dataset_info = await self._convert_to_dataset_info(info)
                datasets.append(dataset_info)
            
            self.logger.info(f"获取到{len(datasets)}个Hugging Face数据集")
            return datasets
            
        except Exception as e:
            self.logger.error(f"获取Hugging Face数据集失败: {e}")
            # 降级到模拟数据
            return await self._get_mock_datasets(category, task_type, search_query, limit, offset)
    
    async def get_dataset_info(self, dataset_id: str) -> Optional[HuggingFaceDatasetInfo]:
        """获取数据集详细信息
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集信息
        """
        self.logger.debug(f"获取Hugging Face数据集信息: {dataset_id}")
        
        if self._use_mock_data:
            return await self._get_mock_dataset_info(dataset_id)
        
        try:
            # 调用Hugging Face API获取详细信息
            dataset_info = await self._get_dataset_details_api(dataset_id)
            
            if not dataset_info:
                return None
            
            # 转换为标准格式
            converted_info = await self._convert_to_dataset_info(dataset_info)
            
            self.logger.info(f"获取到Hugging Face数据集信息: {dataset_id}")
            return converted_info
            
        except Exception as e:
            self.logger.error(f"获取Hugging Face数据集信息失败: {e}")
            return await self._get_mock_dataset_info(dataset_id)
    
    async def get_dataset_samples(
        self,
        dataset_id: str,
        subset: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取数据集样本
        
        Args:
            dataset_id: 数据集ID
            subset: 子集名称
            limit: 限制数量
            offset: 偏移量
            
        Returns:
            样本数据列表
        """
        self.logger.debug(f"获取Hugging Face数据集样本: {dataset_id}, subset={subset}")
        
        if self._use_mock_data:
            return await self._get_mock_samples(dataset_id, subset, limit, offset)
        
        try:
            # 加载数据集
            ds = load_dataset(
                dataset_id,
                name=subset,
                cache_dir=self.cache_dir,
                streaming=True  # 使用流式加载以节省内存
            )
            
            # 获取样本
            samples = []
            
            # 处理不同的数据集结构
            if isinstance(ds, dict):
                # 多个分割的数据集
                split_name = subset or list(ds.keys())[0]
                if split_name in ds:
                    split_ds = ds[split_name]
                    
                    # 跳过offset个样本
                    for i, sample in enumerate(split_ds):
                        if i < offset:
                            continue
                        if len(samples) >= limit:
                            break
                        samples.append(sample)
            else:
                # 单个数据集
                for i, sample in enumerate(ds):
                    if i < offset:
                        continue
                    if len(samples) >= limit:
                        break
                    samples.append(sample)
            
            self.logger.info(f"获取到{len(samples)}个Hugging Face数据集样本")
            return samples
            
        except Exception as e:
            self.logger.error(f"获取Hugging Face数据集样本失败: {e}")
            return await self._get_mock_samples(dataset_id, subset, limit, offset)
    
    async def search_datasets(self, query: str, limit: int = 20) -> List[HuggingFaceDatasetInfo]:
        """搜索数据集
        
        Args:
            query: 搜索查询
            limit: 限制数量
            
        Returns:
            数据集信息列表
        """
        return await self.list_datasets(search_query=query, limit=limit)
    
    async def _search_datasets_api(
        self,
        search: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        limit: int = 50
    ) -> List[DatasetInfo]:
        """调用搜索API
        
        Args:
            search: 搜索查询
            filter: 过滤条件
            limit: 限制数量
            
        Returns:
            数据集信息列表
        """
        try:
            # 调用Hugging Face Hub API
            datasets_info = list(self.hf_api.list_datasets(
                search=search,
                filter=filter,
                limit=limit
            ))
            
            return datasets_info
            
        except Exception as e:
            self.logger.error(f"调用Hugging Face搜索API失败: {e}")
            raise
    
    async def _get_dataset_details_api(self, dataset_id: str) -> Optional[DatasetInfo]:
        """获取数据集详细信息API
        
        Args:
            dataset_id: 数据集ID
            
        Returns:
            数据集详细信息
        """
        try:
            # 调用Hugging Face Hub API
            dataset_info = self.hf_api.dataset_info(dataset_id)
            return dataset_info
            
        except Exception as e:
            self.logger.error(f"调用Hugging Face详情API失败: {e}")
            raise
    
    def _matches_category(self, dataset_info: DatasetInfo, category: str) -> bool:
        """检查数据集是否匹配指定类别
        
        Args:
            dataset_info: 数据集信息
            category: 类别
            
        Returns:
            是否匹配
        """
        # 检查任务类别
        if hasattr(dataset_info, 'task_categories') and dataset_info.task_categories:
            for task_cat in dataset_info.task_categories:
                if self._map_task_to_category(task_cat) == category:
                    return True
        
        # 检查标签
        if hasattr(dataset_info, 'tags') and dataset_info.tags:
            for tag in dataset_info.tags:
                if self._map_tag_to_category(tag) == category:
                    return True
        
        return False
    
    def _map_task_to_category(self, task: str) -> str:
        """将任务类型映射到类别
        
        Args:
            task: 任务类型
            
        Returns:
            类别
        """
        task_lower = task.lower()
        
        if any(keyword in task_lower for keyword in ['image', 'vision', 'object-detection', 'image-classification']):
            return 'vision'
        elif any(keyword in task_lower for keyword in ['text', 'nlp', 'language', 'question-answering', 'sentiment']):
            return 'nlp'
        elif any(keyword in task_lower for keyword in ['audio', 'speech', 'sound']):
            return 'audio'
        elif any(keyword in task_lower for keyword in ['multimodal', 'vision-language']):
            return 'multimodal'
        else:
            return 'other'
    
    def _map_tag_to_category(self, tag: str) -> str:
        """将标签映射到类别
        
        Args:
            tag: 标签
            
        Returns:
            类别
        """
        return self._map_task_to_category(tag)
    
    async def _convert_to_dataset_info(self, info: DatasetInfo) -> HuggingFaceDatasetInfo:
        """转换为标准数据集信息格式
        
        Args:
            info: Hugging Face数据集信息
            
        Returns:
            标准化的数据集信息
        """
        # 提取基本信息
        dataset_id = info.id
        name = dataset_id.split('/')[-1] if '/' in dataset_id else dataset_id
        description = getattr(info, 'description', '') or ''
        
        # 确定类别和任务类型
        category = 'unknown'
        task_type = 'unknown'
        
        if hasattr(info, 'task_categories') and info.task_categories:
            task_type = info.task_categories[0]
            category = self._map_task_to_category(task_type)
        
        # 提取其他信息
        tags = getattr(info, 'tags', []) or []
        size_bytes = getattr(info, 'size_in_bytes', None)
        
        # 提取语言信息
        language = 'unknown'
        if hasattr(info, 'language') and info.language:
            if isinstance(info.language, list):
                language = info.language[0] if info.language else 'unknown'
            else:
                language = str(info.language)
        
        # 提取许可证信息
        license_info = getattr(info, 'license', 'unknown') or 'unknown'
        
        # 提取作者信息
        author = dataset_id.split('/')[0] if '/' in dataset_id else 'unknown'
        
        # 提取时间信息
        created_at = getattr(info, 'created_at', None)
        updated_at = getattr(info, 'last_modified', None)
        
        # 提取统计信息
        download_count = getattr(info, 'downloads', 0) or 0
        like_count = getattr(info, 'likes', 0) or 0
        
        return HuggingFaceDatasetInfo(
            dataset_id=dataset_id,
            name=name,
            description=description,
            category=category,
            task_type=task_type,
            source="huggingface",
            tags=tags,
            size_bytes=size_bytes,
            sample_count=None,  # 通常需要加载数据集才能获取
            format_type="unknown",
            language=language,
            license=license_info,
            author=author,
            created_at=created_at,
            updated_at=updated_at,
            download_count=download_count,
            like_count=like_count,
            metadata={
                "task_categories": getattr(info, 'task_categories', []),
                "paperswithcode_id": getattr(info, 'paperswithcode_id', None),
                "pretty_name": getattr(info, 'pretty_name', None)
            }
        )
    
    async def _get_mock_datasets(
        self,
        category: Optional[str] = None,
        task_type: Optional[str] = None,
        search_query: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[HuggingFaceDatasetInfo]:
        """获取模拟数据集数据"""
        mock_datasets = [
            HuggingFaceDatasetInfo(
                dataset_id="squad",
                name="SQuAD",
                description="Stanford Question Answering Dataset (SQuAD) is a reading comprehension dataset",
                category="nlp",
                task_type="question-answering",
                tags=["question-answering", "nlp"],
                size_bytes=35000000,  # 35MB
                sample_count=100000,
                format_type="json",
                language="english",
                license="CC BY-SA 4.0",
                author="rajpurkar",
                created_at=datetime(2016, 6, 1),
                updated_at=datetime(2023, 5, 1),
                download_count=25000,
                like_count=1200
            ),
            HuggingFaceDatasetInfo(
                dataset_id="imdb",
                name="IMDB Movie Reviews",
                description="Large Movie Review Dataset for sentiment analysis",
                category="nlp",
                task_type="text-classification",
                tags=["sentiment-analysis", "text-classification"],
                size_bytes=80000000,  # 80MB
                sample_count=50000,
                format_type="text",
                language="english",
                license="Apache 2.0",
                author="stanfordnlp",
                created_at=datetime(2011, 1, 1),
                updated_at=datetime(2023, 2, 15),
                download_count=18500,
                like_count=890
            ),
            HuggingFaceDatasetInfo(
                dataset_id="cifar10",
                name="CIFAR-10",
                description="The CIFAR-10 dataset consists of 60000 32x32 colour images in 10 classes",
                category="vision",
                task_type="image-classification",
                tags=["computer-vision", "image-classification"],
                size_bytes=170000000,  # 170MB
                sample_count=60000,
                format_type="image",
                language="multilingual",
                license="MIT",
                author="uoft-cs",
                created_at=datetime(2009, 4, 1),
                updated_at=datetime(2023, 1, 20),
                download_count=32000,
                like_count=1500
            ),
            HuggingFaceDatasetInfo(
                dataset_id="common_voice",
                name="Common Voice",
                description="Mozilla's Common Voice dataset for speech recognition",
                category="audio",
                task_type="automatic-speech-recognition",
                tags=["audio", "speech-recognition", "mozilla"],
                size_bytes=100000000000,  # 100GB
                sample_count=1000000,
                format_type="audio",
                language="multilingual",
                license="CC0",
                author="mozilla-foundation",
                created_at=datetime(2017, 6, 1),
                updated_at=datetime(2023, 8, 10),
                download_count=15000,
                like_count=980
            )
        ]
        
        # 应用过滤
        filtered_datasets = []
        for ds in mock_datasets:
            if category and ds.category != category:
                continue
            if task_type and ds.task_type != task_type:
                continue
            if search_query and search_query.lower() not in ds.name.lower() and search_query.lower() not in ds.description.lower():
                continue
            filtered_datasets.append(ds)
        
        # 应用分页
        return filtered_datasets[offset:offset + limit]
    
    async def _get_mock_dataset_info(self, dataset_id: str) -> Optional[HuggingFaceDatasetInfo]:
        """获取模拟数据集信息"""
        mock_datasets = await self._get_mock_datasets()
        
        for ds in mock_datasets:
            if ds.dataset_id == dataset_id:
                return ds
        
        return None
    
    async def _get_mock_samples(
        self,
        dataset_id: str,
        subset: Optional[str] = None,
        limit: int = 10,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """获取模拟样本数据"""
        # 根据数据集类型生成不同的模拟样本
        if dataset_id == "squad":
            return [
                {
                    "id": f"squad_{i + offset}",
                    "title": f"Sample Title {i + offset}",
                    "context": f"This is a sample context for question {i + offset}. It provides background information needed to answer the question.",
                    "question": f"What is the main topic of sample {i + offset}?",
                    "answers": {
                        "text": [f"sample topic {i + offset}"],
                        "answer_start": [25]
                    }
                }
                for i in range(limit)
            ]
        elif dataset_id == "imdb":
            return [
                {
                    "text": f"This is a sample movie review {i + offset}. The movie was {'excellent' if (i + offset) % 2 == 0 else 'terrible'} and I {'loved' if (i + offset) % 2 == 0 else 'hated'} it.",
                    "label": (i + offset) % 2  # 0 for negative, 1 for positive
                }
                for i in range(limit)
            ]
        elif dataset_id == "cifar10":
            return [
                {
                    "img": f"<PIL.Image.Image image mode=RGB size=32x32 at 0x{hex(id(object()))}>",
                    "label": (i + offset) % 10
                }
                for i in range(limit)
            ]
        elif dataset_id == "common_voice":
            return [
                {
                    "client_id": f"client_{(i + offset) % 1000}",
                    "path": f"audio/clip_{i + offset}.mp3",
                    "audio": {
                        "path": f"audio/clip_{i + offset}.mp3",
                        "array": f"[audio array data for sample {i + offset}]",
                        "sampling_rate": 48000
                    },
                    "sentence": f"This is the transcription for audio clip {i + offset}.",
                    "up_votes": (i + offset) % 5,
                    "down_votes": 0,
                    "age": "twenties",
                    "gender": "male" if (i + offset) % 2 == 0 else "female",
                    "accent": "us",
                    "locale": "en",
                    "segment": ""
                }
                for i in range(limit)
            ]
        else:
            return [
                {
                    "id": f"sample_{i + offset}",
                    "data": f"Sample data {i + offset}",
                    "label": f"label_{(i + offset) % 3}"
                }
                for i in range(limit)
            ]