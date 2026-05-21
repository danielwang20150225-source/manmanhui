"""
微干预 - 测试配置
定义共享的 fixtures 和测试配置
"""
import pytest
import requests
import time
import os
from pathlib import Path

# API基础URL
API_BASE = os.getenv("API_BASE", "http://localhost:8000")

# 用于标识测试环境的header
TEST_HEADER = {
    "X-Test-Environment": "true",
    "Content-Type": "application/json"
}


@pytest.fixture(scope="session")
def api_base_url():
    """API基础URL"""
    return API_BASE


@pytest.fixture(scope="session")
def wait_for_backend(api_base_url):
    """等待后端服务就绪"""
    max_retries = 30
    retry_interval = 1

    for i in range(max_retries):
        try:
            response = requests.get(f"{api_base_url}/api/health", timeout=5)
            if response.status_code == 200:
                print(f"\n✓ 后端服务已就绪 ({api_base_url})")
                return True
        except requests.exceptions.RequestException:
            pass

        if i < max_retries - 1:
            print(f"\n等待后端启动... ({i+1}/{max_retries})")
            time.sleep(retry_interval)

    pytest.fail(f"后端服务未能在 {max_retries} 秒内启动: {api_base_url}")


@pytest.fixture(scope="session")
def api_client(api_base_url, wait_for_backend):
    """带重试机制的API客户端"""
    class APIClient:
        def __init__(self, base_url):
            self.base_url = base_url
            self.session = requests.Session()
            self.session.headers.update(TEST_HEADER)

        def get(self, path, **kwargs):
            url = f"{self.base_url}{path}"
            return self.session.get(url, **kwargs)

        def post(self, path, **kwargs):
            url = f"{self.base_url}{path}"
            return self.session.post(url, **kwargs)

        def delete(self, path, **kwargs):
            url = f"{self.base_url}{path}"
            return self.session.delete(url, **kwargs)

        def put(self, path, **kwargs):
            url = f"{self.base_url}{path}"
            return self.session.put(url, **kwargs)

    return APIClient(api_base_url)


@pytest.fixture
def sample_scenario_id():
    """返回示例情境ID（如果有的话）"""
    # 这个值需要在测试中动态创建或查询
    return None


# ==================== 错误码定义 ====================
class ErrorCode:
    """错误码体系"""

    # 前端错误 (1xxx)
    FRONTEND_PAGE_NAV = 1001  # 页面跳转错误
    FRONTEND_RENDER = 1101     # 数据渲染错误
    FRONTEND_INPUT = 1201      # 用户输入错误

    # 后端错误 (2xxx)
    BACKEND_VALIDATION = 2001  # 参数验证错误
    BACKEND_LOGIC = 2101       # 业务逻辑错误
    BACKEND_EXTERNAL = 2201    # 外部服务错误(DeepSeek)

    # API错误 (3xxx)
    API_NOT_FOUND = 3001       # 资源不存在
    API_PARAM_ERROR = 3002     # 参数错误
    API_SERVER_ERROR = 3003   # 服务器内部错误


class TestResult:
    """测试结果记录"""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []

    def record_pass(self, test_name):
        self.passed += 1
        print(f"  ✓ {test_name}")

    def record_fail(self, test_name, reason):
        self.failed += 1
        self.errors.append({"test": test_name, "reason": reason})
        print(f"  ✗ {test_name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*50}")
        print(f"测试结果: {self.passed}/{total} 通过")
        if self.errors:
            print(f"\n失败详情:")
            for e in self.errors:
                print(f"  - {e['test']}: {e['reason']}")
        return self.failed == 0
