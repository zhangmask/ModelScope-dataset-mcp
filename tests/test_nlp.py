"""自然语言处理模块测试

测试NLP查询解析功能。
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any, List

from src.modelscope_mcp.nlp.query_parser import (
    QueryParser, QueryIntent, QueryEntity, ParsedQuery
)
from src.modelscope_mcp.nlp.intent_classifier import (
    IntentClassifier, Intent, IntentResult
)
from src.modelscope_mcp.nlp.entity_extractor import (
    EntityExtractor, EntityType, Entity
)


class TestQueryEntity:
    """测试查询实体"""
    
    @pytest.mark.unit
    def test_query_entity_creation(self):
        """测试查询实体创建"""
        entity = QueryEntity(
            type="dataset_name",
            value="squad",
            confidence=0.95,
            start_pos=10,
            end_pos=15
        )
        
        assert entity.type == "dataset_name"
        assert entity.value == "squad"
        assert entity.confidence == 0.95
        assert entity.start_pos == 10
        assert entity.end_pos == 15
    
    @pytest.mark.unit
    def test_query_entity_to_dict(self):
        """测试转换为字典"""
        entity = QueryEntity(
            type="task_type",
            value="classification",
            confidence=0.8
        )
        
        data = entity.to_dict()
        
        assert data["type"] == "task_type"
        assert data["value"] == "classification"
        assert data["confidence"] == 0.8
        assert "start_pos" in data
        assert "end_pos" in data


class TestQueryIntent:
    """测试查询意图"""
    
    @pytest.mark.unit
    def test_query_intent_creation(self):
        """测试查询意图创建"""
        intent = QueryIntent(
            name="list_datasets",
            confidence=0.9,
            parameters={
                "task_type": "nlp",
                "limit": 10
            }
        )
        
        assert intent.name == "list_datasets"
        assert intent.confidence == 0.9
        assert intent.parameters["task_type"] == "nlp"
        assert intent.parameters["limit"] == 10
    
    @pytest.mark.unit
    def test_query_intent_to_dict(self):
        """测试转换为字典"""
        intent = QueryIntent(
            name="search_datasets",
            confidence=0.85,
            parameters={"query": "sentiment analysis"}
        )
        
        data = intent.to_dict()
        
        assert data["name"] == "search_datasets"
        assert data["confidence"] == 0.85
        assert data["parameters"]["query"] == "sentiment analysis"


class TestParsedQuery:
    """测试解析后的查询"""
    
    @pytest.mark.unit
    def test_parsed_query_creation(self):
        """测试解析后查询创建"""
        intent = QueryIntent(name="list_datasets", confidence=0.9)
        entities = [
            QueryEntity(type="task_type", value="nlp", confidence=0.8),
            QueryEntity(type="limit", value="5", confidence=0.7)
        ]
        
        parsed = ParsedQuery(
            original_query="Show me 5 NLP datasets",
            intent=intent,
            entities=entities,
            confidence=0.85
        )
        
        assert parsed.original_query == "Show me 5 NLP datasets"
        assert parsed.intent.name == "list_datasets"
        assert len(parsed.entities) == 2
        assert parsed.confidence == 0.85
    
    @pytest.mark.unit
    def test_parsed_query_to_dict(self):
        """测试转换为字典"""
        intent = QueryIntent(name="get_dataset_info", confidence=0.95)
        entities = [
            QueryEntity(type="dataset_name", value="squad", confidence=0.9)
        ]
        
        parsed = ParsedQuery(
            original_query="Tell me about squad dataset",
            intent=intent,
            entities=entities,
            confidence=0.9
        )
        
        data = parsed.to_dict()
        
        assert data["original_query"] == "Tell me about squad dataset"
        assert data["intent"]["name"] == "get_dataset_info"
        assert len(data["entities"]) == 1
        assert data["entities"][0]["type"] == "dataset_name"
        assert data["confidence"] == 0.9


class TestEntity:
    """测试实体"""
    
    @pytest.mark.unit
    def test_entity_creation(self):
        """测试实体创建"""
        entity = Entity(
            text="squad",
            label="DATASET",
            start=10,
            end=15,
            confidence=0.95
        )
        
        assert entity.text == "squad"
        assert entity.label == "DATASET"
        assert entity.start == 10
        assert entity.end == 15
        assert entity.confidence == 0.95


class TestEntityType:
    """测试实体类型"""
    
    @pytest.mark.unit
    def test_entity_type_values(self):
        """测试实体类型值"""
        assert EntityType.DATASET_NAME.value == "dataset_name"
        assert EntityType.TASK_TYPE.value == "task_type"
        assert EntityType.LANGUAGE.value == "language"
        assert EntityType.NUMBER.value == "number"
        assert EntityType.KEYWORD.value == "keyword"


class TestIntent:
    """测试意图"""
    
    @pytest.mark.unit
    def test_intent_values(self):
        """测试意图值"""
        assert Intent.LIST_DATASETS.value == "list_datasets"
        assert Intent.SEARCH_DATASETS.value == "search_datasets"
        assert Intent.GET_DATASET_INFO.value == "get_dataset_info"
        assert Intent.FILTER_SAMPLES.value == "filter_samples"
        assert Intent.UNKNOWN.value == "unknown"


class TestIntentResult:
    """测试意图结果"""
    
    @pytest.mark.unit
    def test_intent_result_creation(self):
        """测试意图结果创建"""
        result = IntentResult(
            intent=Intent.LIST_DATASETS,
            confidence=0.9,
            features={
                "has_list_keyword": True,
                "has_dataset_keyword": True
            }
        )
        
        assert result.intent == Intent.LIST_DATASETS
        assert result.confidence == 0.9
        assert result.features["has_list_keyword"] is True
        assert result.features["has_dataset_keyword"] is True


class TestEntityExtractor:
    """测试实体提取器"""
    
    @pytest.fixture
    def entity_extractor(self):
        """创建实体提取器实例"""
        return EntityExtractor()
    
    @pytest.mark.unit
    def test_extract_dataset_names(self, entity_extractor):
        """测试提取数据集名称"""
        text = "I want to use squad and glue datasets for my project"
        entities = entity_extractor.extract_entities(text)
        
        dataset_entities = [e for e in entities if e.label == "DATASET"]
        assert len(dataset_entities) >= 2
        
        dataset_names = [e.text.lower() for e in dataset_entities]
        assert "squad" in dataset_names
        assert "glue" in dataset_names
    
    @pytest.mark.unit
    def test_extract_task_types(self, entity_extractor):
        """测试提取任务类型"""
        text = "Show me classification and question answering datasets"
        entities = entity_extractor.extract_entities(text)
        
        task_entities = [e for e in entities if e.label == "TASK"]
        assert len(task_entities) >= 2
        
        task_types = [e.text.lower() for e in task_entities]
        assert any("classification" in task for task in task_types)
        assert any("question" in task or "answering" in task for task in task_types)
    
    @pytest.mark.unit
    def test_extract_numbers(self, entity_extractor):
        """测试提取数字"""
        text = "Give me 10 datasets with at least 1000 samples"
        entities = entity_extractor.extract_entities(text)
        
        number_entities = [e for e in entities if e.label == "NUMBER"]
        assert len(number_entities) >= 2
        
        numbers = [e.text for e in number_entities]
        assert "10" in numbers
        assert "1000" in numbers
    
    @pytest.mark.unit
    def test_extract_languages(self, entity_extractor):
        """测试提取语言"""
        text = "I need English and Chinese datasets for multilingual training"
        entities = entity_extractor.extract_entities(text)
        
        language_entities = [e for e in entities if e.label == "LANGUAGE"]
        assert len(language_entities) >= 2
        
        languages = [e.text.lower() for e in language_entities]
        assert "english" in languages
        assert "chinese" in languages
    
    @pytest.mark.unit
    def test_extract_keywords(self, entity_extractor):
        """测试提取关键词"""
        text = "Find sentiment analysis datasets with high accuracy"
        entities = entity_extractor.extract_entities(text)
        
        keyword_entities = [e for e in entities if e.label == "KEYWORD"]
        assert len(keyword_entities) > 0
        
        keywords = [e.text.lower() for e in keyword_entities]
        assert any("sentiment" in keyword for keyword in keywords)
        assert any("accuracy" in keyword for keyword in keywords)
    
    @pytest.mark.unit
    def test_entity_positions(self, entity_extractor):
        """测试实体位置"""
        text = "Show me squad dataset"
        entities = entity_extractor.extract_entities(text)
        
        squad_entity = next((e for e in entities if e.text.lower() == "squad"), None)
        assert squad_entity is not None
        assert squad_entity.start >= 0
        assert squad_entity.end > squad_entity.start
        assert text[squad_entity.start:squad_entity.end].lower() == "squad"
    
    @pytest.mark.unit
    def test_entity_confidence(self, entity_extractor):
        """测试实体置信度"""
        text = "I need the IMDB movie review dataset"
        entities = entity_extractor.extract_entities(text)
        
        for entity in entities:
            assert 0.0 <= entity.confidence <= 1.0
    
    @pytest.mark.unit
    def test_empty_text(self, entity_extractor):
        """测试空文本"""
        entities = entity_extractor.extract_entities("")
        assert entities == []
    
    @pytest.mark.unit
    def test_no_entities_text(self, entity_extractor):
        """测试无实体文本"""
        text = "Hello world"
        entities = entity_extractor.extract_entities(text)
        # 可能有一些通用关键词被提取，但不应该有特定的数据集或任务实体
        dataset_entities = [e for e in entities if e.label == "DATASET"]
        assert len(dataset_entities) == 0


class TestIntentClassifier:
    """测试意图分类器"""
    
    @pytest.fixture
    def intent_classifier(self):
        """创建意图分类器实例"""
        return IntentClassifier()
    
    @pytest.mark.unit
    def test_classify_list_datasets(self, intent_classifier):
        """测试分类列出数据集意图"""
        queries = [
            "List all datasets",
            "Show me available datasets",
            "What datasets do you have?",
            "Give me a list of datasets",
            "Display datasets"
        ]
        
        for query in queries:
            result = intent_classifier.classify(query)
            assert result.intent == Intent.LIST_DATASETS
            assert result.confidence > 0.5
    
    @pytest.mark.unit
    def test_classify_search_datasets(self, intent_classifier):
        """测试分类搜索数据集意图"""
        queries = [
            "Search for NLP datasets",
            "Find sentiment analysis datasets",
            "Look for question answering data",
            "I need datasets about computer vision",
            "Search datasets related to classification"
        ]
        
        for query in queries:
            result = intent_classifier.classify(query)
            assert result.intent == Intent.SEARCH_DATASETS
            assert result.confidence > 0.5
    
    @pytest.mark.unit
    def test_classify_get_dataset_info(self, intent_classifier):
        """测试分类获取数据集信息意图"""
        queries = [
            "Tell me about squad dataset",
            "What is the IMDB dataset?",
            "Give me information about glue",
            "Describe the CoNLL dataset",
            "Show details of cifar10"
        ]
        
        for query in queries:
            result = intent_classifier.classify(query)
            assert result.intent == Intent.GET_DATASET_INFO
            assert result.confidence > 0.5
    
    @pytest.mark.unit
    def test_classify_filter_samples(self, intent_classifier):
        """测试分类过滤样本意图"""
        queries = [
            "Show me samples from squad dataset",
            "Get examples from IMDB reviews",
            "Filter positive samples",
            "Give me 10 samples with label 'positive'",
            "Show training examples"
        ]
        
        for query in queries:
            result = intent_classifier.classify(query)
            assert result.intent == Intent.FILTER_SAMPLES
            assert result.confidence > 0.5
    
    @pytest.mark.unit
    def test_classify_unknown(self, intent_classifier):
        """测试分类未知意图"""
        queries = [
            "What's the weather today?",
            "How to cook pasta?",
            "Tell me a joke",
            "What time is it?",
            "Random text without meaning"
        ]
        
        for query in queries:
            result = intent_classifier.classify(query)
            assert result.intent == Intent.UNKNOWN
    
    @pytest.mark.unit
    def test_confidence_scores(self, intent_classifier):
        """测试置信度分数"""
        # 明确的查询应该有高置信度
        clear_query = "List all available datasets"
        result = intent_classifier.classify(clear_query)
        assert result.confidence > 0.8
        
        # 模糊的查询应该有较低置信度
        ambiguous_query = "show data"
        result = intent_classifier.classify(ambiguous_query)
        assert result.confidence < 0.8
    
    @pytest.mark.unit
    def test_features_extraction(self, intent_classifier):
        """测试特征提取"""
        query = "List all NLP datasets"
        result = intent_classifier.classify(query)
        
        assert isinstance(result.features, dict)
        assert len(result.features) > 0
        
        # 应该包含一些相关特征
        feature_keys = list(result.features.keys())
        assert any("list" in key.lower() for key in feature_keys)
        assert any("dataset" in key.lower() for key in feature_keys)
    
    @pytest.mark.unit
    def test_empty_query(self, intent_classifier):
        """测试空查询"""
        result = intent_classifier.classify("")
        assert result.intent == Intent.UNKNOWN
        assert result.confidence == 0.0
    
    @pytest.mark.unit
    def test_case_insensitive(self, intent_classifier):
        """测试大小写不敏感"""
        queries = [
            "LIST ALL DATASETS",
            "list all datasets",
            "List All Datasets",
            "LiSt AlL dAtAsEtS"
        ]
        
        results = [intent_classifier.classify(query) for query in queries]
        
        # 所有结果应该相同
        intents = [r.intent for r in results]
        assert all(intent == Intent.LIST_DATASETS for intent in intents)
        
        # 置信度应该相似
        confidences = [r.confidence for r in results]
        assert max(confidences) - min(confidences) < 0.1


class TestQueryParser:
    """测试查询解析器"""
    
    @pytest.fixture
    def query_parser(self):
        """创建查询解析器实例"""
        return QueryParser()
    
    @pytest.mark.unit
    async def test_parse_list_datasets_query(self, query_parser):
        """测试解析列出数据集查询"""
        query = "Show me 10 NLP datasets"
        parsed = await query_parser.parse(query)
        
        assert parsed.original_query == query
        assert parsed.intent.name == "list_datasets"
        assert parsed.confidence > 0.5
        
        # 检查提取的实体
        entity_types = [e.type for e in parsed.entities]
        assert "number" in entity_types  # "10"
        assert "task_type" in entity_types  # "NLP"
    
    @pytest.mark.unit
    async def test_parse_search_datasets_query(self, query_parser):
        """测试解析搜索数据集查询"""
        query = "Find sentiment analysis datasets in English"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name == "search_datasets"
        assert parsed.confidence > 0.5
        
        # 检查提取的实体
        entity_values = [e.value.lower() for e in parsed.entities]
        assert any("sentiment" in value for value in entity_values)
        assert any("english" in value for value in entity_values)
    
    @pytest.mark.unit
    async def test_parse_get_dataset_info_query(self, query_parser):
        """测试解析获取数据集信息查询"""
        query = "Tell me about the squad dataset"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name == "get_dataset_info"
        assert parsed.confidence > 0.5
        
        # 检查数据集名称实体
        dataset_entities = [e for e in parsed.entities if e.type == "dataset_name"]
        assert len(dataset_entities) > 0
        assert any("squad" in e.value.lower() for e in dataset_entities)
    
    @pytest.mark.unit
    async def test_parse_filter_samples_query(self, query_parser):
        """测试解析过滤样本查询"""
        query = "Show me 5 positive samples from IMDB dataset"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name == "filter_samples"
        assert parsed.confidence > 0.5
        
        # 检查提取的实体
        entity_types = [e.type for e in parsed.entities]
        entity_values = [e.value.lower() for e in parsed.entities]
        
        assert "number" in entity_types  # "5"
        assert "dataset_name" in entity_types  # "IMDB"
        assert any("positive" in value for value in entity_values)
    
    @pytest.mark.unit
    async def test_parse_complex_query(self, query_parser):
        """测试解析复杂查询"""
        query = "Find 20 Chinese text classification datasets with more than 1000 samples"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name in ["search_datasets", "list_datasets"]
        assert parsed.confidence > 0.3
        
        # 检查提取的多个实体
        entity_types = [e.type for e in parsed.entities]
        entity_values = [e.value.lower() for e in parsed.entities]
        
        assert "number" in entity_types  # "20", "1000"
        assert "language" in entity_types  # "Chinese"
        assert "task_type" in entity_types  # "classification"
    
    @pytest.mark.unit
    async def test_parse_ambiguous_query(self, query_parser):
        """测试解析模糊查询"""
        query = "data"
        parsed = await query_parser.parse(query)
        
        assert parsed.original_query == query
        # 模糊查询可能被分类为任何意图或未知
        assert parsed.confidence < 0.8
    
    @pytest.mark.unit
    async def test_parse_unknown_query(self, query_parser):
        """测试解析未知查询"""
        query = "What's the weather like today?"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name == "unknown"
        assert parsed.confidence < 0.5
    
    @pytest.mark.unit
    async def test_parse_empty_query(self, query_parser):
        """测试解析空查询"""
        parsed = await query_parser.parse("")
        
        assert parsed.original_query == ""
        assert parsed.intent.name == "unknown"
        assert parsed.confidence == 0.0
        assert len(parsed.entities) == 0
    
    @pytest.mark.unit
    async def test_parse_query_with_parameters(self, query_parser):
        """测试解析带参数的查询"""
        query = "List datasets sorted by downloads in descending order"
        parsed = await query_parser.parse(query)
        
        assert parsed.intent.name == "list_datasets"
        
        # 检查意图参数
        params = parsed.intent.parameters
        assert "sort_by" in params or "order" in params
    
    @pytest.mark.unit
    async def test_parse_query_confidence_calculation(self, query_parser):
        """测试查询置信度计算"""
        # 高置信度查询
        high_conf_query = "List all available datasets"
        high_parsed = await query_parser.parse(high_conf_query)
        
        # 低置信度查询
        low_conf_query = "maybe show some stuff"
        low_parsed = await query_parser.parse(low_conf_query)
        
        assert high_parsed.confidence > low_parsed.confidence
    
    @pytest.mark.unit
    async def test_parse_query_entity_confidence(self, query_parser):
        """测试实体置信度"""
        query = "Show me squad and glue datasets"
        parsed = await query_parser.parse(query)
        
        for entity in parsed.entities:
            assert 0.0 <= entity.confidence <= 1.0
    
    @pytest.mark.unit
    async def test_parse_multilingual_query(self, query_parser):
        """测试多语言查询解析"""
        # 注意：这个测试假设解析器支持多语言
        # 如果不支持，可以跳过或修改
        queries = [
            "显示所有数据集",  # 中文
            "Mostrar todos los datasets",  # 西班牙语
            "Afficher tous les jeux de données"  # 法语
        ]
        
        for query in queries:
            parsed = await query_parser.parse(query)
            # 至少应该能解析出一些信息，即使置信度较低
            assert parsed.original_query == query
            assert isinstance(parsed.confidence, float)


@pytest.mark.integration
class TestNLPIntegration:
    """NLP模块集成测试"""
    
    @pytest.mark.unit
    async def test_full_nlp_pipeline(self):
        """测试完整NLP流水线"""
        query_parser = QueryParser()
        
        # 测试完整的解析流程
        query = "Find 10 English sentiment analysis datasets with high accuracy"
        parsed = await query_parser.parse(query)
        
        # 验证解析结果的完整性
        assert parsed.original_query == query
        assert parsed.intent is not None
        assert parsed.intent.name in ["search_datasets", "list_datasets"]
        assert len(parsed.entities) > 0
        assert 0.0 <= parsed.confidence <= 1.0
        
        # 验证实体提取的准确性
        entity_types = [e.type for e in parsed.entities]
        entity_values = [e.value.lower() for e in parsed.entities]
        
        assert "number" in entity_types
        assert "language" in entity_types
        assert "task_type" in entity_types
        assert any("10" in value for value in entity_values)
        assert any("english" in value for value in entity_values)
        assert any("sentiment" in value for value in entity_values)
    
    @pytest.mark.unit
    async def test_nlp_error_handling(self):
        """测试NLP错误处理"""
        query_parser = QueryParser()
        
        # 测试各种边界情况
        edge_cases = [
            "",  # 空字符串
            "   ",  # 只有空格
            "\n\t",  # 只有换行和制表符
            "!@#$%^&*()",  # 只有特殊字符
            "a" * 1000,  # 超长字符串
        ]
        
        for case in edge_cases:
            try:
                parsed = await query_parser.parse(case)
                # 应该能够处理而不抛出异常
                assert parsed is not None
                assert parsed.original_query == case
            except Exception as e:
                pytest.fail(f"Failed to handle edge case '{case}': {e}")
    
    @pytest.mark.unit
    async def test_nlp_performance(self):
        """测试NLP性能"""
        import time
        
        query_parser = QueryParser()
        query = "List all machine learning datasets"
        
        # 测试解析时间
        start_time = time.time()
        parsed = await query_parser.parse(query)
        end_time = time.time()
        
        parse_time = end_time - start_time
        
        # 解析时间应该在合理范围内（比如小于1秒）
        assert parse_time < 1.0
        assert parsed is not None
    
    @pytest.mark.unit
    async def test_nlp_consistency(self):
        """测试NLP一致性"""
        query_parser = QueryParser()
        query = "Show me NLP datasets"
        
        # 多次解析同一查询，结果应该一致
        results = []
        for _ in range(5):
            parsed = await query_parser.parse(query)
            results.append(parsed)
        
        # 验证意图一致性
        intents = [r.intent.name for r in results]
        assert all(intent == intents[0] for intent in intents)
        
        # 验证置信度一致性（允许小幅波动）
        confidences = [r.confidence for r in results]
        assert max(confidences) - min(confidences) < 0.1