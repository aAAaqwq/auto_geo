# AutoGeo AI搜索引擎优化自动化平台

> 开发者备注：一个用 Electron + Vue3 + FastAPI + n8n + Playwright 搞的智能平台，自动发布文章、检测收录、生成GEO内容！AI能力全部通过n8n工作流调度，解耦设计，想换AI服务商只需改个配置！

## 功能特性

### 核心功能
- ✅ **多平台发布**：知乎、百家号、搜狐、头条号
- ✅ **账号管理**：安全的 Cookie 存储和授权
- ✅ **文章编辑**：富文本编辑器，支持图片上传
- ✅ **批量发布**：一键发布到多个平台
- ✅ **发布进度**：实时查看发布状态

### GEO/AI优化功能 ✨
- ✅ **关键词管理**：项目与关键词管理、关键词蒸馏
- ✅ **收录检测**：自动检测AI搜索引擎收录情况(豆包/千问/DeepSeek)
- ✅ **GEO文章生成**：基于关键词自动生成SEO优化文章
- ✅ **数据报表**：收录趋势、平台分布、关键词排名
- ✅ **预警通知**：命中率下降、零收录、持续低迷预警
- ✅ **定时任务**：每日自动检测、失败重试
- ✅ **WebSocket推送**：实时进度通知

## 技术栈

| 层级 | 技术选型 |
|------|---------|
| 前端 | Vue 3 + TypeScript + Vite + Element Plus + Pinia + ECharts |
| 后端 | FastAPI + SQLAlchemy + Playwright + APScheduler |
| AI中台 | n8n 工作流引擎 + DeepSeek API |
| 桌面 | Electron |
| 数据库 | SQLite |

## 快速开始

### 环境要求

- **Node.js**: 18+
- **Python**: 3.10+
- **Docker** (可选，用于运行 n8n)
- **操作系统**: Windows / macOS / Linux

### 1. 安装依赖

```bash
# 后端依赖
cd backend
pip install -r requirements.txt
playwright install chromium

# 前端依赖
cd ../fronted
npm install
```

### 2. 启动 n8n (AI工作流引擎)

```bash
# 方式1: Docker (推荐)
docker run -it --rm \
  --name n8n \
  -p 5678:5678 \
  -v ~/.n8n:/home/node/.n8n \
  n8nio/n8n

# 方式2: npm
npm install -g n8n
n8n start
```

然后访问 http://localhost:5678，导入 `n8n/workflows/` 下的工作流文件。

详细配置请查看 [n8n 集成文档](./n8n/README.md)

### 3. 启动后端

```bash
cd backend
python main.py
```

后端服务运行在 `http://127.0.0.1:8001`

### 4. 启动前端

```bash
cd fronted
npm run dev
```

## API 端点

### GEO/关键词 API
- `GET /api/geo/projects` - 获取项目列表
- `POST /api/geo/projects` - 创建项目
- `GET /api/geo/projects/{id}/keywords` - 获取项目关键词
- `POST /api/geo/distill` - 关键词蒸馏
- `POST /api/geo/generate-questions` - 生成问题变体

### 收录检测 API
- `POST /api/index-check/check` - 执行收录检测
- `GET /api/index-check/records` - 获取检测记录
- `GET /api/index-check/trend/{keyword_id}` - 获取关键词趋势

### 报表 API
- `GET /api/reports/overview` - 数据总览
- `GET /api/reports/trend/index` - 收录趋势
- `GET /api/reports/ranking/keywords` - 关键词排名

### 预警通知 API
- `POST /api/notifications/check` - 检查预警
- `GET /api/notifications/summary` - 预警汇总
- `GET /api/notifications/rules` - 预警规则

### 定时任务 API
- `GET /api/scheduler/jobs` - 定时任务列表
- `POST /api/scheduler/trigger-check` - 手动触发检测
- `GET /api/scheduler/status` - 服务状态

## 目录结构

```
auto_geo/
├── backend/              # 后端服务 (FastAPI)
│   ├── api/              # API 路由
│   │   ├── account.py    # 账号管理
│   │   ├── article.py    # 文章管理
│   │   ├── publish.py    # 发布管理
│   │   ├── keywords.py   # 关键词/GEO API
│   │   ├── geo.py        # GEO文章API
│   │   ├── index_check.py  # 收录检测API
│   │   ├── reports.py    # 报表API
│   │   ├── notifications.py  # 预警通知API
│   │   └── scheduler.py  # 定时任务API
│   ├── database/         # 数据库
│   │   ├── models.py     # 数据模型
│   │   └── __init__.py   # 数据库初始化
│   ├── services/         # 业务服务
│   │   ├── n8n_service.py     # n8n webhook调用封装
│   │   ├── keyword_service.py
│   │   ├── index_check_service.py
│   │   ├── geo_article_service.py
│   │   ├── notification_service.py
│   │   └── scheduler_service.py
│   ├── main.py           # 入口文件
│   └── requirements.txt  # Python 依赖
│
├── fronted/              # 前端应用 (Electron + Vue3)
│   ├── electron/         # Electron 主进程
│   ├── src/              # Vue 源码
│   │   ├── views/geo/    # GEO功能页面
│   │   │   ├── Keywords.vue
│   │   │   ├── Articles.vue
│   │   │   └── Monitor.vue
│   │   └── services/api/  # API封装
│   ├── package.json      # Node 依赖
│   └── vite.config.ts    # Vite 配置
│
├── n8n/                  # n8n AI工作流
│   ├── workflows/        # 工作流JSON文件
│   │   ├── keyword-distill.json       # 关键词蒸馏
│   │   ├── geo-article-generate.json  # GEO文章生成
│   │   ├── index-check-analysis.json  # 收录分析
│   │   └── generate-questions.json    # 问题变体生成
│   └── README.md         # n8n集成文档
│
├── docs/                 # 项目文档
│   ├── PRD-GEO-Automation.md
│   ├── architecture/
│   └── plans/
│
└── README.md             # 本文件
```

## 开发说明

### 端口配置

| 服务 | 地址 |
|------|------|
| 前端开发服务器 | http://127.0.0.1:5173 |
| 后端 API | http://127.0.0.1:8001 |
| API 文档 | http://127.0.0.1:8001/docs |
| WebSocket | ws://127.0.0.1:8001/ws |
| n8n 工作流引擎 | http://127.0.0.1:5678 |
| n8n Webhook | http://127.0.0.1:5678/webhook/* |

### 数据存储

- **数据库**: `backend/data/auto_geo.db`
- **Cookies**: `backend/data/cookies/` 目录
- **日志**: `logs/` 目录

## 常见问题

### Q: 前端启动后提示无法连接后端？

A: 需要先启动后端服务。开两个终端，分别运行：
- 终端1: `cd backend && python main.py`
- 终端2: `cd fronted && npm run dev`

### Q: n8n webhook 调用失败？

A: 检查以下几点：
1. n8n 是否正常运行：访问 http://localhost:5678
2. workflow 是否已激活：在 n8n 界面点击 "Save and activate workflow"
3. DeepSeek API 凭证是否配置正确

### Q: Windows下构建内存不足？

A: 这是大项目构建的常见问题，使用开发模式即可：`npm run dev`

### Q: 如何启动定时任务？

A: 后端启动后调用 `POST /api/scheduler/start` 即可启动定时检测

### Q: 如何更换 AI 服务商？

A: 只需在 n8n 中修改 AI 节点的凭证配置，无需修改业务代码！

## 更新日志

### v2.1.0 (2025-01-22)
- ✅ 新增 n8n AI 中台架构
- ✅ AI 能力与业务代码解耦
- ✅ 创建 4 个 n8n 工作流（关键词蒸馏、文章生成、收录分析、问题变体）
- ✅ 后端新增 n8n_service.py 封装
- ✅ 换 AI 服务商只需改 n8n 配置，不动代码

### v2.0.0 (2025-01-17)
- ✅ 完成预警通知系统
- ✅ 完成定时任务系统(集成预警检查)
- ✅ 完成数据统计报表
- ✅ 完成GEO文章生成
- ✅ 完成收录检测功能
- ✅ 前后端对接测试通过
- ✅ 所有API正常工作

### v1.0.0 (2025-01-13)
- ✅ 基础多平台发布功能
- ✅ 账号管理与授权
- ✅ 文章编辑与发布

## 许可证

MIT License

---

**维护者**: 老王
**更新日期**: 2025-01-22
**版本**: v2.1.0 (新增 n8n AI 中台)
