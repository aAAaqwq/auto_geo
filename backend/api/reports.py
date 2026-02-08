# -*- coding: utf-8 -*-
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, Integer, desc, case
from backend.database import get_db
from backend.database.models import Project, Keyword, IndexCheckRecord, GeoArticle, Article, PublishRecord, Account, QuestionVariant

router = APIRouter(prefix="/api/reports", tags=["数据报表"])

class SummaryStats(BaseModel):
    total_articles: int
    common_articles: int
    geo_articles: int
    publish_success_rate: float
    publish_success_count: int
    publish_total_count: int
    keyword_hit_rate: float
    keyword_hit_count: int
    keyword_check_count: int
    company_hit_rate: float
    company_hit_count: int
    company_check_count: int

class PlatformStat(BaseModel):
    platform: str
    hit_count: int
    total_count: int
    hit_rate: float

class ProjectRank(BaseModel):
    rank: int
    project_name: str
    company_name: str
    content_volume: int
    ai_mention_rate: float
    brand_relevance: float

class ContentAnalysis(BaseModel):
    rank: int
    title: str
    platform: str
    ai_contribution: float
    publish_time: Optional[str]

class TrendDataPoint(BaseModel):
    """趋势数据点"""
    date: str
    keyword_found_count: int
    company_found_count: int
    total_checks: int

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
    platform: Optional[str] = Query(None, description="平台筛选"),
    db: Session = Depends(get_db)
):
    """
    获取收录趋势数据
    
    注意：用于绘制趋势图表！
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # 构建查询
    query = db.query(
        func.date(IndexCheckRecord.check_time).label("date"),
        func.sum(case((IndexCheckRecord.keyword_found == True, 1), else_=0)).label("keyword_found"),
        func.sum(case((IndexCheckRecord.company_found == True, 1), else_=0)).label("company_found"),
        func.count().label("total_checks")
    ).filter(
        IndexCheckRecord.check_time >= start_date
    )
    
    # 增加平台筛选
    if platform:
        query = query.filter(IndexCheckRecord.platform == platform)
        
    # 按日期分组统计
    trends = query.group_by(
        func.date(IndexCheckRecord.check_time)
    ).order_by(
        func.date(IndexCheckRecord.check_time)
    ).all()

    # 转换为响应模型
    result = []
    for trend in trends:
        result.append(TrendDataPoint(
            date=str(trend.date),
            keyword_found_count=trend.keyword_found or 0,
            company_found_count=trend.company_found or 0,
            total_checks=trend.total_checks
        ))

    return result

@router.get("/stats", response_model=SummaryStats)
async def get_summary_stats(
    project_id: Optional[int] = Query(None),
    days: int = Query(7),
    db: Session = Depends(get_db)
):
    """获取数据总览卡片数据"""
    start_date = datetime.now() - timedelta(days=days)
    
    # 1. 文章生成数
    common_query = db.query(Article).filter(Article.created_at >= start_date)
    geo_query = db.query(GeoArticle).filter(GeoArticle.created_at >= start_date)
    
    if project_id:
        # Article表没有project_id，假设通过关键词关联（如果有的话），或者在此项目中不统计普通文章
        # 这里为了简化，如果指定了项目，普通文章数设为0，或者以后端模型关联为准
        # 根据模型，Article没有直接关联Project。GeoArticle有关联Keyword->Project
        geo_query = geo_query.join(Keyword).filter(Keyword.project_id == project_id)
        common_count = 0 
    else:
        common_count = common_query.count()
    
    geo_count = geo_query.count()
    total_articles = common_count + geo_count
    
    # 2. 发布成功率
    # 统计 PublishRecord (普通文章的发布记录)
    # 注意：Article 不关联 Project，所以如果指定了 project_id，普通文章的发布记录不计入
    if project_id:
        pr_total = 0
        pr_success = 0
    else:
        pr_query = db.query(PublishRecord).filter(PublishRecord.created_at >= start_date)
        pr_total = pr_query.count()
        pr_success = pr_query.filter(PublishRecord.publish_status == 2).count()
    
    # 统计 GeoArticle 的发布状态
    geo_pub_query = geo_query.filter(GeoArticle.publish_status == "published")
    geo_pub_total = geo_query.filter(GeoArticle.publish_status.in_(["published", "failed"])).count()
    geo_pub_success = geo_pub_query.count()
    
    total_pub_count = pr_total + geo_pub_total
    total_pub_success = pr_success + geo_pub_success
    pub_rate = round((total_pub_success / total_pub_count * 100), 2) if total_pub_count > 0 else 0
    
    # 3. 关键词/公司名命中率
    idx_query = db.query(IndexCheckRecord).filter(IndexCheckRecord.check_time >= start_date)
    if project_id:
        idx_query = idx_query.join(Keyword).filter(Keyword.project_id == project_id)
    
    idx_total = idx_query.count()
    kw_hit_count = idx_query.filter(IndexCheckRecord.keyword_found == True).count()
    co_hit_count = idx_query.filter(IndexCheckRecord.company_found == True).count()
    
    kw_rate = round((kw_hit_count / idx_total * 100), 2) if idx_total > 0 else 0
    co_rate = round((co_hit_count / idx_total * 100), 2) if idx_total > 0 else 0
    
    return SummaryStats(
        total_articles=total_articles,
        common_articles=common_count,
        geo_articles=geo_count,
        publish_success_rate=pub_rate,
        publish_success_count=total_pub_success,
        publish_total_count=total_pub_count,
        keyword_hit_rate=kw_rate,
        keyword_hit_count=kw_hit_count,
        keyword_check_count=idx_total,
        company_hit_rate=co_rate,
        company_hit_count=co_hit_count,
        company_check_count=idx_total
    )

@router.get("/platform-comparison", response_model=List[PlatformStat])
async def get_platform_comparison(
    project_id: Optional[int] = Query(None),
    days: int = Query(7),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """AI平台对比分析"""
    start_date = datetime.now() - timedelta(days=days)
    query = db.query(
        IndexCheckRecord.platform,
        func.count(IndexCheckRecord.id).label("total"),
        func.sum(cast(IndexCheckRecord.keyword_found, Integer)).label("kw_hits")
    ).filter(IndexCheckRecord.check_time >= start_date)

    if project_id:
        query = query.join(Keyword).filter(Keyword.project_id == project_id)

    if platform:
        query = query.filter(IndexCheckRecord.platform == platform)

    stats = query.group_by(IndexCheckRecord.platform).all()

    return [
        PlatformStat(
            platform=s.platform,
            total_count=s.total,
            hit_count=int(s.kw_hits or 0),
            hit_rate=round((int(s.kw_hits or 0) / s.total * 100), 2) if s.total > 0 else 0
        ) for s in stats
    ]

@router.get("/project-leaderboard", response_model=List[ProjectRank])
async def get_project_leaderboard(days: int = Query(7), db: Session = Depends(get_db)):
    """项目影响力排行榜"""
    start_date = datetime.now() - timedelta(days=days)
    projects = db.query(Project).filter(Project.status == 1).all()
    
    result = []
    for i, p in enumerate(projects):
        # 统计该项目的文章数
        content_volume = db.query(GeoArticle).join(Keyword).filter(
            Keyword.project_id == p.id,
            GeoArticle.created_at >= start_date
        ).count()
        
        # 统计收录率作为提及率参考
        idx_query = db.query(IndexCheckRecord).join(Keyword).filter(
            Keyword.project_id == p.id,
            IndexCheckRecord.check_time >= start_date
        )
        total_checks = idx_query.count()
        hits = idx_query.filter(IndexCheckRecord.keyword_found == True).count()
        mention_rate = round((hits / total_checks * 100), 2) if total_checks > 0 else 0
        
        result.append(ProjectRank(
            rank=i + 1,
            project_name=p.name,
            company_name=p.company_name,
            content_volume=content_volume,
            ai_mention_rate=mention_rate,
            brand_relevance=mention_rate # 暂时使用相同逻辑
        ))
    
    # 按提及率排序
    result.sort(key=lambda x: x.ai_mention_rate, reverse=True)
    for i, item in enumerate(result):
        item.rank = i + 1
        
    return result[:10]

@router.get("/content-analysis", response_model=List[ContentAnalysis])
async def get_content_analysis(
    project_id: Optional[int] = Query(None),
    days: int = Query(7),
    platform: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """高贡献内容分析"""
    start_date = datetime.now() - timedelta(days=days)

    # 结合 Geo只看已发布的
    query = db.query(GeoArticle).filter(GeoArticle.created_at >= start_date)
    if project_id:
        query = query.join(Keyword).filter(Keyword.project_id == project_id)

    if platform:
        query = query.filter(GeoArticle.platform == platform)

    articles = query.filter(GeoArticle.publish_status == "published").order_by(desc(GeoArticle.created_at)).limit(10).all()

    result = []
    for i, a in enumerate(articles):
        # 根据收录状态计算贡献度
        # 已收录90%，未收录10%
        contribution = 90.0 if a.index_status == "indexed" else 10.0

        result.append(ContentAnalysis(
            rank=i + 1,
            title=a.title or "无标题",
            platform=a.platform or "未知",
            ai_contribution=contribution,
            publish_time=a.publish_time.strftime("%Y-%m-%d %H:%M") if a.publish_time else None
        ))

    return result


@router.get("/overview")
async def get_overview(
    db: Session = Depends(get_db)
):
    """获取数据总览"""
    # 统计关键词数量
    total_keywords = db.query(Keyword).count()
    
    # 统计检测记录
    total_records = db.query(IndexCheckRecord).count()
    keyword_found = db.query(IndexCheckRecord).filter(IndexCheckRecord.keyword_found == True).count()
    company_found = db.query(IndexCheckRecord).filter(IndexCheckRecord.company_found == True).count()
    
    # 计算总体命中率
    overall_hit_rate = 0
    if total_records > 0:
        overall_hit_rate = round(((keyword_found + company_found) / (total_records * 2)) * 100, 2)
    
    return {
        "total_keywords": total_keywords,
        "keyword_found": keyword_found,
        "company_found": company_found,
        "overall_hit_rate": overall_hit_rate
    }
