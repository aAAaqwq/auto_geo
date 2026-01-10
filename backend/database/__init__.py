# -*- coding: utf-8 -*-
"""
数据库连接管理
老王我写的东西，简单但够用！
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import DATABASE_DIR, DATABASE_URL

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
    老王提醒：用完自动关闭，别tm搞内存泄漏！
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    初始化数据库表
    老王提醒：第一次运行时调用！
    """
    from .models import Account, Article, PublishRecord  # noqa: F401
    Base.metadata.create_all(bind=engine)
