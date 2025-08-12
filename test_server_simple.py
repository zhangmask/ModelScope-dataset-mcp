#!/usr/bin/env python3
"""简化的服务器功能测试"""

import sys
import os
import asyncio
from unittest.mock import Mock, AsyncMock

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

async def test_mcp_tools():
    """测试MCP工具基本功能"""
    try:
        from modelscope_mcp.tools.list_datasets import ListDatasetsHandler
        from modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
        from modelscope_mcp.tools.filter_samples import FilterSamplesHandler
        
        # 创建模拟的服务
        mock_db_service = Mock()
        mock_cache_service = Mock()
        
        # 测试ListDatasetsHandler (只需要2个参数)
        list_handler = ListDatasetsHandler(mock_db_service, mock_cache_service)
        print("✓ ListDatasetsHandler 创建成功")
        
        # 测试GetDatasetInfoHandler
        info_handler = GetDatasetInfoHandler(mock_db_service, mock_cache_service)
        print("✓ GetDatasetInfoHandler 创建成功")
        
        # 测试FilterSamplesHandler
        filter_handler = FilterSamplesHandler(mock_db_service, mock_cache_service)
        print("✓ FilterSamplesHandler 创建成功")
        
        return True
    except Exception as e:
        print(f"✗ MCP工具测试失败: {e}")
        return False

async def test_database_service():
    """测试数据库服务"""
    try:
        from modelscope_mcp.services.database import DatabaseService
        from modelscope_mcp.core.config import Config
        import os
        
        # 设置内存数据库
        os.environ["DATABASE_URL"] = "sqlite:///:memory:"
        config = Config()
        
        db_service = DatabaseService(config)
        await db_service.initialize()
        print("✓ 数据库服务初始化成功")
        
        await db_service.close()
        print("✓ 数据库服务关闭成功")
        
        return True
    except Exception as e:
        print(f"✗ 数据库服务测试失败: {e}")
        return False

async def test_cache_service():
    """测试缓存服务"""
    try:
        from modelscope_mcp.services.cache import CacheService
        from modelscope_mcp.core.config import Config
        import os
        
        # 禁用Redis，使用内存缓存
        os.environ["CACHE_ENABLED"] = "false"
        config = Config()
        
        cache_service = CacheService(config)
        print("✓ 缓存服务创建成功")
        
        return True
    except Exception as e:
        print(f"✗ 缓存服务测试失败: {e}")
        return False

async def main():
    """主测试函数"""
    print("开始ModelScope MCP Server服务器功能测试...\n")
    
    tests = [
        ("MCP工具测试", test_mcp_tools),
        ("数据库服务测试", test_database_service),
        ("缓存服务测试", test_cache_service),
    ]
    
    passed = 0
    total = len(tests)
    
    for name, test_func in tests:
        print(f"运行 {name}...")
        if await test_func():
            passed += 1
        print()
    
    print(f"测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有服务器功能测试通过!")
        return 0
    else:
        print("❌ 部分测试失败")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)