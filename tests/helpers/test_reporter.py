# -*- coding: utf-8 -*-
"""
测试报告生成器
我用这个来收集测试结果并生成HTML报告！
"""

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class TestResult:
    """单个测试结果"""
    name: str
    status: str  # pass/fail/skip
    duration: float
    error_message: str = ""
    screenshot_path: str = ""
    console_errors: List[str] = field(default_factory=list)
    network_errors: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))


@dataclass
class TestSuite:
    """测试套件"""
    name: str
    tests: List[TestResult] = field(default_factory=list)
    start_time: str = field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    end_time: str = ""
    total_duration: float = 0.0

    @property
    def passed(self) -> int:
        return sum(1 for t in self.tests if t.status == "pass")

    @property
    def failed(self) -> int:
        return sum(1 for t in self.tests if t.status == "fail")

    @property
    def skipped(self) -> int:
        return sum(1 for t in self.tests if t.status == "skip")

    @property
    def total(self) -> int:
        return len(self.tests)

    @property
    def pass_rate(self) -> str:
        if self.total == 0:
            return "0%"
        return f"{(self.passed / self.total) * 100:.1f}%"


class TestReporter:
    """
    测试报告收集器

    提醒：负责收集所有测试结果并生成HTML报告！
    """

    def __init__(self, report_dir: Path):
        """
        初始化报告收集器

        Args:
            report_dir: 报告输出目录
        """
        self.report_dir = Path(report_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)

        self.screenshot_dir = self.report_dir / "screenshots"
        self.log_dir = self.report_dir / "logs"

        self.screenshot_dir.mkdir(exist_ok=True)
        self.log_dir.mkdir(exist_ok=True)

        self.suites: List[TestSuite] = []
        self.current_suite: Optional[TestSuite] = None

    def start_suite(self, name: str):
        """开始一个测试套件"""
        self.current_suite = TestSuite(name=name)
        self.suites.append(self.current_suite)

    def end_suite(self):
        """结束当前测试套件"""
        if self.current_suite:
            self.current_suite.end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.current_suite.total_duration = sum(t.duration for t in self.current_suite.tests)

    def add_result(self, test: TestResult):
        """添加测试结果"""
        if self.current_suite:
            self.current_suite.tests.append(test)

    def add_pass(self, name: str, duration: float):
        """添加通过结果"""
        self.add_result(TestResult(name=name, status="pass", duration=duration))

    def add_fail(self, name: str, duration: float, error_message: str,
                 screenshot_path: str = "", console_errors: List[str] = None):
        """添加失败结果"""
        self.add_result(TestResult(
            name=name,
            status="fail",
            duration=duration,
            error_message=error_message,
            screenshot_path=screenshot_path,
            console_errors=console_errors or []
        ))

    def add_skip(self, name: str, duration: float = 0):
        """添加跳过结果"""
        self.add_result(TestResult(name=name, status="skip", duration=duration))

    def save_screenshot(self, name: str, content: bytes) -> str:
        """
        保存截图

        Args:
            name: 截图名称（不含扩展名）
            content: 截图二进制内容

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.png"
        path = self.screenshot_dir / filename

        with open(path, "wb") as f:
            f.write(content)

        return str(path)

    def save_log(self, name: str, content: str) -> str:
        """
        保存日志

        Args:
            name: 日志名称
            content: 日志内容

        Returns:
            保存的文件路径
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{name}_{timestamp}.log"
        path = self.log_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(path)

    def save_json(self):
        """保存JSON格式的原始数据"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_path = self.report_dir / f"results_{timestamp}.json"

        data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "suites": [
                {
                    "name": suite.name,
                    "start_time": suite.start_time,
                    "end_time": suite.end_time,
                    "total_duration": suite.total_duration,
                    "total": suite.total,
                    "passed": suite.passed,
                    "failed": suite.failed,
                    "skipped": suite.skipped,
                    "pass_rate": suite.pass_rate,
                    "tests": [
                        {
                            "name": t.name,
                            "status": t.status,
                            "duration": t.duration,
                            "error_message": t.error_message,
                            "screenshot_path": t.screenshot_path,
                            "console_errors": t.console_errors,
                            "timestamp": t.timestamp
                        }
                        for t in suite.tests
                    ]
                }
                for suite in self.suites
            ]
        }

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return json_path

    def generate_html(self) -> str:
        """
        生成HTML报告

        Returns:
            HTML报告文件路径
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 计算总体统计
        total_tests = sum(s.total for s in self.suites)
        total_passed = sum(s.passed for s in self.suites)
        total_failed = sum(s.failed for s in self.suites)
        total_skipped = sum(s.skipped for s in self.suites)
        total_duration = sum(s.total_duration for s in self.suites)
        overall_pass_rate = f"{(total_passed / total_tests * 100):.1f}%" if total_tests > 0 else "0%"

        html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AutoGeo 测试报告 - {timestamp}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 28px;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 14px;
        }}

        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }}

        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}

        .summary-card .label {{
            font-size: 12px;
            color: #666;
            text-transform: uppercase;
        }}

        .summary-card.total .value {{ color: #667eea; }}
        .summary-card.passed .value {{ color: #28a745; }}
        .summary-card.failed .value {{ color: #dc3545; }}
        .summary-card.rate .value {{ color: #17a2b8; }}

        .suites {{
            padding: 30px;
        }}

        .suite {{
            margin-bottom: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
        }}

        .suite-header {{
            background: #f8f9fa;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            cursor: pointer;
            user-select: none;
        }}

        .suite-header:hover {{
            background: #e9ecef;
        }}

        .suite-title {{
            font-weight: 600;
            font-size: 16px;
        }}

        .suite-stats {{
            display: flex;
            gap: 15px;
            font-size: 12px;
        }}

        .suite-stats span {{
            padding: 2px 8px;
            border-radius: 10px;
        }}

        .suite-stats .total {{ background: #e9ecef; }}
        .suite-stats .passed {{ background: #d4edda; color: #155724; }}
        .suite-stats .failed {{ background: #f8d7da; color: #721c24; }}

        .test-list {{
            display: none;
        }}

        .test-list.show {{
            display: block;
        }}

        .test-item {{
            padding: 15px 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 15px;
        }}

        .test-item.pass {{
            background: #f8fff9;
        }}

        .test-item.fail {{
            background: #fff8f8;
        }}

        .test-status {{
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 12px;
        }}

        .test-item.pass .test-status {{
            background: #28a745;
            color: white;
        }}

        .test-item.fail .test-status {{
            background: #dc3545;
            color: white;
        }}

        .test-item.skip .test-status {{
            background: #6c757d;
            color: white;
        }}

        .test-info {{
            flex: 1;
        }}

        .test-name {{
            font-weight: 500;
            margin-bottom: 3px;
        }}

        .test-duration {{
            font-size: 12px;
            color: #999;
        }}

        .test-error {{
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            font-size: 12px;
            font-family: monospace;
        }}

        .test-screenshot {{
            margin-top: 10px;
        }}

        .test-screenshot img {{
            max-width: 100%;
            max-height: 300px;
            border-radius: 4px;
            border: 1px solid #ddd;
        }}

        .console-errors {{
            margin-top: 10px;
            background: #fff3cd;
            padding: 10px;
            border-radius: 4px;
        }}

        .console-errors h4 {{
            font-size: 12px;
            margin-bottom: 5px;
            color: #856404;
        }}

        .console-errors ul {{
            list-style: none;
            font-size: 11px;
            font-family: monospace;
        }}

        .footer {{
            padding: 20px;
            text-align: center;
            background: #f8f9fa;
            color: #666;
            font-size: 12px;
        }}

        .toggle-icon {{
            transition: transform 0.2s;
        }}

        .suite-header.open .toggle-icon {{
            transform: rotate(180deg);
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AutoGeo 真实环境测试报告</h1>
            <p>生成时间: {timestamp} | 环境: 真实环境 | 测试框架: Playwright MCP</p>
        </div>

        <div class="summary">
            <div class="summary-card total">
                <div class="value">{total_tests}</div>
                <div class="label">总测试数</div>
            </div>
            <div class="summary-card passed">
                <div class="value">{total_passed}</div>
                <div class="label">通过</div>
            </div>
            <div class="summary-card failed">
                <div class="value">{total_failed}</div>
                <div class="label">失败</div>
            </div>
            <div class="summary-card rate">
                <div class="value">{overall_pass_rate}</div>
                <div class="label">通过率</div>
            </div>
        </div>

        <div class="suites">
"""

        # 生成每个测试套件
        for suite in self.suites:
            html_content += f"""
            <div class="suite">
                <div class="suite-header" onclick="toggleSuite(this)">
                    <div class="suite-title">{suite.name}</div>
                    <div class="suite-stats">
                        <span class="total">总计: {suite.total}</span>
                        <span class="passed">通过: {suite.passed}</span>
                        <span class="failed">失败: {suite.failed}</span>
                        <span class="toggle-icon">▼</span>
                    </div>
                </div>
                <div class="test-list">
"""

            # 生成每个测试
            for test in suite.tests:
                status_class = test.status
                status_icon = "✓" if test.status == "pass" else ("✗" if test.status == "fail" else "-")

                html_content += f"""
                    <div class="test-item {status_class}">
                        <div class="test-status">{status_icon}</div>
                        <div class="test-info">
                            <div class="test-name">{test.name}</div>
                            <div class="test-duration">耗时: {test.duration:.2f}s | {test.timestamp}</div>
"""

                # 添加错误信息
                if test.status == "fail" and test.error_message:
                    html_content += f"""
                            <div class="test-error">{test.error_message}</div>
"""

                # 添加截图
                if test.screenshot_path:
                    # 转换为相对路径
                    rel_path = Path(test.screenshot_path).relative_to(self.report_dir)
                    html_content += f"""
                            <div class="test-screenshot">
                                <img src="{rel_path}" alt="失败截图">
                            </div>
"""

                # 添加控制台错误
                if test.console_errors:
                    html_content += """
                            <div class="console-errors">
                                <h4>控制台错误:</h4>
                                <ul>
"""
                    for error in test.console_errors:
                        html_content += f"                                    <li>{error}</li>\n"
                    html_content += """
                                </ul>
                            </div>
"""

                html_content += """
                        </div>
                    </div>
"""

            html_content += """
                </div>
            </div>
"""

        # 添加JavaScript和结尾
        html_content += f"""
        </div>

        <div class="footer">
            <p>AutoGeo 自动化测试系统 | 总耗时: {total_duration:.2f}s</p>
        </div>
    </div>

    <script>
        function toggleSuite(header) {{
            header.classList.toggle('open');
            const list = header.nextElementSibling;
            list.classList.toggle('show');
        }}

        // 自动展开失败的测试套件
        document.addEventListener('DOMContentLoaded', function() {{
            const suites = document.querySelectorAll('.suite');
            suites.forEach(function(suite) {{
                const failed = suite.querySelector('.test-item.fail');
                if (failed) {{
                    suite.querySelector('.suite-header').click();
                }}
            }});
        }});
    </script>
</body>
</html>
"""

        # 保存HTML报告
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_path = self.report_dir / f"report_{timestamp}.html"

        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(html_path)


# 便捷函数
def create_reporter(report_dir: str = None) -> TestReporter:
    """创建测试报告收集器"""
    if report_dir is None:
        report_dir = Path(__file__).parent.parent / "reports"
    return TestReporter(Path(report_dir))
