# -*- coding: utf-8 -*-
"""
数据报表功能测试
验证全面化数据报表系统的各项功能
"""

import pytest
import requests
from datetime import datetime, timedelta


# 测试基础URL
BASE_URL = "http://127.0.0.1:8001"


@pytest.mark.monitor
@pytest.mark.usefixtures("backend_server")
class TestReports:
    """数据报表功能测试类"""

    def test_comprehensive_overview(self, clean_db, test_project):
        """测试全面数据概览接口"""
        response = requests.get(f"{BASE_URL}/api/reports/comprehensive")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证返回数据结构
        assert "total_articles" in data
        assert "total_geo_articles" in data
        assert "total_articles_generated" in data
        assert "geo_articles_passed" in data
        assert "geo_articles_failed" in data
        assert "total_publish_records" in data
        assert "publish_success" in data
        assert "publish_failed" in data
        assert "publish_pending" in data
        assert "publish_success_rate" in data
        assert "total_checks" in data
        assert "keyword_found" in data
        assert "company_found" in data
        assert "keyword_hit_rate" in data
        assert "company_hit_rate" in data
        assert "total_projects" in data
        assert "total_keywords" in data
        assert "active_keywords" in data
        
        # 验证数据类型
        assert isinstance(data["total_articles"], int)
        assert isinstance(data["total_geo_articles"], int)
        assert isinstance(data["publish_success_rate"], float)
        assert isinstance(data["keyword_hit_rate"], float)
        assert isinstance(data["company_hit_rate"], float)

    def test_comprehensive_overview_with_project_filter(self, clean_db, test_project):
        """测试带项目筛选的全面数据概览"""
        response = requests.get(f"{BASE_URL}/api/reports/comprehensive", params={
            "project_id": test_project.id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "total_articles" in data
        assert "total_keywords" in data

    def test_daily_trends(self, clean_db):
        """测试每日趋势数据接口"""
        response = requests.get(f"{BASE_URL}/api/reports/daily-trends", params={
            "days": 7
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证返回7天的数据
        assert len(data) <= 7
        
        # 验证数据结构
        if len(data) > 0:
            trend = data[0]
            assert "date" in trend
            assert "articles_generated" in trend
            assert "articles_published" in trend
            assert "publish_success" in trend
            assert "index_checks" in trend
            assert "keyword_hits" in trend

    def test_daily_trends_with_project_filter(self, clean_db, test_project):
        """测试带项目筛选的每日趋势数据"""
        response = requests.get(f"{BASE_URL}/api/reports/daily-trends", params={
            "days": 30,
            "project_id": test_project.id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 30

    def test_platform_comparison(self, clean_db):
        """测试平台对比分析接口"""
        response = requests.get(f"{BASE_URL}/api/reports/platform-comparison", params={
            "days": 30
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证返回3个平台的数据
        assert len(data) <= 3
        
        # 验证数据结构
        if len(data) > 0:
            platform = data[0]
            assert "platform" in platform
            assert "platform_name" in platform
            assert "daily_data" in platform
            assert isinstance(platform["daily_data"], list)
            
            # 验证每日数据结构
            if len(platform["daily_data"]) > 0:
                daily = platform["daily_data"][0]
                assert "date" in daily
                assert "total_checks" in daily
                assert "keyword_hits" in daily
                assert "hit_rate" in daily

    def test_platform_comparison_with_project_filter(self, clean_db, test_project):
        """测试带项目筛选的平台对比分析"""
        response = requests.get(f"{BASE_URL}/api/reports/platform-comparison", params={
            "days": 7,
            "project_id": test_project.id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_project_comparison(self, clean_db, test_project):
        """测试项目对比分析接口"""
        response = requests.get(f"{BASE_URL}/api/reports/project-comparison", params={
            "days": 30
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证数据结构
        if len(data) > 0:
            project = data[0]
            assert "project_id" in project
            assert "project_name" in project
            assert "company_name" in project
            assert "daily_data" in project
            assert isinstance(project["daily_data"], list)
            
            # 验证每日数据结构
            if len(project["daily_data"]) > 0:
                daily = project["daily_data"][0]
                assert "date" in daily
                assert "total_checks" in daily
                assert "keyword_hits" in daily
                assert "hit_rate" in daily

    def test_project_comparison_with_project_ids(self, clean_db, test_project):
        """测试指定项目ID的项目对比分析"""
        response = requests.get(f"{BASE_URL}/api/reports/project-comparison", params={
            "days": 30,
            "project_ids": str(test_project.id)
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_top_projects(self, clean_db):
        """测试项目TOP排行榜接口"""
        response = requests.get(f"{BASE_URL}/api/reports/top-projects", params={
            "limit": 10
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
        
        # 验证数据结构
        if len(data) > 0:
            project = data[0]
            assert "project_id" in project
            assert "project_name" in project
            assert "company_name" in project
            assert "total_keywords" in project
            assert "total_checks" in project
            assert "keyword_hit_rate" in project
            assert "company_hit_rate" in project
            assert "total_articles" in project
            assert "total_publish" in project
            
            # 验证排序（按关键词命中率降序）
            if len(data) > 1:
                assert data[0]["keyword_hit_rate"] >= data[1]["keyword_hit_rate"]

    def test_top_projects_with_project_filter(self, clean_db, test_project):
        """测试带项目筛选的TOP排行榜"""
        response = requests.get(f"{BASE_URL}/api/reports/top-projects", params={
            "limit": 5,
            "project_id": test_project.id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)

    def test_projects_stats(self, clean_db, test_project):
        """测试项目统计数据接口"""
        response = requests.get(f"{BASE_URL}/api/reports/projects")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证数据结构
        if len(data) > 0:
            project = data[0]
            assert "project_id" in project
            assert "project_name" in project
            assert "company_name" in project
            assert "total_keywords" in project
            assert "active_keywords" in project
            assert "total_questions" in project
            assert "total_checks" in project
            assert "keyword_hit_rate" in project
            assert "company_hit_rate" in project

    def test_platforms_stats(self, clean_db):
        """测试平台统计数据接口"""
        response = requests.get(f"{BASE_URL}/api/reports/platforms")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证返回3个平台的数据
        assert len(data) <= 3
        
        # 验证数据结构
        if len(data) > 0:
            platform = data[0]
            assert "platform" in platform
            assert "total_checks" in platform
            assert "keyword_found" in platform
            assert "company_found" in platform
            assert "keyword_hit_rate" in platform
            assert "company_hit_rate" in platform

    def test_trends(self, clean_db):
        """测试收录趋势数据接口"""
        response = requests.get(f"{BASE_URL}/api/reports/trends", params={
            "days": 30
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        # 验证数据结构
        if len(data) > 0:
            trend = data[0]
            assert "date" in trend
            assert "keyword_found_count" in trend
            assert "company_found_count" in trend
            assert "total_checks" in trend

    def test_overview(self, clean_db):
        """测试总体概览数据接口"""
        response = requests.get(f"{BASE_URL}/api/reports/overview")
        assert response.status_code == 200
        
        data = response.json()
        
        # 验证返回数据结构
        assert "total_projects" in data
        assert "total_keywords" in data
        assert "total_checks" in data
        assert "keyword_found" in data
        assert "company_found" in data
        assert "overall_hit_rate" in data
        
        # 验证数据类型
        assert isinstance(data["total_projects"], int)
        assert isinstance(data["total_keywords"], int)
        assert isinstance(data["total_checks"], int)
        # overall_hit_rate 可能是 int (0) 或 float (有数据时)
        assert isinstance(data["overall_hit_rate"], (int, float))

    def test_days_parameter_validation(self, clean_db):
        """测试days参数验证"""
        # 测试超出范围的days参数
        response = requests.get(f"{BASE_URL}/api/reports/daily-trends", params={
            "days": 100
        })
        # 应该返回422错误（参数验证失败）
        assert response.status_code == 422

    def test_empty_data_handling(self, clean_db):
        """测试空数据处理"""
        # 清空文章数据（因为其他测试可能生成了数据，且 clean_db 是 function 级别的，
        # 但有些数据可能是通过其他进程或手动插入的，这里确保清理干净）
        from backend.database.models import GeoArticle, Article, PublishRecord, IndexCheckRecord
        clean_db.query(PublishRecord).delete()
        clean_db.query(IndexCheckRecord).delete()
        clean_db.query(GeoArticle).delete()
        clean_db.query(Article).delete()
        clean_db.commit()

        # 在空数据库中测试
        response = requests.get(f"{BASE_URL}/api/reports/comprehensive")
        assert response.status_code == 200
        
        data = response.json()
        # 验证空数据时返回0值
        assert data["total_articles"] == 0
        assert data["total_geo_articles"] == 0
        assert data["total_publish_records"] == 0
        assert data["total_checks"] == 0

    def test_comprehensive_overview_publish_filter_logic(self, clean_db, test_project):
        """测试全面概览中发布数据的项目筛选逻辑（验证当前已知限制）"""
        response = requests.get(f"{BASE_URL}/api/reports/comprehensive", params={
            "project_id": test_project.id
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_publish_records" in data

    def test_project_comparison_invalid_ids(self, clean_db):
        """测试项目对比接口参数校验：非法ID格式"""
        response = requests.get(f"{BASE_URL}/api/reports/project-comparison", params={
            "days": 30,
            "project_ids": "invalid,ids"
        })
        # 期望返回 422 错误
        assert response.status_code == 422

    def test_top_articles(self, clean_db):
        """测试高贡献文章列表接口"""
        response = requests.get(f"{BASE_URL}/api/reports/top-articles", params={
            "limit": 10
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10
        
        # 验证数据结构
        if len(data) > 0:
            article = data[0]
            assert "article_id" in article
            assert "title" in article
            assert "platform" in article
            assert "created_at" in article
            assert "keyword_hit_rate" in article
            assert "last_check_status" in article
            
            # 验证排序（按命中率降序）
            if len(data) > 1:
                assert data[0]["keyword_hit_rate"] >= data[1]["keyword_hit_rate"]

    def test_top_articles_with_project_filter(self, clean_db, test_project):
        """测试带项目筛选的高贡献文章列表"""
        response = requests.get(f"{BASE_URL}/api/reports/top-articles", params={
            "limit": 5,
            "project_id": test_project.id
        })
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
