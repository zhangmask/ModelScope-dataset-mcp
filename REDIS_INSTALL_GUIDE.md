# Windows Redis 安装指南

本指南提供了在Windows系统上安装Redis的多种方法。虽然MCP服务器已经配置为在没有Redis的情况下正常运行，但如果您希望启用缓存功能以提高性能，可以按照以下方法安装Redis。

## 方法一：使用WSL2（推荐）

### 1. 安装WSL2

如果您还没有安装WSL2，请按照以下步骤：

```powershell
# 以管理员身份运行PowerShell
wsl --install
```

重启计算机后，安装Ubuntu：

```powershell
wsl --install -d Ubuntu
```

### 2. 在WSL2中安装Redis

打开WSL2终端（Ubuntu），运行以下命令：

```bash
# 更新包列表
sudo apt update

# 安装Redis
sudo apt install redis-server

# 启动Redis服务
sudo service redis-server start

# 设置Redis开机自启
sudo systemctl enable redis-server
```

### 3. 配置Redis允许外部连接

编辑Redis配置文件：

```bash
sudo nano /etc/redis/redis.conf
```

找到并修改以下行：

```
# 注释掉bind 127.0.0.1行，或者改为：
bind 0.0.0.0

# 关闭保护模式（仅用于开发环境）
protected-mode no
```

重启Redis服务：

```bash
sudo service redis-server restart
```

### 4. 获取WSL2的IP地址

在WSL2中运行：

```bash
hostname -I
```

记下这个IP地址，然后在Windows中修改`.env`文件：

```env
# 将REDIS_HOST改为WSL2的IP地址
REDIS_HOST=172.x.x.x  # 替换为实际的WSL2 IP
REDIS_PORT=6379
REDIS_DB=0
```

## 方法二：使用Docker Desktop

### 1. 安装Docker Desktop

从[Docker官网](https://www.docker.com/products/docker-desktop/)下载并安装Docker Desktop for Windows。

### 2. 运行Redis容器

在PowerShell中运行：

```powershell
# 拉取Redis镜像并运行容器
docker run -d --name redis-server -p 6379:6379 redis:latest

# 验证Redis是否运行
docker ps
```

### 3. 配置环境变量

修改`.env`文件：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 4. 管理Redis容器

```powershell
# 停止Redis
docker stop redis-server

# 启动Redis
docker start redis-server

# 删除Redis容器
docker rm redis-server
```

## 方法三：使用Memurai（Windows原生Redis替代品）

### 1. 下载Memurai

访问[Memurai官网](https://www.memurai.com/)下载Windows版本。

### 2. 安装Memurai

运行下载的安装程序，按照向导完成安装。

### 3. 启动Memurai服务

安装完成后，Memurai会自动作为Windows服务启动。您也可以手动管理：

```powershell
# 启动服务
net start Memurai

# 停止服务
net stop Memurai
```

### 4. 配置环境变量

修改`.env`文件：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 方法四：使用Redis for Windows（非官方）

⚠️ **注意：这是非官方版本，不推荐用于生产环境**

### 1. 下载Redis for Windows

从[Microsoft Archive](https://github.com/microsoftarchive/redis/releases)下载预编译的Windows版本。

### 2. 解压并运行

```powershell
# 解压到某个目录，例如 C:\Redis
# 在该目录中打开PowerShell

# 启动Redis服务器
.\redis-server.exe
```

### 3. 配置环境变量

修改`.env`文件：

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## 验证Redis安装

### 1. 测试Redis连接

创建一个简单的测试脚本：

```python
# test_redis.py
import redis

try:
    # 连接Redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    
    # 测试连接
    r.ping()
    print("✓ Redis连接成功！")
    
    # 测试基本操作
    r.set('test_key', 'test_value')
    value = r.get('test_key')
    print(f"✓ Redis读写测试成功：{value.decode()}")
    
except Exception as e:
    print(f"✗ Redis连接失败：{e}")
```

运行测试：

```powershell
python test_redis.py
```

### 2. 启用MCP服务器的Redis缓存

修改`.env`文件，将Redis配置从`disabled`改为实际的连接信息：

```env
# 启用Redis缓存
REDIS_HOST=localhost  # 或WSL2的IP地址
REDIS_PORT=6379
REDIS_DB=0
# REDIS_PASSWORD=  # 如果设置了密码
# REDIS_SSL=false
```

### 3. 重启MCP服务器

```powershell
python src/modelscope_mcp/server.py
```

您应该看到类似以下的日志：

```
2025-08-12 22:00:00 - CacheService - INFO - 正在连接Redis: localhost:6379
2025-08-12 22:00:00 - CacheService - INFO - Redis连接初始化完成
```

## 性能对比

启用Redis缓存后，您将获得以下性能提升：

- **数据集查询**：重复查询速度提升10-100倍
- **样本过滤**：大型数据集过滤速度显著提升
- **API响应**：减少对ModelScope API的重复调用

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 确保Redis服务正在运行
   - 检查防火墙设置
   - 验证IP地址和端口配置

2. **WSL2 IP地址变化**
   - WSL2的IP地址可能在重启后变化
   - 可以创建脚本自动获取IP地址

3. **Docker容器无法访问**
   - 确保端口映射正确（-p 6379:6379）
   - 检查Docker Desktop是否正在运行

### 获取帮助

如果遇到问题，可以：

1. 查看MCP服务器日志
2. 使用`redis-cli`测试连接
3. 检查Windows事件查看器
4. 参考Redis官方文档

## 总结

- **推荐方案**：WSL2 + Redis（最接近生产环境）
- **简单方案**：Docker Desktop + Redis（易于管理）
- **轻量方案**：继续使用无Redis模式（已经可以正常工作）

选择适合您需求的方案即可。MCP服务器在任何情况下都能正常运行！