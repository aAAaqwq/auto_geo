# Phase 2 - n8n 部署状态报告

> 检查时间: 2026-03-01 10:45 CST | 检查人: 小ops

---

## 一、当前状态

| 项目 | 状态 |
|------|------|
| n8n 进程 | ❌ 未运行（无 Docker 容器、无 systemd 服务、无进程） |
| n8n 安装 | ❌ 未安装（不在 PATH，未全局 npm，无 Docker 镜像） |
| Docker | ✅ 可用 — Docker 29.2.1 + Compose v2.32.4 |
| n8n 工作流 | ✅ 4 个 JSON 就绪，位于 `n8n/workflows/` |
| 后端集成代码 | ✅ `n8n_client.py` + `n8n_service.py` 已就绪 |
| 配置 | ✅ `config.py` L129: `N8N_WEBHOOK_URL = http://localhost:5678/webhook` |

## 二、工作流清单 (4个)

| 文件 | Webhook 路径 | 节点数 | 功能 |
|------|-------------|--------|------|
| keyword-distill.json | /webhook/keyword-distill | 5 | 关键词蒸馏 (Webhook→Set→OpenAI→Code→Response) |
| geo-article-generate.json | /webhook/geo-article-generate | 4 | GEO文章生成 |
| index-check-analysis.json | /webhook/index-check-analysis | 4 | 收录检测分析 |
| generate-questions.json | /webhook/generate-questions | 4 | 问题变体生成 |

所有 workflow 使用 `n8n-nodes-base.openAi` 节点，需配置 OpenAI credentials。

## 三、后端集成

- **n8n_client.py**: 通用 httpx 异步客户端，URL 从 config.py 读取，超时 300s
- **n8n_service.py**: 4 个业务方法 (distill_keywords / generate_questions / generate_geo_article / analyze_index_check)，内置重试 (MAX_RETRIES=2)，Pydantic 请求校验
- **默认连接**: `http://localhost:5678/webhook`

## 四、部署方案

### 推荐: Docker 方式

系统资源: 内存 3.2G 可用 / 磁盘 34G 剩余 / 8核 CPU — Docker 已安装

```bash
docker pull n8nio/n8n:latest
mkdir -p ~/.n8n
docker run -d --name n8n --restart unless-stopped \
  -p 5678:5678 -v ~/.n8n:/home/node/.n8n \
  --memory=512m \
  -e N8N_BASIC_AUTH_ACTIVE=true \
  -e N8N_BASIC_AUTH_USER=admin \
  -e N8N_BASIC_AUTH_PASSWORD=<密码> \
  n8nio/n8n:latest
```

### 备选: npm 全局

```bash
npm install -g n8n && n8n start &
```

## 五、所需配置

| 配置项 | 值 | 位置 |
|--------|-----|------|
| N8N_WEBHOOK_URL | http://localhost:5678/webhook | .env (已默认) |
| OpenAI API Key | 需填入 | n8n Web UI → Credentials |
| 4个 Workflow | 需导入 | n8n Web UI → Import |
| 激活 Workflow | 需操作 | n8n Web UI → 每个 workflow 开 Active |

## 六、注意事项

1. **内存偏紧**: n8n (~300MB) + auto_geo后端 + Playwright 可能吃紧，建议 `--memory=512m` 限制
2. **AI Provider**: workflow 用 OpenAI 节点，需确认用哪家 key (OpenAI/DeepSeek/其他兼容)
3. **持久化**: Docker 必须挂载 `~/.n8n`，否则重启丢数据
4. **端口**: 5678 (n8n) + 8001 (后端)，均空闲可用
