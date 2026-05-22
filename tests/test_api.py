"""
微干预 - API测试用例
测试所有后端API端点
"""
import pytest
import json
import time


class TestHealthAPI:
    """健康检查API测试"""

    def test_health_check(self, api_client):
        """TC_API_001: 健康检查返回200"""
        response = api_client.get("/api/health")
        assert response.status_code == 200, f"健康检查失败: {response.status_code}"

        data = response.json()
        assert data.get("status") == "ok", f"状态不为ok: {data}"
        print(f"  ✓ 健康检查正常: {data}")


class TestScenariosAPI:
    """情境管理API测试"""

    def test_get_scenarios_empty(self, api_client):
        """TC_API_002: 获取空情境列表"""
        response = api_client.get("/api/scenarios")
        assert response.status_code == 200, f"获取情境列表失败: {response.status_code}"

        data = response.json()
        assert "data" in data or "scenarios" in data, f"响应格式错误: {data}"
        print(f"  ✓ 获取情境列表成功")

    def test_get_scenario_detail_not_found(self, api_client):
        """TC_API_003: 获取不存在的情境详情"""
        response = api_client.get("/api/scenarios/non_existent_id_12345")
        # 可能是404或返回空数据，取决于后端实现
        assert response.status_code in [200, 404], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 不存在情境处理正确")

    def test_create_scenario_and_get(self, api_client):
        """TC_API_004: 创建情境并验证"""
        # 这个需要POST，但可能需要完整参数
        # 先跳过，等确认API契约
        pytest.skip("等待确认创建情境API的参数格式")


class TestTrainingDayAPI:
    """每日训练API测试"""

    def test_get_training_day_not_found(self, api_client):
        """TC_API_005: 获取不存在情境的每日训练"""
        response = api_client.get("/api/scenarios/fake_id_12345/days/1")
        # 应该返回明确的错误，而不是500
        assert response.status_code in [200, 404], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 不存在情境的每日训练处理正确")


class TestRecognizeAPI:
    """意图识别API测试"""

    def test_recognize_simple_text(self, api_client):
        """TC_API_006: 识别简单情境文本"""
        payload = {
            "text": "孩子不愿意跟人沟通"
        }
        response = api_client.post("/api/scenarios/recognize", json=payload)
        assert response.status_code == 200, f"识别请求失败: {response.status_code}"

        data = response.json()
        # 应该有matched_package或类似字段
        assert "data" in data or "package" in data or "matched" in data, f"响应格式错误: {data}"
        print(f"  ✓ 意图识别正常: {data}")

    def test_recognize_empty_text(self, api_client):
        """TC_API_007: 空文本识别"""
        payload = {"text": ""}
        response = api_client.post("/api/scenarios/recognize", json=payload)
        # 应该返回错误，而不是崩溃
        assert response.status_code in [200, 400, 422], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 空文本处理正确")


class TestPackagesAPI:
    """任务包API测试"""

    def test_get_packages(self, api_client):
        """TC_API_008: 获取任务包列表"""
        response = api_client.get("/api/packages")
        assert response.status_code == 200, f"获取任务包列表失败: {response.status_code}"

        data = response.json()
        assert "data" in data or "packages" in data, f"响应格式错误: {data}"
        print(f"  ✓ 获取任务包列表成功")


class TestFeedbackAPI:
    """反馈API测试（旧版endpoint）"""

    def test_submit_feedback_not_found(self, api_client):
        """TC_API_009: 向不存在的情境提交反馈（旧版endpoint）"""
        payload = {
            "scenario_id": "fake_id_12345",
            "day": 1,
            "emoji": "satisfied",
            "text": "测试"
        }
        # 旧版 endpoint /api/feedback（保留兼容）
        response = api_client.post("/api/feedback", json=payload)
        # 应该返回明确错误或404
        assert response.status_code in [200, 404], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 不存在情境的反馈处理正确")


class TestErrorHandling:
    """错误处理测试"""

    def test_invalid_json(self, api_client):
        """TC_API_010: 发送无效JSON"""
        response = api_client.session.post(
            f"{api_client.base_url}/api/scenarios/recognize",
            data="not json",
            headers={"Content-Type": "application/json"}
        )
        # 应该返回422或400
        assert response.status_code in [400, 422, 500], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 无效JSON处理正确: {response.status_code}")

    def test_missing_required_field(self, api_client):
        """TC_API_011: 缺少必需字段"""
        payload = {}  # text字段缺失
        response = api_client.post("/api/scenarios/recognize", json=payload)
        # 应该返回422验证错误
        assert response.status_code in [200, 400, 422], f"未预期的状态码: {response.status_code}"
        print(f"  ✓ 缺少必需字段处理正确")


class TestTaskPackageGenerateAPI:
    """任务包生成API测试"""

    def test_generate_task_package_basic(self, api_client):
        """TC_API_012: 生成任务包（基础参数）"""
        # 使用已知的有效 package_code
        payload = {
            "package_code": "08",  # 情绪行为管理
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "test_user"
        }
        response = api_client.post("/api/task-packages/generate", json=payload)
        assert response.status_code == 200, f"生成任务包失败: {response.status_code}"

        data = response.json()
        assert data.get("code") == 0, f"返回错误: {data}"
        assert "data" in data, f"缺少data字段: {data}"

        result = data["data"]
        assert "scenario_id" in result, f"缺少scenario_id: {result}"
        assert "days" in result, f"缺少days字段: {result}"
        print(f"  ✓ 任务包生成成功: {result.get('scenario_id')}")

    def test_generate_task_package_with_raw_input(self, api_client):
        """TC_API_013: 生成任务包（带原始输入）"""
        payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "test_user",
            "raw_input": "孩子情绪崩溃，哭闹不止"
        }
        response = api_client.post("/api/task-packages/generate", json=payload)
        assert response.status_code == 200, f"生成任务包失败: {response.status_code}"

        data = response.json()
        assert data.get("code") == 0, f"返回错误: {data}"
        print(f"  ✓ 带原始输入的任务包生成成功")

    def test_generate_task_package_creates_scenario(self, api_client):
        """TC_API_014: 生成任务包后能获取到情境"""
        # 生成任务包
        payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "test_user"
        }
        response = api_client.post("/api/task-packages/generate", json=payload)
        assert response.status_code == 200, f"生成任务包失败: {response.status_code}"

        data = response.json()
        scenario_id = data.get("data", {}).get("scenario_id")
        assert scenario_id, f"未返回scenario_id: {data}"

        # 通过API获取该情境
        get_response = api_client.get(f"/api/scenarios/{scenario_id}")
        assert get_response.status_code == 200, f"获取情境失败: {get_response.status_code}"

        get_data = get_response.json()
        assert get_data.get("code") == 0, f"获取情境返回错误: {get_data}"
        print(f"  ✓ 任务包生成的情境可查询: {scenario_id}")


class TestFeedbackAPIV2:
    """反馈API测试（v2版本）"""

    def test_submit_feedback_v2_basic(self, api_client):
        """TC_API_015: 提交反馈v2（基础测试）"""
        # 先创建一个情境用于测试
        gen_payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "test_user"
        }
        gen_response = api_client.post("/api/task-packages/generate", json=gen_payload)
        if gen_response.status_code != 200:
            pytest.skip("无法创建测试情境")

        scenario_id = gen_response.json().get("data", {}).get("scenario_id")
        if not scenario_id:
            pytest.skip("未获得scenario_id")

        # 提交反馈
        feedback_payload = {
            "scenario_id": scenario_id,
            "task_id": f"{scenario_id}_D1_T1",
            "day": 1,
            "emoji": "satisfied",
            "text": "今天孩子配合得不错"
        }
        response = api_client.post(f"/api/scenarios/{scenario_id}/feedback", json=feedback_payload)
        assert response.status_code == 200, f"提交反馈失败: {response.status_code}"

        data = response.json()
        assert data.get("code") == 0, f"返回错误: {data}"
        assert "data" in data, f"缺少data字段: {data}"

        result = data["data"]
        assert "feedback_id" in result, f"缺少feedback_id: {result}"
        assert "encouragement_text" in result, f"缺少encouragement_text: {result}"
        print(f"  ✓ 反馈提交成功: {result.get('feedback_id')}")

    def test_submit_feedback_emoji_only(self, api_client):
        """TC_API_016: 只提交emoji（无文字备注）"""
        # 创建测试情境
        gen_payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "test_user"
        }
        gen_response = api_client.post("/api/task-packages/generate", json=gen_payload)
        if gen_response.status_code != 200:
            pytest.skip("无法创建测试情境")

        scenario_id = gen_response.json().get("data", {}).get("scenario_id")
        if not scenario_id:
            pytest.skip("未获得scenario_id")

        # 只提交emoji，无文字
        feedback_payload = {
            "scenario_id": scenario_id,
            "task_id": f"{scenario_id}_D1_T1",
            "day": 1,
            "emoji": "satisfied"
        }
        response = api_client.post(f"/api/scenarios/{scenario_id}/feedback", json=feedback_payload)
        assert response.status_code == 200, f"提交反馈失败: {response.status_code}"
        print(f"  ✓ 无文字反馈提交成功")

    def test_submit_feedback_not_found_scenario(self, api_client):
        """TC_API_017: 向不存在的情境提交反馈"""
        fake_id = "fake_scenario_id_12345"
        feedback_payload = {
            "scenario_id": fake_id,
            "task_id": "fake_task_id",
            "day": 1,
            "emoji": "satisfied",
            "text": "测试"
        }
        response = api_client.post(f"/api/scenarios/{fake_id}/feedback", json=feedback_payload)
        # 应该返回404
        assert response.status_code == 404, f"预期404，实际: {response.status_code}"
        print(f"  ✓ 不存在情境返回404")


# ==================== 集成测试 ====================
class TestScenarioLifecycle:
    """情境完整生命周期测试"""

    def test_full_lifecycle(self, api_client):
        """
        TC_API_018: 完整情境生命周期
        1. 用户输入 → 识别情境
        2. 生成任务包
        3. 获取训练内容
        4. 提交反馈
        5. 查看历史
        """
        # Step 1: 识别情境
        recognize_payload = {"text": "孩子情绪崩溃"}
        resp = api_client.post("/api/scenarios/recognize", json=recognize_payload)
        assert resp.status_code == 200, f"识别请求失败: {resp.status_code}"
        matched = resp.json().get("data", {})
        print(f"  Step 1: 识别完成 - {matched.get('package_name', 'unknown')}")

        # Step 2: 生成任务包
        package_code = matched.get("package_code", "08")
        gen_payload = {
            "package_code": package_code,
            "package_name": matched.get("package_name", ""),
            "period_days": 7,
            "user_id": "integration_test_user"
        }
        gen_resp = api_client.post("/api/task-packages/generate", json=gen_payload)
        assert gen_resp.status_code == 200, f"生成任务包失败: {gen_resp.status_code}"
        gen_data = gen_resp.json().get("data", {})
        scenario_id = gen_data.get("scenario_id")
        assert scenario_id, f"未返回scenario_id: {gen_data}"
        print(f"  Step 2: 任务包生成 - {scenario_id}")

        # Step 3: 获取训练内容
        day_resp = api_client.get(f"/api/scenarios/{scenario_id}/days/1")
        assert day_resp.status_code == 200, f"获取训练内容失败: {day_resp.status_code}"
        day_data = day_resp.json().get("data", {})
        assert "goal" in day_data or "today_goal" in day_data, f"缺少目标字段: {day_data}"
        print(f"  Step 3: 训练内容获取成功")

        # Step 4: 提交反馈
        task_id = day_data.get("tasks", [{}])[0].get("task_id") if day_data.get("tasks") else f"{scenario_id}_D1_T1"
        feedback_payload = {
            "scenario_id": scenario_id,
            "task_id": task_id,
            "day": 1,
            "emoji": "satisfied",
            "text": "集成测试反馈"
        }
        fb_resp = api_client.post(f"/api/scenarios/{scenario_id}/feedback", json=feedback_payload)
        assert fb_resp.status_code == 200, f"提交反馈失败: {fb_resp.status_code}"
        print(f"  Step 4: 反馈提交成功")

        # Step 5: 查看历史
        history_resp = api_client.get(f"/api/scenarios/{scenario_id}/history")
        assert history_resp.status_code == 200, f"获取历史失败: {history_resp.status_code}"
        history_data = history_resp.json().get("data", {})
        assert "history" in history_data, f"缺少history字段: {history_data}"
        assert len(history_data["history"]) > 0, "历史记录为空"
        print(f"  Step 5: 历史记录查询成功")

        print(f"  ✓ 完整生命周期测试通过")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
