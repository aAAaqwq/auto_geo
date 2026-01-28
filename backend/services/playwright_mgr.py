# -*- coding: utf-8 -*-
"""
Playwright浏览器管理器 - 工业级完整版
负责：浏览器生命周期、账号授权、自动化发布、用户名提取
整合了浏览器管理和发布任务执行的基础设施
"""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Any, Callable

from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from loguru import logger
from sqlalchemy.orm import Session

from backend.config import (
    BROWSER_TYPE, BROWSER_ARGS, USER_DATA_DIR,
    LOGIN_CHECK_INTERVAL, LOGIN_MAX_WAIT_TIME, PLATFORMS,
    HOST, PORT
)
from backend.services.crypto import encrypt_cookies, encrypt_storage_state, decrypt_cookies, decrypt_storage_state
# 注意：这里我们只导入 registry，具体的发布器注册逻辑通常在应用启动时完成
from backend.services.playwright.publishers.base import registry


class AuthTask:
    """授权任务模型"""

    def __init__(
            self,
            platform: str,
            account_id: Optional[int] = None,
            account_name: Optional[str] = None
    ):
        self.task_id = str(uuid.uuid4())
        self.platform = platform
        self.account_id = account_id
        self.account_name = account_name
        self.status = "pending"  # pending, running, success, failed, timeout
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.cookies: List[Dict] = []
        self.storage_state: Dict = {}
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()
        # 授权成功后的账号ID（新账号创建后）
        self.created_account_id: Optional[int] = None


class PlaywrightManager:
    """
    Playwright 管理器 (单例模式)
    管理所有浏览器实例、授权任务和上下文
    """

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._auth_tasks: Dict[str, AuthTask] = {}
        self._contexts: Dict[str, BrowserContext] = {}
        self._is_running = False
        # 数据库会话工厂（由外部设置，通常是 SessionLocal）
        self._db_factory: Optional[Callable] = None
        # WebSocket 通知回调
        self._ws_callback: Optional[Callable] = None

    def set_db_factory(self, db_factory: Callable):
        """设置数据库会话工厂"""
        self._db_factory = db_factory

    def set_ws_callback(self, callback: Callable):
        """设置 WebSocket 通知回调"""
        self._ws_callback = callback

    def _get_db(self) -> Optional[Session]:
        """获取数据库会话"""
        if self._db_factory:
            # 如果是生成器函数，使用 next()
            # 如果是类（如 SessionLocal），直接实例化
            try:
                db_obj = self._db_factory()
                if hasattr(db_obj, '__next__'):
                    return next(db_obj)
                return db_obj
            except Exception as e:
                logger.error(f"获取数据库会话失败: {e}")
                return None
        return None

    async def start(self):
        """启动浏览器服务"""
        if self._is_running:
            return

        logger.info("🚀 正在启动 Playwright 浏览器服务...")
        self._playwright = await async_playwright().start()

        # 尝试查找本地 Chrome 路径（绕过检测，更稳定）
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe")
        ]

        executable_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                executable_path = path
                logger.info(f"✅ 找到本地 Chrome 浏览器: {path}")
                break

        launch_options = {
            "headless": False,  # 授权和发布通常需要有头模式，或者由上层控制
            "args": BROWSER_ARGS + [
                "--disable-blink-features=AutomationControlled",  # 核心反爬
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-features=Translate",
                "--no-sandbox"
            ]
        }

        if executable_path:
            launch_options["executable_path"] = executable_path

        try:
            self._browser = await self._playwright[BROWSER_TYPE].launch(**launch_options)
            self._is_running = True
            logger.success(f"✅ Playwright 浏览器 ({BROWSER_TYPE}) 已就绪")
        except Exception as e:
            logger.error(f"❌ 浏览器启动失败: {e}")
            raise e

    async def stop(self):
        """停止浏览器服务"""
        if not self._is_running:
            return

        # 关闭所有上下文
        for context in self._contexts.values():
            await context.close()
        self._contexts.clear()

        # 关闭浏览器
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()

        self._is_running = False
        logger.info("🛑 Playwright 浏览器服务已停止")

    # ==================== 授权相关 ====================

    async def create_auth_task(
            self,
            platform: str,
            account_id: Optional[int] = None,
            account_name: Optional[str] = None
    ) -> AuthTask:
        """
        创建授权任务：启动浏览器，打开登录页，注入JS桥接
        """
        logger.info(f"[Auth] 开始创建授权任务: platform={platform}, account_id={account_id}")

        await self.start()

        if platform not in PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}")

        task = AuthTask(platform, account_id, account_name)
        self._auth_tasks[task.task_id] = task

        platform_config = PLATFORMS[platform]

        # 创建浏览器上下文
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        task.context = context

        # 注入 JS 桥接函数：供前端控制页调用
        async def confirm_auth_wrapper(task_id_from_browser: str) -> str:
            """浏览器调用的确认授权函数"""
            return await self._finalize_auth(task_id_from_browser)

        await context.expose_function("confirmAuth", confirm_auth_wrapper)
        logger.info(f"[Auth] confirmAuth 函数已注入")

        # Tab 1: 打开目标平台登录页
        login_page = await context.new_page()
        task.page = login_page
        await login_page.goto(platform_config["login_url"], wait_until="domcontentloaded")

        # 第二个标签页：打开本地HTML控制页
        # 修复：使用 HTTP URL 代替 file:///，更可靠且解决了拼写错误问题
        control_page_url = f"http://{HOST}:{PORT}/static/auth_confirm.html?task_id={task.task_id}&platform={platform}"

        control_page = await context.new_page()
        try:
            await control_page.goto(control_page_url)
        except Exception as e:
            logger.error(f"打开控制页失败: {e}")

        task.status = "running"
        logger.info(f"[Auth] 授权任务就绪: {task.task_id}")

        return task

    async def _finalize_auth(self, task_id: str) -> str:
        """
        核心：提取登录凭证并入库
        """
        task = self._auth_tasks.get(task_id)
        if not task:
            return json.dumps({"success": False, "message": "任务已失效"})

        logger.info(f"[Auth] 收到确认信号: {task_id}")

        try:
            # 1. 提取 Cookies 和 Storage
            cookies = await task.context.cookies()
            storage_state = await task.page.evaluate(
                "() => ({ localStorage: {...localStorage}, sessionStorage: {...sessionStorage} })") or {}

            # 2. 基础验证
            # 针对不同平台的关键 Cookie 检查
            platform_checks = {
                "zhihu": "z_c0",
                "baijiahao": "BDUSS",
                "toutiao": "sessionid"
            }
            key_cookie = platform_checks.get(task.platform)
            if key_cookie and not any(c['name'] == key_cookie for c in cookies):
                return json.dumps({"success": False, "message": f"未检测到登录凭证 ({key_cookie})，请先登录"})

            # 3. 提取用户名
            username = await self._extract_username(task.page, task.platform)
            logger.info(f"[Auth] 提取到用户名: {username}")

            # 4. 数据库操作
            db = self._get_db()
            if not db:
                return json.dumps({"success": False, "message": "数据库连接失败"})

            try:
                from backend.database.models import Account

                # 加密敏感数据
                enc_cookies = encrypt_cookies(cookies)
                enc_storage = encrypt_storage_state(storage_state)

                if task.account_id:
                    # 更新
                    account = db.query(Account).filter(Account.id == task.account_id).first()
                    if account:
                        account.cookies = enc_cookies
                        account.storage_state = enc_storage
                        account.username = username or account.username
                        account.status = 1
                        account.last_auth_time = datetime.now()
                        db.commit()
                        logger.success(f"[Auth] 账号 {account.account_name} 更新成功")
                else:
                    # 新增
                    name = task.account_name or f"{PLATFORMS[task.platform]['name']}_{username or 'User'}"
                    account = Account(
                        platform=task.platform,
                        account_name=name,
                        username=username,
                        cookies=enc_cookies,
                        storage_state=enc_storage,
                        status=1,
                        last_auth_time=datetime.now()
                    )
                    db.add(account)
                    db.commit()
                    db.refresh(account)
                    task.created_account_id = account.id
                    logger.success(f"[Auth] 新账号 {name} 创建成功")

                task.status = "success"

                # WebSocket 通知
                if self._ws_callback:
                    await self._ws_callback({
                        "type": "auth_complete",
                        "task_id": task_id,
                        "success": True,
                        "platform": task.platform
                    })

                # 延时关闭
                asyncio.create_task(self._delayed_close_task(task_id))

                return json.dumps({"success": True, "message": "授权成功！账号已保存"})

            except Exception as e:
                db.rollback()
                logger.error(f"[Auth] 数据库错误: {e}")
                return json.dumps({"success": False, "message": str(e)})
            finally:
                db.close()

        except Exception as e:
            logger.error(f"[Auth] 处理异常: {e}")
            return json.dumps({"success": False, "message": str(e)})

    async def _delayed_close_task(self, task_id: str):
        """延时关闭任务，给前端反应时间"""
        await asyncio.sleep(5)
        await self.close_auth_task(task_id)

    async def close_auth_task(self, task_id: str):
        """关闭任务资源"""
        task = self._auth_tasks.get(task_id)
        if task:
            if task.context: await task.context.close()
            if task_id in self._auth_tasks: del self._auth_tasks[task_id]
            logger.info(f"[Auth] 任务资源已释放: {task_id}")

    async def _extract_username(self, page: Page, platform: str) -> Optional[str]:
        """
        从页面提取用户名 (增强版)
        """
        try:
            if platform == "zhihu":
                # 尝试多种选择器
                selectors = [".AppHeader-profileText", ".Header-userName", ".UserLink-link", ".ProfileHeader-name"]
                for s in selectors:
                    el = await page.query_selector(s)
                    if el:
                        text = await el.text_content()
                        if text: return text.strip()

            elif platform == "toutiao":
                selectors = [".user-name", ".name", ".mp-name"]
                for s in selectors:
                    el = await page.query_selector(s)
                    if el:
                        text = await el.text_content()
                        if text: return text.strip()

            return None
        except:
            return None

    # ==================== 发布相关 ====================

    async def execute_publish(self, article: Any, account: Any) -> Dict[str, Any]:
        """
        供 Service 调用的发布执行入口 (核心)
        """
        await self.start()

        # 动态获取发布器
        publisher = registry.get(account.platform)
        if not publisher:
            return {"success": False, "error_msg": f"未找到平台 {account.platform} 的适配器"}

        # 准备上下文
        context = None
        try:
            # 解密 Session
            state_data = {}
            if account.storage_state:
                try:
                    decrypted = decrypt_storage_state(account.storage_state)
                    state_data = decrypted if decrypted else json.loads(account.storage_state)
                except:
                    logger.warning(f"账号 {account.account_name} Session 解析失败，尝试裸奔")

            context = await self._browser.new_context(
                storage_state=state_data if state_data else None,
                viewport={"width": 1280, "height": 800}
            )

            page = await context.new_page()

            # 执行发布逻辑
            logger.info(f"🚀 [Publish] 开始执行发布: {account.platform} - {article.title}")
            result = await publisher.publish(page, article, account)

            return result

        except Exception as e:
            logger.exception(f"❌ [Publish] 执行异常: {e}")
            return {"success": False, "error_msg": str(e)}
        finally:
            if context:
                await context.close()


# 全局单例
playwright_mgr = PlaywrightManager()