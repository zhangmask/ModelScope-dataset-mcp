"""查询数据集工具

实现query_dataset MCP工具，用于根据自然语言查询数据集。
"""

import json
from typing import Dict, Any, Optional, List, Tuple
import re
from datetime import datetime

from ..core.logger import LoggerMixin
from ..services.database import DatabaseService
from ..services.cache import CacheService
from ..models.dataset import Dataset
from ..models.query import QueryHistory, QueryResult


class QueryDatasetHandler(LoggerMixin):
    """查询数据集工具处理器"""
    
    def __init__(self, db_service: DatabaseService, cache_service: CacheService):
        """初始化处理器
        
        Args:
            db_service: 数据库服务
            cache_service: 缓存服务
        """
        self.db_service = db_service
        self.cache_service = cache_service
    
    async def handle(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """处理query_dataset请求
        
        Args:
            arguments: 工具参数
            
        Returns:
            查询结果
        """
        try:
            # 解析参数
            query_text = arguments.get("query")
            dataset_name = arguments.get("dataset_name")
            limit = arguments.get("limit", 50)
            include_metadata = arguments.get("include_metadata", True)
            session_id = arguments.get("session_id")
            
            if not query_text:
                return {
                    "success": False,
                    "error": "query参数是必需的",
                    "datasets": [],  # 改为datasets字段以保持一致性
                    "results": [],   # 保留results字段以向后兼容
                    "total_count": 0,
                    "total": 0       # 添加total字段以保持一致性
                }
            
            self.logger.info(
                f"查询数据集: query='{query_text}', dataset={dataset_name}, "
                f"limit={limit}, session={session_id}"
            )
            
            # 生成缓存键
            cache_key = self._generate_cache_key(query_text, dataset_name, limit, include_metadata)
            
            # 尝试从缓存获取
            cached_result = await self.cache_service.get_query_result(cache_key)
            if cached_result:
                self.logger.debug(f"从缓存返回查询结果: {query_text[:50]}...")
                return cached_result
            
            # 解析查询
            parsed_query = await self._parse_query(query_text, dataset_name)
            
            # 记录查询历史
            query_history = await self._create_query_history(
                query_text, parsed_query, session_id
            )
            query_history_id = query_history.id
            
            # 执行查询
            result = await self._execute_query(
                parsed_query, limit, include_metadata, query_history_id
            )
            
            # 更新查询历史
            await self._update_query_history(query_history_id, result)
            
            # 缓存结果
            await self.cache_service.cache_query_result(cache_key, result)
            
            return result
            
        except Exception as e:
            self.logger.error(f"查询数据集失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "datasets": [],  # 改为datasets字段以保持一致性
                "results": [],   # 保留results字段以向后兼容
                "total_count": 0,
                "total": 0       # 添加total字段以保持一致性
            }
    
    async def _parse_query(self, query_text: str, dataset_name: Optional[str] = None) -> Dict[str, Any]:
        """解析自然语言查询
        
        Args:
            query_text: 查询文本
            dataset_name: 指定的数据集名称
            
        Returns:
            解析后的查询结构
        """
        parsed = {
            "original_query": query_text,
            "query_type": "search",
            "target_datasets": [],
            "filters": {},
            "keywords": [],
            "categories": [],
            "sources": [],
            "intent": "general_search"
        }
        
        query_lower = query_text.lower()
        
        # 解析查询类型
        if any(word in query_lower for word in ["list", "show", "display", "all"]):
            parsed["query_type"] = "list"
            parsed["intent"] = "list_datasets"
        elif any(word in query_lower for word in ["find", "search", "look for"]):
            parsed["query_type"] = "search"
            parsed["intent"] = "search_datasets"
        elif any(word in query_lower for word in ["info", "details", "about"]):
            parsed["query_type"] = "info"
            parsed["intent"] = "get_info"
        elif any(word in query_lower for word in ["filter", "where", "with"]):
            parsed["query_type"] = "filter"
            parsed["intent"] = "filter_samples"
        
        # 解析数据集名称
        if dataset_name:
            parsed["target_datasets"].append(dataset_name)
        else:
            # 从查询文本中提取数据集名称
            dataset_patterns = [
                r"\b(coco|imagenet|squad|mnist|cifar|glue)\b",
                r"\b([a-zA-Z0-9_-]+)\s+dataset\b",
                r"dataset\s+([a-zA-Z0-9_-]+)\b"
            ]
            
            for pattern in dataset_patterns:
                matches = re.findall(pattern, query_lower)
                for match in matches:
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]
                    if match and match not in parsed["target_datasets"]:
                        parsed["target_datasets"].append(match)
        
        # 解析类别
        category_keywords = {
            "vision": ["image", "vision", "visual", "photo", "picture", "object detection", "classification"],
            "nlp": ["text", "nlp", "language", "sentiment", "translation", "question answering"],
            "audio": ["audio", "speech", "sound", "music", "voice"],
            "multimodal": ["multimodal", "multi-modal", "vision-language"]
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                parsed["categories"].append(category)
        
        # 解析来源
        source_keywords = {
            "modelscope": ["modelscope", "ms"],
            "huggingface": ["huggingface", "hf", "hugging face"],
            "kaggle": ["kaggle"],
            "github": ["github"]
        }
        
        for source, keywords in source_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                parsed["sources"].append(source)
        
        # 解析过滤条件
        filters = {}
        
        # 大小过滤
        size_patterns = [
            (r"larger than (\d+)\s*(mb|gb|tb)", "min_size"),
            (r"smaller than (\d+)\s*(mb|gb|tb)", "max_size"),
            (r"more than (\d+)\s*samples", "min_samples"),
            (r"less than (\d+)\s*samples", "max_samples")
        ]
        
        for pattern, filter_key in size_patterns:
            match = re.search(pattern, query_lower)
            if match:
                value = int(match.group(1))
                unit = match.group(2) if len(match.groups()) > 1 else None
                
                if "size" in filter_key and unit:
                    # 转换为字节
                    multipliers = {"mb": 1024*1024, "gb": 1024*1024*1024, "tb": 1024*1024*1024*1024}
                    value *= multipliers.get(unit, 1)
                
                filters[filter_key] = value
        
        # 标签过滤
        tag_match = re.search(r"tagged with ([a-zA-Z0-9_,-]+)", query_lower)
        if tag_match:
            tags = [tag.strip() for tag in tag_match.group(1).split(",")]
            filters["tags"] = tags
        
        parsed["filters"] = filters
        
        # 提取关键词
        # 移除停用词和常见词汇
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with",
            "by", "from", "up", "about", "into", "through", "during", "before", "after",
            "above", "below", "between", "among", "dataset", "datasets", "data", "find",
            "search", "show", "list", "get", "all", "some", "any", "that", "this", "these",
            "those", "i", "you", "he", "she", "it", "we", "they", "me", "him", "her", "us", "them"
        }
        
        # 提取英文和中文关键词
        english_words = re.findall(r"\b[a-zA-Z]{2,}\b", query_lower)
        chinese_text = re.findall(r"[\u4e00-\u9fff]+", query_lower)
        
        # 过滤英文停用词
        english_keywords = [word for word in english_words if word not in stop_words and len(word) > 2]
        
        # 中文关键词提取 - 简单的基于常见词汇的分词
        chinese_keywords = []
        for text in chinese_text:
            # 提取常见的中文关键词
            common_keywords = [
                '中文', '英文', '文本', '图像', '音频', '视频', '数据集', '分类', '检测', '识别',
                '情感', '分析', '翻译', '问答', '对话', '生成', '预测', '推荐', '搜索',
                '新闻', '评论', '微博', '论文', '书籍', '电影', '音乐', '游戏',
                '医疗', '金融', '教育', '科技', '体育', '娱乐', '政治', '经济'
            ]
            
            # 检查文本中是否包含这些关键词
            for keyword in common_keywords:
                if keyword in text and keyword not in chinese_keywords:
                    chinese_keywords.append(keyword)
            
            # 如果没有找到常见关键词，且文本较短，直接使用
            if not chinese_keywords and len(text) <= 4:
                chinese_keywords.append(text)
        
        # 合并关键词
        all_keywords = english_keywords + chinese_keywords
        parsed["keywords"] = list(set(all_keywords))  # 去重
        
        return parsed
    
    async def _create_query_history(
        self,
        query_text: str,
        parsed_query: Dict[str, Any],
        session_id: Optional[str]
    ) -> QueryHistory:
        """创建查询历史记录
        
        Args:
            query_text: 原始查询文本
            parsed_query: 解析后的查询
            session_id: 会话ID
            
        Returns:
            查询历史对象
        """
        query_data = {
            "query_text": query_text,
            "query_type": parsed_query["query_type"],
            "parsed_query": parsed_query,
            "target_dataset": parsed_query["target_datasets"][0] if parsed_query["target_datasets"] else None,
            "filter_conditions": parsed_query["filters"],
            "session_id": session_id,
            "status": "executing"
        }
        
        return await self.db_service.create_query_history(query_data)
    
    async def _execute_query(
        self,
        parsed_query: Dict[str, Any],
        limit: int,
        include_metadata: bool,
        query_history_id: int
    ) -> Dict[str, Any]:
        """执行查询
        
        Args:
            parsed_query: 解析后的查询
            limit: 结果限制
            include_metadata: 是否包含元数据
            query_history_id: 查询历史ID
            
        Returns:
            查询结果
        """
        start_time = datetime.now()
        
        try:
            # 根据查询类型执行不同的逻辑
            if parsed_query["query_type"] == "list":
                results = await self._execute_list_query(parsed_query, limit)
            elif parsed_query["query_type"] == "search":
                results = await self._execute_search_query(parsed_query, limit)
            elif parsed_query["query_type"] == "info":
                results = await self._execute_info_query(parsed_query, limit)
            elif parsed_query["query_type"] == "filter":
                results = await self._execute_filter_query(parsed_query, limit)
            else:
                results = await self._execute_search_query(parsed_query, limit)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # 构建响应
            response = {
                "success": True,
                "query_type": parsed_query["query_type"],
                "intent": parsed_query["intent"],
                "datasets": results,  # 改为datasets字段以保持一致性
                "results": results,   # 保留results字段以向后兼容
                "total_count": len(results),
                "total": len(results),  # 添加total字段以保持一致性
                "execution_time": execution_time,
                "query_history_id": query_history_id
            }
            
            if include_metadata:
                response["metadata"] = {
                    "parsed_query": parsed_query,
                    "timestamp": datetime.now().isoformat(),
                    "cache_key": self._generate_cache_key(
                        parsed_query["original_query"], 
                        parsed_query["target_datasets"][0] if parsed_query["target_datasets"] else None,
                        limit, 
                        include_metadata
                    )
                }
            
            return response
            
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            self.logger.error(f"执行查询失败: {e}")
            
            return {
                "success": False,
                "error": str(e),
                "query_type": parsed_query["query_type"],
                "datasets": [],  # 改为datasets字段以保持一致性
                "results": [],   # 保留results字段以向后兼容
                "total_count": 0,
                "total": 0,      # 添加total字段以保持一致性
                "execution_time": execution_time,
                "query_history_id": query_history_id
            }
    
    async def _execute_list_query(self, parsed_query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """执行列表查询"""
        # 构建过滤条件
        filters = {}
        
        if parsed_query["categories"]:
            filters["category"] = parsed_query["categories"]
        
        if parsed_query["sources"]:
            filters["source"] = parsed_query["sources"]
        
        # 查询数据集
        datasets = await self.db_service.get_datasets(
            category=filters.get("category")[0] if filters.get("category") else None,
            source=filters.get("source")[0] if filters.get("source") else None,
            limit=limit
        )
        
        return [await self._format_dataset_result(dataset) for dataset in datasets]
    
    async def _execute_search_query(self, parsed_query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """执行搜索查询"""
        results = []
        
        # 如果指定了数据集名称，直接查询
        if parsed_query["target_datasets"]:
            for dataset_name in parsed_query["target_datasets"]:
                dataset = await self.db_service.get_dataset_by_name(dataset_name)
                if dataset:
                    results.append(await self._format_dataset_result(dataset))
        else:
            # 基于关键词搜索
            search_terms = parsed_query["keywords"]
            if search_terms:
                # 尝试每个关键词单独搜索，然后合并结果
                found_datasets = set()
                
                for term in search_terms[:5]:  # 限制关键词数量
                    datasets = await self.db_service.get_datasets(
                        search=term,
                        source=parsed_query["sources"][0] if parsed_query["sources"] else None,
                        limit=limit * 2  # 增加限制以获得更多候选
                    )
                    for dataset in datasets:
                        if dataset.id not in found_datasets:
                            found_datasets.add(dataset.id)
                            results.append(await self._format_dataset_result(dataset))
                            if len(results) >= limit:
                                break
                    if len(results) >= limit:
                        break
                
                # 如果没有结果且有分类信息，尝试按分类搜索
                if not results and parsed_query["categories"]:
                    datasets = await self.db_service.get_datasets(
                        category=parsed_query["categories"][0],
                        source=parsed_query["sources"][0] if parsed_query["sources"] else None,
                        limit=limit
                    )
                    results.extend([await self._format_dataset_result(dataset) for dataset in datasets])
            elif parsed_query["categories"] or parsed_query["sources"]:
                # 如果没有关键词但有分类或来源信息，按分类/来源搜索
                datasets = await self.db_service.get_datasets(
                    category=parsed_query["categories"][0] if parsed_query["categories"] else None,
                    source=parsed_query["sources"][0] if parsed_query["sources"] else None,
                    limit=limit
                )
                results.extend([await self._format_dataset_result(dataset) for dataset in datasets])
        
        return results[:limit]
    
    async def _execute_info_query(self, parsed_query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """执行信息查询"""
        results = []
        
        if parsed_query["target_datasets"]:
            for dataset_name in parsed_query["target_datasets"]:
                dataset = await self.db_service.get_dataset_by_name(dataset_name)
                if dataset:
                    result = await self._format_dataset_result(dataset, detailed=True)
                    results.append(result)
        
        return results
    
    async def _execute_filter_query(self, parsed_query: Dict[str, Any], limit: int) -> List[Dict[str, Any]]:
        """执行过滤查询"""
        # 获取所有数据集
        all_datasets = await self.db_service.get_datasets(limit=1000)
        
        # 应用过滤条件
        filtered_datasets = []
        for dataset in all_datasets:
            if await self._match_dataset_filters(dataset, parsed_query["filters"]):
                filtered_datasets.append(dataset)
        
        return [await self._format_dataset_result(dataset) for dataset in filtered_datasets[:limit]]
    
    async def _match_dataset_filters(self, dataset: Dataset, filters: Dict[str, Any]) -> bool:
        """检查数据集是否匹配过滤条件"""
        for filter_key, filter_value in filters.items():
            if filter_key == "min_size" and dataset.size_bytes:
                if dataset.size_bytes < filter_value:
                    return False
            elif filter_key == "max_size" and dataset.size_bytes:
                if dataset.size_bytes > filter_value:
                    return False
            elif filter_key == "min_samples" and dataset.total_samples:
                if dataset.total_samples < filter_value:
                    return False
            elif filter_key == "max_samples" and dataset.total_samples:
                if dataset.total_samples > filter_value:
                    return False
            elif filter_key == "tags" and dataset.tags:
                if not any(tag in dataset.tags for tag in filter_value):
                    return False
        
        return True
    
    async def _format_dataset_result(self, dataset: Dataset, detailed: bool = False) -> Dict[str, Any]:
        """格式化数据集结果
        
        Args:
            dataset: 数据集对象
            detailed: 是否返回详细信息
            
        Returns:
            格式化的数据集信息
        """
        result = {
            "id": dataset.id,
            "name": dataset.name,
            "display_name": dataset.display_name or dataset.name,
            "description": dataset.description,
            "source": dataset.source,
            "category": dataset.category,
            "total_samples": dataset.total_samples,
            "tags": dataset.tags or []
        }
        
        if detailed:
            result.update({
                "source_id": dataset.source_id,
                "size_bytes": dataset.size_bytes,
                "size_human": self._format_bytes(dataset.size_bytes) if dataset.size_bytes else None,
                "features": dataset.features,
                "schema_info": dataset.schema_info,
                "created_at": dataset.created_at.isoformat() if dataset.created_at else None,
                "updated_at": dataset.updated_at.isoformat() if dataset.updated_at else None,
                "last_accessed": dataset.last_accessed,
                "is_active": dataset.is_active
            })
            
            # 添加子集信息
            if hasattr(dataset, 'subsets') and dataset.subsets:
                result["subsets"] = [
                    {
                        "name": subset.name,
                        "split": subset.split,
                        "sample_count": subset.sample_count
                    }
                    for subset in dataset.subsets
                ]
        
        return result
    
    async def _update_query_history(self, query_history_id: int, result: Dict[str, Any]):
        """更新查询历史
        
        Args:
            query_history_id: 查询历史ID
            result: 查询结果
        """
        update_data = {
            "status": "completed" if result["success"] else "failed",
            "result_count": result["total_count"],
            "execution_time": result["execution_time"]
        }
        
        if not result["success"]:
            update_data["error_message"] = result.get("error")
        
        await self.db_service.update_query_history(query_history_id, update_data)
        
        # 创建查询结果记录
        if result["success"] and result.get("datasets", result.get("results", [])):
            results_data = result.get("datasets", result.get("results", []))
            for index, sample_data in enumerate(results_data):
                query_result = {
                    "query_id": query_history_id,
                    "sample_index": index,
                    "sample_data": sample_data,
                    "sample_metadata": {"source": "dataset_query"},
                    "relevance_score": 1.0
                }
                await self.db_service.create_query_result(query_result)
    
    def _format_bytes(self, bytes_size: int) -> str:
        """格式化字节大小为人类可读格式"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if bytes_size < 1024.0:
                return f"{bytes_size:.1f} {unit}"
            bytes_size /= 1024.0
        return f"{bytes_size:.1f} PB"
    
    def _generate_cache_key(
        self,
        query_text: str,
        dataset_name: Optional[str],
        limit: int,
        include_metadata: bool
    ) -> str:
        """生成缓存键"""
        key_parts = [
            f"query:{query_text}",
            f"dataset:{dataset_name or 'all'}",
            f"limit:{limit}",
            f"metadata:{include_metadata}"
        ]
        return ":".join(key_parts)