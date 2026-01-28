# -*- coding: utf-8 -*-
"""
微信公众号发布适配器
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher


class WechatPublisher(BasePublisher):
    """
    微信公众号发布适配器

    发布页面：https://mp.weixin.qq.com/cgi-bin/appmsg?t=media/appmsg_edit&action=edit&type=77
    """

    async def publish(self, page: Page, article: Any, account: Any) -> Dict[str, Any]:
        """发布文章到微信公众号"""
        try:
            # 1. 导航到发布页面
            if not await self.navigate_to_publish_page(page):
                return {"success": False, "platform_url": None, "error_msg": "导航失败"}

            # 2. 等待编辑器加载
            await asyncio.sleep(5)

            # 3. 填充标题
            if not await self._fill_title(page, article.title):
                return {"success": False, "platform_url": None, "error_msg": "标题填充失败"}

            # 4. 填充正文
            if not await self._fill_content(page, article.content):
                return {"success": False, "platform_url": None, "error_msg": "正文填充失败"}

            # 5. 点击发布（微信公众号通常需要预览或合规检查，这里仅做初步点击）
            # 注意：微信发布流程复杂，可能需要处理扫码确认等逻辑
            logger.info("微信公众号初步填充完成，由于微信发布需扫码确认，建议手动完成最后一步")
            
            return {
                "success": True,
                "platform_url": page.url,
                "message": "内容已填充，请在浏览器中手动完成扫码发布确认"
            }

        except Exception as e:
            logger.error(f"微信公众号发布失败: {e}")
            return {"success": False, "platform_url": None, "error_msg": str(e)}

    async def _fill_title(self, page: Page, title: str) -> bool:
        """填充标题"""
        try:
            selector = "#title"
            if await self.wait_for_selector(page, selector, 5000):
                await page.fill(selector, title)
                logger.info(f"微信公众号标题已填充: {title[:20]}...")
                return True
            return False
        except Exception as e:
            logger.error(f"微信公众号标题填充失败: {e}")
            return False

    async def _fill_content(self, page: Page, content: str) -> bool:
        """填充正文"""
        try:
            # 微信使用自定义编辑器
            selector = "#js_editor"
            if await self.wait_for_selector(page, selector, 5000):
                # 微信编辑器通常需要通过 evaluate 注入或模拟输入
                await page.evaluate(f"""
                    (content) => {{
                        const editor = document.getElementById('js_editor');
                        if (editor) {{
                            editor.innerHTML = content;
                        }}
                    }}
                """, content)
                logger.info(f"微信公众号正文已填充: {len(content)} 字符")
                return True
            return False
        except Exception as e:
            logger.error(f"微信公众号正文填充失败: {e}")
            return False
