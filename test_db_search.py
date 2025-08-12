#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from modelscope_mcp.services.database import DatabaseService
from modelscope_mcp.core.config import Config

async def test_database_search():
    """测试数据库搜索功能"""
    try:
        print("🔍 测试数据库搜索功能...")
        
        # 初始化服务
        config = Config()
        db = DatabaseService(config)
        await db.initialize()
        
        # 1. 查看所有数据集
        print("\n1. 所有数据集:")
        all_datasets = await db.get_datasets(limit=10)
        for dataset in all_datasets:
            print(f"   - {dataset.name}")
            print(f"     描述: {dataset.description}")
            print(f"     标签: {dataset.tags}")
            print(f"     分类: {dataset.category}")
            print()
        
        # 2. 测试搜索功能
        print("2. 测试搜索功能:")
        search_terms = ['中文', 'chinese', 'text', 'classification', '文本']
        
        for term in search_terms:
            print(f"\n   搜索: '{term}'")
            results = await db.get_datasets(search=term, limit=5)
            print(f"   结果: {len(results)} 个数据集")
            for dataset in results:
                print(f"     - {dataset.name}")
        
        # 3. 测试分类搜索
        print("\n3. 测试分类搜索:")
        categories = ['text-classification', 'nlp', 'vision']
        
        for category in categories:
            print(f"\n   分类: '{category}'")
            results = await db.get_datasets(category=category, limit=5)
            print(f"   结果: {len(results)} 个数据集")
            for dataset in results:
                print(f"     - {dataset.name}")
        
        await db.close()
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_database_search())