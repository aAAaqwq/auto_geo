# -*- coding: utf-8 -*-
"""
GEO文章API
写的GEO文章API，包含生成和质检！
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.geo_article_service import GeoArticleService
from backend.database.models import GeoArticle, Keyword, User
from backend.schemas import ApiResponse
from loguru import logger
from backend.services.auth import get_current_user, is_admin


router = APIRouter(prefix="/api/geo", tags=["GEO文章"])


# ==================== 请求/响应模型 ====================

class GenerateArticleRequest(BaseModel):
    """生成文章请求"""
    keyword_id: int
    company_name: str
    platform: str = "zhihu"


class ArticleResponse(BaseModel):
    """文章响应"""
    id: int
    keyword_id: int
    title: Optional[str]
    content: str
    quality_score: Optional[int]
    ai_score: Optional[int]
    readability_score: Optional[int]
    quality_status: str
    platform: Optional[str]
    publish_status: str
    created_at: str

    class Config:
        from_attributes = True


class QualityCheckResponse(BaseModel):
    """质检响应"""
    article_id: int
    quality_score: Optional[int]
    ai_score: Optional[int]
    readability_score: Optional[int]
    quality_status: str


# ==================== 文章生成API ====================

@router.post("/generate", response_model=ApiResponse)
async def generate_article(
    request: GenerateArticleRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    生成文章

    调用n8n工作流基于关键词生成SEO优化文章。
    注意：这是AI驱动的核心功能！
    """
    keyword_query = db.query(Keyword).filter(Keyword.id == request.keyword_id)
    if not is_admin(current_user):
        keyword_query = keyword_query.filter(Keyword.owner_id == current_user.id)
    keyword = keyword_query.first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = GeoArticleService(db)
    result = await service.generate(
        keyword_id=request.keyword_id,
        company_name=request.company_name,
        platform=request.platform
    )

    if result.get("status") == "error":
        return ApiResponse(success=False, message=result.get("message", "生成失败"))

    return ApiResponse(
        success=True,
        message="文章生成成功",
        data={
            "article_id": result.get("article_id"),
            "title": result.get("title"),
            "content": result.get("content")
        }
    )


@router.post("/articles/{article_id}/check-quality", response_model=ApiResponse)
async def check_quality(
    article_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    质检文章

    调用n8n工作流检测文章的AI味和质量。
    注意：分数越高表示越像AI写的！
    """
    query = db.query(GeoArticle).filter(GeoArticle.id == article_id)
    if not is_admin(current_user):
        query = query.filter(GeoArticle.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    service = GeoArticleService(db)
    result = await service.check_quality(article_id)

    if result.get("status") == "error":
        return ApiResponse(success=False, message=result.get("message", "质检失败"))

    return ApiResponse(
        success=True,
        message="质检完成",
        data=result
    )


@router.get("/articles/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取文章详情"""
    query = db.query(GeoArticle).filter(GeoArticle.id == article_id)
    if not is_admin(current_user):
        query = query.filter(GeoArticle.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")
    return article


@router.get("/keywords/{keyword_id}/articles", response_model=List[ArticleResponse])
async def get_keyword_articles(keyword_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    获取关键词的所有文章

    注意：返回值按创建时间倒序！
    """
    keyword_query = db.query(Keyword).filter(Keyword.id == keyword_id)
    if not is_admin(current_user):
        keyword_query = keyword_query.filter(Keyword.owner_id == current_user.id)
    keyword = keyword_query.first()
    if not keyword:
        raise HTTPException(status_code=404, detail="关键词不存在")

    service = GeoArticleService(db)
    articles = service.get_keyword_articles(keyword_id)
    return articles


@router.put("/articles/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    title: Optional[str] = None,
    content: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新文章

    注意：更新后需要重新质检！
    """
    query = db.query(GeoArticle).filter(GeoArticle.id == article_id)
    if not is_admin(current_user):
        query = query.filter(GeoArticle.owner_id == current_user.id)
    existing = query.first()
    if not existing:
        raise HTTPException(status_code=404, detail="文章不存在")

    service = GeoArticleService(db)
    article = service.update_article(article_id, title, content)
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 重置质检状态
    article.quality_status = "pending"
    db.commit()

    return article


@router.delete("/articles/{article_id}", response_model=ApiResponse)
async def delete_article(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    删除文章

    注意：删除会级联删除相关数据！
    """
    query = db.query(GeoArticle).filter(GeoArticle.id == article_id)
    if not is_admin(current_user):
        query = query.filter(GeoArticle.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()

    logger.info(f"文章已删除: {article_id}")
    return ApiResponse(success=True, message="文章已删除")


@router.get("/articles", response_model=List[ArticleResponse])
async def list_articles(
    keyword_id: Optional[int] = Query(None, description="筛选关键词ID"),
    quality_status: Optional[str] = Query(None, description="质检状态筛选"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取文章列表

    注意：支持多维度筛选！
    """
    query = db.query(GeoArticle)

    if not is_admin(current_user):
        query = query.filter(GeoArticle.owner_id == current_user.id)
    if keyword_id:
        query = query.filter(GeoArticle.keyword_id == keyword_id)
    if quality_status:
        query = query.filter(GeoArticle.quality_status == quality_status)

    articles = query.order_by(GeoArticle.created_at.desc()).limit(limit).all()
    return articles
