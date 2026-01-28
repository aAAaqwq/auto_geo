---
name: "auto-geo-dev-style"
description: "协助开发者遵循 auto_geo 项目的开发规范和风格。包括后端 FastAPI/SQLAlchemy 异步模式、前端 Vue 3/TS 组合式 API 规范，以及自动化测试的最佳实践。在进行新功能开发、重构或编写测试时调用此 Skill。"
---

# Auto Geo Development Style Guide

本 Skill 旨在确保项目的开发风格保持高度一致，涵盖了后端架构、前端模式、测试规范以及通用的工程实践。

## 1. 后端开发规范 (FastAPI + SQLAlchemy)

### 异步优先 (Async/Await)
- 所有 API 端点和 I/O 密集型 Service 方法必须使用 `async def`。
- 数据库操作使用异步会话（如 `AsyncSession`）。

### 数据模型与验证
- 使用 **SQLAlchemy** 进行 ORM 建模，**Pydantic** 进行数据验证。
- 遵循单一职责原则：
  - `models/`：定义数据库实体。
  - `schemas/`：定义请求/响应的 Pydantic 模型。
  - `api/`：处理请求分发，保持逻辑简洁。
  - `services/`：封装核心业务逻辑。

### 数据库查询优化 (N+1 避免)
- 在处理数据报表时，严禁在循环中执行查询。
- 优先使用 `group_by` 和 `func` 进行数据库层面的聚合。
- 在内存中使用字典（Map）结构快速合并多表数据。

### 依赖注入
- 利用 FastAPI 的 `Depends` 机制管理数据库会话、认证等通用逻辑。

### 异常处理与鲁棒性
- **后端**：统一在 `main.py` 中使用全局异常处理器。在 Playwright 适配器中，应针对不稳定的 DOM 操作使用 `try-except` 块，并提供备用选择器或 JS 注入方案。
- **前端**：在 Axios 拦截器中统一处理 HTTP 异常。使用 `useRequest` 钩子管理 `loading` 和 `error` 状态。

### 日志规范
- **后端**：统一使用 `loguru` 库。记录关键任务节点、API 调用细节及异常堆栈，禁止使用原生 `print`。

### 身份验证与安全
- **多平台授权**：采用“半自动”模式，通过 Playwright 捕获 `cookies` 和 `storage_state`。
- **敏感数据**：存入数据库前必须通过加密模块（如 `services/crypto.py`）进行加密。

## 2. 前端开发规范 (Vue 3 + TS + Electron)

### 组合式 API (Composition API)
- 全量使用 `<script setup>` 语法。
- 将复杂逻辑提取到 `composables/` 目录下的 Hooks 中（如 `useRequest`, `usePagedRequest`）。

### Electron IPC 安全通信
- **通道校验**：在 `ipc-handlers.ts` 中实现 `validateSender` 校验。
- **白名单机制**：仅允许通过预定义的 `INVOKE_CHANNELS` 和 `SEND_CHANNELS` 进行主进程与渲染进程间的通信。

### 类型安全
- **严禁使用 `any`**。必须为 API 返回值、Store 状态和组件 Props 定义明确的接口（Interface/Type）。
- 在 `types/` 目录下集中管理通用类型定义。

### 状态管理 (Pinia)
- 按照功能模块划分 Store（如 `useArticleStore`, `useAccountStore`）。
- Store 内部仅存放状态和修改状态的 Actions，复杂的业务逻辑应留在 Service 层或 Composables 中。

### 组件化开发
- 优先使用 **Element Plus** UI 库。
- 样式使用 **SCSS**，遵循 BEM 命名规范或使用 `scoped` 样式。

## 3. 自动化核心技术 (Playwright)

### 跨上下文交互
- 使用 `context.expose_function` 将后端 Python 函数暴露给浏览器环境，实现“网页内直接触发后端逻辑”。

### 适配器注册表
- 遵循开闭原则，使用 `PublisherRegistry` 动态注册不同平台的发布器。

### DOM 操作“黑科技”
- 当常规 `fill` 或 `click` 失效时，优先考虑使用 `page.evaluate` 注入原生 JS 来手动触发事件或修改样式（如移除遮罩层）。

## 4. 自动化测试规范 (Pytest)

### 模块化组织
- 测试文件应与业务模块对应（如 `tests/test_monitor/test_reports.py`）。
- 复杂场景使用 `pytest markers` 进行标记（如 `@pytest.mark.asyncio`）。

### 基础设施 (Fixtures)
- 充分利用 `conftest.py` 中的 Fixtures，避免在测试用例中重复编写环境搭建代码。
- 集成测试应能够自动处理数据库的初始化和清理。

## 5. 通用工程实践

### 务实与敏捷
- 代码应简洁明了，避免过度设计。
- 允许在非关键路径使用直观的错误提示（如有趣的注释）。

### 高度解耦
- 保持后端服务、前端 UI 与底层自动化引擎（Playwright/n8n）之间的清晰边界。

### 自动化驱动
- 任何重复性的手动操作（如生成报告、多平台发布）都应考虑封装为自动化工具。
