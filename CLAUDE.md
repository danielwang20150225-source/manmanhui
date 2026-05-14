# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

---
##产品设计规范##
请严格按照设计规范上的定义构建demo，设计规划地址：D:\星娃项目\micro-intervention\docs\微干预V2.0原型设计规范.md



## 产品定位

**微干预（原名"慢慢会"）** — ASD儿童（自闭症谱系）家庭干预AI助手

核心价值：**让每一个情境问题，都能转化成为一次有效干预**

服务对象：整个自闭症家庭——孩子是最终受益者，家长端是执行手段。

---

## 产品原则（Daniel底线，不可违背）

1. **ASD儿童干预安全**：做ASD儿童干预产品，绝对不能负面影响孩子的干预效果。这是最高优先级，高于产品优化和商业目标。
2. **专业有效**：不追求"有趣"或"低门槛"，追求专业、有效、不制造焦虑。
3. **家长端设计**：简单低门槛、正反馈机制

---

## 项目结构

```
星娃项目/
├── micro-intervention/          # 前端（活跃开发）
│   ├── index.html               # 首页
│   ├── input.html               # 情境输入
│   ├── package.html             # 任务包确认
│   ├── task-detail.html         # 情境详情
│   ├── training.html            # 每日训练
│   ├── feedback.html            # 训练反馈
│   ├── history.html             # 训练历史
│   ├── config.js                # API配置（API_BASE = ''）
│   ├── js/router.js            # 路由
│   ├── js/store/scenarioStore.js
│   ├── js/store/trainingStore.js
│   └── docs/
│       ├── PRD-v5.0-微干预.md   # 最新PRD（v5.0）
│       └── Demo版原型设计.md    # Demo版设计
│
├── manmanhui/                   # 后端（FastAPI）
│   ├── app.py                   # 入口，端口8000
│   ├── database.py              # 数据模型
│   ├── db/manmanhui.db         # SQLite数据库
│   ├── config/config.example.env
│   ├── data/
│   │   ├── processed/knowledge_chunks.json  # 280条知识片段
│   │   └── knowledge-base/
│   │       └── 05_情境任务包/  # 66个任务包MD文件
│   ├── prompts/                 # AI提示词（A/B/C）
│   └── docs/
│
└── _archive/                    # 归档（279个废弃文件，勿动）
```

---

## 启动方式

```bash
# 后端（当前工作目录）
cd D:\星娃项目\manmanhui
python app.py
# 访问 http://localhost:8000/

# API健康检查
curl http://localhost:8000/api/health
```

前端由后端直接serve，无需单独启动http-server。

---

## 核心技术决策

| 决策 | 状态 | 说明 |
|------|------|------|
| ChromaDB RAG | ❌ 不启用 | 当前直接调用DeepSeek，不走向量检索 |
| Mock模式 | ✅ 支持 | `MOCK_MODE=true` 启用，返回预设数据 |
| 数据持久化 | anonymous UUID + localStorage | Demo版数据存储方案 |

---

## 关键文档

| 文档 | 路径 |
|------|------|
| PRD v5.0 | `micro-intervention/docs/PRD-v5.0-微干预.md` |
| Demo版原型设计 | `micro-intervention/docs/Demo版原型设计.md` |
| 任务包体系设计 | `manmanhui/data/knowledge-base/05_情境任务包/任务包体系设计.md` |
| 内容生产体系 | `manmanhui/data/knowledge-base/05_情境任务包/内容生产体系_v1.md` |
| 审核标准 | `manmanhui/data/knowledge-base/05_情境任务包/审核子agent标准与工作流.md` |

---

## 任务包体系（66个）

| 分类 | 数量 | 说明 |
|------|------|------|
| 01-50 | 50个 | 标准任务包 |
| S-01~S-10 | 10个 | 升级版任务包 |
| AAC-01~AAC-02 | 2个 | AAC辅助沟通 |
| L-01~L-03 | 3个 | 简化版任务包 |
| SP-01 | 1个 | 专项任务包 |

**优先级**：
- P1（最高频）：01呼名、02穿衣、06吃饭、08情绪
- P2：03如厕、04刷牙、07感官、09社交
- P3：05外出、10问题行为、22洗手
- P4：其余53个

---

## 飞书数据

- Base ID: GlT3b6ZyNaVFyksHi45czz4pnyf
- 66条任务包记录已导入

---

## API端点（17个）

| 路径 | 方法 | 说明 |
|------|------|------|
| `/api/health` | GET | 健康检查 |
| `/api/scenarios` | GET | 情境列表 |
| `/api/scenarios/{id}` | GET | 情境详情 |
| `/api/scenarios/{id}/history` | GET | 训练历史 |
| `/api/scenarios/{id}/days/{day}` | GET | 当日训练内容 |
| `/api/scenarios/{id}/feedback` | POST | 提交训练反馈 |
| `/api/scenarios/recognize` | POST | 识别用户输入 |
| `/api/task-packages/generate` | POST | 生成训练方案 |

---

## 意图匹配流程

1. 用户输入 → **Prompt C** 判断意图类型
2. `situation_input` → **Prompt A** 匹配任务包（66选1）
3. `feedback_submit` → **Prompt B** / 表情判断树 分析反馈
4. 降级：`fallback_recognize()` 纯关键词规则

---

## 已知经验教训

**Markdown解析**：
- 解析表格时绝不能用 `\s+` 压缩换行
- Regex优先用非贪婪+前瞻断言

**CORS**：
- `allow_origins=["*"]` 和 `allow_credentials=True` 不能同时配置

---

## 禁止事项

1. ❌ 不要修改 `_archive/` 目录
2. ❌ 不要修改 `竞品分析/` 目录
3. ❌ 不要在产品中加入任何可能负面影响ASD儿童干预效果的功能
4. ❌ 不要硬编码WSL IP地址
