# -*- coding: utf-8 -*-
"""
授权功能单元测试
老王我测试整个授权流程的各个部分！
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
from services.crypto import encrypt_cookies, decrypt_cookies, encrypt_storage_state, decrypt_storage_state


async def test_database_connection():
    """测试数据库连接"""
    print("\n" + "=" * 50)
    print("测试1: 数据库连接")
    print("=" * 50)

    init_db()
    db = next(get_db())

    # 测试查询
    accounts = db.query(Account).all()
    print(f"  当前账号数量: {len(accounts)}")

    for acc in accounts:
        print(f"  - ID: {acc.id}, 平台: {acc.platform}, 名称: {acc.account_name}")

    db.close()
    print("  [PASS] 数据库连接正常")
    return True


async def test_encryption():
    """测试加密解密功能"""
    print("\n" + "=" * 50)
    print("测试2: 加密解密功能")
    print("=" * 50)

    test_cookies = [{"name": "test", "value": "value123", "domain": ".zhihu.com"}]
    test_storage = {"localStorage": {"key1": "value1"}}

    # 加密
    encrypted_cookies = encrypt_cookies(test_cookies)
    encrypted_storage = encrypt_storage_state(test_storage)

    print(f"  原始cookies: {test_cookies}")
    print(f"  加密后: {encrypted_cookies[:50]}...")

    # 解密
    decrypted_cookies = decrypt_cookies(encrypted_cookies)
    decrypted_storage = decrypt_storage_state(encrypted_storage)

    print(f"  解密后: {decrypted_cookies}")

    assert decrypted_cookies == test_cookies, "Cookies加密解密失败"
    print("  [PASS] 加密解密功能正常")
    return True


async def test_playwright_init():
    """测试Playwright初始化"""
    print("\n" + "=" * 50)
    print("测试3: Playwright初始化")
    print("=" * 50)

    try:
        await playwright_mgr.start()
        print("  [PASS] Playwright启动成功")

        await playwright_mgr.stop()
        print("  [PASS] Playwright停止成功")
        return True
    except Exception as e:
        print(f"  [FAIL] Playwright初始化失败: {e}")
        return False


async def test_auth_task_creation():
    """测试授权任务创建"""
    print("\n" + "=" * 50)
    print("测试4: 授权任务创建")
    print("=" * 50)

    # 设置数据库工厂
    playwright_mgr.set_db_factory(get_db)

    try:
        await playwright_mgr.start()

        task = await playwright_mgr.create_auth_task(
            platform="zhihu",
            account_name="单元测试账号"
        )

        print(f"  Task ID: {task.task_id}")
        print(f"  平台: {PLATFORMS['zhihu']['name']}")
        print(f"  状态: {task.status}")
        print(f"  Context: {task.context is not None}")
        print(f"  Page: {task.page is not None}")

        # 清理
        await playwright_mgr.close_auth_task(task.task_id)
        await playwright_mgr.stop()

        print("  [PASS] 授权任务创建成功")
        return True
    except Exception as e:
        print(f"  [FAIL] 授权任务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_cookie_extraction_simulation():
    """模拟测试Cookie提取（不实际登录）"""
    print("\n" + "=" * 50)
    print("测试5: Cookie提取模拟")
    print("=" * 50)

    try:
        await playwright_mgr.start()
        playwright_mgr.set_db_factory(get_db)

        task = await playwright_mgr.create_auth_task(
            platform="zhihu",
            account_name="Cookie测试"
        )

        # 等待页面加载
        await asyncio.sleep(2)

        # 模拟提取cookies
        if task.context:
            cookies = await task.context.cookies()
            print(f"  提取到 {len(cookies)} 个cookies")

            # 显示一些关键cookies
            for cookie in cookies[:5]:
                if cookie.get('name') in ['capsion_ticket', 'd_c0', 'z_c0']:
                    print(f"  - {cookie['name']}: {cookie['value'][:20]}...")

        # 清理
        await playwright_mgr.close_auth_task(task.task_id)
        await playwright_mgr.stop()

        print("  [PASS] Cookie提取模拟成功")
        return True
    except Exception as e:
        print(f"  [FAIL] Cookie提取模拟失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def run_all_tests():
    """运行所有单元测试"""
    print("\n" + "=" * 60)
    print(" " * 15 + "授权功能单元测试")
    print("=" * 60)

    results = []

    results.append(await test_database_connection())
    results.append(await test_encryption())
    results.append(await test_playwright_init())
    results.append(await test_auth_task_creation())
    results.append(await test_cookie_extraction_simulation())

    print("\n" + "=" * 60)
    print("测试结果汇总:")
    print("=" * 60)

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print(f"  总计: {total}")
    print(f"  通过: {passed}")
    print(f"  失败: {failed}")

    if failed == 0:
        print("\n  [SUCCESS] 所有测试通过!")
    else:
        print(f"\n  [FAILURE] {failed} 个测试失败")

    print("=" * 60)

    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
