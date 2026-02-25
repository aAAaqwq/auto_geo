# backend/services/websocket_manager.py
from typing import Dict
from fastapi import WebSocket
from loguru import logger


class ConnectionManager:
    def __init__(self):
        # 存储活跃的连接 {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

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
        """🌟 补全此方法：发送消息给指定客户端"""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"发送个人消息失败: {e}")

    async def broadcast(self, message: dict):
        """广播消息给所有客户端"""
        for connection in list(self.active_connections.values()):
            try:
                await connection.send_json(message)
            except Exception:
                # 忽略已经失效的连接
                pass


# 创建全局单例
ws_manager = ConnectionManager()
