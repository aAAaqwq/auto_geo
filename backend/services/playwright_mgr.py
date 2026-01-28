# -*- coding: utf-8 -*-
"""
Playwright浏览器管理器
用异步模式，效率拉满！
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
    LOGIN_CHECK_INTERVAL, LOGIN_MAX_WAIT_TIME, PLATFORMS
)
from backend.services.crypto import encrypt_cookies, encrypt_storage_state, decrypt_cookies, decrypt_storage_state


class AuthTask:
    """授权任务"""
    def __init__(
        self,
        platform: str,
        account_id: Optional[int] = None,
        account_name: Optional[str] = None,
        owner_id: Optional[int] = None,
    ):
        self.task_id = str(uuid.uuid4())
        self.platform = platform
        self.account_id = account_id
        self.account_name = account_name
        self.owner_id = owner_id
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
    Playwright管理器

    注意：这个类管理所有浏览器实例，！
    """

    def __init__(self):
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._auth_tasks: Dict[str, AuthTask] = {}
        self._contexts: Dict[str, BrowserContext] = {}
        self._is_running = False
        # 数据库会话（由外部设置）
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
            # get_db 是生成器函数，需要用 next() 获取实际的会话
            return next(self._db_factory())
        return None

    async def start(self):
        """启动浏览器服务"""
        if self._is_running:
            return

        self._playwright = await async_playwright().start()

        # 用真实Chrome，不用Chromium被知乎检测！
        # Windows Chrome路径
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                os.environ.get("USERNAME", "")
            ),
        ]

        executable_path = None
        for path in chrome_paths:
            if os.path.exists(path):
                executable_path = path
                logger.info(f"找到Chrome浏览器: {path}")
                break

        launch_options = {
            "headless": False,
            "args": BROWSER_ARGS + [
                "--disable-dev-shm-usage",
                "--disable-background-networking",
                "--disable-background-timer-throttling",
                "--disable-backgrounding-occluded-windows",
                "--disable-renderer-backgrounding",
                "--disable-features=Translate",
                "--disable-ipc-flooding-protection",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            ]
        }

        if executable_path:
            launch_options["executable_path"] = executable_path

        self._browser = await self._playwright[BROWSER_TYPE].launch(**launch_options)
        self._is_running = True
        logger.info(f"Playwright浏览器已启动: {BROWSER_TYPE}")

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
        logger.info("Playwright浏览器已停止")

    async def create_auth_task(
        self,
        platform: str,
        account_id: Optional[int] = None,
        account_name: Optional[str] = None,
        owner_id: Optional[int] = None,
    ) -> AuthTask:
        """
        创建授权任务

        用 expose_function 绕过 CORS 问题！
        用户在目标页面登录后，切换到控制页点击按钮即可。

        Args:
            platform: 平台ID
            account_id: 账号ID（更新授权时使用）
            account_name: 账号名称（新账号时使用）

        Returns:
            授权任务对象
        """
        logger.info(f"[create_auth_task] 开始创建授权任务: platform={platform}, account_id={account_id}, account_name={account_name}")

        await self.start()

        if platform not in PLATFORMS:
            raise ValueError(f"不支持的平台: {platform}")

        task = AuthTask(platform, account_id, account_name, owner_id)
        self._auth_tasks[task.task_id] = task

        platform_config = PLATFORMS[platform]
        logger.info(f"[create_auth_task] 任务创建成功: task_id={task.task_id}")

        # 创建浏览器上下文
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        )
        task.context = context

        # 定义授权确认函数（将被暴露给浏览器）
        async def confirm_auth_wrapper(task_id_from_browser: str) -> str:
            """浏览器调用的确认授权函数 - 返回JSON字符串"""
            logger.info(f"[授权确认] 收到请求: task_id={task_id_from_browser}")

            if task_id_from_browser != task.task_id:
                logger.warning(f"[授权确认] 任务ID不匹配: 期望{task.task_id}, 收到{task_id_from_browser}")
                return '{"success": false, "message": "任务ID不匹配"}'

            # 提取cookies和存储状态
            if not task.context or not task.page:
                logger.error("[授权确认] 授权任务已失效")
                return '{"success": false, "message": "授权任务已失效，请重新开始授权"}'

            try:
                all_cookies = await task.context.cookies()
                storage_state = await task.page.evaluate("""
                    () => {
                        return {
                            localStorage: {...localStorage},
                            sessionStorage: {...sessionStorage}
                        };
                    }
                """) or {}

                logger.info(f"[授权确认] 提取到 {len(all_cookies)} 个cookies")

                # 各平台的登录验证关键cookie（只用这些来判断是否登录！）
                # 注意：按调研文档建议，我们会保存全部cookies，但只用关键cookie做登录验证
                platform_login_check_cookies = {
                    "zhihu": ["z_c0"],  # 知乎：z_c0是登录成功凭证，最核心！
                    "baijiahao": ["BDUSS"],  # 百家号：BDUSS是百度统一登录凭证，最核心！
                    "sohu": ["SUV"],  # 搜狐：SUV是唯一设备标识
                    "toutiao": ["sessionid"],  # 头条：sessionid会话ID
                }

                # 获取当前平台用于验证登录的关键cookies
                check_cookies = platform_login_check_cookies.get(task.platform, [])
                cookie_names = {c["name"] for c in all_cookies}

                logger.info(f"[授权确认] 验证用关键cookie: {check_cookies}")
                logger.info(f"[授权确认] 当前所有cookies: {list(cookie_names)}")

                # 验证是否真的登录了（检查关键cookie是否存在）
                missing_cookies = [name for name in check_cookies if name not in cookie_names]

                if missing_cookies:
                    missing_str = ", ".join(missing_cookies)
                    logger.warning(f"[授权确认] 未检测到登录cookie，缺少: {missing_str}")
                    return f'{{"success": false, "message": "未检测到登录信息，请先在平台完成登录！缺少关键cookie: {missing_str}"}}'

                # 按调研文档建议：保存全部cookies，不要精简！
                # 因为各平台可能会验证多个cookie的组合
                cookies_to_save = all_cookies
                logger.info(f"[授权确认] 登录验证通过，保存全部 {len(cookies_to_save)} 个cookies")

                # 新增：提取平台用户名
                username = await self._extract_username(task.page, task.platform)
                if username:
                    logger.info(f"[授权确认] 提取到用户名: {username}")
                else:
                    logger.info("[授权确认] 未提取到用户名，使用默认值")

                # 保存到数据库
                db = self._get_db()
                if not db:
                    logger.error("[授权确认] 无法获取数据库会话")
                    return '{"success": false, "message": "数据库连接失败"}'

                try:
                    from backend.database.models import Account

                    if task.account_id:
                        # 更新现有账号
                        account = db.query(Account).filter(Account.id == task.account_id).first()
                        if account:
                            account.cookies = encrypt_cookies(cookies_to_save)  # 保存全部cookies
                            account.storage_state = encrypt_storage_state(storage_state)
                            account.status = 1
                            account.last_auth_time = task.created_at
                            account.username = username or account.username  # 更新：保存用户名
                            db.commit()
                            task.account_id = account.id
                            logger.info(f"[授权确认] 账号已更新: {account.id}")
                            account_id_to_return = account.id
                        else:
                            logger.warning(f"[授权确认] 账号不存在: {task.account_id}")
                            return '{"success": false, "message": "账号不存在"}'
                    else:
                        # 创建新账号
                        account_name_to_use = task.account_name or f"{PLATFORMS[task.platform]['name']}账号"
                        account = Account(
                            owner_id=task.owner_id,
                            platform=task.platform,
                            account_name=account_name_to_use,
                            username=username,  # 新增：保存用户名
                            cookies=encrypt_cookies(cookies_to_save),  # 保存全部cookies
                            storage_state=encrypt_storage_state(storage_state),
                            status=1,
                            last_auth_time=task.created_at
                        )
                        db.add(account)
                        db.commit()
                        db.refresh(account)
                        task.created_account_id = account.id
                        logger.info(f"[授权确认] 新账号已创建: {account.id}")
                        account_id_to_return = account.id

                    task.status = "success"
                    task.cookies = cookies_to_save  # 保存全部cookies
                    task.storage_state = storage_state

                    # 通过 WebSocket 通知前端
                    if self._ws_callback:
                        await self._ws_callback({
                            "type": "auth_complete",
                            "task_id": task.task_id,
                            "platform": task.platform,
                            "account_id": task.account_id or task.created_account_id,
                            "success": True
                        })

                    import json
                    result = json.dumps({
                        "success": True,
                        "message": "授权成功！账号已保存",
                        "data": {
                            "account_id": account_id_to_return,
                            "platform": task.platform,
                            "task_id": task_id_from_browser,
                            "cookies_count": len(cookies_to_save)
                        }
                    })

                    # 授权成功后关闭浏览器
                    logger.info(f"[授权确认] 授权成功，正在关闭浏览器...")
                    await task.context.close()

                    return result

                except Exception as e:
                    logger.error(f"[授权确认] 数据库操作失败: {e}")
                    db.rollback()
                    return f'{{"success": false, "message": "保存失败: {str(e)}"}}'
                finally:
                    db.close()

            except Exception as e:
                logger.error(f"[授权确认] 处理失败: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return f'{{"success": false, "message": "{str(e)}"}}'

        # 暴露函数给浏览器（绕过CORS！）
        await context.expose_function("confirmAuth", confirm_auth_wrapper)
        logger.info(f"[授权] confirmAuth 函数已暴露到浏览器上下文")

        # 第一个标签页：打开目标平台登录页
        login_page = await context.new_page()
        task.page = login_page
        await login_page.goto(platform_config["login_url"], wait_until="domcontentloaded")

        # 第二个标签页：打开本地HTML控制页
        static_dir = Path(__file__).parent.parent.parent / "backend" / "static"
        control_page_path = static_dir / "auth_confirm.hl"
        control_page_url = f"file:///{control_page_path.as_posix()}?task_id={task.task_id}&platform={platform}"

        control_page = await context.new_page()
        await control_page.goto(control_page_url)

        task.status = "running"
        logger.info(f"授权任务已创建: {task.task_id}, 平台: {platform_config['name']}, 已打开本地控制页")

        return task

    async def _check_login_status(self, task: AuthTask):
        """
        检测登录状态

        注意：各平台的登录成功判断逻辑不同，需要适配！
        """
        start_time = datetime.now()
        platform = task.platform

        while True:
            # 检查超时
            elapsed = (datetime.now() - start_time).total_seconds() * 1000
            if elapsed > LOGIN_MAX_WAIT_TIME:
                task.status = "timeout"
                task.error_message = "授权超时，请重试"
                logger.warning(f"授权任务超时: {task.task_id}")
                break

            # 检查登录状态（平台特定逻辑）
            is_logged_in = await self._check_platform_login(task.page, platform)

            if is_logged_in:
                # 登录成功，提取cookies和存储状态
                task.cookies = await task.context.cookies()
                task.storage_state = await task.page.evaluate("""
                    () => {
                        return {
                            localStorage: {...localStorage},
                            sessionStorage: {...sessionStorage}
                        };
                    }
                """) or {}
                task.status = "success"
                logger.info(f"授权成功: {task.task_id}")

                # 自动保存到数据库
                await self._save_auth_result(task)
                break

            await asyncio.sleep(LOGIN_CHECK_INTERVAL / 1000)

    async def _save_auth_result(self, task: AuthTask):
        """
        保存授权结果到数据库

        用这个来自动创建或更新账号记录！
        """
        db = self._get_db()
        if not db:
            logger.warning(f"无法获取数据库会话，跳过保存授权结果: {task.task_id}")
            return

        try:
            from backend.database.models import Account

            if task.account_id:
                # 更新现有账号
                account = db.query(Account).filter(Account.id == task.account_id).first()
                if account:
                    account.cookies = encrypt_cookies(task.cookies)
                    account.storage_state = encrypt_storage_state(task.storage_state)
                    account.status = 1  # 激活账号
                    account.last_auth_time = task.created_at
                    db.commit()
                    logger.info(f"账号授权已更新: {account.id}")
                    task.account_id = account.id
                else:
                    logger.warning(f"账号不存在: {task.account_id}")
            else:
                # 创建新账号
                account_name = task.account_name or f"{PLATFORMS[task.platform]['name']}账号"
                account = Account(
                    owner_id=task.owner_id,
                    platform=task.platform,
                    account_name=account_name,
                    cookies=encrypt_cookies(task.cookies),
                    storage_state=encrypt_storage_state(task.storage_state),
                    status=1,  # 激活账号
                    last_auth_time=task.created_at
                )
                db.add(account)
                db.commit()
                db.refresh(account)
                task.created_account_id = account.id
                logger.info(f"新账号已创建: {account.id}, 名称: {account_name}")

            # 通过 WebSocket 通知前端
            if self._ws_callback:
                await self._ws_callback({
                    "type": "auth_complete",
                    "task_id": task.task_id,
                    "platform": task.platform,
                    "account_id": task.account_id or task.created_account_id,
                    "success": True
                })

        except Exception as e:
            logger.error(f"保存授权结果失败: {e}")
            db.rollback()
        finally:
            db.close()

    async def _check_platform_login(self, page: Page, platform: str) -> bool:
        """
        检查各平台登录状态

        注意：这个方法需要根据各平台实际页面结构调整！
        """
        try:
            if platform == "zhihu":
                # 知乎：检查是否有用户头像或登录按钮消失
                await page.wait_for_selector(".AppHeader-header, .Header", timeout=5000)
                has_login = await page.query_selector(".Header-loginButton") is None
                return has_login

            elif platform == "baijiahao":
                # 百家号：检查是否跳转到主页或存在用户信息
                url = page.url
                return "builder/rc" in url or "login" not in url

            elif platform == "sohu":
                # 搜狐：检查是否存在用户头像
                return await page.query_selector(".user-avatar, .avatar") is not None

            elif platform == "toutiao":
                # 头条：检查是否有用户信息
                return await page.query_selector(".user-info, .avatar") is not None

            else:
                # 默认：检查URL是否变化
                return "login" not in page.url

        except Exception as e:
            logger.debug(f"登录状态检测异常: {platform}, {e}")
            return False

    async def load_account_context(self, account_id: int, platform: str,
                                    encrypted_cookies: str,
                                    encrypted_storage: str) -> BrowserContext:
        """
        加载已保存的账号上下文

        Args:
            account_id: 账号ID
            platform: 平台ID
            encrypted_cookies: 加密的cookies
            encrypted_storage: 加密的存储状态

        Returns:
            浏览器上下文
        """
        await self.start()

        context_id = f"{platform}_{account_id}"

        # 如果上下文已存在，直接返回
        if context_id in self._contexts:
            return self._contexts[context_id]

        # 解密数据
        cookies = decrypt_cookies(encrypted_cookies)
        storage_state = decrypt_storage_state(encrypted_storage)

        # 创建新上下文
        context = await self._browser.new_context(
            viewport={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )

        # 添加cookies
        if cookies:
            await context.add_cookies(cookies)

        self._contexts[context_id] = context
        logger.info(f"账号上下文已加载: {context_id}")

        return context

    def get_auth_task(self, task_id: str) -> Optional[AuthTask]:
        """获取授权任务"""
        return self._auth_tasks.get(task_id)

    def get_auth_tasks(self) -> List[AuthTask]:
        """获取所有授权任务"""
        return list(self._auth_tasks.values())

    async def close_auth_task(self, task_id: str):
        """关闭授权任务"""
        task = self._auth_tasks.get(task_id)
        if task:
            if task.context:
                await task.context.close()
            del self._auth_tasks[task_id]
            logger.info(f"授权任务已关闭: {task_id}")

    async def _extract_username(self, page: Page, platform: str) -> Optional[str]:
        """
        从平台页面提取用户名

        用这个来获取平台用户名并保存到数据库！
        """
        import re

        try:
            if platform == "zhihu":
                # 知乎：从页面标题或个人信息中提取
                # 等待页面加载
                await asyncio.sleep(2)  # 给页面更多加载时间

                # 尝试从页面获取用户信息
                try:
                    # 方法1：尝试访问知乎个人中心API获取用户名
                    user_info = await page.evaluate("""() => {
                        // 尝试从localStorage获取用户信息
                        const userInfo = localStorage.getItem('zse93') || localStorage.getItem('userInfo');
                        if (userInfo) {
                            try {
                                return JSON.parse(userInfo);
                            } catch(e) {}
                        }
                        // 尝试从页面获取
                        const nameEl = document.querySelector('.AppHeader-profileText') ||
                                      document.querySelector('.Header-userName') ||
                                      document.querySelector('[data-zop-userlink]');
                        if (nameEl) {
                            return { name: nameEl.textContent || nameEl.getAttribute('data-zop-userlink') };
                        }
                        return null;
                    }""")
                    if user_info and isinstance(user_info, dict):
                        username = user_info.get('name') or user_info.get('userName') or user_info.get('screenName')
                        if username:
                            logger.info(f"[知乎] 从页面数据提取到用户名: {username}")
                            return username
                except Exception as e:
                    logger.debug(f"[知乎] 从页面数据提取失败: {e}")

                # 方法2：尝试多种选择器
                selectors = [
                    ".AppHeader-profileText",  # 新版知乎
                    ".Header-userName",  # 旧版知乎
                    "[data-zop-userlink]",  # 用户链接
                    ".ProfileHeader-name",  # 个人主页
                    ".UserLink-link",  # 用户链接
                ]
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip():
                                username = text.strip()
                                logger.info(f"[知乎] 提取到用户名: {username}")
                                return username
                    except Exception:
                        continue

                # 方法3：尝试从 URL 提取（知乎个人主页 URL 格式）
                url = page.url
                if "people/" in url or "zhihu.com/" in url:
                    match = re.search(r"zhihu\.com/people/([^/?]+)", url)
                    if match:
                        username = match.group(1)
                        logger.info(f"[知乎] 从URL提取到用户名: {username}")
                        return username

            elif platform == "baijiahao":
                # 百家号：需要访问作者中心页面获取用户名
                await asyncio.sleep(2)

                # 百家号需要从页面API或cookie中获取
                try:
                    # 尝试从页面获取用户信息
                    user_info = await page.evaluate("""() => {
                        // 尝试从localStorage获取
                        for (let key in localStorage) {
                            if (key.includes('user') || key.includes('User')) {
                                try {
                                    const data = JSON.parse(localStorage[key]);
                                    if (data && (data.name || data.userName || data.nickname)) {
                                        return data;
                                    }
                                } catch(e) {}
                            }
                        }
                        // 尝试从页面元素获取
                        const nameEl = document.querySelector('.user-name') ||
                                      document.querySelector('.author-name') ||
                                      document.querySelector('[class*="userName"]');
                        if (nameEl) {
                            return { name: nameEl.textContent };
                        }
                        return null;
                    }""")
                    if user_info:
                        username = (user_info.get('name') or user_info.get('userName') or
                                   user_info.get('nickname') or user_info.get('authorName'))
                        if username:
                            logger.info(f"[百家号] 提取到用户名: {username}")
                            return str(username)
                except Exception as e:
                    logger.debug(f"[百家号] 从页面提取用户名失败: {e}")

                # 尝试从页面URL或导航栏获取
                try:
                    # 访问百家号主页查看用户名
                    await page.goto("https://baijiahao.baidu.com/builder/rc/static/author/index", wait_until="networkidle")
                    await asyncio.sleep(2)

                    selectors = [
                        ".user-name",
                        ".author-name",
                        "[class*='user-name']",
                        "[class*='author-name']",
                        ".name-text",
                    ]
                    for selector in selectors:
                        try:
                            element = await page.query_selector(selector)
                            if element:
                                text = await element.text_content()
                                if text and text.strip() and len(text.strip()) > 1:
                                    username = text.strip()
                                    logger.info(f"[百家号] 从作者中心提取到用户名: {username}")
                                    return username
                        except Exception:
                            continue
                except Exception as e:
                    logger.debug(f"[百家号] 访问作者中心失败: {e}")

                logger.info("[百家号] 无法提取用户名，使用默认值")
                return "百家号作者"

            elif platform == "sohu":
                # 搜狐号
                await asyncio.sleep(2)
                await page.wait_for_load_state("networkidle", timeout=5000)

                # 尝试从页面获取用户信息
                try:
                    user_info = await page.evaluate("""() => {
                        // 尝试从localStorage获取
                        for (let key in localStorage) {
                            if (key.includes('user') || key.includes('User')) {
                                try {
                                    const data = JSON.parse(localStorage[key]);
                                    if (data && (data.name || data.userName)) {
                                        return data;
                                    }
                                } catch(e) {}
                            }
                        }
                        return null;
                    }""")
                    if user_info:
                        username = user_info.get('name') or user_info.get('userName')
                        if username:
                            logger.info(f"[搜狐] 提取到用户名: {username}")
                            return str(username)
                except Exception:
                    pass

                selectors = [
                    ".user-name",
                    ".author-name",
                    "[class*='user'] [class*='name']",
                    ".user-info .name",
                    "[class*='nickname']",
                ]
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip() and len(text.strip()) > 1:
                                username = text.strip()
                                logger.info(f"[搜狐] 提取到用户名: {username}")
                                return username
                    except Exception:
                        continue

            elif platform == "toutiao":
                # 头条号
                await asyncio.sleep(2)
                await page.wait_for_load_state("networkidle", timeout=5000)

                # 尝试从页面获取用户信息
                try:
                    user_info = await page.evaluate("""() => {
                        // 尝试从localStorage获取
                        for (let key in localStorage) {
                            if (key.includes('user') || key.includes('User')) {
                                try {
                                    const data = JSON.parse(localStorage[key]);
                                    if (data && (data.name || data.userName || data.user_info)) {
                                        return data;
                                    }
                                } catch(e) {}
                            }
                        }
                        return null;
                    }""")
                    if user_info:
                        username = (user_info.get('name') or user_info.get('userName') or
                                   user_info.get('user_info', {}).get('name'))
                        if username:
                            logger.info(f"[头条] 提取到用户名: {username}")
                            return str(username)
                except Exception:
                    pass

                selectors = [
                    ".user-name",
                    ".author-name",
                    "[class*='user'] [class*='name']",
                    ".user-info .name",
                    "[class*='nickname']",
                    ".mp-name",
                ]
                for selector in selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            text = await element.text_content()
                            if text and text.strip() and len(text.strip()) > 1:
                                username = text.strip()
                                logger.info(f"[头条] 提取到用户名: {username}")
                                return username
                    except Exception:
                        continue

            logger.warning(f"[{platform}] 未能提取用户名")
            return None

        except Exception as e:
            logger.warning(f"[{platform}] 提取用户名失败: {e}")
            return None


# 全局单例
playwright_mgr = PlaywrightManager()


# ==================== 发布功能 ====================

class PublishTask:
    """发布任务"""
    def __init__(self, task_id: str, article: Any, account: Any, platform: str, publisher):
        self.task_id = task_id
        self.article = article
        self.account = account
        self.platform = platform
        self.publisher = publisher
        self.status = "pending"  # pending, publishing, success, failed
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.created_at = datetime.now()


    async def execute(self, context: BrowserContext):
        """执行发布任务"""
        self.status = "publishing"

        try:
            # 创建页面
            page = await context.new_page()

            # 调用发布器发布
            self.result = await self.publisher.publish(page, self.article, self.account)

            if self.result.get("success"):
                self.status = "success"
            else:
                self.status = "failed"
                self.error_message = self.result.get("error_msg", "未知错误")

        except Exception as e:
            self.status = "failed"
            self.error_message = str(e)
            self.result = {
                "success": False,
                "platform_url": None,
                "error_msg": str(e)
            }
            logger.error(f"发布任务执行失败: {self.task_id}, {e}")

        finally:
            try:
                await page.close()
            except Exception:
                pass


    async def execute_with_context(self, playwright_mgr: PlaywrightManager):
        """
        使用playwright_mgr创建上下文并执行发布
        """
        # 加载账号上下文
        context = await playwright_mgr.load_account_context(
            self.account.id,
            self.platform,
            self.account.cookies or "",
            self.account.storage_state or ""
        )

        # 执行发布
        await self.execute(context)


class PublishManager:
    """
    发布管理器
    用这个来管理批量发布任务！
    """

    def __init__(self, platforms_config: Dict[str, Any]):
        self.platforms_config = platforms_config
        self._publishers: Dict[str, Any] = {}

        # 导入并注册发布器
        from services.playwright.publishers import register_publishers
        register_publishers(platforms_config)

        # 获取所有发布器
        from services.playwright.publishers import list_publishers
        self._publishers = list_publishers()

        logger.info(f"发布管理器已初始化，已注册 {len(self._publishers)} 个平台")

    def get_publisher(self, platform_id: str) -> Optional[Any]:
        """获取平台发布器"""
        return self._publishers.get(platform_id)

    async def create_task(self, task_id: str, article: Any, account: Any) -> PublishTask:
        """创建发布任务"""
        publisher = self.get_publisher(account.platform)
        if not publisher:
            raise ValueError(f"不支持的平台: {account.platform}")

        task = PublishTask(task_id, article, account, account.platform, publisher)
        return task

    async def execute_task(self, task: PublishTask) -> Dict[str, Any]:
        """执行单个发布任务"""
        await task.execute_with_context(playwright_mgr)

        return {
            "task_id": task.task_id,
            "status": task.status,
            "result": task.result,
            "error_msg": task.error_message
        }

    async def execute_batch(self, tasks: List[PublishTask], progress_callback=None):
        """批量执行发布任务"""
        completed = 0

        for task in tasks:
            result = await self.execute_task(task)
            completed += 1

            # 进度回调
            if progress_callback:
                await progress_callback(completed, len(tasks), task)

        return {
            "total": len(tasks),
            "completed": completed,
            "results": [t.result for t in tasks]
        }
