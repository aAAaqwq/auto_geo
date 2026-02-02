# -*- coding: utf-8 -*-
"""
数据报表API
写的数据报表API，统计SEO效果！
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, case

from backend.database import get_db
from backend.database.models import Project, Keyword, IndexCheckRecord, QuestionVariant
from backend.schemas import ApiResponse
from backend.services.auth import require_role
from loguru import logger


router = APIRouter(prefix="/api/reports", tags=["数据报表"], dependencies=[Depends(require_role("admin"))])


# ==================== 响应模型 ====================

class ProjectStatsResponse(BaseModel):
    """项目统计响应"""
    project_id: int
    project_name: str
    company_name: str
    total_keywords: int
    active_keywords: int
    total_questions: int
    total_checks: int
    keyword_hit_rate: float
    company_hit_rate: float


class PlatformStatsResponse(BaseModel):
    """平台统计响应"""
    platform: str
    total_checks: int
    keyword_found: int
    company_found: int
    keyword_hit_rate: float
    company_hit_rate: float


class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str
    keyword_found_count: int
    company_found_count: int
    total_checks: int


# ==================== 报表API ====================

@router.get("/projects", response_model=List[ProjectStatsResponse])
async def get_project_stats(db: Session = Depends(get_db)):
    """
    获取所有项目的统计数据

    注意：返回每个项目的关键词数量、命中率等！
    """
    projects = db.query(Project).filter(Project.status == 1).all()

    results = []
    for project in projects:
        # 统计关键词数量
        total_keywords = db.query(Keyword).filter(
            Keyword.project_id == project.id
        ).count()
        active_keywords = db.query(Keyword).filter(
            Keyword.project_id == project.id,
            Keyword.status == "active"
        ).count()

        # 统计问题变体数量
        keyword_ids = db.query(Keyword.id).filter(
            Keyword.project_id == project.id
        ).subquery()
        total_questions = db.query(QuestionVariant).filter(
            QuestionVariant.keyword_id.in_(keyword_ids)
        ).count()

        # 统计检测记录
        keyword_ids_active = db.query(Keyword.id).filter(
            Keyword.project_id == project.id,
            Keyword.status == "active"
        ).subquery()

        total_checks = db.query(IndexCheckRecord).filter(
            IndexCheckRecord.keyword_id.in_(keyword_ids_active)
        ).count()

        # 计算命中率
        stats = db.query(
            func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
            func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
        ).filter(
            IndexCheckRecord.keyword_id.in_(keyword_ids_active)
        ).first()

        keyword_found = stats.keyword_found or 0
        company_found = stats.company_found or 0

        keyword_hit_rate = round(keyword_found / total_checks * 100, 2) if total_checks > 0 else 0
        company_hit_rate = round(company_found / total_checks * 100, 2) if total_checks > 0 else 0

        results.append(ProjectStatsResponse(
            project_id=project.id,
            project_name=project.name,
            company_name=project.company_name,
            total_keywords=total_keywords,
            active_keywords=active_keywords,
            total_questions=total_questions,
            total_checks=total_checks,
            keyword_hit_rate=keyword_hit_rate,
            company_hit_rate=company_hit_rate
        ))

    return results


@router.get("/platforms", response_model=List[PlatformStatsResponse])
async def get_platform_stats(db: Session = Depends(get_db)):
    """
    获取各平台的统计数据

    注意：比较不同平台的收录效果！
    """
    platforms = ["doubao", "qianwen", "deepseek"]

    results = []
    for platform in platforms:
        # 统计该平台的检测记录
        records = db.query(IndexCheckRecord).filter(
            IndexCheckRecord.platform == platform
        ).all()

        total_checks = len(records)
        keyword_found = sum(1 for r in records if r.keyword_found)
        company_found = sum(1 for r in records if r.company_found)

        keyword_hit_rate = round(keyword_found / total_checks * 100, 2) if total_checks > 0 else 0
        company_hit_rate = round(company_found / total_checks * 100, 2) if total_checks > 0 else 0

        # 平台名称映射
        platform_names = {
            "doubao": "豆包",
            "qianwen": "通义千问",
            "deepseek": "DeepSeek"
        }

        results.append(PlatformStatsResponse(
            platform=platform_names.get(platform, platform),
            total_checks=total_checks,
            keyword_found=keyword_found,
            company_found=company_found,
            keyword_hit_rate=keyword_hit_rate,
            company_hit_rate=company_hit_rate
        ))

    return results


@router.get("/trends", response_model=List[TrendDataPoint])
async def get_trends(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取收录趋势数据

    注意：用于绘制趋势图表！
    """
    start_date = datetime.now() - timedelta(days=days)

    # 按日期分组统计
    trends = db.query(
        func.date(IndexCheckRecord.check_time).label("date"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found"),
        func.count().label("total_checks")
    ).filter(
        IndexCheckRecord.check_time >= start_date
    ).group_by(
        func.date(IndexCheckRecord.check_time)
    ).order_by(
        func.date(IndexCheckRecord.check_time)
    ).all()

    results = []
    for trend in trends:
        results.append(TrendDataPoint(
            date=str(trend.date),
            keyword_found_count=trend.keyword_found or 0,
            company_found_count=trend.company_found or 0,
            total_checks=trend.total_checks
        ))

    return results


@router.get("/overview")
async def get_overview(db: Session = Depends(get_db)):
    """
    获取总体概览数据

    注意：用于仪表盘展示！
    """
    # 项目统计
    total_projects = db.query(Project).filter(Project.status == 1).count()

    # 关键词统计
    total_keywords = db.query(Keyword).filter(Keyword.status == "active").count()

    # 检测记录统计
    total_checks = db.query(IndexCheckRecord).count()

    # 命中率统计
    stats = db.query(
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
    ).first()

    keyword_found = stats.keyword_found or 0
    company_found = stats.company_found or 0

    overall_hit_rate = round((keyword_found + company_found) / (total_checks * 2) * 100, 2) if total_checks > 0 else 0

    return {
        "total_projects": total_projects,
        "total_keywords": total_keywords,
        "total_checks": total_checks,
        "keyword_found": keyword_found,
        "company_found": company_found,
        "overall_hit_rate": overall_hit_rate
    }
