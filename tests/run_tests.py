# -*- coding: utf-8 -*-
"""
一键运行测试脚本
我写的测试启动器，方便！
"""

import sys
import os
import subprocess
import argparse
import time
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def check_dependencies():
    """检查依赖是否安装"""
    print("🔍 检查测试依赖...")

    required = ["pytest", "requests"]
    missing = []

    for module in required:
        try:
            __import__(module)
        except ImportError:
            missing.append(module)

    if missing:
        print(f"[FAIL] 缺少依赖: {', '.join(missing)}")
        print("[PKG] 请运行: pip install pytest requests")
        return False

    print("[OK] 依赖检查通过")
    return True


def start_services():
    """启动前后端服务"""
    print("\n[INFO] 启动服务...")

    backend_url = "http://127.0.0.1:8001"
    frontend_url = "http://127.0.0.1:5173"

    # 检查服务是否已启动
    try:
        import requests
        requests.get(f"{backend_url}/api/health", timeout=2)
        print(f"[OK] 后端服务已运行: {backend_url}")
    except:
        print(f"[WARN] 后端服务未启动，请先启动后端:")
        print(f"   cd {project_root}/backend && python main.py")
        return False

    return True


def run_tests(args):
    """运行pytest测试"""
    import pytest

    print("\n[TEST] 开始运行测试...")
    print("=" * 50)

    # 构建pytest参数
    pytest_args = [
        "tests",
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    # 添加HTML报告
    if args.html:
        report_dir = project_root / "tests" / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        pytest_args.extend([
            f"--html={report_dir}/report.html",
            "--self-contained-html"
        ])

    # 添加标记过滤
    if args.marker:
        pytest_args.extend(["-m", args.marker])

    # 添加文件/文件夹过滤
    if args.path:
        pytest_args.append(args.path)

    # 添加详细输出
    if args.verbose:
        pytest_args.append("-vv")

    # 并行运行（如果安装了pytest-xdist）
    if args.parallel:
        pytest_args.extend(["-n", str(args.parallel)])

    # 运行测试
    exit_code = pytest.main(pytest_args)

    return exit_code


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="AutoGeo 测试运行器")
    parser.add_argument("--no-dep-check", action="store_true", help="跳过依赖检查")
    parser.add_argument("--html", action="store_true", help="生成HTML报告")
    parser.add_argument("-m", "--marker", help="按标记过滤测试 (geo/monitor/publish)")
    parser.add_argument("-p", "--path", help="指定测试文件/目录")
    parser.add_argument("-v", "--verbose", action="store_true", help="更详细的输出")
    parser.add_argument("-j", "--parallel", type=int, help="并行运行（需要pytest-xdist）")
    parser.add_argument("--skip-services", action="store_true", help="跳过服务检查")

    args = parser.parse_args()

    print("=" * 50)
    print("[TEST] AutoGeo 自动化测试")
    print("=" * 50)

    # 检查依赖
    if not args.no_dep_check:
        if not check_dependencies():
            sys.exit(1)

    # 检查服务
    if not args.skip_services:
        if not start_services():
            print("\n[WARN] 跳过服务检查继续运行（部分测试可能失败）")

    # 运行测试
    exit_code = run_tests(args)

    # 输出结果
    print("\n" + "=" * 50)
    if exit_code == 0:
        print("[OK] 所有测试通过！")
    else:
        print(f"[FAIL] 测试失败，退出码: {exit_code}")
        print("📄 查看详细报告: tests/reports/report.html")

    print("=" * 50)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()
