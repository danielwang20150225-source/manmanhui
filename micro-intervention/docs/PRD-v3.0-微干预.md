# 慢慢会·微干预 产品需求文档 v3.0

> **维护者**：PM Agent  
> **版本**：v3.0  
> **日期**：2026-05-05  
> **状态**：已发布，用于Sprint 1开发

---

## 目录

1. [产品概述](#1-产品概述)
2. [用户角色与用户故事](#2-用户角色与用户故事)
3. [功能模块详解](#3-功能模块详解)
4. [字段定义](#4-字段定义)
5. [API契约](#5-api契约)
6. [数据模型](#6-数据模型)
7. [状态机](#7-状态机)
8. [v2.1→v3.0变更说明](#8-v21→v30变更说明)
9. [已知风险与注意事项](#9-已知风险与注意事项)

---

## 1. 产品概述

### 1.1 产品背景

微干预定位为 **ASD儿童家庭干预工具**，服务于ASD儿童家庭——孩子是最终受益者，家长端是执行手段。

核心洞察：ASD儿童的核心障碍体现在社交互动、语言沟通、行为模式和感觉处理等多个维度，且这些问题往往在具体生活情境中才真实暴露。家长最需要的，不是理论课程，而是一个能**在真实情境中引导孩子逐步适应的工具**。

### 1.2 核心价值主张

> **让每一个情境问题，都能转化成为一次有效干预**

产品不追求"有趣"或"低门槛"，而追求**专业、有效、不制造焦虑**。训练方案基于行为干预（ABA）原理和感觉统合理论，通过每日短时训练（5-12分钟）持续渗透。

### 1.3 核心流程

```
添加情境 → AI生成14天训练方案 → 每日训练 → 记录反馈 → 追踪进度
```

1. **添加情境**：家长描述孩子的问题行为或困难情境（语音/文字），选择快捷标签
2. **生成方案**：AI分析情境，生成14天渐进式训练计划（每天含3-5个步骤）
3. **每日训练**：家长按步骤引导孩子练习，记录完成情况
4. **反馈记录**：记录当天训练效果（顺利/一般/有点难）和训练次数
5. **进度追踪**：查看累计数据、连续天数、历史记录

### 1.4 产品原则（Daniel底线）

- 做ASD儿童干预产品，绝对不能负面影响孩子的干预效果
- 每次训练以"孩子真正进步"为唯一标准
- 不做空洞正向鼓励，不给家长制造焦虑
- MVP优先，砍功能不手软

### 1.5 品牌调性

- 温暖但不幼稚，专业但不高冷
- **禁止卡通化**：无emoji logo、无幼稚图案、无表情包化
- 色彩体系：
  - 背景色：#F7F4F0
  - 卡片色：#FFFFFF
  - 强调色：#7CB342
  - 文字主色：#2D2D2D
  - 文字次色：#6B6B6B

---

## 2. 用户角色与用户故事

### 2.1 角色定义

| 角色 | 描述 | 使用场景 |
|------|------|----------|
| **家长（主用户）** | 干预执行者、训练记录者、方案观察者 | 添加情境、查看训练方案、执行每日训练、记录反馈、追踪进度 |
| **孩子（最终受益者）** | 训练的被动接受者，家长的观察对象 | 练习页（v3.0为占位模块，暂无实际功能） |

---

### 2.2 用户故事总表

#### 故事簇A：添加情境

| # | 用户故事 | 验收标准 |
|---|---------|----------|
| **A1** | 作为家长，我想要快速描述孩子的问题情境，以便AI能生成针对性的训练方案 | 输入文字或选择快捷标签即可描述情境；语音输入可替代打字 |
| **A2** | 作为家长，我想要看到AI正在为我生成方案的过程，以免我以为系统卡死了 | 点击生成后显示loading状态和进度提示 |
| **A3** | 作为家长，我想要在输入为空时看到明确提示，以便我知道如何修正 | 空输入时按钮变红并显示提示 |
| **A4** | 作为家长，我想要在AI生成失败时看到明确的错误信息，以便我决定是否重试 | 显示具体错误码和可操作提示 |

#### 故事簇B：查看训练方案

| # | 用户故事 | 验收标准 |
|---|---------|----------|
| **B1** | 作为家长，我想要在进入训练前了解方案的核心目标和注意事项，以便做好准备 | package.html展示核心目标+折叠注意事项 |
| **B2** | 作为家长，我想要一键开始今天的训练，以便快速进入执行状态 | 点击"开始第1天训练"直接跳转training.html |
| **B3** | 作为家长，我想要能返回首页查看所有情境列表，以便管理多个情境 | 点击"返回首页"跳转index.html |

#### 故事簇C：执行每日训练

| # | 用户故事 | 验收标准 |
|---|---------|----------|
| **C1** | 作为家长，我想要看到今日的训练目标、步骤和每步预计时长，以便合理安排时间 | 页面展示goal、steps列表、estimated_duration_seconds |
| **C2** | 作为家长，我想要在训练结束后记录效果，以便追踪孩子进步 | 点击"我完成了今天的训练"跳转feedback.html |
| **C3** | 作为家长，我想要在训练过程中能看到当前进度，以便知道还剩多少 | 页面顶部有当日进度条（当天内步骤进度） |
| **C4** | 作为家长，我想要能随时退出训练而不丢失进度，以便灵活安排 | 返回按钮可用，退出后数据不丢失 |

#### 故事簇D：记录训练反馈

| # | 用户故事 | 验收标准 |
|---|---------|----------|
| **D1** | 作为家长，我想要选择今天训练的效果（顺利/一般/有点难），以便记录真实反馈 | 三个emoji按钮，必选 |
| **D2** | 作为家长，我想要记录今天练了几次，以便了解训练密度 | 三个次数选项，必选 |
| **D3** | 作为家长，我想要补充文字备注，以便记录更多细节 | textarea选填，有placeholder引导 |
| **D4** | 作为家长，我想要在未填写必选项时看到提示，以便知道为何无法提交 | 按钮disabled时显示hint文字 |
| **D5** | 作为家长，我想要在提交成功后返回首页，以便继续其他操作 | 提交后跳转index.html |

#### 故事簇E：追踪训练进度

| # | 用户故事 | 验收标准 |
|---|---------|----------|
| **E1** | 作为家长，我想要在首页看到所有情境的整体进度，以便知道哪些在进行中 | index.html展示情境卡片列表+进度条 |
| **E2** | 作为家长，我想要进入情境详情页查看累计训练次数和连续天数，以便评估整体进展 | task-detail.html展示概览数据 |
| **E3** | 作为家长，我想要查看训练历史记录，以便回顾孩子的进步轨迹 | history.html展示所有训练记录 |
| **E4** | 作为家长，我想要在没有情境时看到引导提示，以便知道如何开始 | 空状态展示CTA按钮"添加第一个情境" |

---

## 3. 功能模块详解

### 3.1 首页（index.html）—— 家长干预首页

#### 3.1.1 功能概述

展示用户所有训练情境的列表视图，支持快速进入进行中的训练。

#### 3.1.2 用户故事

- **US-A1**：作为家长，我想要看到所有情境的整体进度，以便知道哪些在训练中
- **US-A4**：作为家长，我想要在没有情境时看到引导提示，以便知道如何开始

#### 3.1.3 主场景（正常流程）

```
1. 用户打开index.html
2. 系统检查本地存储/调用GET /api/scenarios
3. 有数据 → 展示情境卡片列表
   无数据 → 展示空状态+CTA按钮
4. 用户点击情境卡片 → 跳转task-detail.html
5. 用户点击"+ 添加情境" → 跳转input.html
```

#### 3.1.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 空状态 | scenarios数组为空 | 显示empty-state区域，隐藏card-list |
| 有数据 | scenarios数组有记录 | 显示card-list，隐藏empty-state |
| 加载中 | API调用中 | 显示loading状态（可省略MVP阶段） |
| 网络错误 | API返回错误 | 显示错误提示，提供重试按钮 |

#### 3.1.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 打开index.html | scenarios列表或空数组 | 卡片列表或空状态 |
| 查看进度 | 查看卡片 | progress_percent计算 | 进度条填充21%/50%/100% |
| 进入详情 | 点击卡片 | 跳转task-detail.html | 页面切换 |
| 添加情境 | 点击添加情境 | 跳转input.html | 页面切换 |
| 退出 | 点击Tab栏其他项 | 跳转对应页面 | 页面切换 |

#### 3.1.6 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 标题"家长干预" + "+ 添加情境"按钮 |
| 空状态 | 首次使用引导，提示添加第一个情境 |
| 情境卡片列表 | 所有情境卡片，含状态、进度 |
| 底部Tab栏 | 家长干预（当前）/ 孩子练习 / 我的 |

#### 3.1.7 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| scenario_title | 情境标题 | string | emoji+文字，如"👕 穿衣抗拒" | [AI]从raw_input提取 | 展示用标题 |
| scenario_status | 状态标签 | enum | active/completed/abandoned | [S]从scenarios.status计算 | 徽章样式不同 |
| current_day | 当前天数 | int | 1-14 | [S]scenarios.current_day | 格式"第N天/共M天" |
| total_days | 总天数 | int | 固定14 | [K]固定值 | 共M天 |
| progress_percent | 进度百分比 | int | 0-100 | [S]current_day/total_days*100 | 进度条填充宽度 |

---

### 3.2 添加情境页（input.html）

#### 3.2.1 功能概述

家长输入孩子的问题情境，支持语音和文字两种输入方式，可选择快捷标签辅助描述。

#### 3.2.2 用户故事

- **US-B1**：作为家长，我想要快速描述孩子的问题情境，以便AI能生成针对性的训练方案
- **US-B2**：作为家长，我想要看到AI正在为我生成方案的过程，以免我以为系统卡死了
- **US-B3**：作为家长，我想要在输入为空时看到明确提示，以便我知道如何修正

#### 3.2.3 主场景（正常流程）

```
1. 用户打开input.html
2. 用户输入文字描述 OR 选择快捷标签 OR 两者都做
3. 用户点击"开始生成训练方案"
4. 系统验证：raw_input_text和selected_tags至少填一项
   → 验证通过 → 显示loading遮罩
   → 验证失败 → 按钮变红0.6秒提示，返回步骤2
5. 调用POST /api/task-packages/generate
6. 成功 → 跳转package.html
7. 失败 → 显示错误提示，用户可重新输入或重试
```

#### 3.2.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 空输入+无标签 | 点击生成但两者都为空 | 按钮变红0.6秒提示，不可提交 |
| 仅语音输入 | 用户按住语音按钮 | 显示"正在聆听..."，松开结束录音 |
| 语音+文字 | 用户同时有语音和文字 | 两者都作为AI输入 |
| 仅选标签 | 用户只选快捷标签 | raw_input_text为空，selected_tags有值，可生成 |
| 生成中 | API调用中 | 显示loading遮罩，按钮disabled |
| 生成失败 | API返回错误 | 显示错误信息，用户可重试或返回 |
| 超时 | 30秒内未收到响应 | 显示超时提示，提供重试按钮 |

#### 3.2.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 打开input.html | 空白表单 | 空白的输入区域和标签 |
| 输入文字 | 打字 | 实时更新textarea | 文字显示 |
| 选择标签 | 点击tag-chip | toggle selected状态 | 标签变绿 |
| 空提交 | 点击生成按钮（无输入） | 按钮变红，0.6秒后恢复 | 红色闪烁提示 |
| 提交成功 | 点击生成（有输入） | loading遮罩显示 | "正在分析情境" |
| 生成完成 | API返回200 | 跳转package.html | 方案展示页 |
| 生成失败 | API返回错误 | 显示错误toast | 错误信息 |
| 返回 | 点击返回按钮 | 跳转index.html | 首页 |

#### 3.2.6 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 返回按钮 + 标题"描述孩子的情况" |
| Tagline | 让每一个情境问题，都能转化成为一次有效干预 |
| 主卡片 | 语音输入区 + 文字输入区 + 分割线 |
| 快捷标签 | 可多选的场景标签chips |
| 底部按钮 | "开始生成训练方案" |
| Loading遮罩 | 生成方案时显示，不可关闭 |

#### 3.2.7 快捷标签选项（preset）

| 标签名 | 说明 |
|--------|------|
| 社交回避 | 回避目光接触或社交互动 |
| 叫名字不应 | 对名字呼唤无反应 |
| 情绪崩溃 | 情绪爆发、哭闹 |
| 穿衣抗拒 | 抗拒换衣服 |
| 眼神不对视 | 避免眼神接触 |
| 刻板行为 | 重复刻板动作 |

#### 3.2.8 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| raw_input_text | 情境描述文本 | string | 最长2000字 | [U]用户输入 | textarea字段 |
| selected_tags | 快捷标签 | string[] | 从预设列表选择，可多选 | [U]用户选择 | 数组形式 |
| voice_input | 语音输入 | binary | 录音二进制 | [U]语音采集 | 按住说话，松开结束 |
| voice_status | 语音状态 | enum | idle/recording | [S]系统状态 | UI状态切换 |

#### 3.2.9 校验规则

| 规则 | 触发 | 行为 |
|------|------|------|
| 非空校验 | 点击生成时 | raw_input_text和selected_tags至少填一项，否则按钮变红0.6秒 |
| 长度校验 | 输入时 | raw_input_text超过2000字时显示字符计数 |

---

### 3.3 任务包生成结果页（package.html）

#### 3.3.1 功能概述

展示AI生成的14天训练方案概览，包含核心目标、训练注意事项，支持一键开始训练。

#### 3.3.2 用户故事

- **US-C1**：作为家长，我想要在进入训练前了解方案的核心目标和注意事项，以便做好准备
- **US-C2**：作为家长，我想要一键开始今天的训练，以便快速进入执行状态

#### 3.3.3 主场景（正常流程）

```
1. 用户从input.html跳转到package.html
2. 系统展示：情境emoji+标题+天数标签+核心目标+折叠的注意事项
3. 用户可点击"训练注意事项"展开/折叠
4. 用户点击"开始第1天训练" → 跳转training.html
5. 或点击"返回首页" → 跳转index.html
```

#### 3.3.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 首次查看 | 新生成的方案 | 折叠区域默认收起 |
| 展开注意事项 | 点击折叠header | max-height动画展开，箭头旋转180° |
| 收起注意事项 | 再次点击 | 收起动画 |
| 训练已开始 | 从task-detail.html重新进入 | 按钮文字变为"继续第N天训练" |

#### 3.3.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 从input.html跳转 | 完整的方案数据 | 方案展示卡片 |
| 查看目标 | 页面加载 | core_goal.title + core_goal.content | 目标标题+说明 |
| 展开注意事项 | 点击折叠 | 动画展开 | 7条注意事项列表 |
| 开始训练 | 点击主按钮 | 跳转training.html | 训练执行页 |
| 返回首页 | 点击次级按钮 | 跳转index.html | 首页 |

#### 3.3.6 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 返回按钮 + "任务包已生成" |
| 主卡片 | 情境emoji + 标题 + 天数标签 + 核心目标 + 折叠注意事项 |
| 底部按钮 | "开始第N天训练" + "返回首页" |

#### 3.3.7 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| scenario_emoji | 情境emoji | string | 单个emoji | [AI]从raw_input推断 | 展示用 |
| scenario_title | 情境标题 | string | emoji+文字 | [AI]从raw_input提取 | 同index.title |
| package_days | 方案天数 | int | 固定14 | [K]固定值 | 不可更改 |
| core_goal_title | 核心目标标题 | string | 简短目标描述 | [AI]生成 | 如"配合伸手进袖子" |
| core_goal_content | 核心目标内容 | string | 详细说明 | [AI]生成 | 含原理说明 |
| training_notes | 训练注意事项 | string[] | 折叠展示 | [AI]生成 | 最多8条 |
| start_day_button | 开始训练按钮文字 | string | "开始第N天训练" | [S]固定文案+天数 | N=1或current_day |

#### 3.3.8 折叠注意事项内容

1. 训练时保持环境安静，避免强光直射
2. 每次训练时间控制在5-12分钟内
3. 必须在孩子情绪平稳时进行训练
4. 使用零食强化时，即时给予不要延迟
5. 孩子哭闹时立即停止，不可强迫
6. 每天训练后记录孩子的反应和进步
7. 一个目标稳定后再进入下一个步骤

---

### 3.4 每日训练执行页（training.html）

#### 3.4.1 功能概述

家长执行当日训练的步骤引导页面，展示今日目标、提示卡和具体步骤列表。

#### 3.4.2 用户故事

- **US-D1**：作为家长，我想要看到今日的训练目标、步骤和每步预计时长，以便合理安排时间
- **US-D2**：作为家长，我想要在训练结束后记录效果，以便追踪孩子进步
- **US-D3**：作为家长，我想要在训练过程中能看到当前进度，以便知道还剩多少

#### 3.4.3 主场景（正常流程）

```
1. 用户从package.html或task-detail.html进入training.html
2. 系统展示：情境名·第N天/共M天 + 当日进度条 + 今日目标 + 提示卡 + 步骤列表
3. 用户按步骤执行训练（步骤仅展示，实际执行由家长线下完成）
4. 用户点击"我完成了今天的训练" → 跳转feedback.html
5. 用户可随时点击返回按钮退出（数据不丢失）
```

#### 3.4.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 查看步骤说明 | 页面加载 | 展示steps数组，每步骤含action+desc |
| 查看步骤时长 | 页面加载 | 每步骤显示estimated_duration_seconds |
| 退出训练 | 点击返回 | 保存当前进度，跳转index.html |
| 已完成当天 | 再次进入 | 按钮变为"查看反馈记录"或跳转feedback |

#### 3.4.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 页面加载 | nav_title + goal + tip + steps数组 | 完整训练引导页 |
| 查看目标 | 看goal-card | today_goal文字 | "配合伸手进袖子..." |
| 查看提示 | 看tip-card | tip_text暖黄色卡片 | "在孩子心情好的时候..." |
| 查看步骤 | 看step-list | steps[N].action + desc + duration | 步骤1/2/3及每步时长 |
| 完成训练 | 点击完成按钮 | 跳转feedback.html | 反馈记录页 |
| 退出 | 点击返回 | 跳转index.html | 首页 |

#### 3.4.6 页面结构

| 区域 | 说明 |
|------|------|
| 状态栏 | 时间 + 信号图标 |
| 导航栏 | 返回 + 情境名·第N天/共M天 |
| 进度条 | 当前进度（当天内步骤进度，非整体进度） |
| 今日目标卡片 | 目标文字展示 |
| 提示卡 | 暖黄色卡片，当日训练小贴士 |
| 步骤列表 | 序号+动作+描述+预计时长 |
| 底部按钮 | "我完成了今天的训练" |
| 底部Tab栏 | 家长干预 / 孩子练习 / 我的 |

#### 3.4.7 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| nav_title | 导航标题 | string | "情境名 · 第N天 / 共M天" | [S]拼接 | 如"穿衣抗拒 · 第3天 / 共14天" |
| progress_percent | 当日步骤进度 | int | 0-100 | [S]已完成步骤/总步骤*100 | 进度条填充 |
| today_goal | 今日目标 | string | 简短描述 | [AI]从days_data[N].goal提取 | 今日要达成的目标 |
| tip_text | 提示文案 | string | 建议性文字 | [AI]生成 | 如"在孩子心情好的时候练习" |
| steps | 步骤列表 | array | 每天3-5个步骤 | [AI]从days_data[N].steps获取 | 数组 |
| steps[N].step_index | 步骤序号 | int | 从1开始 | [S]索引 | 显示用 |
| steps[N].step_action | 步骤动作 | string | 动词短语，家长执行动作 | [AI]生成 | 如"用毛巾轻碰手背" |
| steps[N].step_desc | 步骤描述 | string | 详细说明+强化时机 | [AI]生成 | 如"说'摸一摸'，立刻给零食强化" |
| steps[N].estimated_duration_seconds | 预计时长（秒） | int | 60-180 | [AI]估算 | **v3.0新增**，每步骤预计时长 |

#### 3.4.8 步骤时长规范（v3.0修正）

- 每个步骤预计时长：60-180秒（1-3分钟）
- 单日总训练时长：5-12分钟（原型描述已修正）
- 不写具体分钟数，写"约X分钟"或直接显示秒数
- 训练页面提示文案：改为"每次5-12分钟即可"

---

### 3.5 训练反馈记录页（feedback.html）

#### 3.5.1 功能概述

训练完成后记录当天效果、训练次数和备注。

#### 3.5.2 用户故事

- **US-E1**：作为家长，我想要选择今天训练的效果（顺利/一般/有点难），以便记录真实反馈
- **US-E2**：作为家长，我想要记录今天练了几次，以便了解训练密度
- **US-E3**：作为家长，我想要补充文字备注，以便记录更多细节
- **US-E4**：作为家长，我想要在未填写必选项时看到提示，以便知道为何无法提交

#### 3.5.3 主场景（正常流程）

```
1. 用户从training.html进入feedback.html
2. 系统展示：完成提示 + 反馈表单（效果选择+次数选择+备注）
3. 用户选择效果（必选）+ 选择次数（必选）+ 可选填备注
4. 用户点击"提交反馈"
5. 系统调用POST /api/scenarios/{id}/feedback
6. 成功 → 跳转index.html
7. 失败 → 显示错误提示
```

#### 3.5.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 未选效果 | 点击提交但未选 | 按钮保持disabled，显示hint |
| 未选次数 | 点击提交但未选 | 按钮保持disabled，显示hint |
| 已选一项 | 只选了效果或次数 | 按钮保持disabled |
| 已选两项 | 效果+次数都选 | 按钮enabled，hint隐藏 |
| 部分填写 | 只有备注 | 按钮保持disabled |
| 提交中 | 点击提交按钮 | 按钮disabled，显示loading |
| 提交成功 | API返回201 | 跳转index.html |
| 提交失败 | API返回错误 | 显示错误toast，按钮恢复 |
| 查看已提交 | 重复进入当天 | 显示已完成状态，跳转index.html |

#### 3.5.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 从training.html跳转 | completion_title + date | "第N天训练已完成"+日期 |
| 选择效果 | 点击emoji-btn | 选中高亮，选中状态存入变量 | 绿色边框+背景 |
| 选择次数 | 点击count-btn | 选中高亮 | 绿色边框+背景 |
| 填写备注 | 输入textarea | 实时更新 | 文字显示 |
| 未完成必填 | 点击提交 | 按钮disabled+hint显示 | "请先选择效果和训练次数" |
| 完成必填 | 选择两项 | 按钮enabled | 按钮变绿可点击 |
| 提交成功 | 点击提交 | 跳转index.html | 首页 |

#### 3.5.6 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 返回 + "记录今日训练" |
| 完成提示区 | 大图标 + "第N天训练已完成" + 日期 |
| 反馈表单卡片 | 效果选择 + 次数选择 + 备注 |
| 底部按钮 | 提交反馈（需必填） |

#### 3.5.7 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| completion_title | 完成标题 | string | "第N天训练已完成" | [S]拼接 | 动态天数 |
| completion_date | 完成日期 | string | YYYY-MM-DD | [S]当前日期 | 展示用 |
| scenario_name | 情境名 | string | 如"穿衣抗拒" | [S]从context获取 | 完成提示用 |
| feedback_rating | 效果选择 | enum | good/neutral/bad | [U]用户选择 | **v3.0新增**，必填 |
| train_count | 训练次数 | enum | "1~2次"/"3~5次"/"5次+" | [U]用户选择 | 必填 |
| feedback_notes | 备注文字 | string | 最长500字 | [U]用户输入 | 选填 |

#### 3.5.8 反馈选项映射

| UI展示 | feedback_rating值 | 说明 |
|--------|-------------------|------|
| 😊 顺利 | good | 孩子配合，无抗拒 |
| 😐 一般 | neutral | 有配合但需辅助 |
| 😣 有点难 | bad | 哭闹或强烈抗拒 |

#### 3.5.9 交互规则

- feedback_rating 和 train_count 均为必填，二选一未选时提交按钮禁用
- disabled按钮样式：背景#E0E0E0，文字#ADADAD，对比度足够
- 提交后 → 跳转 index.html

---

### 3.6 情境详情页（task-detail.html）

#### 3.6.1 功能概述

单个情境的详细视图，展示整体进度、概览数据、核心目标和最近训练记录。

#### 3.6.2 用户故事

- **US-F1**：作为家长，我想要查看情境的整体进度和数据统计，以便评估训练效果

#### 3.6.3 主场景（正常流程）

```
1. 用户从index.html点击情境卡片进入task-detail.html
2. 系统展示：进度头部 + 概览数据 + 核心目标 + 最近训练记录
3. 用户点击"继续今天的训练" → 跳转training.html
4. 或点击"查看全部训练记录" → 跳转history.html
5. 或点击返回 → 跳转index.html
```

#### 3.6.4 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 进行中 | status=active | 显示"进行中"badge |
| 已完成 | status=completed | 显示"已完成"badge |
| 无记录 | recent_records为空 | 显示空状态提示 |
| 最后一天 | current_day=14 | 按钮显示"完成最后一天训练" |

#### 3.6.5 闭环验证

| 步骤 | 操作 | 系统返回 | 用户看到 |
|------|------|----------|----------|
| 入口 | 从index.html点击 | scenario详情数据 | 进度页 |
| 查看进度 | 看progress-header | progress_percent=21% | 进度条21% |
| 查看数据 | 看overview-cards | total_train_count + consecutive_days | 6次训练/连续3天 |
| 查看目标 | 看goal-card | core_goal.title + desc | 本阶段核心目标 |
| 查看最近 | 看history-list | 最近3条记录 | 3条训练记录 |
| 继续训练 | 点击主按钮 | 跳转training.html | 训练页 |
| 查看全部 | 点击次按钮 | 跳转history.html | 历史页 |
| 返回 | 点击返回 | 跳转index.html | 首页 |

#### 3.6.6 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 返回 + "情境详情" |
| 进度头部 | emoji+标题+状态badge + 进度条 + 剩余天数 |
| 概览数据 | 累计训练次数 + 连续训练天数 |
| 核心目标 | 本阶段核心目标标题+描述 |
| 最近训练 | 最近3条训练记录（emoji+日期+详情+次数） |
| 底部按钮 | "继续今天的训练" + "查看全部训练记录" |

#### 3.6.7 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| scenario_emoji | 情境emoji | string | 单个emoji | [AI]从raw_input推断 | 同package |
| scenario_title | 情境标题 | string | emoji+文字 | [AI]从raw_input提取 | 同index |
| scenario_status | 状态badge | enum | active/completed | [S]scenarios.status | 进行中/已完成样式不同 |
| current_day | 当前天数 | int | 1-14 | [S]scenarios.current_day | 格式"第N天/共M天" |
| total_days | 总天数 | int | 固定14 | [K]固定值 | 共M天 |
| progress_percent | 整体进度 | int | 0-100 | [S]current_day/total_days*100 | 进度条 |
| days_remaining | 剩余天数 | int | 0-13 | [S]total_days - current_day | 底部标签 |
| total_train_count | 累计训练次数 | int | >=0 | [S]sum(daily_task_status.train_count) | 概览卡片 |
| consecutive_days | 连续训练天数 | int | >=0 | [S]count(连续日期段) | 概览卡片，需计算 |
| core_goal_main | 核心目标主标题 | string | 简短目标 | [AI]从scenarios.goal提取 | 标题 |
| core_goal_desc | 核心目标说明 | string | 详细说明 | [AI]从scenarios.goal提取 | 描述 |
| recent_records | 最近训练记录 | array | 最多3条 | [S]从daily_task_status查询 | 时间倒序 |
| recent_records[N].emoji | 表情emoji | string | 😊/😐/😣 | [S]从feedback_rating映射 | 背景色不同 |
| recent_records[N].date | 记录日期 | string | "今天"/"昨天"/"前天 · 第N天" | [S]日期格式化 | 动态 |
| recent_records[N].detail | 记录详情 | string | 备注文字前50字 | [U]feedback_notes | 有备注才显示 |
| recent_records[N].train_count | 训练次数 | string | "练了N次" | [S]从train_count格式化 | 显示在标签 |

---

### 3.7 训练历史页（history.html）

#### 3.7.1 功能概述

展示单个情境的全部训练记录，按月分组，含统计汇总。

#### 3.7.2 主场景（正常流程）

```
1. 用户从task-detail.html点击"查看全部训练记录"进入history.html
2. 系统展示：情境标题栏 + 统计数据 + 月份分组列表
3. 用户点击返回 → 跳转task-detail.html
```

#### 3.7.3 分支场景

| 场景 | 触发条件 | 系统行为 |
|------|----------|----------|
| 无记录 | records数组为空 | 显示空状态"还没有训练记录" |
| 单月 | 只有一个月份 | 只显示一个月份分组 |
| 多月 | 跨月记录 | 按月份分组，每组标题"YYYY年M月" |

#### 3.7.4 页面结构

| 区域 | 说明 |
|------|------|
| 顶部导航 | 返回 + "训练记录" |
| 情境标题栏 | emoji+情境名+训练次数 |
| 统计数据行 | 顺利次数 / 一般次数 / 有点难次数 |
| 月份分组列表 | 按月展示所有训练记录 |

#### 3.7.5 字段定义

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| scenario_emoji | 情境emoji | string | 单个emoji | [AI]同前 | 标题栏用 |
| scenario_name | 情境名称 | string | 纯文字 | [AI]同前 | 标题栏用 |
| total_record_count | 总训练次数 | int | >=0 | [S]count(daily_task_status) | 标题栏"共N次训练" |
| stats_good | 顺利次数 | int | >=0 | [S]count(rating=good) | 绿色数字 |
| stats_neutral | 一般次数 | int | >=0 | [S]count(rating=neutral) | 橙色数字 |
| stats_bad | 有点难次数 | int | >=0 | [S]count(rating=bad) | 红色数字 |
| month_group | 月份分组 | string | "YYYY年M月" | [S]按日期分组 | 分组标题 |
| record_list | 记录列表 | array | 当月所有记录 | [S]按月筛选 | 按日期降序 |
| record_list[N].day_num | 天数 | string | "第N天" | [S]从current_day | 记录头部 |
| record_list[N].date | 日期时间 | string | "今天 HH:mm"/"昨天 HH:mm"/"MM-DD HH:mm" | [S]日期格式化 | 记录头部 |
| record_list[N].effect_badge | 效果徽章 | enum | good/neutral/bad | [S]同rating | 样式+emoji不同 |
| record_list[N].effect_label | 效果标签 | string | "顺利"/"一般"/"有点难" | [S]映射 | 显示用 |
| record_list[N].body_text | 记录正文 | string | 备注文字 | [U]feedback_notes | 可为空 |
| record_list[N].train_count_tag | 次数标签 | string | "练了N次" | [S]格式化 | footer标签 |
| record_list[N].has_note | 是否有备注 | bool | true/false | [S]feedback_notes非空 | footer标签显示 |

---

### 3.8 其他页面

| 页面 | 功能概述 | 状态 |
|------|----------|------|
| me.html | 个人中心，展示孩子档案入口和应用信息 | 已有初步版本 |
| child-profile.html | 管理孩子基本信息 | 已有初步版本 |
| settings.html | 应用全局设置入口 | 已有初步版本 |
| reminder.html | 设置每日训练提醒时间 | 已有初步版本 |
| about.html | 应用介绍和价值观声明 | 已有初步版本 |
| practice.html | 孩子练习页（v3.0占位模块） | 占位模块，暂不开发 |

---

## 4. 字段定义

### 4.1 字段来源标记说明

| 标记 | 含义 | 说明 |
|------|------|------|
| [U] | User Input | 用户输入数据 |
| [AI] | AI Generated | AI模型生成 |
| [S] | System | 系统计算/生成 |
| [K] | Constant | 固定常量 |
| [DB] | Database | 数据库存储 |

### 4.2 场景相关字段（scenarios表）

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| id | 情境ID | UUID | RFC4122 | [S]系统生成 | 主键 |
| package_code | 方案代码 | string | 唯一标识 | [S]系统生成 | 用于关联tasks表 |
| package_name | 方案名称 | string | "YYYYMMDDHHmmss_情境摘要" | [S]生成 | 内部用 |
| raw_input | 原始输入 | string | 用户输入文本 | [U]input.raw_input_text | AI分析用 |
| goal | 核心目标 | JSON | {title, content} | [AI]生成 | 从14天方案提取首日目标 |
| status | 状态 | enum | active/completed/abandoned/deleted | [S]状态机流转 | 默认active |
| current_day | 当前天数 | int | 1-14 | [S]每日+1 | 达到14则completed |
| confidence | AI置信度 | float | 0.0-1.0 | [AI]生成 | 方案可信度参考 |
| behavior_tags | 行为标签 | JSON array | ["社交", "语言", ...] | [AI]从selected_tags推断 | 分类用 |
| signal_type | 信号类型 | string | 如"感觉敏感" | [AI]推断 | 问题分类 |
| signal_detail | 信号详情 | string | 具体表现描述 | [AI]分析 | 问题细化 |
| days_data | 14天方案数据 | JSON | 见下方结构 | [AI]生成 | 完整训练方案 |
| clarification_needed | 是否需要澄清 | bool | true/false | [AI]判断 | 输入模糊时true |
| created_at | 创建时间 | datetime | ISO8601 | [S]系统时间 | |
| updated_at | 更新时间 | datetime | ISO8601 | [S]系统时间 | |
| completed_at | 完成时间 | datetime | ISO8601 | [S]状态变更时 | status=completed时 |

### 4.3 days_data JSON结构

```json
{
  "days": [
    {
      "day": 1,
      "goal": "今日目标描述",
      "tip": "今日小贴士",
      "steps": [
        {
          "index": 1,
          "action": "步骤动作",
          "desc": "步骤描述",
          "estimated_duration_seconds": 60
        }
      ]
    }
  ]
}
```

### 4.4 任务相关字段（tasks表）

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| task_id | 任务ID | UUID | RFC4122 | [S]系统生成 | 主键 |
| scenario_id | 情境ID | UUID | FK to scenarios | [S]关联 | 外键 |
| package_code | 方案代码 | string | 同scenarios | [S]复制 | 冗余索引用 |
| day | 天数 | int | 1-14 | [S]固定 | 属于哪天 |
| task_index | 任务序号 | int | 1-N | [S]当天步骤数 | 当天第几个步骤 |
| status | 状态 | enum | pending/completed/skipped | [S]流转 | 默认pending |
| completed_at | 完成时间 | datetime | ISO8602 | [S]用户完成时 | |

### 4.5 每日训练状态字段（daily_task_status表）

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| id | 记录ID | UUID | RFC4122 | [S]系统生成 | 主键 |
| scenario_id | 情境ID | UUID | FK to scenarios | [U]/[S]必填 | 外键 |
| date | 训练日期 | date | YYYY-MM-DD | [S]当天日期 | 分区键 |
| current_day | 当天天数 | int | 1-14 | [S]context | 显示用 |
| train_count | 训练次数 | enum | "1~2次"/"3~5次"/"5次+" | [U]feedback | 需存储为数值区间 |
| feedback_rating | 反馈评分 | enum | good/neutral/bad | [U]feedback | **v3.0新增** |
| feedback_note | 反馈备注 | string | 最长500字 | [U]feedback | 选填 |

### 4.6 孩子档案字段（children表）

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| id | 档案ID | UUID | RFC4122 | [S]系统生成 | 主键 |
| name | 姓名 | string | 最长20字 | [U]child-profile | 默认"小星" |
| age | 年龄 | int | 3-15 | [U]child-profile | 默认3 |
| gender | 性别 | enum | boy/girl | [U]child-profile | 默认boy |
| created_at | 创建时间 | datetime | ISO8601 | [S]系统 | |
| updated_at | 更新时间 | datetime | ISO8601 | [S]系统 | |

### 4.7 用户设置字段（user_settings表）

| 字段名 | 中文名 | 类型 | 格式/约束 | 来源 | 说明 |
|--------|--------|------|----------|------|------|
| user_id | 用户ID | UUID | FK | [S]认证系统 | 主键 |
| reminder_enabled | 提醒开关 | bool | true/false | [U]reminder | 默认true |
| reminder_time | 提醒时间 | time | HH:mm | [U]reminder | 默认"09:00" |
| quiet_mode | 安静模式 | bool | true/false | [U]settings | 默认false |

---

## 5. API契约

### 5.1 生成训练方案

**接口**：`POST /api/task-packages/generate`

**请求头**：
```
Content-Type: application/json
Authorization: Bearer ***
```

**请求体**：

| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| raw_input | string | 是 | 用户输入的情境描述文本，最长2000字 |
| selected_tags | string[] | 否 | 用户选择的快捷标签数组，如["穿衣抗拒","情绪崩溃"] |
| child_age | int | 否 | 孩子年龄，3-15岁，用于AI生成更精准的方案 |
| child_gender | string | 否 | 孩子性别，boy/girl |

**请求体示例**：
```json
{
  "raw_input": "今天早上送幼儿园的时候，孩子突然开始哭闹，怎么哄都不行...",
  "selected_tags": ["情绪崩溃", "穿衣抗拒"],
  "child_age": 11,
  "child_gender": "boy"
}
```

**响应体（成功，201）**：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| scenario_id | UUID | 生成的情境ID |
| package_code | string | 方案代码 |
| scenario_emoji | string | AI推断的情境emoji |
| scenario_title | string | AI提取的情境标题，格式"emoji+关键词" |
| core_goal | object | {title, content} |
| days_data | object | 完整14天方案结构 |
| confidence | float | AI置信度，0.0-1.0 |
| created_at | string | ISO8601时间戳 |

**响应体示例**：
```json
{
  "scenario_id": "550e8400-e29b-41d4-a716-446655440000",
  "package_code": "20260505101234_fuyi_kangju",
  "scenario_emoji": "👕",
  "scenario_title": "👕 穿衣抗拒",
  "core_goal": {
    "title": "配合伸手进袖子，无抗拒完成穿衣",
    "content": "通过渐进式感觉统合训练，逐步降低孩子对衣物触碰皮肤的敏感反应..."
  },
  "days_data": {
    "days": [
      {
        "day": 1,
        "goal": "接受毛巾触碰手臂",
        "tip": "在孩子心情好的时候练习，每次5-10分钟即可",
        "steps": [
          {"index": 1, "action": "用毛巾轻碰手背", "desc": "说'摸一摸'，立刻给零食强化", "estimated_duration_seconds": 60},
          {"index": 2, "action": "用毛巾包裹手臂1-2秒", "desc": "同时给零食，减少孩子警觉", "estimated_duration_seconds": 90},
          {"index": 3, "action": "用软棉布碰触手背/手心", "desc": "立刻给零食，巩固触觉接受", "estimated_duration_seconds": 90}
        ]
      }
    ]
  },
  "confidence": 0.87,
  "created_at": "2026-05-05T10:12:34Z"
}
```

**错误响应**：

| HTTP状态码 | error_code | 说明 |
|------------|------------|------|
| 400 | INVALID_INPUT | raw_input为空且无selected_tags |
| 400 | INPUT_TOO_LONG | raw_input超过2000字 |
| 422 | CLARIFICATION_NEEDED | AI判断需要澄清情境 |
| 500 | AI_GENERATION_FAILED | AI服务调用失败 |
| 504 | AI_TIMEOUT | DeepSeek调用超时（前端超时30s） |

**错误体格式**：
```json
{
  "error_code": "INVALID_INPUT",
  "message": "请输入情境描述或选择快捷标签",
  "details": {}
}
```

---

### 5.2 获取情境列表

**接口**：`GET /api/scenarios`

**查询参数**：

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | enum | 否 | 筛选状态：active/completed/abandoned |
| page | int | 否 | 页码，默认1 |
| page_size | int | 否 | 每页数量，默认20 |

**响应体（200）**：
```json
{
  "scenarios": [
    {
      "scenario_id": "uuid",
      "scenario_emoji": "👕",
      "scenario_title": "👕 穿衣抗拒",
      "status": "active",
      "current_day": 3,
      "total_days": 14,
      "progress_percent": 21,
      "updated_at": "2026-05-05T09:30:00Z"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 20
}
```

---

### 5.3 获取情境详情

**接口**：`GET /api/scenarios/{scenario_id}`

**响应体（200）**：
```json
{
  "scenario_id": "uuid",
  "package_code": "code",
  "scenario_emoji": "👕",
  "scenario_title": "👕 穿衣抗拒",
  "status": "active",
  "current_day": 3,
  "total_days": 14,
  "progress_percent": 21,
  "total_train_count": 6,
  "consecutive_days": 3,
  "core_goal": {
    "title": "配合伸手进袖子，无抗拒完成穿衣",
    "content": "通过渐进式感觉统合训练..."
  },
  "recent_records": [
    {
      "emoji": "😊",
      "date": "今天 · 第3天",
      "detail": "孩子主动伸手进袖子",
      "train_count": "练了2次"
    }
  ],
  "created_at": "2026-05-03T10:00:00Z",
  "updated_at": "2026-05-05T09:30:00Z"
}
```

---

### 5.4 获取当日训练

**接口**：`GET /api/scenarios/{scenario_id}/days/{day}`

**响应体（200）**：
```json
{
  "scenario_id": "uuid",
  "day": 3,
  "total_days": 14,
  "nav_title": "穿衣抗拒 · 第3天 / 共14天",
  "progress_percent": 33,
  "today_goal": "配合伸手进袖子，无抗拒完成穿衣",
  "tip_text": "在孩子心情好的时候练习，每次5-10分钟即可",
  "steps": [
    {
      "step_index": 1,
      "step_action": "用毛巾轻碰手背",
      "step_desc": "说'摸一摸'，立刻给零食强化",
      "estimated_duration_seconds": 60
    },
    {
      "step_index": 2,
      "step_action": "用毛巾包裹手臂1-2秒",
      "step_desc": "同时给零食，减少孩子警觉",
      "estimated_duration_seconds": 90
    },
    {
      "step_index": 3,
      "step_action": "用软棉布碰触手背/手心",
      "step_desc": "立刻给零食，巩固触觉接受",
      "estimated_duration_seconds": 90
    }
  ]
}
```

---

### 5.5 提交训练反馈

**接口**：`POST /api/scenarios/{scenario_id}/feedback`

**请求体**：

```json
{
  "day": 3,
  "feedback_rating": "good",
  "train_count": "3~5次",
  "feedback_notes": "孩子主动伸手进袖子了，虽然最后还是有点抗拒，但全程没有哭闹"
}
```

**响应体（201）**：

```json
{
  "record_id": "uuid",
  "scenario_id": "uuid",
  "day": 3,
  "feedback_rating": "good",
  "train_count": "3~5次",
  "feedback_notes": "孩子主动伸手进袖子了...",
  "created_at": "2026-05-05T09:45:00Z"
}
```

---

### 5.6 获取训练历史

**接口**：`GET /api/scenarios/{scenario_id}/history`

**响应体（200）**：

```json
{
  "scenario_id": "uuid",
  "scenario_emoji": "👕",
  "scenario_name": "穿衣抗拒",
  "total_record_count": 6,
  "stats": {
    "good": 4,
    "neutral": 1,
    "bad": 1
  },
  "records": [
    {
      "day_num": "第3天",
      "date": "今天 09:32",
      "effect_badge": "good",
      "effect_label": "顺利",
      "body_text": "孩子主动伸手进袖子了...",
      "train_count_tag": "练了2次",
      "has_note": true
    }
  ]
}
```

---

### 5.7 Mock模式（测试用）

**说明**：为解决DeepSeek调用慢导致测试超时问题，v3.0支持测试mock模式。

**启用方式**：环境变量 `MOCK_MODE=true` 或请求头 `X-Mock-Mode: true`

**Mock响应**：返回预存的模拟方案数据，不调用真实AI服务，响应延迟固定200ms。

---

## 6. 数据模型

### 6.1 ER图概述

```
scenarios (1) ──────< tasks (N)
    │                    │
    │                    │
    ▼                    ▼
daily_task_status    feedback
```

### 6.2 表结构

#### scenarios 表（核心实体）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID v4 |
| user_id | TEXT | | 用户ID |
| package_code | TEXT | NOT NULL | 方案代码 |
| package_name | TEXT | NOT NULL | 方案名称 |
| raw_input | TEXT | NOT NULL | 原始输入 |
| goal | TEXT | | JSON核心目标 |
| status | TEXT | NOT NULL DEFAULT 'active' | active/completed/abandoned/deleted |
| current_day | INTEGER | DEFAULT 1 | 1-14 |
| confidence | REAL | | AI置信度 |
| behavior_tags | TEXT | | JSON array |
| signal_type | TEXT | | 信号类型 |
| signal_detail | TEXT | | 信号详情 |
| clarification_needed | INTEGER | DEFAULT 0 | 是否需要澄清 |
| days_data | TEXT | | JSON完整方案 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | |
| completed_at | TIMESTAMP | | |

#### tasks 表（每日任务下的具体任务）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | "{package_code}_D{day}_T{task_index}" |
| scenario_id | TEXT | NOT NULL, FK | 外键 |
| package_code | TEXT | NOT NULL | 冗余索引 |
| day | INTEGER | NOT NULL | 1-14 |
| name | TEXT | NOT NULL | 任务名称 |
| steps | TEXT | | JSON array of step objects |
| duration_minutes | INTEGER | | 预计分钟数 |
| status | TEXT | NOT NULL DEFAULT 'pending' | pending/completed/skipped |
| has_feedback | INTEGER | DEFAULT 0 | 是否有反馈 |
| order_index | INTEGER | DEFAULT 0 | 排序 |

#### daily_task_status 表（每日训练状态）

| 字段名 | 类型 | 约束 | 说明 |
|--------|------|------|------|
| id | TEXT | PRIMARY KEY | UUID |
| scenario_id | TEXT | NOT NULL, FK | 外键 |
| day | INTEGER | NOT NULL | 1-14 |
| date | TEXT | NOT NULL | YYYY-MM-DD |
| status | TEXT | NOT NULL DEFAULT 'pending' | pending/in_progress/completed/skipped |
| train_count | TEXT | | "1~2次"/"3~5次"/"5次+" |
| feedback_rating | TEXT | | good/neutral/bad |
| feedback_note | TEXT | | 最长500字 |
| completed_at | TIMESTAMP | | |

---

## 7. 状态机

### 7.1 情境状态流转

```
[创建] → active（进行中）
           ↓
    ┌──────┼──────┐
    ↓      ↓      ↓
completed abandoned deleted
 (已完成) (已放弃) (已删除)
```

**流转规则**：

| 当前状态 | 事件 | 下一状态 | 触发条件 |
|----------|------|----------|----------|
| active | 完成第14天 | completed | current_day > 14 或 current_day == 14且feedback已提交 |
| active | 主动放弃 | abandoned | 用户点击"放弃"按钮 |
| active | 超期未练 | abandoned | 超过14天未提交反馈（可选实现） |
| abandoned | 重新激活 | active | 用户重新开始训练（current_day重置） |
| completed | 无 | - | 终态，不可逆 |
| deleted | 无 | - | 终态，仅用于软删除 |

### 7.2 每日任务状态

```
[当日开始] → pending
                ↓
    ┌───────────┼───────────┐
    ↓           ↓           ↓
completed   skipped    pending（未完成）
```

**流转规则**：

| 当前状态 | 事件 | 下一状态 |
|----------|------|----------|
| pending | 提交反馈 | completed |
| pending | 跳过当天 | skipped |
| pending | 超过当天24:00 | skipped（自动） |

---

## 8. v2.1→v3.0变更说明

### 8.1 API契约明确化

**问题**：v2.1时 `/api/task-packages/generate` 请求体字段不明确。

**v3.0解决方案**：
- 生成方案接口为 `POST /api/task-packages/generate`，是新建场景，**不需要**scenario_id
- 请求体明确使用 `raw_input`（用户输入文本）和 `selected_tags`（快捷标签数组）
- 不使用scenario_id或package_name作为请求字段
- 响应体返回新生成的 `scenario_id` 和 `package_code`

### 8.2 步骤预计时长字段补全

**问题**：原型和Schema缺少每步骤预计时长字段。

**v3.0解决方案**：
- 在 `daily_plan[N].steps[M]` 结构中新增 `estimated_duration_seconds` 字段
- 类型：int，单位秒，范围60-180（1-3分钟）
- AI生成方案时估算每步骤时长
- 前端可选择显示秒数或"约X分钟"

### 8.3 反馈评分字段补全

**问题**：feedback.html设计了效果选择，但数据库和API缺少feedback_rating字段。

**v3.0解决方案**：
- `daily_task_status` 表新增 `feedback_rating` 字段，enum(good/neutral/bad)
- API `POST /api/scenarios/{id}/feedback` 请求体新增 `feedback_rating` 必填字段
- 前端UI映射：😊顺利→good、😐一般→neutral、😣有点难→bad

### 8.4 时长描述一致性修正

**问题**：原型写"10-20分钟"，Schema标准是"5-12分钟"。

**v3.0解决方案**：
- 统一修正为**5-12分钟**
- package.html注意事项第2条：改为"每次训练时间控制在5-12分钟内"
- 训练页面提示文案：改为"每次5-12分钟即可"

### 8.5 DeepSeek超时解决方案

**问题**：第一轮测试发现DeepSeek调用慢，测试用例超时。

**v3.0解决方案**：
- 前端超时设置：30秒
- 后端增加重试机制：最多重试2次
- **新增Mock模式**：环境变量 `MOCK_MODE=true` 时返回预存模拟数据，响应延迟200ms

### 8.6 "NT孩子"表述移除

**问题**：v2.1文案中出现"NT孩子"表述，无循证出处。

**v3.0处理**：
- 所有文案中移除"NT孩子"表述
- 机制解读统一改为通用ASD机制描述
- AI生成方案时，机制说明标注"AI综合分析"来源

### 8.7 空状态引导补全

**问题**：index.html空状态未引导用户行动。

**v3.0处理**：
- 空状态区域显示CTA按钮"添加第一个情境"
- 点击后跳转input.html

### 8.8 disabled按钮对比度修正

**问题**：feedback.html disabled按钮对比度差。

**v3.0处理**：
- disabled样式：背景#E0E0E0，文字#ADADAD
- 正常样式：背景#7CB342，文字#FFFFFF
- 对比度明显差异，用户可识别

---

## 9. 已知风险与注意事项

### 9.1 产品风险

| # | 风险 | 影响等级 | 应对措施 |
|---|------|----------|----------|
| R-1 | AI生成内容质量不稳定 | 高 | PRD定义字段约束，测试覆盖 |
| R-2 | DeepSeek调用慢/超时 | 中 | Mock模式+超时降级+重试机制 |
| R-3 | ASD儿童干预安全性 | 高 | 产品原则"不影响孩子干预效果"是最高优先级 |

### 9.2 技术风险

| # | 风险 | 影响等级 | 应对措施 |
|---|------|----------|----------|
| T-1 | 前端30秒超时设置 | 中 | 实际可能需要更长，建议45-60秒 |
| T-2 | Mock模式数据覆盖不全 | 低 | 预存数据需完整覆盖核心场景 |
| T-3 | 数据库迁移脚本 | 中 | 需提前准备回滚方案 |

### 9.3 开放问题

| # | 问题 | 优先级 | 状态 |
|---|------|--------|------|
| O-1 | 孩子练习模块（practice.html）无实际功能 | P1 | 待设计 |
| O-2 | 新用户引导流程未定义 | P1 | 待PRD补充 |
| O-3 | 提醒功能具体逻辑未定义 | P2 | 待设计 |
| O-4 | AI模型调用超时处理方案 | P1 | 已定义Mock模式 |
| O-5 | 多孩子支持（一个家长多个ASD孩子） | P2 | 待设计 |

### 9.4 数据隐私声明

- 孩子信息（姓名、年龄、性别）仅用于提供更精准的干预建议
- 所有数据不会分享给任何人
- 语音输入数据仅用于本次AI分析，不做持久化存储

---

## 附录

### A. 快捷标签预设列表

| 标签名 | emoji | 说明 |
|--------|-------|------|
| 社交回避 | 👀 | 回避目光接触或社交互动 |
| 叫名字不应 | 👂 | 对名字呼唤无反应 |
| 情绪崩溃 | 😢 | 情绪爆发、哭闹 |
| 穿衣抗拒 | 👕 | 抗拒换衣服 |
| 眼神不对视 | 🙈 | 避免眼神接触 |
| 刻板行为 | 🔄 | 重复刻板动作 |

### B. 状态badge样式

| 状态 | badge背景色 | 文字色 | emoji |
|------|-------------|--------|-------|
| 进行中（active） | #E8F5E9 | #7CB342 | 🔥 |
| 已完成（completed） | #E3F2FD | #1976D2 | ✅ |
| 已放弃（abandoned） | #FFEBEE | #E57373 | ⏸️ |

### C. 反馈效果样式

| 效果 | emoji | feedback_rating | 徽章背景色 | 文字色 |
|------|-------|-----------------|------------|--------|
| 顺利 | 😊 | good | #E8F5E9 | #7CB342 |
| 一般 | 😐 | neutral | #FFF8E1 | #F5A623 |
| 有点难 | 😣 | bad | #FFEBEE | #E57373 |

### D. 色彩体系

| 用途 | 色值 | 说明 |
|------|------|------|
| 背景色 | #F7F4F0 | 页面背景 |
| 卡片色 | #FFFFFF | 卡片背景 |
| 强调色 | #7CB342 | 按钮、进度条、Tab选中 |
| 文字主色 | #2D2D2D | 标题、主要文字 |
| 文字次色 | #6B6B6B | 辅助说明文字 |
| 边框色 | #E8E4E0 | 分割线、边框 |
| 提示卡片 | #FFF8F0 | 暖黄色提示卡片背景 |
| 提示文字 | #8D6E63 | 提示卡片文字 |

---

**文档版本**：v3.0  
**最后更新**：2026-05-05  
**维护者**：产品团队