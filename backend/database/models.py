# -*- coding: utf-8 -*-
"""
数据模型定义
用SQLAlchemy ORM，类型安全！
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, func, ForeignKey
from sqlalchemy.orm import relationship
from backend.database import Base

# 表参数：允许扩展现有表
TABLE_ARGS = {"extend_existing": True}


class Account(Base):
    """
    账号表
    存储各平台账号信息和授权状态
    """
    __tablename__ = "accounts"
    __table_args__ = TABLE_ARGS

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
    __table_args__ = TABLE_ARGS

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
    __table_args__ = TABLE_ARGS

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


# ==================== GEO相关表 ====================

class Project(Base):
    """
    项目表
    存储客户/项目信息
    """
    __tablename__ = "projects"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="项目名称")
    company_name = Column(String(200), nullable=False, comment="公司名称")
    domain_keyword = Column(String(200), nullable=True, comment="领域关键词，用于关键词蒸馏")
    description = Column(Text, nullable=True, comment="项目描述")
    industry = Column(String(100), nullable=True, comment="行业")

    # 状态
    status = Column(Integer, default=1, comment="状态：1=活跃 0=停用")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Project {self.name}>"


class Keyword(Base):
    """
    关键词表
    存储AI分析出的高价值关键词
    """
    __tablename__ = "keywords"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True, comment="项目ID")
    keyword = Column(String(200), nullable=False, comment="关键词")
    difficulty_score = Column(Integer, nullable=True, comment="难度评分（0-100）")

    # 状态
    status = Column(String(20), default="active", comment="状态：active=活跃 inactive=停用")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<Keyword {self.keyword}>"


class QuestionVariant(Base):
    """
    问题变体表
    存储基于关键词生成的不同问法
    """
    __tablename__ = "question_variants"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False, index=True, comment="关键词ID")
    question = Column(Text, nullable=False, comment="问题变体")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")

    def __repr__(self):
        return f"<QuestionVariant {self.question[:30]}...>"


class IndexCheckRecord(Base):
    """
    收录检测记录表
    存储AI平台收录检测结果
    """
    __tablename__ = "index_check_records"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False, index=True, comment="关键词ID")
    platform = Column(String(50), nullable=False, comment="检测平台：doubao/qianwen/deepseek")
    question = Column(Text, nullable=False, comment="检测时使用的问题")
    answer = Column(Text, nullable=True, comment="AI回答内容")

    # 检测结果
    keyword_found = Column(Boolean, nullable=True, comment="是否包含关键词")
    company_found = Column(Boolean, nullable=True, comment="是否包含公司名")

    # 时间戳
    check_time = Column(DateTime, default=func.now(), comment="检测时间")

    def __repr__(self):
        return f"<IndexCheckRecord keyword_id={self.keyword_id} platform={self.platform}>"


class GeoArticle(Base):
    """
    GEO文章表
    存储AI生成的文章及质检信息
    """
    __tablename__ = "geo_articles"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    keyword_id = Column(Integer, ForeignKey("keywords.id", ondelete="CASCADE"), nullable=False, index=True, comment="关键词ID")
    title = Column(Text, nullable=True, comment="文章标题")
    content = Column(Text, nullable=False, comment="文章正文内容")

    # 质检相关
    quality_score = Column(Integer, nullable=True, comment="质量评分（0-100）")
    ai_score = Column(Integer, nullable=True, comment="AI味检测分数（0-100，越高越像AI）")
    readability_score = Column(Integer, nullable=True, comment="可读性评分（0-100）")
    quality_status = Column(String(20), default="pending", comment="质检状态：pending=待检查 passed=通过 failed=未通过")

    # 发布相关
    platform = Column(String(50), nullable=True, comment="目标发布平台")
    publish_status = Column(String(20), default="draft", comment="发布状态：draft=草稿 published=已发布 failed=发布失败")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<GeoArticle id={self.id} keyword_id={self.keyword_id}>"


# ==================== 知识库相关表 ====================

class KnowledgeCategory(Base):
    """
    知识库分类表（企业分类）
    存储企业/客户的知识库分类信息
    """
    __tablename__ = "knowledge_categories"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    name = Column(String(200), nullable=False, comment="企业/分类名称")
    industry = Column(String(100), nullable=True, comment="所属行业")
    description = Column(Text, nullable=True, comment="分类描述")
    tags = Column(String(500), nullable=True, comment="标签，逗号分隔")
    color = Column(String(20), default="#6366f1", comment="主题颜色")

    # 状态
    status = Column(Integer, default=1, comment="状态：1=活跃 0=停用")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<KnowledgeCategory {self.name}>"


class Knowledge(Base):
    """
    知识库条目表
    存储企业相关的知识内容
    """
    __tablename__ = "knowledge_items"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    category_id = Column(Integer, ForeignKey("knowledge_categories.id", ondelete="CASCADE"), nullable=False, index=True, comment="分类ID")
    title = Column(String(200), nullable=False, comment="知识标题")
    content = Column(Text, nullable=False, comment="知识内容")
    type = Column(String(50), default="other", comment="知识类型：company_intro=企业介绍 product=产品服务 industry=行业知识 faq=常见问题 other=其他")

    # 状态
    status = Column(Integer, default=1, comment="状态：1=启用 0=停用")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<Knowledge {self.title}>"


# ==================== 参考文章表（爆火文章收集）====================

class ReferenceArticle(Base):
    """
    参考文章表
    存储从各平台采集的爆火/热门文章，用于内容创作参考
    """
    __tablename__ = "reference_articles"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")

    # 基本信息
    title = Column(String(500), nullable=False, comment="文章标题")
    url = Column(String(1000), nullable=False, unique=True, comment="原文链接")
    content = Column(Text, nullable=False, comment="文章正文（已清洗）")
    summary = Column(Text, nullable=True, comment="文章摘要")

    # 来源信息
    platform = Column(String(50), nullable=False, index=True, comment="来源平台：zhihu/toutiao等")
    author = Column(String(200), nullable=True, comment="作者名称")
    publish_time = Column(String(50), nullable=True, comment="原文发布时间")

    # 热度指标
    likes = Column(Integer, default=0, comment="点赞数")
    reads = Column(Integer, default=0, comment="阅读量")
    comments = Column(Integer, default=0, comment="评论数")

    # 采集信息
    keyword = Column(String(200), nullable=True, index=True, comment="采集时使用的关键词")
    collected_at = Column(DateTime, default=func.now(), comment="采集时间")

    # RAGFlow 同步状态
    ragflow_synced = Column(Boolean, default=False, comment="是否已同步到RAGFlow")
    ragflow_doc_id = Column(String(100), nullable=True, comment="RAGFlow文档ID")
    ragflow_sync_time = Column(DateTime, nullable=True, comment="RAGFlow同步时间")

    # 状态
    status = Column(Integer, default=1, comment="状态：1=正常 0=已删除")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<ReferenceArticle {self.title[:30]}... ({self.platform})>"
