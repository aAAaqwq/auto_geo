#!/bin/bash
# AutoGeo 后端服务部署脚本（不含 RAGFlow）
# 版本: 1.0.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "========================================="
echo "AutoGeo 后端服务部署脚本（无 RAGFlow）"
echo "========================================="

# 检查环境变量文件
if [ ! -f .env.backend ]; then
    echo "错误: .env.backend 文件不存在"
    echo "请先复制 .env.backend.example 并修改配置:"
    echo "  cp .env.backend.example .env.backend"
    echo "  vim .env.backend"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env.backend | xargs)

# 检查必要的环境变量
if [ -z "$DB_PASSWORD" ]; then
    echo "错误: DB_PASSWORD 未设置"
    exit 1
fi

if [ -z "$AUTO_GEO_ENCRYPTION_KEY" ]; then
    echo "错误: AUTO_GEO_ENCRYPTION_KEY 未设置"
    echo "生成方法: python3 -c 'import secrets; print(secrets.token_urlsafe(32))'"
    exit 1
fi

echo ""
echo "_step 1/5: 创建必要目录..."
mkdir -p backups nginx/ssl nginx/conf.d

echo ""
echo "_step 2/5: 配置防火墙..."
# 开放 80 端口
if command -v ufw &> /dev/null; then
    sudo ufw allow 80/tcp || true
    sudo ufw allow 443/tcp || true
fi

echo ""
echo "_step 3/5: 拉取镜像..."
docker-compose -f docker-compose.backend.yml pull

echo ""
echo "_step 4/5: 启动服务..."
docker-compose -f docker-compose.backend.yml up -d

echo ""
echo "_step 5/5: 检查服务状态..."
sleep 5

# 检查服务健康状态
echo ""
echo "服务状态检查:"
docker-compose -f docker-compose.backend.yml ps

# 测试后端健康接口
echo ""
echo "测试后端服务..."
if curl -s http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ 后端服务运行正常"
else
    echo "⚠️ 后端服务可能未就绪，请查看日志:"
    echo "  docker-compose -f docker-compose.backend.yml logs backend"
fi

echo ""
echo "========================================="
echo "部署完成!"
echo "========================================="
echo ""
echo "访问地址:"
echo "  API 文档: http://your-server-ip/docs"
echo "  健康检查: http://your-server-ip/api/health"
echo ""
echo "常用命令:"
echo "  查看日志: docker-compose -f docker-compose.backend.yml logs -f"
echo "  停止服务: docker-compose -f docker-compose.backend.yml down"
echo "  重启服务: docker-compose -f docker-compose.backend.yml restart"
echo ""
