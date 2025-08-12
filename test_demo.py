#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的MCP服务器测试脚本
"""

import sys
import os
from pathlib import Path

print("=== ModelScope MCP服务器测试 ===")
print(f"Python版本: {sys.version}")
print(f"当前目录: {os.getcwd()}")
print(f"项目路径: {Path.cwd()}")

# 添加项目路径
sys.path.append('src')
print(f"Python路径: {sys.path[-1]}")

print("\n正在测试模块导入...")

try:
    print("1. 导入ConfigManager...")
    from modelscope_mcp.config import ConfigManager
    print("   ✅ ConfigManager导入成功")
    
    print("2. 导入DatabaseService...")
    from modelscope_mcp.services.database import DatabaseService
    print("   ✅ DatabaseService导入成功")
    
    print("3. 导入CacheService...")
    from modelscope_mcp.services.cache import CacheService
    print("   ✅ CacheService导入成功")
    
    print("4. 导入QueryDatasetHandler...")