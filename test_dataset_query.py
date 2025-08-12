#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据集查询功能验证测试

这个脚本用于验证MCP服务器的数据集查询功能，包括：
1. 添加测试数据集
2. 测试数据集查询
3. 测试硅基流动API集成
4. 验证自然语言查询功能
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from modelscope_mcp.core.config import Config
    from modelscope_mcp.services.database import DatabaseService
    from modelscope_mcp.services.cache import CacheService
    from modelscope_mcp.tools.list_datasets import ListDatasetsHandler
    from modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
    from modelscope_mcp.tools.query_dataset import QueryDatasetHandler
    from modelscope_mcp.models.dataset import Dataset
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    sys.exit(1)


class DatasetQueryTester:
    """数据集查询功能测试器"""
    
    def __init__(self):
        self.config = None
        self.db_service = None
        self.cache_service = None
        self.handlers = {}
        self.test_datasets = []
    
    async def setup(self):
        """初始化测试环境"""
        try:
            print("🔧 初始化数据集查询测试环境...")
            
            # 加载配置
            self.config = Config()
            print("✅ 配置加载成功")
            
            # 初始化数据库服务
            self.db_service = DatabaseService(self.config)
            await self.db_service.initialize()
            print("✅ 数据库服务初始化成功")
            
            # 初始化缓存服务
            self.cache_service = CacheService(self.config)
            await self.cache_service.initialize()
            print("✅ 缓存服务初始化成功")
            
            # 初始化处理器
            self.handlers = {
                'list_datasets': ListDatasetsHandler(self.db_service, self.cache_service),
                'get_dataset_info': GetDatasetInfoHandler(self.db_service, self.cache_service),
                'query_dataset': QueryDatasetHandler(self.db_service, self.cache_service)
            }
            print("✅ 处理器初始化成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def add_test_datasets(self):
        """添加测试数据集"""
        print("\n📊 添加测试数据集...")
        
        test_datasets_data = [
            {
                "name": "chinese_text_classification",
                "display_name": "中文文本分类数据集",
                "description": "包含新闻、评论等多种类型的中文文本分类数据",
                "source": "modelscope",
                "source_id": "damo/nlp_structbert_sentiment-classification_chinese-base",
                "category": "text-classification",
                "tags": ["中文", "文本分类", "情感分析"],
                "total_samples": 10000,
                "size_bytes": 50000000
            },
            {
                "name": "english_sentiment_analysis",
                "display_name": "英文情感分析数据集",
                "description": "英文电影评论情感分析数据集",
                "source": "huggingface",
                "source_id": "imdb",
                "category": "text-classification",
                "tags": ["英文", "情感分析", "电影评论"],
                "total_samples": 50000,
                "size_bytes": 100000000
            },
            {
                "name": "chinese_ner_dataset",
                "display_name": "中文命名实体识别数据集",
                "description": "中文命名实体识别标注数据",
                "source": "modelscope",
                "source_id": "damo/nlp_structbert_named-entity-recognition_chinese-base",
                "category": "token-classification",
                "tags": ["中文", "命名实体识别", "NER"],
                "total_samples": 8000,
                "size_bytes": 30000000
            }
        ]
        
        try:
            for dataset_data in test_datasets_data:
                # 创建数据集对象
                dataset = Dataset(
                    name=dataset_data["name"],
                    display_name=dataset_data["display_name"],
                    description=dataset_data["description"],
                    source=dataset_data["source"],
                    source_id=dataset_data["source_id"],
                    category=dataset_data["category"],
                    tags=dataset_data["tags"],
                    total_samples=dataset_data["total_samples"],
                    size_bytes=dataset_data["size_bytes"],
                    created_at=datetime.now()
                )
                
                # 保存到数据库
                dataset_dict = {
                    "name": dataset.name,
                    "display_name": dataset.display_name,
                    "description": dataset.description,
                    "source": dataset.source,
                    "source_id": dataset.source_id,
                    "category": dataset.category,
                    "tags": dataset.tags,
                    "total_samples": dataset.total_samples,
                    "size_bytes": dataset.size_bytes,
                    "created_at": dataset.created_at
                }
                created_dataset = await self.db_service.create_dataset(dataset_dict)
                self.test_datasets.append(created_dataset)
                print(f"✅ 添加数据集: {created_dataset.display_name}")
            
            print(f"📊 成功添加 {len(self.test_datasets)} 个测试数据集")
            return True
            
        except Exception as e:
            print(f"❌ 添加测试数据集失败: {e}")
            return False
    
    async def test_list_datasets(self):
        """测试列出数据集功能"""
        print("\n🔍 测试列出数据集功能...")
        
        test_cases = [
            {"name": "列出所有数据集", "args": {}},
            {"name": "按分类筛选", "args": {"category": "text-classification"}},
            {"name": "按来源筛选", "args": {"source": "modelscope"}},
            {"name": "搜索关键词", "args": {"search": "中文"}}
        ]
        
        results = []
        
        for test_case in test_cases:
            try:
                result = await self.handlers['list_datasets'].handle(test_case["args"])
                success = result.get("success", False)
                count = len(result.get("datasets", []))
                
                print(f"  {test_case['name']}: {'✅' if success else '❌'} ({count} 个数据集)")
                results.append(success)
                
            except Exception as e:
                print(f"  {test_case['name']}: ❌ 错误: {e}")
                results.append(False)
        
        return all(results)
    
    async def test_dataset_info(self):
        """测试获取数据集信息功能"""
        print("\n🔍 测试获取数据集信息功能...")
        
        if not self.test_datasets:
            print("❌ 没有测试数据集")
            return False
        
        try:
            # 测试获取第一个数据集的信息
            dataset = self.test_datasets[0]
            result = await self.handlers['get_dataset_info'].handle({
                "dataset_name": dataset.name
            })
            
            success = result.get("success", False)
            dataset_info = result.get("dataset")
            
            if success and dataset_info:
                print(f"✅ 获取数据集信息成功: {dataset_info.get('display_name')}")
                print(f"  描述: {dataset_info.get('description', 'N/A')[:50]}...")
                print(f"  样本数: {dataset_info.get('total_samples', 'N/A')}")
                return True
            else:
                print(f"❌ 获取数据集信息失败")
                return False
                
        except Exception as e:
            print(f"❌ 测试获取数据集信息失败: {e}")
            return False
    
    async def test_natural_language_query(self):
        """测试自然语言查询功能"""
        print("\n🔍 测试自然语言查询功能...")
        
        queries = [
            "找一些中文文本分类的数据集",
            "我需要情感分析的数据",
            "有没有命名实体识别的数据集"
        ]
        
        results = []
        
        for query in queries:
            try:
                result = await self.handlers['query_dataset'].handle({
                    "query": query,
                    "limit": 3
                })
                
                success = result.get("success", False)
                datasets = result.get("datasets", [])
                
                print(f"  查询: '{query}'")
                print(f"    结果: {'✅' if success else '❌'} ({len(datasets)} 个数据集)")
                
                if datasets:
                    for i, dataset in enumerate(datasets[:2], 1):
                        print(f"    {i}. {dataset.get('display_name', dataset.get('name'))}")
                
                results.append(success)
                
            except Exception as e:
                print(f"  查询 '{query}': ❌ 错误: {e}")
                results.append(False)
        
        return any(results)  # 至少有一个查询成功
    
    async def test_siliconflow_integration(self):
        """测试硅基流动API集成"""
        print("\n🔍 测试硅基流动API集成...")
        
        try:
            # 检查配置
            config_file = Path("config.json")
            if not config_file.exists():
                print("❌ 配置文件不存在")
                return False
            
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                siliconflow_config = config_data.get('siliconflow', {})
            
            if not siliconflow_config.get('enabled'):
                print("❌ 硅基流动API未启用")
                return False
            
            api_key = siliconflow_config.get('api_key')
            api_url = siliconflow_config.get('api_url')
            
            print(f"✅ 硅基流动API配置正确")
            print(f"  API URL: {api_url}")
            print(f"  API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
            
            # 这里可以添加实际的API调用测试
            # 由于需要网络请求，暂时只验证配置
            
            return True
            
        except Exception as e:
            print(f"❌ 硅基流动API集成测试失败: {e}")
            return False
    
    async def cleanup(self):
        """清理测试环境"""
        try:
            if self.db_service:
                await self.db_service.close()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"❌ 清理失败: {e}")
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始数据集查询功能验证测试...")
        
        # 初始化
        if not await self.setup():
            return False
        
        try:
            # 添加测试数据
            await self.add_test_datasets()
            
            # 运行测试
            tests = [
                ("硅基流动API集成", self.test_siliconflow_integration()),
                ("列出数据集", self.test_list_datasets()),
                ("获取数据集信息", self.test_dataset_info()),
                ("自然语言查询", self.test_natural_language_query())
            ]
            
            results = {}
            
            for test_name, test_coro in tests:
                try:
                    result = await test_coro
                    results[test_name] = result
                except Exception as e:
                    print(f"❌ {test_name} 测试失败: {e}")
                    results[test_name] = False
            
            # 输出测试结果摘要
            print("\n📊 数据集查询功能验证结果摘要:")
            print("=" * 50)
            
            passed = 0
            total = len(results)
            
            for test_name, result in results.items():
                status = "✅ 通过" if result else "❌ 失败"
                print(f"  {test_name}: {status}")
                if result:
                    passed += 1
            
            print(f"\n总计: {passed}/{total} 个测试通过")
            
            if passed == total:
                print("🎉 所有数据集查询功能验证都通过了！")
                return True
            else:
                print(f"⚠️  有 {total - passed} 个测试失败")
                return False
                
        finally:
            await self.cleanup()


async def main():
    """主函数"""
    tester = DatasetQueryTester()
    success = await tester.run_all_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())