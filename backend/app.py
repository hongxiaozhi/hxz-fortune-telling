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


@app.errorhandler(400)
def handle_400(error):
    return jsonify({"error": "bad_request", "message": str(error)}), 400


@app.errorhandler(404)
def handle_404(error):
    return jsonify({"error": "not_found", "message": str(error)}), 404


@app.errorhandler(500)
def handle_500(error):
    return jsonify({"error": "server_error", "message": str(error)}), 500


@app.errorhandler(BadRequest)
def handle_bad_json(error):
    if request.path.startswith("/api/"):
        return jsonify({"error": "invalid_json", "message": "Malformed JSON body"}), 400
    return jsonify({"error": "bad_request", "message": str(error)}), 400


@app.route("/api/fortune/health", methods=["GET"])
def health():
    return jsonify(
        {
            "status": "ok",
            "service": "hxz-fortune",
            "version": "v1.3.0",
        }
    )


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path):
    if path.startswith("api/"):
        return jsonify({"error": "not_found"}), 404

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

    if "precision_mode" in data and data["precision_mode"] not in [None, "", "approx", "standard"]:
        return "Invalid precision_mode value", None

    if "analysis_mode" in data and data["analysis_mode"] not in [None, "", "standard", "advanced"]:
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
    idx = 1
    while seg_start <= end:
        seg_end = min(seg_start + timedelta(days=6), end)
        segments.append(
            {
                "segment_index": idx,
                "start_date": seg_start.strftime("%Y-%m-%d"),
                "end_date": seg_end.strftime("%Y-%m-%d"),
            }
        )
        seg_start = seg_end + timedelta(days=1)
        idx += 1

    return None, segments


@app.route("/api/fortune/analyze", methods=["POST"])
def analyze():
    try:
        data = request.get_json(force=True)
    except BadRequest:
        return jsonify({"error": "invalid_json", "message": "Malformed JSON body"}), 400

    err, segments = validate_and_segment(data)
    if err:
        return jsonify({"error": "validation_error", "message": err}), 400

    precision_mode = data.get("precision_mode", "standard")
    analysis_mode = data.get("analysis_mode", "standard")
    has_birth_time = data.get("has_birth_time", False)
    birth_place = (data.get("birth_place") or "").strip()

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

    bazi_summary = {
        "year_pillar": "甲子",
        "month_pillar": "乙丑",
        "day_pillar": "丙寅",
        "hour_pillar": None if not has_birth_time else "丁卯",
    }

    wuxing_score = {
        "wood": 70,
        "fire": 60,
        "earth": 50,
        "metal": 40,
        "water": 30,
    }

    overall_advice = {
        "suitable": "适合稳步推进计划，优先做学习、整理和长期积累类事项。",
        "avoid": "不宜冲动决策，也要避免同时摊开过多事务消耗精力。",
        "reminder": "保持作息节奏稳定，先顾好体力与情绪，再谈效率。",
    }

    if analysis_mode == "advanced":
        overall_advice["reminder"] = "进阶模式会更强调输入完整度与时间段差异，建议结合具体安排逐项判断。"

    segs = []
    for seg in segments:
        trend = "aligned" if seg["segment_index"] % 2 == 1 else "deviated"
        segs.append(
            {
                "segment_index": seg["segment_index"],
                "start_date": seg["start_date"],
                "end_date": seg["end_date"],
                "trend_alignment": trend,
                "suitable": "这段时间适合按部就班推进手头计划，先做确定性高的事。",
                "avoid": "避免争执、情绪化表态，以及为了赶进度而仓促拍板。",
                "reminder": "留意精力分配，保持节奏感，比一口气冲刺更重要。",
                "dimensions": {
                    "work_study": "high" if trend == "aligned" else "medium",
                    "finance": "medium",
                    "social": "low" if trend == "deviated" else "medium",
                    "health": "medium",
                },
            }
        )

    analysis_context = {
        "analysis_mode": analysis_mode,
        "has_birth_time": has_birth_time,
        "birth_place": birth_place or None,
        "inputs_summary": [
            "已启用进阶模式" if analysis_mode == "advanced" else "使用标准模式",
            "已提供出生时辰" if has_birth_time else "未提供出生时辰",
            f"出生地：{birth_place}" if birth_place else "未提供出生地",
        ],
    }

    mode_hint = (
        "进阶模式会更关注输入完整度对结果的影响，如果你要做更细的区间判断，建议同时提供出生时辰和出生地。"
        if analysis_mode == "advanced"
        else "标准模式适合先看大方向，如果你需要比较不同输入条件对结果的影响，可以切换到进阶模式。"
    )

    result = {
        "request_id": str(uuid.uuid4()),
        "disclaimer": "本结果仅供参考，不替代医疗、法律或财务等专业意见。",
        "precision_level": precision_level,
        "precision_note": precision_note,
        "bazi_summary": bazi_summary,
        "wuxing_score": wuxing_score,
        "overall_advice": overall_advice,
        "segments": segs,
        "upgrade_hint": upgrade_hint,
        "analysis_context": analysis_context,
        "mode_hint": mode_hint,
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
