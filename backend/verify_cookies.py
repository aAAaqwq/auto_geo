# -*- coding: utf-8 -*-
"""
验证数据库中保存的cookies
老王我检查一下保存的数据是否正确！
"""

import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from database import get_db, init_db
from database.models import Account
from services.crypto import decrypt_cookies


def verify_cookies():
    """验证数据库中的cookies"""

    print("=" * 60)
    print(" " * 15 + "数据库Cookies验证")
    print("=" * 60)

    init_db()
    db = next(get_db())

    accounts = db.query(Account).all()

    print(f"\n数据库中共有 {len(accounts)} 个账号:\n")

    for acc in accounts:
        print(f"{'=' * 60}")
        print(f"ID: {acc.id}")
        print(f"平台: {acc.platform}")
        print(f"账号名称: {acc.account_name}")
        print(f"状态: { '已激活' if acc.status == 1 else '未激活'}")
        print(f"最后授权时间: {acc.last_auth_time}")

        # 解密cookies
        if acc.cookies:
            try:
                cookies = decrypt_cookies(acc.cookies)
                print(f"\nCookies数量: {len(cookies)}")
                print(f"加密数据长度: {len(acc.cookies)} 字符")

                # 显示关键cookies
                print(f"\n关键Cookies:")
                platform_key_cookies = {
                    "zhihu": ["z_c0", "d_c0", "SESSIONID", "q_c1", "JOID"],
                    "baijiahao": ["BDUSS", "STOKEN", "PTOKEN", "BAIDUID"],
                    "sohu": ["SUV"],
                    "toutiao": ["sessionid"],
                }
                key_cookies = platform_key_cookies.get(acc.platform, [])
                cookie_names = {c["name"]: c for c in cookies}

                for kc in key_cookies:
                    if kc in cookie_names:
                        c = cookie_names[kc]
                        val_preview = c["value"][:30] + "..." if len(c["value"]) > 30 else c["value"]
                        print(f"  [OK] {kc}: {val_preview}")
                    else:
                        print(f"  [X] {kc}: (不存在)")

                # 显示所有cookie名称
                all_names = sorted([c["name"] for c in cookies])
                print(f"\n所有Cookie名称 ({len(all_names)}):")
                for name in all_names:
                    print(f"  - {name}")

            except Exception as e:
                print(f"[ERROR] Cookies解密失败: {e}")
        else:
            print("\n[X] 无Cookies数据")

        print()

    db.close()

    print("=" * 60)
    print("验证完成！")
    print("=" * 60)


if __name__ == "__main__":
    verify_cookies()
