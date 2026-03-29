def test_invalid_gender(client):
    payload = valid_payload(gender='invalid')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'gender' in data['message']

def test_invalid_calendar_type(client):
    payload = valid_payload(calendar_type='gregorian')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'calendar_type' in data['message']

def test_invalid_precision_mode(client):
    payload = valid_payload(precision_mode='super')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'precision_mode' in data['message']

def test_invalid_birth_date_format(client):
    payload = valid_payload(birth_date='01-01-2000')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'birth_date' in data['message']

def test_invalid_birth_time_format(client):
    payload = valid_payload(has_birth_time=True, birth_time='25:61')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'validation_error'
    assert 'birth_time' in data['message']

def test_malformed_json_returns_json_error(client):
    # Send invalid JSON (not using json=, but data= and wrong content-type)
    resp = client.post('/api/fortune/analyze', data='{bad json}', content_type='application/json')
    assert resp.status_code == 400
    data = resp.get_json()
    assert data['error'] == 'invalid_json'
    assert 'Malformed JSON' in data['message']

import sys
import os
import pytest
from flask import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_endpoint(client):
    resp = client.get('/api/fortune/health')
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'status' in data and data['status'] == 'ok'
    assert 'service' in data and data['service'] == 'hxz-fortune'
    assert 'version' in data and data['version'] == 'v1.1.0'

def valid_payload(**overrides):
    base = {
        'gender': 'male',
        'calendar_type': 'solar',
        'birth_date': '2000-01-01',
        'has_birth_time': True,
        'birth_time': '12:00',
        'start_date': '2023-01-01',
        'end_date': '2023-01-30',
        'precision_mode': 'standard'
    }
    base.update(overrides)
    return base

def test_analyze_valid(client):
    resp = client.post('/api/fortune/analyze', json=valid_payload())
    assert resp.status_code == 200
    data = resp.get_json()
    for key in ['request_id','disclaimer','precision_level','bazi_summary','wuxing_score','overall_advice','segments','upgrade_hint']:
        assert key in data
    assert isinstance(data['segments'], list) and len(data['segments']) > 0

def test_missing_required_fields(client):
    for field in ['gender','calendar_type','birth_date','start_date','end_date']:
        payload = valid_payload()
        del payload[field]
        resp = client.post('/api/fortune/analyze', json=payload)
        assert resp.status_code == 400
        data = resp.get_json()
        assert data['error'] == 'validation_error'
        assert 'Missing required field' in data['message']

def test_birth_time_provided_when_flag_false(client):
    payload = valid_payload(has_birth_time=False, birth_time='12:00')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'birth_time must be empty' in data['message']

def test_start_date_after_end_date(client):
    payload = valid_payload(start_date='2023-02-01', end_date='2023-01-01')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'start_date must be before' in data['message']

def test_date_span_exceeds_180_days(client):
    payload = valid_payload(start_date='2023-01-01', end_date='2023-08-01')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 400
    data = resp.get_json()
    assert 'Date range cannot exceed' in data['message']

def test_precision_downgrade_and_upgrade_hint(client):
    payload = valid_payload(has_birth_time=False, birth_time=None, precision_mode='standard')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['precision_level'] == 'low'
    assert data['upgrade_hint']['show'] is True
    assert data['precision_note']

def test_segmentation_7_day_chunks(client):
    payload = valid_payload(start_date='2023-01-01', end_date='2023-01-30')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    segments = data['segments']
    assert len(segments) == 5  # 4x7 + 1x2 days
    for seg in segments[:-1]:
        sd = seg['start_date']
        ed = seg['end_date']
        d1 = (int(ed[-2:]) - int(sd[-2:]) + 1)
        assert d1 == 7
    last = segments[-1]
    sd = last['start_date']
    ed = last['end_date']
    d1 = (int(ed[-2:]) - int(sd[-2:]) + 1)
    assert d1 <= 7

def test_segment_trend_field(client):
    payload = valid_payload(start_date='2023-01-01', end_date='2023-01-30')
    resp = client.post('/api/fortune/analyze', json=payload)
    assert resp.status_code == 200
    data = resp.get_json()
    for seg in data['segments']:
        assert seg['trend_alignment'] in ['aligned','deviated']
