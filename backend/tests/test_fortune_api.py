import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def valid_payload(**overrides):
    payload = {
        "gender": "male",
        "calendar_type": "solar",
        "birth_date": "2000-01-01",
        "has_birth_time": True,
        "birth_time": "12:00",
        "start_date": "2023-01-01",
        "end_date": "2023-01-30",
        "precision_mode": "standard",
    }
    payload.update(overrides)
    return payload


def test_health_endpoint(client):
    response = client.get("/api/fortune/health")

    assert response.status_code == 200
    data = response.get_json()
    assert data["status"] == "ok"
    assert data["service"] == "hxz-fortune"
    assert data["version"] == "v1.1.1"


def test_analyze_valid(client):
    response = client.post("/api/fortune/analyze", json=valid_payload())

    assert response.status_code == 200
    data = response.get_json()

    for key in [
        "request_id",
        "disclaimer",
        "precision_level",
        "precision_note",
        "bazi_summary",
        "wuxing_score",
        "overall_advice",
        "segments",
        "upgrade_hint",
    ]:
        assert key in data

    assert isinstance(data["segments"], list) and data["segments"]
    assert "参考" in data["disclaimer"]
    assert data["bazi_summary"]["year_pillar"] == "甲子"
    assert "适合" in data["overall_advice"]["suitable"]


def test_chinese_result_copy_regression(client):
    response = client.post("/api/fortune/analyze", json=valid_payload())

    assert response.status_code == 200
    data = response.get_json()

    assert "参考" in data["disclaimer"]
    assert "适合" in data["overall_advice"]["suitable"]
    assert "避免" in data["overall_advice"]["avoid"]
    assert "提醒" in data["overall_advice"]["reminder"]
    assert data["segments"][0]["suitable"].startswith("这段时间适合")
    assert data["segments"][0]["avoid"].startswith("避免")
    assert data["segments"][0]["reminder"].startswith("留意")


def test_missing_required_fields(client):
    for field in ["gender", "calendar_type", "birth_date", "start_date", "end_date"]:
        payload = valid_payload()
        del payload[field]

        response = client.post("/api/fortune/analyze", json=payload)

        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "validation_error"
        assert "Missing required field" in data["message"]


def test_invalid_gender(client):
    response = client.post("/api/fortune/analyze", json=valid_payload(gender="invalid"))

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "gender" in data["message"]


def test_invalid_calendar_type(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(calendar_type="gregorian"),
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "calendar_type" in data["message"]


def test_invalid_precision_mode(client):
    response = client.post("/api/fortune/analyze", json=valid_payload(precision_mode="super"))

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "precision_mode" in data["message"]


def test_invalid_birth_date_format(client):
    response = client.post("/api/fortune/analyze", json=valid_payload(birth_date="01-01-2000"))

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "birth_date" in data["message"]


def test_invalid_birth_time_format(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(has_birth_time=True, birth_time="25:61"),
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "validation_error"
    assert "birth_time" in data["message"]


def test_malformed_json_returns_json_error(client):
    response = client.post(
        "/api/fortune/analyze",
        data="{bad json}",
        content_type="application/json",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["error"] == "invalid_json"
    assert "Malformed JSON" in data["message"]


def test_birth_time_provided_when_flag_false(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(has_birth_time=False, birth_time="12:00"),
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "birth_time must be empty" in data["message"]


def test_start_date_after_end_date(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(start_date="2023-02-01", end_date="2023-01-01"),
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "start_date must be before" in data["message"]


def test_date_span_exceeds_180_days(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(start_date="2023-01-01", end_date="2023-08-01"),
    )

    assert response.status_code == 400
    data = response.get_json()
    assert "Date range cannot exceed" in data["message"]


def test_precision_downgrade_and_upgrade_hint(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(has_birth_time=False, birth_time=None, precision_mode="standard"),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["precision_level"] == "low"
    assert data["upgrade_hint"]["show"] is True
    assert "出生时辰" in data["precision_note"]
    assert "补充出生时辰" in data["upgrade_hint"]["title"]
    assert "更精细" in data["upgrade_hint"]["content"]


def test_approx_mode_without_birth_time_has_no_upgrade_hint(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(has_birth_time=False, birth_time=None, precision_mode="approx"),
    )

    assert response.status_code == 200
    data = response.get_json()
    assert data["precision_level"] == "low"
    assert data["precision_note"] == ""
    assert data["upgrade_hint"]["show"] is False


def test_segmentation_7_day_chunks(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(start_date="2023-01-01", end_date="2023-01-30"),
    )

    assert response.status_code == 200
    data = response.get_json()
    segments = data["segments"]
    assert len(segments) == 5

    for segment in segments[:-1]:
        day_count = int(segment["end_date"][-2:]) - int(segment["start_date"][-2:]) + 1
        assert day_count == 7

    last_segment = segments[-1]
    last_day_count = int(last_segment["end_date"][-2:]) - int(last_segment["start_date"][-2:]) + 1
    assert last_day_count <= 7


def test_segment_trend_field(client):
    response = client.post(
        "/api/fortune/analyze",
        json=valid_payload(start_date="2023-01-01", end_date="2023-01-30"),
    )

    assert response.status_code == 200
    data = response.get_json()
    for segment in data["segments"]:
        assert segment["trend_alignment"] in ["aligned", "deviated"]
