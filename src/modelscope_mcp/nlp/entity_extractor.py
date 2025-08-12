"""实体提取器

实现从自然语言查询中提取实体的功能。
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..core.logger import LoggerMixin


class EntityType(Enum):
    """实体类型枚举"""
    DATASET_NAME = "dataset_name"
    CATEGORY = "category"
    SOURCE = "source"
    TASK_TYPE = "task_type"
    FORMAT = "format"
    SIZE = "size"
    COUNT = "count"
    TAG = "tag"
    DATE = "date"
    LANGUAGE = "language"
    LICENSE = "license"
    AUTHOR = "author"
    VERSION = "version"


@dataclass
class Entity:
    """实体对象"""
    type: EntityType
    value: str
    confidence: float
    start_pos: int
    end_pos: int
    normalized_value: Any
    metadata: Dict[str, Any]


@dataclass
class ExtractionResult:
    """实体提取结果"""
    entities: List[Entity]
    entity_groups: Dict[EntityType, List[Entity]]
    confidence: float
    metadata: Dict[str, Any]


class EntityExtractor(LoggerMixin):
    """实体提取器
    
    使用规则和模式匹配从查询文本中提取各种实体。
    """
    
    def __init__(self):
        """初始化提取器"""
        self._init_extraction_patterns()
        self._init_entity_vocabularies()
        self._init_normalization_rules()
    
    def _init_extraction_patterns(self):
        """初始化提取模式"""
        self.patterns = {
            EntityType.DATASET_NAME: [
                # 知名数据集名称
                r"\b(coco|imagenet|squad|mnist|cifar|glue|openimages|ade20k|pascal|voc|cityscapes)\b",
                # 带有dataset关键词的模式
                r"\b([a-zA-Z0-9_-]+)[-_]?(dataset|data)\b",
                r"\bdataset\s+([a-zA-Z0-9_-]+)\b",
                r"\b([a-zA-Z0-9_-]+)\s+dataset\b",
                # 引号中的数据集名称
                r'["\']([a-zA-Z0-9_/-]+)["\']',
                # 特定格式的数据集ID
                r"\b([a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+)\b"
            ],
            EntityType.CATEGORY: [
                r"\b(vision|image|visual|computer\s+vision|cv)\b",
                r"\b(nlp|text|language|natural\s+language\s+processing)\b",
                r"\b(audio|speech|sound|voice|acoustic)\b",
                r"\b(multimodal|multi-modal|vision-language|vl)\b",
                r"\b(tabular|structured|numerical)\b",
                r"\b(time\s+series|temporal|sequential)\b"
            ],
            EntityType.SOURCE: [
                r"\b(modelscope|ms)\b",
                r"\b(huggingface|hf|hugging\s+face)\b",
                r"\b(kaggle)\b",
                r"\b(github)\b",
                r"\b(tensorflow\s+datasets|tfds)\b",
                r"\b(pytorch|torchvision)\b"
            ],
            EntityType.TASK_TYPE: [
                r"\b(classification|classify|categorization)\b",
                r"\b(detection|detect|object\s+detection)\b",
                r"\b(segmentation|segment|semantic\s+segmentation)\b",
                r"\b(recognition|recognize|ocr)\b",
                r"\b(question\s+answering|qa|questions?)\b",
                r"\b(sentiment\s+analysis|sentiment|emotion)\b",
                r"\b(translation|translate|machine\s+translation)\b",
                r"\b(summarization|summarize|summary)\b",
                r"\b(named\s+entity\s+recognition|ner)\b",
                r"\b(pos\s+tagging|part\s+of\s+speech)\b"
            ],
            EntityType.FORMAT: [
                r"\b(jpg|jpeg|png|bmp|tiff|webp|gif)\b",
                r"\b(txt|json|csv|tsv|xml|yaml|yml)\b",
                r"\b(wav|mp3|flac|ogg|m4a|aac)\b",
                r"\b(mp4|avi|mov|mkv|webm)\b",
                r"\b(parquet|arrow|hdf5|h5)\b"
            ],
            EntityType.SIZE: [
                r"\b(\d+(?:\.\d+)?)\s*(bytes?|b|kb|mb|gb|tb|pb)\b",
                r"\b(larger|bigger|greater|smaller|less)\s+than\s+(\d+(?:\.\d+)?)\s*(bytes?|b|kb|mb|gb|tb)\b",
                r"\bbetween\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)\s*(bytes?|b|kb|mb|gb|tb)\b"
            ],
            EntityType.COUNT: [
                r"\b(\d+(?:,\d{3})*)\s*(samples?|records?|examples?|items?|entries?)\b",
                r"\b(more|less)\s+than\s+(\d+(?:,\d{3})*)\s*(samples?|records?|examples?)\b",
                r"\bbetween\s+(\d+(?:,\d{3})*)\s+and\s+(\d+(?:,\d{3})*)\s*(samples?|records?)\b"
            ],
            EntityType.TAG: [
                r"\btagged\s+with\s+([a-zA-Z0-9_,-]+)\b",
                r"\btags?\s*[:=]\s*([a-zA-Z0-9_,-]+)\b",
                r"\blabeled\s+as\s+([a-zA-Z0-9_,-]+)\b",
                r"\bcategory\s*[:=]\s*([a-zA-Z0-9_,-]+)\b"
            ],
            EntityType.DATE: [
                r"\b(\d{4})\b",  # 年份
                r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b",  # 日期
                r"\b(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})\b",
                r"\b(created|updated|published)\s+(after|before|in)\s+(\d{4})\b",
                r"\b(last|past)\s+(\d+)\s+(years?|months?|days?)\b"
            ],
            EntityType.LANGUAGE: [
                r"\b(english|chinese|japanese|korean|french|german|spanish|italian|portuguese|russian|arabic)\b",
                r"\b(en|zh|ja|ko|fr|de|es|it|pt|ru|ar)\b",
                r"\bmultilingual\b",
                r"\blanguage\s*[:=]\s*([a-zA-Z]{2,})\b"
            ],
            EntityType.LICENSE: [
                r"\b(mit|apache|gpl|bsd|cc|creative\s+commons)\b",
                r"\blicense\s*[:=]\s*([a-zA-Z0-9_-]+)\b",
                r"\bopen\s+source\b",
                r"\bcommercial\s+use\b"
            ],
            EntityType.AUTHOR: [
                r"\bby\s+([a-zA-Z\s]+)\b",
                r"\bauthor\s*[:=]\s*([a-zA-Z\s]+)\b",
                r"\bcreated\s+by\s+([a-zA-Z\s]+)\b",
                r"\bfrom\s+([a-zA-Z\s]+)\b"
            ],
            EntityType.VERSION: [
                r"\bv(\d+(?:\.\d+)*)\b",
                r"\bversion\s+(\d+(?:\.\d+)*)\b",
                r"\b(\d+(?:\.\d+)*)\s+version\b"
            ]
        }
    
    def _init_entity_vocabularies(self):
        """初始化实体词汇表"""
        self.vocabularies = {
            EntityType.DATASET_NAME: {
                # 计算机视觉数据集
                "coco": "COCO",
                "imagenet": "ImageNet",
                "mnist": "MNIST",
                "cifar": "CIFAR",
                "pascal": "PASCAL VOC",
                "voc": "PASCAL VOC",
                "cityscapes": "Cityscapes",
                "openimages": "Open Images",
                "ade20k": "ADE20K",
                # NLP数据集
                "squad": "SQuAD",
                "glue": "GLUE",
                "superglue": "SuperGLUE",
                "imdb": "IMDB",
                "wikitext": "WikiText",
                "bookcorpus": "BookCorpus",
                # 音频数据集
                "librispeech": "LibriSpeech",
                "commonvoice": "Common Voice",
                "voxceleb": "VoxCeleb"
            },
            EntityType.CATEGORY: {
                "vision": "vision",
                "image": "vision",
                "visual": "vision",
                "cv": "vision",
                "computer vision": "vision",
                "nlp": "nlp",
                "text": "nlp",
                "language": "nlp",
                "natural language": "nlp",
                "audio": "audio",
                "speech": "audio",
                "sound": "audio",
                "voice": "audio",
                "multimodal": "multimodal",
                "multi-modal": "multimodal",
                "vision-language": "multimodal"
            },
            EntityType.SOURCE: {
                "modelscope": "modelscope",
                "ms": "modelscope",
                "huggingface": "huggingface",
                "hf": "huggingface",
                "hugging face": "huggingface",
                "kaggle": "kaggle",
                "github": "github",
                "tensorflow datasets": "tensorflow",
                "tfds": "tensorflow",
                "pytorch": "pytorch",
                "torchvision": "pytorch"
            },
            EntityType.LANGUAGE: {
                "en": "english",
                "zh": "chinese",
                "ja": "japanese",
                "ko": "korean",
                "fr": "french",
                "de": "german",
                "es": "spanish",
                "it": "italian",
                "pt": "portuguese",
                "ru": "russian",
                "ar": "arabic"
            }
        }
    
    def _init_normalization_rules(self):
        """初始化标准化规则"""
        self.normalization_rules = {
            EntityType.SIZE: self._normalize_size,
            EntityType.COUNT: self._normalize_count,
            EntityType.DATE: self._normalize_date,
            EntityType.DATASET_NAME: self._normalize_dataset_name,
            EntityType.CATEGORY: self._normalize_category,
            EntityType.SOURCE: self._normalize_source,
            EntityType.LANGUAGE: self._normalize_language
        }
    
    async def extract(self, query_text: str) -> ExtractionResult:
        """提取实体
        
        Args:
            query_text: 查询文本
            
        Returns:
            实体提取结果
        """
        self.logger.debug(f"提取实体: {query_text}")
        
        entities = []
        
        # 对每种实体类型进行提取
        for entity_type in EntityType:
            type_entities = await self._extract_entities_by_type(query_text, entity_type)
            entities.extend(type_entities)
        
        # 去重和冲突解决
        entities = await self._resolve_conflicts(entities)
        
        # 按实体类型分组
        entity_groups = self._group_entities_by_type(entities)
        
        # 计算整体置信度
        overall_confidence = self._calculate_overall_confidence(entities)
        
        # 构建元数据
        metadata = {
            "total_entities": len(entities),
            "entity_type_counts": {entity_type.value: len(group) for entity_type, group in entity_groups.items()},
            "extraction_method": "pattern_matching",
            "query_length": len(query_text)
        }
        
        return ExtractionResult(
            entities=entities,
            entity_groups=entity_groups,
            confidence=overall_confidence,
            metadata=metadata
        )
    
    async def _extract_entities_by_type(self, query_text: str, entity_type: EntityType) -> List[Entity]:
        """按类型提取实体
        
        Args:
            query_text: 查询文本
            entity_type: 实体类型
            
        Returns:
            该类型的实体列表
        """
        entities = []
        
        if entity_type not in self.patterns:
            return entities
        
        patterns = self.patterns[entity_type]
        
        for pattern in patterns:
            matches = re.finditer(pattern, query_text, re.IGNORECASE)
            
            for match in matches:
                # 提取实体值
                entity_value = self._extract_entity_value(match, entity_type)
                
                if not entity_value:
                    continue
                
                # 计算置信度
                confidence = self._calculate_entity_confidence(match, entity_type, query_text)
                
                # 标准化实体值
                normalized_value = await self._normalize_entity_value(entity_value, entity_type)
                
                # 构建实体对象
                entity = Entity(
                    type=entity_type,
                    value=entity_value,
                    confidence=confidence,
                    start_pos=match.start(),
                    end_pos=match.end(),
                    normalized_value=normalized_value,
                    metadata={
                        "pattern": pattern,
                        "match_text": match.group(0),
                        "context": self._get_context(query_text, match.start(), match.end())
                    }
                )
                
                entities.append(entity)
        
        return entities
    
    def _extract_entity_value(self, match: re.Match, entity_type: EntityType) -> Optional[str]:
        """从匹配结果中提取实体值
        
        Args:
            match: 正则匹配结果
            entity_type: 实体类型
            
        Returns:
            实体值
        """
        groups = match.groups()
        
        if not groups:
            return match.group(0).strip()
        
        # 根据实体类型选择合适的组
        if entity_type == EntityType.DATASET_NAME:
            # 选择非空的第一个组，排除"dataset"等关键词
            for group in groups:
                if group and group.lower() not in ["dataset", "data"]:
                    return group.strip()
        elif entity_type in [EntityType.SIZE, EntityType.COUNT]:
            # 对于大小和数量，通常需要数值和单位
            if len(groups) >= 2:
                return f"{groups[0]} {groups[1]}".strip()
            else:
                return groups[0].strip()
        else:
            # 默认返回第一个非空组
            for group in groups:
                if group and group.strip():
                    return group.strip()
        
        return match.group(0).strip()
    
    def _calculate_entity_confidence(self, match: re.Match, entity_type: EntityType, query_text: str) -> float:
        """计算实体置信度
        
        Args:
            match: 正则匹配结果
            entity_type: 实体类型
            query_text: 查询文本
            
        Returns:
            置信度分数
        """
        base_confidence = 0.7
        
        # 基于匹配长度调整
        match_length = match.end() - match.start()
        if match_length > 10:
            base_confidence += 0.1
        elif match_length < 3:
            base_confidence -= 0.1
        
        # 基于上下文调整
        context = self._get_context(query_text, match.start(), match.end(), window=10)
        
        # 如果上下文包含相关关键词，提高置信度
        context_keywords = {
            EntityType.DATASET_NAME: ["dataset", "data", "corpus"],
            EntityType.CATEGORY: ["type", "category", "domain"],
            EntityType.SOURCE: ["from", "source", "platform"],
            EntityType.SIZE: ["size", "bytes", "large", "small"],
            EntityType.COUNT: ["samples", "records", "examples", "items"]
        }
        
        if entity_type in context_keywords:
            for keyword in context_keywords[entity_type]:
                if keyword in context.lower():
                    base_confidence += 0.05
        
        # 基于词汇表匹配调整
        entity_value = self._extract_entity_value(match, entity_type)
        if (entity_type in self.vocabularies and 
            entity_value and 
            entity_value.lower() in self.vocabularies[entity_type]):
            base_confidence += 0.2
        
        return min(0.95, max(0.1, base_confidence))
    
    def _get_context(self, text: str, start: int, end: int, window: int = 20) -> str:
        """获取实体的上下文
        
        Args:
            text: 原始文本
            start: 实体开始位置
            end: 实体结束位置
            window: 上下文窗口大小
            
        Returns:
            上下文文本
        """
        context_start = max(0, start - window)
        context_end = min(len(text), end + window)
        return text[context_start:context_end]
    
    async def _normalize_entity_value(self, value: str, entity_type: EntityType) -> Any:
        """标准化实体值
        
        Args:
            value: 原始实体值
            entity_type: 实体类型
            
        Returns:
            标准化后的值
        """
        if entity_type in self.normalization_rules:
            return self.normalization_rules[entity_type](value)
        return value
    
    def _normalize_size(self, value: str) -> Dict[str, Any]:
        """标准化大小值"""
        # 提取数值和单位
        match = re.search(r'(\d+(?:\.\d+)?)\s*(\w+)', value.lower())
        if not match:
            return {"raw": value, "bytes": None, "unit": None}
        
        number = float(match.group(1))
        unit = match.group(2)
        
        # 转换为字节
        multipliers = {
            "b": 1, "byte": 1, "bytes": 1,
            "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4, "pb": 1024**5
        }
        
        bytes_value = number * multipliers.get(unit, 1)
        
        return {
            "raw": value,
            "number": number,
            "unit": unit,
            "bytes": int(bytes_value)
        }
    
    def _normalize_count(self, value: str) -> Dict[str, Any]:
        """标准化计数值"""
        # 移除逗号并提取数字
        number_str = re.sub(r'[,\s]', '', value)
        match = re.search(r'(\d+)', number_str)
        
        if not match:
            return {"raw": value, "count": None}
        
        count = int(match.group(1))
        
        return {
            "raw": value,
            "count": count
        }
    
    def _normalize_date(self, value: str) -> Dict[str, Any]:
        """标准化日期值"""
        # 简单的年份提取
        year_match = re.search(r'(\d{4})', value)
        
        result = {"raw": value}
        
        if year_match:
            result["year"] = int(year_match.group(1))
        
        return result
    
    def _normalize_dataset_name(self, value: str) -> str:
        """标准化数据集名称"""
        # 使用词汇表进行标准化
        if EntityType.DATASET_NAME in self.vocabularies:
            vocab = self.vocabularies[EntityType.DATASET_NAME]
            normalized = vocab.get(value.lower(), value)
            return normalized
        return value
    
    def _normalize_category(self, value: str) -> str:
        """标准化类别"""
        if EntityType.CATEGORY in self.vocabularies:
            vocab = self.vocabularies[EntityType.CATEGORY]
            return vocab.get(value.lower(), value.lower())
        return value.lower()
    
    def _normalize_source(self, value: str) -> str:
        """标准化来源"""
        if EntityType.SOURCE in self.vocabularies:
            vocab = self.vocabularies[EntityType.SOURCE]
            return vocab.get(value.lower(), value.lower())
        return value.lower()
    
    def _normalize_language(self, value: str) -> str:
        """标准化语言"""
        if EntityType.LANGUAGE in self.vocabularies:
            vocab = self.vocabularies[EntityType.LANGUAGE]
            return vocab.get(value.lower(), value.lower())
        return value.lower()
    
    async def _resolve_conflicts(self, entities: List[Entity]) -> List[Entity]:
        """解决实体冲突
        
        Args:
            entities: 原始实体列表
            
        Returns:
            解决冲突后的实体列表
        """
        # 按位置排序
        entities.sort(key=lambda e: (e.start_pos, e.end_pos))
        
        resolved_entities = []
        
        for entity in entities:
            # 检查是否与已有实体重叠
            overlapping = False
            
            for existing in resolved_entities:
                if self._entities_overlap(entity, existing):
                    # 如果重叠，选择置信度更高的
                    if entity.confidence > existing.confidence:
                        resolved_entities.remove(existing)
                        resolved_entities.append(entity)
                    overlapping = True
                    break
            
            if not overlapping:
                resolved_entities.append(entity)
        
        return resolved_entities
    
    def _entities_overlap(self, entity1: Entity, entity2: Entity) -> bool:
        """检查两个实体是否重叠
        
        Args:
            entity1: 实体1
            entity2: 实体2
            
        Returns:
            是否重叠
        """
        return not (entity1.end_pos <= entity2.start_pos or entity2.end_pos <= entity1.start_pos)
    
    def _group_entities_by_type(self, entities: List[Entity]) -> Dict[EntityType, List[Entity]]:
        """按类型分组实体
        
        Args:
            entities: 实体列表
            
        Returns:
            按类型分组的实体字典
        """
        groups = {}
        
        for entity in entities:
            if entity.type not in groups:
                groups[entity.type] = []
            groups[entity.type].append(entity)
        
        return groups
    
    def _calculate_overall_confidence(self, entities: List[Entity]) -> float:
        """计算整体置信度
        
        Args:
            entities: 实体列表
            
        Returns:
            整体置信度
        """
        if not entities:
            return 0.0
        
        # 计算加权平均置信度
        total_confidence = sum(entity.confidence for entity in entities)
        return total_confidence / len(entities)