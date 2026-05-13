# n8n 部署指南

## 快速开始

```bash
# 一键部署
./deploy.sh
```

首次运行会自动创建 `.env` 文件，按提示修改后再次运行即可。

---

## 配置说明

编辑 `.env` 文件：

```bash
# 你的服务器IP或域名（重要！用于webhook）
N8N_HOST=123.45.67.89
WEBHOOK_URL=http://123.45.67.89:5678

# 登录账号密码
N8N_USER=admin
N8N_PASSWORD=your_secure_password

# 数据库密码（自动生成，可不改）
POSTGRES_PASSWORD=xxx
REDIS_PASSWORD=xxx
```

---

## 服务架构

```
n8n_network
├── n8n_postgres    # PostgreSQL 数据库
├── n8n_redis       # Redis 队列
└── n8n             # n8n 主服务（端口5678）
```

**注意**: n8n_network 为外部网络，AutoGeo 后端会共享此网络连接数据库。

---

## 常用命令

```bash
# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down

# 重启
docker-compose restart

# 备份数据库
docker-compose exec postgres pg_dump -U n8n n8n > backup/n8n_$(date +%Y%m%d).sql
```

---

## 获取 API Key

1. 登录 n8n 界面 `http://your-ip:5678`
2. 点击左侧 Settings（设置）
3. 选择 n8n API → 生成 API Key

---

## 注意事项

- **N8N_HOST** 必须是可访问的公网IP或域名，否则 webhook 无法被外部调用
- 数据持久化在 Docker 卷中，重启不会丢失
- 首次启动可能需要 30-60 秒

---

## 故障排查

```bash
# 检查服务状态
docker-compose ps

# 查看日志
docker-compose logs n8n

# 测试数据库连接
docker exec n8n_postgres psql -U n8n -c "\l"
```
