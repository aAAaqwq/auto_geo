# AutoGeo 后端服务

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 初始化Playwright

```bash
playwright install chromium
```

### 3. 启动服务

```bash
python main.py
```

服务将在 `http://127.0.0.1:8001` 启动

API文档: `http://127.0.0.1:8001/docs`

## API接口

### 账号管理

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/accounts` | 获取账号列表 |
| POST | `/api/accounts` | 创建账号 |
| GET | `/api/accounts/{id}` | 获取账号详情 |
| PUT | `/api/accounts/{id}` | 更新账号 |
| DELETE | `/api/accounts/{id}` | 删除账号 |
| POST | `/api/accounts/auth/start` | 开始授权 |
| GET | `/api/accounts/auth/status/{task_id}` | 查询授权状态 |
| POST | `/api/accounts/auth/confirm/{task_id}` | **手动确认授权完成** |
| POST | `/api/accounts/auth/save/{task_id}` | 保存授权结果（已废弃） |
| DELETE | `/api/accounts/auth/task/{task_id}` | 取消授权任务 |

> **授权流程说明**（v1.0 - 2026-01-09更新）：
> 1. 调用 `/api/accounts/auth/start` 打开浏览器
> 2. 浏览器自动打开两个标签页：
>    - 标签1：目标平台登录页（如知乎）
>    - 标签2：本地控制页（紫色背景，带授权按钮）
> 3. 用户在标签1中手动完成登录
> 4. 用户切换到标签2，点击"完成授权"按钮
> 5. 系统自动提取并保存关键登录cookies
> 6. 授权成功后浏览器自动关闭
>
> **核心特性**：
> - ✅ 使用 `expose_function` 绕过CORS限制
> - ✅ **全量保存cookies**（按调研文档建议，不精简）
> - ✅ 严格登录验证（只检查最核心的关键cookie）
> - ✅ AES-256加密存储cookies
> - ✅ 授权成功自动关闭浏览器
>
> **详细文档**：参见 `.claude/docs/AUTH-FEATURE.md` 和 `.claude/docs/COOKIE_RESEARCH.md`

### 文章管理

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/articles` | 获取文章列表 |
| POST | `/api/articles` | 创建文章 |
| GET | `/api/articles/{id}` | 获取文章详情 |
| PUT | `/api/articles/{id}` | 更新文章 |
| DELETE | `/api/articles/{id}` | 删除文章 |

### 其他

| 方法 | 路径 | 说明 |
|-----|------|------|
| GET | `/api/health` | 健康检查 |
| GET | `/api/platforms` | 获取支持的平台 |
| WS | `/ws` | WebSocket连接 |

## 目录结构

```
backend/
├── main.py                 # 服务入口
├── config.py               # 配置文件
├── requirements.txt        # 依赖清单
├── api/                    # API路由
│   ├── account.py          # 账号API
│   └── article.py          # 文章API
├── database/               # 数据库
│   ├── __init__.py         # 连接管理
│   └── models.py           # 数据模型
├── schemas/                # Pydantic模型
│   └── __init__.py         # 请求/响应定义
└── services/               # 业务服务
    ├── crypto.py           # 加密服务
    └── playwright_mgr.py   # 浏览器管理
```

## 开发说明

- 数据库文件: `backend/database/auto_geo.db`
- Cookie存储: `.cookies/`
- 日志文件: `logs/auto_geo.log`
