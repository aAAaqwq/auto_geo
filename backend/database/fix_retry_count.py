# -*- coding: utf-8 -*-
"""
修复 geo_articles 表缺少 retry_count 列的问题
使用纯 SQLite 方式，避免依赖 backend 模块
"""

import sqlite3
from pathlib import Path

def fix_retry_count_column():
    """添加 retry_count 列到 geo_articles 表"""
    
    # 数据库文件路径
    db_path = Path(r"D:\Project\auto_geo-master\auto_geo-master\backend\database\auto_geo_v3.db")
    
    if not db_path.exists():
        print("数据库文件不存在: {}".format(db_path))
        return False
    
    print("数据库路径: {}".format(db_path))
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(geo_articles)")
        columns = [row[1] for row in cursor.fetchall()]
        
        print("现有列: {}".format(columns))
        
        if 'retry_count' in columns:
            print("retry_count 列已存在，无需修复")
            return True
        
        # 添加 retry_count 列
        cursor.execute("""
            ALTER TABLE geo_articles 
            ADD COLUMN retry_count INTEGER DEFAULT 0
        """)
        
        conn.commit()
        print("成功添加 retry_count 列到 geo_articles 表")
        return True
        
    except Exception as e:
        conn.rollback()
        print("修复失败: {}".format(e))
        import traceback
        traceback.print_exc()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    success = fix_retry_count_column()
    exit(0 if success else 1)
