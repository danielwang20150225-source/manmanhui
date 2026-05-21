"""
飞书同步模块
将用户输入日志同步到飞书多维表格
"""
import os
import json
import requests
import time
from typing import Dict, Any, Optional

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
    """获取配置（运行时读取，避免模块加载时未加载dotenv）"""
    return {
        "app_id": os.getenv("FEISHU_APP_ID", ""),
        "app_secret": os.getenv("FEISHU_APP_SECRET", ""),
        "base_id": os.getenv("FEISHU_BASE_ID", "GlT3b6ZyNaVFyksHi45czz4pnyf"),
        "table_id": os.getenv("FEISHU_LOG_TABLE_ID", "tbleqRKsLgwbuvwf"),
    }


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
        else:
            return None
    except Exception:
        return None


def is_feishu_configured() -> bool:
    """检查飞书是否已正确配置"""
    config = _get_config()
    return bool(config["app_id"] and config["app_secret"])


def sync_user_input_log_to_feishu(log_data: Dict[str, Any]) -> bool:
    """同步用户输入日志到飞书多维表格

    Args:
        log_data: 日志数据，包含以下字段：
            - raw_input: 用户输入
            - input_timestamp: 输入时间
            - analysis_duration_ms: AI分析耗时
            - matched_package_code: 匹配的任务包编号
            - matched_package_name: 匹配的任务包名称
            - confidence: 匹配置信度
            - scenario_id: 创建的情境ID

    Returns:
        bool: 是否同步成功
    """
    config = _get_config()
    if not config["app_id"] or not config["app_secret"]:
        # 未配置飞书，静默跳过
        return False

    token = get_tenant_access_token()
    if not token:
        return False

    try:
        # 飞书多维表格 API 路径：/bitable/v1/apps/{app_token}/tables/{table_id}/records
        url = f"{FEISHU_API_BASE}/bitable/v1/apps/{config['base_id']}/tables/{config['table_id']}/records"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        # 飞书多维表格字段映射
        fields = {
            "用户输入": log_data.get("raw_input", ""),
            "输入时间": log_data.get("input_timestamp", ""),
            "分析耗时ms": log_data.get("analysis_duration_ms", 0),
            "任务包编号": log_data.get("matched_package_code", ""),
            "任务包名称": log_data.get("matched_package_name", ""),
            "匹配置信度": log_data.get("confidence", 0),
            "情境ID": log_data.get("scenario_id", ""),
            "意图类型": log_data.get("intent_type", ""),
            "用户ID": log_data.get("user_id", ""),
        }

        payload = {
            "fields": fields
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()

        return result.get("code") == 0

    except Exception:
        return False


def create_feishu_log_table() -> bool:
    """创建飞书用户输入日志表（如果不存在）

    这个函数需要在飞书多维表格中创建一个新的数据表
    需要先在飞书中创建表，然后获取table_id
    """
    config = _get_config()
    if not config["app_id"] or not config["app_secret"]:
        return False

    token = get_tenant_access_token()
    if not token:
        return False

    try:
        # 创建数据表
        url = f"{FEISHU_API_BASE}/bitable/v1/apps/{config['base_id']}/tables"

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }

        payload = {
            "table": {
                "name": "用户输入日志",
                "fields": [
                    {"field_name": "用户输入", "type": 1},  # 文本
                    {"field_name": "输入时间", "type": 1},  # 文本
                    {"field_name": "分析耗时ms", "type": 2},  # 数字
                    {"field_name": "任务包编号", "type": 1},  # 文本
                    {"field_name": "任务包名称", "type": 1},  # 文本
                    {"field_name": "匹配置信度", "type": 2},  # 数字
                    {"field_name": "情境ID", "type": 1},  # 文本
                    {"field_name": "意图类型", "type": 1},  # 文本
                    {"field_name": "用户ID", "type": 1},  # 文本
                ]
            }
        }

        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        result = resp.json()

        return result.get("code") == 0

    except Exception:
        return False