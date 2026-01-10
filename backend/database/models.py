# -*- coding: utf-8 -*-
"""
数据模型定义
老王我用SQLAlchemy ORM，类型安全！
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from database import Base


class Account(Base):
    """
    账号表
    存储各平台账号信息和授权状态
    """
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    platform = Column(String(50), nullable=False, index=True, comment="平台ID：zhihu/baijiahao/sohu/toutiao")
    account_name = Column(String(100), nullable=False, comment="账号备注名称")
    username = Column(String(100), nullable=True, comment="登录账号/用户名")

    # 授权相关（加密存储）
    cookies = Column(Text, nullable=True, comment="加密的Cookies")
    storage_state = Column(Text, nullable=True, comment="加密的本地存储状态")
    user_agent = Column(String(500), nullable=True, comment="浏览器UA")

    # 状态相关
    status = Column(Integer, default=1, comment="账号状态：1=正常 0=禁用 -1=授权过期")
    last_auth_time = Column(DateTime, nullable=True, comment="最后授权时间")

    # 备注
    remark = Column(Text, nullable=True, comment="备注信息")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Account {self.platform}:{self.account_name}>"


class Article(Base):
    """
    文章表
    存储文章内容和基本信息
    """
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    title = Column(String(200), nullable=False, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章正文内容（Markdown/HTML）")

    # 标签和分类
    tags = Column(String(500), nullable=True, comment="标签，逗号分隔")
    category = Column(String(100), nullable=True, comment="文章分类")

    # 封面图
    cover_image = Column(String(500), nullable=True, comment="封面图片URL")

    # 状态
    status = Column(Integer, default=0, comment="状态：0=草稿 1=已发布")

    # 统计
    view_count = Column(Integer, default=0, comment="查看次数")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    published_at = Column(DateTime, nullable=True, comment="首次发布时间")

    def __repr__(self):
        return f"<Article {self.title}>"


class PublishRecord(Base):
    """
    发布记录表
    记录文章到各平台的发布状态
    """
    __tablename__ = "publish_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 外键
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="CASCADE"), nullable=False, index=True, comment="文章ID")
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, index=True, comment="账号ID")

    # 发布状态
    publish_status = Column(
        Integer,
        default=0,
        comment="发布状态：0=待发布 1=发布中 2=成功 3=失败"
    )

    # 结果
    platform_url = Column(String(500), nullable=True, comment="发布后的文章链接")
    error_msg = Column(Text, nullable=True, comment="错误信息")

    # 重试
    retry_count = Column(Integer, default=0, comment="重试次数")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    published_at = Column(DateTime, nullable=True, comment="实际发布时间")

    def __repr__(self):
        return f"<PublishRecord article_id={self.article_id} account_id={self.account_id} status={self.publish_status}>"
