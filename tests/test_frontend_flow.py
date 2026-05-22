"""
微干预 - 前端流程测试
测试用户完整流程的页面跳转和数据渲染
"""
import pytest
import requests
import re


BASE_URL = "http://localhost:8000"


class TestPageNavigation:
    """页面跳转测试"""

    def test_index_page_loads(self):
        """TC_FLOW_001: 首页能正常加载"""
        response = requests.get(f"{BASE_URL}/static/index.html")
        assert response.status_code == 200, f"首页加载失败: {response.status_code}"

        # 检查关键元素
        content = response.text
        assert "家长干预" in content or "情境" in content, "首页缺少关键内容"
        print(f"  ✓ 首页加载正常")

    def test_input_page_loads(self):
        """TC_FLOW_002: 输入页能正常加载"""
        response = requests.get(f"{BASE_URL}/static/input.html")
        assert response.status_code == 200, f"输入页加载失败: {response.status_code}"

        content = response.text
        assert "input" in content.lower() or "情境" in content, "输入页内容异常"
        print(f"  ✓ 输入页加载正常")

    def test_task_detail_page_loads(self):
        """TC_FLOW_003: 任务详情页能正常加载（不带ID）"""
        response = requests.get(f"{BASE_URL}/static/task-detail.html")
        assert response.status_code == 200, f"任务详情页加载失败: {response.status_code}"
        print(f"  ✓ 任务详情页加载正常")

    def test_training_page_loads(self):
        """TC_FLOW_004: 训练页能正常加载"""
        response = requests.get(f"{BASE_URL}/static/training.html")
        assert response.status_code == 200, f"训练页加载失败: {response.status_code}"
        print(f"  ✓ 训练页加载正常")

    def test_feedback_page_loads(self):
        """TC_FLOW_005: 反馈页能正常加载"""
        response = requests.get(f"{BASE_URL}/static/feedback.html")
        assert response.status_code == 200, f"反馈页加载失败: {response.status_code}"
        print(f"  ✓ 反馈页加载正常")

    def test_history_page_loads(self):
        """TC_FLOW_006: 历史页能正常加载"""
        response = requests.get(f"{BASE_URL}/static/history.html")
        assert response.status_code == 200, f"历史页加载失败: {response.status_code}"
        print(f"  ✓ 历史页加载正常")


class TestPageContent:
    """页面内容测试"""

    def test_index_has_scenario_list_container(self):
        """TC_FLOW_007: 首页有情境列表容器"""
        response = requests.get(f"{BASE_URL}/static/index.html")
        content = response.text

        assert 'id="cardList"' in content or "card-list" in content or "scenario" in content.lower(), \
            "首页缺少情境列表容器"
        print(f"  ✓ 首页有情境列表容器")

    def test_index_has_empty_state(self):
        """TC_FLOW_008: 首页有空状态提示"""
        response = requests.get(f"{BASE_URL}/static/index.html")
        content = response.text

        assert 'id="emptyState"' in content or "empty-state" in content or "empty" in content.lower(), \
            "首页缺少空状态容器"
        print(f"  ✓ 首页有空状态")

    def test_training_page_has_goal_container(self):
        """TC_FLOW_009: 训练页有目标容器"""
        response = requests.get(f"{BASE_URL}/static/training.html")
        content = response.text

        # 检查是否有目标展示区域
        assert "goal" in content.lower() or "目标" in content or "today" in content.lower(), \
            "训练页缺少目标展示区域"
        print(f"  ✓ 训练页有目标容器")

    def test_feedback_page_has_emoji_options(self):
        """TC_FLOW_010: 反馈页有表情选项"""
        response = requests.get(f"{BASE_URL}/static/feedback.html")
        content = response.text

        # 检查是否有emoji选择
        assert "emoji" in content.lower() or "😊" in content or "满意" in content, \
            "反馈页缺少emoji选项"
        print(f"  ✓ 反馈页有emoji选项")


class TestJavaScriptDependencies:
    """JS依赖测试"""

    def test_config_js_exists(self):
        """TC_FLOW_011: config.js存在"""
        response = requests.get(f"{BASE_URL}/static/config.js")
        assert response.status_code == 200, f"config.js不存在: {response.status_code}"
        print(f"  ✓ config.js存在")

    def test_router_js_exists(self):
        """TC_FLOW_012: router.js存在"""
        response = requests.get(f"{BASE_URL}/static/js/router.js")
        assert response.status_code == 200, f"router.js不存在: {response.status_code}"
        print(f"  ✓ router.js存在")

    def test_scenario_store_exists(self):
        """TC_FLOW_013: scenarioStore.js存在"""
        response = requests.get(f"{BASE_URL}/static/js/store/scenarioStore.js")
        assert response.status_code == 200, f"scenarioStore.js不存在: {response.status_code}"
        print(f"  ✓ scenarioStore.js存在")

    def test_training_store_exists(self):
        """TC_FLOW_014: trainingStore.js存在"""
        response = requests.get(f"{BASE_URL}/static/js/store/trainingStore.js")
        assert response.status_code == 200, f"trainingStore.js不存在: {response.status_code}"
        print(f"  ✓ trainingStore.js存在")


class TestNavigationLinks:
    """导航链接测试"""

    def test_index_links_to_input(self):
        """TC_FLOW_015: 首页链接到输入页"""
        response = requests.get(f"{BASE_URL}/static/index.html")
        content = response.text

        assert "input.html" in content, "首页缺少到input.html的链接"
        print(f"  ✓ 首页链接到输入页")

    def test_index_links_to_task_detail(self):
        """TC_FLOW_016: 首页/任务详情链接存在"""
        response = requests.get(f"{BASE_URL}/static/task-detail.html")
        content = response.text

        # 检查是否有跳转到训练的链接
        assert "training.html" in content or "history.html" in content, \
            "任务详情页缺少跳转链接"
        print(f"  ✓ 任务详情页有跳转链接")

    def test_training_links_to_feedback(self):
        """TC_FLOW_017: 训练页链接到反馈页"""
        response = requests.get(f"{BASE_URL}/static/training.html")
        content = response.text

        assert "feedback.html" in content, "训练页缺少到feedback.html的链接"
        print(f"  ✓ 训练页链接到反馈页")


class TestAPIConsistency:
    """前后端API一致性测试"""

    def test_api_base_configured(self):
        """TC_FLOW_018: API_BASE配置正确"""
        response = requests.get(f"{BASE_URL}/static/config.js")
        content = response.text

        # 检查API_BASE是否配置
        assert "API_BASE" in content, "config.js缺少API_BASE定义"
        print(f"  ✓ API_BASE已配置")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
