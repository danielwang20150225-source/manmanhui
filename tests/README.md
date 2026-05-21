# 微干预 - 测试套件

## 测试文件说明

| 文件 | 说明 |
|------|------|
| `test_api.py` | API端点测试（17个端点） |
| `test_frontend_flow.py` | 前端页面跳转测试（18个测试） |
| `test_stores.py` | 状态管理测试（15个测试） |
| `conftest.py` | 测试配置和共享fixtures |
| `run_tests.py` | 测试运行器（一键运行所有测试） |

## 运行测试

### 方式1：一键运行所有测试

```bash
cd D:\星娃项目\manmanhui\tests
python run_tests.py
```

### 方式2：分别运行各模块

```bash
# API测试
pytest test_api.py -v

# 前端流程测试
pytest test_frontend_flow.py -v

# 状态管理测试
pytest test_stores.py -v
```

### 方式3：运行特定测试用例

```bash
# 只运行健康检查测试
pytest test_api.py::TestHealthAPI::test_health_check -v

# 只运行页面导航测试
pytest test_frontend_flow.py::TestPageNavigation -v
```

## 前置条件

1. **启动后端服务**
   ```bash
   cd D:\星娃项目\manmanhui
   python app.py
   ```

2. **安装测试依赖**
   ```bash
   pip install requests pytest
   ```

3. **确认后端运行**
   ```bash
   curl http://localhost:8000/api/health
   # 应返回 {"status": "ok", ...}
   ```

## 测试用例列表

### API测试 (test_api.py)

| ID | 测试名称 | 说明 |
|----|----------|------|
| TC_API_001 | 健康检查 | GET /api/health |
| TC_API_002 | 获取空情境列表 | GET /api/scenarios |
| TC_API_003 | 获取不存在的情境 | GET /api/scenarios/{id} |
| TC_API_005 | 获取不存在情境的每日训练 | GET /api/scenarios/{id}/days/{day} |
| TC_API_006 | 识别简单情境文本 | POST /api/scenarios/recognize |
| TC_API_007 | 空文本识别 | POST /api/scenarios/recognize |
| TC_API_008 | 获取任务包列表 | GET /api/packages |
| TC_API_009 | 向不存在情境提交反馈 | POST /api/feedback |
| TC_API_010 | 发送无效JSON | POST /api/scenarios/recognize |
| TC_API_011 | 缺少必需字段 | POST /api/scenarios/recognize |
| TC_API_012 | 生成任务包（基础） | POST /api/task-packages/generate |
| TC_API_013 | 生成任务包（带原始输入） | POST /api/task-packages/generate |
| TC_API_014 | 生成后查询情境 | 生成 → 查询 |
| TC_API_015 | 提交反馈v2（基础） | POST /api/scenarios/{id}/feedback |
| TC_API_016 | 只提交emoji | POST /api/scenarios/{id}/feedback |
| TC_API_017 | 不存在情境提交反馈 | POST /api/scenarios/{id}/feedback |
| TC_API_018 | 完整生命周期 | 识别 → 生成 → 训练 → 反馈 → 历史 |

### 前端流程测试 (test_frontend_flow.py)

| ID | 测试名称 | 说明 |
|----|----------|------|
| TC_FLOW_001 | 首页加载 | GET /static/index.html |
| TC_FLOW_002 | 输入页加载 | GET /static/input.html |
| TC_FLOW_003 | 任务详情页加载 | GET /static/task-detail.html |
| TC_FLOW_004 | 训练页加载 | GET /static/training.html |
| TC_FLOW_005 | 反馈页加载 | GET /static/feedback.html |
| TC_FLOW_006 | 历史页加载 | GET /static/history.html |
| TC_FLOW_007 | 首页情境列表容器 | 检查HTML元素 |
| TC_FLOW_008 | 首页空状态 | 检查HTML元素 |
| TC_FLOW_009 | 训练页目标容器 | 检查HTML元素 |
| TC_FLOW_010 | 反馈页emoji选项 | 检查HTML元素 |
| TC_FLOW_011 | config.js存在 | GET /static/config.js |
| TC_FLOW_012 | router.js存在 | GET /static/js/router.js |
| TC_FLOW_013 | scenarioStore.js存在 | GET /static/js/store/scenarioStore.js |
| TC_FLOW_014 | trainingStore.js存在 | GET /static/js/store/trainingStore.js |
| TC_FLOW_015 | 首页链接到输入页 | 检查HTML链接 |
| TC_FLOW_016 | 任务详情页跳转链接 | 检查HTML链接 |
| TC_FLOW_017 | 训练页链接到反馈页 | 检查HTML链接 |
| TC_FLOW_018 | API_BASE配置 | 检查config.js |

### 状态管理测试 (test_stores.py)

| ID | 测试名称 | 说明 |
|----|----------|------|
| TC_STORE_001 | fetchScenarios返回数组 | scenarioStore测试 |
| TC_STORE_002 | 字段映射正确 | scenarioStore测试 |
| TC_STORE_003 | 空状态返回正确结构 | scenarioStore测试 |
| TC_STORE_004 | 分页参数正确 | scenarioStore测试 |
| TC_STORE_005 | 新情境出现在列表 | scenarioStore测试 |
| TC_STORE_006 | 情境详情包含必要字段 | scenarioStore测试 |
| TC_STORE_007 | Emoji提取逻辑 | scenarioStore测试 |
| TC_STORE_008 | 进度计算 | scenarioStore测试 |
| TC_STORE_009 | 获取当日训练数据 | trainingStore测试 |
| TC_STORE_010 | 当日训练数据字段完整 | trainingStore测试 |
| TC_STORE_011 | 步骤结构正确 | trainingStore测试 |
| TC_STORE_012 | 天数边界测试 | trainingStore测试 |
| TC_STORE_013 | 获取多天训练数据 | trainingStore测试 |
| TC_STORE_014 | 处理不存在的scenario_id | 错误处理 |
| TC_STORE_015 | 处理不存在的情境训练请求 | 错误处理 |

## 测试覆盖的核心流程

```
用户输入 → 识别情境 → 生成任务包 → 每日训练 → 提交反馈 → 查看历史
     ↓           ↓           ↓           ↓           ↓
   input.html  recognize   generate    training   feedback  history
                              ↓           ↓
                          scenarioStore  trainingStore
```

## 生成HTML测试报告

```bash
# 安装 pytest-html（可选）
pip install pytest-html

# 生成HTML报告
pytest --html=report.html --self-contained-html
```

## 注意事项

1. 测试需要后端服务运行在 `http://localhost:8000`
2. 测试会自动等待后端启动（最多30秒）
3. 某些测试会创建真实数据（如情境），这是正常测试行为
4. 如需清理测试数据，直接删除数据库文件或运行 `DELETE FROM scenarios WHERE user_id LIKE 'test%'`

## MOCK_MODE 测试

如果不想调用真实 DeepSeek API，可以设置环境变量：

```bash
# Windows
set MOCK_MODE=true
python app.py

# 或在 config/.env 中添加
MOCK_MODE=true
```

在 MOCK_MODE 下，测试将使用预设的 Mock 数据，不会调用外部 API。