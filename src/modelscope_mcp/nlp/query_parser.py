"""查询解析器

实现自然语言查询的解析和理解功能。
"""

import re
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.logger import LoggerMixin


class QueryType(Enum):
    """查询类型枚举"""
    LIST = "list"
    SEARCH = "search"
    INFO = "info"
    FILTER = "filter"
    COMPARE = "compare"
    RECOMMEND = "recommend"


class Intent(Enum):
    """意图枚举"""
    LIST_DATASETS = "list_datasets"
    SEARCH_DATASETS = "search_datasets"
    GET_DATASET_INFO = "get_dataset_info"
    FILTER_SAMPLES = "filter_samples"
    COMPARE_DATASETS = "compare_datasets"
    RECOMMEND_DATASETS = "recommend_datasets"
    GET_STATISTICS = "get_statistics"


@dataclass
class ParsedQuery:
    """解析后的查询结构"""
    original_query: str
    query_type: QueryType
    intent: Intent
    confidence: float
    entities: Dict[str, Any]
    filters: Dict[str, Any]
    keywords: List[str]
    parameters: Dict[str, Any]
    metadata: Dict[str, Any]


class QueryParser(LoggerMixin):
    """查询解析器
    
    负责解析自然语言查询，提取意图、实体和参数。
    """
    
    def __init__(self):
        """初始化解析器"""
        self._init_patterns()
        self._init_keywords()
    
    def _init_patterns(self):
        """初始化正则表达式模式"""
        self.patterns = {
            # 查询类型模式
            "list_patterns": [
                r"\b(list|show|display|get all|enumerate)\b.*\b(datasets?|data)\b",
                r"\bwhat\s+(datasets?|data)\s+(are\s+)?available\b",
                r"\bshow\s+me\s+(all\s+)?(datasets?|data)\b"
            ],
            "search_patterns": [
                r"\b(find|search|look for|locate)\b.*\b(datasets?|data)\b",
                r"\bi\s+(need|want|am looking for)\b.*\b(datasets?|data)\b",
                r"\bdo\s+you\s+have\b.*\b(datasets?|data)\b"
            ],
            "info_patterns": [
                r"\b(info|information|details|about|describe)\b.*\b(dataset|data)\b",
                r"\btell\s+me\s+about\b.*\b(dataset|data)\b",
                r"\bwhat\s+is\b.*\b(dataset|data)\b"
            ],
            "filter_patterns": [
                r"\b(filter|where|with|having)\b.*\b(samples?|data|records?)\b",
                r"\bshow\s+me\s+(samples?|data|records?)\s+(where|with|that)\b",
                r"\bget\s+(samples?|data|records?)\s+(where|with|that)\b"
            ],
            "compare_patterns": [
                r"\b(compare|vs|versus|difference between)\b.*\b(datasets?|data)\b",
                r"\bwhich\s+is\s+better\b.*\b(datasets?|data)\b",
                r"\bwhat.*difference.*between\b.*\b(datasets?|data)\b"
            ],
            "recommend_patterns": [
                r"\b(recommend|suggest|best)\b.*\b(datasets?|data)\b",
                r"\bwhat.*best.*\b(datasets?|data)\b",
                r"\bwhich.*\b(datasets?|data).*should\s+i\s+use\b"
            ],
            
            # 实体提取模式
            "dataset_name_patterns": [
                r"\b(coco|imagenet|squad|mnist|cifar|glue|openimages|ade20k)\b",
                r"\b([a-zA-Z0-9_-]+)[-_]?(dataset|data)\b",
                r"\bdataset\s+([a-zA-Z0-9_-]+)\b",
                r"\b([a-zA-Z0-9_-]+)\s+dataset\b"
            ],
            "category_patterns": [
                r"\b(vision|image|visual|computer vision|cv)\b",
                r"\b(nlp|text|language|natural language)\b",
                r"\b(audio|speech|sound|voice)\b",
                r"\b(multimodal|multi-modal|vision-language|vl)\b"
            ],
            "source_patterns": [
                r"\b(modelscope|ms)\b",
                r"\b(huggingface|hf|hugging\s+face)\b",
                r"\b(kaggle)\b",
                r"\b(github)\b"
            ],
            "size_patterns": [
                r"\b(larger|bigger|greater)\s+than\s+(\d+)\s*(mb|gb|tb|bytes?)\b",
                r"\b(smaller|less)\s+than\s+(\d+)\s*(mb|gb|tb|bytes?)\b",
                r"\bmore\s+than\s+(\d+)\s*(samples?|records?|examples?)\b",
                r"\bless\s+than\s+(\d+)\s*(samples?|records?|examples?)\b",
                r"\bbetween\s+(\d+)\s+and\s+(\d+)\s*(mb|gb|tb|bytes?|samples?|records?)\b"
            ],
            "task_patterns": [
                r"\b(classification|detection|segmentation|recognition)\b",
                r"\b(question\s+answering|qa|sentiment|translation)\b",
                r"\b(object\s+detection|image\s+classification)\b",
                r"\b(named\s+entity\s+recognition|ner|pos\s+tagging)\b"
            ]
        }
    
    def _init_keywords(self):
        """初始化关键词映射"""
        self.keywords = {
            "categories": {
                "vision": ["image", "vision", "visual", "photo", "picture", "cv", "computer vision"],
                "nlp": ["text", "nlp", "language", "natural language", "sentiment", "translation"],
                "audio": ["audio", "speech", "sound", "music", "voice", "acoustic"],
                "multimodal": ["multimodal", "multi-modal", "vision-language", "vl"]
            },
            "sources": {
                "modelscope": ["modelscope", "ms"],
                "huggingface": ["huggingface", "hf", "hugging face"],
                "kaggle": ["kaggle"],
                "github": ["github"]
            },
            "tasks": {
                "classification": ["classification", "classify", "categorize"],
                "detection": ["detection", "detect", "object detection"],
                "segmentation": ["segmentation", "segment", "semantic segmentation"],
                "qa": ["question answering", "qa", "questions"],
                "sentiment": ["sentiment", "emotion", "feeling"],
                "translation": ["translation", "translate", "machine translation"]
            },
            "formats": {
                "image": ["jpg", "jpeg", "png", "bmp", "tiff", "webp"],
                "text": ["txt", "json", "csv", "tsv", "xml"],
                "audio": ["wav", "mp3", "flac", "ogg", "m4a"]
            }
        }
        
        # 停用词
        self.stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "up", "about", "into", "through", "during", "before", "after",
            "above", "below", "between", "among", "dataset", "datasets", "data", "find",
            "search", "show", "list", "get", "all", "some", "any", "that", "this", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them",
            "is", "are", "was", "were", "be", "been", "being", "have", "has", "had", "do", "does",
            "did", "will", "would", "could", "should", "may", "might", "must", "can", "cannot"
        }
    
    async def parse(self, query_text: str) -> ParsedQuery:
        """解析查询文本
        
        Args:
            query_text: 原始查询文本
            
        Returns:
            解析后的查询对象
        """
        self.logger.debug(f"解析查询: {query_text}")
        
        # 预处理
        normalized_query = self._normalize_query(query_text)
        
        # 确定查询类型和意图
        query_type, intent, confidence = await self._classify_query(normalized_query)
        
        # 提取实体
        entities = await self._extract_entities(normalized_query)
        
        # 提取过滤条件
        filters = await self._extract_filters(normalized_query)
        
        # 提取关键词
        keywords = await self._extract_keywords(normalized_query)
        
        # 提取参数
        parameters = await self._extract_parameters(normalized_query, query_type)
        
        # 构建元数据
        metadata = {
            "normalized_query": normalized_query,
            "processing_steps": [
                "normalization",
                "classification", 
                "entity_extraction",
                "filter_extraction",
                "keyword_extraction",
                "parameter_extraction"
            ],
            "confidence_breakdown": {
                "overall": confidence,
                "query_type": confidence,
                "entities": self._calculate_entity_confidence(entities),
                "filters": self._calculate_filter_confidence(filters)
            }
        }
        
        return ParsedQuery(
            original_query=query_text,
            query_type=query_type,
            intent=intent,
            confidence=confidence,
            entities=entities,
            filters=filters,
            keywords=keywords,
            parameters=parameters,
            metadata=metadata
        )
    
    def _normalize_query(self, query_text: str) -> str:
        """标准化查询文本
        
        Args:
            query_text: 原始查询文本
            
        Returns:
            标准化后的查询文本
        """
        # 转换为小写
        normalized = query_text.lower().strip()
        
        # 移除多余的空格
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 移除标点符号（保留连字符和下划线）
        normalized = re.sub(r'[^\w\s-]', ' ', normalized)
        
        # 处理常见缩写
        abbreviations = {
            "ml": "machine learning",
            "ai": "artificial intelligence",
            "cv": "computer vision",
            "nlp": "natural language processing",
            "qa": "question answering",
            "ner": "named entity recognition",
            "pos": "part of speech",
            "hf": "huggingface",
            "ms": "modelscope"
        }
        
        for abbr, full in abbreviations.items():
            normalized = re.sub(rf'\b{abbr}\b', full, normalized)
        
        return normalized
    
    async def _classify_query(self, query_text: str) -> Tuple[QueryType, Intent, float]:
        """分类查询类型和意图
        
        Args:
            query_text: 标准化后的查询文本
            
        Returns:
            查询类型、意图和置信度
        """
        scores = {}
        
        # 计算每种查询类型的匹配分数
        for query_type, patterns in self.patterns.items():
            if not query_type.endswith('_patterns'):
                continue
                
            type_name = query_type.replace('_patterns', '')
            score = 0
            
            for pattern in patterns:
                if re.search(pattern, query_text, re.IGNORECASE):
                    score += 1
            
            if score > 0:
                scores[type_name] = score / len(patterns)
        
        # 选择得分最高的类型
        if not scores:
            return QueryType.SEARCH, Intent.SEARCH_DATASETS, 0.5
        
        best_type = max(scores.keys(), key=lambda k: scores[k])
        confidence = scores[best_type]
        
        # 映射到枚举类型
        type_mapping = {
            "list": (QueryType.LIST, Intent.LIST_DATASETS),
            "search": (QueryType.SEARCH, Intent.SEARCH_DATASETS),
            "info": (QueryType.INFO, Intent.GET_DATASET_INFO),
            "filter": (QueryType.FILTER, Intent.FILTER_SAMPLES),
            "compare": (QueryType.COMPARE, Intent.COMPARE_DATASETS),
            "recommend": (QueryType.RECOMMEND, Intent.RECOMMEND_DATASETS)
        }
        
        query_type, intent = type_mapping.get(best_type, (QueryType.SEARCH, Intent.SEARCH_DATASETS))
        
        return query_type, intent, confidence
    
    async def _extract_entities(self, query_text: str) -> Dict[str, Any]:
        """提取实体
        
        Args:
            query_text: 查询文本
            
        Returns:
            提取的实体字典
        """
        entities = {
            "datasets": [],
            "categories": [],
            "sources": [],
            "tasks": [],
            "formats": []
        }
        
        # 提取数据集名称
        for pattern in self.patterns["dataset_name_patterns"]:
            matches = re.findall(pattern, query_text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    # 选择非空的匹配组
                    dataset_name = next((m for m in match if m and m not in ['dataset', 'data']), None)
                else:
                    dataset_name = match
                
                if dataset_name and dataset_name not in entities["datasets"]:
                    entities["datasets"].append(dataset_name)
        
        # 提取类别
        for category, keywords in self.keywords["categories"].items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    if category not in entities["categories"]:
                        entities["categories"].append(category)
        
        # 提取来源
        for source, keywords in self.keywords["sources"].items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    if source not in entities["sources"]:
                        entities["sources"].append(source)
        
        # 提取任务类型
        for task, keywords in self.keywords["tasks"].items():
            for keyword in keywords:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    if task not in entities["tasks"]:
                        entities["tasks"].append(task)
        
        # 提取格式
        for format_type, extensions in self.keywords["formats"].items():
            for ext in extensions:
                if re.search(rf'\b{re.escape(ext)}\b', query_text, re.IGNORECASE):
                    if format_type not in entities["formats"]:
                        entities["formats"].append(format_type)
        
        return entities
    
    async def _extract_filters(self, query_text: str) -> Dict[str, Any]:
        """提取过滤条件
        
        Args:
            query_text: 查询文本
            
        Returns:
            过滤条件字典
        """
        filters = {}
        
        # 提取大小过滤条件
        size_patterns = [
            (r"(larger|bigger|greater)\s+than\s+(\d+)\s*(mb|gb|tb)", "min_size"),
            (r"(smaller|less)\s+than\s+(\d+)\s*(mb|gb|tb)", "max_size"),
            (r"more\s+than\s+(\d+)\s*(samples?|records?|examples?)", "min_samples"),
            (r"less\s+than\s+(\d+)\s*(samples?|records?|examples?)", "max_samples"),
            (r"between\s+(\d+)\s+and\s+(\d+)\s*(mb|gb|tb)", "size_range"),
            (r"between\s+(\d+)\s+and\s+(\d+)\s*(samples?|records?)", "sample_range")
        ]
        
        for pattern, filter_type in size_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                if "range" in filter_type:
                    min_val = int(match.group(1))
                    max_val = int(match.group(2))
                    unit = match.group(3) if len(match.groups()) > 2 else None
                    
                    if "size" in filter_type:
                        filters["min_size"] = self._convert_size_to_bytes(min_val, unit)
                        filters["max_size"] = self._convert_size_to_bytes(max_val, unit)
                    else:
                        filters["min_samples"] = min_val
                        filters["max_samples"] = max_val
                else:
                    value = int(match.group(2))
                    unit = match.group(3) if len(match.groups()) > 2 else None
                    
                    if "size" in filter_type:
                        filters[filter_type] = self._convert_size_to_bytes(value, unit)
                    else:
                        filters[filter_type] = value
        
        # 提取标签过滤
        tag_patterns = [
            r"tagged\s+with\s+([a-zA-Z0-9_,-]+)",
            r"tags?\s*[:=]\s*([a-zA-Z0-9_,-]+)",
            r"labeled\s+as\s+([a-zA-Z0-9_,-]+)"
        ]
        
        for pattern in tag_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                tags = [tag.strip() for tag in match.group(1).split(",")]
                filters["tags"] = tags
                break
        
        # 提取时间过滤
        time_patterns = [
            (r"created\s+after\s+(\d{4})", "created_after"),
            (r"created\s+before\s+(\d{4})", "created_before"),
            (r"updated\s+after\s+(\d{4})", "updated_after"),
            (r"updated\s+before\s+(\d{4})", "updated_before")
        ]
        
        for pattern, filter_type in time_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                year = int(match.group(1))
                filters[filter_type] = f"{year}-01-01"
        
        return filters
    
    async def _extract_keywords(self, query_text: str) -> List[str]:
        """提取关键词
        
        Args:
            query_text: 查询文本
            
        Returns:
            关键词列表
        """
        # 分词
        words = re.findall(r'\b[a-zA-Z]{2,}\b', query_text)
        
        # 过滤停用词和常见词汇
        keywords = []
        for word in words:
            if (word.lower() not in self.stop_words and 
                len(word) > 2 and 
                not word.isdigit()):
                keywords.append(word.lower())
        
        # 去重并保持顺序
        seen = set()
        unique_keywords = []
        for keyword in keywords:
            if keyword not in seen:
                seen.add(keyword)
                unique_keywords.append(keyword)
        
        return unique_keywords
    
    async def _extract_parameters(self, query_text: str, query_type: QueryType) -> Dict[str, Any]:
        """提取查询参数
        
        Args:
            query_text: 查询文本
            query_type: 查询类型
            
        Returns:
            参数字典
        """
        parameters = {}
        
        # 提取限制数量
        limit_patterns = [
            r"(first|top)\s+(\d+)",
            r"limit\s+(\d+)",
            r"show\s+(\d+)",
            r"(\d+)\s+results?"
        ]
        
        for pattern in limit_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                if pattern.startswith(r"(\d+)"):
                    parameters["limit"] = int(match.group(1))
                else:
                    parameters["limit"] = int(match.group(2))
                break
        
        # 提取排序参数
        sort_patterns = [
            (r"sort\s+by\s+(\w+)", "sort_by"),
            (r"order\s+by\s+(\w+)", "sort_by"),
            (r"sorted\s+by\s+(\w+)", "sort_by")
        ]
        
        for pattern, param_name in sort_patterns:
            match = re.search(pattern, query_text, re.IGNORECASE)
            if match:
                parameters[param_name] = match.group(1)
                
                # 检查排序方向
                if re.search(r"descending|desc|reverse", query_text, re.IGNORECASE):
                    parameters["sort_order"] = "desc"
                else:
                    parameters["sort_order"] = "asc"
                break
        
        # 根据查询类型设置默认参数
        if query_type == QueryType.LIST:
            parameters.setdefault("limit", 20)
        elif query_type == QueryType.SEARCH:
            parameters.setdefault("limit", 10)
        elif query_type == QueryType.FILTER:
            parameters.setdefault("limit", 50)
        
        return parameters
    
    def _convert_size_to_bytes(self, value: int, unit: str) -> int:
        """转换大小单位为字节
        
        Args:
            value: 数值
            unit: 单位
            
        Returns:
            字节数
        """
        multipliers = {
            "b": 1,
            "kb": 1024,
            "mb": 1024 * 1024,
            "gb": 1024 * 1024 * 1024,
            "tb": 1024 * 1024 * 1024 * 1024
        }
        
        unit_lower = unit.lower() if unit else "b"
        return value * multipliers.get(unit_lower, 1)
    
    def _calculate_entity_confidence(self, entities: Dict[str, Any]) -> float:
        """计算实体提取的置信度
        
        Args:
            entities: 提取的实体
            
        Returns:
            置信度分数
        """
        total_entities = sum(len(entity_list) for entity_list in entities.values())
        if total_entities == 0:
            return 0.5
        
        # 基于实体数量和类型计算置信度
        confidence = min(0.9, 0.5 + (total_entities * 0.1))
        return confidence
    
    def _calculate_filter_confidence(self, filters: Dict[str, Any]) -> float:
        """计算过滤条件的置信度
        
        Args:
            filters: 过滤条件
            
        Returns:
            置信度分数
        """
        if not filters:
            return 1.0  # 没有过滤条件时置信度为1
        
        # 基于过滤条件的复杂度计算置信度
        confidence = min(0.95, 0.7 + (len(filters) * 0.05))
        return confidence