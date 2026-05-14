# oh-my-claudecode 使用指南

> 来源：oh-my-claudecode 官方文档
> 版本：4.13.7

---

## 什么是 oh-my-claudecode？

oh-my-claudecode (OMC) 是一个 Claude Code 的**多智能体编排系统**，它让你可以通过简单的自然语言指令，驱动多个 AI 智能体协同完成复杂任务。

### 核心价值

| 价值点 | 说明 |
|--------|------|
| **效率** | 自动并行化 + 智能路由，节省 30-50% token |
| **能力** | 整合 Codex/Gemini，突破单一模型局限 |
| **可靠** | 持久执行模式确保任务不半途而废 |
| **学习** | 从调试中提取可复用技能，避免重复踩坑 |

---

## 安装与配置

### 已完成安装

```
插件名称：oh-my-claudecode@omc
版本：4.13.7
作用域：user（全局可用）
状态：已启用
```

### 首次使用配置

如果你通过 `omc --plugin-dir <path>` 或 `claude --plugin-dir <path>` 运行：

```bash
omc setup
# 添加 --plugin-dir-mode 标志避免重复复制
```

### 启用 Team 模式（推荐）

在 `~/.claude/settings.json` 中添加：

```json
{
  "env": {
    "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"
  }
}
```

---

## 触发方式总览

### 1. 斜杠命令（主要方式）

在 Claude Code 对话中直接输入：

| 命令 | 功能 | 示例 |
|------|------|------|
| `/team` | Team 编排模式 | `/team 3:executor "fix all TypeScript errors"` |
| `/omc-teams` | tmux CLI 工作者 | `/omc-teams 2:codex "security review"` |
| `/ccg` | 三模型并行 | `/ccg Review this PR` |
| `/autopilot` | 全自动执行 | `/autopilot build a REST API` |
| `/ralph` | 持久模式 | `/ralph refactor auth module` |
| `/ulw` | 最大并行 | `/ulw fix all errors` |
| `/plan` | 规划访谈 | `/plan the API design` |
| `/deep-interview` | 苏格拉底式需求澄清 | `/deep-interview "I want to build an app"` |
| `/omc-setup` | 配置设置 | `/omc-setup` |
| `/omc-doctor` | 诊断检查 | `/omc-doctor` |
| `/skill` | 技能管理 | `/skill list` |

### 2. 自然语言触发（魔法关键词）

无需记忆命令，直接描述需求：

```
autopilot: build a task management app
ralph: refactor the authentication system
ulw fix all the lint errors
plan the database schema
deep-interview I have a vague idea about...
```

### 3. 前缀关键词

| 关键词 | 效果 | 示例 |
|--------|------|------|
| `team` | 标准 Team 编排 | `team 3:executor fix all errors` |
| `omc-teams` | tmux CLI 工作者 | `omc-teams 2:codex security review` |
| `ccg` | 三模型编排 | `ccg review this PR` |
| `autopilot` | 自主执行 | `autopilot: build a todo app` |
| `ralph` | 持久模式（包含 ultrawork） | `ralph: refactor auth` |
| `ulw` | 最大并行化 | `ulw fix all errors` |
| `plan` | 规划访谈 | `plan the API` |
| `ralplan` | 迭代规划共识 | `ralplan this feature` |
| `deep-interview` | 苏格拉底式需求澄清 | `deep-interview vague idea` |

### 4. 中文触发关键词（可选）

以下关键词可直接替代英文关键词使用：

| 中文关键词 | 对应原词 | 效果 | 示例 |
|-----------|---------|------|------|
| `团队` | team | 标准 Team 编排 | `团队 3:executor "修复所有错误"` |
| `并行` | omc-teams | tmux CLI 工作者 | `并行 2:codex "安全审查"` |
| `三剑客` | ccg | 三模型并行 | `三剑客 "review PR"` |
| `自动驾驶` | autopilot | 自主执行 | `自动驾驶: "构建任务管理应用"` |
| `持久模式` | ralph | 持久模式（包含 ultrawork） | `持久模式: "重构认证模块"` |
| `闪电` | ulw | 最大并行化 | `闪电 "修复所有错误"` |
| `规划` | plan | 规划访谈 | `规划 "API 设计"` |
| `共创` | ralplan | 迭代规划共识 | `共创 "这个功能"` |
| `深度访谈` | deep-interview | 苏格拉底式需求澄清 | `深度访谈 "我有个模糊的想法"` |

---

## 核心功能详解

### 1. Team 模式（推荐）

**用途**：在共享任务列表上协作的多个 Claude 智能体

**流水线**：
```
team-plan → team-prd → team-exec → team-verify → team-fix (循环)
```

**语法**：
```
/team N:agent_type "任务描述"
```

**示例**：
```bash
/team 3:executor "fix all TypeScript errors"
/team 2:researcher "investigate the performance issue"
```

**可用的 agent_type**：
- `executor` - 执行者，负责实际编码
- `reviewer` - 审查者，代码审查
- `architect` - 架构师，系统设计
- `researcher` - 研究者，调研分析
- `tester` - 测试者，测试编写

### 2. omc-teams（tmux CLI 工作者）

**用途**：在 tmux 分屏中启动真实的 CLI 进程

**语法**：
```
/omc-teams N:cli_type "任务描述"
```

**cli_type**：
| 类型 | 最适合 |
|------|--------|
| `codex` | 代码审查、安全分析、架构 |
| `gemini` | UI/UX 设计、文档、大上下文任务 |
| `claude` | 通用任务 |

**示例**：
```bash
/omc-teams 2:codex "review auth module for security issues"
/omc-teams 2:gemini "redesign UI components"
/omc-teams 1:claude "implement payment flow"
```

**注意**：需要安装对应的 CLI 工具：
- Codex: `npm install -g @openai/codex`
- Gemini: `npm install -g @google/gemini-cli`

### 3. ccg（三模型并行）

**用途**：同时使用 Codex（分析）+ Gemini（设计）+ Claude（综合）

**语法**：
```
/ccg 任务描述
```

**示例**：
```bash
/ccg Review this PR — architecture (Codex) and UI (Gemini)
/ccg Design a new feature
```

### 4. Autopilot（全自动执行）

**用途**：最小化繁琐配置的端到端功能开发

**语法**：
```
autopilot: 任务描述
# 或
/autopilot 任务描述
```

**示例**：
```bash
autopilot: build a REST API for managing tasks
/autopilot create a user authentication system
```

### 5. Ultrawork（ulw）

**用途**：不需要 Team 的并行修复/重构

**语法**：
```
/ulw 任务描述
# 或
ulw 任务描述
```

**示例**：
```bash
/ulw fix all TypeScript errors in the project
ulw refactor all React components
```

### 6. Ralph（持久模式）

**用途**：必须完整完成的任务，包含 ultrawork 的并行执行

**语法**：
```
/ralph 任务描述
# 或
ralph: 任务描述
```

**示例**：
```bash
/ralph refactor the entire auth module
ralph: migrate database to new schema
```

### 7. 规划工具

#### /plan（规划访谈）

**用途**：帮你理清需求和设计

**语法**：
```
/plan 主题
```

**示例**：
```bash
/plan the API design
/plan the database schema
```

#### /deep-interview（苏格拉底式需求澄清）

**用途**：在编写代码之前帮你理清模糊的想法

**语法**：
```
/deep-interview "模糊的想法描述"
```

**示例**：
```bash
/deep-interview "I want to build a task management app"
/deep-interview "We need to improve our CI/CD pipeline"
```

---

## 技能系统

### 什么是技能（Skills）？

从调试过程中提取的可复用模式，存储为 `.md` 文件，自动注入到相关场景。

### 技能存储位置

| 作用域 | 路径 | 优先级 |
|--------|------|--------|
| 项目 | `.omc/skills/` | 高 |
| 用户 | `~/.omc/skills/` | 低（回退） |

### 技能文件格式

```markdown
# .omc/skills/fix-proxy-crash.md
---
name: Fix Proxy Crash
description: aiohttp proxy crashes on ClientDisconnectedError
triggers: ["proxy", "aiohttp", "disconnected"]
source: extracted
---

在 server.py:42 的处理程序外包裹 try/except ClientDisconnectedError...
```

### 技能管理命令

```bash
/skill list          # 列出所有技能
/skill add <path>    # 添加技能
/skill remove <name> # 删除技能
/skill edit <name>   # 编辑技能
/skill search <term> # 搜索技能
/skillify           # 从当前会话提取技能
```

### 自动学习

使用 `/skillify` 从调试过程中提取可复用模式。

---

## 实用工具

### 1. 速率限制等待

当速率限制重置时自动恢复会话：

```bash
omc wait              # 检查状态，获取指导
omc wait --start      # 启用自动恢复守护进程
omc wait --stop       # 禁用守护进程
```

### 2. 通知配置

配置任务完成时的通知：

```bash
# Telegram
omc config-stop-callback telegram --enable --token <token> --chat <chat_id>

# Discord
omc config-stop-callback discord --enable --webhook <url>

# Slack
omc config-stop-callback slack --enable --webhook <url>
```

### 3. OpenClaw 集成

将 Claude Code 会话事件转发到 OpenClaw 网关：

```bash
/oh-my-claudecode:configure-notifications
# 然后选择 "openclaw"
```

---

## 快速参考表

### 场景 → 命令对照

| 场景 | 推荐命令 |
|------|----------|
| 需要多个智能体协作 | `/team N:executor` |
| 同时用 Codex + Gemini | `/ccg` |
| 全自动开发新功能 | `autopilot:` |
| 快速并行修复多个问题 | `/ulw` |
| 必须完整完成的大任务 | `/ralph` |
| 厘清模糊的需求 | `/deep-interview` |
| 系统设计和规划 | `/plan` |
| tmux 多窗口协作 | `/omc-teams` |
| 管理复用技能 | `/skill list/add/remove` |

### 魔法关键词速查

```
┌─────────────────────────────────────────────────────────────┐
│ team N:agent    │ Team 编排        │ team 3:executor       │
│ omc-teams N:cli │ tmux CLI 工作者  │ omc-teams 2:codex    │
│ ccg             │ 三模型并行        │ ccg review PR        │
│ autopilot:      │ 全自动执行       │ autopilot: build API  │
│ ralph:          │ 持久模式         │ ralph: refactor auth  │
│ ulw             │ 最大并行         │ ulw fix errors       │
│ plan            │ 规划访谈         │ plan the schema      │
│ deep-interview  │ 需求澄清         │ deep-interview idea  │
└─────────────────────────────────────────────────────────────┘
```

### 中文关键词速查

```
┌─────────────────────────────────────────────────────────────┐
│ 团队 N:agent   │ Team 编排        │ 团队 3:executor       │
│ 并行 N:cli     │ tmux CLI 工作者  │ 并行 2:codex        │
│ 三剑客          │ 三模型并行        │ 三剑客 review PR     │
│ 自动驾驶:       │ 全自动执行       │ 自动驾驶: build API  │
│ 持久模式:       │ 持久模式         │ 持久模式: 重构 auth  │
│ 闪电            │ 最大并行         │ 闪电 fix errors      │
│ 规划            │ 规划访谈         │ 规划 the schema      │
│ 共创            │ 迭代规划共识     │ 共创 this feature    │
│ 深度访谈        │ 需求澄清         │ 深度访谈 vague idea  │
└─────────────────────────────────────────────────────────────┘
```

---

## 常见问题

### Q: Team 模式和 omc-teams 有什么区别？

**Team 模式**：Claude Code 原生的多智能体协作，通过 `team-plan → team-prd → team-exec → team-verify` 流水线运行。

**omc-teams**：在 tmux 分屏中启动真实的 CLI 进程（Codex/Gemini/Claude），按需生成，任务完成后自动退出。

### Q: 需要安装额外的 CLI 工具吗？

**可选但推荐**：
- Codex: `npm install -g @openai/codex`
- Gemini: `npm install -g @google/gemini-cli`

没有它们，Team 模式和 Autopilot 仍然可用。

### Q: 如何更新插件？

```bash
# 更新 marketplace 克隆
/plugin marketplace update omc

# 重新运行设置
/omc-setup
```

### Q: 遇到问题怎么办？

```bash
/omc-doctor
```

---

## 为你的项目使用 OMC

### 星娃项目适用场景

| 场景 | OMC 命令 |
|------|----------|
| 批量代码审查 | `/team 2:reviewer "review all API endpoints"` |
| 前后端并行开发 | `/ccg implement the training flow"` |
| 重构多个模块 | `/ulw refactor store modules"` |
| 全栈功能开发 | `autopilot: add user profile feature` |
| 技术调研 | `/team 1:researcher "investigate RAG optimization"` |

---

## 更多信息

- 完整文档：https://github.com/Yeachan-Heo/oh-my-claudecode
- CLI 参考：`omc --help`
- Discord 社区：见项目首页
