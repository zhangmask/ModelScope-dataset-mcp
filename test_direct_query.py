#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from modelscope_mcp.tools.query_dataset import QueryDatasetHandler
from modelscope_mcp.tools.list_datasets import ListDatasetsHandler
from modelscope_mcp.services.database import DatabaseService
from modelscope_mcp.services.cache import CacheService
from modelscope_mcp.core.config import Config

async def test_direct_query():
    """直接测试查询功能"""
    try:
        print("🔍 直接测试数据集查询功能...")
        
        # 初始化服务
        config = Config()
        db = DatabaseService(config)
        await db.initialize()
        
        cache = CacheService(config)
        await cache.initialize()
        
        # 1. 先测试列出数据集
        print("\n1. 测试列出数据集:")
        list_handler = ListDatasetsHandler(db, cache)
        list_result = await list_handler.handle({
            'source': 'all',
            'limit': 10
        })
        print(f"   找到 {len(list_result.get('datasets', []))} 个数据集")
        
        if list_result.get('datasets'):
            for i, dataset in enumerate(list_result['datasets'][:3], 1):
                print(f"   {i}. {dataset['name']}: {dataset.get('description', 'N/A')[:50]}...")
        
        # 2. 测试查询数据集（不使用自然语言处理）
        print("\n2. 测试查询数据集（直接搜索）:")
        query_handler = QueryDatasetHandler(db, cache)
        
        # 测试直接搜索
        search_queries = [
            '中文',
            'chinese',
            'text',
            'classification'
        ]
        
        for query in search_queries:
            print(f"\n   搜索关键词: '{query}'")
            result = await query_handler.handle({
                'query': query,
                'limit': 3
            })
            datasets = result.get('datasets', [])
            print(f"   结果: {len(datasets)} 个数据集")
            
            if datasets:
                for dataset in datasets:
                    print(f"     - {dataset['name']}")
        
        # 3. 测试数据库直接查询
        print("\n3. 测试数据库直接查询:")
        all_datasets = await db.get_datasets(limit=10)
        print(f"   数据库中总共有 {len(all_datasets)} 个数据集")
        
        for dataset in all_datasets:
            print(f"   - {dataset.name}: {dataset.category}, tags: {dataset.tags}")
        
        await db.close()
        await cache.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_direct_query())