# HXZ Fortune v1.1 - Minimal Flask App
# Run: python app.py
# For first-time DB setup: python init_db.py



from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta
import uuid
import re

app = Flask(__name__)
CORS(app)

# --- Unified JSON error handlers ---
@app.errorhandler(400)
def handle_400(e):
    return jsonify({'error': 'bad_request', 'message': str(e)}), 400

@app.errorhandler(404)
def handle_404(e):
    return jsonify({'error': 'not_found', 'message': str(e)}), 404

@app.errorhandler(500)
def handle_500(e):
    return jsonify({'error': 'server_error', 'message': str(e)}), 500

@app.errorhandler(BadRequest)
def handle_bad_json(e):
    # Malformed JSON
    if request.path.startswith('/api/'):
        return jsonify({'error': 'invalid_json', 'message': 'Malformed JSON body'}), 400
    return jsonify({'error': 'bad_request', 'message': str(e)}), 400

# --- Health Check ---

# --- Health Check ---
@app.route('/api/fortune/health', methods=['GET'])
def health():
    return jsonify({
        'status': 'ok',
        'service': 'hxz-fortune',
        'version': 'v1.1.0'
    })


@app.route('/', methods=['GET'])
def index():
    # Provide a simple JSON overview when hitting the root path
    return jsonify({
        'service': 'hxz-fortune',
        'status': 'running',
        'available_endpoints': [
            {'path': '/api/fortune/health', 'method': 'GET', 'desc': 'health check'},
            {'path': '/api/fortune/analyze', 'method': 'POST', 'desc': 'analysis endpoint'}
        ]
    })

# --- Validation and Segmentation ---
def validate_and_segment(data):
    required = ['gender', 'calendar_type', 'birth_date', 'start_date', 'end_date']
    for k in required:
        if k not in data or data[k] in [None, '', 'null']:
            return f"Missing required field: {k}", None
    if data['gender'] not in {'male', 'female', 'other', 'unknown'}:
        return 'Invalid gender value', None
    if data['calendar_type'] not in {'solar', 'lunar'}:
        return 'Invalid calendar_type value', None
    if 'precision_mode' in data and data['precision_mode'] not in [None, '', 'approx', 'standard']:
        return 'Invalid precision_mode value', None
    date_re = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    for dfield in ['birth_date', 'start_date', 'end_date']:
        if not date_re.match(str(data[dfield])):
            return f"{dfield} must be in YYYY-MM-DD format", None
    try:
        start = datetime.strptime(data['start_date'], '%Y-%m-%d')
        end = datetime.strptime(data['end_date'], '%Y-%m-%d')
        _ = datetime.strptime(data['birth_date'], '%Y-%m-%d')
    except Exception:
        return 'Invalid date format', None
    if start > end:
        return 'start_date must be before or equal to end_date', None
    if (end - start).days > 179:
        return 'Date range cannot exceed 180 days', None
    has_birth_time = data.get('has_birth_time', False)
    birth_time = data.get('birth_time')
    if not has_birth_time:
        if birth_time not in [None, '', 'null']:
            return 'birth_time must be empty if has_birth_time is false', None
    else:
        if birth_time in [None, '', 'null']:
            return 'birth_time is required when has_birth_time is true', None
        time_re = re.compile(r'^(?:[01]\d|2[0-3]):[0-5]\d$')
        if not time_re.match(str(birth_time)):
            return 'birth_time must be in HH:MM 24-hour format', None
    # Segment into 7-day chunks
    segments = []
    seg_start = start
    idx = 1
    while seg_start <= end:
        seg_end = min(seg_start + timedelta(days=6), end)
        segments.append({
            'segment_index': idx,
            'start_date': seg_start.strftime('%Y-%m-%d'),
            'end_date': seg_end.strftime('%Y-%m-%d')
        })
        seg_start = seg_end + timedelta(days=1)
        idx += 1
    return None, segments

# --- Analyze Endpoint ---
@app.route('/api/fortune/analyze', methods=['POST'])
def analyze():
    try:
        data = request.get_json(force=True)
    except BadRequest:
        return jsonify({'error': 'invalid_json', 'message': 'Malformed JSON body'}), 400
    err, segments = validate_and_segment(data)
    if err:
        return jsonify({'error': 'validation_error', 'message': err}), 400
    precision_mode = data.get('precision_mode', 'standard')
    has_birth_time = data.get('has_birth_time', False)
    precision_level = 'medium' if precision_mode == 'standard' and has_birth_time else 'low'
    precision_note = ''
    upgrade_hint = {'show': False, 'title': '', 'content': '', 'affected_dimensions': []}
    if precision_mode == 'standard' and not has_birth_time:
        precision_note = '未提供出生时辰，已降级为大致模式。'
        upgrade_hint = {
            'show': True,
            'title': '建议补充出生时辰',
            'content': '补充出生时辰可提升分析精度，获得更个性化建议。',
            'affected_dimensions': ['work_study', 'finance', 'social', 'health']
        }
    bazi_summary = {
        'year_pillar': '甲子',
        'month_pillar': '乙丑',
        'day_pillar': '丙寅',
        'hour_pillar': None if not has_birth_time else '丁卯'
    }
    wuxing_score = {
        'wood': 70,
        'fire': 60,
        'earth': 50,
        'metal': 40,
        'water': 30
    }
    overall_advice = {
        'suitable': '适合专注学习与自我提升。',
        'avoid': '避免冲动决策与过度劳累。',
        'reminder': '保持平衡，关注身心健康。'
    }
    segs = []
    for seg in segments:
        trend = 'aligned' if seg['segment_index'] % 2 == 1 else 'deviated'
        segs.append({
            'segment_index': seg['segment_index'],
            'start_date': seg['start_date'],
            'end_date': seg['end_date'],
            'trend_alignment': trend,
            'suitable': '本段适合稳步推进计划。',
            'avoid': '避免与人争执。',
            'reminder': '注意作息，适当锻炼。',
            'dimensions': {
                'work_study': 'high' if trend == 'aligned' else 'medium',
                'finance': 'medium',
                'social': 'low' if trend == 'deviated' else 'medium',
                'health': 'medium'
            }
        })
    result = {
        'request_id': str(uuid.uuid4()),
        'disclaimer': '本结果仅供参考，不替代医疗、法律、财务等专业建议。',
        'precision_level': precision_level,
        'precision_note': precision_note,
        'bazi_summary': bazi_summary,
        'wuxing_score': wuxing_score,
        'overall_advice': overall_advice,
        'segments': segs,
        'upgrade_hint': upgrade_hint
    }
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
