# AutoGeo 简化部署指南（不含 RAGFlow）

## 快速部署步骤

### 1. 服务器准备

```bash
# 安装 Docker

curl -fsSL https://get.docker.com | sh
sudo systemctl enable docker
sudo systemctl start docker

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 创建项目目录
sudo mkdir -p /opt/autogeo
cd /opt/autogeo

# 克隆项目
sudo git clone https://github.com/Architecture-Matrix/Auto_GEO.git .
```

### 2. 配置后端

```bash
cd /opt/autogeo/deploy

# 复制环境变量模板
sudo cp .env.simple.example .env.backend
sudo vim .env.backend
```

**必须修改的配置项：**

```bash
# 数据库密码
DB_PASSWORD=your-secure-password

# 加密密钥（生成命令见下文）
AUTO_GEO_ENCRYPTION_KEY=your-32-byte-key

# 你的服务器IP或域名
CORS_ORIGINS=http://your-server-ip:5173,http://localhost:5173

# DeepSeek API Key（用于AI生成）
DEEPSEEK_API_KEY=sk-your-deepseek-key
```

**生成加密密钥：**
```bash
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. 部署后端

```bash
cd /opt/autogeo/deploy
sudo chmod +x deploy-simple.sh
sudo ./deploy-simple.sh
```

部署成功后会显示：
- API 文档地址: `http://your-server-ip/docs`
- 健康检查: `http://your-server-ip/api/health`

### 4. 配置前端

在**本地开发机**上：

```bash
cd /path/to/Auto_GEO/frontend

# 复制生产环境配置
cp .env.production.example .env.production
vim .env.production
```

修改为：
```bash
VITE_API_BASE_URL=http://your-server-ip/api
VITE_WS_URL=ws://your-server-ip/ws
VITE_STATIC_URL=http://your-server-ip/static
VITE_ENABLE_MOCK=false
```

### 5. 构建前端

```bash
# 安装依赖
npm install

# 构建生产版本
npm run build
```

构建完成后，`dist/` 目录包含前端静态文件。

### 6. 部署前端到服务器

**方式一：直接复制到服务器**

```bash
# 在本地执行
scp -r dist/* root@your-server-ip:/opt/autogeo/nginx/html/
```

**方式二：使用 Nginx 反向代理到本地开发服务器**

如果前端需要热更新，可以在本地运行：
```bash
npm run dev -- --host
```

然后在服务器 Nginx 配置中添加代理（参考下文）。

### 7. 完整部署架构

```
┌─────────────────────────────────────────────────────────────┐
│                       你的服务器                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐  │
│   │                     Nginx (80端口)                   │  │
│   │  ┌─────────────────┐    ┌─────────────────────────┐ │  │
│   │  │  /api/*         │    │  /* (静态文件)          │ │  │
│   │  │  ▼              │    │  ▼                      │ │  │
│   │  │  Backend:8001   │    │  /opt/autogeo/nginx/html│ │  │
│   │  └─────────────────┘    └─────────────────────────┘ │  │
│   └─────────────────────────────────────────────────────┘  │
│          │                                    │             │
│          ▼                                    ▼             │
│   ┌─────────────┐                    ┌─────────────┐       │
│   │  Backend    │                    │  静态文件    │       │
│   │  (FastAPI)  │                    │  (前端构建)  │       │
│   │  Port:8001  │                    │             │       │
│   └──────┬──────┘                    └─────────────┘       │
│          │                                                   │
│          ▼                                                   │
│   ┌─────────────┐                                           │
│   │ PostgreSQL  │                                           │
│   │ Port:5432   │                                           │
│   └─────────────┘                                           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## 常用命令

```bash
# 查看运行状态
cd /opt/autogeo/deploy
docker-compose -f docker-compose.backend.yml ps

# 查看日志
docker-compose -f docker-compose.backend.yml logs -f

# 查看后端日志
docker-compose -f docker-compose.backend.yml logs -f backend

# 重启服务
docker-compose -f docker-compose.backend.yml restart

# 停止服务
docker-compose -f docker-compose.backend.yml down

# 进入后端容器
docker-compose -f docker-compose.backend.yml exec backend bash

# 数据库备份
docker-compose -f docker-compose.backend.yml exec postgres pg_dump -U autogeo autogeo > backup.sql

# 数据库恢复
docker-compose -f docker-compose.backend.yml exec -T postgres psql -U autogeo autogeo < backup.sql
```

## 故障排查

### 1. 端口冲突

```bash
# 检查 80 端口是否被占用
sudo netstat -tlnp | grep :80

# 如果被占用，修改 docker-compose.backend.yml 中的端口映射
# 例如改为 "8080:80"
```

### 2. 后端无法启动

```bash
# 查看后端日志
cd /opt/autogeo/deploy
docker-compose -f docker-compose.backend.yml logs backend

# 常见错误：
# - 环境变量缺失：检查 .env.backend
# - 数据库连接失败：检查 postgres 是否健康
```

### 3. 前端无法连接后端

```bash
# 检查后端健康状态
curl http://your-server-ip/api/health

# 检查 CORS 配置
# 确保 .env.backend 中的 CORS_ORIGINS 包含前端地址
```

### 4. 数据库连接问题

```bash
# 检查 postgres 状态
docker-compose -f docker-compose.backend.yml ps postgres

# 进入数据库
docker-compose -f docker-compose.backend.yml exec postgres psql -U autogeo -d autogeo
```

## 配置文件参考

### Nginx 配置

如需自定义 Nginx 配置，修改 `deploy/nginx/conf.d/default.conf`：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api/ {
        proxy_pass http://backend:8001/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    # WebSocket 代理
    location /ws {
        proxy_pass http://backend:8001/ws;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### SSL/HTTPS 配置（可选）

使用 Certbot 自动配置 HTTPS：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo systemctl enable certbot.timer
```

## 更新部署

```bash
cd /opt/autogeo

# 拉取最新代码
git pull origin main

# 重新部署
cd deploy
sudo ./deploy-simple.sh
```

## 无 RAGFlow 的功能说明

不部署 RAGFlow 时，以下功能**不可用**：

- ❌ 知识库管理（需要 RAGFlow 向量检索）
- ❌ 基于知识库的文章生成（可以改用普通文章生成）

**仍可正常使用的功能**：

- ✅ 客户管理
- ✅ 项目管理
- ✅ 关键词蒸馏
- ✅ GEO文章生成（基于提示词模板）
- ✅ 文章管理
- ✅ 账号管理
- ✅ 批量发布
- ✅ 收录监控
- ✅ 定时任务
- ✅ 数据报表

---

**遇到问题？** 检查日志：`docker-compose -f docker-compose.backend.yml logs -f`
