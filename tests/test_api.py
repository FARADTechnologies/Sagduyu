import pytest
from fastapi.testclient import TestClient

from sagduyu.api import create_app
from sagduyu.scenarios import coordinated_campaign


def test_health_and_scenario_catalog() -> None:
    with TestClient(create_app()) as client:
        health = client.get("/health")
        scenarios = client.get("/api/v1/scenarios")

    assert health.status_code == 200
    assert health.json() == {
        "status": "ok",
        "engine_version": "0.1.0",
        "moderation_store": "memory",
        "graph_store": "disabled",
    }
    assert scenarios.status_code == 200
    assert scenarios.json() == [
        "announced-campaign",
        "coordinated-campaign",
        "organic-discussion",
    ]


def test_campaign_replay_alert_detail_and_decision_flow() -> None:
    with TestClient(create_app()) as client:
        replay = client.post("/api/v1/replays/coordinated-campaign")
        assert replay.status_code == 200
        replay_body = replay.json()
        assert replay_body["event_count"] == 30
        assert replay_body["alert_count"] == 1

        alert_id = replay_body["alerts"][0]["alert_id"]
        detail = client.get(f"/api/v1/alerts/{alert_id}")
        assert detail.status_code == 200
        assert detail.json()["risk_score"] >= 70

        decision = client.post(
            f"/api/v1/alerts/{alert_id}/decisions",
            json={
                "status": "confirmed",
                "reason": "Zaman ve içerik sinyalleri birlikte güçlü.",
                "reviewer": "test-moderator",
            },
        )
        assert decision.status_code == 201
        assert decision.json()["status"] == "confirmed"

        filtered = client.get("/api/v1/alerts", params={"review_status": "confirmed"})
        assert filtered.status_code == 200
        assert [alert["alert_id"] for alert in filtered.json()] == [alert_id]

        decisions = client.get(f"/api/v1/alerts/{alert_id}/decisions")
        assert decisions.status_code == 200
        assert len(decisions.json()) == 1


def test_new_analysis_does_not_erase_existing_alerts_or_decisions() -> None:
    with TestClient(create_app()) as client:
        campaign = client.post("/api/v1/replays/coordinated-campaign").json()
        alert_id = campaign["alerts"][0]["alert_id"]
        client.post(
            f"/api/v1/alerts/{alert_id}/decisions",
            json={
                "status": "confirmed",
                "reason": "Birden fazla bağımsız sinyal birlikte güçlü.",
                "reviewer": "test-moderator",
            },
        )
        replay = client.post("/api/v1/replays/organic-discussion")
        alerts = client.get("/api/v1/alerts")
        decisions = client.get(f"/api/v1/alerts/{alert_id}/decisions")

    assert replay.status_code == 200
    assert replay.json()["alert_count"] == 0
    assert [alert["alert_id"] for alert in alerts.json()] == [alert_id]
    assert decisions.json()[0]["status"] == "confirmed"


def test_platform_neutral_events_can_be_analyzed() -> None:
    events = [event.model_dump(mode="json") for event in coordinated_campaign()]
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/analyses",
            json={"source_id": "synthetic-adapter", "events": events},
        )

    assert response.status_code == 200
    assert response.json()["source_id"] == "synthetic-adapter"
    assert response.json()["event_count"] == 30
    assert response.json()["alert_count"] == 1


def test_unknown_resources_return_not_found() -> None:
    with TestClient(create_app()) as client:
        scenario = client.post("/api/v1/replays/unknown")
        alert = client.get("/api/v1/alerts/missing")
        decisions = client.get("/api/v1/alerts/missing/decisions")

    assert scenario.status_code == 404
    assert alert.status_code == 404
    assert decisions.status_code == 404


def test_pending_or_empty_decision_is_rejected() -> None:
    with TestClient(create_app()) as client:
        replay = client.post("/api/v1/replays/coordinated-campaign").json()
        alert_id = replay["alerts"][0]["alert_id"]

        pending = client.post(
            f"/api/v1/alerts/{alert_id}/decisions",
            json={"status": "pending", "reason": "Karar yok", "reviewer": "moderator"},
        )
        short_reason = client.post(
            f"/api/v1/alerts/{alert_id}/decisions",
            json={"status": "confirmed", "reason": "x", "reviewer": "moderator"},
        )

    assert pending.status_code == 422
    assert short_reason.status_code == 422


def test_courtesy_check_explains_masking_and_preserves_user_choice() -> None:
    with TestClient(create_app()) as client:
        response = client.post(
            "/api/v1/text/courtesy-check",
            json={"text": "Bu yorum s.4.l.4.k görünüyor."},
        )

    assert response.status_code == 200
    body = response.json()
    assert body["should_warn"] is True
    assert body["user_may_continue"] is True
    assert body["matches"][0]["canonical_form"] == "salak"
    assert body["method"] == "transparent_demo_baseline_v1"


def test_empty_cors_configuration_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAGDUYU_CORS_ORIGINS", ", ,")

    with pytest.raises(ValueError, match="at least one origin"):
        create_app()
