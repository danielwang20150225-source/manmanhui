"""
Mock 数据加载器
从 data/mock/mock_packages.json 加载 Mock 数据
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Mock 数据文件路径
MOCK_DATA_PATH = Path(__file__).parent.parent / "data" / "mock" / "mock_packages.json"

# 缓存
_mock_cache: Optional[Dict[str, Any]] = None


def load_mock_data() -> Dict[str, Any]:
    """加载 Mock 数据文件"""
    global _mock_cache

    if _mock_cache is not None:
        return _mock_cache

    if not MOCK_DATA_PATH.exists():
        return {"packages": {}, "fallback": None}

    with open(MOCK_DATA_PATH, 'r', encoding='utf-8') as f:
        _mock_cache = json.load(f)

    return _mock_cache


def get_mock_package(package_code: str) -> Optional[Dict[str, Any]]:
    """根据 package_code 获取 Mock 数据"""
    data = load_mock_data()
    packages = data.get("packages", {})

    # 精确匹配
    if package_code in packages:
        return packages[package_code]

    # 模糊匹配（检查 code 是否包含在 key 中）
    for key, package in packages.items():
        if package_code in key or key in package_code:
            return package

    return None


def get_mock_packages_by_tag(tag: str) -> Optional[Dict[str, Any]]:
    """根据标签获取 Mock 数据（PRD 定义）"""
    data = load_mock_data()
    packages = data.get("packages", {})

    # 标签到 package_code 的映射
    tag_mapping = {
        "穿衣抗拒": "20260505001_fuyi_kangju",
        "社交回避": "20260505002_shejiao_duobi",
        "叫名字不应": "20260505003_jiaomingzi_baying",
        "情绪崩溃": "20260505004_qingxu_bengkuai",
        "眼神不对视": "20260505005_yanshen_buyishi",
        "刻板行为": "20260505006_kebian_xingwei",
    }

    package_code = tag_mapping.get(tag)
    if package_code and package_code in packages:
        return packages[package_code]

    return None


def get_fallback_package() -> Optional[Dict[str, Any]]:
    """获取默认 Mock 数据（兜底）"""
    data = load_mock_data()
    packages = data.get("packages", {})

    fallback_code = data.get("fallback")
    if fallback_code and fallback_code in packages:
        return packages[fallback_code]

    # 兜底的兜底：返回第一个包
    if packages:
        return next(iter(packages.values()))

    return None


def is_mock_mode() -> bool:
    """检查是否启用 Mock 模式"""
    return os.getenv("MOCK_MODE", "").lower() == "true"


def get_mock_encouragement(emoji: str, day: int = 1) -> str:
    """获取 Mock 鼓励文案"""
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
        # PRD v3.4 映射
        "👍": "太棒了！继续保持，期待你明天更棒！",
        "😐": "加油！明天再试一次，一定会有突破！",
        "👎": "今天有点难，但每一次尝试都是进步！",
    }

    emoji_key = emoji if emoji in encouragements else "satisfied"
    if isinstance(emoji_key, str) and emoji_key in encouragements:
        return encouragements[emoji_key][day % 3]
    elif emoji in encouragements:
        return encouragements[emoji]

    return "做得好！继续加油！"


def get_mock_analysis() -> Dict[str, Any]:
    """获取 Mock 分析结果"""
    return {
        "signal": "maintain",
        "analysis_text": "Mock数据，无真实分析",
        "target_step": None,
        "recommendation": None,
        "mode": "rule"
    }