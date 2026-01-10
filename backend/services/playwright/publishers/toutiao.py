# -*- coding: utf-8 -*-
"""
头条号发布适配器
老王我对头条号也熟悉！
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher


class ToutiaoPublisher(BasePublisher):
    """
    头条号发布适配器

    发布页面：https://mp.toutiao.com/profile/article/article_edit
    """

    async def publish(self, page: Page, article: Any, account: Any) -> Dict[str, Any]:
        """发布文章到头条号"""
        try:
            # 1. 导航到发布页面
            if not await self.navigate_to_publish_page(page):
                return {"success": False, "platform_url": None, "error_msg": "导航失败"}

            # 2. 等待编辑器加载
            await asyncio.sleep(3)

            # 3. 填充标题
            if not await self._fill_title(page, article.title):
                return {"success": False, "platform_url": None, "error_msg": "标题填充失败"}

            # 4. 填充正文
            if not await self._fill_content(page, article.content):
                return {"success": False, "platform_url": None, "error_msg": "正文填充失败"}

            # 5. 点击发布
            if not await self._click_publish(page):
                return {"success": False, "platform_url": None, "error_msg": "发布失败"}

            # 6. 等待结果
            result = await self._wait_for_publish_result(page)

            return result

        except Exception as e:
            logger.error(f"头条号发布失败: {e}")
            return {"success": False, "platform_url": None, "error_msg": str(e)}

    async def _fill_title(self, page: Page, title: str) -> bool:
        """填充标题"""
        try:
            selectors = [
                "[field='title']",
                "input[name='title']",
                "input[placeholder*='标题']",
            ]

            for selector in selectors:
                try:
                    if await self.wait_for_selector(page, selector, 5000):
                        await page.fill(selector, title)
                        logger.info(f"头条号标题已填充: {title[:20]}...")
                        return True
                except Exception:
                    continue

            return False
        except Exception as e:
            logger.error(f"头条号标题填充失败: {e}")
            return False

    async def _fill_content(self, page: Page, content: str) -> bool:
        """填充正文"""
        try:
            # 头条号编辑器
            selectors = [
                ".article-container",
                "[contenteditable='true']",
                ".editor-body",
            ]

            for selector in selectors:
                try:
                    if await self.wait_for_selector(page, selector, 5000):
                        await page.click(selector)
                        await asyncio.sleep(0.5)

                        await page.keyboard.press("Control+A")
                        await asyncio.sleep(0.2)
                        await page.keyboard.type(content)

                        logger.info(f"头条号正文已填充: {len(content)} 字符")
                        return True
                except Exception:
                    continue

            await page.keyboard.type(content)
            logger.info(f"头条号正文已填充（直接输入）: {len(content)} 字符")
            return True

        except Exception as e:
            logger.error(f"头条号正文填充失败: {e}")
            return False

    async def _click_publish(self, page: Page) -> bool:
        """点击发布按钮"""
        try:
            selectors = [
                ".submit-btn",
                "button:has-text('发布')",
                "[class*='submit']",
            ]

            for selector in selectors:
                try:
                    if await self.wait_for_selector(page, selector, 3000):
                        await page.click(selector)
                        logger.info("头条号发布按钮已点击")
                        return True
                except Exception:
                    continue

            return False
        except Exception as e:
            logger.error(f"头条号点击发布失败: {e}")
            return False

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        """等待发布结果"""
        try:
            await asyncio.sleep(3)

            return {
                "success": True,
                "platform_url": page.url,
                "error_msg": None
            }

        except Exception as e:
            return {
                "success": False,
                "platform_url": None,
                "error_msg": f"等待结果失败: {str(e)}"
            }
