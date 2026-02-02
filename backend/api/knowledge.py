# -*- coding: utf-8 -*-
"""
知识库管理API
管理企业知识库分类和知识条目
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.database.models import KnowledgeCategory, Knowledge, User, Project
from backend.schemas import ApiResponse
from loguru import logger
from backend.services.auth import get_current_user, is_admin


router = APIRouter(prefix="/api/knowledge", tags=["知识库管理"])


# ==================== 请求/响应模型 ====================

class KnowledgeCategoryCreate(BaseModel):
    """创建知识库分类请求"""
    name: str
    industry: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    color: str = "#6366f1"


class KnowledgeCategoryUpdate(BaseModel):
    """更新知识库分类请求"""
    name: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[str] = None
    color: Optional[str] = None


class KnowledgeCategoryResponse(BaseModel):
    """知识库分类响应"""
    id: int
    name: str
    industry: Optional[str]
    description: Optional[str]
    tags: Optional[str]
    color: str
    knowledge_count: int
    project_count: int
    created_at: str
    updated_at: str


class KnowledgeCreate(BaseModel):
    """创建知识条目请求"""
    category_id: int
    title: str
    content: str
    type: str = "other"


class KnowledgeUpdate(BaseModel):
    """更新知识条目请求"""
    title: Optional[str] = None
    content: Optional[str] = None
    type: Optional[str] = None


class KnowledgeResponse(BaseModel):
    """知识条目响应"""
    id: int
    category_id: int
    title: str
    content: str
    type: str
    created_at: str
    updated_at: str


# ==================== 知识库分类API ====================

@router.get("/categories", response_model=List[KnowledgeCategoryResponse])
async def get_categories(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取知识库分类列表

    Args:
        search: 搜索关键词（可选）
        db: 数据库会话

    Returns:
        分类列表
    """
    query = db.query(KnowledgeCategory).filter(KnowledgeCategory.status == 1)
    if not is_admin(current_user):
        query = query.filter(KnowledgeCategory.owner_id == current_user.id)

    if search:
        query = query.filter(
            (KnowledgeCategory.name.like(f"%{search}%")) |
            (KnowledgeCategory.industry.like(f"%{search}%")) |
            (KnowledgeCategory.tags.like(f"%{search}%"))
        )

    categories = query.order_by(KnowledgeCategory.updated_at.desc()).all()

    result = []
    for cat in categories:
        # 统计知识数量
        knowledge_count = db.query(Knowledge).filter(
            Knowledge.category_id == cat.id,
            Knowledge.status == 1
        ).count()

        # 统计关联项目数（根据行业匹配）
        project_query = db.query(Project).filter(
            Project.industry == cat.industry,
            Project.status == 1
        )
        if not is_admin(current_user):
            project_query = project_query.filter(Project.owner_id == current_user.id)
        project_count = project_query.count() if cat.industry else 0

        result.append(KnowledgeCategoryResponse(
            id=cat.id,
            name=cat.name,
            industry=cat.industry,
            description=cat.description,
            tags=cat.tags,
            color=cat.color,
            knowledge_count=knowledge_count,
            project_count=project_count,
            created_at=cat.created_at.isoformat() if cat.created_at else "",
            updated_at=cat.updated_at.isoformat() if cat.updated_at else "",
        ))

    return result


@router.post("/categories", response_model=ApiResponse)
async def create_category(
    data: KnowledgeCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建知识库分类

    Args:
        data: 分类数据
        db: 数据库会话

    Returns:
        创建结果
    """
    try:
        category = KnowledgeCategory(
            name=data.name,
            industry=data.industry,
            description=data.description,
            tags=data.tags,
            color=data.color,
            owner_id=current_user.id,
        )
        db.add(category)
        db.commit()
        db.refresh(category)

        return ApiResponse(success=True, data={"id": category.id}, message="分类创建成功")
    except Exception as e:
        db.rollback()
        logger.error(f"创建分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/categories/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: int,
    data: KnowledgeCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新知识库分类

    Args:
        category_id: 分类ID
        data: 更新数据
        db: 数据库会话

    Returns:
        更新结果
    """
    try:
        query = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id)
        if not is_admin(current_user):
            query = query.filter(KnowledgeCategory.owner_id == current_user.id)
        category = query.first()

        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        if data.name is not None:
            category.name = data.name
        if data.industry is not None:
            category.industry = data.industry
        if data.description is not None:
            category.description = data.description
        if data.tags is not None:
            category.tags = data.tags
        if data.color is not None:
            category.color = data.color

        db.commit()
        return ApiResponse(success=True, message="分类更新成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/categories/{category_id}", response_model=ApiResponse)
async def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除知识库分类

    Args:
        category_id: 分类ID
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        query = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id)
        if not is_admin(current_user):
            query = query.filter(KnowledgeCategory.owner_id == current_user.id)
        category = query.first()

        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        # 删除分类（会级联删除关联的知识）
        db.delete(category)
        db.commit()

        return ApiResponse(success=True, message="分类删除成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除分类失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 知识条目API ====================

@router.get("/categories/{category_id}/knowledge", response_model=List[KnowledgeResponse])
async def get_knowledge_list(
    category_id: int,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    获取指定分类的知识列表

    Args:
        category_id: 分类ID
        search: 搜索关键词（可选）
        db: 数据库会话

    Returns:
        知识条目列表
    """
    cat_query = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == category_id)
    if not is_admin(current_user):
        cat_query = cat_query.filter(KnowledgeCategory.owner_id == current_user.id)
    category = cat_query.first()
    if not category:
        raise HTTPException(status_code=404, detail="分类不存在")

    query = db.query(Knowledge).filter(
        Knowledge.category_id == category_id,
        Knowledge.status == 1
    )

    if search:
        query = query.filter(
            (Knowledge.title.like(f"%{search}%")) |
            (Knowledge.content.like(f"%{search}%"))
        )

    items = query.order_by(Knowledge.updated_at.desc()).all()

    return [
        KnowledgeResponse(
            id=item.id,
            category_id=item.category_id,
            title=item.title,
            content=item.content,
            type=item.type,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else "",
        )
        for item in items
    ]


@router.post("/knowledge", response_model=ApiResponse)
async def create_knowledge(
    data: KnowledgeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    创建知识条目

    Args:
        data: 知识数据
        db: 数据库会话

    Returns:
        创建结果
    """
    try:
        # 验证分类存在
        cat_query = db.query(KnowledgeCategory).filter(KnowledgeCategory.id == data.category_id)
        if not is_admin(current_user):
            cat_query = cat_query.filter(KnowledgeCategory.owner_id == current_user.id)
        category = cat_query.first()
        if not category:
            raise HTTPException(status_code=404, detail="分类不存在")

        knowledge = Knowledge(
            category_id=data.category_id,
            title=data.title,
            content=data.content,
            type=data.type,
            owner_id=current_user.id,
        )
        db.add(knowledge)
        db.commit()
        db.refresh(knowledge)

        return ApiResponse(success=True, data={"id": knowledge.id}, message="知识添加成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"创建知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/knowledge/{knowledge_id}", response_model=ApiResponse)
async def update_knowledge(
    knowledge_id: int,
    data: KnowledgeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    更新知识条目

    Args:
        knowledge_id: 知识ID
        data: 更新数据
        db: 数据库会话

    Returns:
        更新结果
    """
    try:
        query = db.query(Knowledge).filter(Knowledge.id == knowledge_id)
        if not is_admin(current_user):
            query = query.filter(Knowledge.owner_id == current_user.id)
        knowledge = query.first()

        if not knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        if data.title is not None:
            knowledge.title = data.title
        if data.content is not None:
            knowledge.content = data.content
        if data.type is not None:
            knowledge.type = data.type

        db.commit()
        return ApiResponse(success=True, message="知识更新成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"更新知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/knowledge/{knowledge_id}", response_model=ApiResponse)
async def delete_knowledge(
    knowledge_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    删除知识条目

    Args:
        knowledge_id: 知识ID
        db: 数据库会话

    Returns:
        删除结果
    """
    try:
        query = db.query(Knowledge).filter(Knowledge.id == knowledge_id)
        if not is_admin(current_user):
            query = query.filter(Knowledge.owner_id == current_user.id)
        knowledge = query.first()

        if not knowledge:
            raise HTTPException(status_code=404, detail="知识不存在")

        db.delete(knowledge)
        db.commit()

        return ApiResponse(success=True, message="知识删除成功")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"删除知识失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge/search", response_model=List[KnowledgeResponse])
async def search_knowledge(
    keyword: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    全局搜索知识

    Args:
        keyword: 搜索关键词
        db: 数据库会话

    Returns:
        知识条目列表
    """
    query = db.query(Knowledge).filter(
        Knowledge.status == 1,
        (Knowledge.title.like(f"%{keyword}%")) |
        (Knowledge.content.like(f"%{keyword}%"))
    )
    if not is_admin(current_user):
        query = query.filter(Knowledge.owner_id == current_user.id)
    items = query.order_by(Knowledge.updated_at.desc()).limit(50).all()

    return [
        KnowledgeResponse(
            id=item.id,
            category_id=item.category_id,
            title=item.title,
            content=item.content,
            type=item.type,
            created_at=item.created_at.isoformat() if item.created_at else "",
            updated_at=item.updated_at.isoformat() if item.updated_at else "",
        )
        for item in items
    ]
