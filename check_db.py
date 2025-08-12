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

async def check_database():
    """检查数据库中的数据集"""
    try:
        print("🔍 检查数据库中的数据集...")
        
        # 初始化服务
        config = Config()
        db = DatabaseService(config)
        await db.initialize()
        
        # 查询数据集
        datasets = await db.get_datasets(limit=10)
        print(f"📊 数据库中有 {len(datasets)} 个数据集")
        
        if datasets:
            print("\n前3个数据集:")
            for i, dataset in enumerate(datasets[:3], 1):
                desc = dataset.description[:50] if dataset.description else "无描述"
                print(f"  {i}. {dataset.name}: {desc}...")
        else:
            print("❌ 数据库中没有数据集数据")
            print("💡 这解释了为什么查询返回0个结果")
        
        await db.close()
        
    except Exception as e:
        print(f"❌ 检查数据库失败: {e}")

if __name__ == "__main__":
    asyncio.run(check_database())