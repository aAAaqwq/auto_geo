# auto_geo 代码审查报告

**审查人**: 小code | **日期**: 2026-03-01 | **范围**: backend/services, backend/api, fronted/src/views, publisher.py

---

## 一、后端 Services 审查

### keyword_service.py ✅ 良好
- 逻辑完整，CRUD + n8n 调用链路清晰
- **问题**: async 方法内用同步 ORM（db.commit()），高并发下可能阻塞事件循环

### geo_article_service.py ✅ 良好
- **问题**: 质检阈值硬编码 >= 60，建议提取为配置项
- **问题**: generate() 缺少对 platform 参数校验

### scheduler_service.py ⚠️ 需改进
- **问题**: retry_failed_checks() 内部 import，应提到文件顶部
- **问题**: 全局单例无线程安全保护
- **问题**: db session 管理用 finally close，建议改为 context manager

### index_check_service.py ✅ 良好
- **问题**: 多平台串行检测，应改为并发
- **问题**: 共用同一个 page 对象，平台间状态可能污染

### publisher.py 🔴 关键问题
1. **headless=False 硬编码** — Linux 无 GUI 服务器会崩溃
2. **Windows User-Agent 硬编码** — Linux 上可能触发反爬
3. **中文变量名**（点击成功）— 不推荐
4. **PublishTask/PublishManager 重复定义** — publisher.py 和 playwright_mgr.py 各有一个
5. **截图路径无目录管理** — 直接写当前目录
6. **裸 except** — 应改为 except Exception

### playwright_mgr.py ⚠️ 需改进
- **600+ 行过长**，职责过多（授权+发布+用户名提取），建议拆分
- **只有 Windows Chrome 路径** — 缺少 Linux 路径（/usr/bin/google-chrome 等）
- **_extract_username() 300+ 行**，硬编码选择器，脆弱难维护
- **confirm_auth_wrapper() 150+ 行**内嵌函数，复杂度过高

---

## 二、后端 API 审查

### 参数校验 ⚠️
- candidate.py 的 sync/update 直接接收 dict，无 Pydantic 校验
- scheduler.py 的 trigger_article_gen() 未实现（只返回成功）

### 返回格式一致性 ⚠️
- reports.py get_overview() 直接返回 dict，没用 ApiResponse
- get_candidates() 返回自定义 dict
- get_project_stats() 直接返回 List，无统一包装

### 缺失接口
- trigger_article_gen() 标注 TODO 未实现
- 缺少批量操作接口
- 缺少 /api/health 健康检查端点

---

## 三、前端 Views 审查

### 空壳页面 🔴
- **AccountAdd.vue** (18行) — 只有提示文字和返回按钮，无实际功能

### 功能不完整 ⚠️
- SchedulerPage.vue — 4个 TODO 未对接 API
- KnowledgePage.vue — 2个 TODO，统计数据用 mock
- CandidatePage.vue — 编辑功能未实现
- Projects.vue — 文章数量硬编码返回 0

---

## 四、TODO/FIXME 汇总（共 11 个）

### 后端 (3个)
- api/scheduler.py L133: TODO 保存到数据库或配置文件
- api/scheduler.py L134: TODO 动态更新任务
- api/scheduler.py L197: TODO 实现文章生成触发逻辑

### 前端 (8个)
- geo/Projects.vue L263: TODO 从API获取文章数量
- knowledge/KnowledgePage.vue L432,L485: TODO 从API获取数据
- scheduler/SchedulerPage.vue L509,L515,L526,L604: TODO API对接
- candidate/CandidatePage.vue L391: TODO 编辑功能

---

## 五、优先级

### P0 必须修复（影响部署）
1. headless=False 硬编码 → Linux 无法运行
2. 只有 Windows Chrome 路径 → 需加 Linux 路径
3. PublishTask/PublishManager 重复定义

### P1 应该修复（影响功能）
4. AccountAdd.vue 空壳页面
5. SchedulerPage.vue TODO 未对接
6. trigger_article_gen() 未实现
7. API 返回格式不统一

### P2 建议改进（代码质量）
8. playwright_mgr.py 拆分
9. 同步/异步 ORM 混用
10. 中文变量名清理
11. 裸 except 修复

---
*审查完成 | 小code | 2026-03-01*
