#!/usr/bin/env python3
"""简单的功能测试"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_imports():
    """测试基本导入"""
    try:
        from modelscope_mcp.models.base import BaseModel
        from modelscope_mcp.models.dataset import Dataset
        from modelscope_mcp.models.query import QueryHistory
        from modelscope_mcp.models.cache import CacheEntry
        print("✓ 所有模型导入成功")
        return True
    except Exception as e:
        print(f"✗ 模型导入失败: {e}")
        return False

def test_config():
    """测试配置加载"""
    try:
        from modelscope_mcp.config.settings import Settings
        settings = Settings()
        print("✓ 配置加载成功")
        return True
    except Exception as e:
        print(f"✗ 配置加载失败: {e}")
        return False

def test_database_models():
    """测试数据库模型创建"""
    try:
        from modelscope_mcp.models.base import Base
        from sqlalchemy import create_engine
        
        # 创建内存数据库
        engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(engine)
        print("✓ 数据库模型创建成功")
        return True
    except Exception as e:
        print(f"✗ 数据库模型创建失败: {e}")
        return False

if __name__ == "__main__":
    print("开始ModelScope MCP Server基本功能测试...\n")
    
    tests = [
        ("导入测试", test_imports),
        ("配置测试", test_config),
        ("数据库模型测试", test_database_models),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"运行 {name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有基本功能测试通过!")
        sys.exit(0)
    else:
        print("❌ 部分测试失败")
        sys.exit(1)