#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope MCP Server 客户端测试脚本
测试MCP工具的调用功能和硅基流动API集成
"""

import asyncio
import json
import sys
import os
from pathlib import Path

# 添加项目路径到sys.path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPTestClient:
    """MCP测试客户端"""
    
    def __init__(self):
        self.session = None
        
    async def connect(self):
        """连接到MCP服务器"""
        try:
            # 启动MCP服务器进程
            server_params = StdioServerParameters(
                command="python",
                args=["src/modelscope_mcp/server.py"],
                env=None
            )
            
            # 创建客户端会话
            self.session = await stdio_client(server_params).__aenter__()
            
            # 初始化会话
            await self.session.initialize()
            
            print("✅ 成功连接到MCP服务器")
            return True
            
        except Exception as e:
            print(f"❌ 连接MCP服务器失败: {e}")
            return False
    
    async def list_tools(self):
        """列出可用的工具"""
        try:
            result = await self.session.list_tools()
            print("\n📋 可用的MCP工具:")
            for tool in result.tools:
                print(f"  - {tool.name}: {tool.description}")
            return result.tools
        except Exception as e:
            print(f"❌ 获取工具列表失败: {e}")
            return []
    
    async def test_list_datasets(self):
        """测试list_datasets工具"""
        print("\n🔍 测试 list_datasets 工具...")
        try:
            result = await self.session.call_tool(
                "list_datasets",
                arguments={
                    "source": "modelscope",
                    "limit": 5
                }
            )
            print(f"✅ list_datasets 调用成功")
            print(f"📊 结果: {json.dumps(result.content, indent=2, ensure_ascii=False)}")
            return True
        except Exception as e:
            print(f"❌ list_datasets 调用失败: {e}")
            return False
    
    async def test_get_dataset_info(self):
        """测试get_dataset_info工具"""
        print("\n🔍 测试 get_dataset_info 工具...")
        try:
            result = await self.session.call_tool(
                "get_dataset_info",
                arguments={
                    "dataset_id": "modelscope/chinese-text-classification",
                    "source": "modelscope"
                }
            )
            print(f"✅ get_dataset_info 调用成功")
            print(f"📊 结果: {json.dumps(result.content, indent=2, ensure_ascii=False)}")
            return True
        except Exception as e:
            print(f"❌ get_dataset_info 调用失败: {e}")
            return False
    
    async def test_query_dataset(self):
        """测试query_dataset工具（使用硅基流动API）"""
        print("\n🔍 测试 query_dataset 工具（自然语言查询）...")
        try:
            result = await self.session.call_tool(
                "query_dataset",
                arguments={
                    "query": "找一些中文文本分类的数据集",
                    "source": "modelscope",
                    "limit": 3
                }
            )
            print(f"✅ query_dataset 调用成功")
            print(f"📊 结果: {json.dumps(result.content, indent=2, ensure_ascii=False)}")
            return True
        except Exception as e:
            print(f"❌ query_dataset 调用失败: {e}")
            return False
    
    async def test_filter_samples(self):
        """测试filter_samples工具"""
        print("\n🔍 测试 filter_samples 工具...")
        try:
            result = await self.session.call_tool(
                "filter_samples",
                arguments={
                    "dataset_id": "modelscope/chinese-text-classification",
                    "source": "modelscope",
                    "filters": {
                        "label": "positive"
                    },
                    "limit": 5
                }
            )
            print(f"✅ filter_samples 调用成功")
            print(f"📊 结果: {json.dumps(result.content, indent=2, ensure_ascii=False)}")
            return True
        except Exception as e:
            print(f"❌ filter_samples 调用失败: {e}")
            return False
    
    async def test_siliconflow_integration(self):
        """测试硅基流动API集成"""
        print("\n🤖 测试硅基流动API集成...")
        try:
            # 测试复杂的自然语言查询
            queries = [
                "我需要一些用于情感分析的中文数据集",
                "找一些图像分类相关的数据集",
                "有没有对话生成的数据集"
            ]
            
            for query in queries:
                print(f"\n🔍 查询: {query}")
                result = await self.session.call_tool(
                    "query_dataset",
                    arguments={
                        "query": query,
                        "source": "modelscope",
                        "limit": 2
                    }
                )
                print(f"✅ 查询成功，找到 {len(result.content)} 个结果")
            
            return True
        except Exception as e:
            print(f"❌ 硅基流动API集成测试失败: {e}")
            return False
    
    async def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始MCP工具功能测试...")
        
        # 连接服务器
        if not await self.connect():
            return False
        
        # 列出工具
        tools = await self.list_tools()
        if not tools:
            return False
        
        # 运行各项测试
        tests = [
            ("list_datasets", self.test_list_datasets),
            ("get_dataset_info", self.test_get_dataset_info),
            ("query_dataset", self.test_query_dataset),
            ("filter_samples", self.test_filter_samples),
            ("siliconflow_integration", self.test_siliconflow_integration)
        ]
        
        results = {}
        for test_name, test_func in tests:
            try:
                results[test_name] = await test_func()
            except Exception as e:
                print(f"❌ 测试 {test_name} 时发生异常: {e}")
                results[test_name] = False
        
        # 输出测试结果摘要
        print("\n📊 测试结果摘要:")
        print("=" * 50)
        for test_name, success in results.items():
            status = "✅ 通过" if success else "❌ 失败"
            print(f"  {test_name}: {status}")
        
        success_count = sum(results.values())
        total_count = len(results)
        print(f"\n总计: {success_count}/{total_count} 个测试通过")
        
        if success_count == total_count:
            print("🎉 所有测试都通过了！MCP服务器运行正常。")
        else:
            print("⚠️  部分测试失败，请检查服务器配置和网络连接。")
        
        return success_count == total_count
    
    async def close(self):
        """关闭连接"""
        if self.session:
            await self.session.__aexit__(None, None, None)


async def main():
    """主函数"""
    client = MCPTestClient()
    try:
        success = await client.run_all_tests()
        return 0 if success else 1
    finally:
        await client.close()


if __name__ == "__main__":
    # 设置事件循环策略（Windows兼容性）
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # 运行测试
    exit_code = asyncio.run(main())
    sys.exit(exit_code)