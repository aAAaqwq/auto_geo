# AutoGeo 部署指南

## 新架构概览（简化版）

```
┌─────────────────────────────────────────────────────────┐
│                    新部署架构（5容器）                    │
├─────────────────┬─────────────────┬─────────────────────┤
│   n8n 服务      │   后端服务      │     前端（桌面）     │
│   (3容器)       │   (2容器)       │                     │
├─────────────────┼─────────────────┼─────────────────────┤
│  PostgreSQL ←───┼─── _backend     │    Electron + Vue3  │
│  Redis      ←───┼───  (共享)      │                     │
│  n8n            │   Nginx         │                     │
└─────────────────┴─────────────────┴─────────────────────┘
```

### 核心变更
- **后端不再自带数据库**，复用 n8n 的 PostgreSQL
- **总容器数从 7 → 5**，节省资源

---

## 快速开始

### 第一步：部署 n8n（必需）

```bash
cd n8n/deploy

# 第一次运行会自动创建 .env 文件
./deploy.sh

# 按提示编辑配置
nano .env

# 再次运行部署
./deploy.sh
```

访问：`http://your-server-ip:5678`

---

### 第二步：部署后端

```bash
cd deploy

# 1. 复制环境变量模板
cp .env.backend.example .env.backend
nano .env.backend
```

**关键配置（只需改4项）：**

```bash
# n8n数据库密码（与 n8n/.env 中的一致）
N8N_DB_PASSWORD=xxx

# 加密密钥（生成: openssl rand -base64 32）
AUTO_GEO_ENCRYPTION_KEY=xxx

# n8n地址和API Key
N8N_WEBHOOK_URL=http://ip:5678/webhook
N8N_API_KEY=xxx

# DeepSeek API
DEEPSEEK_API_KEY=sk-xxx
```

```bash
# 2. 执行部署
./deploy.sh
```

访问：`http://your-server-ip/api`

---

## 文件结构

```
deploy/
├── docker-compose.backend.yml    # 后端编排（2服务）
├── deploy.sh                     # 一键部署脚本
├── .env.backend.example          # 环境变量模板
└── README.md                     # 本文档

n8n/deploy/
├── docker-compose.yml            # n8n编排（3服务）
├── deploy.sh                     # 一键部署脚本
├── .env                          # 自动生成
└── backup/                       # 数据备份
```

---

## 常用命令

| 操作 | 命令 |
|------|------|
| 后端日志 | `cd deploy && docker-compose logs -f` |
| n8n日志 | `cd n8n/deploy && docker-compose logs -f` |
| 停止后端 | `cd deploy && docker-compose down` |
| 停止n8n | `cd n8n/deploy && docker-compose down` |

---

## 注意事项

1. **必须先部署 n8n**，后端依赖 n8n 的数据库
2. 后端会自动在 n8n_postgres 中创建 `autogeo` 数据库
3. 确保防火墙开放 5678（n8n）和 80（后端）端口

---

## 故障排查

### 后端无法连接数据库
```bash
# 检查 n8n_postgres 是否运行
docker ps | grep n8n_postgres

# 检查密码是否正确
docker exec n8n_postgres psql -U n8n -c "\l"
```

### 端口冲突
```bash
# 查看端口占用
netstat -tlnp | grep -E '80|5678'
```

---

## 可选：部署 RAGFlow

如需 RAG 功能，单独部署（不依赖 n8n）：

```bash
cd deploy
cp .env.ragflow.example .env.ragflow
# 配置后执行
docker-compose -f docker-compose.ragflow.yml up -d
```

详见 [RAGFLOW-DEPLOY.md](./RAGFLOW-DEPLOY.md)
