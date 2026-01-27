# -*- coding: utf-8 -*-
"""
知乎文章收集适配器
爬取知乎热门文章！
"""

import asyncio
import re
from typing import Dict, Any, Optional, List
from playwright.async_api import Page
from loguru import logger

from .base import BaseCollector


class ZhihuCollector(BaseCollector):
    """
    知乎文章收集适配器

    搜索页面：https://www.zhihu.com/search?type=content&q={keyword}
    """

    SELECTORS = {
        "search_results": ".SearchResult-Card",
        "article_title": ".ContentItem-title a",
        "article_link": ".ContentItem-title a",
        "vote_count": ".VoteButton--up",
        "comment_count": ".ContentItem-actions button:has-text('评论')",
        "author": ".AuthorInfo-name",
        "content_body": ".Post-RichText, .RichContent-inner",
    }

    async def search(self, page: Page, keyword: str) -> List[Dict[str, Any]]:
        """搜索知乎文章"""
        try:
            # 1. 导航到搜索页
            search_url = f"https://www.zhihu.com/search?type=content&q={keyword}"
            await page.goto(search_url, wait_until="networkidle")
            
            # 增加延时，等待页面加载和可能的弹窗
            await self._random_sleep(3, 5)

            # 检测登录弹窗
            await self._handle_login_popup(page)
            
            logger.info(f"[知乎] 已导航到搜索页: {keyword}")

            # 2. 滚动加载更多结果
            await self._human_scroll(page)

            # 3. 提取搜索结果
            articles = await self._extract_search_results(page)

            return articles

        except Exception as e:
            logger.error(f"[知乎] 搜索失败: {e}")
            return []

    async def _extract_search_results(self, page: Page) -> List[Dict[str, Any]]:
        """提取搜索结果"""
        articles = []

        try:
            # 获取所有搜索结果卡片
            cards = await page.query_selector_all(".SearchResult-Card, .Card.SearchResult-Card")

            for card in cards:
                try:
                    # 提取标题和链接
                    title_elem = await card.query_selector("h2.ContentItem-title a, .ContentItem-title a")
                    if not title_elem:
                        continue

                    title = await title_elem.text_content()
                    href = await title_elem.get_attribute("href")

                    # 处理相对链接
                    if href and not href.startswith("http"):
                        href = f"https://www.zhihu.com{href}"

                    # 提取点赞数
                    likes = 0
                    vote_elem = await card.query_selector(".VoteButton--up, [class*='VoteButton']")
                    if vote_elem:
                        vote_text = await vote_elem.text_content()
                        likes = self._parse_number(vote_text)

                    # 提取评论数
                    comments = 0
                    comment_elem = await card.query_selector("button:has-text('评论'), [class*='comment']")
                    if comment_elem:
                        comment_text = await comment_elem.text_content()
                        comments = self._parse_number(comment_text)

                    # 提取作者
                    author = ""
                    author_elem = await card.query_selector(".AuthorInfo-name, .UserLink-link")
                    if author_elem:
                        author = await author_elem.text_content()

                    if title and href:
                        articles.append({
                            "title": title.strip(),
                            "url": href,
                            "likes": likes,
                            "reads": likes * 50,  # 知乎没有直接显示阅读量，用点赞估算
                            "comments": comments,
                            "author": author.strip() if author else "",
                        })

                except Exception as e:
                    logger.debug(f"[知乎] 提取单条结果失败: {e}")
                    continue

        except Exception as e:
            logger.error(f"[知乎] 提取搜索结果失败: {e}")

        return articles

    async def extract_content(self, page: Page, url: str) -> Optional[str]:
        """提取文章正文"""
        try:
            await page.goto(url, wait_until="networkidle")
            
            # 增加延时，等待页面加载
            await self._random_sleep(3, 5)

            # 检测登录弹窗
            await self._handle_login_popup(page)
            
            # 尝试多种选择器
            selectors = [
                ".Post-RichText",
                ".RichContent-inner",
                ".RichText",
                "article",
                ".ContentItem-content",
            ]

            for selector in selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        content = await elem.text_content()
                        if content and len(content) > 100:
                            logger.info(f"[知乎] 提取正文成功: {len(content)} 字符")
                            return content.strip()
                except Exception:
                    continue

            logger.warning(f"[知乎] 未能提取正文: {url}")
            return None

        except Exception as e:
            logger.error(f"[知乎] 提取正文失败: {e}")
            return None

    def _parse_number(self, text: str) -> int:
        """解析数字（支持 1.2k, 1.5w 等格式）"""
        if not text:
            return 0

        text = text.strip().lower()

        # 移除非数字字符但保留k、w、万
        match = re.search(r'([\d.]+)\s*([kwm万])?', text)
        if not match:
            return 0

        num = float(match.group(1))
        unit = match.group(2)

        if unit in ['k', 'K']:
            num *= 1000
        elif unit in ['w', 'W', '万']:
            num *= 10000
        elif unit in ['m', 'M']:
            num *= 1000000

        return int(num)
