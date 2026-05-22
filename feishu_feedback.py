"""
飞书反馈同步模块
将用户反馈同步到飞书多维表格
"""
import os
import uuid
import json
import requests
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# 加载环境变量
from pathlib import Path
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / "config" / ".env")

# 飞书API基础URL
FEISHU_API_BASE = "https://open.feishu.cn/open-apis"

# 缓存token
_cached_token = None
_token_expires_at = 0


def _get_config():
    """获取配置"""
    return {
        "app_id": os.getenv("FEISHU_APP_ID", ""),
        "app_secret": os.getenv("FEISHU_APP_SECRET", ""),
        # 用户反馈表格配置（需要手动在飞书创建）
        "feedback_base_id": os.getenv("FEISHU_FEEDBACK_BASE_ID", ""),
        "feedback_table_id": os.getenv("FEISHU_FEEDBACK_TABLE_ID", ""),
    }


def is_feishu_feedback_configured() -> bool:
    """检查飞书反馈功能是否已配置"""
    config = _get_config()
    return bool(config["app_id"] and config["app_secret"] and
                config["feedback_base_id"] and config["feedback_table_id"])


def get_tenant_access_token() -> Optional[str]:
    """获取tenant_access_token"""
    global _cached_token, _token_expires_at

    config = _get_config()

    # 检查缓存的token是否还有效
    if _cached_token and time.time() < _token_expires_at - 300:
        return _cached_token

    if not config["app_id"] or not config["app_secret"]:
        return None

    try:
        url = f"{FEISHU_API_BASE}/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": config["app_id"],
            "app_secret": config["app_secret"]
        }
        resp = requests.post(url, json=payload, timeout=10)
        data = resp.json()

        if data.get("code") == 0:
            _cached_token = data.get("tenant_access_token")
            _token_expires_at = time.time() + data.get("expire", 7200)
            return _cached_token
        return None
    except Exception:
        return None


def upload_image_to_feishu(image_data: bytes, filename: str = "feedback.png") -> Optional[str]:
    """
    上传图片到飞书云盘

    Args:
        image_data: 图片二进制数据
        filename: 文件名

    Returns:
        file_token 或 None
    """
    config = _get_config()
    if not config["app_id"] or not config["app_secret"]:
        return None

    token = get_tenant_access_token()
    if not token:
        return None

    try:
        # 使用 drive API 上传文件到多维表格
        url = f"{FEISHU_API_BASE}/drive/v1/files/upload_all"
        headers = {
            "Authorization": f"Bearer {token}"
        }

        files = {
            "file_name": (None, filename),
            "parent_type": (None, "bitable_file"),
            "parent_node": (None, config["feedback_base_id"]),
            "size": (None, str(len(image_data))),
            "file": (filename, image_data, "image/png")
        }

        resp = requests.post(url, headers=headers, files=files, timeout=30)
        result = resp.json()

        if result.get("code") == 0:
            return result.get("data", {}).get("file_token")
        print(f"[飞书] 图片上传失败: {result}")
        return None
    except Exception as e:
        print(f"[飞书] 图片上传异常: {e}")
        return None


def create_feedback_record(
    feedback_id: str,
    user_identifier: str,
    page_source: str,
    feedback_text: str,
    image_tokens: List[str],
    created_at: str,
    client_ip: str = ""
) -> bool:
    """
    在飞书多维表格中创建反馈记录

    Args:
        feedback_id: 反馈唯一ID
        user_identifier: 用户UUID
        page_source: 来源页面
        feedback_text: 反馈内容
        image_tokens: 飞书图片token列表
        created_at: 创建时间
        client_ip: 客户端IP

    Returns:
        是否创建成功
    """
    config = _get_config()
    if not config["app_id"] or not config["app_secret"]:
        return False

    if not config["feedback_base_id"] or not config["feedback_table_id"]:
        return False

    token = get_tenant_access_token()
    if not token:
        return False

    try:
        url = f"{FEISHU_API_BASE}/bitable/v1/apps/{config['feedback_base_id']}/tables/{config['feedback_table_id']}/records"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 组合用户标识
        full_identifier = f"{user_identifier}_{client_ip}" if client_ip else user_identifier

        # 飞书多维表格字段映射
        # image_tokens 需要是字符串（多行文本）
        # created_at 需要是 Unix 时间戳（秒）
        from datetime import datetime, timezone
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_at_timestamp = int(dt.timestamp() * 1000)  # 毫秒
        except:
            created_at_timestamp = int(datetime.now(timezone.utc).timestamp() * 1000)  # 毫秒

        fields = {
            "反馈ID": feedback_id,
            "用户标识": full_identifier,
            "来源页面": page_source,
            "反馈内容": feedback_text,
            "提交时间": created_at_timestamp,
            "处理状态": "待处理"
        }

        # 如果有图片，设置附件字段
        if image_tokens:
            fields["附件"] = [{"file_token": token} for token in image_tokens]

        payload = {
            "fields": fields
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()

        return result.get("code") == 0

    except Exception:
        return False


def update_feedback_status(feedback_id: str, status: str) -> bool:
    """
    更新反馈状态

    Args:
        feedback_id: 反馈ID
        status: 新状态（待处理/处理中/已处理）

    Returns:
        是否更新成功
    """
    config = _get_config()
    if not config["feedback_base_id"] or not config["feedback_table_id"]:
        return False

    token = get_tenant_access_token()
    if not token:
        return False

    try:
        # 先查询记录获取 record_id
        search_url = f"{FEISHU_API_BASE}/bitable/v1/apps/{config['feedback_base_id']}/tables/{config['feedback_table_id']}/records"

        headers = {
            "Authorization": f"Bearer {token}"
        }

        params = {
            "filter": f'AND(CurrentValue."feedback_id"="{feedback_id}")'
        }

        resp = requests.get(search_url, headers=headers, params=params, timeout=30)
        result = resp.json()

        if result.get("code") != 0:
            return False

        items = result.get("data", {}).get("items", [])
        if not items:
            return False

        record_id = items[0].get("record_id")

        # 更新状态
        update_url = f"{FEISHU_API_BASE}/bitable/v1/apps/{config['feedback_base_id']}/tables/{config['feedback_table_id']}/records/{record_id}"

        payload = {
            "fields": {
                "status": status
            }
        }

        resp = requests.put(update_url, headers=headers, json=payload, timeout=30)
        result = resp.json()

        return result.get("code") == 0

    except Exception:
        return False


def generate_feedback_id() -> str:
    """生成反馈唯一ID"""
    timestamp = datetime.now().strftime("%Y%m%d")
    random_str = uuid.uuid4().hex[:8]
    return f"fb_{timestamp}_{random_str}"


# ============================================================
# 数据库操作（本地备份）
# ============================================================

def save_feedback_to_db(
    feedback_id: str,
    user_identifier: str,
    page_source: str,
    feedback_text: str,
    image_tokens: List[str],
    client_ip: str = ""
) -> bool:
    """
    保存反馈到本地SQLite数据库（备份用）

    需要先创建表：
    CREATE TABLE IF NOT EXISTS user_feedbacks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        feedback_id TEXT UNIQUE,
        user_identifier TEXT,
        page_source TEXT,
        feedback_text TEXT,
        image_tokens TEXT,
        client_ip TEXT,
        feishu_synced INTEGER DEFAULT 0,
        created_at TEXT,
        synced_at TEXT
    );
    """
    try:
        from database import get_db_cursor

        with get_db_cursor() as cursor:
            # 确保表存在
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_feedbacks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    feedback_id TEXT UNIQUE,
                    user_identifier TEXT,
                    page_source TEXT,
                    feedback_text TEXT,
                    image_tokens TEXT,
                    client_ip TEXT,
                    feishu_synced INTEGER DEFAULT 0,
                    created_at TEXT,
                    synced_at TEXT
                )
            """)

            # 插入记录
            cursor.execute("""
                INSERT OR REPLACE INTO user_feedbacks
                (feedback_id, user_identifier, page_source, feedback_text, image_tokens, client_ip, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                feedback_id,
                user_identifier,
                page_source,
                feedback_text,
                json.dumps(image_tokens),
                client_ip,
                datetime.now().isoformat()
            ))

        return True
    except Exception:
        return False


def mark_feedback_synced(feedback_id: str) -> bool:
    """标记反馈已同步到飞书"""
    try:
        from database import get_db_cursor

        with get_db_cursor() as cursor:
            cursor.execute("""
                UPDATE user_feedbacks
                SET feishu_synced = 1, synced_at = ?
                WHERE feedback_id = ?
            """, (datetime.now().isoformat(), feedback_id))

        return True
    except Exception:
        return False


def create_feedback_table() -> Optional[Dict[str, str]]:
    """
    创建飞书用户反馈表格

    Returns:
        包含 base_id 和 table_id 的字典，或 None
    """
    config = _get_config()
    if not config["app_id"] or not config["app_secret"]:
        print("[飞书] 未配置APP_ID或APP_SECRET")
        return None

    token = get_tenant_access_token()
    if not token:
        print("[飞书] 无法获取access_token")
        return None

    try:
        # 先创建一个新的多维表格应用
        create_app_url = f"{FEISHU_API_BASE}/bitable/v1/apps"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 创建应用
        app_payload = {
            "name": "用户反馈"
        }
        app_resp = requests.post(create_app_url, headers=headers, json=app_payload, timeout=30)
        app_result = app_resp.json()

        if app_result.get("code") != 0:
            print(f"[飞书] 创建应用失败: {app_result}")
            return None

        base_id = app_result.get("data", {}).get("app", {}).get("app_token")
        print(f"[飞书] 创建应用成功，base_id: {base_id}")

        # 获取默认表格ID
        tables_url = f"{FEISHU_API_BASE}/bitable/v1/apps/{base_id}/tables"
        tables_resp = requests.get(tables_url, headers=headers, timeout=30)
        tables_result = tables_resp.json()

        if tables_result.get("code") != 0:
            print(f"[飞书] 获取表格列表失败: {tables_result}")
            return None

        # 使用第一个表格
        table_id = tables_result.get("data", {}).get("items", [{}])[0].get("table_id")
        print(f"[飞书] 获取表格成功，table_id: {table_id}")

        # 添加字段
        fields_url = f"{FEISHU_API_BASE}/bitable/v1/apps/{base_id}/tables/{table_id}/fields"

        fields = [
            {"field_name": "反馈ID", "type": 1},      # 文本
            {"field_name": "用户标识", "type": 1},   # 文本
            {"field_name": "来源页面", "type": 1},       # 文本
            {"field_name": "反馈内容", "type": 1},    # 文本
            {"field_name": "图片Token", "type": 1},     # 多选（用文本代替）
            {"field_name": "提交时间", "type": 5},       # 时间
            {"field_name": "处理状态", "type": 3},            # 单选
        ]

        for field in fields:
            field_resp = requests.post(fields_url, headers=headers, json=field, timeout=30)
            if field_resp.json().get("code") == 0:
                print(f"[飞书] 创建字段成功: {field['field_name']}")

        print(f"""
[飞书] 用户反馈表格创建完成！

配置信息：
  FEISHU_FEEDBACK_BASE_ID={base_id}
  FEISHU_FEEDBACK_TABLE_ID={table_id}

请将以上配置添加到 config/.env 文件中
""")
        return {"base_id": base_id, "table_id": table_id}

    except Exception as e:
        print(f"[飞书] 创建反馈表格异常: {e}")
        return None


if __name__ == "__main__":
    # 单独运行时创建表格
    print("开始创建飞书用户反馈表格...")
    result = create_feedback_table()
    if result:
        print(f"创建成功！")
        print(f"请将以下配置添加到 config/.env:")
        print(f"  FEISHU_FEEDBACK_BASE_ID={result['base_id']}")
        print(f"  FEISHU_FEEDBACK_TABLE_ID={result['table_id']}")
    else:
        print("创建失败，请检查飞书配置")