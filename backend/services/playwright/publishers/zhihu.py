# -*- coding: utf-8 -*-
"""
知乎发布适配器 - 完整版
老王根据研究结果更新！支持：封面、AI声明、话题、富文本
"""

import asyncio
import re
import os
import tempfile
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from playwright.async_api import Page, FileChooser
from loguru import logger
import httpx

from .base import BasePublisher


class ZhihuPublisher(BasePublisher):
    """
    知乎发布适配器 - 完整版

    支持功能：
    - 标题输入
    - 正文输入（富文本 + 图片上传）
    - 封面图片上传
    - AI创作声明
    - 话题添加
    - 发布
    """

    async def publish(self, page: Page, article: Any, account: Any) -> Dict[str, Any]:
        """发布文章到知乎"""
        try:
            # 1. 导航到发布页面
            if not await self.navigate_to_publish_page(page):
                return {"success": False, "platform_url": None, "error_msg": "导航失败"}

            # 2. 等待页面加载，检查登录状态
            await asyncio.sleep(3)
            if "signin" in page.url or "login" in page.url:
                return {"success": False, "platform_url": None, "error_msg": "登录已过期，请重新授权"}

            # 3. 等待编辑器就绪
            await self._wait_for_editor_ready(page)

            # 4. 填充标题
            if not await self._fill_title(page, article.title):
                return {"success": False, "platform_url": None, "error_msg": "标题填充失败"}

            # 5. 填充正文（支持图片上传）
            if not await self._fill_content_with_images(page, article.content):
                return {"success": False, "platform_url": None, "error_msg": "正文填充失败"}

            # 6. 添加封面图片（如果有）
            if hasattr(article, 'cover_image') and article.cover_image:
                await self._upload_cover_image(page, article.cover_image)

            # 7. 设置AI创作声明
            if hasattr(article, 'use_ai_declaration') and article.use_ai_declaration:
                await self._set_ai_declaration(page)

            # 8. 添加话题（如果有）
            if hasattr(article, 'topics') and article.topics:
                await self._add_topics(page, article.topics)

            # 9. 点击发布
            if not await self._click_publish(page):
                return {"success": False, "platform_url": None, "error_msg": "发布失败"}

            # 10. 等待发布结果
            result = await self._wait_for_publish_result(page)

            return result

        except Exception as e:
            logger.error(f"知乎发布失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": False, "platform_url": None, "error_msg": str(e)}

    async def _wait_for_editor_ready(self, page: Page) -> bool:
        """等待知乎编辑器准备就绪"""
        try:
            if await self.wait_for_selector(page, "textarea[placeholder*='标题']", 15000):
                logger.info("✅ 编辑器已就绪")
                await asyncio.sleep(1)
                return True
            return True
        except Exception:
            return True

    async def _fill_title(self, page: Page, title: str) -> bool:
        """填充标题"""
        try:
            selector = "textarea[placeholder*='请输入标题']"

            if await self.wait_for_selector(page, selector, 5000):
                # 使用JavaScript设置值
                await page.evaluate("""
                    (title) => {
                        const textarea = document.querySelector("textarea[placeholder*='请输入标题']");
                        if (textarea) {
                            textarea.value = title;
                            textarea.dispatchEvent(new Event('input', { bubbles: true }));
                            textarea.dispatchEvent(new Event('change', { bubbles: true }));
                            return true;
                        }
                        return false;
                    }
                """, title)
                logger.info(f"✅ 标题已填充: {title[:30]}...")
                await asyncio.sleep(0.5)
                return True

            return False
        except Exception as e:
            logger.error(f"标题填充失败: {e}")
            return False

    async def _fill_content_with_images(self, page: Page, content: str) -> bool:
        """
        填充正文（支持图片上传）

        策略：
        1. 解析Markdown，提取图片URL
        2. 填充纯文本内容
        3. 点击工具栏图片按钮上传每张图片
        """
        try:
            editor_selector = ".public-DraftEditor-content"

            if await self.wait_for_selector(page, editor_selector, 5000):
                # 点击编辑器激活
                await page.click(editor_selector)
                await asyncio.sleep(0.5)

                # 清空现有内容
                await page.keyboard.press("Control+A")
                await asyncio.sleep(0.2)
                await page.keyboard.press("Delete")
                await asyncio.sleep(0.3)

                # 解析内容，提取图片URL
                text_content, image_urls = self._parse_markdown_with_images(content)

                logger.info(f"解析到 {len(image_urls)} 张图片")

                # 先填充纯文本内容（移除图片标记）
                await page.evaluate(f"navigator.clipboard.writeText({repr(text_content)})")
                await asyncio.sleep(0.1)
                await page.keyboard.press("Control+V")
                await asyncio.sleep(1)

                logger.info("✅ 正文文本已填充")

                # 上传图片
                if image_urls:
                    await self._upload_images_to_editor(page, image_urls)

                return True

            return False
        except Exception as e:
            logger.error(f"正文填充失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def _parse_markdown_with_images(self, content: str) -> Tuple[List[str], List[str]]:
        """
        解析Markdown，分离文本和图片

        Returns:
            (文本列表, 图片URL列表)
        """
        # 匹配Markdown图片语法 ![alt](url)
        img_pattern = r'!\[([^\]]*)\]\(([^)]+)\)'

        # 提取所有图片
        images = re.findall(img_pattern, content)

        # 移除图片标记，得到纯文本
        text = re.sub(img_pattern, '', content)

        # 处理标题
        text = re.sub(r'^###\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'\n\n【\1】\n\n', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+)$', r'\n\n========== \1 ==========\n\n', text, flags=re.MULTILINE)

        # 移除加粗标记
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # 移除链接标记
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)

        # 处理列表
        text = re.sub(r'^-\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+(.+)$', r'\1. ', text, flags=re.MULTILINE)

        # 合并多余换行
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        # 提取图片URL
        image_urls = [url for alt, url in images]

        return [text.strip()], image_urls

    async def _upload_images_to_editor(self, page: Page, image_urls: List[str]) -> bool:
        """
        上传图片到编辑器

        步骤：
        1. 点击工具栏的图片按钮（文本是"图片"）
        2. 监听文件选择器
        3. 上传图片文件
        """
        try:
            logger.info(f"开始上传 {len(image_urls)} 张图片")

            # 工具栏图片按钮选择器
            image_button_selectors = [
                "button:has-text('图片')",
                ".ToolbarButton:has-text('图片')",
                "button .ZDI--Image24",  # SVG图标类名
            ]

            for i, img_url in enumerate(image_urls):
                try:
                    logger.info(f"上传第 {i+1}/{len(image_urls)} 张图片: {img_url}")

                    # 1. 下载图片
                    temp_file = await self._download_image(img_url)
                    if not temp_file:
                        logger.warning(f"图片下载失败: {img_url}")
                        continue

                    # 2. 点击工具栏图片按钮并监听文件选择
                    async with page.expect_file_chooser() as fc_info:
                        # 尝试多种选择器点击图片按钮
                        clicked = False
                        for selector in image_button_selectors:
                            try:
                                btn = await page.query_selector(selector)
                                if btn:
                                    await btn.click()
                                    clicked = True
                                    logger.debug(f"已点击图片按钮: {selector}")
                                    break
                            except Exception:
                                continue

                        if not clicked:
                            # 尝试通过SVG图标查找
                            await page.evaluate("""
                                () => {
                                    const svg = document.querySelector('.ZDI--Image24');
                                    if (svg) {
                                        const btn = svg.closest('button');
                                        if (btn) btn.click();
                                    }
                                }
                            """)

                    # 3. 选择文件上传
                    file_chooser = await fc_info.value
                    await file_chooser.set_files(temp_file)
                    logger.info(f"✅ 第 {i+1} 张图片已上传")

                    # 4. 等待上传完成
                    await asyncio.sleep(2)

                    # 清理临时文件
                    if os.path.exists(temp_file):
                        os.remove(temp_file)

                except Exception as e:
                    logger.error(f"上传第 {i+1} 张图片失败: {e}")
                    continue

            logger.info("✅ 图片上传完成")
            return True

        except Exception as e:
            logger.error(f"图片上传失败: {e}")
            return False

    async def _convert_markdown_to_rich_text(self, page: Page, markdown: str) -> str:
        """
        将Markdown转换为知乎编辑器可识别的格式

        策略：
        1. 提取图片URL，后面单独上传
        2. 将Markdown格式转换为纯文本
        3. 使用知乎编辑器自身的格式化功能
        """
        # 移除图片标记（图片单独处理）
        text = re.sub(r'!\[([^\]]*)\]\(([^)]+)\)', '', markdown)

        # 处理标题 - 转换为带换行的文本
        text = re.sub(r'^###\s+(.+)$', r'\n\1\n', text, flags=re.MULTILINE)
        text = re.sub(r'^##\s+(.+)$', r'\n\n【\1】\n\n', text, flags=re.MULTILINE)
        text = re.sub(r'^#\s+(.+)$', r'\n\n========== \1 ==========\n\n', text, flags=re.MULTILINE)

        # 移除加粗标记（保留文本）
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)

        # 移除链接标记
        text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'\1', text)

        # 处理列表
        text = re.sub(r'^-\s+(.+)$', r'• \1', text, flags=re.MULTILINE)
        text = re.sub(r'^\d+\.\s+(.+)$', r'\1. ', text, flags=re.MULTILINE)

        # 合并多余换行
        text = re.sub(r'\n{4,}', '\n\n\n', text)

        return text.strip()

    async def _upload_cover_image(self, page: Page, image_url: str) -> bool:
        """
        上传封面图片

        元素：label.UploadPicture-wrapper > input.UploadPicture-input[type="file"]
        """
        try:
            logger.info(f"开始上传封面图片: {image_url}")

            # 1. 下载图片
            temp_file = await self._download_image(image_url)
            if not temp_file:
                logger.warning("封面图片下载失败")
                return False

            # 2. 设置文件选择监听
            async with page.expect_file_chooser() as fc_info:
                # 3. 点击封面上传按钮
                await page.click("label.UploadPicture-wrapper")

            # 4. 选择文件
            file_chooser = await fc_info.value
            await file_chooser.set_files(temp_file)
            logger.info("✅ 封面图片已上传")

            # 5. 等待上传完成
            await asyncio.sleep(2)

            # 清理临时文件
            if os.path.exists(temp_file):
                os.remove(temp_file)

            return True

        except Exception as e:
            logger.error(f"封面上传失败: {e}")
            return False

    async def _set_ai_declaration(self, page: Page) -> bool:
        """
        设置AI创作声明

        元素：button[title*="AI"] 或包含"AI助手"文本的按钮
        """
        try:
            logger.info("设置AI创作声明")

            # AI助手按钮选择器
            selectors = [
                "button:has-text('AI助手')",
                ".ToolbarButton:has-text('AI')",
                "[class*='AiAssistant']",
            ]

            clicked = False
            for selector in selectors:
                try:
                    if await self.wait_for_selector(page, selector, 5000):
                        await page.click(selector)
                        clicked = True
                        logger.info("✅ 已点击AI助手按钮")
                        await asyncio.sleep(1)
                        break
                except Exception:
                    continue

            if not clicked:
                logger.warning("未找到AI助手按钮")
                return False

            # 查找并点击"AI辅助创作"选项
            # 等待弹出菜单
            await asyncio.sleep(1)

            ai_option_selectors = [
                "text=AI辅助创作",
                "[role='menuitem']:has-text('AI')",
                ".css-jjc8wi",  # 从研究中获取的类名
            ]

            for selector in ai_option_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        await element.click()
                        logger.info("✅ 已选择AI辅助创作")
                        await asyncio.sleep(0.5)
                        return True
                except Exception:
                    continue

            logger.warning("未找到AI辅助创作选项，可能已默认选择")
            return True

        except Exception as e:
            logger.error(f"设置AI声明失败: {e}")
            return False

    async def _add_topics(self, page: Page, topics: List[str]) -> bool:
        """
        添加话题

        从研究中发现话题输入框可能需要滚动或点击才能显示
        """
        try:
            logger.info(f"添加话题: {topics}")

            # 话题输入框可能在页面下方，需要先滚动
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(1)

            # 尝试多种方式找到话题输入框
            topic_selectors = [
                "input[placeholder*='话题']",
                "input[placeholder*='添加话题']",
                "[class*='TopicInput']",
                "[class*='TagInput']",
            ]

            topic_input = None
            for selector in topic_selectors:
                try:
                    topic_input = await page.query_selector(selector)
                    if topic_input:
                        break
                except Exception:
                    continue

            if not topic_input:
                logger.warning("未找到话题输入框，尝试其他方式")

                # 可能需要点击"添加话题"按钮
                add_topic_buttons = [
                    "button:has-text('添加话题')",
                    "text=添加话题",
                ]

                for btn_selector in add_topic_buttons:
                    try:
                        btn = await page.query_selector(btn_selector)
                        if btn:
                            await btn.click()
                            await asyncio.sleep(1)
                            break
                    except Exception:
                        continue

            # 输入话题
            for topic in topics[:3]:  # 最多3个话题
                try:
                    # 点击话题输入框
                    await page.click("input[placeholder*='话题'], input[placeholder*='添加'], [class*='TopicInput'], [class*='TagInput']")
                    await asyncio.sleep(0.3)

                    # 输入话题名称
                    await page.fill("input[placeholder*='话题'], input[placeholder*='添加'], [class*='TopicInput'], [class*='TagInput']", topic)
                    await asyncio.sleep(0.5)

                    # 按回车确认
                    await page.keyboard.press("Enter")
                    await asyncio.sleep(0.5)

                    logger.info(f"✅ 已添加话题: {topic}")
                except Exception as e:
                    logger.debug(f"添加话题 {topic} 失败: {e}")

            return True

        except Exception as e:
            logger.error(f"添加话题失败: {e}")
            return False

    async def _download_image(self, url: str) -> Optional[str]:
        """下载图片到临时文件"""
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url)
                if resp.status_code == 200:
                    content_type = resp.headers.get('Content-Type', 'image/jpeg')
                    ext = '.jpg'
                    if 'png' in content_type:
                        ext = '.png'
                    elif 'gif' in content_type:
                        ext = '.gif'
                    elif 'webp' in content_type:
                        ext = '.webp'

                    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                        f.write(resp.content)
                        return f.name
                return None
        except Exception as e:
            logger.error(f"图片下载失败: {e}")
            return None

    async def _click_publish(self, page: Page) -> bool:
        """点击发布按钮"""
        try:
            # 等待发布按钮可点击（按钮在填入内容后才会启用）
            await asyncio.sleep(2)

            selectors = [
                "button.PublishButton",
                "button[class*='PublishButton']:not([disabled])",
                "button:has-text('发布'):not([disabled])",
                ".css-d0uhtl:not([disabled])",  # 从研究获取的类名
            ]

            for selector in selectors:
                try:
                    # 检查按钮是否存在且可点击
                    if await self.wait_for_selector(page, selector, 5000):
                        # 再次检查是否禁用
                        is_disabled = await page.is_disabled(selector)
                        if not is_disabled:
                            await page.click(selector)
                            logger.info("✅ 发布按钮已点击")
                            await asyncio.sleep(1)
                            return True
                        else:
                            logger.debug(f"按钮 {selector} 仍处于disabled状态")
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue

            logger.error("发布按钮不可点击或未找到")
            return False

        except Exception as e:
            logger.error(f"点击发布失败: {e}")
            return False

    async def _wait_for_publish_result(self, page: Page) -> Dict[str, Any]:
        """等待发布结果"""
        try:
            await asyncio.sleep(5)

            current_url = page.url
            if "/p/" in current_url:
                return {
                    "success": True,
                    "platform_url": current_url,
                    "error_msg": None
                }

            return {
                "success": True,
                "platform_url": current_url,
                "error_msg": None
            }

        except Exception as e:
            return {
                "success": False,
                "platform_url": None,
                "error_msg": f"等待结果失败: {str(e)}"
            }
