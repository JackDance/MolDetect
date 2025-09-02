# MolDetect Docker 部署指南

## 概述

本项目提供了完整的 Docker 部署方案，使用国内镜像源加速构建过程。

## 文件说明

- `Dockerfile`: Docker 镜像构建文件
- `docker-compose.yml`: Docker Compose 配置文件
- `docker-start.sh`: 一键启动脚本
- `.dockerignore`: Docker 构建忽略文件

## 快速开始

### 方法一：使用启动脚本（推荐）

```bash
# 运行启动脚本
./docker-start.sh
```

### 方法二：手动构建和启动

```bash
# 1. 构建镜像
docker-compose build

# 2. 启动服务
docker-compose up -d

# 3. 查看日志
docker-compose logs -f
```

### 方法三：使用 Docker 命令

```bash
# 1. 构建镜像
docker build -t moldetect-api .

# 2. 运行容器
docker run -d \
  --name moldetect-api \
  -p 13111:13111 \
  -v $(pwd)/assets/output:/app/assets/output \
  moldetect-api
```

## 服务访问

启动成功后，可以通过以下地址访问服务：

- **API 文档**: http://localhost:13111/docs
- **健康检查**: http://localhost:13111/health
- **检测接口**: http://localhost:13111/detect
- **可视化接口**: http://localhost:13111/visualize

## 目录结构

```
MolDetect/
├── Dockerfile              # Docker 构建文件
├── docker-compose.yml      # Docker Compose 配置
├── docker-start.sh         # 启动脚本
├── .dockerignore           # Docker 忽略文件
├── requirements.txt        # Python 依赖
├── app.py                  # 主应用文件
├── models/                 # 模型文件目录
│   └── best_hf.ckpt       # 模型文件
└── assets/                 # 资源文件目录
    └── output/            # 可视化输出目录
```

## 配置说明

### 启动方式

使用 `uvicorn` 作为 ASGI 服务器启动 FastAPI 应用：
- 支持异步处理，性能更好
- 自动重载功能（开发环境）
- 更好的并发处理能力

### 端口配置

- 容器内端口: 13111
- 宿主机端口: 13111
- 可在 `docker-compose.yml` 中修改端口映射

### 镜像源配置

- **APT 源**: 阿里云镜像源
- **PIP 源**: 清华大学镜像源

### 环境变量

- `PYTHONUNBUFFERED=1`: 确保 Python 输出不被缓冲
- `PYTHONDONTWRITEBYTECODE=1`: 不生成 .pyc 文件

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec moldetect bash

# 查看容器资源使用情况
docker stats moldetect-api
```

## 故障排除

### 1. 模型文件不存在

确保 `models/best_hf.ckpt` 文件存在：

```bash
ls -la models/
```

### 2. 端口被占用

如果端口 13111 被占用，可以修改 `docker-compose.yml` 中的端口映射：

```yaml
ports:
  - "13008:13111"  # 将宿主机端口改为 13008
```

### 3. 构建失败

如果构建失败，可以尝试清理 Docker 缓存：

```bash
docker system prune -a
docker-compose build --no-cache
```

### 4. 内存不足

如果遇到内存不足的问题，可以增加 Docker 的内存限制或使用更小的基础镜像。

## GPU 支持

如果需要 GPU 支持，请：

1. 安装 NVIDIA Docker 运行时
2. 取消 `docker-compose.yml` 中 GPU 相关配置的注释
3. 重新构建和启动服务

## 生产环境部署

在生产环境中，建议：

1. 使用具体的镜像标签而不是 `latest`
2. 配置适当的资源限制
3. 设置日志轮转
4. 配置健康检查和监控
5. 使用 HTTPS 和反向代理

## 更新服务

```bash
# 停止服务
docker-compose down

# 重新构建镜像
docker-compose build --no-cache

# 启动服务
docker-compose up -d
```
