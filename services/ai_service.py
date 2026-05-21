"""
AI 服务层
封装 DeepSeek API 调用、Mock 降级、反馈分析等 AI 相关逻辑
"""
import os
import re
import json
import asyncio
from typing import Dict, List, Any, Optional

# DeepSeek API 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", ""))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


# ============================================================
# DeepSeek API 调用（带三层降级）
# ============================================================

def call_deepseek_with_fallback(system_prompt: str, user_message: str, temperature: float = 0.3) -> Dict[str, Any]:
    """
    DeepSeek API调用（60s超时 + 重试2次 + NVIDIA NIM备用 + Mock降级）
    三层降级机制：DeepSeek API → 重试2次 → NVIDIA NIM → Mock数据
    """
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry

    # MOCK_MODE 降级
    if os.getenv("MOCK_MODE", "").lower() == "true":
        return mock_deepseek_response(user_message)

    # 第1层：DeepSeek API（60s超时 + 重试2次）
    session = requests.Session()
    retry_strategy = Retry(
        total=2,
        backoff_factor=1,  # 重试间隔：1s, 2s
        status_forcelist=[500, 502, 503, 504, 408, 429]
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ],
        "temperature": temperature,
        "max_tokens": 2000
    }

    # 尝试DeepSeek API（60秒超时）
    for attempt in range(3):  # 3次尝试（1次原始 + 2次重试）
        try:
            response = session.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # 提取JSON
                for pattern in [r'\[[\s\S]+\]', r'\{[\s\S]*\}']:
                    try:
                        json_match = re.search(pattern, content)
                        if json_match:
                            return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        continue
                return {"content": content}
            elif response.status_code in [500, 502, 503, 504]:
                continue  # 重试
            else:
                break  # 其他错误，跳到备用
        except requests.exceptions.Timeout:
            continue  # 超时，重试
        except requests.exceptions.RequestException:
            break  # 网络错误，跳到备用

    # 第2层：NVIDIA NIM 备用
    nvim_api_key = os.getenv("BACKUP_MODEL_API_KEY", "")
    nvim_base_url = os.getenv("BACKUP_MODEL_BASE_URL", "https://integrate.api.nvidia.com/v1")

    if nvim_api_key and nvim_api_key != "nvapi-...B9bn":
        nvim_headers = {
            "Authorization": f"Bearer {nvim_api_key}",
            "Content-Type": "application/json"
        }
        nvim_payload = {
            "model": "deepseek-ai/deepseek-v3",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            "temperature": temperature,
            "max_tokens": 2000
        }
        try:
            response = session.post(
                f"{nvim_base_url}/chat/completions",
                headers=nvim_headers,
                json=nvim_payload,
                timeout=60
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                for pattern in [r'\[[\s\S]+\]', r'\{[\s\S]*\}']:
                    try:
                        json_match = re.search(pattern, content)
                        if json_match:
                            return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        continue
                return {"content": content}
        except Exception:
            pass  # 备用也失败，降级到Mock

    # 最终降级：Mock数据
    return mock_deepseek_response(user_message)


def mock_deepseek_response(user_message: str) -> Dict[str, Any]:
    """Mock降级响应（用于测试或API不可用时）"""
    return {
        "mock": True,
        "message": "MOCK_MODE active - this is a mock response",
        "input_received": user_message[:100] if user_message else ""
    }


def call_deepseek_sync(system_prompt: str, user_message: str, temperature: float = 0.3) -> Dict[str, Any]:
    """同步调用 DeepSeek API（使用三层降级）"""
    return call_deepseek_with_fallback(system_prompt, user_message, temperature)


async def call_deepseek(system_prompt: str, user_message: str, temperature: float = 0.3) -> Dict[str, Any]:
    """异步调用 DeepSeek API"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, call_deepseek_sync, system_prompt, user_message, temperature)


# ============================================================
# 反馈分析引擎
# ============================================================

# 表情 → 信号映射
def map_emoji_to_signal(emoji: str) -> str:
    """将 emoji 表情映射为分析信号"""
    emoji_signal_map = {
        "👍": "positive",
        "😊": "positive",
        "good": "positive",
        "satisfied": "positive",
        "very_satisfied": "positive",
        "😐": "neutral",
        "neutral": "neutral",
        "dissatisfied": "neutral",
        "👎": "negative",
        "😣": "negative",
        "bad": "negative",
        "very_dissatisfied": "negative",
    }
    return emoji_signal_map.get(emoji, "neutral")


# 表情判断树
EXPRESSION_TREE = {
    # (当前信号, 历史信号) → (分析信号, 动作)
    ("positive", "positive"): ("stable", "maintain"),     # 👍 → 👍 → maintain
    ("positive", "neutral"): ("stable", "maintain"),     # 👍 → 😐 → maintain
    ("positive", "negative"): ("stable", "maintain"),    # 👍 → 👎 → maintain (正向优先)
    ("neutral", "positive"): ("stable", "maintain"),      # 😐 → 👍 → maintain
    ("neutral", "neutral"): ("stable", "maintain"),      # 😐 → 😐 → maintain
    ("neutral", "negative"): ("concerning", "escalate"),   # 😐 → 👎 → escalate
    ("negative", "positive"): ("stable", "maintain"),     # 👎 → 👍 → maintain
    ("negative", "neutral"): ("concerning", "escalate"), # 👎 → 😐 → escalate
    ("negative", "negative"): ("concerning", "escalate"), # 👎 → 👎 → escalate
}


def map_signal_to_action(signal: str) -> str:
    """Signal → 后台动作映射"""
    action_map = {
        "escalate": "escalate",
        "maintain": "maintain",
        "de-escalate": "de-escalate",
        "regenerate": "regenerate",
        "positive": "de-escalate",
        "stable": "maintain",
        "concerning": "escalate",
        "negative": "escalate",
        "recovery": "regenerate"
    }
    return action_map.get(signal, "maintain")


def rule_based_analyze(current_emoji: str, history_emoji: Optional[str] = None) -> Dict[str, Any]:
    """
    表情判断树规则引擎（无文字备注时）
    根据连续状态组合返回signal和后台动作
    """
    current_signal = map_emoji_to_signal(current_emoji)
    history_signal = map_emoji_to_signal(history_emoji) if history_emoji else None

    # 先尝试用完整key查树
    if history_signal:
        key = (current_signal, history_signal)
        signal, action = EXPRESSION_TREE.get(key, ("stable", "maintain"))
    else:
        # 没有历史记录，优先用树的单项规则
        key = (current_signal, None)
        if key in EXPRESSION_TREE:
            signal, action = EXPRESSION_TREE[key]
        elif current_signal == "positive":
            signal, action = "stable", "de-escalate"  # 首次😊→降级
        elif current_signal == "negative":
            signal, action = "concerning", "escalate"  # 首次😣→升级
        else:
            signal, action = "stable", "maintain"      # 首次😐→维持

    return {
        "signal": signal,
        "action": action,
        "analysis": f"表情判断树分析：当前={current_emoji}，历史={history_emoji or '无'}",
        "mode": "rule"
    }


async def ai_full_analyze(
    current_emoji: str,
    feedback_text: str,
    current_day: int,
    scenario_id: str,
    history_records: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    AI完整分析（有文字备注时调用DeepSeek API）
    返回analysis/signal/target_step/recommendation
    """
    # 构建分析上下文
    context = {
        "current_emoji": current_emoji,
        "feedback_text": feedback_text,
        "current_day": current_day,
        "scenario_id": scenario_id,
        "history": [
            {
                "day": r.get("day"),
                "emoji": r.get("emoji"),
                "text": r.get("text"),
                "analysis": json.loads(r.get("analysis_result", "{}")) if r.get("analysis_result") else {}
            }
            for r in history_records[:2]  # 最近2条
        ]
    }

    # 构造分析提示词
    analysis_prompt = f"""你是一个ASD儿童干预专家，请分析以下训练反馈：

当前反馈：
- 表情：{current_emoji}
- 家长备注：{feedback_text}
- 训练天数：第{current_day}天

历史记录：
{json.dumps(context['history'], ensure_ascii=False, indent=2)}

请返回JSON格式的分析结果：
{{
    "analysis": "一句话分析结论",
    "signal": "escalate/maintain/de-escalate/regenerate",
    "target_step": null或数字（当signal是de-escalate时指定退回哪一步）,
    "recommendation": null或字符串（当signal是regenerate时的建议）,
    "confidence": 0.0-1.0（分析置信度）
}}

判断规则：
1. emoji和文字矛盾时，以文字为主
2. 正面词（进步、主动、成功、配合）→ escalate优先
3. 负面词（哭、怕、抗拒、不肯、崩溃）→ de-escalate
4. 中性描述（一般、还行、正常）→ maintain
5. 建议类（可以…、也许…）→ 提取建议转recommendation
6. 当前步骤是最难步骤时，escalate→maintain
7. 当前步骤是最简单步骤时，de-escalate→maintain
"""

    try:
        result = await call_deepseek(analysis_prompt, json.dumps(context, ensure_ascii=False), temperature=0.3)
        if isinstance(result, dict):
            return {
                "signal": result.get("signal", "stable"),
                "action": map_signal_to_action(result.get("signal", "stable")),
                "analysis": result.get("analysis", "AI分析完成"),
                "target_step": result.get("target_step"),
                "recommendation": result.get("recommendation"),
                "confidence": result.get("confidence", 0.8),
                "mode": "ai"
            }
    except Exception:
        pass

    # AI分析失败，降级到表情判断树
    return rule_based_analyze(current_emoji, history_records[0].get("emoji") if history_records else None)


def apply_signal_action(
    signal: str,
    action: str,
    current_day: int,
    max_day: int = 14,
    min_day: int = 1
) -> Dict[str, Any]:
    """
    Signal后台动作执行 + 边界规则处理
    已是最难步骤时escalate→maintain，已是最简单步骤时de-escalate→maintain
    """
    # 边界规则处理
    if action == "escalate" and current_day >= max_day:
        action = "maintain"
        reason = "已是最难步骤，无法继续升级"
    elif action == "de-escalate" and current_day <= min_day:
        action = "maintain"
        reason = "已是最简单步骤，无法继续降级"
    else:
        reason = None

    # 执行动作
    next_day = current_day
    if action == "escalate":
        next_day = min(current_day + 1, max_day)
        message = f"明天进入第{next_day}天训练（升级）"
    elif action == "de-escalate":
        next_day = max(current_day - 1, min_day)
        message = f"明天退回第{next_day}天（更简单的步骤）"
    elif action == "regenerate":
        message = "已记录，明天继续当前训练"
    else:  # maintain
        message = f"明天继续第{current_day}天训练"

    return {
        "signal": signal,
        "action": action,
        "next_day": next_day,
        "message": message,
        "reason": reason
    }


# ============================================================
# 关键词兜底识别
# ============================================================

def fallback_recognize(text: str) -> Dict[str, Any]:
    """DeepSeek 不可用时的降级识别（关键词匹配）"""
    # 新编号（01~50）关键词映射
    KEYWORD_MAP = {
        "01": ["叫名字", "呼名", "不应", "不理", "不应名", "不回头", "不应声", "不听话", "不听指令", "不听线", "叫名字不应"],
        "02": ["穿衣", "穿衣服", "抗拒穿", "不肯穿"],
        "03": ["如厕", "上厕所", "大小便", "坐马桶", "尿裤子", "排便"],
        "04": ["刷牙", "口腔护理", "抗拒刷牙", "不肯刷牙", "洗牙"],
        "05": ["外出", "出门", "崩溃", "跑开", "公共场所", "乱跑", "外出哭闹"],
        "06": ["吃饭", "坐不住", "用餐", "吃飯", "挑食", "喂食", "拒绝食物"],
        "07": ["触觉", "降敏", "感官", "理发", "洗脸", "洗手", "抗拒触摸"],
        "08": ["情绪", "崩溃", "自我伤害", "发脾气", "撞头", "自伤", "打人", "攻击行为", "动手打人", "打人行为", "打人动作", "打人事件"],
        "09": ["社交", "发起", "找朋友", "不知道怎么玩", "不愿意跟人沟通", "不愿意沟通", "回避", "紧张", "不说话", "不沟通", "聊天就躲", "问问题就躲", "沟通紧张", "跟人说话", "找人玩", "回避行为"],
        "10": ["高频", "问题行为", "各种问题", "转圈", "自言自语", "刻板行为"],
        "11": ["PECS", "图片交换", "无语言", "图片沟通"],
        "12": ["功能性沟通", "FCT", "表达需求", "哭闹表达"],
        "13": ["行为功能", "FBA", "问题行为分析"],
        "14": ["感知觉", "感觉统合", "感官调节", "听觉敏感", "视觉敏感"],
        "15": ["挑食", "喂养", "拒食", "食物选择", "进食困难"],
        "16": ["共同注意", "跟随目光", "目光转移", "眼神", "不看人"],
        "17": ["社会故事", "情境适应"],
        "18": ["认知行为", "情绪调节", "CBT"],
        "19": ["语言理解", "听不懂", "指令理解"],
        "20": ["表达性语言", "发音", "词汇少", "语言表达"],
        "21": ["睡眠", "入睡", "夜醒", "早起", "不肯睡", "拒绝上床"],
        "22": ["洗手", "个人卫生", "不肯洗手"],
        "23": ["游戏", "玩法", "不会玩", "游戏技能"],
        "24": ["入学", "分离焦虑", "上学哭", "幼升小"],
        "25": ["自我管理", "自我监督", "自我奖励"],
        "26": ["模仿", "不会模仿"],
        "27": ["注意力", "分心", "注意力短", "易分散"],
        "28": ["轮流", "等待", "插话", "不肯等"],
        "29": ["分享", "馈赠", "不肯分享"],
        "30": ["集体活动", "集体中", "不配合"],
        "31": ["就医", "医院", "体检", "抗拒检查", "牙科"],
        "32": ["生日", "聚会", "派对"],
        "33": ["交通", "交通规则", "横冲直撞"],
        "34": ["客人", "来客人", "客人接待"],
        "35": ["兄弟姐妹", "兄弟", "姐妹", "冲突"],
        "36": ["阅读", "前阅读", "识字"],
        "37": ["书写", "写字", "握笔"],
        "38": ["数学", "数感"],
        "39": ["执行功能", "计划性", "任务切换"],
        "40": ["时间管理", "磨蹭", "拖延", "时间概念"],
        "41": ["社区", "小区", "广场"],
        "42": ["公园", "游乐场", "滑梯", "秋千"],
        "43": ["餐厅", "外出就餐", "餐馆"],
        "44": ["超市", "购物", "乱拿东西"],
        "45": ["公交", "地铁", "公共交通", "坐车"],
        "46": ["友谊", "交朋友", "同伴关系"],
        "47": ["校园规则", "学校规则", "违反纪律"],
        "48": ["课堂常规", "课堂", "离开座位", "打断老师"],
        "49": ["课间", "课间过渡"],
        "50": ["暑假", "暑期", "假期结构化"],
    }
    for code, kws in KEYWORD_MAP.items():
        if any(kw in text for kw in kws):
            return {
                "match": {
                    "package_code": code,
                    "package_name": f"任务包_{code}",
                    "confidence": 0.9,
                },
                "signal": {"type": "none", "detail": ""},
                "behavior_tags": [],
                "clarification_needed": []
            }
    # 无匹配 → 返回需要追问
    return {
        "match": None,
        "signal": {"type": "multi_problem", "detail": "无法确定具体情境，请补充描述孩子的主要问题"},
        "behavior_tags": [],
        "clarification_needed": ["孩子目前最让您困扰的问题是什么？"]
    }