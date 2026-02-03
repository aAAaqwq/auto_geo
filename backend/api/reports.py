# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, case
from backend.database import get_db
from backend.database.models import (
    Project, Keyword, IndexCheckRecord, QuestionVariant,
    Article, GeoArticle, PublishRecord
)
from backend.schemas import ApiResponse
from loguru import logger

router = APIRouter(prefix="/api/reports", tags=["数据报表"])


class TrendDataPoint(BaseModel):
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


class ProjectStatsResponse(BaseModel):
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
    platform: str
    total_checks: int
    keyword_found: int
    company_found: int
    keyword_hit_rate: float
    company_hit_rate: float


# ==================== 报表API ====================

@router.get("/projects", response_model=List[ProjectStatsResponse])
async def get_project_stats(db: Session = Depends(get_db)):
    """
    获取所有项目的统计数据

    注意：返回每个项目的关键词数量、命中率等！
    """
    # 1. 批量查询关键词统计
    keyword_stats = db.query(
        Keyword.project_id,
        func.count(Keyword.id).label('total'),
        func.sum(case((Keyword.status == 'active', 1), else_=0)).label('active')
    ).group_by(Keyword.project_id).all()
    keyword_map = {r.project_id: (r.total, r.active or 0) for r in keyword_stats}

    # 2. 批量查询问题变体统计
    question_stats = db.query(
        Keyword.project_id,
        func.count(QuestionVariant.id).label('total')
    ).select_from(Keyword).join(
        QuestionVariant, QuestionVariant.keyword_id == Keyword.id
    ).group_by(
        Keyword.project_id
    ).all()
    question_map = {r.project_id: r.total for r in question_stats}

    # 3. 批量查询检测记录统计 (只统计 active 关键词)
    check_stats = db.query(
        Keyword.project_id,
        func.count(IndexCheckRecord.id).label('total'),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label('keyword_found'),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label('company_found')
    ).select_from(Keyword).join(
        IndexCheckRecord, IndexCheckRecord.keyword_id == Keyword.id
    ).filter(
        Keyword.status == "active"
    ).group_by(
        Keyword.project_id
    ).all()
    check_map = {
        r.project_id: (r.total, r.keyword_found or 0, r.company_found or 0) 
        for r in check_stats
    }

    # 4. 组装结果
    projects = db.query(Project).filter(Project.status == 1).all()
    results = []
    
    for project in projects:
        total_keywords, active_keywords = keyword_map.get(project.id, (0, 0))
        total_questions = question_map.get(project.id, 0)
        total_checks, keyword_found, company_found = check_map.get(project.id, (0, 0, 0))

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

    # 优化：使用聚合查询直接在数据库层计算
    stats = db.query(
        IndexCheckRecord.platform,
        func.count(IndexCheckRecord.id).label('total'),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label('keyword_found'),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label('company_found')
    ).filter(
        IndexCheckRecord.platform.in_(platforms)
    ).group_by(
        IndexCheckRecord.platform
    ).all()
    
    stats_map = {
        r.platform: (r.total, r.keyword_found or 0, r.company_found or 0) 
        for r in stats
    }

    results = []
    for platform in platforms:
        total_checks, keyword_found, company_found = stats_map.get(platform, (0, 0, 0))

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
    """获取收录趋势数据"""
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

    # 按日期分组统计
    stats = db.query(
        func.substr(IndexCheckRecord.check_time, 1, 10).label("date_str"),
        func.count(IndexCheckRecord.id).label("total"),
        func.sum(cast(IndexCheckRecord.keyword_found, Integer)).label("kw_found"),
        func.sum(cast(IndexCheckRecord.company_found, Integer)).label("co_found")
    ).filter(IndexCheckRecord.check_time >= start_date) \
        .group_by("date_str") \
        .order_by("date_str").all()

    if not stats:
        return [TrendDataPoint(date=datetime.now().strftime("%Y-%m-%d"), keyword_found_count=0, company_found_count=0, total_checks=0)]

    return [
        TrendDataPoint(
            date=s.date_str,
            keyword_found_count=int(s.kw_found or 0),
            company_found_count=int(s.co_found or 0),
            total_checks=int(s.total or 0)
        ) for s in stats
    ]


@router.get("/overview")
async def get_overview(db: Session = Depends(get_db)):
    """获取顶部统计卡片"""
    # 统计监测记录表
    total_checks = db.query(IndexCheckRecord).count()

    if total_checks == 0:
        return {
            "total_projects": db.query(Project).filter(Project.status == 1).count(),
            "total_keywords": 0,
            "total_checks": 0,
            "keyword_found": 0,
            "company_found": 0,
            "overall_hit_rate": 0
        }

    kw_hits = db.query(IndexCheckRecord).filter(IndexCheckRecord.keyword_found == True).count()
    co_hits = db.query(IndexCheckRecord).filter(IndexCheckRecord.company_found == True).count()

    # 命中率 = (公司命中的次数 / 总检测次数) * 100
    hit_rate = round((co_hits / total_checks) * 100, 2)

    return {
        "total_projects": db.query(Project).filter(Project.status == 1).count(),
        "total_keywords": total_checks,
        "total_checks": total_checks,
        "keyword_found": kw_hits,
        "company_found": co_hits,
        "overall_hit_rate": hit_rate
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
    
    # 优化：合并查询
    stats = geo_query.with_entities(
        func.count(GeoArticle.id).label("total"),
        func.sum(case((GeoArticle.quality_status == "passed", 1), else_=0)).label("passed"),
        func.sum(case((GeoArticle.quality_status == "failed", 1), else_=0)).label("failed")
    ).first()

    total_geo_articles = stats.total or 0
    total_articles_generated = total_articles + total_geo_articles
    geo_articles_passed = stats.passed or 0
    geo_articles_failed = stats.failed or 0
    
    # ========== 发布统计 ==========
    publish_query = db.query(PublishRecord)
    if project_id:
        # 通过文章关联项目（需要关联GeoArticle和Keyword）
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_article_ids = db.query(GeoArticle.id).filter(GeoArticle.keyword_id.in_(keyword_ids)).subquery()
    
    # 优化：合并查询
    publish_stats = publish_query.with_entities(
        func.count(PublishRecord.id).label("total"),
        func.sum(case((PublishRecord.publish_status == 2, 1), else_=0)).label("success"),
        func.sum(case((PublishRecord.publish_status == 3, 1), else_=0)).label("failed"),
        func.sum(case((PublishRecord.publish_status == 0, 1), else_=0)).label("pending")
    ).first()
    
    total_publish_records = publish_stats.total or 0
    publish_success = publish_stats.success or 0
    publish_failed = publish_stats.failed or 0
    publish_pending = publish_stats.pending or 0
    
    publish_success_rate = round(publish_success / total_publish_records * 100, 2) if total_publish_records > 0 else 0
    
    # ========== 收录统计 ==========
    check_query = db.query(IndexCheckRecord)
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
    
    # 优化：合并查询
    check_stats = check_query.with_entities(
        func.count(IndexCheckRecord.id).label("total"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
    ).first()
    
    total_checks = check_stats.total or 0
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
    
    # 1. 统计普通文章每日生成数
    articles_daily = db.query(
        func.date(Article.created_at).label("date"),
        func.count().label("count")
    ).filter(
        Article.created_at >= start_date
    ).group_by(
        func.date(Article.created_at)
    ).all()
    articles_map = {str(r.date): r.count for r in articles_daily}
    
    # 2. 统计GEO文章每日生成数
    geo_query = db.query(
        func.date(GeoArticle.created_at).label("date"),
        func.count().label("count")
    ).filter(
        GeoArticle.created_at >= start_date
    )
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_query = geo_query.filter(GeoArticle.keyword_id.in_(keyword_ids))
    
    geo_articles_daily = geo_query.group_by(func.date(GeoArticle.created_at)).all()
    geo_articles_map = {str(r.date): r.count for r in geo_articles_daily}
    
    # 3. 统计每日发布数
    publish_daily = db.query(
        func.date(PublishRecord.published_at).label("date"),
        func.count().label("total"),
        func.sum(case((PublishRecord.publish_status == 2, 1), else_=0)).label("success")
    ).filter(
        PublishRecord.published_at >= start_date
    ).group_by(
        func.date(PublishRecord.published_at)
    ).all()
    publish_map = {str(r.date): (r.total, r.success or 0) for r in publish_daily}
    
    # 4. 统计每日检测数和命中数
    check_query = db.query(
        func.date(IndexCheckRecord.check_time).label("date"),
        func.count().label("total"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("hits")
    ).filter(
        IndexCheckRecord.check_time >= start_date
    )
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
    
    checks_daily = check_query.group_by(func.date(IndexCheckRecord.check_time)).all()
    checks_map = {str(r.date): (r.total, r.hits or 0) for r in checks_daily}
    
    # 组合结果
    results = []
    for date in date_range:
        date_str = date.isoformat()
        
        art_count = articles_map.get(date_str, 0)
        geo_art_count = geo_articles_map.get(date_str, 0)
        pub_total, pub_success = publish_map.get(date_str, (0, 0))
        check_total, check_hits = checks_map.get(date_str, (0, 0))
        
        results.append(DailyTrendPoint(
            date=date_str,
            articles_generated=art_count + geo_art_count,
            articles_published=pub_total,
            publish_success=pub_success,
            index_checks=check_total,
            keyword_hits=check_hits
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
    
    # 一次性获取所有平台的每日统计数据
    check_query = db.query(
        IndexCheckRecord.platform,
        func.date(IndexCheckRecord.check_time).label("date"),
        func.count().label("total"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("hits")
    ).filter(
        IndexCheckRecord.check_time >= start_date,
        IndexCheckRecord.platform.in_(platforms)
    )
    
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        check_query = check_query.filter(IndexCheckRecord.keyword_id.in_(keyword_ids))
    
    stats_results = check_query.group_by(
        IndexCheckRecord.platform,
        func.date(IndexCheckRecord.check_time)
    ).all()
    
    # 构造数据映射：platform -> date -> {total, hits}
    stats_map = {}
    for r in stats_results:
        if r.platform not in stats_map:
            stats_map[r.platform] = {}
        stats_map[r.platform][str(r.date)] = {"total": r.total, "hits": r.hits or 0}
    
    results = []
    for platform in platforms:
        platform_data = {
            "platform": platform,
            "platform_name": platform_names.get(platform, platform),
            "daily_data": []
        }
        
        platform_stats = stats_map.get(platform, {})
        
        for date in date_range:
            date_str = date.isoformat()
            day_stats = platform_stats.get(date_str, {"total": 0, "hits": 0})
            
            total_checks = day_stats["total"]
            keyword_hits = day_stats["hits"]
            hit_rate = round(keyword_hits / total_checks * 100, 2) if total_checks > 0 else 0
            
            platform_data["daily_data"].append({
                "date": date_str,
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
        try:
            project_id_list = [int(x.strip()) for x in project_ids.split(",")]
        except ValueError:
            raise HTTPException(status_code=422, detail="project_ids必须是逗号分隔的整数列表")
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
    
    # 一次性获取所有项目的每日统计数据
    project_ids_actual = [p.id for p in projects]
    check_query = db.query(
        Keyword.project_id,
        func.date(IndexCheckRecord.check_time).label("date"),
        func.count().label("total"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("hits")
    ).join(
        Keyword, IndexCheckRecord.keyword_id == Keyword.id
    ).filter(
        IndexCheckRecord.check_time >= start_date,
        Keyword.project_id.in_(project_ids_actual)
    ).group_by(
        Keyword.project_id,
        func.date(IndexCheckRecord.check_time)
    )
    
    stats_results = check_query.all()
    
    # 构造映射：project_id -> date -> {total, hits}
    stats_map = {}
    for r in stats_results:
        if r.project_id not in stats_map:
            stats_map[r.project_id] = {}
        stats_map[r.project_id][str(r.date)] = {"total": r.total, "hits": r.hits or 0}
    
    results = []
    for project in projects:
        project_data = {
            "project_id": project.id,
            "project_name": project.name,
            "company_name": project.company_name,
            "daily_data": []
        }
        
        project_stats = stats_map.get(project.id, {})
        
        for date in date_range:
            date_str = date.isoformat()
            day_stats = project_stats.get(date_str, {"total": 0, "hits": 0})
            
            total_checks = day_stats["total"]
            keyword_hits = day_stats["hits"]
            hit_rate = round(keyword_hits / total_checks * 100, 2) if total_checks > 0 else 0
            
            project_data["daily_data"].append({
                "date": date_str,
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
    
    # 使用 SQLAlchemy 的聚合查询优化
    # 1. 关键词总数
    kw_total_sub = db.query(
        Keyword.project_id,
        func.count(Keyword.id).label("total_keywords")
    ).group_by(Keyword.project_id).subquery()

    # 2. 检测统计
    check_stats_sub = db.query(
        Keyword.project_id,
        func.count(IndexCheckRecord.id).label("total_checks"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found")
    ).join(
        IndexCheckRecord, Keyword.id == IndexCheckRecord.keyword_id
    ).group_by(Keyword.project_id).subquery()

    # 3. 文章统计
    geo_article_sub = db.query(
        Keyword.project_id,
        func.count(GeoArticle.id).label("total_articles")
    ).join(
        GeoArticle, Keyword.id == GeoArticle.keyword_id
    ).group_by(Keyword.project_id).subquery()

    # 主查询
    query = db.query(
        Project.id.label("project_id"),
        Project.name.label("project_name"),
        Project.company_name,
        func.coalesce(kw_total_sub.c.total_keywords, 0).label("total_keywords"),
        func.coalesce(check_stats_sub.c.total_checks, 0).label("total_checks"),
        func.coalesce(check_stats_sub.c.keyword_found, 0).label("keyword_found"),
        func.coalesce(check_stats_sub.c.company_found, 0).label("company_found"),
        func.coalesce(geo_article_sub.c.total_articles, 0).label("total_articles")
    ).outerjoin(
        kw_total_sub, Project.id == kw_total_sub.c.project_id
    ).outerjoin(
        check_stats_sub, Project.id == check_stats_sub.c.project_id
    ).outerjoin(
        geo_article_sub, Project.id == geo_article_sub.c.project_id
    ).filter(Project.status == 1)

    if project_id:
        query = query.filter(Project.id == project_id)

    stats_results = query.all()

    results = []
    for r in stats_results:
        if r.total_checks == 0:
            continue
            
        keyword_hit_rate = round(r.keyword_found / r.total_checks * 100, 2)
        company_hit_rate = round(r.company_found / r.total_checks * 100, 2)
        
        results.append({
            "project_id": r.project_id,
            "project_name": r.project_name,
            "company_name": r.company_name,
            "total_keywords": r.total_keywords,
            "total_checks": r.total_checks,
            "keyword_hit_rate": keyword_hit_rate,
            "company_hit_rate": company_hit_rate,
            "total_articles": r.total_articles,
            "total_publish": 0
        })
    
    # 按关键词命中率排序
    results.sort(key=lambda x: x["keyword_hit_rate"], reverse=True)
    
    return results[:limit]


@router.get("/article-stats", response_model=dict)
async def get_article_stats(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取文章统计数据（用于GEO Dashboard）
    
    注意：返回文章总数、发布数、收录数等核心指标！
    """
    # 基础查询
    geo_query = db.query(GeoArticle)
    
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_query = geo_query.filter(GeoArticle.keyword_id.in_(keyword_ids))
    
    # 文章统计
    total_articles = geo_query.count()
    
    # 已发布文章数（status为published）
    published_count = geo_query.filter(GeoArticle.publish_status == "published").count()
    
    # 已收录文章数（通过关联的关键词检测记录）
    indexed_subquery = db.query(IndexCheckRecord.keyword_id).filter(
        IndexCheckRecord.keyword_found == True
    ).distinct().subquery()
    
    if project_id:
        indexed_count = geo_query.filter(GeoArticle.keyword_id.in_(indexed_subquery)).count()
    else:
        indexed_count = geo_query.filter(GeoArticle.keyword_id.in_(indexed_subquery)).count()
    
    # 计算收录率
    index_rate = round((indexed_count / published_count * 100), 1) if published_count > 0 else 0
    
    # 平台分布（从发布记录中统计）
    platform_stats = db.query(
        GeoArticle.platform,
        func.count(GeoArticle.id).label('count')
    ).filter(
        GeoArticle.platform.isnot(None)
    ).group_by(GeoArticle.platform).all()
    
    platform_distribution = {p.platform: p.count for p in platform_stats}
    
    return {
        "total_articles": total_articles,
        "published_count": published_count,
        "indexed_count": indexed_count,
        "index_rate": index_rate,
        "platform_distribution": platform_distribution
    }


@router.get("/funnel-data", response_model=dict)
async def get_funnel_data(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    days: int = Query(30, ge=1, le=90, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取漏斗图数据（生成→发布→收录转化漏斗）
    
    注意：展示内容生产到收录的完整转化链路！
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 基础查询条件
    base_geo_query = db.query(GeoArticle).filter(GeoArticle.created_at >= start_date)
    
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        base_geo_query = base_geo_query.filter(GeoArticle.keyword_id.in_(keyword_ids))
    
    # 1. 生成文章数
    generated_count = base_geo_query.count()
    
    # 2. 已发布文章数
    published_count = base_geo_query.filter(GeoArticle.publish_status == "published").count()
    
    # 3. 质检通过数
    passed_count = base_geo_query.filter(GeoArticle.quality_status == "passed").count()
    
    # 4. 已收录文章数（通过检测记录判断）
    indexed_subquery = db.query(IndexCheckRecord.keyword_id).filter(
        IndexCheckRecord.keyword_found == True,
        IndexCheckRecord.check_time >= start_date
    ).distinct().subquery()
    
    if project_id:
        indexed_count = base_geo_query.filter(GeoArticle.keyword_id.in_(indexed_subquery)).count()
    else:
        indexed_count = base_geo_query.filter(GeoArticle.keyword_id.in_(indexed_subquery)).count()
    
    # 计算转化率
    publish_rate = round((published_count / generated_count * 100), 2) if generated_count > 0 else 0
    quality_rate = round((passed_count / generated_count * 100), 2) if generated_count > 0 else 0
    index_rate = round((indexed_count / published_count * 100), 2) if published_count > 0 else 0
    overall_rate = round((indexed_count / generated_count * 100), 2) if generated_count > 0 else 0
    
    return {
        "funnel_data": [
            {"name": "生成文章", "value": generated_count},
            {"name": "质检通过", "value": passed_count},
            {"name": "已发布", "value": published_count},
            {"name": "已收录", "value": indexed_count}
        ],
        "conversion_rates": {
            "quality_rate": quality_rate,      # 质检通过率
            "publish_rate": publish_rate,      # 发布转化率
            "index_rate": index_rate,          # 收录转化率（从发布）
            "overall_rate": overall_rate       # 总转化率（从生成到收录）
        },
        "summary": {
            "generated": generated_count,
            "published": published_count,
            "indexed": indexed_count,
            "period_days": days
        }
    }


@router.get("/kpi-cards", response_model=dict)
async def get_kpi_cards(
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取KPI卡片数据（核心指标概览）
    
    注意：用于首页展示的关键指标卡片！
    """
    # 基础查询
    geo_query = db.query(GeoArticle)
    
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        geo_query = geo_query.filter(GeoArticle.keyword_id.in_(keyword_ids))
    
    # 1. 文章生成指标
    total_generated = geo_query.count()
    today_generated = geo_query.filter(
        func.date(GeoArticle.created_at) == func.date(func.now())
    ).count()
    week_generated = geo_query.filter(
        GeoArticle.created_at >= func.now() - timedelta(days=7)
    ).count()
    
    # 2. 发布指标
    total_published = geo_query.filter(GeoArticle.publish_status == "published").count()
    publish_rate = round((total_published / total_generated * 100), 1) if total_generated > 0 else 0
    
    # 3. 收录指标
    indexed_subquery = db.query(IndexCheckRecord.keyword_id).filter(
        IndexCheckRecord.keyword_found == True
    ).distinct().subquery()
    
    total_indexed = geo_query.filter(GeoArticle.keyword_id.in_(indexed_subquery)).count()
    index_rate = round((total_indexed / total_published * 100), 1) if total_published > 0 else 0
    
    # 4. 项目与关键词
    total_projects = db.query(Project).filter(Project.status == 1).count()
    total_keywords = db.query(Keyword).count()
    
    if project_id:
        active_keywords = db.query(Keyword).filter(
            Keyword.project_id == project_id,
            Keyword.status == "active"
        ).count()
    else:
        active_keywords = db.query(Keyword).filter(Keyword.status == "active").count()
    
    # 5. 平台分布
    platform_stats = db.query(
        GeoArticle.platform,
        func.count(GeoArticle.id).label('count')
    ).filter(
        GeoArticle.platform.isnot(None),
        GeoArticle.publish_status == "published"
    ).group_by(GeoArticle.platform).all()
    
    platform_distribution = {p.platform: p.count for p in platform_stats}
    
    return {
        "article_generation": {
            "total": total_generated,
            "today": today_generated,
            "this_week": week_generated,
            "unit": "篇"
        },
        "publishing": {
            "total_published": total_published,
            "publish_rate": publish_rate,
            "unit": "%"
        },
        "indexing": {
            "total_indexed": total_indexed,
            "index_rate": index_rate,
            "unit": "%"
        },
        "projects_keywords": {
            "total_projects": total_projects,
            "total_keywords": total_keywords,
            "active_keywords": active_keywords
        },
        "platform_distribution": platform_distribution,
        "update_time": datetime.now(timezone.utc).isoformat()
    }


@router.get("/top-articles", response_model=List[dict])
async def get_top_articles(
    limit: int = Query(10, ge=1, le=50, description="返回数量"),
    project_id: Optional[int] = Query(None, description="项目ID筛选"),
    db: Session = Depends(get_db)
):
    """
    获取高贡献文章列表
    
    注意：返回命中率最高的文章（通过关联的关键词检测结果）！
    """
    # 使用 SQLAlchemy 聚合查询优化
    # 1. 统计每个关键词的命中率
    kw_stats_sub = db.query(
        IndexCheckRecord.keyword_id,
        func.count(IndexCheckRecord.id).label("total_checks"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_hits")
    ).group_by(IndexCheckRecord.keyword_id).subquery()

    # 2. 获取每个关键词的最新检测状态 (使用子查询获取最新ID)
    latest_check_id_sub = db.query(
        IndexCheckRecord.keyword_id,
        func.max(IndexCheckRecord.id).label("max_id")
    ).group_by(IndexCheckRecord.keyword_id).subquery()

    latest_check_status_sub = db.query(
        IndexCheckRecord.keyword_id,
        IndexCheckRecord.keyword_found.label("last_status")
    ).join(
        latest_check_id_sub, IndexCheckRecord.id == latest_check_id_sub.c.max_id
    ).subquery()

    # 主查询
    query = db.query(
        GeoArticle.id.label("article_id"),
        GeoArticle.title,
        GeoArticle.platform,
        GeoArticle.created_at,
        func.coalesce(kw_stats_sub.c.total_checks, 0).label("total_checks"),
        func.coalesce(kw_stats_sub.c.keyword_hits, 0).label("keyword_hits"),
        func.coalesce(latest_check_status_sub.c.last_status, False).label("last_status")
    ).outerjoin(
        kw_stats_sub, GeoArticle.keyword_id == kw_stats_sub.c.keyword_id
    ).outerjoin(
        latest_check_status_sub, GeoArticle.keyword_id == latest_check_status_sub.c.keyword_id
    )
    
    if project_id:
        keyword_ids = db.query(Keyword.id).filter(Keyword.project_id == project_id).subquery()
        query = query.filter(GeoArticle.keyword_id.in_(keyword_ids))
        
    stats_results = query.all()
    
    results = []
    for r in stats_results:
        hit_rate = round(r.keyword_hits / r.total_checks * 100, 2) if r.total_checks > 0 else 0
        
        if hit_rate > 0:
            results.append({
                "article_id": r.article_id,
                "title": r.title,
                "platform": r.platform,
                "created_at": r.created_at.isoformat(),
                "keyword_hit_rate": hit_rate,
                "last_check_status": r.last_status
            })
            
    # 按命中率排序
    results.sort(key=lambda x: x["keyword_hit_rate"], reverse=True)
    
    return results[:limit]

