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
            "version": "v1.1.0",
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
    has_birth_time = data.get("has_birth_time", False)
    precision_level = "medium" if precision_mode == "standard" and has_birth_time else "low"
    precision_note = ""
    upgrade_hint = {"show": False, "title": "", "content": "", "affected_dimensions": []}

    if precision_mode == "standard" and not has_birth_time:
        precision_note = "Birth time was not provided, so the result has been downgraded to approximate mode."
        upgrade_hint = {
            "show": True,
            "title": "Add birth time for a more precise reading",
            "content": "Providing birth time can improve accuracy and produce more personalized suggestions.",
            "affected_dimensions": ["work_study", "finance", "social", "health"],
        }

    bazi_summary = {
        "year_pillar": "Jia Zi",
        "month_pillar": "Yi Chou",
        "day_pillar": "Bing Yin",
        "hour_pillar": None if not has_birth_time else "Ding Mao",
    }

    wuxing_score = {
        "wood": 70,
        "fire": 60,
        "earth": 50,
        "metal": 40,
        "water": 30,
    }

    overall_advice = {
        "suitable": "Good for steady progress, learning, and self-improvement.",
        "avoid": "Avoid impulsive decisions and overcommitting your energy.",
        "reminder": "Keep your routine balanced and pay attention to rest.",
    }

    segs = []
    for seg in segments:
        trend = "aligned" if seg["segment_index"] % 2 == 1 else "deviated"
        segs.append(
            {
                "segment_index": seg["segment_index"],
                "start_date": seg["start_date"],
                "end_date": seg["end_date"],
                "trend_alignment": trend,
                "suitable": "A good period to move plans forward step by step.",
                "avoid": "Avoid friction, arguments, and rushed choices.",
                "reminder": "Protect your energy and keep a stable rhythm.",
                "dimensions": {
                    "work_study": "high" if trend == "aligned" else "medium",
                    "finance": "medium",
                    "social": "low" if trend == "deviated" else "medium",
                    "health": "medium",
                },
            }
        )

    result = {
        "request_id": str(uuid.uuid4()),
        "disclaimer": "This result is for reference only and does not replace medical, legal, or financial advice.",
        "precision_level": precision_level,
        "precision_note": precision_note,
        "bazi_summary": bazi_summary,
        "wuxing_score": wuxing_score,
        "overall_advice": overall_advice,
        "segments": segs,
        "upgrade_hint": upgrade_hint,
    }
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)
