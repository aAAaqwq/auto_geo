# -*- coding: utf-8 -*-
"""
GEO文章生成服务
用这个来处理AI文章生成和质检！
"""

from typing import Any, Dict, Optional
from loguru import logger
from sqlalchemy.orm import Session

from backend.database.models import GeoArticle, Keyword
from backend.services.n8n_client import get_n8n_client


class GeoArticleService:
    """
    GEO文章服务

    注意：这个服务负责与n8n交互完成文章生成！
    """

    def __init__(self, db: Session):
        """
        初始化文章服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.n8n = get_n8n_client()

    async def generate(
        self,
        keyword_id: int,
        company_name: str,
        platform: str = "zhihu"
    ) -> Dict[str, Any]:
        """
        生成文章

        Args:
            keyword_id: 关键词ID
            company_name: 公司名称
            platform: 目标发布平台

        Returns:
            生成结果
        """
        # 获取关键词
        keyword_obj = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword_obj:
            return {"status": "error", "message": "关键词不存在"}

        logger.info(f"开始生成文章: {keyword_obj.keyword} - {platform}")

        # 调用n8n工作流生成文章
        result = await self.n8n.call("generate-article", {
            "keyword": keyword_obj.keyword,
            "company_name": company_name,
            "platform": platform
        })

        if result.get("status") == "error":
            logger.error(f"文章生成失败: {result.get('message')}")
            return {"status": "error", "message": result.get("message")}

        # 保存文章到数据库
        article = GeoArticle(
            owner_id=keyword_obj.owner_id,
            keyword_id=keyword_id,
            title=result.get("title"),
            content=result.get("content"),
            platform=platform,
            quality_status="pending"
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)

        logger.info(f"文章已生成: {article.id}")
        return {
            "status": "success",
            "article_id": article.id,
            "title": article.title,
            "content": article.content
        }

    async def check_quality(self, article_id: int) -> Dict[str, Any]:
        """
        质检文章

        Args:
            article_id: 文章ID

        Returns:
            质检结果
        """
        article = self.db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
        if not article:
            return {"status": "error", "message": "文章不存在"}

        logger.info(f"开始质检文章: {article_id}")

        # 调用n8n工作流质检
        result = await self.n8n.call("check-quality", {
            "content": article.content,
            "title": article.title or ""
        })

        if result.get("status") == "error":
            logger.error(f"质检失败: {result.get('message')}")
            return {"status": "error", "message": result.get("message")}

        # 更新质检结果
        article.quality_score = result.get("quality_score")
        article.ai_score = result.get("ai_score")
        article.readability_score = result.get("readability_score")

        # 判断是否通过质检
        if article.quality_score and article.quality_score >= 60:
            article.quality_status = "passed"
        else:
            article.quality_status = "failed"

        self.db.commit()

        logger.info(f"质检完成: {article_id} - {article.quality_status}")
        return {
            "status": "success",
            "quality_score": article.quality_score,
            "ai_score": article.ai_score,
            "readability_score": article.readability_score,
            "quality_status": article.quality_status
        }

    def get_article(self, article_id: int) -> Optional[GeoArticle]:
        """获取文章详情"""
        return self.db.query(GeoArticle).filter(GeoArticle.id == article_id).first()

    def get_keyword_articles(self, keyword_id: int) -> list[GeoArticle]:
        """获取关键词的所有文章"""
        return self.db.query(GeoArticle).filter(
            GeoArticle.keyword_id == keyword_id
        ).order_by(GeoArticle.created_at.desc()).all()

    def update_article(
        self,
        article_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[GeoArticle]:
        """更新文章"""
        article = self.db.query(GeoArticle).filter(GeoArticle.id == article_id).first()
        if not article:
            return None

        if title is not None:
            article.title = title
        if content is not None:
            article.content = content

        self.db.commit()
        self.db.refresh(article)
        return article
