# -*- coding: utf-8 -*-
"""
AutoGeo 后端服务入口
用FastAPI，异步高性能！
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import uuid
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from backend.config import (
    APP_NAME, APP_VERSION, DEBUG, HOST, PORT, RELOAD,
    CORS_ORIGINS, PLATFORMS
)
from backend.database import init_db, get_db, engine
from backend.api import account, article, publish, keywords, geo, index_check, reports, notifications, scheduler, knowledge


# ==================== WebSocket连接管理 ====================
class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """接受连接"""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket连接建立: {client_id}")

    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket连接断开: {client_id}")

    async def send_personal(self, message: dict, client_id: str):
        """发送消息给指定客户端"""
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(message)

    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        for connection in self.active_connections.values():
            await connection.send_json(message)


ws_manager = ConnectionManager()  # WebSocket管理器，给个清晰的命名


# ==================== 应用生命周期 ====================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info(f"{APP_NAME} v{APP_VERSION} 正在启动...")
    init_db()  # 初始化数据库

    # 设置 account API 的 WebSocket 管理器
    account.set_ws_manager(ws_manager)
    # 设置 publish API 的 WebSocket 管理器
    publish.set_ws_manager(ws_manager)
    # 设置 notifications API 的 WebSocket 回调
    notifications.set_ws_callback(ws_manager.broadcast)

    # 导入并启动Playwright（延迟导入）
    from backend.services.playwright_mgr import playwright_mgr
    # 设置数据库工厂
    playwright_mgr.set_db_factory(get_db)
    # 设置WebSocket回调
    playwright_mgr.set_ws_callback(ws_manager.broadcast)
    # 注意：不在启动时自动启动浏览器，按需启动

    yield

    # 关闭时
    logger.info("正在关闭服务...")
    from backend.services.playwright_mgr import playwright_mgr
    await playwright_mgr.stop()


# ==================== 创建应用 ====================
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    debug=DEBUG,
    lifespan=lifespan
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(account.router)
app.include_router(article.router)
app.include_router(publish.router)  # 加上发布路由！
app.include_router(keywords.router)  # 加上关键词路由！
app.include_router(geo.router)  # 加上GEO文章路由！
app.include_router(index_check.router)  # 加上收录检测路由！
app.include_router(reports.router)  # 加上数据报表路由！
app.include_router(notifications.router)  # 加上预警通知路由！
app.include_router(scheduler.router)  # 加上定时任务路由！
app.include_router(knowledge.router)  # 加上知识库路由！


# ==================== 基础接口 ====================
@app.get("/")
async def root():
    """健康检查"""
    return {
        "name": APP_NAME,
        "version": APP_VERSION,
        "status": "running"
    }


@app.get("/api/health")
async def health():
    """健康检查"""
    return {"status": "ok"}


@app.get("/api/platforms")
async def get_platforms():
    """获取支持的平台列表"""
    return {
        "platforms": list(PLATFORMS.values())
    }


# ==================== WebSocket ====================
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, client_id: str = None):
    """
    WebSocket端点

    注意：用于实时推送发布进度！
    """
    if not client_id:
        client_id = str(uuid.uuid4())

    await ws_manager.connect(websocket, client_id)

    try:
        while True:
            data = await websocket.receive_text()
            # 处理客户端消息（心跳等）
            logger.debug(f"收到WebSocket消息: {client_id} - {data}")
    except WebSocketDisconnect:
        ws_manager.disconnect(client_id)


# ==================== 错误处理 ====================
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return HTTPException(status_code=500, detail="服务器内部错误")


# ==================== 启动服务 ====================
if __name__ == "__main__":
    import uvicorn
    import asyncio
    import sys
    import signal

    # 修复：Windows 上 asyncio 子进程需要 ProactorEventLoop
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

    logger.info(f"正在启动 {APP_NAME} v{APP_VERSION}...")
    logger.info(f"服务地址: http://{HOST}:{PORT}")
    logger.info(f"API文档: http://{HOST}:{PORT}/docs")

    # 创建 uvicorn 配置
    # 注意：reload 模式下优雅关闭可能不完全，生产环境建议设为 False
    config = uvicorn.Config(
        app=app,
        host=HOST,
        port=PORT,
        reload=RELOAD,
        log_level="info",
        # 优雅关闭超时时间（秒）
        timeout_graceful_shutdown=5
    )
    server = uvicorn.Server(config)

    # 优雅关闭处理
    def signal_handler(sig: int, frame):
        """处理关闭信号"""
        logger.info(f"收到关闭信号, 正在优雅关闭服务...")
        # 设置退出标志
        if hasattr(server, 'should_exit'):
            server.should_exit = True
        # 同时也调用 shutdown
        if hasattr(server, 'shutdown'):
            asyncio.create_task(server.shutdown())

    # 注册信号处理器
    # Windows: 只支持 SIGINT (Ctrl+C)
    # Unix: 支持 SIGINT, SIGTERM
    if sys.platform == "win32":
        signal.signal(signal.SIGINT, signal_handler)
    else:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    # 运行服务器
    try:
        server.run()
    except KeyboardInterrupt:
        logger.info("收到 Ctrl+C, 正在关闭...")
    finally:
        logger.info("正在清理资源...")
        # 关闭所有 WebSocket 连接
        for client_id in list(ws_manager.active_connections.keys()):
            logger.debug(f"关闭 WebSocket 连接: {client_id}")
        ws_manager.active_connections.clear()

        # 关闭 Playwright 浏览器
        try:
            from backend.services.playwright_mgr import playwright_mgr
            asyncio.run(playwright_mgr.stop())
            logger.info("Playwright 浏览器已关闭")
        except Exception as e:
            logger.debug(f"关闭 Playwright 时出错: {e}")

        # 关闭数据库连接
        try:
            engine.dispose()
            logger.info("数据库连接已关闭")
        except Exception as e:
            logger.debug(f"关闭数据库连接时出错: {e}")

        logger.info(f"{APP_NAME} 已安全关闭")
