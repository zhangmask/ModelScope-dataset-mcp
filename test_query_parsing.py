#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from modelscope_mcp.tools.query_dataset import QueryDatasetHandler
from modelscope_mcp.services.database import DatabaseService
from modelscope_mcp.services.cache import CacheService
from modelscope_mcp.core.config import Config

async def test_query_parsing():
    """测试查询解析功能"""
    try:
        print("🔍 测试查询解析功能...")
        
        # 初始化服务
        config = Config()
        db = DatabaseService(config)
        cache = CacheService(config)
        await db.initialize()
        await cache.initialize()
        
        # 创建查询处理器
        handler = QueryDatasetHandler(db, cache)
        
        # 测试不同的查询
        test_queries = [
            "中文",
            "chinese", 
            "text",
            "classification",
            "文本分类",
            "find chinese datasets",
            "search for text classification",
            "list all datasets"
        ]
        
        for query in test_queries:
            print(f"\n查询: '{query}'")
            
            # 解析查询
            parsed = await handler._parse_query(query)
            print(f"  查询类型: {parsed['query_type']}")
            print(f"  意图: {parsed['intent']}")
            print(f"  关键词: {parsed['keywords']}")
            print(f"  目标数据集: {parsed['target_datasets']}")
            print(f"  分类: {parsed['categories']}")
            print(f"  来源: {parsed['sources']}")
            
            # 执行搜索查询
            if parsed['query_type'] == 'search':
                print("  执行搜索...")
                results = await handler._execute_search_query(parsed, 5)
                print(f"  搜索结果: {len(results)} 个数据集")
                for result in results:
                    print(f"    - {result['name']}")
        
        await db.close()
        await cache.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_query_parsing())