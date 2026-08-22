from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sagduyu.engine import CoordinationEngine
from sagduyu.models import EventType, RiskLevel, SocialEvent
from sagduyu.scenarios import announced_campaign, coordinated_campaign, organic_discussion


def test_coordinated_campaign_produces_explainable_high_risk_alert() -> None:
    alerts = CoordinationEngine().analyze(coordinated_campaign())

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    assert alert.risk_score >= 70
    assert len(alert.account_ids) == 8
    assert alert.graph.density == 1.0
    assert alert.synthetic is True
    assert {signal.key for signal in alert.signals} == {
        "temporal",
        "content",
        "shared_target",
        "repetition",
        "density",
        "deletion",
    }
    assert sum(signal.contribution for signal in alert.signals) == pytest.approx(
        alert.risk_score,
        abs=0.02,
    )
    assert alert.targets[0].account_count == 8


def test_organic_discussion_does_not_produce_alert() -> None:
    alerts = CoordinationEngine().analyze(organic_discussion())

    assert alerts == []


def test_announced_campaign_is_flagged_for_review_without_claiming_harm() -> None:
    alerts = CoordinationEngine().analyze(announced_campaign())

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert.synthetic is True
    assert "koordinasyon adayı" in alert.summary
    assert "zararlı" not in alert.summary.lower()


def test_analysis_is_deterministic_for_the_same_events() -> None:
    engine = CoordinationEngine()
    events = coordinated_campaign()

    first = engine.analyze(events)
    second = engine.analyze(list(reversed(events)))

    assert first == second


def test_delete_event_requires_reference() -> None:
    with pytest.raises(ValidationError):
        SocialEvent(
            event_id="delete_without_reference",
            account_id="account_1",
            event_type=EventType.DELETE,
            created_at=datetime.now(UTC),
            synthetic=True,
        )


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("window_seconds", 0),
        ("edge_threshold", 1.1),
        ("min_cluster_size", 1),
        ("min_alert_score", 101.0),
    ],
)
def test_invalid_engine_configuration_is_rejected(argument: str, value: float) -> None:
    with pytest.raises(ValueError):
        CoordinationEngine(**{argument: value})  # type: ignore[arg-type]
