# -*- coding: utf-8 -*-

import sys
import os
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from typing import List
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles  # 必须导入
from loguru import logger

# 导入配置和数据库
from backend.config import (
    APP_NAME,
    APP_VERSION,
    DEBUG,
    HOST,
    PORT,
    RELOAD,
    CORS_ORIGINS,
    PLATFORMS,
)
from backend.database import init_db, get_db, engine, SessionLocal
from backend.scripts.fix_database import check_and_fix_database

# 导入所有 API 路由模块
from backend.api import (
    account,
    article,
    publish,
    keywords,
    geo,
    index_check,
    reports,
    notifications,
    scheduler,
    knowledge,
    upload,
    candidate,
    auth,
    article_collection,
    site_builder,  # [新增] 网站生成路由
)

# 导入服务组件
from backend.services.websocket_manager import ws_manager
from backend.services.scheduler_service import get_scheduler_service
from backend.services.n8n_service import get_n8n_service

# ==================== 日志拦截器 (核心监控功能) ====================

def socket_log_sink(message):
    """
    Loguru 拦截器：将每一条日志通过 WebSocket 广播出去
    """
    try:
        record = message.record
        log_payload = {
            "time": record["time"].strftime("%H:%M:%S"),
            "level": record["level"].name,
            "module": record["extra"].get("module", "系统"),
            "message": record["message"],
        }
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(ws_manager.broadcast(log_payload))
        except RuntimeError:
            pass
    except Exception:
        pass

# 配置 Loguru
logger.remove()
logger.add(sys.stdout, level="INFO", colorize=True)
logger.add(socket_log_sink, level="INFO")


# ==================== 应用生命周期管理 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    # ---------------- 启动阶段 ----------------
    logger.info(f"🚀 {APP_NAME} v{APP_VERSION} 正在启动...")

    # 1. 初始化数据库
    try:
        init_db()
        check_and_fix_database()
        logger.success("✅ 数据库初始化检查完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 2. 注入全局 WebSocket 管理器
    account.set_ws_manager(ws_manager)
    publish.set_ws_manager(ws_manager)
    notifications.set_ws_callback(ws_manager.broadcast)

    # 3. 初始化 Playwright 管理器
    from backend.services.playwright_mgr import playwright_mgr
    playwright_mgr.set_db_factory(SessionLocal)
    playwright_mgr.set_ws_callback(ws_manager.broadcast)

    # 4. 启动定时任务引擎
    scheduler_instance = get_scheduler_service()
    scheduler_instance.set_db_factory(SessionLocal)
    scheduler_instance.start()
    logger.bind(module="调度中心").success("自动化任务引擎已启动")

    yield

    # ---------------- 关闭阶段 ----------------
    logger.info("正在关闭服务，释放资源...")
    scheduler_instance.stop()
    await playwright_mgr.stop()
    n8n_service = await get_n8n_service()
    await n8n_service.close()
    logger.info("服务已安全关闭")


# ==================== 创建应用实例 ====================
app = FastAPI(title=APP_NAME, version=APP_VERSION, debug=DEBUG, lifespan=lifespan)

# 跨域中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 🛠️ [核心新增] 静态资源挂载 ====================

current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")

if not os.path.exists(static_dir):
    logger.info(f"正在创建静态目录: {static_dir}")
    os.makedirs(static_dir)
if not os.path.exists(os.path.join(static_dir, "uploads")):
    os.makedirs(os.path.join(static_dir, "uploads"))
if not os.path.exists(os.path.join(static_dir, "sites")):
    os.makedirs(os.path.join(static_dir, "sites"))

# 挂载目录
app.mount("/static", StaticFiles(directory=static_dir), name="static")
logger.success(f"✅ 静态资源已挂载: {static_dir}")


# ==================== 注册路由 ====================
app.include_router(account.router)
app.include_router(article.router)
app.include_router(publish.router)
app.include_router(keywords.router)
app.include_router(geo.router)
app.include_router(index_check.router)
app.include_router(reports.router)
app.include_router(notifications.router)
app.include_router(scheduler.router)
app.include_router(knowledge.router)
app.include_router(upload.router)       # 文件上传
app.include_router(candidate.router)
app.include_router(auth.router)
app.include_router(article_collection.router)
app.include_router(site_builder.router) # [新增] 网站生成器路由


# ==================== WebSocket 端点 ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    if not client_id:
        client_id = f"client_{uuid.uuid4().hex[:8]}"

    await ws_manager.connect(websocket, client_id)
    await ws_manager.send_personal(
        {
            "time": "系统",
            "level": "SUCCESS",
            "module": "系统",
            "message": "实时监控链路已就绪",
        },
        client_id,
    )

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"WebSocket 异常: {e}")
        ws_manager.disconnect(client_id)


# ==================== 基础健康检查 ====================
@app.get("/")
async def root():
    return {"app": APP_NAME, "version": APP_VERSION, "status": "running"}

@app.get("/api/health")
async def health():
    return {"status": "ok"}

@app.get("/api/platforms")
async def get_platforms():
    return {"platforms": list(PLATFORMS.values())}


# ==================== 全局异常处理 ====================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.exception(f"未处理的异常: {exc}")
    return HTTPException(status_code=500, detail=str(exc))


# ==================== 启动脚本 ====================
if __name__ == "__main__":
    import uvicorn

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    logger.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
    logger.info(f"服务地址: http://{HOST}:{PORT}")

    uvicorn.run("main:app", host=HOST, port=PORT, reload=RELOAD, log_level="info")
