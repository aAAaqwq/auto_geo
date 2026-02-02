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


class User(Base):
    """
    用户表
    管理系统登录用户与角色
    """
    __tablename__ = "users"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    username = Column(String(100), unique=True, nullable=False, index=True, comment="用户名")
    email = Column(String(200), unique=True, nullable=True, index=True, comment="邮箱")
    password_hash = Column(String(200), nullable=False, comment="密码哈希")
    role = Column(String(20), default="user", comment="角色：admin/user")
    status = Column(String(20), default="active", comment="状态：active/disabled")
    last_login_at = Column(DateTime, nullable=True, comment="最后登录时间")

    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")

    def __repr__(self):
        return f"<User {self.username} role={self.role}>"


class RefreshToken(Base):
    """
    刷新令牌表
    用于会话管理与强制登出
    """
    __tablename__ = "refresh_tokens"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True, comment="用户ID")
    token_hash = Column(String(200), nullable=False, index=True, comment="刷新令牌哈希")
    expires_at = Column(DateTime, nullable=False, comment="过期时间")
    revoked_at = Column(DateTime, nullable=True, comment="撤销时间")
    ip = Column(String(100), nullable=True, comment="IP地址")
    user_agent = Column(String(500), nullable=True, comment="User-Agent")

    created_at = Column(DateTime, default=func.now(), comment="创建时间")


class AuditLog(Base):
    """
    审计日志表
    记录关键操作
    """
    __tablename__ = "audit_logs"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="用户ID")
    action = Column(String(100), nullable=False, comment="操作类型")
    target_type = Column(String(100), nullable=True, comment="目标类型")
    target_id = Column(String(100), nullable=True, comment="目标ID")
    meta = Column(Text, nullable=True, comment="扩展信息")
    created_at = Column(DateTime, default=func.now(), comment="创建时间")


class Account(Base):
    """
    账号表
    存储各平台账号信息和授权状态
    """
    __tablename__ = "accounts"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")

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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True, comment="所属用户ID")
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

# ==================== AI招聘候选人相关表 ====================

class Candidate(Base):
    """
    AI招聘候选人表
    存储n8n AI招聘流程筛选的候选人数据
    """
    __tablename__ = "candidates"
    __table_args__ = TABLE_ARGS

    id = Column(Integer, primary_key=True, autoincrement=True, comment="主键ID")
    uid = Column(String(100), unique=True, nullable=False, index=True, comment="候选人唯一标识（来自招聘平台）")
    detail = Column(Text, nullable=True, comment="候选人详细信息（JSON格式）")

    # 附件相关（修复拼写：attached 不是 attatched）
    attached = Column(Text, nullable=True, comment="附件信息（JSON格式，存储简历链接等）")

    # 发送状态
    is_send = Column(Boolean, default=False, comment="是否已发送文章/消息")

    # 关联文章（可选：如果发送了文章，记录文章ID）
    article_id = Column(Integer, ForeignKey("articles.id", ondelete="SET NULL"), nullable=True, comment="关联的文章ID")

    # 状态
    status = Column(Integer, default=1, comment="状态：1=有效 0=无效 -1=已删除")

    # 备注
    remark = Column(Text, nullable=True, comment="备注信息")

    # 时间戳
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
    sent_at = Column(DateTime, nullable=True, comment="发送时间")

    def __repr__(self):
        return f"<Candidate uid={self.uid} is_send={self.is_send}>"

