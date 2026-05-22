"""
慢慢会 - 数据库层
完全对齐 PRD v2.1 数据模型
"""

import os
import json
import sqlite3
import uuid
import re
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from contextlib import contextmanager
from datetime import datetime, date
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Project paths
PROJECT_ROOT = Path(__file__).parent
DB_PATH = PROJECT_ROOT / "db" / "manmanhui.db"

# Ensure db directory exists
DB_PATH.parent.mkdir(parents=True, exist_ok=True)


# ============================================================
# Connection
# ============================================================

def get_db_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db_cursor():
    """Context manager for database operations"""
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ============================================================
# Schema 初始化
# ============================================================

def init_database():
    """Initialize all database tables aligned with PRD v2.1"""
    with get_db_cursor() as cursor:
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='scenarios'")
        table_exists = cursor.fetchone() is not None

        # 如果表已存在，直接返回（不删除数据）
        if table_exists:
            return

        # 新建所有表（PRD v2.1 对齐）
        # ---- scenarios 表（核心实体）----
        cursor.execute("""
            CREATE TABLE scenarios (
                id TEXT PRIMARY KEY,           -- UUID v4
                user_id TEXT,
                package_code TEXT NOT NULL,
                package_name TEXT NOT NULL,
                raw_input TEXT NOT NULL,
                goal TEXT,
                status TEXT NOT NULL DEFAULT 'active',  -- active|completed|abandoned|deleted
                current_day INTEGER DEFAULT 1,
                confidence REAL,
                behavior_tags TEXT,             -- JSON array
                signal_type TEXT,
                signal_detail TEXT,
                clarification_needed INTEGER DEFAULT 0,
                days_data TEXT,                -- JSON: full 7-day task package
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        """)

        # ---- tasks 表（每日任务下的具体任务）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,           -- "{package_code}_D{day}_T{task_index}"
                scenario_id TEXT NOT NULL,
                package_code TEXT NOT NULL,
                day INTEGER NOT NULL,
                name TEXT NOT NULL,
                steps TEXT,                    -- JSON array of step objects
                duration_minutes INTEGER,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending|completed|skipped
                has_feedback INTEGER DEFAULT 0,
                order_index INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id)
            )
        """)

        # ---- encouragement_texts 表（每日任务状态）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS encouragement_texts (
                id TEXT PRIMARY KEY,           -- UUID
                scenario_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                emoji TEXT NOT NULL,           -- very_dissatisfied|dissatisfied|neutral|satisfied|very_satisfied
                text TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                UNIQUE(scenario_id, day, emoji)
            )
        """)

        # ---- feedback 表（重构，对齐 PRD v2.1）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id TEXT PRIMARY KEY,           -- UUID v4
                scenario_id TEXT NOT NULL,
                task_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                emoji TEXT,
                text TEXT,
                training_record TEXT,           -- JSON: {opportunities, independent_success, p0_success_rate, max_prompt_level, emotion_behavior, session_duration_minutes}
                analysis_result TEXT,           -- JSON from Prompt B
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            )
        """)

        # ---- daily_task_status 表（每日任务状态）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS daily_task_status (
                id TEXT PRIMARY KEY,
                scenario_id TEXT NOT NULL,
                day INTEGER NOT NULL,
                date TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending',  -- pending|in_progress|completed|skipped
                completed_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scenario_id) REFERENCES scenarios(id),
                UNIQUE(scenario_id, day)
            )
        """)

        # ---- 保留旧 situations 表用于迁移（不再写入新数据）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS situations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                raw_input TEXT NOT NULL,
                matched_package_code TEXT,
                matched_package_name TEXT,
                confidence REAL,
                alternative_codes TEXT,
                behavior_tags TEXT,
                severity TEXT,
                signal_type TEXT,
                signal_detail TEXT,
                clarification_needed TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- 旧 feedback 表保留用于迁移 ----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS old_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                package_code TEXT NOT NULL,
                package_name TEXT,
                day_number INTEGER,
                emoji TEXT,
                feedback_text TEXT,
                training_opportunities INTEGER,
                independent_success INTEGER,
                p0_success_rate REAL,
                max_prompt_level TEXT,
                emotion_behavior TEXT,
                session_duration_minutes INTEGER,
                analysis_result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- children 表（孩子档案，PRD v3.4 定义）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS children (
                id TEXT PRIMARY KEY,           -- UUID v4
                user_id TEXT,
                name TEXT NOT NULL,            -- 孩子姓名，默认"小星"
                age INTEGER,                   -- 年龄
                gender TEXT,                   -- 性别：boy/girl
                diagnosis_date TEXT,           -- 诊断日期 YYYY-MM-DD
                diagnosis_type TEXT,           -- 诊断类型，如"ASD"
                diagnosis_level TEXT,          -- 程度：轻度/中度/重度
                notes TEXT,                    -- 备注
                avatar_emoji TEXT,             -- 头像emoji
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- user_settings 表（用户设置，PRD v3.4 定义）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id TEXT PRIMARY KEY,           -- UUID v4
                user_id TEXT NOT NULL,
                key TEXT NOT NULL,             -- 设置键
                value TEXT,                    -- 设置值（JSON字符串）
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, key)
            )
        """)

        # ---- Indexes ----
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_user ON scenarios(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scenarios_status ON scenarios(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_scenario ON tasks(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_day ON tasks(scenario_id, day)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_encouragement_scenario ON encouragement_texts(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_scenario ON feedback(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_feedback_task ON feedback(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_daily_status_scenario ON daily_task_status(scenario_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_children_user ON children(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_settings_user ON user_settings(user_id)")

        # ---- user_input_logs 表（用户输入日志）----
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_input_logs (
                id TEXT PRIMARY KEY,           -- UUID v4
                user_id TEXT,                  -- 用户ID（来自localStorage）
                raw_input TEXT NOT NULL,       -- 用户原始输入
                input_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                intent_type TEXT,              -- 意图类型（situation_input/create_scenario等）
                analysis_duration_ms INTEGER,  -- AI语义分析耗时（毫秒）
                matched_package_code TEXT,     -- 匹配到的任务包编号
                matched_package_name TEXT,    -- 匹配到的任务包名称
                confidence REAL,              -- 匹配置信度
                recognition_result TEXT,       -- AI返回的完整识别结果（JSON）
                scenario_id TEXT,              -- 创建的情境ID
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # ---- user_input_logs 索引 ----
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_user ON user_input_logs(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_time ON user_input_logs(input_timestamp)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_logs_scenario ON user_input_logs(scenario_id)")

        # ---- daily_task_status 表补充缺失字段（PRD v3.4 定义）----
        # train_count: 训练次数（"1~2次"/"3~5次"/"5次+"）
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN train_count TEXT
        """)
        # feedback_rating: 反馈评分（good/neutral/bad）
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN feedback_rating TEXT
        """)
        # feedback_note: 反馈备注
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN feedback_note TEXT
        """)
        # analysis_signal: 分析信号（escalate/maintain/de-escalate/regenerate）
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN analysis_signal TEXT
        """)
        # analysis_target_step: 目标步骤
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN analysis_target_step INTEGER
        """)
        # analysis_recommendation: 建议（仅regenerate时）
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN analysis_recommendation TEXT
        """)
        # analysis_mode: 分析模式（ai/rule）
        cursor.execute("""
            ALTER TABLE daily_task_status ADD COLUMN analysis_mode TEXT
        """)


# ============================================================
# Scenarios CRUD
# ============================================================

def create_scenario(
    user_id: str,
    package_code: str,
    package_name: str,
    raw_input: str,
    goal: str,
    confidence: float,
    behavior_tags: List[str],
    signal_type: str,
    signal_detail: str,
    days_data: Dict[str, Any]
) -> str:
    """创建新 scenario，返回 scenario_id (UUID)"""
    scenario_id = str(uuid.uuid4())
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO scenarios (
                id, user_id, package_code, package_name, raw_input, goal,
                confidence, behavior_tags, signal_type, signal_detail,
                days_data, clarification_needed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scenario_id, user_id, package_code, package_name, raw_input, goal,
            confidence, json.dumps(behavior_tags, ensure_ascii=False),
            signal_type, signal_detail,
            json.dumps(days_data, ensure_ascii=False),
            1 if signal_type and signal_type != "none" else 0
        ))
    return scenario_id


def get_scenario(scenario_id: str) -> Optional[Dict[str, Any]]:
    """获取 scenario（排除已删除的）"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM scenarios WHERE id = ? AND status != 'deleted'", (scenario_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def create_user_input_log(
    user_id: str,
    raw_input: str,
    intent_type: str,
    analysis_duration_ms: int,
    matched_package_code: str,
    matched_package_name: str,
    confidence: float,
    recognition_result: Dict[str, Any],
    scenario_id: str = None
) -> str:
    """创建用户输入日志，返回 log_id"""
    import time
    log_id = str(uuid.uuid4())
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO user_input_logs (
                id, user_id, raw_input, input_timestamp, intent_type,
                analysis_duration_ms, matched_package_code, matched_package_name,
                confidence, recognition_result, scenario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            log_id, user_id, raw_input, time.strftime("%Y-%m-%d %H:%M:%S"),
            intent_type, analysis_duration_ms, matched_package_code,
            matched_package_name, confidence,
            json.dumps(recognition_result, ensure_ascii=False),
            scenario_id
        ))
    return log_id


def get_user_input_logs(
    user_id: str = None,
    limit: int = 100,
    offset: int = 0
) -> List[Dict[str, Any]]:
    """获取用户输入日志"""
    with get_db_cursor() as cursor:
        if user_id:
            cursor.execute("""
                SELECT * FROM user_input_logs
                WHERE user_id = ?
                ORDER BY input_timestamp DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
        else:
            cursor.execute("""
                SELECT * FROM user_input_logs
                ORDER BY input_timestamp DESC
                LIMIT ? OFFSET ?
            """, (limit, offset))
        return [dict(row) for row in cursor.fetchall()]


def update_scenario_status(scenario_id: str, status: str) -> bool:
    """更新 scenario 状态（软删除/完成/废弃）"""
    completed_at = datetime.now().isoformat() if status in ("completed", "deleted", "abandoned") else None
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE scenarios SET status = ?, updated_at = ?, completed_at = ?
            WHERE id = ?
        """, (status, datetime.now().isoformat(), completed_at, scenario_id))
        return cursor.rowcount > 0


def update_scenario_current_day(scenario_id: str, day: int) -> bool:
    """更新 scenario 当前进度天数"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE scenarios SET current_day = ?, updated_at = ?
            WHERE id = ?
        """, (day, datetime.now().isoformat(), scenario_id))
        return cursor.rowcount > 0


# ============================================================
# Tasks CRUD
# ============================================================

def create_tasks_for_scenario(scenario_id: str, package_code: str, days_data: Dict[str, Any]) -> List[str]:
    """
    根据 days_data 创建 tasks 表记录。
    days_data 结构: {"days": [{"day": 1, "theme": "...", "goal": {...}, "steps": [...]}, ...]}
    返回 task_id 列表。
    """
    task_ids = []
    with get_db_cursor() as cursor:
        for day_obj in days_data.get("days", []):
            day = day_obj["day"]
            tasks_in_day = day_obj.get("tasks", [])
            if not tasks_in_day:
                # 兼容只有单个任务的情况（daily_plan 中直接是 steps）
                task_id = f"{package_code}_D{day}_T1"
                cursor.execute("""
                    INSERT OR REPLACE INTO tasks
                    (id, scenario_id, package_code, day, name, steps, duration_minutes, status, order_index)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', 0)
                """, (
                    task_id, scenario_id, package_code, day,
                    day_obj.get("theme", f"Day {day}"),
                    json.dumps(day_obj.get("steps", []), ensure_ascii=False),
                    day_obj.get("duration_minutes", 10)
                ))
                task_ids.append(task_id)
            else:
                for idx, task_obj in enumerate(tasks_in_day, 1):
                    task_id = f"{package_code}_D{day}_T{idx}"
                    cursor.execute("""
                        INSERT OR REPLACE INTO tasks
                        (id, scenario_id, package_code, day, name, steps, duration_minutes, status, order_index)
                        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', ?)
                    """, (
                        task_id, scenario_id, package_code, day,
                        task_obj.get("name", day_obj.get("theme", f"Task {idx}")),
                        json.dumps(task_obj.get("steps", []), ensure_ascii=False),
                        day_obj.get("duration_minutes", day_obj.get("duration_minutes", 10)),
                        idx
                    ))
                    task_ids.append(task_id)
    return task_ids


def get_tasks_for_day(scenario_id: str, day: int) -> List[Dict[str, Any]]:
    """获取某天的所有任务"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM tasks
            WHERE scenario_id = ? AND day = ?
            ORDER BY order_index
        """, (scenario_id, day))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_task(task_id: str) -> Optional[Dict[str, Any]]:
    """获取单个任务"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def update_task_status(task_id: str, status: str) -> bool:
    """更新任务状态"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE tasks SET status = ?, has_feedback = 1
            WHERE id = ?
        """, (status, task_id))
        return cursor.rowcount > 0


def get_scenario_tasks_summary(scenario_id: str) -> List[Dict[str, Any]]:
    """获取 scenario 下所有天的任务概览（用于 GET /api/tasks/daily 响应）"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT day, status, COUNT(*) as task_count,
                   SUM(CASE WHEN has_feedback = 1 THEN 1 ELSE 0 END) as completed_count
            FROM tasks
            WHERE scenario_id = ?
            GROUP BY day, status
            ORDER BY day
        """, (scenario_id,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================
# Encouragement Texts
# ============================================================

def generate_encouragement_texts(scenario_id: str, package_name: str) -> int:
    """
    任务包创建时批量生成鼓励文（21条 = 7天 × 3档emoji）。
    MVP方案：使用硬编码模板，不调用AI。
    返回生成条数。
    """
    emojis = ["very_dissatisfied", "dissatisfied", "satisfied"]
    encouragements = {
        "very_dissatisfied": [
            "今天有点难，但每一次尝试都是进步！💪",
            "没关系的，我们慢慢来，明天会更棒的！🌱",
            "今天虽然不顺利，但你在努力，就是最棒的！❤️",
        ],
        "dissatisfied": [
            "今天的进步虽然小，但积累起来就很了不起！🌟",
            "加油！明天我们再试一次，一定会有突破的！💫",
            "你在慢慢进步，妈妈/爸爸为你骄傲！🌈",
        ],
        "satisfied": [
            "太棒了！今天的训练很顺利，你做得真好！🎉",
            "进步明显！继续保持，期待你明天更棒的表现！🏆",
            "做得好！你的努力得到了回报，继续加油！⭐",
        ],
    }

    count = 0
    with get_db_cursor() as cursor:
        for day in range(1, 8):
            for emoji in emojis:
                text = encouragements[emoji][day % 3]
                enc_id = str(uuid.uuid4())
                try:
                    cursor.execute("""
                        INSERT INTO encouragement_texts (id, scenario_id, day, emoji, text)
                        VALUES (?, ?, ?, ?, ?)
                    """, (enc_id, scenario_id, day, emoji, text))
                    count += 1
                except sqlite3.IntegrityError:
                    pass  # 已存在则跳过
    return count


def get_encouragement_for_day(scenario_id: str, day: int, emoji: str) -> Optional[str]:
    """获取某天某emoji对应的鼓励文"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT text FROM encouragement_texts
            WHERE scenario_id = ? AND day = ? AND emoji = ?
        """, (scenario_id, day, emoji))
        row = cursor.fetchone()
        return row["text"] if row else None


# ============================================================
# AI Encouragement Generation (US-006)
# ============================================================

# DeepSeek API配置（从环境变量读取）
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")


def generate_ai_encouragement(feedback_data: Dict[str, Any]) -> str:
    """
    US-006: AI实时生成微感知文案（温暖、正向、≤20字）
    调用DeepSeek API，失败时fallback到硬编码模板。

    feedback_data 包含:
    - emoji: 家长选择的表情 (very_dissatisfied/dissatisfied/satisfied/very_satisfied)
    - day: 当前训练天数 (int)
    - training_record: 训练数据 (dict，可选)
    - parent_text: 家长文字备注 (str，可选)
    - scenario_id: 情境ID (str，可选)
    """
    emoji_label_map = {
        "very_dissatisfied": "有难度",
        "dissatisfied": "有挑战",
        "satisfied": "顺利",
        "very_satisfied": "非常棒",
        "👍": "顺利",
        "😐": "有挑战",
        "👎": "有难度",
    }
    emoji = feedback_data.get("emoji", "satisfied")
    day = feedback_data.get("day", 1)
    training_record = feedback_data.get("training_record") or {}
    parent_text = feedback_data.get("parent_text", "")
    scenario_id = feedback_data.get("scenario_id", "")

    # 构建上下文
    p0_rate = training_record.get("p0_success_rate", None)
    independent_success = training_record.get("independent_success", 0)
    opportunities = training_record.get("opportunities", 0)
    emotion_behavior = training_record.get("emotion_behavior", "")

    system_prompt = """你是一个ASD儿童家庭干预的微感知文案专家。
你的任务是生成温暖、正向的鼓励文案，帮助家长建立信心。
要求：
1. 温暖、简洁、正向
2. 不使用专业术语（不用P0/P2等缩写，不用"强化"、"辅助"等）
3. 使用对比句式（"比昨天..."、"这次..."）
4. 控制在20字以内
5. 纯文案输出，不要任何格式符号，直接输出一句话"""

    # 构造user_message
    context_parts = [f"家长提交了第{day}天训练反馈，表情反馈：{emoji_label_map.get(emoji, emoji)}"]
    if parent_text:
        context_parts.append(f"家长备注：{parent_text}")
    if p0_rate is not None:
        context_parts.append(f"独立成功率：{p0_rate:.0%}" if p0_rate > 1 else f"独立成功：{independent_success}/{opportunities}次")
    if emotion_behavior:
        context_parts.append(f"孩子表现：{emotion_behavior}")
    if scenario_id:
        context_parts.append(f"训练主题ID：{scenario_id[:8]}")

    user_message = "\n".join(context_parts) + "\n\n请生成一句温暖的鼓励文案（≤20字），直接输出，不要任何前缀。"

    # 调用DeepSeek
    result = _call_deepseek_simple(system_prompt, user_message, temperature=0.7)
    text = result.get("content", "").strip()

    # 清理输出（去除引号、序号等）
    text = re.sub(r'^[""\'""\d\.\-\s]+', '', text)
    text = text.strip('""\'"')

    # 长度校验，截断超长文本
    if len(text) > 20:
        text = text[:19] + "…"

    # Fallback兜底
    if not text or len(text) < 5:
        return _fallback_encouragement(emoji, day)

    return text


def _call_deepseek_simple(system_prompt: str, user_message: str, temperature: float = 0.7) -> Dict[str, Any]:
    """调用DeepSeek API（三层降级：DeepSeek → NVIDIA NIM → Mock）"""
    # MOCK_MODE降级
    if os.getenv("MOCK_MODE", "").lower() == "true":
        return _mock_encouragement_response(emoji_for_mock(user_message))

    session = requests.Session()
    retry_strategy = Retry(
        total=2, backoff_factor=1,
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
        "max_tokens": 100
    }

    # 第1层：DeepSeek API（60s超时）
    for attempt in range(3):
        try:
            response = session.post(
                f"{DEEPSEEK_BASE_URL}/chat/completions",
                headers=headers, json=payload, timeout=60
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return {"content": content}
            elif response.status_code in [500, 502, 503, 504]:
                continue
            else:
                break
        except requests.exceptions.Timeout:
            continue
        except requests.exceptions.RequestException:
            break

    # 第2层：NVIDIA NIM备用
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
            "max_tokens": 100
        }
        try:
            response = session.post(
                f"{nvim_base_url}/chat/completions",
                headers=nvim_headers, json=nvim_payload, timeout=60
            )
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                return {"content": content}
        except Exception:
            pass

    # 最终降级：Mock
    return _mock_encouragement_response(emoji_for_mock(user_message))


def emoji_for_mock(user_message: str) -> str:
    """从user_message中推断emoji类型"""
    if "非常棒" in user_message or "very_satisfied" in user_message:
        return "very_satisfied"
    elif "有难度" in user_message or "very_dissatisfied" in user_message:
        return "very_dissatisfied"
    elif "有挑战" in user_message or "dissatisfied" in user_message:
        return "dissatisfied"
    return "satisfied"


def _mock_encouragement_response(emoji: str) -> Dict[str, Any]:
    """Mock降级响应"""
    texts = {
        "very_satisfied": "太棒了！继续保持，期待你明天更棒！",
        "satisfied": "今天的进步虽然小，但积累起来很了不起！",
        "dissatisfied": "加油！明天再试一次，一定会有突破！",
        "very_dissatisfied": "今天有点难，但每一次尝试都是进步！",
    }
    return {"content": texts.get(emoji, "做得好！继续加油！")}


def _fallback_encouragement(emoji: str, day: int) -> str:
    """硬编码兜底鼓励文案"""
    encouragements = {
        "very_satisfied": [
            "太棒了！继续保持，期待你明天更棒！",
            "今天的训练很顺利，你做得真好！",
            "进步明显！继续加油，棒棒哒！",
        ],
        "satisfied": [
            "今天的进步虽然小，但积累起来很了不起！",
            "加油！明天再试一次，一定会有突破！",
            "你在慢慢进步，继续加油！",
        ],
        "dissatisfied": [
            "加油！明天再试一次，一定会有突破！",
            "今天的进步虽然小，但积累起来很了不起！",
            "没关系，我们慢慢来，明天会更棒的！",
        ],
        "very_dissatisfied": [
            "今天有点难，但每一次尝试都是进步！",
            "没关系，我们慢慢来，明天会更棒的！",
            "今天虽然不顺利，但你在努力就是最棒的！",
        ],
    }
    emoji_key = emoji if emoji in encouragements else "satisfied"
    return encouragements[emoji_key][day % 3]


# ============================================================
# Daily Task Status
# ============================================================

def init_daily_status(scenario_id: str, days: int) -> None:
    """初始化每日任务状态（创建scenario时调用）"""
    today = date.today()
    with get_db_cursor() as cursor:
        for i in range(days):
            day_num = i + 1
            day_date = (today + __import__('datetime').timedelta(days=i)).isoformat()
            cursor.execute("""
                INSERT OR IGNORE INTO daily_task_status (id, scenario_id, day, date, status)
                VALUES (?, ?, ?, ?, 'pending')
            """, (str(uuid.uuid4()), scenario_id, day_num, day_date))


def update_daily_status(scenario_id: str, day: int, status: str) -> bool:
    """更新每日状态"""
    completed_at = datetime.now().isoformat() if status == "completed" else None
    with get_db_cursor() as cursor:
        cursor.execute("""
            UPDATE daily_task_status SET status = ?, completed_at = ?
            WHERE scenario_id = ? AND day = ?
        """, (status, completed_at, scenario_id, day))
        return cursor.rowcount > 0


def get_daily_status(scenario_id: str, day: int) -> Optional[Dict[str, Any]]:
    """获取某天状态"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM daily_task_status WHERE scenario_id = ? AND day = ?
        """, (scenario_id, day))
        row = cursor.fetchone()
        return dict(row) if row else None


# ============================================================
# Feedback
# ============================================================

def create_feedback(
    scenario_id: str,
    task_id: str,
    day: int,
    emoji: str,
    text: str,
    training_record: Dict[str, Any],
    analysis_result: Dict[str, Any]
) -> str:
    """创建反馈记录"""
    feedback_id = str(uuid.uuid4())
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO feedback (id, scenario_id, task_id, day, emoji, text, training_record, analysis_result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            feedback_id, scenario_id, task_id, day, emoji, text,
            json.dumps(training_record, ensure_ascii=False),
            json.dumps(analysis_result, ensure_ascii=False)
        ))
    # 同步更新 task 和 daily_status
    update_task_status(task_id, "completed")
    all_tasks_done = check_day_all_tasks_done(scenario_id, day)
    if all_tasks_done:
        update_daily_status(scenario_id, day, "completed")
        # 检查是否所有7天都完成了 -> scenario 标记 completed
        if check_all_days_completed(scenario_id):
            update_scenario_status(scenario_id, "completed")
    return feedback_id


def check_day_all_tasks_done(scenario_id: str, day: int) -> bool:
    """检查某天所有任务是否都完成了"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN has_feedback = 1 THEN 1 ELSE 0 END) as done
            FROM tasks WHERE scenario_id = ? AND day = ?
        """, (scenario_id, day))
        row = cursor.fetchone()
        total = row["total"] or 0
        done = row["done"] or 0
        return done >= total and total > 0


def check_all_days_completed(scenario_id: str) -> bool:
    """检查某scenario是否所有7天都完成了"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as total, SUM(CASE WHEN has_feedback = 1 THEN 1 ELSE 0 END) as done
            FROM tasks WHERE scenario_id = ?
        """, (scenario_id,))
        row = cursor.fetchone()
        total = row["total"] or 0
        done = row["done"] or 0
        return done >= total and total >= 7


def get_feedback_history(scenario_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """获取某 scenario 的反馈历史（Mock模式下task可能不在tasks表，去除JOIN）"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT f.*
            FROM feedback f
            WHERE f.scenario_id = ?
            ORDER BY f.created_at DESC
            LIMIT ?
        """, (scenario_id, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# ============================================================
# 旧数据迁移（一次性）
# ============================================================

def migrate_old_feedback():
    """一次性迁移旧 feedback 数据到新表（只执行一次）"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='old_feedback'")
        if cursor.fetchone():
            return  # 已迁移

    with get_db_cursor() as cursor:
        # 复制旧数据到 old_feedback
        cursor.execute("""
            INSERT INTO old_feedback
            SELECT * FROM feedback
        """)

    with get_db_cursor() as cursor:
        # 迁移 feedback 表：添加新字段（SQLite不支持直接添加TEXT PRIMARY KEY，用新表替代）
        pass  # 实际上通过 ALTER TABLE 无法添加 PRIMARY KEY，需要重建表，此处略过迁移


# ============================================================
# 旧 API 兼容函数（保留用于前端 demo 联调）
# ============================================================

def save_feedback_legacy(feedback_data: Dict[str, Any], analysis_result: Dict[str, Any]) -> int:
    """兼容旧 save_feedback 签名，内部重定向到新实现"""
    pass  # 已废弃，不再使用


def save_situation(situation_data: Dict[str, Any]) -> int:
    """兼容旧 save_situation 签名，内部写入 situations 表"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO situations (
                raw_input, matched_package_code, matched_package_name,
                confidence, alternative_codes, behavior_tags, severity,
                signal_type, signal_detail, clarification_needed
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            situation_data.get("raw_input"),
            situation_data.get("matched_package_code"),
            situation_data.get("matched_package_name"),
            situation_data.get("confidence"),
            json.dumps(situation_data.get("alternative_codes", [])),
            json.dumps(situation_data.get("behavior_tags", [])),
            situation_data.get("severity"),
            situation_data.get("signal_type"),
            situation_data.get("signal_detail"),
            json.dumps(situation_data.get("clarification_needed", []))
        ))
        return cursor.lastrowid


def get_history_by_package(package_code: str, limit: int = 50) -> List[Dict[str, Any]]:
    """兼容旧 API：通过 package_code 查历史（跨 scenario）"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT f.*, s.package_name
            FROM old_feedback f
            JOIN scenarios s ON s.package_code = f.package_code
            WHERE f.package_code = ?
            ORDER BY f.created_at DESC
            LIMIT ?
        """, (package_code, limit))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def get_all_feedbacks(limit: int = 100) -> List[Dict[str, Any]]:
    """兼容旧 API：获取所有反馈"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM feedback ORDER BY created_at DESC LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


# Initialize on module load
init_database()
