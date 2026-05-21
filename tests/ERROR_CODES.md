# 微干预 - 错误码体系 v1.0

> **维护者**：测试工程师
> **版本**：v1.0
> **日期**：2026-05-07
> **状态**：初始版本

---

## 目录

1. [错误码设计原则](#1-错误码设计原则)
2. [前端错误码（1xxx）](#2-前端错误码1xxx)
3. [后端错误码（2xxx）](#3-后端错误码2xxx)
4. [API错误码（3xxx）](#4-api错误码3xxx)
5. [第三方服务错误码（4xxx）](#5-第三方服务错误码4xxx)
6. [PRD对照表](#6-prd对照表)
7. [错误处理流程](#7-错误处理流程)

---

## 1. 错误码设计原则

### 1.1 错误码结构

```
Error Code: [CATEGORY]-[MODULE]-[NUMBER]
Example: 1001, 2001, 3001
```

### 1.2 错误码分类

| 前缀 | 分类 | 说明 |
|------|------|------|
| 1xxx | 前端错误 | 页面跳转、数据渲染、用户输入相关错误 |
| 2xxx | 后端错误 | 参数验证、业务逻辑、数据库相关错误 |
| 3xxx | API错误 | HTTP状态码映射的业务错误码 |
| 4xxx | 第三方服务错误 | DeepSeek API、ChromaDB等外部服务错误 |

### 1.3 错误响应格式

```json
{
  "error_code": "1001",
  "message": "页面加载失败",
  "details": {
    "page": "index.html",
    "reason": "network_error"
  },
  "timestamp": "2026-05-07T10:30:00Z"
}
```

---

## 2. 前端错误码（1xxx）

### 2.1 页面跳转错误（10xx）

| 错误码 | 名称 | 说明 | 排查方向 |
|--------|------|------|----------|
| 1001 | PAGE_NOT_FOUND | 页面不存在 | 检查HTML文件是否存在，URL是否正确 |
| 1002 | PAGE_LOAD_FAILED | 页面加载失败 | 刷新页面或检查网络 |
| 1003 | REDIRECT_LOOP | 页面重定向循环 | 清除缓存后重试 |
| 1004 | UNAUTHORIZED_ACCESS | 未授权访问 | 请先登录 |
| 1005 | SESSION_EXPIRED | 会话已过期 | 请重新打开应用 |
| 1006 | NAVIGATION_FAIL | 导航失败 | 检查window.location和router配置 |
| 1007 | TAB_SWITCH_FAIL | Tab切换失败 | 检查tab-bar组件的onclick处理 |

### 2.2 数据渲染错误（11xx）

| 错误码 | 名称 | 说明 | 排查方向 |
|--------|------|------|----------|
| 1101 | DATA_FETCH_FAILED | 数据获取失败 | 检查网络后重试 |
| 1102 | DATA_PARSE_FAILED | 数据解析失败 | 请更新应用版本 |
| 1103 | DATA_RENDER_FAILED | 数据渲染失败 | 刷新页面 |
| 1104 | LIST_EMPTY | 列表数据为空 | 暂无数据 |
| 1105 | DETAIL_NOT_FOUND | 详情数据不存在 | 检查数据是否已删除 |
| 1106 | IMAGE_LOAD_FAILED | 图片加载失败 | 刷新页面重试 |
| 1107 | STORAGE_READ_FAILED | 读取本地存储失败 | 尝试清除浏览器缓存 |
| 1108 | STORE_INIT_FAIL | Store初始化失败 | 检查localStorage，状态管理 |
| 1109 | STATE_UPDATE_FAIL | 状态更新失败 | 检查subscribe/notify模式 |

### 2.3 用户输入错误（12xx）

| 错误码 | 名称 | 说明 | 排查方向 |
|--------|------|------|----------|
| 1201 | INPUT_EMPTY | 输入内容为空 | 请输入情境描述或选择标签 |
| 1202 | INPUT_TOO_LONG | 输入内容过长 | 请控制在2000字以内 |
| 1203 | INPUT_INVALID_CHAR | 输入包含无效字符 | 请检查输入内容 |
| 1204 | TAG_REQUIRED | 至少选择一个标签 | 请选择至少一个快捷标签 |
| 1205 | FEEDBACK_RATING_REQUIRED | 请选择训练效果 | 选择一个效果选项 |
| 1206 | FEEDBACK_COUNT_REQUIRED | 请选择训练次数 | 选择一个次数选项 |
| 1207 | FORM_INCOMPLETE | 表单填写不完整 | 请完成所有必填项 |
| 1208 | INPUT_INVALID | 输入无效 | 检查输入格式校验 |

---

## 3. 后端错误码（2xxx）

### 3.1 参数验证错误（20xx）

| 错误码 | 名称 | HTTP状态码 | 说明 | 排查方向 |
|--------|------|------------|------|----------|
| 2001 | INVALID_REQUEST_FORMAT | 400 | 请求格式错误 | 检查Content-Type和请求体 |
| 2002 | MISSING_REQUIRED_PARAM | 400 | 缺少必填参数 | 检查请求参数 |
| 2003 | INVALID_PARAM_TYPE | 400 | 参数类型错误 | 检查参数格式和类型 |
| 2004 | INVALID_PARAM_VALUE | 400 | 参数值超出范围 | 检查参数取值范围 |
| 2005 | INVALID_UUID | 400 | UUID格式错误 | 检查scenario_id格式 |
| 2006 | INVALID_DATE_FORMAT | 400 | 日期格式错误 | 使用YYYY-MM-DD格式 |
| 2007 | INVALID_DAY_RANGE | 400 | 天数超出范围（应1-14） | day参数应为1-14 |

### 3.2 业务逻辑错误（21xx）

| 错误码 | 名称 | HTTP状态码 | 说明 | PRD对应 |
|--------|------|------------|------|---------|
| 2101 | SCENARIO_NOT_FOUND | 404 | 情境不存在 | 5001 scenario_not_found |
| 2102 | TASK_NOT_FOUND | 404 | 任务不存在 | 5002 task_not_found |
| 2103 | FEEDBACK_NOT_FOUND | 404 | 反馈记录不存在 | - |
| 2104 | DAY_NOT_FOUND | 404 | 指定天数不存在 | 5002 day not found |
| 2105 | SCENARIO_COMPLETED | 400 | 情境已完成，不可修改 | - |
| 2106 | SCENARIO_DELETED | 400 | 情境已删除 | - |
| 2107 | MAX_SCENARIOS_REACHED | 400 | 已达最大情境数量（3个） | 情境槽位机制 |
| 2108 | DUPLICATE_FEEDBACK | 400 | 已提交过今日反馈 | - |
| 2109 | INVALID_STATUS_TRANSITION | 400 | 状态流转无效 | 状态机规则 |
| 2110 | OPERATION_NOT_ALLOWED | 403 | 操作不被允许 | - |
| 2111 | STATUS_INVALID | 400 | 状态无效 | 检查场景状态机转换 |
| 2112 | PROGRESS_NOT_FOUND | 404 | 进度不存在 | 检查localStorage |

### 3.3 数据库错误（22xx）

| 错误码 | 名称 | HTTP状态码 | 说明 |
|--------|------|------------|------|
| 2201 | DATABASE_CONNECTION | 500 | 数据库连接失败 |
| 2202 | DATABASE_QUERY_FAILED | 500 | 数据库查询失败 |
| 2203 | DATABASE_WRITE_FAILED | 500 | 数据库写入失败 |
| 2204 | DATABASE_TRANSACTION_FAILED | 500 | 数据库事务失败 |

### 3.4 外部服务错误（23xx）

| 错误码 | 名称 | HTTP状态码 | 说明 |
|--------|------|------------|------|
| 2301 | DEEPSEEK_ERROR | 500 | DeepSeek API错误 |
| 2302 | DEEPSEEK_TIMEOUT | 504 | DeepSeek超时（60s） |
| 2303 | DEEPSEEK_PARSE_ERROR | 500 | DeepSeek响应解析错误 |

---

## 4. API错误码（3xxx）

### 4.1 HTTP 200 成功（业务错误在data中）

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 3000 | SUCCESS | 操作成功 |
| 3001 | SUCCESS_WITH_WARNING | 操作成功但有警告 |

### 4.2 HTTP 400 客户端错误

| 错误码 | 名称 | 说明 | PRD对应 |
|--------|------|------|---------|
| 4001 | INVALID_INPUT | 输入无效 | INVALID_INPUT |
| 4002 | INPUT_TOO_LONG | 输入过长（>2000字） | INPUT_TOO_LONG |
| 4003 | CLARIFICATION_NEEDED | 需要澄清情境 | CLARIFICATION_NEEDED |
| 4004 | PACKAGE_NOT_FOUND | 任务包不存在 | package_not_found |
| 4005 | SCENARIO_COMPLETED_CANNOT_DELETE | 已完成情境不可删除 | scenario_completed_cannot_delete |

### 4.3 HTTP 404 资源不存在

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 4401 | NOT_FOUND | 资源不存在 |
| 4402 | SCENARIO_NOT_FOUND | 情境不存在 |
| 4403 | TASK_NOT_FOUND | 任务不存在 |
| 4404 | DAY_NOT_FOUND | 天数不存在 |

### 4.4 HTTP 422 参数验证错误

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 4201 | VALIDATION_ERROR | 参数验证失败 |
| 4202 | MISSING_FIELD | 缺少字段 |
| 4203 | INVALID_FIELD_TYPE | 字段类型错误 |

### 4.5 HTTP 500 服务端错误

| 错误码 | 名称 | 说明 | PRD对应 |
|--------|------|------|---------|
| 5000 | INTERNAL_ERROR | 内部错误 | - |
| 5001 | AI_GENERATION_FAILED | AI服务调用失败 | AI_GENERATION_FAILED |
| 5002 | DELETE_FAILED | 删除操作失败 | delete_failed |
| 5003 | DATABASE_ERROR | 数据库操作失败 | - |

### 4.6 HTTP 504 超时错误

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 5401 | AI_TIMEOUT | DeepSeek调用超时（前端超时30s） |
| 5402 | EXTERNAL_SERVICE_TIMEOUT | 外部服务超时 |

---

## 5. 第三方服务错误码（4xxx）

### 5.1 DeepSeek API错误（41xx）

| 错误码 | 名称 | HTTP状态码 | 说明 |
|--------|------|------------|------|
| 4101 | DEEPSEEK_API_KEY_INVALID | 401 | API密钥无效 |
| 4102 | DEEPSEEK_API_KEY_MISSING | 401 | 缺少API密钥 |
| 4103 | DEEPSEEK_RATE_LIMIT | 429 | 请求频率超限 |
| 4104 | DEEPSEEK_TIMEOUT | 504 | DeepSeek请求超时 |
| 4105 | DEEPSEEK_SERVER_ERROR | 500 | DeepSeek服务器错误 |
| 4106 | DEEPSEEK_INVALID_RESPONSE | 502 | DeepSeek响应格式错误 |
| 4107 | DEEPSEEK_UNAVAILABLE | 503 | DeepSeek服务不可用 |

### 5.2 NVIDIA NIM备用API错误（42xx）

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 4201 | NVIDIA_API_KEY_INVALID | API密钥无效 |
| 4202 | NVIDIA_TIMEOUT | 请求超时 |
| 4203 | NVIDIA_SERVER_ERROR | 服务器错误 |
| 4204 | NVIDIA_UNAVAILABLE | 服务不可用 |

### 5.3 ChromaDB向量库错误（43xx）

| 错误码 | 名称 | 说明 |
|--------|------|------|
| 4301 | CHROMA_CONNECTION_FAILED | 连接向量库失败 |
| 4302 | CHROMA_QUERY_FAILED | 向量检索失败 |
| 4303 | CHROMA_COLLECTION_NOT_FOUND | Collection不存在 |

---

## 6. PRD对照表

### 6.1 PRD错误码映射

| PRD错误码 | 本文档错误码 | 说明 |
|-----------|-------------|------|
| INVALID_INPUT | 4001 | raw_input为空且无selected_tags |
| INPUT_TOO_LONG | 4002 | raw_input超过2000字 |
| CLARIFICATION_NEEDED | 4003 | AI判断需要澄清情境 |
| AI_GENERATION_FAILED | 5001 | AI服务调用失败 |
| AI_TIMEOUT | 5401 | DeepSeek调用超时 |
| scenario_not_found | 2101/4402 | 情境不存在 |
| task_not_found | 2102/4403 | 任务不存在 |
| package_not_found | 4004 | 任务包不存在 |
| scenario_completed_cannot_delete | 4005 | 已完成情境不可删除 |
| delete_failed | 5002 | 删除操作失败 |

### 6.2 快速定位表

| 场景 | 错误码 |
|------|--------|
| 页面加载失败 | 1002 |
| 数据获取失败 | 1101 |
| 输入为空 | 1201 |
| 输入过长 | 1202 |
| 反馈效果未选 | 1205 |
| 反馈次数未选 | 1206 |
| API资源不存在 | 4401 |
| DeepSeek超时 | 4104/5401 |
| 情境不存在 | 2101/4402 |

---

## 7. 错误处理流程

### 7.1 前端错误处理流程

```
用户操作
    ↓
调用API
    ↓
┌─────────────────────────┐
│  成功（HTTP 200）        │
│  检查 code 字段          │
│  code=0 → 正常处理        │
│  code≠0 → 显示错误信息    │
└─────────────────────────┘
    ↓
┌─────────────────────────┐
│  失败（HTTP 4xx/5xx）    │
│  显示错误码对应提示       │
│  提供重试选项            │
└─────────────────────────┘
```

### 7.2 后端降级流程（三层降级）

```
请求到达
    ↓
┌─────────────────────────┐
│ Layer 1: DeepSeek API    │
│  - 超时: 60s            │
│  - 重试: 2次            │
│  - 状态码: 500/502/503   │
└─────────────────────────┘
         ↓ 失败
┌─────────────────────────┐
│ Layer 2: NVIDIA NIM      │
│  - 超时: 60s            │
│  - 需要配置BACKUP_MODEL_* │
└─────────────────────────┘
         ↓ 失败
┌─────────────────────────┐
│ Layer 3: Mock数据        │
│  - MOCK_MODE=true       │
│  - 返回预存L1数据        │
│  - 固定200ms延迟         │
└─────────────────────────┘
```

### 7.3 错误日志格式

```json
{
  "timestamp": "2026-05-07T12:00:00Z",
  "error_code": "2101",
  "error_name": "SCENARIO_NOT_FOUND",
  "layer": "backend",
  "message": "情境不存在: scenario_id=xxx",
  "request": {
    "method": "GET",
    "path": "/api/scenarios/xxx",
    "params": {}
  },
  "details": {},
  "stack": "..."
}
```

---

## 附录：错误码速查表

### A. 前端错误速查

| 场景 | 错误码 |
|------|--------|
| 页面不存在 | 1001 |
| 页面加载失败 | 1002 |
| 重定向循环 | 1003 |
| 会话过期 | 1005 |
| 数据获取失败 | 1101 |
| 数据解析失败 | 1102 |
| 数据渲染失败 | 1103 |
| 列表为空 | 1104 |
| 输入为空 | 1201 |
| 输入过长 | 1202 |
| 效果未选 | 1205 |
| 次数未选 | 1206 |

### B. API错误速查

| API | 错误场景 | 错误码 |
|-----|----------|--------|
| 任意 | 成功 | 3000 |
| 任意 | 资源不存在 | 4401 |
| POST /api/task-packages/generate | 空输入 | 4001 |
| POST /api/task-packages/generate | 输入过长 | 4002 |
| POST /api/task-packages/generate | 需要澄清 | 4003 |
| POST /api/task-packages/generate | AI生成失败 | 5001 |
| POST /api/task-packages/generate | 超时 | 5401 |
| GET /api/scenarios/{id} | 情境不存在 | 4402 |
| DELETE /api/scenarios/{id} | 已完成不可删除 | 4005 |
| POST /api/scenarios/{id}/feedback | 情境不存在 | 4402 |
| GET /api/scenarios/{id}/days/{day} | 天数不存在 | 4404 |

### C. 第三方服务错误速查

| 服务 | 错误场景 | 错误码 |
|------|----------|--------|
| DeepSeek | API密钥无效 | 4101 |
| DeepSeek | 频率超限 | 4103 |
| DeepSeek | 超时 | 4104 |
| DeepSeek | 服务器错误 | 4105 |
| NVIDIA NIM | 超时 | 4202 |
| NVIDIA NIM | 服务不可用 | 4204 |
| ChromaDB | 连接失败 | 4301 |

---

## 前端错误上报示例

```javascript
// 在页面中添加错误追踪
window.onerror = function(msg, url, line, col, error) {
    console.error({
        error_code: '1103',  // RENDER_FAIL
        message: msg,
        url: url,
        line: line,
        col: col
    });
    return false;
};

// API错误处理
async function handleApiError(response) {
    const data = await response.json();
    if (data.code !== 0) {
        console.error({
            error_code: data.code,
            message: data.message,
            details: data.details
        });
        // 显示用户友好的错误提示
        showErrorToast(getErrorMessage(data.code));
    }
}
```

---

**文档版本**：v1.0
**最后更新**：2026-05-07
