# -*- coding: utf-8 -*-
"""
关键词服务
用这个来处理关键词蒸馏和问题生成！
"""

from typing import Any, Dict, List, Optional
from loguru import logger
from sqlalchemy.orm import Session

from backend.database.models import Project, Keyword, QuestionVariant
from backend.services.n8n_client import get_n8n_client


class KeywordService:
    """
    关键词服务

    注意：这个服务负责与n8n交互完成关键词分析！
    """

    def __init__(self, db: Session):
        """
        初始化关键词服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.n8n = get_n8n_client()

    async def distill(
        self,
        company_name: str,
        industry: str,
        description: str,
        count: int = 10,
        core_kw: Optional[str] = None,
        prefixes: Optional[str] = None,
        suffixes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        蒸馏关键词

        Args:
            company_name: 公司名称
            industry: 行业
            description: 公司描述
            count: 返回关键词数量

        Returns:
            包含关键词列表的字典
        """
        logger.info(
            f"开始关键词蒸馏: company={company_name}, core_kw={core_kw or industry}, "
            f"industry={industry or ''}, description_len={len(description or '')}, "
            f"count={count}, prefixes={prefixes or ''}, suffixes={suffixes or ''}"
        )
        payload = {
            "core_kw": core_kw or industry or "",
            "target_info": company_name or "",
            "prefixes": prefixes or "",
            "suffixes": suffixes or "",
            "title_hint": ""
        }
        logger.info(f"蒸馏调用参数: {payload}")
        result = await self.n8n.call("keyword-distill", payload)

        if result.get("status") == "error":
            return {"status": "error", "message": result.get("message"), "keywords": []}

        extracted: List[str] = []
        if isinstance(result.get("data"), list):
            extracted = [str(x).strip() for x in result.get("data") if str(x).strip()]
        elif isinstance(result.get("data"), dict):
            core = result["data"].get("core_keywords") or []
            long_tail = result["data"].get("long_tail_keywords") or []
            combined = list(core) + list(long_tail)
            extracted = [str(x).strip() for x in combined if str(x).strip()]
        elif "keywords" in result:
            raw = result.get("keywords") or []
            extracted = [str(x).strip() for x in raw if str(x).strip()]

        seen = set()
        deduped = []
        for k in extracted:
            if k not in seen:
                seen.add(k)
                deduped.append(k)

        if count and isinstance(count, int) and count > 0:
            deduped = deduped[:count]

        keywords_output = [{"keyword": k} for k in deduped]
        return {"status": "success", "keywords": keywords_output}

    async def generate_questions(
        self,
        keyword: str,
        count: int = 3
    ) -> List[str]:
        """
        生成问题变体

        Args:
            keyword: 关键词
            count: 生成问题数量

        Returns:
            问题列表
        """
        logger.info(f"生成问题变体: {keyword}")

        result = await self.n8n.call("generate-questions", {
            "keyword": keyword,
            "count": count
        })

        questions = result.get("questions", [])
        logger.info(f"问题变体生成完成，共{len(questions)}个问题")
        return questions

    def create_project(
        self,
        name: str,
        company_name: str,
        description: Optional[str] = None,
        industry: Optional[str] = None
    ) -> Project:
        """
        创建项目

        Args:
            name: 项目名称
            company_name: 公司名称
            description: 项目描述
            industry: 行业

        Returns:
            创建的项目对象
        """
        project = Project(
            name=name,
            company_name=company_name,
            description=description,
            industry=industry
        )
        self.db.add(project)
        self.db.commit()
        self.db.refresh(project)
        logger.info(f"项目已创建: {project.name}")
        return project

    def add_keyword(
        self,
        project_id: int,
        keyword: str,
        difficulty_score: Optional[int] = None
    ) -> Keyword:
        """
        添加关键词

        Args:
            project_id: 项目ID
            keyword: 关键词
            difficulty_score: 难度评分

        Returns:
            创建的关键词对象
        """
        kw = Keyword(
            project_id=project_id,
            keyword=keyword,
            difficulty_score=difficulty_score
        )
        self.db.add(kw)
        self.db.commit()
        self.db.refresh(kw)
        logger.info(f"关键词已添加: {kw.keyword}")
        return kw

    def add_question_variant(
        self,
        keyword_id: int,
        question: str
    ) -> QuestionVariant:
        """
        添加问题变体

        Args:
            keyword_id: 关键词ID
            question: 问题

        Returns:
            创建的问题变体对象
        """
        qv = QuestionVariant(
            keyword_id=keyword_id,
            question=question
        )
        self.db.add(qv)
        self.db.commit()
        self.db.refresh(qv)
        logger.info(f"问题变体已添加: {qv.question[:30]}...")
        return qv

    def get_project_keywords(self, project_id: int) -> List[Keyword]:
        """
        获取项目的所有关键词

        Args:
            project_id: 项目ID

        Returns:
            关键词列表
        """
        return self.db.query(Keyword).filter(
            Keyword.project_id == project_id,
            Keyword.status == "active"
        ).all()

    def get_keyword_questions(self, keyword_id: int) -> List[QuestionVariant]:
        """
        获取关键词的所有问题变体

        Args:
            keyword_id: 关键词ID

        Returns:
            问题变体列表
        """
        return self.db.query(QuestionVariant).filter(
            QuestionVariant.keyword_id == keyword_id
        ).all()

    def list_projects(self) -> List[Project]:
        """
        列出所有项目

        Returns:
            项目列表
        """
        return self.db.query(Project).filter(Project.status == 1).all()
