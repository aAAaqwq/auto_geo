# -*- coding: utf-8 -*-
"""
测试新的授权流程
老王我用本地HTML控制页方案！
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.playwright_mgr import playwright_mgr
from config import PLATFORMS
from database import get_db


async def test_auth():
    """测试授权流程"""

    print("=" * 50)
    print("开始测试授权流程...")
    print("=" * 50)

    # 设置数据库工厂（艹！测试脚本里必须手动设置！）
    playwright_mgr.set_db_factory(get_db)
    print("[OK] 数据库工厂已设置")

    # 创建知乎授权任务
    task = await playwright_mgr.create_auth_task(
        platform="zhihu",
        account_name="测试账号"
    )

    print(f"\n[OK] 浏览器已打开!")
    print(f"  Task ID: {task.task_id}")
    print(f"  Platform: {PLATFORMS['zhihu']['name']}")
    print(f"  Login URL: {PLATFORMS['zhihu']['login_url']}")

    print("\n" + "=" * 50)
    print("操作步骤:")
    print("=" * 50)
    print("1. 在第一个标签页完成知乎登录")
    print("2. 登录成功后，切换到第二个标签页（本地控制页）")
    print("3. 点击红色 '完成授权' 按钮")
    print("=" * 50)

    print("\n浏览器将保持打开3分钟，请在此时间内完成操作...")
    print("按 Ctrl+C 可提前结束\n")

    # 保持运行，等待用户操作
    try:
        await asyncio.sleep(180)  # 等待3分钟
    except KeyboardInterrupt:
        print("\n用户取消操作")

    # 清理
    await playwright_mgr.close_auth_task(task.task_id)
    await playwright_mgr.stop()

    print("\n测试完成！")


if __name__ == "__main__":
    asyncio.run(test_auth())
