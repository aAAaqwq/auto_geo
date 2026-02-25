#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查文章真实状态
用于验证发布状态更新是否正确
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from backend.database import get_db
from backend.database.models import GeoArticle


def inspect_article(article_id: int = 1):
    """检查指定文章的状态信息"""
    db = next(get_db())
    try:
        article = db.query(GeoArticle).filter(GeoArticle.id == article_id).first()

        print("\n" + "=" * 60)
        print(f"文章 ID: {article.id}")
        print(f"文章标题: {article.title}")
        print("=" * 60)
        print(f"publish_status: {article.publish_status}")
        print(f"platform: {article.platform}")
        print(f"account_id: {article.account_id}")
        print(f"project_id: {article.project_id}")
        print(f"error_msg: {article.error_msg}")
        print("=" * 60)

        # 检查 publish_status 的具体值
        if article.publish_status == "failed":
            print("✅ 数据库中的 publish_status 确实是 'failed' - UI 应该立即变红！")
        elif article.publish_status is None:
            print("⚠️  publish_status 为 None")
        else:
            print(f"⚠️  publish_status 值为: '{article.publish_status}'")

        if article.publish_status == "failed" and article.error_msg:
            print(f"✅ 失败原因: {article.error_msg}")
    except Exception as e:
        print(f"❌ 查询失败: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="检查文章状态")
    parser.add_argument("--id", type=int, default=1, help="文章ID")
    args = parser.parse_args()

    print("\n")
    print("🔍 开始检查文章状态...")
    print("=" * 60)
    inspect_article(args.id)
    print("=" * 60)
