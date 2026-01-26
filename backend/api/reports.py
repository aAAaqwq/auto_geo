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
from backend.database.models import (
    Project, Keyword, IndexCheckRecord, QuestionVariant,
    Article, GeoArticle, PublishRecord
)
from backend.schemas import ApiResponse
from loguru import logger


router = APIRouter(prefix="/api/reports", tags=["数据报表"])


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


class ComprehensiveOverviewResponse(BaseModel):
    """全面数据概览响应"""
    # 文章相关
    total_articles: int  # 普通文章总数
    total_geo_articles: int  # GEO文章总数
    total_articles_generated: int  # 总生成文章数（普通+GEO）
    geo_articles_passed: int  # 质检通过的文章数
    geo_articles_failed: int  # 质检未通过的文章数
    
    # 发布相关
    total_publish_records: int  # 总发布记录数
    publish_success: int  # 发布成功数
    publish_failed: int  # 发布失败数
    publish_pending: int  # 待发布数
    publish_success_rate: float  # 发布成功率
    
    # 收录相关
    total_checks: int  # 总检测次数
    keyword_found: int  # 关键词命中数
    company_found: int  # 公司名命中数
    keyword_hit_rate: float  # 关键词命中率
    company_hit_rate: float  # 公司名命中率
    
    # 项目相关
    total_projects: int  # 项目总数
    total_keywords: int  # 关键词总数
    active_keywords: int  # 活跃关键词数


class DailyTrendPoint(BaseModel):
    """每日趋势数据点"""
    date: str
    articles_generated: int  # 当日生成文章数
    articles_published: int  # 当日发布文章数
    publish_success: int  # 当日发布成功数
    index_checks: int  # 当日检测次数
    keyword_hits: int  # 当日关键词命中数


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


@router.get("/comprehensive", response_model=ComprehensiveOverviewResponse)
async def get_comprehensive_overview(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取全面数据概览

    注意：包含文章生成、发布、收录等全方位数据统计！
    """
    # ========== 文章统计 ==========
    # 普通文章总数
    total_articles = db.query(Article).count()
    
    # GEO文章总数
    geo_query = db.query(GeoArticle)
    if project_id:
        # 通过关键词关联项目
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_query = geo_query.filter(GeoArticle.keyword_id.in_(keyword_ids))
    
    total_geo_articles = geo_query.count()
    total_articles_generated = total_articles + total_geo_articles
    
    # 质检通过/未通过的文章数
    geo_articles_passed = geo_query.filter(GeoArticle.quality_status == "passed").count()
    geo_articles_failed = geo_query.filter(GeoArticle.quality_status == "failed").count()
    
    # ========== 发布统计 ==========
    publish_query = db.query(PublishRecord)
    if project_id:
        # 通过文章关联项目（需要关联GeoArticle和Keyword）
        # 这里简化处理，如果project_id存在，只统计GEO文章的发布
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_article_ids = db.query(GeoArticle.id).filter(GeoArticle.keyword_id.in_(keyword_ids)).subquery()
        # 注意：PublishRecord关联的是Article，不是GeoArticle，这里需要特殊处理
        # 暂时不按项目筛选发布记录
    
    total_publish_records = publish_query.count()
    publish_success = publish_query.filter(PublishRecord.publish_status == 2).count()  # 2=成功
    publish_failed = publish_query.filter(PublishRecord.publish_status == 3).count()  # 3=失败
    publish_pending = publish_query.filter(PublishRecord.publish_status == 0).count()  # 0=待发布
    
    publish_success_rate = round(publish_success / total_publish_records * 100, 2) if total_publish_records > 0 else 0
    
    # ========== 收录统计 ==========
    check_query = db.query(IndexCheckRecord)
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
    
    total_checks = check_query.count()
    
    check_stats = check_query.with_entities(
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
    ).first()
    
    keyword_found = check_stats.keyword_found or 0
    company_found = check_stats.company_found or 0
    
    keyword_hit_rate = round(keyword_found / total_checks * 100, 2) if total_checks > 0 else 0
    company_hit_rate = round(company_found / total_checks * 100, 2) if total_checks > 0 else 0
    
    # ========== 项目统计 ==========
    project_query = db.query(Project).filter(Project.status == 1)
    if project_id:
        project_query = project_query.filter(Project.id == project_id)
    
    total_projects = project_query.count()
    
    keyword_query = db.query(Keyword)
    if project_id:
        keyword_query = keyword_query.filter(Keyword.project_id == project_id)
    
    total_keywords = keyword_query.count()
    active_keywords = keyword_query.filter(Keyword.status == "active").count()
    
    return ComprehensiveOverviewResponse(
        total_articles=total_articles,
        total_geo_articles=total_geo_articles,
        total_articles_generated=total_articles_generated,
        geo_articles_passed=geo_articles_passed,
        geo_articles_failed=geo_articles_failed,
        total_publish_records=total_publish_records,
        publish_success=publish_success,
        publish_failed=publish_failed,
        publish_pending=publish_pending,
        publish_success_rate=publish_success_rate,
        total_checks=total_checks,
        keyword_found=keyword_found,
        company_found=company_found,
        keyword_hit_rate=keyword_hit_rate,
        company_hit_rate=company_hit_rate,
        total_projects=total_projects,
        total_keywords=total_keywords,
        active_keywords=active_keywords
    )


@router.get("/daily-trends", response_model=List[DailyTrendPoint])
async def get_daily_trends(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取每日趋势数据

    注意：包含文章生成、发布、收录的每日趋势！
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 获取所有日期范围
    date_range = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).date()
        date_range.append(date)
    date_range.reverse()
    
    results = []
    
    for date in date_range:
        date_str = date.isoformat()
        date_start = datetime.combine(date, datetime.min.time())
        date_end = datetime.combine(date, datetime.max.time())
        
        # 统计当日生成的文章数（普通文章 + GEO文章）
        articles_generated = db.query(Article).filter(
            Article.created_at >= date_start,
            Article.created_at < date_end
        ).count()
        
        geo_articles_generated = db.query(GeoArticle)
        if project_id:
            keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
            geo_articles_generated = geo_articles_generated.filter(GeoArticle.keyword_id.in_(keyword_ids))
        
        geo_articles_generated = geo_articles_generated.filter(
            GeoArticle.created_at >= date_start,
            GeoArticle.created_at < date_end
        ).count()
        
        total_generated = articles_generated + geo_articles_generated
        
        # 统计当日发布的文章数
        publish_query = db.query(PublishRecord).filter(
            PublishRecord.published_at >= date_start,
            PublishRecord.published_at < date_end
        )
        articles_published = publish_query.count()
        publish_success = publish_query.filter(PublishRecord.publish_status == 2).count()
        
        # 统计当日检测次数和命中数
        check_query = db.query(IndexCheckRecord).filter(
            IndexCheckRecord.check_time >= date_start,
            IndexCheckRecord.check_time < date_end
        )
        if project_id:
            keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
            check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
        
        index_checks = check_query.count()
        keyword_hits = check_query.filter(IndexCheckRecord.keyword_found == True).count()
        
        results.append(DailyTrendPoint(
            date=date_str,
            articles_generated=total_generated,
            articles_published=articles_published,
            publish_success=publish_success,
            index_checks=index_checks,
            keyword_hits=keyword_hits
        ))
    
    return results


@router.get("/platform-comparison", response_model=List[dict])
async def get_platform_comparison(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取平台对比分析数据
    
    注意：用于绘制多平台对比趋势图！
    """
    start_date = datetime.now() - timedelta(days=days)
    platforms = ["doubao", "qianwen", "deepseek"]
    
    # 获取日期范围
    date_range = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).date()
        date_range.append(date)
    date_range.reverse()
    
    platform_names = {
        "doubao": "豆包",
        "qianwen": "通义千问",
        "deepseek": "DeepSeek"
    }
    
    results = []
    
    for platform in platforms:
        platform_data = {
            "platform": platform,
            "platform_name": platform_names.get(platform, platform),
            "daily_data": []
        }
        
        for date in date_range:
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            
            # 统计该平台当日的检测记录
            check_query = db.query(IndexCheckRecord).filter(
                IndexCheckRecord.platform == platform,
                IndexCheckRecord.check_time >= date_start,
                IndexCheckRecord.check_time < date_end
            )
            
            if project_id:
                keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
                check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
            
            total_checks = check_query.count()
            keyword_hits = check_query.filter(IndexCheckRecord.keyword_found == True).count()
            hit_rate = round(keyword_hits / total_checks * 100, 2) if total_checks > 0 else 0
            
            platform_data["daily_data"].append({
                "date": date.isoformat(),
                "total_checks": total_checks,
                "keyword_hits": keyword_hits,
                "hit_rate": hit_rate
            })
        
        results.append(platform_data)
    
    return results


@router.get("/project-comparison", response_model=List[dict])
async def get_project_comparison(
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    project_ids: Optional[str] = Query(None, description="项目ID列表，逗号分隔"),
    db: Session = Depends(get_db)
):
    """
    获取项目对比分析数据
    
    注意：用于绘制多项目对比趋势图！
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 获取要对比的项目列表
    if project_ids:
        project_id_list = [int(x.strip()) for x in project_ids.split(",")]
        projects = db.query(Project).filter(Project.id.in_(project_id_list)).all()
    else:
        # 如果没有指定，获取所有活跃项目
        projects = db.query(Project).filter(Project.status == 1).limit(5).all()
    
    # 获取日期范围
    date_range = []
    for i in range(days):
        date = (datetime.now() - timedelta(days=i)).date()
        date_range.append(date)
    date_range.reverse()
    
    results = []
    
    for project in projects:
        project_data = {
            "project_id": project.id,
            "project_name": project.name,
            "company_name": project.company_name,
            "daily_data": []
        }
        
        # 获取项目的关键词ID
        keyword_ids = db.query(Keyword.id).filter(
            Keyword.project_id == project.id,
            Keyword.status == "active"
        ).subquery()
        
        for date in date_range:
            date_start = datetime.combine(date, datetime.min.time())
            date_end = datetime.combine(date, datetime.max.time())
            
            # 统计该项目当日的检测记录
            check_query = db.query(IndexCheckRecord).filter(
                IndexCheckRecord.keyword_id.in_(keyword_ids),
                IndexCheckRecord.check_time >= date_start,
                IndexCheckRecord.check_time < date_end
            )
            
            total_checks = check_query.count()
            keyword_hits = check_query.filter(IndexCheckRecord.keyword_found == True).count()
            hit_rate = round(keyword_hits / total_checks * 100, 2) if total_checks > 0 else 0
            
            project_data["daily_data"].append({
                "date": date.isoformat(),
                "total_checks": total_checks,
                "keyword_hits": keyword_hits,
                "hit_rate": hit_rate
            })
        
        results.append(project_data)
    
    return results


@router.get("/top-projects", response_model=List[dict])
async def get_top_projects(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取项目TOP排行榜
    
    注意：按收录命中率排序！
    """
    project_query = db.query(Project).filter(Project.status == 1)
    if project_id:
        project_query = project_query.filter(Project.id == project_id)
    
    projects = project_query.all()
    
    results = []
    
    for project in projects:
        # 获取项目的关键词ID
        keyword_ids = db.query(Keyword.id).filter(
            Keyword.project_id == project.id,
            Keyword.status == "active"
        ).subquery()
        
        # 统计检测记录
        total_checks = db.query(IndexCheckRecord).filter(
            IndexCheckRecord.keyword_id.in_(keyword_ids)
        ).count()
        
        if total_checks == 0:
            continue
        
        # 计算命中率
        stats = db.query(
            func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
            func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
        ).filter(
            IndexCheckRecord.keyword_id.in_(keyword_ids)
        ).first()
        
        keyword_found = stats.keyword_found or 0
        company_found = stats.company_found or 0
        
        keyword_hit_rate = round(keyword_found / total_checks * 100, 2) if total_checks > 0 else 0
        company_hit_rate = round(company_found / total_checks * 100, 2) if total_checks > 0 else 0
        
        # 统计文章和发布数据
        geo_articles = db.query(GeoArticle).filter(GeoArticle.keyword_id.in_(keyword_ids)).count()
        
        results.append({
            "project_id": project.id,
            "project_name": project.name,
            "company_name": project.company_name,
            "total_keywords": db.query(Keyword).filter(Keyword.project_id == project.id).count(),
            "total_checks": total_checks,
            "keyword_hit_rate": keyword_hit_rate,
            "company_hit_rate": company_hit_rate,
            "total_articles": geo_articles,
            "total_publish": 0  # 暂时不统计
        })
    
    # 按关键词命中率排序
    results.sort(key=lambda x: x["keyword_hit_rate"], reverse=True)
    
    return results[:limit]
