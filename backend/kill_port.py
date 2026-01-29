# -*- coding: utf-8 -*-
"""
端口清理脚本
用于强制释放被占用的端口（Windows 专用）
"""

import sys
import subprocess

def kill_port(port: int):
    """
    强制释放指定端口
    """
    print(f"正在检查端口 {port}...")

    try:
        # Windows: 使用 netstat 查找占用端口的进程
        result = subprocess.run(
            ['netstat', '-ano'],
            capture_output=True,
            text=True,
            encoding='gbk',
            errors='ignore'
        )

        # 查找占用该端口的进程
        pids = set()
        for line in result.stdout.split('\n'):
            if f':{port}' in line and 'LISTENING' in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    if pid.isdigit():
                        pids.add(pid)

        if not pids:
            print(f"  端口 {port} 没有被占用")
            return True

        print(f"  发现 {len(pids)} 个进程占用端口 {port}: {pids}")

        # 杀掉这些进程
        for pid in pids:
            try:
                subprocess.run(
                    ['taskkill', '/F', '/PID', pid],
                    capture_output=True,
                    text=True,
                    encoding='gbk',
                    errors='ignore'
                )
                print(f"  ✓ 已终止进程 {pid}")
            except Exception as e:
                print(f"  ✗ 终止进程 {pid} 失败: {e}")

        print(f"✅ 端口 {port} 已释放")
        return True

    except Exception as e:
        print(f"❌ 清理端口失败: {e}")
        return False


if __name__ == "__main__":
    # 默认清理 8001 端口（后端 API）
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    print("=" * 40)
    print("端口清理工具")
    print("=" * 40)

    kill_port(port)

    print("")
    print("现在可以重新启动后端服务了！")
