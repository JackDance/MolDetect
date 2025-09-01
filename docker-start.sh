#!/bin/bash

# MolDetect Docker 启动脚本

echo "=== MolDetect Docker 启动脚本 ==="

# 检查 Docker 是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker 未安装，请先安装 Docker"
    exit 1
fi

# 检查 docker-compose 是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "错误: docker-compose 未安装，请先安装 docker-compose"
    exit 1
fi

# 创建必要的目录
echo "创建必要的目录..."
mkdir -p assets/output
mkdir -p models

# 检查模型文件是否存在
if [ ! -f "models/best_hf.ckpt" ]; then
    echo "警告: 模型文件 models/best_hf.ckpt 不存在"
    echo "请确保模型文件已放置在 models/ 目录下"
fi

# 构建镜像
echo "构建 Docker 镜像..."
docker-compose build

# 启动服务
echo "启动 MolDetect 服务..."
docker-compose up -d

# 等待服务启动
echo "等待服务启动..."
sleep 10

# 检查服务状态
echo "检查服务状态..."
if curl -f http://localhost:13007/health &> /dev/null; then
    echo "✅ 服务启动成功！"
    echo "🌐 API 文档地址: http://localhost:13007/docs"
    echo "🔍 健康检查: http://localhost:13007/health"
    echo "📊 可视化输出目录: ./assets/output"
else
    echo "❌ 服务启动失败，请检查日志:"
    docker-compose logs
fi

echo "=== 启动完成 ==="
