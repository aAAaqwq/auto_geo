# AutoGeo 前端

> 老王备注：这个项目用 Electron + Vue3 + Vite 搞的桌面应用前端

## 技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| Electron | ^28.0.0 | 跨平台桌面应用框架 |
| Vue | ^3.4.0 | 渐进式前端框架 |
| TypeScript | ^5.3.0 | JavaScript 超集 |
| Vite | ^5.0.0 | 下一代前端构建工具 |
| Pinia | ^2.1.7 | Vue 官方状态管理 |
| Element Plus | ^2.5.0 | Vue 3 组件库 |

## 目录结构

```
fronted/
├── electron/              # Electron 主进程代码
│   ├── main/             #   主进程入口
│   └── preload/          #   预加载脚本
├── src/                  # 渲染进程源码
│   ├── components/      #   Vue 组件
│   ├── views/           #   页面视图
│   ├── stores/          #   Pinia 状态管理
│   ├── services/        #   API 服务
│   └── types/           #   TypeScript 类型定义
├── scripts/             # 构建脚本
│   └── dev.js          #   开发启动脚本
├── package.json         # 依赖配置
├── vite.config.ts       # Vite 配置
└── tsconfig.json        # TypeScript 配置
```

## 快速开始

### 1. 安装依赖

```bash
cd fronted
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

这会同时启动：
- Vite 开发服务器（http://127.0.0.1:5173）
- Electron 桌面窗口

### 3. 构建生产版本

```bash
npm run build
```

## 可用脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 + Electron |
| `npm run build` | 构建生产版本 |
| `npm run build:renderer` | 仅构建渲染进程 |
| `npm run build:electron` | 仅构建 Electron 主进程 |
| `npm run preview` | 预览构建结果 |
| `npm run type-check` | TypeScript 类型检查 |
| `npm run lint` | ESLint 代码检查 |

## 开发注意事项

### 端口配置

- Vite 开发服务器默认运行在 `http://127.0.0.1:5173`
- API 代理指向 `http://127.0.0.1:8001`

### Electron 通信

主进程与渲染进程通过 IPC 通信，具体通道定义见：
- `electron/main/ipc-handlers.ts` - 主进程处理器
- `electron/preload/index.ts` - 预加载暴露 API

### 依赖问题排查

如果启动时遇到依赖错误：

```bash
# 1. 清理 node_modules 和锁文件
rm -rf node_modules package-lock.json

# 2. 重新安装
npm install

# 3. 如果还有问题，尝试清理 npm 缓存
npm cache clean --force
npm install
```

## 开发规范

- 组件命名：PascalCase（如 `AccountCard.vue`）
- 文件命名：camelCase（如 `useAccount.ts`）
- 代码风格：遵循 ESLint 配置
- 提交前请运行 `npm run lint` 检查代码

---

**维护者**: 老王
**更新日期**: 2025-01-13
