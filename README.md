# ModelScope MCP Server

🚀 **基于MCP协议的ModelScope数据集查询服务器**

一个高性能、易用的MCP（Model Context Protocol）服务器，专为ModelScope数据集查询和管理而设计。支持自然语言查询、智能缓存、多层架构等先进特性。

## ✨ 核心特性

- 🔍 **自然语言查询** - 支持中文自然语言查询数据集
- 🚀 **高性能缓存** - 多层缓存架构，响应速度快
- 🛡️ **安全可靠** - 完整的错误处理和日志记录
- 🔧 **易于部署** - 提供完整的批处理脚本套件
- 📊 **实时监控** - 详细的性能指标和状态监控
- 🌐 **MCP协议** - 完全兼容MCP标准协议

## 🚀 快速开始

### 方式一：一键启动（推荐）

1. **下载项目**
   ```bash
   git clone <repository-url>
   cd modelscope-mcp
   ```

2. **一键启动**
   ```cmd
   # 双击运行或在命令行执行
   quick_start.bat
   ```

   这个脚本会自动完成所有设置并启动服务器！

### 方式二：图形化管理

运行管理菜单：
```cmd
menu.bat
```

提供友好的图形化界面，包含所有管理功能。

### 方式三：手动安装

1. **安装Python依赖**
   ```cmd
   install_deps.bat
   ```

2. **配置API密钥**
   编辑 `config.json` 文件，设置您的SiliconFlow API密钥：
   ```json
   {
     "siliconflow": {
       "api_key": "YOUR_API_KEY_HERE",
       "api_url": "https://api.siliconflow.cn/v1/chat/completions"
     }
   }
   ```

3. **启动服务器**
   ```cmd
   start_server.bat
   ```

## 📋 可用脚本

| 脚本 | 功能 | 描述 |
|------|------|------|
| `quick_start.bat` | 🚀 一键启动 | 自动检查环境、安装依赖、启动服务器 |
| `menu.bat` | 📋 管理菜单 | 图形化管理界面，包含所有功能 |
| `start_server.bat` | ▶️ 启动服务器 | 启动MCP服务器 |
| `stop_server.bat` | ⏹️ 停止服务器 | 停止正在运行的服务器 |
| `install_deps.bat` | 📦 安装依赖 | 安装Python依赖包 |
| `test_all.bat` | 🧪 运行测试 | 执行所有功能测试 |

## 🔧 MCP工具

服务器提供以下MCP工具：

### 1. list_datasets
列出可用的数据集
```json
{
  "name": "list_datasets",
  "arguments": {
    "limit": 10,
    "offset": 0
  }
}
```

### 2. get_dataset_info
获取特定数据集的详细信息
```json
{
  "name": "get_dataset_info",
  "arguments": {
    "dataset_id": "dataset_name"
  }
}
```

### 3. query_dataset
使用自然语言查询数据集
```json
{
  "name": "query_dataset",
  "arguments": {
    "query": "查找图像分类相关的数据集",
    "limit": 5
  }
}
```

### 4. filter_samples
根据条件过滤数据集样本
```json
{
  "name": "filter_samples",
  "arguments": {
    "dataset_id": "dataset_name",
    "filters": {
      "category": "image"
    },
    "limit": 10
  }
}
```

## 📊 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │────│  MCP Protocol   │────│   MCP Server    │
│   (Claude等)    │    │   (JSON-RPC)    │    │ (ModelScope)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   缓存层        │    │   数据库层      │    │   API层         │
│ (Memory/Redis)  │    │   (SQLite)      │    │ (SiliconFlow)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔍 使用示例

### 在Claude中使用

1. 配置MCP服务器连接
2. 使用自然语言查询：
   ```
   "帮我找一些图像分类的数据集"
   "查找中文文本处理相关的数据集"
   "我需要语音识别的训练数据"
   ```

### 测试服务器功能

运行测试脚本验证所有功能：
```cmd
test_all.bat
```

## 📝 配置说明

### config.json 配置文件

```json
{
  "siliconflow": {
    "api_key": "YOUR_API_KEY_HERE",
    "api_url": "https://api.siliconflow.cn/v1/chat/completions"
  },
  "database": {
    "url": "sqlite:///data/modelscope_mcp.db"
  },
  "cache": {
    "type": "memory",
    "redis_url": "redis://localhost:6379/0",
    "enabled": false
  },
  "logging": {
    "level": "INFO",
    "file": "logs/modelscope_mcp.log"
  }
}
```

### 环境要求

- **Python**: 3.8+
- **操作系统**: Windows (批处理脚本)
- **内存**: 建议2GB+
- **存储**: 建议1GB+

## 🐛 故障排除

### 常见问题

1. **服务器启动失败**
   - 检查Python是否正确安装
   - 确认端口8000未被占用
   - 查看日志文件：`logs/modelscope_mcp.log`

2. **API调用失败**
   - 验证SiliconFlow API密钥是否正确
   - 检查网络连接
   - 确认API配额是否充足

3. **依赖安装问题**
   - 使用 `install_deps.bat` 重新安装
   - 检查pip是否为最新版本
   - 考虑使用虚拟环境

### 获取帮助

- 查看详细日志：`logs/modelscope_mcp.log`
- 运行诊断测试：`test_all.bat`
- 查看系统状态：使用 `menu.bat` → "查看服务器状态"

## 📖 文档

- [设计文档](DESIGN.md) - 详细的架构设计和技术实现
- [API文档](docs/api.md) - MCP工具API参考
- [开发指南](docs/development.md) - 开发和贡献指南

## 🤝 贡献

欢迎贡献代码！请查看 [DESIGN.md](DESIGN.md) 了解项目架构和开发指南。

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🌟 致谢

- [ModelScope](https://modelscope.cn/) - 数据集平台
- [SiliconFlow](https://siliconflow.cn/) - AI API服务
- [MCP Protocol](https://github.com/modelcontextprotocol) - 协议标准

---

**🎉 开始您的ModelScope数据集查询之旅！**

如有问题，请查看文档或提交Issue。