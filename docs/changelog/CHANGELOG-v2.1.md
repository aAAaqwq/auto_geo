# AutoGeo v2.1.0 更新日志

**发布日期**: 2026-01-28
**版本**: v2.1.0
**主题**: 账号授权修复与系统稳定性优化

---

## 概述

本次更新主要修复了账号授权功能中控制页面无法显示的关键 Bug，解决了 Windows 系统下的端口冲突问题，并统一修正了项目中多处拼写错误。

---

## 问题分析

### 1. 账号授权失效
- **现象**: 用户在进行账号授权时，浏览器弹出“无法访问您的文件”错误（ERR_FILE_NOT_FOUND）。
- **原因**: 
  - 代码中将 `.html` 误写为 `.hl`（如 `auth_confirm.hl`）。
  - 使用 `file:///` 协议直接打开本地文件，受浏览器安全策略限制且路径解析不稳。

### 2. 端口启动失败 (EACCES)
- **现象**: 前端启动时提示 `Error: listen EACCES: permission denied 127.0.0.1:5173`。
- **原因**: Windows 系统将 `5173` 等常用端口列入了“排除范围”（Excluded Port Range），导致普通程序无权监听。

---

## 核心改动

### 1. 账号授权逻辑优化
- **静态文件服务**: 在 `backend/main.py` 中引入 `fastapi.staticfiles`，将 `backend/static` 目录挂载为 HTTP 服务。
- **访问协议切换**: 在 `backend/services/playwright_mgr.py` 中，将授权控制页的访问方式从 `file:///` 协议切换为 `http://127.0.0.1:8001/static/auth_confirm.html`，彻底解决跨域和路径访问问题。
- **拼写修正**: 修正了 `auth_confirm.html` 的文件引用及相关逻辑。

### 2. 端口与环境适配
- **端口迁移**: 将前端开发服务器默认端口从 `5173` 迁移至 `5500`（避开了 Windows 端口排除范围）。
- **配置同步**:
  - 更新 `fronted/vite.config.ts` 中的 `port` 配置。
  - 更新 `fronted/scripts/dev.js` 中的环境变量。
  - 更新 `backend/config.py` 中的 `CORS_ORIGINS`，允许来自 `5500` 端口的跨域请求。

### 3. 全局拼写修正 (hl -> html)
- **Electron**: 修正 `fronted/electron/main/window-manager.ts` 中对 `index.html` 的引用。
- **测试系统**: 
  - 修正 `tests/helpers/test_reporter.py` 中的方法名（`generate_hl` -> `generate_html`）及生成的标签名。
  - 修正 `tests/run_tests.py` 中的参数及报告路径。

---

## 修复验证

### 验证步骤
1. **服务启动**: 运行 `py -3.11 main.py` 和 `npm run dev`，确认无端口冲突报错。
2. **账号授权**: 在界面点击“添加账号”，观察是否能正确弹出登录页和授权确认页。
3. **功能闭环**: 在授权确认页点击“确认授权”，验证 Cookie 是否成功加密存入数据库。

### 结果
- ✅ 前后端服务正常启动。
- ✅ 授权控制页 `auth_confirm.html` 完美显示。
- ✅ 账号授权流程恢复通畅。

---

## 文件修改清单

| 文件 | 类型 | 说明 |
|------|------|------|
| [main.py](file:///d:/Project/auto_geo-master/auto_geo-master/backend/main.py) | 修改 | 增加静态文件挂载逻辑 |
| [playwright_mgr.py](file:///d:/Project/auto_geo-master/auto_geo-master/backend/services/playwright_mgr.py) | 修改 | 修复拼写错误，切换授权页访问协议 |
| [config.py](file:///d:/Project/auto_geo-master/auto_geo-master/backend/config.py) | 修改 | 更新 CORS 允许源端口 |
| [vite.config.ts](file:///d:/Project/auto_geo-master/auto_geo-master/fronted/vite.config.ts) | 修改 | 调整开发服务器端口为 5500 |
| [dev.js](file:///d:/Project/auto_geo-master/auto_geo-master/fronted/scripts/dev.js) | 修改 | 同步更新 Electron 渲染进程 URL |
| [window-manager.ts](file:///d:/Project/auto_geo-master/auto_geo-master/fronted/electron/main/window-manager.ts) | 修改 | 修正生产模式下的文件引用 |
| [test_reporter.py](file:///d:/Project/auto_geo-master/auto_geo-master/tests/helpers/test_reporter.py) | 修改 | 修正测试报告生成逻辑中的拼写 |
| [run_tests.py](file:///d:/Project/auto_geo-master/auto_geo-master/tests/run_tests.py) | 修改 | 修正测试运行参数中的拼写 |

---

## 技术总结

### 最佳实践
1. **优先使用 HTTP 服务**: 内部静态页面应尽量通过应用自身的 Web 服务（如 FastAPI 的 StaticFiles）提供，而非直接访问磁盘文件，以规避权限和协议限制。
2. **端口冲突处理**: 在 Windows 开发环境下，若遇到 `EACCES` 错误，应先检查 `netsh interface ipv4 show excludedportrange protocol=tcp`，确认端口是否被系统预留。
3. **拼写一致性**: 严格遵守文件扩展名规范，避免因手误导致的资源加载失败。
