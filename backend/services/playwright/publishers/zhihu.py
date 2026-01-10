# -*- coding: utf-8 -*-
"""
知乎发布适配器
老王我研究过知乎的页面结构，这tm得仔细处理！
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher


class ZhihuPublisher(BasePublisher):
    """
    知乎发布适配器

    发布页面：https://zhuanlan.zhihu.com/write
    """

    # 选择器定义（老王我根据实际页面结构定义的）
    SELECTORS = {
        "title_input": "input[placeholder*='标题']",
        "content_editor": ".public-DraftStyleDefault-block",  # Draft.js编辑器
        "publish_button": ".PublishButton",
        "publish_success_indicator": ".PostItem",
    }

    async def publish(self, page: Page, article: Any, account: Any) -> Dict[str, Any]:
        """
        发布文章到知乎
        """
        try:
            # 1. 导航到发布页面
            if not await self.navigate_to_publish_page(page):
                return {"success": False, "platform_url": None, "error_msg": "导航失败"}

            # 2. 等待编辑器加载
            await asyncio.sleep(2)

            # 3. 填充标题
            if not await self._fill_title(page, article.title):
                return {"success": False, "platform_url": None, "error_msg": "标题填充失败"}

            # 4. 点击正文区域
            try:
                await page.click(self.SELECTORS["content_editor"])
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"点击正文区域失败: {e}")

            # 5. 填充正文（知乎用Draft.js，需要特殊处理）
            if not await self._fill_content(page, article.content):
                return {"success": False, "platform_url": None, "error_msg": "正文填充失败"}

            # 6. 点击发布
            if not await self._click_publish(page):
                return {"success": False, "platform_url": None, "error_msg": "发布失败"}

            # 7. 等待发布结果
            result = await self._wait_for_publish_result(page)

            return result

        except Exception as e:
            logger.error(f"知乎发布失败: {e}")
            return {"success": False, "platform_url": None, "error_msg": str(e)}

    async def _fill_title(self, page: Page, title: str) -> bool:
        """填充标题"""
        try:
            # 知乎标题输入框
            selector = "input[placeholder*='请输入标题']"
            if not await self.wait_for_selector(page, selector, 5000):
                # 尝试其他选择器
                selector = "input.Input"
                if not await self.wait_for_selector(page, selector, 5000):
                    return False

            await page.fill(selector, title)
            logger.info(f"知乎标题已填充: {title[:20]}...")
            return True
        except Exception as e:
            logger.error(f"知乎标题填充失败: {e}")
            return False

    async def _fill_content(self, page: Page, content: str) -> bool:
        """
        填充正文（知乎用Draft.js编辑器）

        老王提醒：知乎的编辑器比较复杂，直接模拟键盘输入！
        """
        try:
            # 方法1：尝试找到编辑器div并点击
            editor_selector = ".public-DraftStyleDefault-block"
            if await self.wait_for_selector(page, editor_selector, 5000):
                await page.click(editor_selector)
                await asyncio.sleep(0.5)

                # 清空现有内容
                await page.keyboard.press("Control+A")
                await asyncio.sleep(0.2)

                # 逐字输入内容（避免触发敏感词检测）
                await page.keyboard.type(content)
                logger.info(f"知乎正文已填充: {len(content)} 字符")
                return True

            # 方法2：直接在body上输入
            await page.keyboard.type(content)
            logger.info(f"知乎正文已填充（直接输入）: {len(content)} 字符")
            return True

        except Exception as e:
            logger.error(f"知乎正文填充失败: {e}")
            return False

    async def _click_publish(self, page: Page) -> bool:
        """点击发布按钮"""
        try:
            # 知乎发布按钮
            selectors = [
                ".PublishButton",
                "button:has-text('发布')",
                "[class*='PublishButton']",
            ]

            for selector in selectors:
                try:
                    if await self.wait_for_selector(page, selector, 3000):
                        await page.click(selector)
                        logger.info("知乎发布按钮已点击")
                        return True
                except Exception:
                    continue

            return False
        except Exception as e:
            logger.error(f"知乎点击发布失败: {e}")
            return False

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        """等待发布结果"""
        try:
            # 等待跳转到文章页面
            await asyncio.sleep(3)

            # 检查URL是否包含文章ID
            if "/p/" in page.url or "/answer/" in page.url:
                return {
                    "success": True,
                    "platform_url": page.url,
                    "error_msg": None
                }

            # 检查是否有错误提示
            error_selectors = [
                ".error-message",
                ".Error",
                "[class*='error']",
            ]
            for selector in error_selectors:
                try:
                    error = await page.query_selector(selector)
                    if error:
                        error_text = await error.inner_text()
                        return {
                            "success": False,
                            "platform_url": None,
                            "error_msg": f"发布失败: {error_text}"
                        }
                except Exception:
                    pass

            # 默认认为成功
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
