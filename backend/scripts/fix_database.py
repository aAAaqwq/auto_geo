#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库修复脚本
添加缺少的列到现有数据库表
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text, inspect
from backend.config import DATABASE_URL
from backend.database.models import Base

def add_column_if_not_exists(engine, table_name, column_name, column_definition):
    """如果列不存在，则添加该列"""
    try:
        # 检查列是否已存在
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        
        if column_name in columns:
            print(f"  ✓ 列 '{column_name}' 已存在于表 '{table_name}' 中")
            return True
        
        # 添加列
        with engine.connect() as conn:
            conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_definition}"))
            conn.commit()
        
        print(f"  ✓ 成功添加列 '{column_name}' 到表 '{table_name}'")
        return True
        
    except Exception as e:
        print(f"  ✗ 添加列 '{column_name}' 失败: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("数据库修复工具")
    print("=" * 60)
    print()
    
    # 创建数据库引擎
    db_path = DATABASE_URL.replace('sqlite:///', '')
    print(f"数据库路径: {db_path}")
    print()
    
    if not os.path.exists(db_path):
        print("✗ 数据库文件不存在，请先初始化数据库")
        print("运行: python rebuild_db.py")
        return 1
    
    engine = create_engine(DATABASE_URL)
    
    print("开始修复数据库结构...")
    print()
    
    # 修复 geo_articles 表
    print("[1/1] 修复 geo_articles 表:")
    
    # 添加 publish_time 列
    add_column_if_not_exists(
        engine, 
        'geo_articles', 
        'publish_time', 
        'DATETIME'
    )
    
    print()
    print("=" * 60)
    print("数据库修复完成！")
    print("=" * 60)
    print()
    print("提示: 请重启后端服务以应用更改")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
