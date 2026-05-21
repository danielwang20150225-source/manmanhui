"""
Markdown 解析器
解析任务包 Markdown 文件为结构化数据
"""
import re
import os
from pathlib import Path
from typing import Dict, List, Any, Optional


# P级提示等级 → 大白话映射（用户可见字段）
P_LEVELS_PLAIN = {
    "P0": "无提示",
    "P1": "视觉提示",
    "P2": "示范引导",
    "P3": "手势提示",
    "P4": "身体辅助",
    "P5": "完全辅助",
}

# 已知环境列表（用于泛化表格解析）
KNOWN_ENVIRONMENTS = {'客厅', '卧室', '阳台', '户外', '厨房', '卫生间', '玄关', '书房', '餐厅', '院子'}


def load_package_markdown(package_code: str, packages_path: str) -> Optional[Dict[str, Any]]:
    """从 markdown 文件加载任务包，返回解析后的 dict"""
    kb_path = Path(packages_path)
    if not kb_path.exists():
        return None

    # 旧代码转新编号映射（处理直接传旧代码的边缘情况）
    OLD_TO_NEW = {
        "S-01": "01", "S-02": "02", "S-03": "03",
        "S-04": "05", "S-05": "06", "S-06": "07",
        "S-07": "08", "S-08": "09", "S-09": "10", "S-10": "10",
        "AAC-01": "11", "AAC-02": "12",
        "L-01": "22", "L-02": "25", "L-03": "03",
        "SP-01": "14",
    }
    if package_code in OLD_TO_NEW:
        package_code = OLD_TO_NEW[package_code]

    # 长格式代码解析（如 "20260505001_fuyi_kangju" → 提取末尾两位数字作为编号）
    if re.match(r'^\d{14}_\d{2}_', package_code):
        # 提取第15-16位的两位数字
        two_digit_code = package_code[14:16]
        if two_digit_code.isdigit() and 1 <= int(two_digit_code) <= 50:
            package_code = two_digit_code

    # 精确匹配策略：
    # - 旧代码（S-01/AAC-01/L-01/SP-01）：完整 stem 相等
    # - 新编号（01~50）：必须在 _XX_ 或 _XX$ 格式中（before必须是_或开头，after必须是_或结尾）
    if re.match(r'^(?:S|AAC|L|SP)-\d{2}$', package_code):
        for md_file in kb_path.glob("*.md"):
            if md_file.stem == f"任务包_{package_code}":
                return parse_package_markdown(md_file)
        return None
    # 新编号：前一个字符必须是_（或开头），后一个字符必须是_（或结尾）
    for md_file in kb_path.glob("*.md"):
        stem = md_file.stem
        idx = stem.find(package_code)
        if idx < 0:
            continue
        ok_before = (idx == 0) or (stem[idx - 1] == '_')
        after_idx = idx + len(package_code)
        ok_after = (after_idx >= len(stem)) or (stem[after_idx] == '_')
        if ok_before and ok_after:
            return parse_package_markdown(md_file)
    return None


def parse_package_markdown(file_path: Path) -> Dict[str, Any]:
    """解析任务包 markdown 文件为结构化 dict"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    package_code = extract_package_code(file_path.stem)
    package_name = extract_field(content, r"包名称[:：]\s*(.+?)(?:\n|$)", 1) or file_path.stem

    # 解析基本信息表
    basic_info = parse_basic_info_table(content)

    # 解析7天计划
    days_data = parse_daily_plan_table(content)

    # 解析各章节内容（前置条件、注意事项等）
    sections = parse_package_sections(content)

    return {
        "package_id": package_code,
        "package_name": package_name,
        "version": "1.0",
        "status": "ready",
        "basic_info": basic_info,
        "days_data": days_data,
        "sections": sections,
        "raw_markdown": content[:500],  # 保留原文用于调试
    }


def extract_package_code(stem: str) -> str:
    """从文件名提取 package_code（兼容旧代码 S-01/L-02/AAC-01 和新编号 01~50）"""
    # 优先匹配旧格式（S/L/AAC/SP 后跟 -XX）
    match = re.search(r'(?:[SL]|AAC|SP)-\d{2}', stem)
    if match:
        old_code = match.group()
        # 旧代码 → 新编号映射
        OLD_TO_NEW = {
            "S-01": "01", "S-02": "02", "S-03": "03",
            "S-04": "05", "S-05": "06", "S-06": "07",
            "S-07": "08", "S-08": "09", "S-09": "10", "S-10": "10",
            "AAC-01": "11", "AAC-02": "12",
            "L-01": "22", "L-02": "25", "L-03": "03",
            "SP-01": "14",
        }
        return OLD_TO_NEW.get(old_code, old_code)
    # 匹配新格式（两位数字）
    match2 = re.search(r'(?<![a-zA-Z])(\d{2})(?![a-zA-Z0-9])', stem)
    if match2:
        num = int(match2.group(1))
        if 1 <= num <= 50:
            return f"{num:02d}"
    return stem


def extract_field(content: str, pattern: str, group: int = 1) -> Optional[str]:
    match = re.search(pattern, content)
    return match.group(group).strip() if match else None


def parse_basic_info_table(content: str) -> Dict[str, Any]:
    """解析基本信息表格"""
    info = {}
    # 适用画像
    profile = extract_field(content, r"适用画像[:：]\s*(.+?)(?:\n|$)")
    if profile:
        age_match = re.search(r"(\d+)[-~](\d+)", profile)
        info["age_range"] = {"min": int(age_match.group(1)), "max": int(age_match.group(2))} if age_match else {"min": 2, "max": 5}
        info["language_level"] = profile
    # 训练周期
    period = extract_field(content, r"训练周期[:：]\s*(\d+)")
    if period:
        info["period_days"] = {"default": int(period), "min": int(period), "max": int(period) + 3}
    # 主目标
    target = extract_field(content, r"(?:^|\n)\|\s*\d+\s*\|[^|]*主目标[^|]*\|\s*([^|]+?)(?:\s*\|)")
    if target:
        info["target"] = target.strip()
    # 单次时长
    duration = extract_field(content, r"单次时长[:：]\s*(\d+)")
    if duration:
        info["single_session_max"] = int(duration)
    return info


def parse_package_sections(content: str) -> Dict[str, Any]:
    """从包 markdown 中提取各章节内容（前置条件、注意事项等）"""
    sections = {}
    parts = re.split(r'\n(?=##\s)', content)
    for part in parts:
        if not part.strip():
            continue
        m = re.match(r'^#{1,4}\s+(.+?)\n', part)
        if not m:
            continue
        title = m.group(1).strip()
        title_clean = re.sub(r'[\U0001F300-\U0001F9FF]', '', title).strip()
        if '前置能力' in title_clean:
            sections['preconditions'] = _clean_section(part)
        elif '不适用' in title_clean or '不做此任务' in title_clean:
            sections['contraindications'] = _clean_section(part)
        elif '提示等级' in title_clean:
            sections['prompt_levels'] = _clean_section(part)
        elif '理论基础' in title_clean or '行为分析' in title_clean:
            sections['theory'] = _clean_section(part)
        elif '升级' in title_clean or '降级' in title_clean:
            sections['level_rules'] = _clean_section(part)
        elif '转介' in title_clean or '立即停止' in title_clean:
            sections['referral'] = _clean_section(part)
        elif '情境' in title_clean and ('解读' in title_clean or '分析' in title_clean):
            sections['context_analysis'] = _clean_section(part)
    return sections


def _clean_section(text: str) -> str:
    """把 markdown 章节转为易读纯文本"""
    text = re.sub(r'^#{1,4}\s+[^\n]*\n', '', text, count=1)
    lines = []
    for line in text.split('\n'):
        if re.match(r'^\|?[\s:-]+\|', line):
            continue
        cells = [c.strip() for c in line.split('|') if c.strip() and not re.match(r'^[\s:-]+$', c)]
        if cells:
            lines.append(' '.join(cells))
    return '\n'.join(lines).strip()


def parse_daily_plan_table(content: str) -> Dict[str, Any]:
    """解析7天训练计划表格"""
    days = []
    # 找到7天计划总览表格
    match = re.search(r"##\s*📅\s*7天训练计划总览([\s\S]*?)(?:=|$)", content)
    if not match:
        # 尝试找 D1-D7 模式
        match = re.search(r"\|\s*D\s*1\s*\|", content)

    # 解析每天的计划（从 ### 天数 标题分割）
    # 支持 D1、D1-D2 等多种格式
    lines = content.split('\n')
    header_line_nums = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Match: ### D1：title 或 #### D1：title（支持3~5个#）
        # 范围标题如 ### D1-D2：xxx 会被展开为多个单日条目，每个指向范围标题行
        m = re.match(r'^#{3,5}\s+D(\d+)(?:-D(\d+))?[：:]\s*(.+)$', stripped)
        if m:
            day_start = int(m.group(1))
            day_end = int(m.group(2)) if m.group(2) else day_start
            # 范围标题（如D1-D2）自身算作第一个条目
            for d in range(day_start, day_end + 1):
                header_line_nums.append((i, str(d), m.group(3)))

    for idx, (header_line_num, day_range, title) in enumerate(header_line_nums):
        day_num = int(day_range.split("-")[0])

        # Content is from after this header line to the next header (or end)
        start_char = len('\n'.join(lines[:header_line_num + 1]))
        if idx + 1 < len(header_line_nums):
            # 有下一个 ### D 标题，用它作为边界
            next_header_line = header_line_nums[idx + 1][0]
            end_char = len('\n'.join(lines[:next_header_line]))
        else:
            # 没有下一个 ### D 标题，找下一个 ## 标题（如 ## 📊 每日记录表）
            end_char = len(content)
            for i in range(header_line_num + 1, len(lines)):
                stripped = lines[i].strip()
                if stripped.startswith('## ') or stripped.startswith('##​'):
                    end_char = len('\n'.join(lines[:i]))
                    break
        day_content = content[start_char:end_char]

        # Day1 需要最早清洗相对时间引用，避免后续提取时污染
        # 注意：只清洗内容，不破坏表格换行结构（不能使用 \s+ 压缩）
        if day_num == 1:
            day_content = re.sub(r'昨天', '首日', day_content)
            day_content = re.sub(r'前天', '', day_content)
            day_content = re.sub(r'以往|之前\s*(曾|已经|进行|做过|完成)', '', day_content)

        # 提取 theme（优先用标题，其次用"主题"行）
        theme_match = re.search(r"主题[:：]\s*(.+?)(?:\n|$)", day_content)
        theme = theme_match.group(1).strip() if theme_match else title.strip()

        # 提取目标（兼容 **今日目标**： 和 **目标**： 两种格式）
        # 使用非贪婪匹配，遇到 **成功标准 或 场景 或 第一个空行就停止
        goal_match = re.search(r"\*\*(?:今日)?目标\*\*[：:](.+?)(?=\*\*成功标准|\*\*场景|\n\n)", day_content, re.DOTALL)
        if not goal_match:
            goal_match = re.search(r"目标[：:]\s*(.+?)(?=\n\n)", day_content, re.DOTALL)
        goal_desc = goal_match.group(1).strip() if goal_match else ""

        # 提取成功标准（观察提示的核心，**成功标准**：格式）
        # 在 **场景** 或 第一个空行 之前的内容
        criteria_match = re.search(r"\*\*成功标准\*\*[：:](.+?)(?=\*\*场景\*\*|\n\n)", day_content, re.DOTALL)
        success_criteria = criteria_match.group(1).strip() if criteria_match else ""

        # 提取观察记录提示（从markdown中提取"观察记录"或"记录要点"字段）
        obs_match = re.search(r"观察记录[：:]\s*(.+?)(?:\n\n|\n##|$)", day_content, re.DOTALL)
        if not obs_match:
            obs_match = re.search(r"记录要点[：:]\s*(.+?)(?:\n\n|\n##|$)", day_content, re.DOTALL)
        obs_prompt = obs_match.group(1).strip().replace("\n", " ").strip() if obs_match else ""

        # 如果没有显式观察记录，从成功标准生成
        if not obs_prompt and success_criteria:
            obs_prompt = f"今日练习后记录：{success_criteria}"

        # 提取场景
        scene_match = re.search(r"场景[:：]\s*(.+?)(?:\n|$)", day_content)
        situation = scene_match.group(1).strip() if scene_match else ""

        # 提取时长
        dur_match = re.search(r"(\d+)[-~](\d+)\s*分钟", day_content)
        duration_min = int(dur_match.group(1)) if dur_match else 5
        duration_max = int(dur_match.group(2)) if dur_match else 10

        # 解析步骤
        steps = parse_steps_section(day_content)

        days.append({
            "day": day_num,
            "theme": theme,
            "goal": {
                "description": goal_desc,
                "success_criteria": {
                    "type": "rate",
                    "threshold": 0.8,
                    "opportunities": 10,
                    "observation_prompt": obs_prompt,  # 动态观察提示
                }
            },
            "situation": situation,
            "duration_min": duration_min,
            "duration_max": duration_max,
            "steps": steps,
            "reinforcement": extract_reinforcement(day_content),
            "generalization": extract_generalization(day_content),
            "parent_script": extract_parent_script(day_content),
        })

    # 如果没找到，按默认7天返回
    if not days:
        for i in range(1, 8):
            days.append({
                "day": i,
                "theme": f"Day {i} 训练",
                "goal": {"description": "完成训练目标", "success_criteria": {"type": "rate", "threshold": 0.8, "opportunities": 10}},
                "situation": "日常场景",
                "duration_min": 5,
                "duration_max": 10,
                "steps": [{"step_order": 1, "description": "步骤1", "prompt_level": "无提示", "success_criteria": "完成"}],
                "reinforcement": "口头表扬+零食强化",
                "generalization": {"situation": "日常场景", "person": "家人", "material": "日常物品"},
                "parent_script": "做得好！",
            })

    return {"days": days}


def parse_steps_section(day_content: str) -> List[Dict[str, Any]]:
    """从某天内容中解析训练步骤（支持多种格式）"""
    steps = []

    # 策略1: 标准步骤格式 | 数字 | 内容 | ...
    # 只收集第一列是纯数字的行（排除包22的环节格式等）
    all_lines = day_content.split('\n')
    standard_rows = []
    duration_format_rows = []  # 包22格式: | 环节 | 时长 | 内容 |

    for line in all_lines:
        line = line.strip()
        if not line.startswith('|') or re.match(r'^\|[-]+\|', line):
            continue  # 跳过空行、分隔行
        # 统一用 split('|') 解析单元格（兼容单管道和多管道）
        raw_cells = line.split('|')
        cells = [c.strip() for c in raw_cells if c.strip()]
        if len(cells) < 2:
            continue
        first_cell = cells[0]
        # 标准格式: 第一列是数字
        if re.match(r'^\d+$', first_cell):
            standard_rows.append(cells)
        # 包22格式: 第一列是环节名（非数字），第二列是时长
        elif len(cells) >= 3:
            time_cell = cells[1].strip()
            if re.match(r'^\d+.*?(分钟|秒|分|min|sec)', time_cell):
                duration_format_rows.append(cells)

    # 解析标准格式行
    for cells in standard_rows:
        first_cell = cells[0]
        step_num_match = re.match(r'^(\d+)', first_cell)
        if step_num_match:
            step_num = int(step_num_match.group(1))
            desc = cells[1].strip() if len(cells) > 1 else ''
            prompt_level = 'P0'
            for cell in cells:
                pl_match = re.search(r'(P[0-4])(?:→|->)?', cell)
                if pl_match:
                    prompt_level = pl_match.group(1)
                    break
            if desc and len(desc) > 1:
                # P级术语转大白话
                plain_level = P_LEVELS_PLAIN.get(prompt_level, prompt_level)
                steps.append({
                    'step_order': step_num,
                    'description': desc[:200],
                    'prompt_level': plain_level,  # 大白话，用户可见
                    'prompt_instruction': '等待独立完成',
                    'success_criteria': '正确完成'
                })

    # 解析包22格式: | 环节名 | 时长 | 内容 | 强化物 |
    for cells in duration_format_rows:
        desc = cells[2].strip()
        if desc and len(desc) > 1:
            steps.append({
                'step_order': len(steps) + 1,
                'description': desc[:200],
                'prompt_level': "无提示",
                'prompt_instruction': '等待独立完成',
                'success_criteria': '正确完成'
            })

    # 策略2: 如果表格解析失败，尝试找编号列表格式
    if not steps:
        numbered_steps = re.findall(
            r"(?:^|\n)\s*(?:第?\d+[题步个部]\s*[:：\.]\\s*|Step\s+\d+\s*[:\.]\s*)(.+?)(?=\n\s*(?:第?\d+[题步个部]|Step\s+\d+|$\s)|\Z)",
            day_content, re.DOTALL
        )
        for idx, (desc,) in enumerate(numbered_steps[:10], 1):
            desc = desc.strip()
            if desc and len(desc) > 2:
                steps.append({
                    "step_order": idx,
                    "description": desc[:200],
                    "prompt_level": "无提示",
                    "prompt_instruction": "等待独立完成",
                    "success_criteria": "正确完成"
                })

    # 策略3: 泛化表格格式（如D7: | 环境 | 活动情境 | ... | 操作要点 |）
    if not steps:
        in_step_table = False
        step_table_rows = []
        env_col_idx = -1

        for line in all_lines:
            line_stripped = line.strip()
            if re.match(r'^\|\s*[-]+\s*\|', line_stripped):
                continue
            if not line_stripped.startswith('|'):
                continue
            cells = [c.strip() for c in re.findall(r'\|(.+?)(?=\|)', line_stripped)]
            if not cells:
                continue
            first_cell = cells[0]

            # 表头：包含"环境"
            if '环境' in first_cell and len(first_cell) < 10:
                in_step_table = True
                for i, col in enumerate(cells):
                    if '操作要点' in col:
                        env_col_idx = i
                        break
                else:
                    env_col_idx = -1
                continue

            # 遇到"检查项"表头就停止
            if first_cell in ('检查项', '检查项目', '场景切换', '泛化计划'):
                in_step_table = False
                continue

            # 已知环境名
            if in_step_table and first_cell in KNOWN_ENVIRONMENTS:
                step_table_rows.append((first_cell, cells, env_col_idx))

        for first_cell, cells, col_idx in step_table_rows:
            if col_idx > 0 and col_idx < len(cells):
                desc = cells[col_idx].strip()
            else:
                desc = cells[-1].strip() if cells[-1].strip() else (cells[-2].strip() if len(cells) >= 2 else '')
            skip_keywords = ['说明', '目标', '内容', '升级版', '本周', '上传', '降级',
                            '成功率', '频率', '次数', '记录表', '计划', '检查项']
            if desc in skip_keywords or any(desc.startswith(kw) for kw in skip_keywords):
                continue
            if desc and len(desc) > 1 and desc not in ('操作要点', '活动情境', '强化方式'):
                steps.append({
                    "step_order": len(steps) + 1,
                    "description": desc[:200],
                    "prompt_level": "无提示",
                    "prompt_instruction": "等待独立完成",
                    "success_criteria": "正确完成"
                })

    # 策略1b: 空格分隔的步骤行（包08等使用此格式）
    for line in all_lines:
        line = line.strip()
        if not line.startswith('|') or re.match(r'^\|[-]+\|', line):
            continue
        raw_cells = line.split('|')
        cells = [c.strip() for c in raw_cells if c.strip()]
        if len(cells) < 1:
            continue
        first_cell = cells[0].strip()
        if re.match(r'^\d+$', first_cell):
            continue
        if first_cell and first_cell[0].isdigit():
            m = re.match(r'^(\d+)\s+(.+?)\s{2,}(P[0-6])\s+(.+?)\s+(.+)$', first_cell)
            if m:
                step_num = int(m.group(1))
                desc = m.group(2).strip()
                p_level = m.group(3)
                success = m.group(4).strip()
                instruction = m.group(5).strip()
                if desc and len(desc) > 1:
                    plain_level = P_LEVELS_PLAIN.get(p_level, p_level)
                    steps.append({
                        'step_order': step_num,
                        'description': desc[:200],
                        'prompt_level': plain_level,
                        'prompt_instruction': instruction[:50] if instruction else '等待独立完成',
                        'success_criteria': success[:50] if success else '正确完成'
                    })
            else:
                num_m = re.match(r'^(\d+)', first_cell)
                p_m = re.search(r'(P[0-6])', first_cell)
                if num_m:
                    step_num = int(num_m.group(1))
                    p_level = p_m.group(1) if p_m else 'P0'
                    if p_m:
                        desc = first_cell[len(num_m.group(0)):first_cell.find(p_m.group(1))].strip()
                    else:
                        desc = first_cell[len(num_m.group(0)):].strip()
                    desc = re.sub(r'\s{2,}.*$', '', desc).strip()
                    if desc and len(desc) > 1:
                        plain_level = P_LEVELS_PLAIN.get(p_level, p_level)
                        steps.append({
                            'step_order': step_num,
                            'description': desc[:200],
                            'prompt_level': plain_level,
                            'prompt_instruction': '等待独立完成',
                            'success_criteria': '正确完成'
                        })

    # 策略4: 空格分隔的步骤行
    space_step_pattern = re.compile(
        r'^\|\s*(\d+)\s+(.+?)\s{2,}(P[0-6])\s+(.+?)\s+(.+?)\s*\|$'
    )
    for line in all_lines:
        line = line.strip()
        if not line.startswith('|') or '|' not in line[1:]:
            continue
        cells = [c.strip() for c in re.findall(r'\|(.+?)(?=\|)', line)]
        if len(cells) >= 3 and re.match(r'^\d+$', cells[0]) and '|' in line[1:]:
            continue
        m = space_step_pattern.match(line)
        if m:
            step_num = int(m.group(1))
            desc = m.group(2).strip()
            p_level = m.group(3)
            success = m.group(4).strip()
            instruction = m.group(5).strip()
            if desc and len(desc) > 1:
                plain_level = P_LEVELS_PLAIN.get(p_level, p_level)
                steps.append({
                    'step_order': step_num,
                    'description': desc[:200],
                    'prompt_level': plain_level,
                    'prompt_instruction': instruction[:50] if instruction else '等待独立完成',
                    'success_criteria': success[:50] if success else '正确完成'
                })

    # 按step_order排序并去重
    steps = sorted(steps, key=lambda x: x.get("step_order", 0))
    seen_orders = set()
    unique_steps = []
    for s in steps:
        order = s.get("step_order", 0)
        if order not in seen_orders:
            seen_orders.add(order)
            unique_steps.append(s)

    # 清理步骤中残留的P级参考文本
    p_ref_pattern = re.compile(r'[(（]P[0-6][)）]|[→\->]P[0-6]\b')
    for s in unique_steps:
        for field in ['description', 'success_criteria', 'prompt_instruction']:
            if field in s and s[field]:
                s[field] = p_ref_pattern.sub('', s[field]).strip()
                s[field] = re.sub(r'\s{2,}', ' ', s[field])

    return unique_steps


def extract_reinforcement(day_content: str) -> str:
    match = re.search(r"强化[:：]\s*(.+?)(?:\n|$)", day_content)
    return match.group(1).strip() if match else "口头表扬+零食强化"


def extract_generalization(day_content: str) -> Dict[str, str]:
    return {
        "situation": "日常场景",
        "person": "家人",
        "material": "日常物品",
    }


def extract_parent_script(day_content: str) -> str:
    match = re.search(r"家长台词[:：]\s*(.+?)(?:\n\n|$)", day_content, re.DOTALL)
    if not match:
        match = re.search(r"家长说[:：]\s*['\"]?(.+?)['\"]?(?:\n|$)", day_content)
    return match.group(1).strip() if match else "做得好！继续加油！"