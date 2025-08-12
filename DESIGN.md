# ModelScope MCP 服务器设计文档

## 📋 项目概述

**ModelScope MCP Server** 是一个基于 Model Context Protocol (MCP) 的智能数据集查询服务器，专为 ModelScope 平台设计。它提供了自然语言查询、智能推荐和实时数据访问等功能，让用户能够通过简单的自然语言描述快速找到所需的数据集。

### 🎯 核心价值

- **智能查询**：支持中文自然语言查询，理解用户意图
- **实时数据**：直接连接 ModelScope API，获取最新数据集信息
- **高性能**：多层缓存机制，确保快速响应
- **易集成**：标准 MCP 协议，可与各种 AI 工具集成

## 🏗️ 系统架构

### 整体架构图

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │  MCP Protocol   │    │   MCP Server    │
│  (AI Tools)     │◄──►│   (JSON-RPC)    │◄──►│ (ModelScope)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ModelScope MCP Server                        │
├─────────────────┬─────────────────┬─────────────────────────────┤
│   MCP Tools     │   Core Services │      External APIs          │
│                 │                 │                             │
│ • list_datasets │ • Database      │ • ModelScope API            │
│ • query_dataset │ • Cache         │ • SiliconFlow API           │
│ • get_info      │ • NLP Parser    │ • HuggingFace API           │
│ • filter_samples│ • Config        │                             │
└─────────────────┴─────────────────┴─────────────────────────────┘
                                │
                                ▼
                    ┌─────────────────────┐
                    │   Data Storage      │
                    │                     │
                    │ • SQLite Database   │
                    │ • Redis Cache       │
                    │ • File Cache        │
                    └─────────────────────┘
```

### 核心组件

#### 1. MCP 工具层 (Tools Layer)

负责实现具体的 MCP 工具功能：

- **list_datasets**: 列出可用数据集
- **get_dataset_info**: 获取数据集详细信息
- **query_dataset**: 自然语言查询数据集
- **filter_samples**: 过滤和获取数据样本

#### 2. 服务层 (Services Layer)

提供核心业务逻辑：

- **DatabaseService**: 数据库操作和管理
- **CacheService**: 缓存管理和优化
- **NLPService**: 自然语言处理和查询解析
- **ConfigService**: 配置管理

#### 3. 集成层 (Integration Layer)

连接外部服务：

- **ModelScope API**: 获取数据集信息
- **SiliconFlow API**: 自然语言理解
- **HuggingFace API**: 备用数据源

## 🧠 核心技术实现

### 1. 自然语言查询处理

#### 查询解析流程

```python
# 查询处理管道
user_query → intent_classification → entity_extraction → query_generation → result_filtering
```

**技术栈：**
- **SiliconFlow API**: 提供强大的中文理解能力
- **意图分类**: 识别查询类型（搜索、过滤、信息获取等）
- **实体提取**: 提取关键词、分类、标签等
- **查询生成**: 将自然语言转换为结构化查询

#### 示例处理过程

```
输入: "找一些中文文本分类的数据集"
     ↓
意图: search_datasets
实体: {"language": "中文", "task": "文本分类"}
     ↓
查询: {"keywords": ["中文", "文本分类"], "category": "nlp"}
     ↓
结果: 匹配的数据集列表
```

### 2. 多层缓存架构

#### 缓存策略

```
L1: 内存缓存 (最快访问)
     ↓ (miss)
L2: Redis缓存 (中等速度)
     ↓ (miss)
L3: 数据库缓存 (持久化)
     ↓ (miss)
L4: 外部API (最慢，实时数据)
```

**缓存配置：**
- **内存缓存**: 1000个条目，LRU淘汰
- **Redis缓存**: 5分钟TTL，压缩存储
- **数据库缓存**: 永久存储，定期更新
- **API缓存**: 2小时TTL，避免频繁请求

### 3. 数据库设计

#### 核心表结构

```sql
-- 数据集表
CREATE TABLE datasets (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) UNIQUE,
    display_name VARCHAR(255),
    description TEXT,
    source VARCHAR(50),
    category VARCHAR(100),
    tags JSON,
    total_samples INTEGER,
    size_bytes BIGINT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 查询历史表
CREATE TABLE query_history (
    id INTEGER PRIMARY KEY,
    query_text TEXT,
    query_type VARCHAR(50),
    parsed_query JSON,
    status VARCHAR(50),
    execution_time FLOAT,
    result_count INTEGER,
    created_at TIMESTAMP
);

-- 缓存表
CREATE TABLE cache_entries (
    id INTEGER PRIMARY KEY,
    cache_key VARCHAR(255) UNIQUE,
    cache_value JSON,
    expires_at TIMESTAMP,
    created_at TIMESTAMP
);
```

### 4. 配置管理

#### 配置文件结构

```json
{
  "siliconflow": {
    "enabled": true,
    "api_key": "sk-xxx",
    "api_url": "https://api.siliconflow.cn",
    "model": "gpt-3.5-turbo"
  },
  "database": {
    "url": "sqlite:///./data/modelscope_mcp.db"
  },
  "cache": {
    "enabled": true,
    "default_ttl": 3600
  }
}
```

## 🔧 MCP 协议实现

### 工具定义

每个 MCP 工具都遵循标准的 JSON Schema 定义：

```python
# 查询数据集工具定义
{
    "name": "query_dataset",
    "description": "使用自然语言查询ModelScope数据集",
    "inputSchema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "自然语言查询描述"
            },
            "limit": {
                "type": "integer",
                "description": "返回结果数量限制",
                "default": 10
            }
        },
        "required": ["query"]
    }
}
```

### 消息处理流程

```
MCP Client Request
       ↓
JSON-RPC Parser
       ↓
Tool Router
       ↓
Handler Execution
       ↓
Response Formatter
       ↓
MCP Client Response
```

## 🚀 性能优化

### 1. 异步处理

- **异步I/O**: 所有数据库和API调用都使用异步操作
- **并发限制**: 控制并发请求数量，避免资源耗尽
- **连接池**: 数据库连接池管理，提高连接复用率

### 2. 查询优化

- **索引优化**: 在常用查询字段上建立索引
- **查询缓存**: 缓存常见查询结果
- **分页查询**: 大结果集分页返回，减少内存占用

### 3. 内存管理

- **对象池**: 复用常用对象，减少GC压力
- **内存监控**: 监控内存使用，及时清理缓存
- **流式处理**: 大数据集流式处理，避免内存溢出

## 🔒 安全设计

### 1. API 安全

- **API密钥管理**: 安全存储和轮换API密钥
- **请求限流**: 防止API滥用和DDoS攻击
- **输入验证**: 严格验证所有输入参数

### 2. 数据安全

- **SQL注入防护**: 使用参数化查询
- **数据加密**: 敏感数据加密存储
- **访问控制**: 基于角色的访问控制

### 3. 错误处理

- **异常捕获**: 全面的异常处理机制
- **错误日志**: 详细的错误日志记录
- **优雅降级**: 服务异常时的降级策略

## 📊 监控和日志

### 1. 性能监控

- **响应时间**: 监控API响应时间
- **吞吐量**: 监控请求处理能力
- **错误率**: 监控错误发生频率
- **资源使用**: 监控CPU、内存、磁盘使用

### 2. 业务监控

- **查询统计**: 统计查询类型和频率
- **缓存命中率**: 监控缓存效果
- **用户行为**: 分析用户查询模式

### 3. 日志管理

```python
# 结构化日志格式
{
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "logger": "QueryDatasetHandler",
    "message": "查询数据集成功",
    "query": "找一些中文文本分类的数据集",
    "result_count": 5,
    "execution_time": 0.234
}
```

## 🔄 扩展性设计

### 1. 插件架构

- **数据源插件**: 支持添加新的数据源
- **NLP插件**: 支持不同的NLP服务提供商
- **缓存插件**: 支持不同的缓存后端

### 2. 微服务化

- **服务拆分**: 可按功能拆分为独立服务
- **API网关**: 统一入口和路由管理
- **服务发现**: 自动服务注册和发现

### 3. 水平扩展

- **负载均衡**: 支持多实例部署
- **数据分片**: 大数据集分片存储
- **读写分离**: 数据库读写分离

## 🧪 测试策略

### 1. 单元测试

- **工具测试**: 每个MCP工具的功能测试
- **服务测试**: 核心服务的逻辑测试
- **集成测试**: 组件间集成测试

### 2. 性能测试

- **压力测试**: 高并发场景测试
- **负载测试**: 持续负载能力测试
- **稳定性测试**: 长时间运行稳定性

### 3. 端到端测试

- **MCP协议测试**: 完整的MCP交互测试
- **用户场景测试**: 真实用户使用场景
- **异常场景测试**: 各种异常情况处理

## 📈 未来规划

### 短期目标 (1-3个月)

- [ ] 支持更多数据源 (HuggingFace, Kaggle)
- [ ] 优化查询性能和准确性
- [ ] 添加更多查询类型支持
- [ ] 完善监控和告警系统

### 中期目标 (3-6个月)

- [ ] 实现分布式部署
- [ ] 添加用户认证和权限管理
- [ ] 支持自定义查询模板
- [ ] 实现智能推荐功能

### 长期目标 (6-12个月)

- [ ] 支持多模态数据集查询
- [ ] 实现联邦学习数据发现
- [ ] 添加数据质量评估
- [ ] 构建数据集生态系统

## 🚀 快速开始

### 使用批处理脚本（推荐）

我们提供了完整的批处理脚本套件，让您可以轻松管理MCP服务器：

#### 🚀 一键启动
```cmd
# 双击运行或在命令行执行
quick_start.bat
```
这个脚本会自动：
- 检查Python环境
- 安装缺失的依赖
- 创建默认配置文件
- 启动MCP服务器

#### 📋 图形化管理菜单
```cmd
menu.bat
```
提供友好的图形化界面，包含：
- 启动/停止服务器
- 安装依赖包
- 运行测试
- 查看状态和日志
- 编辑配置文件
- 开发者工具

#### 🔧 独立脚本
```cmd
start_server.bat    # 启动服务器
stop_server.bat     # 停止服务器
install_deps.bat    # 安装依赖
test_all.bat        # 运行所有测试
```

### 手动安装（开发者）

如果您需要进行开发或自定义配置：

1. **克隆项目**
```bash
git clone <repository-url>
cd modelscope-mcp
```

2. **安装依赖**
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

3. **配置环境**
```bash
cp config.example.json config.json
# 编辑 config.json 配置API密钥
```

4. **运行测试**
```bash
python -m pytest tests/
```

5. **启动服务器**
```bash
python src/modelscope_mcp/server.py
```

## 🤝 贡献指南

### 开发环境设置

推荐使用我们提供的批处理脚本进行开发环境设置，或按照上述手动安装步骤进行配置。

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写完整的文档字符串
- 添加适当的单元测试

### 提交流程

1. Fork 项目
2. 创建功能分支
3. 提交代码变更
4. 创建 Pull Request
5. 代码审查和合并

---

**ModelScope MCP Server** - 让数据集查询变得智能而简单！ 🚀