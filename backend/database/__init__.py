# -*- coding: utf-8 -*-
"""
数据库连接管理
写的东西，简单但够用！
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from backend.config import DATABASE_DIR, DATABASE_URL

# 确保数据库目录存在
DATABASE_DIR.mkdir(exist_ok=True)

# 创建引擎
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite特有配置
    echo=False,  # 生产环境设为False
    pool_pre_ping=True,  # 连接健康检查
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 基类
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话的依赖注入函数
    注意：用完自动关闭，！
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表
    注意：第一次运行时调用！
    """
    from .models import (
        User, RefreshToken, AuditLog,
        Account, Article, PublishRecord,
        Project, Keyword, QuestionVariant,
        IndexCheckRecord, GeoArticle,
        KnowledgeCategory, Knowledge
    )  # noqa: F401
    from loguru import logger
    from sqlalchemy import inspect

    # 获取已存在的表
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # 创建所有表（SQLAlchemy会自动处理外键依赖顺序）
    try:
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("数据库表创建完成")
    except Exception as e:
        error_str = str(e).lower()
        if "already exists" in error_str:
            logger.info(f"部分表已存在，继续创建")

    # 输出创建结果
    inspector = inspect(engine)
    all_tables = inspector.get_table_names()
    for table in all_tables:
        if table not in existing_tables:
            logger.info(f"表 {table} 创建成功")
        else:
            logger.info(f"表 {table} 已存在")
