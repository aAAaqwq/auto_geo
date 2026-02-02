# -*- coding: utf-8 -*-
"""
定时任务API
写的定时任务API，管理定时检测！
"""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, BackgroundTasks, Body
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.services.scheduler_service import get_scheduler_service
from backend.schemas import ApiResponse
from backend.services.auth import require_role
from loguru import logger


router = APIRouter(prefix="/api/scheduler", tags=["定时任务"], dependencies=[Depends(require_role("admin"))])


# ==================== 响应模型 ====================

class JobInfo(BaseModel):
    """任务信息"""
    id: str
    name: str
    next_run_time: str | None


class JobConfig(BaseModel):
    """任务配置"""
    enabled: bool
    schedule_type: str  # daily, weekly, weekdays
    time: str  # HH:mm
    project_id: Optional[int] = None
    count: Optional[int] = None
    platforms: Optional[List[str]] = None
    concurrency: Optional[int] = None


class JobConfigRequest(BaseModel):
    """任务配置请求"""
    article_gen: Optional[JobConfig] = None
    index_check: Optional[JobConfig] = None
    article_publish: Optional[JobConfig] = None


# 全局服务实例
_scheduler_service = None


def get_scheduler():
    """获取定时任务服务"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = get_scheduler_service()
        # 设置数据库工厂
        _scheduler_service.set_db_factory(lambda: get_db().__next__())
    return _scheduler_service


# ==================== 定时任务配置存储 ====================
# 简单内存存储（后续可改为数据库存储）
_job_configs: Dict[str, JobConfig] = {
    "article_gen": JobConfig(
        enabled=False,
        schedule_type="daily",
        time="09:00",
        count=5
    ),
    "index_check": JobConfig(
        enabled=True,
        schedule_type="daily",
        time="02:00",
        platforms=["doubao", "qianwen", "deepseek"],
        concurrency=3
    ),
    "article_publish": JobConfig(
        enabled=False,
        schedule_type="weekdays",
        time="10:00",
        platforms=["zhihu", "baijiahao"],
        count=3
    ),
}


# ==================== 定时任务API ====================

@router.get("/jobs", response_model=List[JobInfo])
async def get_scheduled_jobs():
    """
    获取所有定时任务

    注意：返回所有已配置的定时任务！
    """
    scheduler = get_scheduler()
    jobs = scheduler.get_scheduled_jobs()
    return jobs


@router.get("/config", response_model=Dict[str, JobConfig])
async def get_job_configs():
    """
    获取所有任务配置

    注意：返回所有任务的配置信息！
    """
    return _job_configs


@router.post("/config", response_model=ApiResponse)
async def update_job_configs(
    data: JobConfigRequest,
    background_tasks: BackgroundTasks
):
    """
    更新任务配置

    注意：更新任务配置后需要重启服务！
    """
    global _job_configs

    try:
        # 更新配置
        if data.article_gen is not None:
            _job_configs["article_gen"] = data.article_gen
        if data.index_check is not None:
            _job_configs["index_check"] = data.index_check
        if data.article_publish is not None:
            _job_configs["article_publish"] = data.article_publish

        # TODO: 保存到数据库或配置文件
        # TODO: 如果服务正在运行，需要动态更新任务

        return ApiResponse(success=True, message="任务配置已更新")
    except Exception as e:
        logger.error(f"更新任务配置失败: {e}")
        return ApiResponse(success=False, message=f"更新失败: {str(e)}")


@router.post("/config/{job_type}", response_model=ApiResponse)
async def update_single_job_config(
    job_type: str,
    config: JobConfig,
    background_tasks: BackgroundTasks
):
    """
    更新单个任务配置

    Args:
        job_type: 任务类型 (article_gen, index_check, article_publish)
        config: 任务配置

    注意：更新单个任务的配置！
    """
    global _job_configs

    if job_type not in _job_configs:
        return ApiResponse(success=False, message=f"未知的任务类型: {job_type}")

    try:
        _job_configs[job_type] = config
        return ApiResponse(success=True, message=f"{job_type} 配置已更新")
    except Exception as e:
        logger.error(f"更新任务配置失败: {e}")
        return ApiResponse(success=False, message=f"更新失败: {str(e)}")


@router.post("/trigger-check", response_model=ApiResponse)
async def trigger_index_check(background_tasks: BackgroundTasks):
    """
    手动触发收录检测任务

    注意：用于立即执行检测，无需等到定时时间！
    """
    scheduler = get_scheduler()
    background_tasks.add_task(scheduler.trigger_check_now)
    return ApiResponse(success=True, message="收录检测任务已触发")


@router.post("/trigger-article-gen", response_model=ApiResponse)
async def trigger_article_gen(
    project_id: int = Body(..., embed=True),
    count: int = Body(5, embed=True),
    background_tasks: BackgroundTasks = None
):
    """
    手动触发文章生成任务

    Args:
        project_id: 项目ID
        count: 生成数量

    注意：用于立即执行文章生成！
    """
    # TODO: 实现文章生成触发逻辑
    return ApiResponse(success=True, message="文章生成任务已触发")


@router.post("/trigger-alert", response_model=ApiResponse)
async def trigger_alert_check(background_tasks: BackgroundTasks):
    """
    手动触发预警检查任务

    注意：用于立即检查预警！
    """
    scheduler = get_scheduler()
    background_tasks.add_task(scheduler.trigger_alert_now)
    return ApiResponse(success=True, message="预警检查任务已触发")


@router.get("/status")
async def get_scheduler_status():
    """
    获取定时任务服务状态

    注意：检查服务是否正在运行！
    """
    scheduler = get_scheduler()
    return {
        "running": scheduler.scheduler.running if scheduler else False,
        "job_count": len(scheduler.get_scheduled_jobs()) if scheduler else 0,
        "configs": _job_configs
    }


@router.post("/start", response_model=ApiResponse)
async def start_scheduler():
    """
    启动定时任务服务

    注意：服务会在应用启动时自动启动！
    """
    scheduler = get_scheduler()
    if scheduler.scheduler.running:
        return ApiResponse(success=True, message="服务已在运行中")

    try:
        scheduler.start()
        return ApiResponse(success=True, message="定时任务服务已启动")
    except Exception as e:
        logger.error(f"启动定时任务服务失败: {e}")
        return ApiResponse(success=False, message=f"启动失败: {str(e)}")


@router.post("/stop", response_model=ApiResponse)
async def stop_scheduler():
    """
    停止定时任务服务

    注意：停止后定时任务将不再执行！
    """
    scheduler = get_scheduler()
    if not scheduler.scheduler.running:
        return ApiResponse(success=True, message="服务已停止")

    try:
        scheduler.stop()
        return ApiResponse(success=True, message="定时任务服务已停止")
    except Exception as e:
        logger.error(f"停止定时任务服务失败: {e}")
        return ApiResponse(success=False, message=f"停止失败: {str(e)}")
