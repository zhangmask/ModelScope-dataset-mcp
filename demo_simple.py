#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ModelScope MCP服务器功能演示脚本
展示中文数据集查询和自然语言理解能力
"""

import sys
import os
import time
from pathlib import Path

# 添加项目路径
sys.path.append('src')

try:
    from modelscope_mcp.tools.query_dataset import QueryDatasetHandler
    from modelscope_mcp.services.database import DatabaseService
    from modelscope_mcp.services.cache import CacheService
    from modelscope_mcp.core.config import Config
except ImportError as e:
    print(f"导入错误: {e}")
    print("请确保在项目根目录运行此脚本")
    sys.exit(1)

def print_separator(title=""):
    """打印分隔线"""
    if title:
        print(f"\n{'='*50}")
        print(f" {title}")
        print(f"{'='*50}")
    else:
        print("-" * 50)

def format_dataset_result(dataset, index):
    """格式化数据集结果显示"""
    name = dataset.get('name', dataset.get('id', 'N/A'))
    description = dataset.get('description', dataset.get('cardData', {}).get('description', 'N/A'))
    relevance = dataset.get('relevance_score', dataset.get('score', 0))
    dataset_id = dataset.get('id', 'N/A')
    tags = dataset.get('tags', [])
    downloads = dataset.get('downloads', 'N/A')
    likes = dataset.get('likes', 'N/A')
    created_at = dataset.get('createdAt', dataset.get('created_at', 'N/A'))
    
    print(f"\n  {index}. 📊 数据集详细信息")
    print(f"     " + "=" * 50)
    print(f"     🆔 数据集ID: {dataset_id}")
    print(f"     📝 数据集名称: {name}")
    
    # 显示描述信息（截断长描述）
    if description and description != 'N/A':
        desc_display = description[:150] + '...' if len(str(description)) > 150 else description
        print(f"     💬 描述: {desc_display}")
    
    # 显示相关性评分
    if relevance > 0:
        print(f"     🎯 相关性评分: {relevance:.3f}")
    
    # 显示统计信息
    print(f"     📥 下载次数: {downloads}")
    if likes != 'N/A':
        print(f"     👍 点赞数: {likes}")
    
    # 显示标签（限制显示数量）
    if tags:
        tags_display = ', '.join(tags[:8]) + ('...' if len(tags) > 8 else '')
        print(f"     🏷️ 标签: {tags_display}")
    
    # 显示创建时间
    if created_at and created_at != 'N/A':
        print(f"     📅 创建时间: {created_at}")
    
    print(f"     " + "=" * 50)
    print("-" * 80)

async def demo_query(handler, query, description):
    """执行演示查询"""
    print_separator()
    print(f"🔍 {description}")
    print(f"查询内容: \"{query}\"")
    print_separator()
    
    try:
        start_time = time.time()
        result = await handler.handle({"query": query, "limit": 5})
        end_time = time.time()
        
        datasets = result.get('datasets', [])
        query_time = (end_time - start_time) * 1000
        
        print(f"✅ 查询完成 (耗时: {query_time:.1f}ms)")
        print(f"📈 找到 {len(datasets)} 个相关数据集")
        print(f"🔍 查询参数: limit=5")
        print(f"📊 完整查询结果: {result}")
        print("\n" + "=" * 80)
        print("详细数据集信息:")
        print("=" * 80)
        
        if datasets:
            for i, dataset in enumerate(datasets, 1):
                format_dataset_result(dataset, i)
        else:
            print("   ❌ 暂无匹配的数据集")
            print(f"   🔍 建议尝试其他关键词或检查数据库是否包含相关数据")
            
        return True
        
    except Exception as e:
        print(f"❌ 查询失败: {e}")
        print(f"🔧 错误详情: {type(e).__name__}")
        import traceback
        print(f"📋 完整错误信息:\n{traceback.format_exc()}")
        return False

async def main():
    """主演示函数"""
    print_separator("ModelScope MCP服务器功能演示")
    print("🚀 展示中文数据集查询和AI语义理解能力")
    print("⚡ 基于硅基流动API的智能搜索")
    
    # 初始化服务
    print("\n🔧 正在初始化服务...")
    try:
        # 使用Config类加载配置
        config = Config()
        
        # 初始化数据库服务
        db_service = DatabaseService(config)
        await db_service.initialize()
        
        # 初始化缓存服务
        cache_service = CacheService(config)
        await cache_service.initialize()
        
        # 初始化查询处理器
        handler = QueryDatasetHandler(db_service, cache_service)
        print("✅ 服务初始化完成")
    except Exception as e:
        print(f"❌ 服务初始化失败: {e}")
        return
    
    # 演示查询列表
    demo_queries = [
        ("中文", "关键词搜索演示"),
        ("找一些中文对话数据", "自然语言查询演示"),
        ("机器学习训练数据集", "专业术语查询演示"),
        ("图像分类相关的数据", "多领域查询演示")
    ]
    
    success_count = 0
    total_queries = len(demo_queries)
    
    # 执行演示查询
    for query, description in demo_queries:
        if await demo_query(handler, query, description):
            success_count += 1
        time.sleep(1)  # 避免请求过快
    
    # 演示总结
    print_separator("演示总结")
    print(f"📊 查询成功率: {success_count}/{total_queries} ({success_count/total_queries*100:.1f}%)")
    print("\n🎯 ModelScope MCP服务器核心能力:")
    print("   ✓ 中文自然语言理解")
    print("   ✓ 智能语义匹配")
    print("   ✓ 实时数据库查询")
    print("   ✓ 相关性评分排序")
    print("   ✓ 高性能缓存机制")
    
    print("\n🏗️ 技术架构特点:")
    print("   • Python FastAPI + SQLite")
    print("   • 硅基流动AI语义理解")
    print("   • MCP协议标准接口")
    print("   • 模块化服务设计")
    
    print("\n🎉 演示完成！MCP服务器运行正常")
    print("="*50)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())