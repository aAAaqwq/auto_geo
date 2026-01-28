# -*- coding: utf-8 -*-
"""
收录检测服务
用这个来检测AI平台的收录情况！
"""

from typing import List, Dict, Any, Optional
from loguru import logger
from sqlalchemy.orm import Session
from playwright.async_api import async_playwright, Browser

from backend.database.models import IndexCheckRecord, Keyword, QuestionVariant
from backend.config import AI_PLATFORMS
from backend.services.playwright.ai_platforms import DoubaoChecker, QianwenChecker, DeepSeekChecker


class IndexCheckService:
    """
    收录检测服务

    注意：这个服务负责AI平台收录检测！
    """

    def __init__(self, db: Session):
        """
        初始化收录检测服务

        Args:
            db: 数据库会话
        """
        self.db = db
        self.checkers = {
            "doubao": DoubaoChecker("doubao", AI_PLATFORMS["doubao"]),
            "qianwen": QianwenChecker("qianwen", AI_PLATFORMS["qianwen"]),
            "deepseek": DeepSeekChecker("deepseek", AI_PLATFORMS["deepseek"]),
        }

    async def check_keyword(
        self,
        keyword_id: int,
        company_name: str,
        platforms: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        检测关键词在所有AI平台的收录情况

        Args:
            keyword_id: 关键词ID
            company_name: 公司名称
            platforms: 要检测的平台列表，默认全部

        Returns:
            检测结果列表
        """
        # 获取关键词信息
        keyword_obj = self.db.query(Keyword).filter(Keyword.id == keyword_id).first()
        if not keyword_obj:
            logger.error(f"关键词不存在: {keyword_id}")
            return []

        # 获取问题变体
        questions = self.db.query(QuestionVariant).filter(
            QuestionVariant.keyword_id == keyword_id
        ).all()

        if not questions:
            # 如果没有问题变体，使用默认问题
            questions = [QuestionVariant(
                id=0,
                keyword_id=keyword_id,
                question=f"什么是{keyword_obj.keyword}？推荐哪家公司？"
            )]

        # 确定要检测的平台
        if platforms is None:
            platforms = list(self.checkers.keys())

        results = []

        # 使用Playwright进行检测
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            page = await context.new_page()

            try:
                for platform_id in platforms:
                    checker = self.checkers.get(platform_id)
                    if not checker:
                        logger.warning(f"未知的平台: {platform_id}")
                        continue

                    logger.info(f"开始检测平台: {checker.name}")

                    for qv in questions:
                        # 调用检测器
                        check_result = await checker.check(
                            page=page,
                            question=qv.question,
                            keyword=keyword_obj.keyword,
                            company=company_name
                        )

                        # 保存检测结果
                        record = IndexCheckRecord(
                            owner_id=keyword_obj.owner_id,
                            keyword_id=keyword_id,
                            platform=platform_id,
                            question=qv.question,
                            answer=check_result.get("answer"),
                            keyword_found=check_result.get("keyword_found", False),
                            company_found=check_result.get("company_found", False)
                        )
                        self.db.add(record)
                        self.db.commit()

                        results.append({
                            "platform": checker.name,
                            "question": qv.question,
                            "keyword_found": check_result.get("keyword_found", False),
                            "company_found": check_result.get("company_found", False),
                            "success": check_result.get("success", False)
                        })

            finally:
                await browser.close()

        logger.info(f"收录检测完成: 关键词ID={keyword_id}, 检测数={len(results)}")
        return results

    def get_check_records(
        self,
        keyword_id: Optional[int] = None,
        platform: Optional[str] = None,
        limit: int = 100
    ) -> List[IndexCheckRecord]:
        """
        获取检测记录

        Args:
            keyword_id: 关键词ID筛选
            platform: 平台筛选
            limit: 返回数量限制

        Returns:
            检测记录列表
        """
        query = self.db.query(IndexCheckRecord)

        if keyword_id:
            query = query.filter(IndexCheckRecord.keyword_id == keyword_id)
        if platform:
            query = query.filter(IndexCheckRecord.platform == platform)

        return query.order_by(IndexCheckRecord.check_time.desc()).limit(limit).all()

    def get_hit_rate(self, keyword_id: int) -> Dict[str, Any]:
        """
        计算关键词命中率

        Args:
            keyword_id: 关键词ID

        Returns:
            命中率统计
        """
        records = self.db.query(IndexCheckRecord).filter(
            IndexCheckRecord.keyword_id == keyword_id
        ).all()

        if not records:
            return {"hit_rate": 0, "total": 0, "keyword_found": 0, "company_found": 0}

        total = len(records)
        keyword_found = sum(1 for r in records if r.keyword_found)
        company_found = sum(1 for r in records if r.company_found)

        return {
            "hit_rate": round((keyword_found + company_found) / (total * 2) * 100, 2),
            "total": total,
            "keyword_found": keyword_found,
            "company_found": company_found
        }
