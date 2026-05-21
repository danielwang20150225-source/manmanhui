"""
慢慢会 - FastAPI Backend
对齐 PRD v2.1 API契约
"""

import os
import re
import json
import uuid
import asyncio
import time
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from contextlib import asynccontextmanager
import hashlib

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi import APIRouter
from pydantic import BaseModel, Field, ConfigDict
from dotenv import load_dotenv

# Import database module
from database import (
    init_database,
    create_scenario,
    get_scenario,
    update_scenario_status,
    update_scenario_current_day,
    create_tasks_for_scenario,
    generate_encouragement_texts,
    init_daily_status,
    get_tasks_for_day,
    get_task,
    get_encouragement_for_day,
    generate_ai_encouragement,
    create_feedback,
    get_feedback_history,
    update_task_status,
    update_daily_status,
    get_daily_status,
    get_history_by_package,
    get_all_feedbacks,
    save_situation,
    create_user_input_log,
    get_user_input_logs,
    get_db_cursor,
    DB_PATH,
)

# Import feishu sync module
from feishu_sync import sync_user_input_log_to_feishu, create_feishu_log_table, is_feishu_configured

# Import feishu feedback module
from feishu_feedback import (
    upload_image_to_feishu,
    create_feedback_record,
    generate_feedback_id,
    save_feedback_to_db,
    mark_feedback_synced,
    is_feishu_feedback_configured,
)

# Import services (增量拆分)
from services.mock_loader import get_mock_package, get_mock_packages_by_tag, get_fallback_package, is_mock_mode, get_mock_encouragement, get_mock_analysis

# Import parsers (增量拆分)
from parsers.markdown_parser import load_package_markdown as _load_package

# Import AI services (增量拆分)
from services.ai_service import (
    call_deepseek,
    call_deepseek_with_fallback,
    fallback_recognize,
    rule_based_analyze,
    ai_full_analyze,
    map_signal_to_action,
    apply_signal_action,
    map_emoji_to_signal,
    EXPRESSION_TREE,
)

# Load environment variables
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / "config" / ".env")

# DeepSeek API configuration
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", os.getenv("OPENAI_API_KEY", ""))
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")

# Packages path（Windows风格默认值，可通过环境变量覆盖）
PACKAGES_LIST_PATH = os.getenv(
    "PACKAGES_LIST_PATH",
    str(Path(__file__).parent / "data" / "knowledge-base" / "05_情境任务包" / "任务包清单.json")
)
# 如果 PACKAGES_PATH 指向文件而不是目录，自动取其父目录
_raw_packages_path = os.getenv(
    "PACKAGES_PATH",
    str(Path(__file__).parent / "data" / "knowledge-base" / "05_情境任务包")
)
if os.path.isfile(_raw_packages_path):
    PACKAGES_PATH = os.path.dirname(_raw_packages_path)
else:
    PACKAGES_PATH = _raw_packages_path

# Load prompts
def load_prompt(filename: str) -> str:
    prompt_path = PROJECT_ROOT / "prompts" / filename
    if prompt_path.exists():
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

PROMPT_A = load_prompt("prompt_A.md")
PROMPT_B = load_prompt("prompt_B.md")
PROMPT_C = load_prompt("prompt_C.md")

# Initialize database
init_database()

# ============================================================
# FastAPI App
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[OK] 慢慢会 API v2.1 已启动")
    print(f"[OK] 数据库: {DB_PATH}")
    print(f"[OK] DeepSeek API: {DEEPSEEK_BASE_URL}")
    print(f"[OK] 任务包路径: {PACKAGES_PATH}")
    mock_mode = os.getenv("MOCK_MODE", "").lower() == "true"
    print(f"[OK] MOCK_MODE: {mock_mode}")
    feishu_enabled = is_feishu_configured()
    print(f"[OK] 飞书同步: {'已配置' if feishu_enabled else '未配置'}")
    yield
    print("[OK] 慢慢会 API 已关闭")


app = FastAPI(
    title="慢慢会 - ASD家庭干预助手",
    description="基于ABA原理的家庭干预任务生成API | PRD v2.1",
    version="2.1.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 前端静态文件服务（挂载到 /static，避免拦截 /api/ 路由）
FRONTEND_PATH = os.getenv(
    "FRONTEND_PATH",
    str(Path(__file__).parent.parent / "micro-intervention")
)
if os.path.exists(FRONTEND_PATH):
    app.mount("/static", StaticFiles(directory=FRONTEND_PATH, html=True), name="frontend")

@app.get("/", include_in_schema=False)
async def serve_root():
    """根路径重定向到index.html"""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/static/index.html")

# ============================================================
# Pydantic Models (对齐 PRD v2.1)
# ============================================================

class RecognizeRequest(BaseModel):
    user_id: str = "default_user"
    text: str = Field(validation_alias="raw_input")
    session_context: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)


class TaskPackageGenerateRequest(BaseModel):
    scenario_id: Optional[str] = Field(default=None, validation_alias="id")
    package_code: Optional[str] = ""  # 空字符串时AI智能匹配
    package_name: str = ""
    period_days: int = 7
    user_id: str = "default_user"
    raw_input: Optional[str] = None  # PRD字段：原始用户输入
    selected_tags: Optional[List[str]] = Field(default=None, validation_alias="behavior_tags")

    model_config = ConfigDict(populate_by_name=True)


class FeedbackSubmitRequest(BaseModel):
    scenario_id: str
    task_id: str
    day: int
    emoji: str = Field(..., min_length=1)
    text: str
    training_record: Optional[Dict[str, Any]] = None


# ============================================================
# Exception Handlers
# ============================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    tb = traceback.format_exc()
    return JSONResponse(
        status_code=500,
        content={"code": 5000, "message": str(exc), "type": type(exc).__name__, "traceback": tb}
    )


# ============================================================
# 任务包 Markdown 解析器
# ============================================================

def load_package_markdown(package_code: str) -> Optional[Dict[str, Any]]:
    """从 markdown 文件加载任务包（委托给 parsers.markdown_parser）"""
    return _load_package(package_code, PACKAGES_PATH)


# Markdown 解析器已迁移到 parsers.markdown_parser
# AI 服务已迁移到 services.ai_service

# ============================================================
# match_package_with_ai (保留在 app.py 用于特定业务逻辑)
# ============================================================

async def match_package_with_ai(user_input: str) -> Optional[Dict[str, Any]]:
    """根据用户描述，使用PROMPT_A进行AI语义分析，匹配最合适任务包"""
    global PROMPT_A

    # 如果PROMPT_A未加载，尝试加载
    if not PROMPT_A:
        PROMPT_A = load_prompt("prompt_A.md")

    if not PROMPT_A or not user_input:
        return None

    try:
        # 使用PROMPT_A进行语义分析
        result = await call_deepseek(
            PROMPT_A,
            json.dumps({"raw_input": user_input}, ensure_ascii=False),
            temperature=0.3
        )

        # 解析返回结果
        if result and isinstance(result, dict):
            match_info = result.get("match") or {}
            package_code = match_info.get("package_code", "")

            if package_code and len(package_code) <= 2:
                # 格式化为两位数字
                package_code = str(package_code).zfill(2)

                # 从任务包清单中查找匹配的任务包名称
                package_name = match_info.get("package_name", "")
                confidence = match_info.get("confidence", 0)

                return {
                    "package_code": package_code,
                    "package_name": package_name,
                    "confidence": confidence,
                    "behavior_tags": result.get("behavior_tags", []),
                    "signal": result.get("signal", {}),
                    "full_result": result
                }

        return None
    except Exception as e:
        print(f"[match_package_with_ai] 语义分析失败: {e}")
        return None


# ============================================================
# API Endpoints (完全对齐 PRD v2.1)
# ============================================================

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "version": "2.1.0", "timestamp": datetime.now().isoformat()}


@app.get("/api/packages")
async def get_packages():
    """GET /api/packages - 获取所有任务包列表（PRD 8.0）"""
    # 优先从清单文件读取
    if os.path.exists(PACKAGES_LIST_PATH):
        with open(PACKAGES_LIST_PATH, 'r', encoding='utf-8') as f:
            packages = json.load(f)
            return {"packages": packages, "total": len(packages)}

    # fallback：扫描目录
    kb_path = Path(PACKAGES_PATH)
    packages = []
    if kb_path.exists():
        for md_file in kb_path.glob("*.md"):
            code = extract_package_code(md_file.stem)
            name = extract_field(
                open(md_file, 'r', encoding='utf-8').read(),
                r"包名称[:：]\s*(.+?)(?:\n|$)", 1
            )
            if code and name:
                packages.append({"code": code, "title": name})
    return {"packages": packages, "total": len(packages)}


# ---- API 1: POST /api/scenarios/recognize ----
@app.post("/api/scenarios/recognize")
async def recognize_scenario(request: RecognizeRequest):
    """
    PRD API 1: 识别用户输入，匹配任务包
    Request: { user_id, text, session_context? }
    Response: { scenario_id?, goal, package_code, package_name, confidence, signal, clarification_needed, ... }
    """
    user_message = json.dumps({
        "raw_input": request.text,
        "session_context": request.session_context or {},
        "timestamp": request.timestamp or datetime.now().isoformat()
    }, ensure_ascii=False)

    # 高频行为类输入直接用fallback（绕过DeepSeek的随机性）
    high_freq_behaviors = ["打人", "攻击行为", "动手打人", "打人行为", "自伤", "自我伤害", "发脾气", "撞头", "情绪崩溃", "崩溃哭闹"]
    if request.text.strip() in high_freq_behaviors or any(k in request.text for k in high_freq_behaviors):
        recognition = fallback_recognize(request.text) or {}
    else:
        try:
            recognition = await call_deepseek(PROMPT_C, user_message, temperature=0.3)
        except Exception:
            recognition = fallback_recognize(request.text) or {}

        # call_deepseek可能返回None或非dict（异常被吞但返回值为None/list）
        if not isinstance(recognition, dict):
            recognition = fallback_recognize(request.text) or {}
        elif recognition is None:
            recognition = fallback_recognize(request.text) or {}

        # 如果DeepSeek返回低置信度或无package_code，降级到关键词匹配兜底
        try:
            routing_info = recognition.get("routing", {})
        except Exception as e:
            import traceback; traceback.print_exc()
            routing_info = {}
        suggested_pkg = routing_info.get("suggested_package_code")
        confidence = float(recognition.get("confidence", 0.0))
        if not suggested_pkg or confidence < 0.8:
            fallback_result = fallback_recognize(request.text) or {"match": {}}
            if not suggested_pkg and (fallback_result.get("match") or {}).get("package_code"):
                recognition.setdefault("routing", {})["suggested_package_code"] = fallback_result["match"]["package_code"]
                recognition.setdefault("routing", {})["suggested_package_name"] = fallback_result["match"]["package_name"]
                recognition["confidence"] = max(confidence, 0.6)

    # 兼容两种格式：PRD格式(match.*) 和 Prompt C格式(routing.suggested_*)
    routing_info = recognition.get("routing", {})
    match_info = recognition.get("match") or {}

    package_code = routing_info.get("suggested_package_code") or match_info.get("package_code", "")
    package_name = routing_info.get("suggested_package_name") or match_info.get("package_name", "")
    confidence = routing_info.get("confidence") or match_info.get("confidence") or float(recognition.get("confidence", 0.0))
    signal_type = recognition.get("signal", {}).get("type", "none")
    signal_detail = recognition.get("signal", {}).get("detail", "")
    behavior_tags = recognition.get("behavior_tags", [])
    goal = match_info.get("goal", "")
    # 如果LLM没有返回goal，从识别到的包的主目标字段填充
    if not goal and package_code:
        pkg_data = load_package_markdown(package_code)
        if pkg_data:
            # 优先用主目标，其次target（兼容旧格式）
            goal = pkg_data.get("basic_info", {}).get("主目标") or pkg_data.get("basic_info", {}).get("target", "")
    clarification_needed = recognition.get("routing", {}).get("clarification_needed", signal_type != "none" or confidence < 0.8 or not package_code)

    # 保存到 situations 表（旧表，用于数据追溯）
    save_situation({
        "raw_input": request.text,
        "matched_package_code": package_code,
        "matched_package_name": package_name,
        "confidence": confidence,
        "behavior_tags": behavior_tags,
        "signal_type": signal_type,
        "signal_detail": signal_detail,
        "clarification_needed": recognition.get("clarification_needed", [])
    })

    # 直接创建 scenario（修复：recognize 时就创建，不要等 generate）
    try:
        # 尝试加载任务包获取 days_data
        days_data = {}
        pkg_data = load_package_markdown(package_code) if package_code else None
        if pkg_data:
            days_data = pkg_data.get("days_data", {})

        sc_id = create_scenario(
            user_id=request.user_id or "anonymous",
            package_code=package_code,
            package_name=package_name,
            raw_input=request.text,
            goal=goal,
            confidence=confidence,
            behavior_tags=behavior_tags,
            signal_type=signal_type,
            signal_detail=signal_detail,
            days_data=days_data
        )
        scenario_id = sc_id
        print(f"[Scenario] 创建成功: {sc_id[:8]}... -> {package_name}")
    except Exception as e:
        scenario_id = None
        print(f"[Scenario] 创建失败: {e}")

    # 记录用户输入日志（本地数据库）
    try:
        create_user_input_log(
            user_id=request.user_id or "anonymous",
            raw_input=request.text,
            intent_type="situation_input",
            analysis_duration_ms=0,  # recognize 不测时
            matched_package_code=package_code,
            matched_package_name=package_name,
            confidence=confidence,
            recognition_result=recognition,
            scenario_id=scenario_id
        )
        print(f"[用户日志] 本地记录成功: {request.text[:20]}... -> {package_name}")
    except Exception as e:
        print(f"[用户日志] 本地记录失败: {e}")

    # 同步到飞书（静默，不打印日志）
    sync_user_input_log_to_feishu({
        "user_id": request.user_id or "anonymous",
        "raw_input": request.text,
        "input_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "analysis_duration_ms": 0,
        "matched_package_code": package_code,
        "matched_package_name": package_name,
        "confidence": confidence,
        "intent_type": "situation_input",
        "scenario_id": None
    })

    response = {
        "code": 0,
        "message": "ok",
        "data": {
            "scenario_id": scenario_id,  # 现在会返回真实的 scenario_id
            "goal": goal,
            "package_code": package_code,
            "package_name": package_name,
            "confidence": confidence,
            "signal": {
                "type": signal_type,
                "detail": signal_detail
            },
            "behavior_tags": behavior_tags,
            "clarification_needed": clarification_needed,
        }
    }
    return response


# ---- API 2: POST /api/task-packages/generate (with MOCK_MODE support) ----
@app.post("/api/task-packages/generate")
async def generate_task_package(request: TaskPackageGenerateRequest):
    """
    B-2: 生成7天任务包（支持MOCK_MODE）
    MOCK_MODE=true时返回L1 Mock数据

    修复：如果传入了 scenario_id，从数据库获取已匹配的信息
    """
    scenario_id = request.scenario_id or str(uuid.uuid4())

    # 修复：从 scenario 获取已匹配的 package_code（不再重新AI匹配）
    package_code_from_db = None
    package_name_from_db = None
    goal_from_db = None

    if scenario_id and scenario_id != str(uuid.uuid4):
        existing_scenario = get_scenario(scenario_id)
        if existing_scenario:
            package_code_from_db = existing_scenario.get("package_code", "")
            package_name_from_db = existing_scenario.get("package_name", "")
            goal_from_db = existing_scenario.get("goal", "")

    # B-8: MOCK_MODE检查（使用services模块）
    if is_mock_mode():
        # 使用Mock数据
        mock_data = get_mock_package(request.package_code)
        if not mock_data:
            # 尝试按标签匹配
            mock_data = get_mock_packages_by_tag(request.package_name)
        if not mock_data:
            # 使用默认兜底
            mock_data = get_fallback_package()
        
        if mock_data:
            # 创建scenario记录
            sc_id = create_scenario(
                user_id=request.user_id,
                package_code=request.package_code,
                package_name=request.package_name or mock_data.get("scenario_title", "Mock方案"),
                raw_input=request.raw_input or "",
                goal=json.dumps(mock_data.get("core_goal", {}), ensure_ascii=False),
                confidence=mock_data.get("confidence", 0.8),
                behavior_tags=[],
                signal_type="none",
                signal_detail="",
                days_data=mock_data.get("days_data", {})
            )
            
            # 创建tasks
            create_tasks_for_scenario(sc_id, request.package_code, mock_data.get("days_data", {}))
            
            # 初始化每日状态
            days_count = len(mock_data.get("days_data", {}).get("days", []))
            init_daily_status(sc_id, days_count)
            
            # 生成鼓励文
            generate_encouragement_texts(sc_id, mock_data.get("scenario_title", ""))
            
            return {
                "code": 0,
                "message": "ok",
                "data": {
                    "scenario_id": sc_id,
                    "package_code": request.package_code,
                    "package_name": mock_data.get("scenario_title", request.package_name),
                    "days": mock_data.get("days_data", {}).get("days", []),
                    "encouragement_texts": [],
                    "context": [],
                    "precautions": [],
                    "mock_mode": True
                }
            }
    
    # 正常流程：加载真实任务包
    # 优先使用数据库中已匹配的信息（从 recognize API 创建的 scenario）
    _request_pkg = request.package_code.strip() if request.package_code else ""
    package_code = package_code_from_db or _request_pkg
    package_name = package_name_from_db or request.package_name
    goal = goal_from_db or ""
    package_data = None
    matched = None

    print(f"[Generate] scenario_id={scenario_id}, package_code={package_code!r}, package_code_from_db={package_code_from_db!r}")

    if package_code and package_code != "default":
        package_data = load_package_markdown(package_code)
        print(f"[Generate] load_package_markdown({package_code!r}) = {package_data is not None}")

    # 如果数据库中没有 package_code 或无法加载，则用AI匹配
    if not package_data:
        raw_input = request.raw_input or ""
        behavior_tags = request.selected_tags or []
        combined_input = f"{' '.join(behavior_tags)} {raw_input}".strip()

        try:
            matched = await match_package_with_ai(combined_input)
            if matched:
                package_data = load_package_markdown(matched.get("package_code", ""))
                package_name = matched.get("package_name", request.package_name or "AI匹配方案")
            else:
                package_name = request.package_name or "通用方案"
        except Exception:
            package_name = request.package_name or "通用方案"

        if not package_data:
            raise HTTPException(status_code=404, detail={
                "code": 4001,
                "message": f"无法为输入匹配任务包，请尝试选择具体标签"
            })
    
    days_data = package_data.get("days_data", {"days": []})
    package_name = package_data.get("package_name", request.package_name)

    raw_input = request.raw_input or ""
    goal = ""

    # 使用 match_package_with_ai 返回的 full_result（避免重复调用AI）
    if matched and matched.get("full_result"):
        recognition_result = {}
        goal = recognition_result.get("goal", "") or recognition_result.get("match", {}).get("package_name", "")
    else:
        recognition_result = {}

    # 确定有效的 package_code（用于后续所有操作）
    effective_package_code = matched.get("package_code") if matched else package_code

    # 如果 scenario_id 来自已存在的 scenario（recognize 创建的），不重复创建
    # 否则创建新的 scenario
    existing_scenario = get_scenario(scenario_id) if scenario_id else None

    if existing_scenario:
        sc_id = existing_scenario["id"]
        print(f"[Scenario] 使用已存在的 scenario: {sc_id[:8]}...")
    else:
        sc_id = create_scenario(
            user_id=request.user_id or "anonymous",
            package_code=effective_package_code or "",
            package_name=package_name,
            raw_input=raw_input,
            goal=goal,
            confidence=0.9,
            behavior_tags=[],
            signal_type="none",
            signal_detail="",
            days_data=days_data
        )
        print(f"[Scenario] 创建新 scenario: {sc_id[:8]}...")

    # 记录用户输入日志（本地数据库）
    try:
        analysis_duration_ms = matched.get("analysis_duration_ms", 0) if matched else 0
        confidence = matched.get("confidence", 0.9) if matched else 0.9

        create_user_input_log(
            user_id=request.user_id or "anonymous",
            raw_input=raw_input,
            intent_type="task_package_generate",
            analysis_duration_ms=analysis_duration_ms,
            matched_package_code=effective_package_code or "",
            matched_package_name=package_name,
            confidence=confidence,
            recognition_result=recognition_result,
            scenario_id=sc_id
        )
        print(f"[用户日志] 本地记录成功，耗时{analysis_duration_ms}ms，匹配包: {package_name}")
    except Exception as e:
        print(f"[用户日志] 本地记录失败: {e}")

    # 同步到飞书（静默，不打印日志）
    sync_user_input_log_to_feishu({
        "user_id": request.user_id or "anonymous",
        "raw_input": raw_input,
        "input_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "intent_type": "task_package_generate",
        "analysis_duration_ms": analysis_duration_ms,
        "matched_package_code": effective_package_code or request.package_code or "",
        "matched_package_name": package_name,
        "confidence": 0.9,
        "scenario_id": sc_id
    })
    
    # 创建tasks表记录（使用AI匹配到的有效package_code）
    create_tasks_for_scenario(sc_id, effective_package_code or request.package_code or "", days_data)
    
    # 初始化每日状态
    days_count = len(days_data.get("days", []))
    init_daily_status(sc_id, days_count)
    
    # 批量生成鼓励文
    generate_encouragement_texts(sc_id, package_name)
    
    # 组装返回
    days_response = []
    for day_obj in days_data.get("days", []):
        day_num = day_obj["day"]
        all_steps = day_obj.get("steps", [])
        obs_prompt = day_obj.get("goal", {}).get("success_criteria", {}).get("observation_prompt", "")
        task_id = f"{effective_package_code or request.package_code or 'XX'}_D{day_num}_T1"
        tasks_in_day = [{
            "task_id": task_id,
            "name": day_obj.get("theme", f"Day {day_num}"),
            "steps": all_steps,
            "duration_minutes": day_obj.get("duration_min", 5),
            "status": "pending",
            "has_feedback": False,
            "observation_point": obs_prompt,
        }]
        
        days_response.append({
            "day_index": day_num,
            "date": (date.today() + timedelta(days=day_num - 1)).isoformat(),
            "theme": day_obj.get("theme", ""),
            "goal": day_obj.get("goal", {}).get("description", ""),
            "situation": day_obj.get("situation", ""),
            "status": "pending",
            "tasks": tasks_in_day,
        })
    
    # 收集encouragement_texts
    encouragements = []
    emojis = ["very_dissatisfied", "dissatisfied", "satisfied"]
    for day in range(1, min(days_count, 8)):
        for emoji in emojis:
            text = get_encouragement_for_day(sc_id, day, emoji)
            if text:
                encouragements.append({"day": day, "emoji": emoji, "text": text})
    
    # 收集context和precautions
    context_parts = []
    if package_data:
        secs = package_data.get("sections", {})
        if secs.get("theory"):
            context_parts.append({"type": "理论基础", "content": secs["theory"]})
        if secs.get("context_analysis"):
            context_parts.append({"type": "情境解读", "content": secs["context_analysis"]})
    
    precautions = []
    if package_data:
        secs = package_data.get("sections", {})
        if secs.get("preconditions"):
            precautions.append({"title": "前置能力检查", "content": secs["preconditions"], "level": "warning"})
        if secs.get("contraindications"):
            precautions.append({"title": "不适用条件", "content": secs["contraindications"], "level": "danger"})
        if secs.get("prompt_levels"):
            precautions.append({"title": "提示等级定义", "content": secs["prompt_levels"], "level": "info"})
        if secs.get("referral"):
            precautions.append({"title": "转介规则", "content": secs["referral"], "level": "danger"})
        if secs.get("level_rules"):
            precautions.append({"title": "升级/降级规则", "content": secs["level_rules"], "level": "warning"})
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "scenario_id": sc_id,
            "package_code": effective_package_code or request.package_code or "",
            "package_name": package_name,
            "days": days_response,
            "encouragement_texts": encouragements,
            "context": context_parts,
            "precautions": precautions,
            "mock_mode": False
        }
    }


# ---- API 3: GET /api/tasks/daily ----
@app.get("/api/tasks/daily")
async def get_daily_tasks(
    scenario_id: str = Query(..., description="情境ID"),
    day: int = Query(..., ge=1, le=14, description="天数")
):
    """
    PRD API 3: 获取每日任务列表
    Response: { day_index, date, status, tasks[] }
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})

    tasks = get_tasks_for_day(scenario_id, day)
    daily_status = get_daily_status(scenario_id, day)

    # 从 days_data 中获取日期
    days_data = json.loads(scenario.get("days_data", "{}"))
    target_day = None
    for d in days_data.get("days", []):
        if d["day"] == day:
            target_day = d
            break

    tasks_response = []
    obs_prompt = (target_day.get("goal", {}).get("success_criteria", {}).get("observation_prompt", "") if target_day else "")
    for t in tasks:
        steps = json.loads(t.get("steps", "[]"))
        tasks_response.append({
            "task_id": t["id"],
            "name": t["name"],
            "steps": steps,
            "duration_minutes": t.get("duration_minutes", 10),
            "status": t["status"],
            "has_feedback": bool(t.get("has_feedback")),
            "observation_point": obs_prompt,  # 动态观察提示
        })

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "day_index": day,
            "date": daily_status.get("date", (date.today() + timedelta(days=day - 1)).isoformat()) if daily_status else "",
            "status": daily_status.get("status", "pending") if daily_status else "pending",
            "tasks": tasks_response,
        }
    }


# ---- API 4: POST /api/feedback ----
@app.post("/api/feedback")
async def submit_feedback(request: FeedbackSubmitRequest):
    """
    PRD API 4: 提交训练反馈
    Request: { scenario_id, task_id, day, emoji, text, training_record? }
    Response: { feedback_id, analysis, encouragement_text, saved }
    """
    scenario = get_scenario(request.scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})

    # Mock模式下task不在tasks表中，跳过强校验
    task = None  # get_task(request.task_id)

    # 分析反馈（Prompt B），失败则降级
    training_record = request.training_record or {}
    user_message = json.dumps({
        "package_code": scenario["package_code"],
        "package_name": scenario["package_name"],
        "day_number": request.day,
        "parent_feedback": {"emoji": request.emoji, "text": request.text},
        "training_record": training_record
    }, ensure_ascii=False)

    try:
        analysis_result = await call_deepseek(PROMPT_B, user_message, temperature=0.3)
    except Exception:
        analysis_result = fallback_analyze_feedback(request.emoji, request.text, training_record)

    # 保存反馈
    feedback_id = create_feedback(
        scenario_id=request.scenario_id,
        task_id=request.task_id,
        day=request.day,
        emoji=request.emoji,
        text=request.text,
        training_record=training_record,
        analysis_result=analysis_result
    )

    # 获取鼓励文
    encouragement = get_encouragement_for_day(request.scenario_id, request.day, request.emoji)
    if not encouragement:
        encouragement = get_fallback_encouragement(request.emoji)

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "feedback_id": feedback_id,
            "analysis": analysis_result,
            "encouragement_text": encouragement,
            "saved": True,
        }
    }


def fallback_analyze_feedback(emoji: str, text: str, training_record: Dict) -> Dict[str, Any]:
    emoji_map = {"very_dissatisfied": "需调整", "dissatisfied": "继续努力", "satisfied": "进展良好", "very_satisfied": "非常棒"}
    return {
        "sentiment": emoji_map.get(emoji, "unknown"),
        "summary": text or "家长反馈已记录",
        "adjustment_suggestions": ["继续当前计划"] if emoji in ("satisfied", "very_satisfied") else ["降低难度", "增加强化"],
        "escalation_needed": emoji == "very_dissatisfied"
    }


def get_fallback_encouragement(emoji: str, day: int = 1) -> str:
    """获取兜底鼓励文案（使用 services.mock_loader）"""
    return get_mock_encouragement(emoji, day)


# ---- API 5: DELETE /api/scenarios/{scenario_id} ----
@app.delete("/api/scenarios/{scenario_id}")
async def delete_scenario(scenario_id: str):
    """
    PRD API 5: 删除情境（软删除）
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})
    if scenario.get("status") == "completed":
        raise HTTPException(status_code=400, detail={"code": 5003, "message": "scenario_completed_cannot_delete"})

    success = update_scenario_status(scenario_id, "deleted")
    if not success:
        return JSONResponse(
            status_code=500,
            content={"code": 5002, "message": "delete_failed - scenario not found"}
        )
    return {
        "code": 0,
        "message": "ok",
        "data": {"deleted": True}
    }


# ---- API 6: GET /api/scenarios/{scenario_id}/interpret ----
@app.get("/api/scenarios/{scenario_id}/interpret")
async def get_scenario_interpret(scenario_id: str):
    """
    PRD API 6: 获取情境解读（知识库内容）
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})

    package_data = load_package_markdown(scenario["package_code"])
    if not package_data:
        raise HTTPException(status_code=404, detail={"code": 4001, "message": "package_not_found"})

    days_data = package_data.get("days_data", {})
    first_day = days_data.get("days", [{}])[0] if days_data.get("days") else {}

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "scenario_name": scenario["package_name"],
            "goal": scenario["goal"] or first_day.get("goal", {}).get("description", ""),
            "possible_causes": [
                "行为功能分析确定",
                "感觉调节困难",
                "沟通意图表达受阻"
            ],
            "research_support": {
                "title": "ALSO原则在ASD家庭干预中的应用",
                "description": "基于ABA原理的家庭干预方法"
            },
            "home_suggestions": [
                "保持一致性",
                "及时强化正确行为",
                "记录进展数据"
            ],
            "stop_conditions": [
                "自伤行为持续出现或加重",
                "攻击行为造成伤害",
                "疑似疼痛"
            ],
            "references": [
                "ALSO-LIFE金手册",
                "PECS图片交换沟通系统"
            ],
            "prerequisites": package_data.get("basic_info", {}).get("prerequisites", []),
        }
    }


# ---- API 7: GET /api/tasks/{task_id}/precautions ----
@app.get("/api/tasks/{task_id}/precautions")
async def get_task_precautions(task_id: str):
    """
    PRD API 7: 获取任务注意事项
    """
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail={"code": 5002, "message": "task_not_found"})

    package_data = load_package_markdown(task["package_code"])
    days_data = package_data.get("days_data", {}) if package_data else {}
    target_day = None
    for d in days_data.get("days", []):
        if d["day"] == task["day"]:
            target_day = d
            break

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "task_id": task_id,
            "name": task["name"],
            "environment_prep": [
                "提前准备好强化物（孩子喜欢的零食/玩具）",
                "选择安静、少干扰的环境",
                "确保孩子情绪稳定、不饥饿/不疲倦"
            ],
            "parent_mindset": [
                "保持积极情绪，不带压力",
                "每一次尝试都值得肯定",
                "遇到抗拒时先暂停，不强制"
            ],
            "stop_conditions": [
                "孩子出现严重情绪崩溃（哭闹超过5分钟无法安抚）",
                "出现自伤或攻击行为",
                "孩子明显表示抗拒（语言或行为）"
            ],
            "faq": [
                {"q": "孩子不配合怎么办？", "a": "降低难度或换一个场景试试"},
                {"q": "连续失败怎么办？", "a": "回退到更容易的步骤，加强辅助"},
                {"q": "可以跳过某天吗？", "a": "建议按顺序完成，确保技能巩固"}
            ],
            "troubleshooting": target_day.get("troubleshooting", []) if target_day else [],
        }
    }


# ============================================================
# B-3: GET /api/scenarios（情境列表）
# ============================================================
@app.get("/api/scenarios")
async def get_scenarios(
    status: Optional[str] = Query(None, description="状态过滤：active/completed/abandoned"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    B-3: 获取情境列表
    支持状态过滤和分页
    """
    with get_db_cursor() as cursor:
        query = "SELECT * FROM scenarios WHERE status != 'deleted'"
        params = []
        if status:
            query += " AND status = ?"
            params.append(status)
        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        scenarios = []
        for row in rows:
            sc = dict(row)
            sc["days_data"] = json.loads(sc.get("days_data", "{}")) if sc.get("days_data") else {}
            sc["behavior_tags"] = json.loads(sc.get("behavior_tags", "[]")) if sc.get("behavior_tags") else []
            # 计算进度
            days_list = sc["days_data"].get("days", [])
            total_days = len(days_list) if days_list else (sc.get("total_days") or 14)
            current_day = sc.get("current_day", 1) or 1
            sc["progress_percent"] = round(current_day * 100 / total_days) if total_days > 0 else 0
            # 前端期望字段对齐
            sc["scenario_id"] = sc["id"]  # 前端用 scenario_id
            # 从 package_name 提取 emoji 和标题（如 "📋 情绪行为管理"）
            pkg_name = sc.get("package_name", "")
            import re
            emoji_match = re.search(r'[\U0001F300-\U0001F9FF]', pkg_name)
            sc["scenario_emoji"] = emoji_match.group() if emoji_match else "📋"
            sc["scenario_title"] = re.sub(r'^任务包_\d+_', '', pkg_name).strip() if pkg_name else "未命名情境"
            sc["total_days"] = total_days
            # 添加 goal 字段（从 days_data 或 scenarios 表的 goal 字段）
            if days_list and days_list[0].get("goal"):
                first_day = days_list[0]
                goal_desc = first_day.get("goal", {}).get("description", "") if isinstance(first_day.get("goal"), dict) else (first_day.get("goal", "") or "")
                sc["goal"] = {"title": goal_desc, "content": goal_desc}
            else:
                raw_goal = sc.get("goal", "")
                if raw_goal:
                    try:
                        goal_obj = json.loads(raw_goal)
                        sc["goal"] = {
                            "title": goal_obj.get("description", "") or goal_obj.get("title", ""),
                            "content": goal_obj.get("description", "") or goal_obj.get("content", "")
                        }
                    except:
                        sc["goal"] = {"title": raw_goal, "content": raw_goal}
                else:
                    sc["goal"] = {"title": "", "content": ""}
            # 添加 last_feedback（最新训练反馈）
            cursor.execute("""
                SELECT emoji, text, created_at FROM feedback
                WHERE scenario_id = ?
                ORDER BY created_at DESC LIMIT 1
            """, [sc["id"]])
            last_fb = cursor.fetchone()
            if last_fb:
                sc["last_feedback"] = {
                    "emoji": last_fb["emoji"],
                    "text": last_fb["text"] or "已训练",
                    "created_at": last_fb["created_at"]
                }
            else:
                sc["last_feedback"] = None

            scenarios.append(sc)
        
        # 获取总数
        cursor.execute("SELECT COUNT(*) as cnt FROM scenarios WHERE status != 'deleted'", [])
        total = cursor.fetchone()["cnt"]
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "scenarios": scenarios,
            "total": total,
            "limit": limit,
            "offset": offset
        }
    }


# ============================================================
# B-4: GET /api/scenarios/{id}（情境详情）
# ============================================================
@app.get("/api/scenarios/{scenario_id}")
async def get_scenario_detail(scenario_id: str):
    """
    B-4: 获取情境详情
    返回概览数据 + 最近3条反馈记录
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})
    
    # 解析JSON字段
    scenario["days_data"] = json.loads(scenario.get("days_data", "{}")) if scenario.get("days_data") else {}
    scenario["behavior_tags"] = json.loads(scenario.get("behavior_tags", "[]")) if scenario.get("behavior_tags") else []
    
    # 计算进度
    days_list = scenario.get("days_data", {}).get("days", [])
    total_days = len(days_list) if days_list else (scenario.get("total_days") or 14)
    current_day = scenario.get("current_day", 1) or 1
    scenario["progress_percent"] = round(current_day * 100 / total_days) if total_days > 0 else 0
    # 前端期望字段对齐
    scenario["scenario_id"] = scenario["id"]
    pkg_name = scenario.get("package_name", "")
    import re
    emoji_match = re.search(r'[\U0001F300-\U0001F9FF]', pkg_name)
    scenario["scenario_emoji"] = emoji_match.group() if emoji_match else "📋"
    scenario["scenario_title"] = re.sub(r'^任务包_\d+_', '', pkg_name).strip() if pkg_name else "未命名情境"
    scenario["total_days"] = total_days
    # goal 对象化：前端期望 goal.title + goal.content
    if days_list:
        first_day = days_list[0]
        scenario["goal"] = {
            "title": first_day.get("goal", {}).get("description", "") if isinstance(first_day.get("goal"), dict) else (first_day.get("goal", "") or ""),
            "content": first_day.get("goal", {}).get("description", "") if isinstance(first_day.get("goal"), dict) else (first_day.get("goal", "") or "")
        }
    else:
        # Fallback: 使用 scenarios 表中存储的 goal 字段（来自任务包的主目标）
        raw_goal = scenario.get("goal", "")
        if raw_goal:
            try:
                goal_obj = json.loads(raw_goal)
                scenario["goal"] = {
                    "title": goal_obj.get("description", "") or goal_obj.get("title", ""),
                    "content": goal_obj.get("description", "") or goal_obj.get("content", "")
                }
            except:
                scenario["goal"] = {"title": raw_goal, "content": raw_goal}
        else:
            scenario["goal"] = {"title": "", "content": ""}

    # 获取累计训练次数（从feedback表COUNT，而不是daily_task_status）
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT COUNT(*) as cnt FROM feedback
            WHERE scenario_id = ?
        """, (scenario_id,))
        total_train = cursor.fetchone()["cnt"]

    # 计算连续训练天数（从feedback表按day分组，统计连续自然日）
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT day FROM feedback
            WHERE scenario_id = ?
            ORDER BY day DESC
        """, (scenario_id,))
        days = [row["day"] for row in cursor.fetchall()]
        consecutive_days = 0
        expected_day = None
        for day in days:
            if expected_day is None:
                consecutive_days = 1
                expected_day = day - 1
            elif day == expected_day:
                consecutive_days += 1
                expected_day = day - 1
            else:
                break
    recent_feedback = get_feedback_history(scenario_id, limit=3)
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "scenario": scenario,
            "total_train_count": total_train,
            "consecutive_days": consecutive_days,
            "recent_feedback": recent_feedback
        }
    }


# ============================================================
# B-5: GET /api/scenarios/{id}/days（天列表）
# ============================================================
@app.get("/api/scenarios/{scenario_id}/days")
async def get_scenario_days(scenario_id: str):
    """
    B-5-0: 获取所有天计划（天列表）
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})

    days_data = json.loads(scenario.get("days_data", "{}")) if scenario.get("days_data") else {}
    days_list = days_data.get("days", [])

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "days": days_list,
            "total_days": len(days_list)
        }
    }


# ============================================================
# B-5: GET /api/scenarios/{id}/days/{day}（每日训练数据）
# ============================================================
@app.get("/api/scenarios/{scenario_id}/days/{day}")
async def get_daily_training_data(scenario_id: str, day: int):
    """
    B-5: 获取每日训练数据
    返回当天goal/tip/steps
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})
    
    days_data = json.loads(scenario.get("days_data", "{}")) if scenario.get("days_data") else {}
    target_day = None
    for d in days_data.get("days", []):
        if d["day"] == day:
            target_day = d
            break
    
    if not target_day:
        raise HTTPException(status_code=404, detail={"code": 5002, "message": f"day {day} not found in scenario"})
    
    # 获取当天任务
    tasks = get_tasks_for_day(scenario_id, day)
    tasks_response = []
    for t in tasks:
        steps = json.loads(t.get("steps", "[]")) if t.get("steps") else []
        tasks_response.append({
            "task_id": t["id"],
            "name": t["name"],
            "steps": steps,
            "duration_minutes": t.get("duration_minutes", 10),
            "status": t["status"],
            "has_feedback": bool(t.get("has_feedback"))
        })
    
    # 获取当天状态
    daily_status = get_daily_status(scenario_id, day)
    
    # 处理goal字段（可能是字符串或dict）
    goal_field = target_day.get("goal", "")
    if isinstance(goal_field, dict):
        goal = goal_field.get("description", "")
        observe_prompt = goal_field.get("success_criteria", {}).get("observation_prompt", "") if isinstance(goal_field.get("success_criteria"), dict) else ""
    else:
        goal = goal_field or ""
        observe_prompt = ""

    # 去掉 "今日练习后记录：" 前缀，保持简洁
    if observe_prompt and "今日练习后记录：" in observe_prompt:
        observe_prompt = observe_prompt.replace("今日练习后记录：", "")

    # 如果没有找到，从 steps 中提取 success_criteria 作为观察提示
    if not observe_prompt:
        for step in target_day.get("steps", []):
            sc = step.get("success_criteria", "")
            if sc and sc != "正确完成":
                observe_prompt = f"记录: {sc}"
                break

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "day_index": day,
            "date": daily_status.get("date", "") if daily_status else "",
            "status": daily_status.get("status", "pending") if daily_status else "pending",
            "theme": target_day.get("theme", ""),
            "day_theme": target_day.get("theme", ""),
            "goal": goal,
            "today_goal": goal,
            "today_tip": target_day.get("reinforcement", "做得好！继续加油！"),
            "tip": target_day.get("reinforcement", "做得好！继续加油！"),
            "observe_prompt": observe_prompt,
            "observation_point": observe_prompt,
            "steps": target_day.get("steps", []),
            "tasks": tasks_response
        }
    }


# Layer 3 分析功能已迁移到 services.ai_service

# B-6: POST /api/scenarios/{id}/feedback（反馈提交）
class FeedbackV2Request(BaseModel):
    scenario_id: str
    task_id: str
    day: int
    emoji: str = Field(..., min_length=1)
    text: str = ""
    training_record: Optional[Dict[str, Any]] = None


@app.post("/api/scenarios/{scenario_id}/feedback")
async def submit_feedback_v2(scenario_id: str, request: FeedbackSubmitRequest):
    """
    B-6: 提交训练反馈（新版，包含Layer 3分析）
    根据是否有文字备注选择分析路径：
    - 有文字备注 → AI完整分析（B-10）
    - 无文字备注 → 表情判断树（B-9）
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})
    
    # Mock模式下task不在tasks表中，跳过强校验
    task = None  # get_task(request.task_id)
    
    # 获取历史反馈
    history_records = get_feedback_history(scenario_id, limit=2)
    
    # Layer 3分析
    has_text_note = request.text and len(request.text.strip()) > 0
    if has_text_note:
        # B-10: AI完整分析
        analysis_result = await ai_full_analyze(
            current_emoji=request.emoji,
            feedback_text=request.text,
            current_day=request.day,
            scenario_id=scenario_id,
            history_records=history_records
        )
    else:
        # B-9: 表情判断树
        last_emoji = history_records[0].get("emoji") if history_records else None
        analysis_result = rule_based_analyze(request.emoji, last_emoji)
    
    # B-11 & B-12: Signal后台动作 + 边界规则
    # days_data在数据库中是JSON字符串，需先解析
    import json as _json
    days_data_str = scenario.get("days_data", "{}")
    days_data = _json.loads(days_data_str) if isinstance(days_data_str, str) else (days_data_str or {})
    max_day = len(days_data.get("days", [])) or 14
    action_result = apply_signal_action(
        signal=analysis_result.get("signal", "stable"),
        action=analysis_result.get("action", "maintain"),
        current_day=request.day,
        max_day=max_day
    )
    
    # 合并分析结果
    analysis_result.update(action_result)
    
    # 保存反馈
    training_record = request.training_record or {}
    feedback_id = create_feedback(
        scenario_id=scenario_id,
        task_id=request.task_id,
        day=request.day,
        emoji=request.emoji,
        text=request.text,
        training_record=training_record,
        analysis_result=analysis_result
    )
    
    # 更新scenario当前天数
    if action_result.get("next_day"):
        update_scenario_current_day(scenario_id, action_result["next_day"])
    
    # 获取鼓励文（US-006: 优先AI生成，兜底数据库/规则）
    ai_encouragement = generate_ai_encouragement({
        "emoji": request.emoji,
        "day": request.day,
        "training_record": training_record,
        "parent_text": request.text,
        "scenario_id": scenario_id,
    })
    # 数据库预置的鼓励文（如果存在，且AI返回的偏短时优先用数据库的）
    db_encouragement = get_encouragement_for_day(scenario_id, request.day, request.emoji)
    # 策略：AI生成 > 数据库预置 > 规则兜底
    if ai_encouragement and len(ai_encouragement) >= 5:
        encouragement = ai_encouragement
    elif db_encouragement:
        encouragement = db_encouragement
    else:
        encouragement = get_fallback_encouragement(request.emoji)
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "feedback_id": feedback_id,
            "analysis": analysis_result,
            "encouragement_text": encouragement,
            "saved": True,
            "mode": analysis_result.get("mode", "rule")
        }
    }


# B-7: GET /api/scenarios/{id}/history（训练历史）
@app.get("/api/scenarios/{scenario_id}/history")
async def get_training_history(
    scenario_id: str,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    B-7: 获取训练历史
    按月分组统计
    """
    scenario = get_scenario(scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail={"code": 5001, "message": "scenario_not_found"})
    
    history = get_feedback_history(scenario_id, limit=limit)
    
    # 统计数据
    stats = {
        "total": len(history),
        "positive_count": 0,
        "neutral_count": 0,
        "negative_count": 0
    }
    
    for record in history:
        record["training_record"] = json.loads(record.get("training_record", "{}")) if record.get("training_record") else {}
        record["analysis_result"] = json.loads(record.get("analysis_result", "{}")) if record.get("analysis_result") else {}
        
        emoji_signal = map_emoji_to_signal(record.get("emoji", ""))
        if emoji_signal == "positive":
            stats["positive_count"] += 1
        elif emoji_signal == "neutral":
            stats["neutral_count"] += 1
        else:
            stats["negative_count"] += 1
    
    # 按月分组
    monthly_data = {}
    for record in history:
        created_at = record.get("created_at", "")
        if created_at:
            month_key = created_at[:7]  # YYYY-MM
            if month_key not in monthly_data:
                monthly_data[month_key] = {
                    "month": month_key,
                    "records": [],
                    "positive_count": 0,
                    "neutral_count": 0,
                    "negative_count": 0
                }
            monthly_data[month_key]["records"].append(record)
            
            emoji_signal = map_emoji_to_signal(record.get("emoji", ""))
            if emoji_signal == "positive":
                monthly_data[month_key]["positive_count"] += 1
            elif emoji_signal == "neutral":
                monthly_data[month_key]["neutral_count"] += 1
            else:
                monthly_data[month_key]["negative_count"] += 1
    
    # 转换为列表并排序
    monthly_list = sorted(monthly_data.values(), key=lambda x: x["month"], reverse=True)
    
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "scenario_id": scenario_id,
            "stats": stats,
            "history": history,
            "monthly": monthly_list
        }
    }


# ============================================================
# 用户反馈 API
# ============================================================

from pydantic import BaseModel
import base64
import html

class FeedbackRequest(BaseModel):
    user_identifier: str
    page_source: str
    feedback_text: str
    images: Optional[List[str]] = []  # base64 encoded images

@app.post("/api/feedback/suggestion")
async def submit_feedback(data: FeedbackRequest, request: Request):
    """
    B-7: 用户意见反馈
    接收用户反馈，保存本地并同步到飞书
    """
    user_identifier = data.user_identifier
    page_source = data.page_source
    feedback_text = data.feedback_text
    images_base64 = data.images or []

    # 输入验证
    if not user_identifier or not page_source or not feedback_text:
        return JSONResponse(
            status_code=400,
            content={"code": 4001, "message": "缺少必需参数"}
        )

    # 清理文本内容，防止 XSS
    feedback_text = html.escape(feedback_text.strip())
    if len(feedback_text) > 500:
        return JSONResponse(
            status_code=400,
            content={"code": 4002, "message": "反馈内容超出500字限制"}
        )

    # 生成反馈ID
    feedback_id = generate_feedback_id()

    # 获取客户端IP
    client_ip = request.client.host if request.client else ""

    # 处理图片上传（接收 base64 编码）
    image_tokens = []
    for img_base64 in images_base64[:3]:  # 最多3张
        try:
            # 移除 data URL 前缀（如 "data:image/png;base64,"）
            if ',' in img_base64:
                img_base64 = img_base64.split(',')[1]

            # 验证 base64 格式
            if len(img_base64) < 100:  # 太短的可能格式错误
                print(f"[反馈] 图片数据过短，跳过: {len(img_base64)} chars")
                continue

            # 解码 base64
            image_data = base64.b64decode(img_base64)

            # 验证图片大小（最大 5MB）
            if len(image_data) > 5 * 1024 * 1024:
                print(f"[反馈] 图片过大，跳过: {len(image_data)} bytes")
                continue

            token = upload_image_to_feishu(image_data, "feedback.png")
            if token:
                image_tokens.append(token)
            else:
                print(f"[反馈] 图片上传失败，返回 token 为空")
        except Exception as e:
            print(f"[反馈] 图片处理异常: {e}")

    # 创建时间
    created_at = datetime.now().isoformat()

    # 保存到本地数据库
    save_feedback_to_db(
        feedback_id=feedback_id,
        user_identifier=user_identifier,
        page_source=page_source,
        feedback_text=feedback_text,
        image_tokens=image_tokens,
        client_ip=client_ip
    )

    # 同步到飞书
    print(f"[反馈] 同步到飞书: feedback_id={feedback_id}, image_tokens数量={len(image_tokens)}")
    feishu_success = create_feedback_record(
        feedback_id=feedback_id,
        user_identifier=user_identifier,
        page_source=page_source,
        feedback_text=feedback_text,
        image_tokens=image_tokens,
        created_at=created_at,
        client_ip=client_ip
    )
    if feishu_success:
        mark_feedback_synced(feedback_id)

    return {
        "code": 0,
        "message": "ok",
        "data": {
            "feedback_id": feedback_id,
            "created_at": created_at
        }
    }


@app.get("/api/feedback/config")
async def get_feedback_config():
    """获取反馈功能配置状态"""
    return {
        "code": 0,
        "message": "ok",
        "data": {
            "enabled": is_feishu_feedback_configured(),
            "max_images": 3,
            "max_text_length": 500
        }
    }


# ============================================================
# 兼容旧 API（保留用于 demo 联调）
# ============================================================

@app.get("/api/history/{package_code}")
async def get_feedback_history_legacy(package_code: str, limit: int = 50):
    try:
        history = get_history_by_package(package_code, limit)
        return {"package_code": package_code, "history": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================
# Startup (Lifespan)
# ============================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[OK] 慢慢会 API v2.1 已启动")
    print(f"[OK] 数据库: {DB_PATH}")
    print(f"[OK] DeepSeek API: {DEEPSEEK_BASE_URL}")
    print(f"[OK] 任务包路径: {PACKAGES_PATH}")
    mock_mode = os.getenv("MOCK_MODE", "").lower() == "true"
    print(f"[OK] MOCK_MODE: {mock_mode}")
    feishu_enabled = is_feishu_configured()
    print(f"[OK] 飞书同步: {'已配置' if feishu_enabled else '未配置'}")
    yield
    print("[OK] 慢慢会 API 已关闭")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
