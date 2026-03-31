import os
import re
import uuid
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_cors import CORS
from werkzeug.exceptions import BadRequest


app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), "..", "frontend"),
    static_url_path="",
)
CORS(app)


def make_json_error(error_type, message, status_code):
    return jsonify({"error": error_type, "message": message}), status_code


@app.errorhandler(400)
def handle_400(error):
    return make_json_error("bad_request", str(error), 400)


@app.errorhandler(404)
def handle_404(error):
    return make_json_error("not_found", str(error), 404)


@app.errorhandler(500)
def handle_500(error):
    return make_json_error("server_error", str(error), 500)


@app.errorhandler(BadRequest)
def handle_bad_json(error):
    if request.path.startswith("/api/"):
        return make_json_error("invalid_json", "Malformed JSON body", 400)
    return make_json_error("bad_request", str(error), 400)


@app.route("/api/fortune/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "hxz-fortune",
            "version": "v1.5.0",
        }
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return make_json_error("not_found", "not_found", 404)

    full_path = os.path.join(app.static_folder, path)
    if path and os.path.exists(full_path):
        return app.send_static_file(path)
    return app.send_static_file("index.html")


def validate_and_segment(data):
    required = ["gender", "calendar_type", "birth_date", "start_date", "end_date"]
    for key in required:
        if key not in data or data[key] in [None, "", "null"]:
            return f"Missing required field: {key}", None

    if data["gender"] not in {"male", "female", "other", "unknown"}:
        return "Invalid gender value", None

    if data["calendar_type"] not in {"solar", "lunar"}:
        return "Invalid calendar_type value", None

    if data.get("precision_mode") not in [None, "", "approx", "standard"]:
        return "Invalid precision_mode value", None

    if data.get("analysis_mode") not in [None, "", "standard", "advanced"]:
        return "Invalid analysis_mode value", None

    birth_place = data.get("birth_place")
    if birth_place not in [None, "", "null"]:
        if not isinstance(birth_place, str):
            return "birth_place must be a string", None
        if len(birth_place.strip()) > 30:
            return "birth_place length cannot exceed 30", None

    date_re = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    for field in ["birth_date", "start_date", "end_date"]:
        if not date_re.match(str(data[field])):
            return f"{field} must be in YYYY-MM-DD format", None

    try:
        start = datetime.strptime(data["start_date"], "%Y-%m-%d")
        end = datetime.strptime(data["end_date"], "%Y-%m-%d")
        datetime.strptime(data["birth_date"], "%Y-%m-%d")
    except ValueError:
        return "Invalid date format", None

    if start > end:
        return "start_date must be before or equal to end_date", None

    if (end - start).days > 179:
        return "Date range cannot exceed 180 days", None

    has_birth_time = data.get("has_birth_time", False)
    birth_time = data.get("birth_time")
    if not has_birth_time:
        if birth_time not in [None, "", "null"]:
            return "birth_time must be empty if has_birth_time is false", None
    else:
        if birth_time in [None, "", "null"]:
            return "birth_time is required when has_birth_time is true", None
        time_re = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")
        if not time_re.match(str(birth_time)):
            return "birth_time must be in HH:MM 24-hour format", None

    segments = []
    seg_start = start
    index = 1
    while seg_start <= end:
        seg_end = min(seg_start + timedelta(days=6), end)
        segments.append(
            {
                "segment_index": index,
                "start_date": seg_start.strftime("%Y-%m-%d"),
                "end_date": seg_end.strftime("%Y-%m-%d"),
            }
        )
        seg_start = seg_end + timedelta(days=1)
        index += 1

    return None, segments


def build_context_notes(analysis_mode, has_birth_time, birth_place):
    notes = []
    notes.append("使用进阶模式" if analysis_mode == "advanced" else "使用标准模式")
    notes.append("已提供出生时辰" if has_birth_time else "未提供出生时辰")
    notes.append(f"出生地：{birth_place}" if birth_place else "未提供出生地")
    return notes


def build_mode_hint(analysis_mode, has_birth_time, birth_place):
    if analysis_mode == "standard":
        return "标准模式适合先看大方向，重点帮助你快速建立近期安排的优先级。"
    if has_birth_time and birth_place:
        return "进阶模式已使用出生时辰和出生地，当前结果会更强调输入完整度带来的细节差异。"
    if has_birth_time or birth_place:
        return "你已开启进阶模式，但输入仍不完整，当前结果会给出部分细化提示，同时保留限制说明。"
    return "你已开启进阶模式，但缺少出生时辰和出生地，当前只能做轻量差异提示，暂不视为精细分析。"


def build_overall_advice(analysis_mode, has_birth_time, birth_place):
    if analysis_mode == "advanced" and has_birth_time and birth_place:
        return {
            "suitable": "适合把近期计划拆成更细的小节点推进，优先安排需要判断节奏和配合度的事项。",
            "avoid": "不宜一口气铺开太多并行任务，尤其要避免在信息未核实前直接做关键决定。",
            "reminder": "当前输入完整度较高，建议把结果当作节奏提醒来用，逐段核对安排会更有效。",
        }
    if analysis_mode == "advanced":
        return {
            "suitable": "适合先根据已有输入做更细的轻重排序，优先处理最容易落地和最可控的安排。",
            "avoid": "不宜把当前结果当成完整定论，尤其在缺少出生时辰或出生地时要避免过度放大细节判断。",
            "reminder": "你已开启进阶模式，但部分输入仍缺失，系统会提示哪些地方能细看、哪些地方仍需保守判断。",
        }
    return {
        "suitable": "适合稳步推进计划，优先做学习、整理和长期积累类事项。",
        "avoid": "不宜冲动决策，也要避免同时摊开过多事务消耗精力。",
        "reminder": "保持作息节奏稳定，先顾好体力与情绪，再谈效率。",
    }


def build_precision_bundle(precision_mode, has_birth_time, analysis_mode, birth_place):
    precision_level = "medium" if precision_mode == "standard" and has_birth_time else "low"
    precision_note = ""
    upgrade_hint = {"show": False, "title": "", "content": "", "affected_dimensions": []}

    if precision_mode == "standard" and not has_birth_time:
        precision_note = "由于未提供出生时辰，本次结果已降级为大概模式，适合做基础参考。"
        upgrade_hint = {
            "show": True,
            "title": "补充出生时辰可获得更精细的结果",
            "content": "如果能补充出生时辰，系统会给出更贴合个人节奏的建议与提醒。",
            "affected_dimensions": ["work_study", "finance", "social", "health"],
        }
    elif analysis_mode == "advanced" and not birth_place:
        precision_note = "当前使用进阶模式，但未提供出生地，差异提示会更偏向方向性提醒。"
        upgrade_hint = {
            "show": True,
            "title": "补充出生地可增强进阶模式差异提示",
            "content": "补充出生地后，系统能更明确地区分哪些分段建议来自输入完整度提升。",
            "affected_dimensions": ["work_study", "social"],
        }

    return precision_level, precision_note, upgrade_hint


def build_segment_copy(trend_alignment, analysis_mode, has_birth_time, birth_place):
    if analysis_mode == "advanced" and has_birth_time and birth_place:
        if trend_alignment == "aligned":
            return (
                "这段时间适合细化安排节奏，优先推进需要提前沟通和连续跟进的事项。",
                "避免为了赶进度直接压缩准备时间，也不要忽略协作节奏。",
                "由于本次输入较完整，这一段更适合做具体安排，但仍建议按周复看变化。",
            )
        return (
            "这段时间适合先做低风险的确认与铺垫，重要事项可拆成两步推进。",
            "避免因为着急推进而省略确认环节，也不要在波动段一次性压满安排。",
            "这一段和整体趋势有轻微偏离，进阶模式提示你更适合留出缓冲，不要把计划压得过满。",
        )

    if analysis_mode == "advanced":
        if trend_alignment == "aligned":
            suitable = "这段时间适合先处理最有把握的安排，再逐步补细节。"
        else:
            suitable = "这段时间适合保守推进，优先保留回旋空间。"
        return (
            suitable,
            "避免把当前结果当成完整精细判断，尤其在输入仍不完整时。",
            "你已开启进阶模式，但当前输入完整度有限，这一段更适合参考方向，而不是直接定死细节。",
        )

    return (
        "这段时间适合按部就班推进手头计划，先做确定性高的事。",
        "避免争执、情绪化表态，以及为了赶进度而仓促拍板。",
        "留意精力分配，保持节奏感，比一口气冲刺更重要。",
    )


@app.route("/api/fortune/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
    except BadRequest:
        return make_json_error("invalid_json", "Malformed JSON body", 400)

    error_message, segments = validate_and_segment(data)
    if error_message:
        return make_json_error("validation_error", error_message, 400)

    precision_mode = data.get("precision_mode", "standard")
    analysis_mode = data.get("analysis_mode", "standard")
    has_birth_time = data.get("has_birth_time", False)
    birth_place = (data.get("birth_place") or "").strip()

    precision_level, precision_note, upgrade_hint = build_precision_bundle(
        precision_mode, has_birth_time, analysis_mode, birth_place
    )

    bazi_summary = {
        "year_pillar": "甲子",
        "month_pillar": "乙丑",
        "day_pillar": "丙寅",
        "hour_pillar": "丁卯" if has_birth_time else None,
    }

    wuxing_score = {
        "wood": 70 if analysis_mode == "standard" else 72,
        "fire": 60 if analysis_mode == "standard" else 58,
        "earth": 50,
        "metal": 40 if birth_place else 38,
        "water": 30 if has_birth_time else 32,
    }

    overall_advice = build_overall_advice(analysis_mode, has_birth_time, birth_place)

    segment_results = []
    for segment in segments:
        trend_alignment = "aligned" if segment["segment_index"] % 2 == 1 else "deviated"
        suitable, avoid, reminder = build_segment_copy(
            trend_alignment, analysis_mode, has_birth_time, birth_place
        )
        segment_results.append(
            {
                "segment_index": segment["segment_index"],
                "start_date": segment["start_date"],
                "end_date": segment["end_date"],
                "trend_alignment": trend_alignment,
                "suitable": suitable,
                "avoid": avoid,
                "reminder": reminder,
                "dimensions": {
                    "work_study": "high" if trend_alignment == "aligned" else "medium",
                    "finance": "medium",
                    "social": "low" if trend_alignment == "deviated" else "medium",
                    "health": "medium",
                },
            }
        )

    result = {
        "request_id": str(uuid.uuid4()),
        "disclaimer": "本结果仅供参考，不替代医疗、法律或财务等专业意见。",
        "precision_level": precision_level,
        "precision_note": precision_note,
        "bazi_summary": bazi_summary,
        "wuxing_score": wuxing_score,
        "overall_advice": overall_advice,
        "segments": segment_results,
        "upgrade_hint": upgrade_hint,
        "analysis_context": {
            "analysis_mode": analysis_mode,
            "has_birth_time": has_birth_time,
            "birth_place": birth_place or None,
            "inputs_summary": build_context_notes(analysis_mode, has_birth_time, birth_place),
        },
        "mode_hint": build_mode_hint(analysis_mode, has_birth_time, birth_place),
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
