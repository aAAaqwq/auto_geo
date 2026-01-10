# -*- coding: utf-8 -*-
"""
测试所有平台的授权功能
老王我一次性把所有平台都测了！
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from services.playwright_mgr import playwright_mgr
from config import PLATFORMS
from database import get_db, init_db
from database.models import Account


async def test_all_platforms():
    """测试所有平台的授权功能"""

    print("=" * 60)
    print(" " * 15 + "所有平台授权测试")
    print("=" * 60)

    # 设置数据库工厂
    playwright_mgr.set_db_factory(get_db)
    init_db()

    # 检查当前数据库中的账号
    db = next(get_db())
    existing_accounts = db.query(Account).all()
    print(f"\n当前数据库账号数: {len(existing_accounts)}")
    for acc in existing_accounts:
        print(f"  - ID: {acc.id}, 平台: {acc.platform}, 名称: {acc.account_name}")
    db.close()

    print("\n" + "=" * 60)
    print("支持的平台:")
    print("=" * 60)
    for key, config in PLATFORMS.items():
        print(f"  {key}: {config['name']} - {config['login_url']}")

    print("\n" + "=" * 60)
    print("测试模式:")
    print("=" * 60)
    print("  1. 知乎 (zhihu)")
    print("  2. 百家号 (baijiahao)")
    print("  3. 搜狐 (sohu)")
    print("  4. 头条 (toutiao)")
    print("  5. 全部测试")

    choice = input("\n请选择 (1-5): ").strip()

    platforms_to_test = []
    if choice == "1":
        platforms_to_test = ["zhihu"]
    elif choice == "2":
        platforms_to_test = ["baijiahao"]
    elif choice == "3":
        platforms_to_test = ["sohu"]
    elif choice == "4":
        platforms_to_test = ["toutiao"]
    elif choice == "5":
        platforms_to_test = list(PLATFORMS.keys())
    else:
        print("无效选择，退出")
        return

    print("\n" + "=" * 60)
    print(f"将要测试的平台: {', '.join([PLATFORMS[p]['name'] for p in platforms_to_test])}")
    print("=" * 60)

    # 逐个测试平台
    for platform in platforms_to_test:
        print(f"\n{'=' * 60}")
        print(f"开始测试: {PLATFORMS[platform]['name']}")
        print(f"{'=' * 60}")

        try:
            task = await playwright_mgr.create_auth_task(
                platform=platform,
                account_name=f"{PLATFORMS[platform]['name']}测试账号"
            )

            print(f"\n[OK] 浏览器已打开!")
            print(f"  Task ID: {task.task_id}")
            print(f"  Platform: {PLATFORMS[platform]['name']}")
            print(f"  Login URL: {PLATFORMS[platform]['login_url']}")

            print("\n操作步骤:")
            print("  1. 在第一个标签页完成登录")
            print("  2. 切换到第二个标签页（本地控制页）")
            print("  3. 点击 '完成授权' 按钮")

            input("\n完成授权后按回车继续...")

            # 检查任务状态
            if task.status == "success":
                print(f"  [SUCCESS] 授权成功！账号ID: {task.created_account_id or task.account_id}")
            else:
                print(f"  [WARNING] 任务状态: {task.status}")

            # 清理
            await playwright_mgr.close_auth_task(task.task_id)

        except Exception as e:
            print(f"  [ERROR] {platform} 测试失败: {e}")

    # 最终检查
    print("\n" + "=" * 60)
    print("最终数据库状态:")
    print("=" * 60)

    db = next(get_db())
    final_accounts = db.query(Account).all()
    print(f"账号总数: {len(final_accounts)}")
    for acc in final_accounts:
        # 解密cookies查看数量
        from services.crypto import decrypt_cookies
        try:
            cookies = decrypt_cookies(acc.cookies)
            print(f"  - ID: {acc.id}, 平台: {acc.platform}, 名称: {acc.account_name}, Cookies: {len(cookies)}个")
        except:
            print(f"  - ID: {acc.id}, 平台: {acc.platform}, 名称: {acc.account_name}, Cookies: 解密失败")
    db.close()

    # 停止playwright
    await playwright_mgr.stop()

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_all_platforms())
    except KeyboardInterrupt:
        print("\n用户取消操作")
