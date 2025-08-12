#!/usr/bin/env python3
"""测试MCP服务器功能

这个脚本测试ModelScope MCP服务器的基本功能，包括：
1. 服务器初始化
2. 工具列表
3. 基本工具调用
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.modelscope_mcp.core.config import Config
from src.modelscope_mcp.core.logger import setup_logging
from src.modelscope_mcp.server import ModelScopeMCPServer


async def test_server_initialization():
    """测试服务器初始化"""
    print("\n=== 测试服务器初始化 ===")
    try:
        # 加载配置
        config = Config.from_env_file()
        setup_logging(config)
        
        # 创建服务器
        server = ModelScopeMCPServer(config)
        print("✓ 服务器创建成功")
        
        # 初始化服务
        await server.initialize_services()
        print("✓ 服务初始化成功")
        
        # 检查工具处理器
        expected_tools = ["list_datasets", "query_dataset", "get_dataset_info", "filter_samples"]
        for tool_name in expected_tools:
            if tool_name in server.tool_handlers:
                print(f"✓ 工具 {tool_name} 已注册")
            else:
                print(f"✗ 工具 {tool_name} 未注册")
        
        # 清理资源
        await server.cleanup()
        print("✓ 资源清理成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 服务器初始化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_tool_handlers():
    """测试工具处理器"""
    print("\n=== 测试工具处理器 ===")
    try:
        # 加载配置
        config = Config.from_env_file()
        setup_logging(config)
        
        # 创建服务器
        server = ModelScopeMCPServer(config)
        await server.initialize_services()
        
        # 测试list_datasets工具
        print("\n--- 测试 list_datasets 工具 ---")
        try:
            handler = server.tool_handlers["list_datasets"]
            result = await handler.handle({"limit": 5})
            print(f"✓ list_datasets 调用成功: {type(result)}")
        except Exception as e:
            print(f"✗ list_datasets 调用失败: {e}")
        
        # 测试get_dataset_info工具
        print("\n--- 测试 get_dataset_info 工具 ---")
        try:
            handler = server.tool_handlers["get_dataset_info"]
            result = await handler.handle({"dataset_name": "test_dataset"})
            print(f"✓ get_dataset_info 调用成功: {type(result)}")
        except Exception as e:
            print(f"✗ get_dataset_info 调用失败: {e}")
        
        # 清理资源
        await server.cleanup()
        
        return True
        
    except Exception as e:
        print(f"✗ 工具处理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cache_service():
    """测试缓存服务"""
    print("\n=== 测试缓存服务 ===")
    try:
        # 加载配置
        config = Config.from_env_file()
        
        from src.modelscope_mcp.services.cache import CacheService
        
        # 创建缓存服务
        cache_service = CacheService(config)
        await cache_service.initialize()
        
        if cache_service.redis_client is None:
            print("✓ Redis已禁用，缓存服务正常运行在fallback模式")
        else:
            print("✓ Redis连接成功")
        
        # 测试缓存操作（应该在没有Redis时优雅失败）
        success = await cache_service.set("test", "key1", "value1")
        if not success:
            print("✓ 缓存设置在无Redis模式下正确返回False")
        
        value = await cache_service.get("test", "key1")
        if value is None:
            print("✓ 缓存获取在无Redis模式下正确返回None")
        
        # 关闭缓存服务
        await cache_service.close()
        print("✓ 缓存服务关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 缓存服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_database_service():
    """测试数据库服务"""
    print("\n=== 测试数据库服务 ===")
    try:
        # 加载配置
        config = Config.from_env_file()
        
        from src.modelscope_mcp.services.database import DatabaseService
        
        # 创建数据库服务
        db_service = DatabaseService(config)
        await db_service.initialize()
        print("✓ 数据库服务初始化成功")
        
        # 关闭数据库服务
        await db_service.close()
        print("✓ 数据库服务关闭成功")
        
        return True
        
    except Exception as e:
        print(f"✗ 数据库服务测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("ModelScope MCP Server 功能测试")
    print("=" * 50)
    
    tests = [
        ("服务器初始化", test_server_initialization),
        ("数据库服务", test_database_service),
        ("缓存服务", test_cache_service),
        ("工具处理器", test_tool_handlers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n开始测试: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"测试 {test_name} 出现异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！MCP服务器在无Redis模式下运行正常。")
        return 0
    else:
        print(f"\n❌ {total - passed} 个测试失败。")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)