# -*- coding: utf-8 -*-
"""
文章管理API
写的文章API，简单明了！
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import Article, User
from backend.schemas import ArticleCreate, ArticleUpdate, ArticleResponse, ArticleListResponse, ApiResponse
from loguru import logger
from backend.services.auth import get_current_user, is_admin
from sqlalchemy import func


router = APIRouter(prefix="/api/articles", tags=["文章管理"])


@router.get("", response_model=ArticleListResponse)
async def get_articles(
    page: int = Query(1, ge=1, description="页码"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[int] = Query(None, description="状态筛选"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取文章列表

    注意：支持分页、状态筛选、关键词搜索！
    """
    query = db.query(Article)

    if not is_admin(current_user):
        query = query.filter(Article.owner_id == current_user.id)
    if status is not None:
        query = query.filter(Article.status == status)

    if keyword:
        query = query.filter(
            (Article.title.contains(keyword)) |
            (Article.content.contains(keyword))
        )

    # 统计总数
    total = query.count()

    # 分页查询
    articles = query.order_by(Article.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    return ArticleListResponse(total=total, items=articles)


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """获取文章详情"""
    query = db.query(Article).filter(Article.id == article_id)
    if not is_admin(current_user):
        query = query.filter(Article.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 增加查看次数
    article.view_count += 1
    db.commit()

    return article


@router.post("", response_model=ArticleResponse, status_code=201)
async def create_article(article_data: ArticleCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    创建文章

    注意：初始状态为草稿！
    """
    article = Article(
        owner_id=current_user.id,
        title=article_data.title,
        content=article_data.content,
        tags=article_data.tags,
        category=article_data.category,
        cover_image=article_data.cover_image,
        status=0  # 草稿状态
    )
    db.add(article)
    db.commit()
    db.refresh(article)

    logger.info(f"文章已创建: {article.id} - {article.title}")
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_data: ArticleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """更新文章"""
    query = db.query(Article).filter(Article.id == article_id)
    if not is_admin(current_user):
        query = query.filter(Article.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    # 更新字段
    if article_data.title is not None:
        article.title = article_data.title
    if article_data.content is not None:
        article.content = article_data.content
    if article_data.tags is not None:
        article.tags = article_data.tags
    if article_data.category is not None:
        article.category = article_data.category
    if article_data.cover_image is not None:
        article.cover_image = article_data.cover_image
    if article_data.status is not None:
        article.status = article_data.status
        if article_data.status == 1 and not article.published_at:
            article.published_at = func.now()

    db.commit()
    db.refresh(article)

    logger.info(f"文章已更新: {article_id}")
    return article


@router.delete("/{article_id}", response_model=ApiResponse)
async def delete_article(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    删除文章

    注意：删除会级联删除相关的发布记录！
    """
    query = db.query(Article).filter(Article.id == article_id)
    if not is_admin(current_user):
        query = query.filter(Article.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    db.delete(article)
    db.commit()

    logger.info(f"文章已删除: {article_id}")
    return ApiResponse(success=True, message="文章已删除")


@router.post("/{article_id}/publish", response_model=ApiResponse)
async def mark_published(article_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """标记文章为已发布"""
    query = db.query(Article).filter(Article.id == article_id)
    if not is_admin(current_user):
        query = query.filter(Article.owner_id == current_user.id)
    article = query.first()
    if not article:
        raise HTTPException(status_code=404, detail="文章不存在")

    article.status = 1
    if not article.published_at:
        article.published_at = func.now()
    db.commit()

    return ApiResponse(success=True, message="文章已标记为已发布")
