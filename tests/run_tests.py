"""
微干预 - 测试运行器
一键运行所有测试并生成报告
"""
import subprocess
import sys
import os
from pathlib import Path
from datetime import datetime


def run_command(cmd, description):
    """运行命令并打印结果"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")

    result = subprocess.run(
        cmd,
        shell=True,
        capture_output=False
    )
    return result.returncode == 0


def print_header(title):
    """打印标题"""
    print(f"\n{'#'*60}")
    print(f"# {title}")
    print(f"# {'-'*56}")
    print(f"# 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}\n")


def main():
    # 确保在正确目录
    test_dir = Path(__file__).parent
    os.chdir(test_dir)

    print_header("微干预 - 测试套件")

    # 检查依赖
    print("检查依赖...")
    try:
        import requests
        import pytest
        print("  ✓ requests 已安装")
        print("  ✓ pytest 已安装")
    except ImportError as e:
        print(f"  ✗ 缺少依赖: {e}")
        print("\n请运行: pip install requests pytest")
        sys.exit(1)

    # 检查后端是否运行
    print("\n检查后端服务...")
    try:
        import requests
        response = requests.get("http://localhost:8000/api/health", timeout=2)
        if response.status_code == 200:
            print("  ✓ 后端服务运行中 (http://localhost:8000)")
        else:
            print(f"  ⚠ 后端返回异常状态码: {response.status_code}")
    except Exception as e:
        print(f"  ✗ 后端服务未运行: {e}")
        print("\n请先启动后端: python app.py")
        sys.exit(1)

    all_passed = True

    # 1. 运行API测试
    if not run_command(
        "pytest test_api.py -v --tb=short",
        "API测试"
    ):
        all_passed = False

    # 2. 运行前端流程测试
    if not run_command(
        "pytest test_frontend_flow.py -v --tb=short",
        "前端流程测试"
    ):
        all_passed = False

    # 3. 运行状态管理测试
    if not run_command(
        "pytest test_stores.py -v --tb=short",
        "状态管理测试"
    ):
        all_passed = False

    # 总结
    print_header("测试完成")
    if all_passed:
        print("✓ 所有测试通过!")
        print("\n如需生成HTML报告，可运行:")
        print("  pytest --html=report.html --self-contained-html")
    else:
        print("✗ 部分测试失败，请检查上方输出")
        sys.exit(1)


if __name__ == "__main__":
    main()
