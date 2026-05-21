"""
微干预 - 状态管理测试
测试 scenarioStore 和 trainingStore 的核心功能
通过 HTTP API 模拟前端 store 的数据流
"""
import pytest
import requests
import json


BASE_URL = "http://localhost:8000"


class TestScenarioStoreFetchScenarios:
    """scenarioStore.fetchScenarios() 功能测试"""

    def test_fetch_scenarios_returns_array(self, api_client):
        """TC_STORE_001: fetchScenarios 返回数组"""
        response = api_client.get("/api/scenarios")
        assert response.status_code == 200, f"请求失败: {response.status_code}"

        data = response.json()
        assert data.get("code") == 0, f"API错误: {data}"

        scenarios = data.get("data", {}).get("scenarios", [])
        assert isinstance(scenarios, list), f"scenarios应为数组: {type(scenarios)}"
        print(f"  ✓ fetchScenarios返回数组，长度: {len(scenarios)}")

    def test_fetch_scenarios_fields_mapping(self, api_client):
        """TC_STORE_002: 字段映射正确"""
        response = api_client.get("/api/scenarios")
        assert response.status_code == 200

        data = response.json()
        scenarios = data.get("data", {}).get("scenarios", [])

        # 即使是空数组，也应返回正确结构
        assert "data" in data, "缺少data字段"
        assert "total" in data.get("data", {}), "缺少total字段"
        print(f"  ✓ 字段映射正确")

        # 如果有数据，验证字段
        if scenarios:
            scenario = scenarios[0]
            # API应返回 id 或 scenario_id
            assert "id" in scenario or "scenario_id" in scenario, \
                f"缺少id字段: {list(scenario.keys())}"
            # 应返回 package_name 或 scenario_title
            assert "package_name" in scenario or "title" in scenario, \
                f"缺少名称字段: {list(scenario.keys())}"
            print(f"  ✓ 场景数据字段完整: {list(scenario.keys())[:5]}...")

    def test_fetch_scenarios_with_empty_state(self, api_client):
        """TC_STORE_003: 空状态返回正确结构"""
        response = api_client.get("/api/scenarios")
        assert response.status_code == 200

        data = response.json()
        scenarios = data.get("data", {}).get("scenarios", [])

        # 前端期望空状态有明确的响应结构
        assert isinstance(scenarios, list), "空状态应返回空数组"
        assert data.get("code") == 0, "空状态code应为0"
        print(f"  ✓ 空状态返回正确: code=0, scenarios=[]")

    def test_fetch_scenarios_pagination(self, api_client):
        """TC_STORE_004: 分页参数正确"""
        response = api_client.get("/api/scenarios?limit=5&offset=0")
        assert response.status_code == 200

        data = response.json()
        assert data.get("code") == 0
        # 验证返回的数组长度不超过limit
        scenarios = data.get("data", {}).get("scenarios", [])
        assert len(scenarios) <= 5, f"超过limit限制: {len(scenarios)}"
        print(f"  ✓ 分页参数正确: limit=5")


class TestScenarioStoreWithData:
    """带数据的 scenarioStore 测试"""

    @pytest.fixture
    def created_scenario_id(self, api_client):
        """创建测试用情境"""
        payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "store_test_user"
        }
        response = api_client.post("/api/task-packages/generate", json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("scenario_id")
        return None

    def test_scenario_list_contains_new_scenario(self, api_client, created_scenario_id):
        """TC_STORE_005: 新创建的情境出现在列表中"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get("/api/scenarios")
        assert response.status_code == 200

        data = response.json()
        scenarios = data.get("data", {}).get("scenarios", [])

        # 验证新创建的情境在列表中
        scenario_ids = [s.get("id") or s.get("scenario_id") for s in scenarios]
        assert created_scenario_id in scenario_ids, \
            f"新创建的情境未在列表中: {created_scenario_id}"
        print(f"  ✓ 新情境存在于列表: {created_scenario_id}")

    def test_scenario_detail_has_required_fields(self, api_client, created_scenario_id):
        """TC_STORE_006: 情境详情包含必要字段"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}")
        assert response.status_code == 200

        data = response.json()
        scenario = data.get("data", {}).get("scenario", {})

        # 验证前端期望的字段
        assert "scenario_id" in scenario or "id" in scenario, \
            "缺少scenario_id"
        assert "package_name" in scenario or "scenario_title" in scenario, \
            "缺少名称字段"

        # 验证 days_data 结构
        days_data = scenario.get("days_data", {})
        if days_data:
            days = days_data.get("days", [])
            if days:
                first_day = days[0]
                assert "day" in first_day, "days缺少day字段"
                assert "theme" in first_day, "days缺少theme字段"
                print(f"  ✓ 情境详情字段完整: {len(days)}天")

    def test_scenario_emoji_extraction(self, api_client, created_scenario_id):
        """TC_STORE_007: Emoji提取逻辑"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}")
        assert response.status_code == 200

        data = response.json()
        scenario = data.get("data", {}).get("scenario", {})

        # 验证 emoji 字段
        pkg_name = scenario.get("package_name", "")
        scenario_emoji = scenario.get("scenario_emoji", "")

        # package_name 可能包含 emoji（如 "👕 穿衣抗拒"）
        # scenario_emoji 应该单独提取
        assert scenario_emoji, f"缺少scenario_emoji: {pkg_name}"
        print(f"  ✓ Emoji提取: {scenario_emoji} <- {pkg_name}")

    def test_scenario_progress_calculation(self, api_client, created_scenario_id):
        """TC_STORE_008: 进度计算"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}")
        assert response.status_code == 200

        data = response.json()
        scenario = data.get("data", {}).get("scenario", {})

        # 验证进度字段
        assert "progress_percent" in scenario or "current_day" in scenario, \
            "缺少进度相关字段"
        print(f"  ✓ 进度字段: {scenario.get('current_day', 1)}/{scenario.get('total_days', 7)}")


class TestTrainingStoreFetchTodayTraining:
    """trainingStore.fetchTodayTraining() 功能测试"""

    @pytest.fixture
    def created_scenario_id(self, api_client):
        """创建测试用情境"""
        payload = {
            "package_code": "08",
            "package_name": "情绪行为管理",
            "period_days": 7,
            "user_id": "training_test_user"
        }
        response = api_client.post("/api/task-packages/generate", json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get("data", {}).get("scenario_id")
        return None

    def test_fetch_today_training_basic(self, api_client, created_scenario_id):
        """TC_STORE_009: 获取当日训练数据"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}/days/1")
        assert response.status_code == 200, f"请求失败: {response.status_code}"

        data = response.json()
        assert data.get("code") == 0, f"API错误: {data}"

        training_data = data.get("data", {})
        assert "goal" in training_data or "today_goal" in training_data, \
            "缺少goal字段"
        print(f"  ✓ 当日训练数据获取成功")

    def test_fetch_today_training_fields(self, api_client, created_scenario_id):
        """TC_STORE_010: 当日训练数据字段完整"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}/days/1")
        assert response.status_code == 200

        data = response.json()
        training_data = data.get("data", {})

        # 验证 store 需要的字段
        assert training_data.get("day_index") == 1, "day_index应为1"
        assert "goal" in training_data or "today_goal" in training_data, \
            "缺少goal"
        assert "tip" in training_data or "today_tip" in training_data, \
            "缺少tip"
        assert "steps" in training_data, "缺少steps"
        assert "tasks" in training_data, "缺少tasks"

        print(f"  ✓ 训练数据字段完整")
        print(f"    - goal: {training_data.get('goal', '')[:30]}...")
        print(f"    - steps: {len(training_data.get('steps', []))}条")
        print(f"    - tasks: {len(training_data.get('tasks', []))}条")

    def test_fetch_today_training_steps_structure(self, api_client, created_scenario_id):
        """TC_STORE_011: 步骤结构正确"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        response = api_client.get(f"/api/scenarios/{created_scenario_id}/days/1")
        assert response.status_code == 200

        data = response.json()
        steps = data.get("data", {}).get("steps", [])

        if steps:
            step = steps[0]
            # 验证步骤必要字段
            assert "step_order" in step or "description" in step, \
                f"步骤缺少必要字段: {list(step.keys())}"
            print(f"  ✓ 步骤结构正确: {len(steps)}个步骤")
            for i, s in enumerate(steps[:3]):
                desc = s.get("description", "")[:30]
                print(f"    步骤{i+1}: {desc}...")
        else:
            print(f"  ⚠ 无步骤数据（可能是Mock模式）")

    def test_fetch_today_training_day_boundary(self, api_client, created_scenario_id):
        """TC_STORE_012: 天数边界测试"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        # 测试不存在的天数
        response = api_client.get(f"/api/scenarios/{created_scenario_id}/days/99")
        # 应该返回404
        assert response.status_code == 404, f"不存在的天数应返回404，实际: {response.status_code}"
        print(f"  ✓ 天数边界处理正确: day=99返回404")

    def test_fetch_training_multiple_days(self, api_client, created_scenario_id):
        """TC_STORE_013: 获取多天训练数据"""
        if not created_scenario_id:
            pytest.skip("无法创建测试情境")

        # 获取第1天和第2天
        for day in [1, 2]:
            response = api_client.get(f"/api/scenarios/{created_scenario_id}/days/{day}")
            assert response.status_code == 200, f"第{day}天请求失败: {response.status_code}"

            data = response.json()
            training_data = data.get("data", {})
            assert training_data.get("day_index") == day, \
                f"day_index不正确: {training_data.get('day_index')} != {day}"

        print(f"  ✓ 多天训练数据获取正确")


class TestStoreErrorHandling:
    """状态管理错误处理测试"""

    def test_scenario_store_handles_missing_id(self, api_client):
        """TC_STORE_014: 处理不存在的scenario_id"""
        response = api_client.get("/api/scenarios/fake_id_12345")
        # 应该返回404
        assert response.status_code == 404, f"预期404，实际: {response.status_code}"
        print(f"  ✓ 不存在scenario处理正确")

    def test_training_store_handles_missing_scenario(self, api_client):
        """TC_STORE_015: 处理不存在的情境的训练请求"""
        response = api_client.get("/api/scenarios/fake_id_12345/days/1")
        assert response.status_code == 404, f"预期404，实际: {response.status_code}"
        print(f"  ✓ 不存在情境的训练请求处理正确")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])