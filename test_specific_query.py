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

async def test_specific_query():
    """测试特定的查询"""
    try:
        print("🔍 测试特定查询...")
        
        # 初始化服务
        config = Config()
        db = DatabaseService(config)
        cache = CacheService(config)
        await db.initialize()
        await cache.initialize()
        
        # 创建查询处理器
        handler = QueryDatasetHandler(db, cache)
        
        # 测试MCP中使用的查询
        query = '找一些中文文本分类的数据集'
        print(f"\n查询: '{query}'")
        
        # 解析查询
        parsed = await handler._parse_query(query)
        print(f"  查询类型: {parsed['query_type']}")
        print(f"  意图: {parsed['intent']}")
        print(f"  关键词: {parsed['keywords']}")
        print(f"  目标数据集: {parsed['target_datasets']}")
        print(f"  分类: {parsed['categories']}")
        print(f"  来源: {parsed['sources']}")
        
        # 执行完整的查询处理
        print("\n执行完整查询处理...")
        result = await handler.handle({
            'query': query,
            'source': 'modelscope',
            'limit': 3
        })
        
        print(f"查询成功: {result.get('success', False)}")
        print(f"结果数量: {len(result.get('datasets', result.get('results', [])))}")
        
        if result.get('datasets') or result.get('results'):
            datasets = result.get('datasets', result.get('results', []))
            for dataset in datasets:
                print(f"  - {dataset.get('name', 'Unknown')}")
        
        if not result.get('success'):
            print(f"错误信息: {result.get('error', 'Unknown error')}")
        
        await db.close()
        await cache.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_specific_query())