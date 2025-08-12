"""意图分类器

实现查询意图的分类和识别功能。
"""

import re
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from ..core.logger import LoggerMixin


class IntentType(Enum):
    """意图类型枚举"""
    LIST_DATASETS = "list_datasets"
    SEARCH_DATASETS = "search_datasets"
    GET_DATASET_INFO = "get_dataset_info"
    FILTER_SAMPLES = "filter_samples"
    COMPARE_DATASETS = "compare_datasets"
    RECOMMEND_DATASETS = "recommend_datasets"
    GET_STATISTICS = "get_statistics"
    DOWNLOAD_DATASET = "download_dataset"
    UPLOAD_DATASET = "upload_dataset"
    DELETE_DATASET = "delete_dataset"
    UNKNOWN = "unknown"


@dataclass
class IntentResult:
    """意图分类结果"""
    intent: IntentType
    confidence: float
    evidence: List[str]
    alternatives: List[Tuple[IntentType, float]]
    metadata: Dict[str, any]


class IntentClassifier(LoggerMixin):
    """意图分类器
    
    使用规则和模式匹配来识别用户查询的意图。
    """
    
    def __init__(self):
        """初始化分类器"""
        self._init_intent_patterns()
        self._init_intent_keywords()
        self._init_context_patterns()
    
    def _init_intent_patterns(self):
        """初始化意图模式"""
        self.intent_patterns = {
            IntentType.LIST_DATASETS: [
                r"\b(list|show|display|enumerate|get all)\b.*\b(datasets?|data)\b",
                r"\bwhat\s+(datasets?|data)\s+(are\s+)?available\b",
                r"\bshow\s+me\s+(all\s+)?(datasets?|data)\b",
                r"\bcan\s+you\s+(list|show)\b.*\b(datasets?|data)\b",
                r"\bi\s+want\s+to\s+see\s+(all\s+)?(datasets?|data)\b"
            ],
            IntentType.SEARCH_DATASETS: [
                r"\b(find|search|look for|locate)\b.*\b(datasets?|data)\b",
                r"\bi\s+(need|want|am looking for)\b.*\b(datasets?|data)\b",
                r"\bdo\s+you\s+have\b.*\b(datasets?|data)\b",
                r"\bwhere\s+can\s+i\s+find\b.*\b(datasets?|data)\b",
                r"\bhelp\s+me\s+find\b.*\b(datasets?|data)\b"
            ],
            IntentType.GET_DATASET_INFO: [
                r"\b(info|information|details|about|describe)\b.*\b(dataset|data)\b",
                r"\btell\s+me\s+about\b.*\b(dataset|data)\b",
                r"\bwhat\s+is\b.*\b(dataset|data)\b",
                r"\bexplain\b.*\b(dataset|data)\b",
                r"\bmore\s+details\s+about\b.*\b(dataset|data)\b"
            ],
            IntentType.FILTER_SAMPLES: [
                r"\b(filter|where|with|having)\b.*\b(samples?|data|records?)\b",
                r"\bshow\s+me\s+(samples?|data|records?)\s+(where|with|that)\b",
                r"\bget\s+(samples?|data|records?)\s+(where|with|that)\b",
                r"\bfind\s+(samples?|data|records?)\s+(where|with|that)\b",
                r"\bselect\s+(samples?|data|records?)\s+(where|with)\b"
            ],
            IntentType.COMPARE_DATASETS: [
                r"\b(compare|vs|versus|difference between)\b.*\b(datasets?|data)\b",
                r"\bwhich\s+is\s+better\b.*\b(datasets?|data)\b",
                r"\bwhat.*difference.*between\b.*\b(datasets?|data)\b",
                r"\bhow\s+do\b.*\b(datasets?|data)\b.*\bcompare\b",
                r"\bcontrast\b.*\b(datasets?|data)\b"
            ],
            IntentType.RECOMMEND_DATASETS: [
                r"\b(recommend|suggest|best)\b.*\b(datasets?|data)\b",
                r"\bwhat.*best.*\b(datasets?|data)\b",
                r"\bwhich.*\b(datasets?|data).*should\s+i\s+use\b",
                r"\badvise\s+me\s+on\b.*\b(datasets?|data)\b",
                r"\bwhat\s+would\s+you\s+recommend\b.*\b(datasets?|data)\b"
            ],
            IntentType.GET_STATISTICS: [
                r"\b(statistics|stats|metrics|numbers)\b.*\b(datasets?|data)\b",
                r"\bhow\s+many\b.*\b(datasets?|data|samples?)\b",
                r"\bcount\s+of\b.*\b(datasets?|data|samples?)\b",
                r"\bsize\s+of\b.*\b(datasets?|data)\b",
                r"\bsummary\s+of\b.*\b(datasets?|data)\b"
            ],
            IntentType.DOWNLOAD_DATASET: [
                r"\b(download|get|fetch|retrieve)\b.*\b(dataset|data)\b",
                r"\bhow\s+to\s+download\b.*\b(dataset|data)\b",
                r"\bwhere\s+to\s+download\b.*\b(dataset|data)\b",
                r"\bcan\s+i\s+download\b.*\b(dataset|data)\b",
                r"\baccess\b.*\b(dataset|data)\b"
            ],
            IntentType.UPLOAD_DATASET: [
                r"\b(upload|add|submit|contribute)\b.*\b(dataset|data)\b",
                r"\bhow\s+to\s+upload\b.*\b(dataset|data)\b",
                r"\bcan\s+i\s+add\b.*\b(dataset|data)\b",
                r"\bsubmit\s+my\b.*\b(dataset|data)\b",
                r"\bshare\b.*\b(dataset|data)\b"
            ],
            IntentType.DELETE_DATASET: [
                r"\b(delete|remove|drop)\b.*\b(dataset|data)\b",
                r"\bhow\s+to\s+delete\b.*\b(dataset|data)\b",
                r"\bcan\s+i\s+remove\b.*\b(dataset|data)\b",
                r"\buninstall\b.*\b(dataset|data)\b"
            ]
        }
    
    def _init_intent_keywords(self):
        """初始化意图关键词"""
        self.intent_keywords = {
            IntentType.LIST_DATASETS: {
                "primary": ["list", "show", "display", "enumerate", "all"],
                "secondary": ["available", "existing", "catalog", "index"]
            },
            IntentType.SEARCH_DATASETS: {
                "primary": ["find", "search", "look", "locate", "discover"],
                "secondary": ["need", "want", "looking", "seeking"]
            },
            IntentType.GET_DATASET_INFO: {
                "primary": ["info", "information", "details", "about", "describe"],
                "secondary": ["explain", "tell", "what", "overview", "summary"]
            },
            IntentType.FILTER_SAMPLES: {
                "primary": ["filter", "where", "with", "having", "select"],
                "secondary": ["samples", "records", "entries", "items"]
            },
            IntentType.COMPARE_DATASETS: {
                "primary": ["compare", "vs", "versus", "difference", "contrast"],
                "secondary": ["better", "best", "which", "between"]
            },
            IntentType.RECOMMEND_DATASETS: {
                "primary": ["recommend", "suggest", "best", "advise"],
                "secondary": ["should", "would", "good", "suitable"]
            },
            IntentType.GET_STATISTICS: {
                "primary": ["statistics", "stats", "metrics", "count", "size"],
                "secondary": ["how many", "numbers", "summary", "overview"]
            },
            IntentType.DOWNLOAD_DATASET: {
                "primary": ["download", "get", "fetch", "retrieve", "access"],
                "secondary": ["how to", "where to", "can i"]
            },
            IntentType.UPLOAD_DATASET: {
                "primary": ["upload", "add", "submit", "contribute", "share"],
                "secondary": ["how to", "can i", "my"]
            },
            IntentType.DELETE_DATASET: {
                "primary": ["delete", "remove", "drop", "uninstall"],
                "secondary": ["how to", "can i"]
            }
        }
    
    def _init_context_patterns(self):
        """初始化上下文模式"""
        self.context_patterns = {
            "question_words": ["what", "how", "where", "when", "why", "which", "who"],
            "action_words": ["can", "could", "would", "should", "may", "might"],
            "polite_words": ["please", "kindly", "help", "assist"],
            "urgency_words": ["urgent", "quickly", "asap", "immediately", "now"],
            "uncertainty_words": ["maybe", "perhaps", "possibly", "might", "could"]
        }
    
    async def classify(self, query_text: str, context: Optional[Dict] = None) -> IntentResult:
        """分类查询意图
        
        Args:
            query_text: 查询文本
            context: 上下文信息
            
        Returns:
            意图分类结果
        """
        self.logger.debug(f"分类意图: {query_text}")
        
        # 预处理查询文本
        normalized_query = self._normalize_query(query_text)
        
        # 计算每个意图的得分
        intent_scores = await self._calculate_intent_scores(normalized_query)
        
        # 应用上下文调整
        if context:
            intent_scores = await self._apply_context_adjustment(intent_scores, context)
        
        # 选择最佳意图
        best_intent, confidence = self._select_best_intent(intent_scores)
        
        # 获取证据
        evidence = await self._get_evidence(normalized_query, best_intent)
        
        # 获取备选意图
        alternatives = self._get_alternatives(intent_scores, best_intent)
        
        # 构建元数据
        metadata = {
            "normalized_query": normalized_query,
            "all_scores": intent_scores,
            "context_applied": context is not None,
            "processing_method": "pattern_matching"
        }
        
        return IntentResult(
            intent=best_intent,
            confidence=confidence,
            evidence=evidence,
            alternatives=alternatives,
            metadata=metadata
        )
    
    def _normalize_query(self, query_text: str) -> str:
        """标准化查询文本"""
        # 转换为小写
        normalized = query_text.lower().strip()
        
        # 移除多余的空格
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # 处理缩写
        abbreviations = {
            "info": "information",
            "stats": "statistics",
            "vs": "versus",
            "dl": "download",
            "ul": "upload"
        }
        
        for abbr, full in abbreviations.items():
            normalized = re.sub(rf'\b{abbr}\b', full, normalized)
        
        return normalized
    
    async def _calculate_intent_scores(self, query_text: str) -> Dict[IntentType, float]:
        """计算每个意图的得分
        
        Args:
            query_text: 标准化后的查询文本
            
        Returns:
            意图得分字典
        """
        scores = {intent: 0.0 for intent in IntentType}
        
        # 基于模式匹配计算得分
        for intent, patterns in self.intent_patterns.items():
            pattern_score = 0
            matched_patterns = 0
            
            for pattern in patterns:
                if re.search(pattern, query_text, re.IGNORECASE):
                    pattern_score += 1
                    matched_patterns += 1
            
            if matched_patterns > 0:
                scores[intent] += (pattern_score / len(patterns)) * 0.6
        
        # 基于关键词计算得分
        for intent, keywords in self.intent_keywords.items():
            keyword_score = 0
            
            # 主要关键词权重更高
            for keyword in keywords["primary"]:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    keyword_score += 0.3
            
            # 次要关键词权重较低
            for keyword in keywords["secondary"]:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    keyword_score += 0.1
            
            scores[intent] += min(keyword_score, 0.4)  # 限制关键词得分上限
        
        # 基于上下文模式调整得分
        context_adjustments = await self._calculate_context_adjustments(query_text)
        for intent in scores:
            scores[intent] += context_adjustments.get(intent, 0)
        
        # 确保得分在0-1范围内
        for intent in scores:
            scores[intent] = max(0, min(1, scores[intent]))
        
        return scores
    
    async def _calculate_context_adjustments(self, query_text: str) -> Dict[IntentType, float]:
        """基于上下文模式计算得分调整
        
        Args:
            query_text: 查询文本
            
        Returns:
            得分调整字典
        """
        adjustments = {intent: 0.0 for intent in IntentType}
        
        # 问句模式倾向于信息获取
        if any(word in query_text for word in self.context_patterns["question_words"]):
            adjustments[IntentType.GET_DATASET_INFO] += 0.1
            adjustments[IntentType.GET_STATISTICS] += 0.1
        
        # 行动词倾向于操作类意图
        if any(word in query_text for word in self.context_patterns["action_words"]):
            adjustments[IntentType.DOWNLOAD_DATASET] += 0.1
            adjustments[IntentType.UPLOAD_DATASET] += 0.1
            adjustments[IntentType.DELETE_DATASET] += 0.1
        
        # 礼貌用词倾向于请求类意图
        if any(word in query_text for word in self.context_patterns["polite_words"]):
            adjustments[IntentType.SEARCH_DATASETS] += 0.05
            adjustments[IntentType.RECOMMEND_DATASETS] += 0.05
        
        # 紧急词汇倾向于快速操作
        if any(word in query_text for word in self.context_patterns["urgency_words"]):
            adjustments[IntentType.LIST_DATASETS] += 0.1
            adjustments[IntentType.SEARCH_DATASETS] += 0.1
        
        # 不确定词汇倾向于推荐
        if any(word in query_text for word in self.context_patterns["uncertainty_words"]):
            adjustments[IntentType.RECOMMEND_DATASETS] += 0.1
        
        return adjustments
    
    async def _apply_context_adjustment(self, scores: Dict[IntentType, float], context: Dict) -> Dict[IntentType, float]:
        """应用上下文调整
        
        Args:
            scores: 原始得分
            context: 上下文信息
            
        Returns:
            调整后的得分
        """
        adjusted_scores = scores.copy()
        
        # 基于历史查询调整
        if "previous_intent" in context:
            prev_intent = context["previous_intent"]
            
            # 相关意图之间的转换更可能
            intent_transitions = {
                IntentType.LIST_DATASETS: [IntentType.GET_DATASET_INFO, IntentType.SEARCH_DATASETS],
                IntentType.SEARCH_DATASETS: [IntentType.GET_DATASET_INFO, IntentType.DOWNLOAD_DATASET],
                IntentType.GET_DATASET_INFO: [IntentType.DOWNLOAD_DATASET, IntentType.FILTER_SAMPLES],
                IntentType.COMPARE_DATASETS: [IntentType.RECOMMEND_DATASETS, IntentType.GET_DATASET_INFO]
            }
            
            if prev_intent in intent_transitions:
                for related_intent in intent_transitions[prev_intent]:
                    adjusted_scores[related_intent] += 0.1
        
        # 基于用户角色调整
        if "user_role" in context:
            role = context["user_role"]
            
            if role == "researcher":
                adjusted_scores[IntentType.GET_DATASET_INFO] += 0.1
                adjusted_scores[IntentType.COMPARE_DATASETS] += 0.1
            elif role == "developer":
                adjusted_scores[IntentType.DOWNLOAD_DATASET] += 0.1
                adjusted_scores[IntentType.FILTER_SAMPLES] += 0.1
            elif role == "student":
                adjusted_scores[IntentType.RECOMMEND_DATASETS] += 0.1
                adjusted_scores[IntentType.GET_DATASET_INFO] += 0.1
        
        # 基于会话状态调整
        if "session_state" in context:
            state = context["session_state"]
            
            if state == "exploring":
                adjusted_scores[IntentType.LIST_DATASETS] += 0.1
                adjusted_scores[IntentType.SEARCH_DATASETS] += 0.1
            elif state == "focused":
                adjusted_scores[IntentType.GET_DATASET_INFO] += 0.1
                adjusted_scores[IntentType.FILTER_SAMPLES] += 0.1
        
        return adjusted_scores
    
    def _select_best_intent(self, scores: Dict[IntentType, float]) -> Tuple[IntentType, float]:
        """选择最佳意图
        
        Args:
            scores: 意图得分
            
        Returns:
            最佳意图和置信度
        """
        # 排除UNKNOWN意图
        valid_scores = {intent: score for intent, score in scores.items() if intent != IntentType.UNKNOWN}
        
        if not valid_scores or max(valid_scores.values()) < 0.1:
            return IntentType.UNKNOWN, 0.0
        
        best_intent = max(valid_scores.keys(), key=lambda k: valid_scores[k])
        confidence = valid_scores[best_intent]
        
        # 如果最高得分太低，返回UNKNOWN
        if confidence < 0.2:
            return IntentType.UNKNOWN, confidence
        
        return best_intent, confidence
    
    async def _get_evidence(self, query_text: str, intent: IntentType) -> List[str]:
        """获取意图分类的证据
        
        Args:
            query_text: 查询文本
            intent: 分类的意图
            
        Returns:
            证据列表
        """
        evidence = []
        
        if intent == IntentType.UNKNOWN:
            return evidence
        
        # 检查匹配的模式
        if intent in self.intent_patterns:
            for pattern in self.intent_patterns[intent]:
                if re.search(pattern, query_text, re.IGNORECASE):
                    evidence.append(f"匹配模式: {pattern}")
        
        # 检查匹配的关键词
        if intent in self.intent_keywords:
            keywords = self.intent_keywords[intent]
            for keyword in keywords["primary"] + keywords["secondary"]:
                if re.search(rf'\b{re.escape(keyword)}\b', query_text, re.IGNORECASE):
                    evidence.append(f"匹配关键词: {keyword}")
        
        return evidence[:5]  # 限制证据数量
    
    def _get_alternatives(self, scores: Dict[IntentType, float], best_intent: IntentType) -> List[Tuple[IntentType, float]]:
        """获取备选意图
        
        Args:
            scores: 所有意图得分
            best_intent: 最佳意图
            
        Returns:
            备选意图列表
        """
        # 排除最佳意图和UNKNOWN
        alternatives = [(intent, score) for intent, score in scores.items() 
                       if intent != best_intent and intent != IntentType.UNKNOWN and score > 0.1]
        
        # 按得分降序排列
        alternatives.sort(key=lambda x: x[1], reverse=True)
        
        return alternatives[:3]  # 返回前3个备选意图