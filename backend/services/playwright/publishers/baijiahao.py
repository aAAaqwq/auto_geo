# -*- coding: utf-8 -*-
"""
百家号发布适配器
老王我对百家号的页面结构也有研究！
"""

import asyncio
from typing import Dict, Any
from playwright.async_api import Page
from loguru import logger

from .base import BasePublisher


class BaijiahaoPublisher(BasePublisher):
    """
    百家号发布适配器

    发布页面：https://baijiahao.baidu.com/builder/rc/edit/index

    老王提醒：百家号页面是React SPA，需要等待DOM加载完成！
    """

    async def publish(self, page: Page, article: Any, account: Any) -> Dict[str, Any]:
        """
        发布文章到百家号
        """
        try:
            logger.info(f"[百家号] 开始发布文章: {article.title}")

            # 1. 导航到发布页面
            if not await self.navigate_to_publish_page(page):
                return {"success": False, "platform_url": None, "error_msg": "导航失败"}

            # 2. 等待页面完全加载（百家号是React SPA，需要更长时间）
            logger.info("[百家号] 等待页面加载...")
            await asyncio.sleep(5)

            # 等待关键DOM元素出现
            try:
                await page.wait_for_selector("body", timeout=10000)
                await page.wait_for_load_state("domcontentloaded", timeout=10000)
            except Exception as e:
                logger.warning(f"[百家号] 页面加载超时，继续尝试: {e}")

            # 3. 填充标题
            logger.info("[百家号] 开始填充标题...")
            title_result = await self._fill_title(page, article.title)
            if not title_result:
                # 即使失败也继续，可能是选择器问题
                logger.warning("[百家号] 标题填充可能失败，继续尝试发布")

            # 4. 等待一下
            await asyncio.sleep(1)

            # 5. 填充正文
            logger.info("[百家号] 开始填充正文...")
            content_result = await self._fill_content(page, article.content)
            if not content_result:
                return {"success": False, "platform_url": None, "error_msg": "正文填充失败"}

            # 6. 再等待一下确保内容加载
            await asyncio.sleep(2)

            # 7. 点击发布
            logger.info("[百家号] 点击发布按钮...")
            publish_result = await self._click_publish(page)
            if not publish_result:
                return {"success": False, "platform_url": None, "error_msg": "发布按钮未找到或点击失败"}

            # 8. 等待发布结果
            logger.info("[百家号] 等待发布结果...")
            result = await self._wait_for_publish_result(page)

            return result

        except Exception as e:
            logger.error(f"[百家号] 发布异常: {e}")
            return {"success": False, "platform_url": None, "error_msg": str(e)}

    async def _fill_title(self, page: Page, title: str) -> bool:
        """填充标题"""
        try:
            logger.info(f"[百家号] 尝试填充标题: {title}")

            # 百家号标题输入框选择器（多种可能）
            selectors = [
                # React组件可能的class
                "input[placeholder*='请输入标题']",
                "input[placeholder*='标题']",
                "input[class*='title']",
                "input[class*='Title']",
                ".title-input",
                ".article-title",
                # 尝试通过text定位
                "input[type='text']",
            ]

            for selector in selectors:
                try:
                    logger.info(f"[百家号] 尝试选择器: {selector}")
                    # 先检查选择器是否存在
                    element = await page.query_selector(selector)
                    if element:
                        # 检查元素是否可见
                        is_visible = await element.is_visible()
                        if is_visible:
                            # 点击输入框激活
                            await element.click()
                            await asyncio.sleep(0.3)

                            # 清空并填充
                            await page.fill(selector, "")
                            await asyncio.sleep(0.2)
                            await page.fill(selector, title)
                            await asyncio.sleep(0.5)

                            # 验证是否填充成功
                            value = await element.input_value()
                            if title in value:
                                logger.info(f"[百家号] 标题填充成功: {title[:20]}...")
                                return True
                            else:
                                logger.warning(f"[百家号] 标题填充后验证失败")
                except Exception as e:
                    logger.debug(f"[百家号] 选择器 {selector} 失败: {e}")
                    continue

            # 尝试通过JavaScript直接填充
            logger.info("[百家号] 尝试通过JavaScript填充标题")
            try:
                result = await page.evaluate(f"""() => {{
                    // 查找所有input
                    const inputs = document.querySelectorAll('input[type="text"], input:not([type])');
                    for (let input of inputs) {{
                        const placeholder = input.placeholder || '';
                        const className = input.className || '';
                        if (placeholder.includes('标题') || className.includes('title') || className.includes('Title')) {{
                            input.click();
                            input.value = '';
                            input.value = '{title}';
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}""")
                if result:
                    logger.info(f"[百家号] JavaScript填充标题成功")
                    return True
            except Exception as e:
                logger.debug(f"[百家号] JavaScript填充标题失败: {e}")

            logger.warning("[百家号] 所有标题填充方法都失败")
            return False

        except Exception as e:
            logger.error(f"[百家号] 标题填充异常: {e}")
            return False

    async def _fill_content(self, page: Page, content: str) -> bool:
        """填充正文"""
        try:
            logger.info(f"[百家号] 开始填充正文，长度: {len(content)}")

            # 百家号编辑器选择器（多种可能）
            selectors = [
                # contenteditable 编辑器
                "[contenteditable='true']",
                ".editor-body",
                "[class*='editor-body']",
                "[class*='EditorBody']",
                "[class*='content-edit']",
                ".ueditor-body",
                "div[role='textbox']",
                "[class*='DraftEditor']",
            ]

            for selector in selectors:
                try:
                    logger.info(f"[百家号] 尝试编辑器选择器: {selector}")

                    # 等待元素出现
                    try:
                        await page.wait_for_selector(selector, timeout=5000)
                    except:
                        continue

                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            # 检查元素是否可见
                            is_visible = await element.is_visible()
                            if not is_visible:
                                continue

                            # 点击编辑器激活
                            await element.click()
                            await asyncio.sleep(0.5)

                            # 清空现有内容
                            await page.keyboard.press("Control+A")
                            await asyncio.sleep(0.2)
                            await page.keyboard.press("Backspace")
                            await asyncio.sleep(0.2)

                            # 分段输入内容（避免一次性输入过长）
                            chunk_size = 500
                            for i in range(0, len(content), chunk_size):
                                chunk = content[i:i+chunk_size]
                                await page.keyboard.type(chunk)
                                await asyncio.sleep(0.1)

                            await asyncio.sleep(0.5)
                            logger.info(f"[百家号] 正文填充成功，长度: {len(content)}")
                            return True

                        except Exception as e:
                            logger.debug(f"[百家号] 元素填充失败: {e}")
                            continue

                except Exception as e:
                    logger.debug(f"[百家号] 选择器 {selector} 失败: {e}")
                    continue

            # 尝试通过JavaScript直接填充
            logger.info("[百家号] 尝试通过JavaScript填充正文")
            try:
                # 转义内容中的特殊字符
                escaped_content = content.replace('\\', '\\\\').replace("'", "\\'").replace('\n', '\\n').replace('\r', '')
                result = await page.evaluate(f"""() => {{
                    // 查找contenteditable元素
                    const editables = document.querySelectorAll('[contenteditable="true"]');
                    for (let el of editables) {{
                        if (el.offsetParent !== null) {{ // 可见
                            el.click();
                            el.focus();
                            el.textContent = '';
                            el.textContent = `{escaped_content}`;
                            el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            el.dispatchEvent(new Event('change', {{ bubbles: true }}'));
                            return true;
                        }}
                    }}
                    return false;
                }}""")
                if result:
                    logger.info("[百家号] JavaScript填充正文成功")
                    return True
            except Exception as e:
                logger.debug(f"[百家号] JavaScript填充正文失败: {e}")

            logger.warning("[百家号] 所有正文填充方法都失败")
            return False

        except Exception as e:
            logger.error(f"[百家号] 正文填充异常: {e}")
            return False

    async def _click_publish(self, page: Page) -> bool:
        """点击发布按钮"""
        try:
            logger.info("[百家号] 开始查找发布按钮")

            # 百家号发布按钮选择器
            selectors = [
                # 通过文本内容查找
                "button:has-text('发布')",
                "span:has-text('发布')",
                "div:has-text('发布')",
                # 通过class查找
                ".submit-btn",
                "[class*='submit']",
                "[class*='publish']",
                "[class*='Publish']",
                ".ant-btn-primary",
                "button[type='submit']",
                "button[class*='btn']",
            ]

            for selector in selectors:
                try:
                    logger.info(f"[百家号] 尝试按钮选择器: {selector}")

                    try:
                        await page.wait_for_selector(selector, timeout=3000)
                    except:
                        continue

                    elements = await page.query_selector_all(selector)
                    for element in elements:
                        try:
                            # 检查元素是否可见
                            is_visible = await element.is_visible()
                            if not is_visible:
                                continue

                            # 获取按钮文本确认
                            text = await element.text_content()
                            if text and '发布' in text:
                                await element.click()
                                await asyncio.sleep(0.5)
                                logger.info("[百家号] 发布按钮已点击")
                                return True
                        except Exception as e:
                            logger.debug(f"[百家号] 按钮点击失败: {e}")
                            continue

                except Exception as e:
                    logger.debug(f"[百家号] 选择器 {selector} 失败: {e}")
                    continue

            # 尝试通过JavaScript点击
            logger.info("[百家号] 尝试通过JavaScript点击发布按钮")
            try:
                result = await page.evaluate("""() => {
                    // 查找包含"发布"文本的按钮
                    const buttons = document.querySelectorAll('button, span[class], div[class]');
                    for (let btn of buttons) {
                        const text = btn.textContent || '';
                        if (text.includes('发布') && btn.offsetParent !== null) {
                            btn.click();
                            return true;
                        }
                    }
                    return false;
                }""")
                if result:
                    logger.info("[百家号] JavaScript点击发布按钮成功")
                    return True
            except Exception as e:
                logger.debug(f"[百家号] JavaScript点击失败: {e}")

            logger.warning("[百家号] 所有发布按钮查找方法都失败")
            return False

        except Exception as e:
            logger.error(f"[百家号] 点击发布按钮异常: {e}")
            return False

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        """等待发布结果"""
        try:
            logger.info("[百家号] 等待发布结果...")

            # 等待一段时间让页面响应
            await asyncio.sleep(5)

            # 检查当前URL
            current_url = page.url
            logger.info(f"[百家号] 当前URL: {current_url}")

            # 检查是否有成功提示
            try:
                # 检查是否有成功消息
                success_selectors = [
                    ".success-message",
                    "[class*='success']",
                    "text=发布成功",
                    "text=提交成功",
                ]
                for selector in success_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                logger.info("[百家号] 检测到发布成功提示")
                                return {
                                    "success": True,
                                    "platform_url": current_url,
                                    "error_msg": None
                                }
                    except:
                        continue
            except Exception as e:
                logger.debug(f"[百家号] 检查成功提示失败: {e}")

            # 检查是否有错误提示
            try:
                error_selectors = [
                    ".error-message",
                    "[class*='error']",
                    "text=失败",
                    "text=错误",
                ]
                for selector in error_selectors:
                    try:
                        element = await page.query_selector(selector)
                        if element:
                            is_visible = await element.is_visible()
                            if is_visible:
                                error_text = await element.text_content()
                                logger.warning(f"[百家号] 检测到错误提示: {error_text}")
                                return {
                                    "success": False,
                                    "platform_url": None,
                                    "error_msg": error_text or "发布失败"
                                }
                    except:
                        continue
            except Exception as e:
                logger.debug(f"[百家号] 检查错误提示失败: {e}")

            # 默认返回成功（假设已发布）
            logger.info("[百家号] 发布完成（无明确错误）")
            return {
                "success": True,
                "platform_url": current_url,
                "error_msg": None
            }

        except Exception as e:
            logger.error(f"[百家号] 等待发布结果异常: {e}")
            return {
                "success": False,
                "platform_url": None,
                "error_msg": f"等待结果失败: {str(e)}"
            }
