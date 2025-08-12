#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的MCP服务器测试脚本
直接测试服务器组件而不是通过MCP协议
"""

import asyncio
import sys
import os
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

try:
    from modelscope_mcp.tools.list_datasets import ListDatasetsHandler
    from modelscope_mcp.tools.get_dataset_info import GetDatasetInfoHandler
    from modelscope_mcp.tools.query_dataset import QueryDatasetHandler
    from modelscope_mcp.tools.filter_samples import FilterSamplesHandler
    from modelscope_mcp.core.config import Config
    from modelscope_mcp.services.database import DatabaseService
    from modelscope_mcp.services.cache import CacheService
except ImportError as e:
    print(f"❌ 导入模块失败: {e}")
    print("请确保所有依赖都已安装")
    sys.exit(1)


class SimpleTestRunner:
    """简单测试运行器"""
    
    def __init__(self):
        self.config = None
        self.db_service = None
        self.cache_service = None
        self.handlers = {}
    
    async def setup(self):
        """初始化测试环境"""
        try:
            print("🔧 初始化测试环境...")
            
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
                'query_dataset': QueryDatasetHandler(self.db_service, self.cache_service),
                'filter_samples': FilterSamplesHandler(self.db_service, self.cache_service)
            }
            print("✅ 处理器初始化成功")
            
            return True
            
        except Exception as e:
            print(f"❌ 初始化失败: {e}")
            return False
    
    async def test_list_datasets(self):
        """测试列出数据集"""
        print("\n🔍 测试 list_datasets...")
        try:
            handler = self.handlers['list_datasets']
            result = await handler.handle({
                'source': 'modelscope',
                'limit': 5
            })
            print(f"✅ list_datasets 成功")
            print(f"📊 返回 {len(result.get('datasets', []))} 个数据集")
            return True
        except Exception as e:
            print(f"❌ list_datasets 失败: {e}")
            return False
    
    async def test_get_dataset_info(self):
        """测试获取数据集信息"""
        print("\n🔍 测试 get_dataset_info...")
        try:
            handler = self.handlers['get_dataset_info']
            result = await handler.handle({
                'dataset_id': 'modelscope/chinese-alpaca-2-7b',
                'source': 'modelscope'
            })
            print(f"✅ get_dataset_info 成功")
            print(f"📊 数据集名称: {result.get('name', 'N/A')}")
            return True
        except Exception as e:
            print(f"❌ get_dataset_info 失败: {e}")
            return False
    
    async def test_query_dataset(self):
        """测试查询数据集（使用硅基流动API）"""
        print("\n🔍 测试 query_dataset（自然语言查询）...")
        try:
            handler = self.handlers['query_dataset']
            result = await handler.handle({
                'query': '找一些中文文本分类的数据集',
                'source': 'modelscope',
                'limit': 3
            })
            print(f"✅ query_dataset 成功")
            print(f"📊 找到 {len(result.get('datasets', []))} 个相关数据集")
            return True
        except Exception as e:
            print(f"❌ query_dataset 失败: {e}")
            return False
    
    async def test_filter_samples(self):
        """测试过滤样本"""
        print("\n🔍 测试 filter_samples...")
        try:
            handler = self.handlers['filter_samples']
            result = await handler.handle({
                'dataset_id': 'modelscope/chinese-alpaca-2-7b',
                'source': 'modelscope',
                'filters': {},
                'limit': 5
            })
            print(f"✅ filter_samples 成功")
            print(f"📊 返回 {len(result.get('samples', []))} 个样本")
            return True
        except Exception as e:
            print(f"❌ filter_samples 失败: {e}")
            return False
    
    async def test_siliconflow_config(self):
        """测试硅基流动配置"""
        print("\n🔍 测试硅基流动API配置...")
        try:
            # 检查配置文件中的硅基流动配置
            config_file = Path("config.json")
            if config_file.exists():
                import json
                with open(config_file, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                    siliconflow_config = config_data.get('siliconflow', {})
                    if siliconflow_config.get('enabled'):
                        api_key = siliconflow_config.get('api_key')
                        api_url = siliconflow_config.get('api_url')
                        print(f"✅ 硅基流动API已启用")
                        print(f"📊 API URL: {api_url}")
                        print(f"📊 API Key: {api_key[:10]}...{api_key[-10:] if api_key else 'None'}")
                        return True
                    else:
                        print("❌ 硅基流动API未启用")
                        return False
            else:
                print("❌ 配置文件不存在")
                return False
        except Exception as e:
            print(f"❌ 硅基流动配置检查失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始MCP服务器功能测试...")
        
        # 初始化
        if not await self.setup():
            return False
        
        # 运行测试
        tests = [
            ('硅基流动配置', self.test_siliconflow_config),
            ('list_datasets', self.test_list_datasets),
            ('get_dataset_info', self.test_get_dataset_info),
            ('query_dataset', self.test_query_dataset),
            ('filter_samples', self.test_filter_samples)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = await test_func()
            except Exception as e:
                print(f"❌ 测试 {test_name} 时发生异常: {e}")
                results[test_name] = False
        
        # 输出结果
        print("\n📊 测试结果摘要:")
        print("=" * 50)
        for test_name, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        success_count = sum(results.values())
        total_count = len(results)
        print(f"\n总计: {success_count}/{total_count} 个测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！")
        else:
            print("⚠️  部分测试失败，请检查配置和网络连接。")
        
        return success_count == total_count
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self.cache_service:
                await self.cache_service.close()
            if self.db_service:
                await self.db_service.close()
            print("✅ 资源清理完成")
        except Exception as e:
            print(f"⚠️  资源清理时出现错误: {e}")


async def main():
    """主函数"""
    runner = SimpleTestRunner()
    try:
        success = await runner.run_all_tests()
        return 0 if success else 1
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    # Windows兼容性
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 测试运行失败: {e}")
        sys.exit(1)