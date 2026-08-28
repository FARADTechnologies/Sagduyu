from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from sagduyu.engine import SIGNAL_WEIGHTS, CoordinationEngine
from sagduyu.models import CoordinationContext, EventType, RiskLevel, SocialEvent
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
    assert len(alert.context_evidence) == 1
    evidence = alert.context_evidence[0]
    assert evidence.context_type == "public_announcement"
    assert evidence.account_count == 6
    assert evidence.event_count == 6
    assert evidence.changes_risk_score is False
    assert "risk skorunu değiştirmez" in evidence.explanation


def test_context_metadata_does_not_change_coordination_score() -> None:
    events = announced_campaign()
    without_context = [event.model_copy(update={"coordination_context": None}) for event in events]

    with_context_alert = CoordinationEngine().analyze(events)[0]
    without_context_alert = CoordinationEngine().analyze(without_context)[0]

    assert with_context_alert.risk_score == without_context_alert.risk_score
    assert without_context_alert.context_evidence == []


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


def test_context_source_rejects_non_web_urls() -> None:
    with pytest.raises(ValidationError):
        CoordinationContext(
            context_type="public_announcement",
            label="Şüpheli bağlantı",
            source_url="javascript:alert(1)",
            disclosure_id="unsafe",
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


def test_engine_uses_explicit_signal_weights_in_score_and_evidence() -> None:
    experimental_weights = {
        "temporal": 0.24,
        "content": 0.20,
        "shared_target": 0.20,
        "repetition": 0.20,
        "density": 0.16,
        "deletion": 0.0,
    }

    alert = CoordinationEngine(signal_weights=experimental_weights).analyze(coordinated_campaign())[
        0
    ]

    contributions = {signal.key: signal for signal in alert.signals}
    assert {key: signal.weight for key, signal in contributions.items()} == experimental_weights
    assert contributions["deletion"].contribution == 0.0
    assert sum(signal.contribution for signal in alert.signals) == pytest.approx(
        alert.risk_score,
        abs=0.02,
    )


@pytest.mark.parametrize(
    "signal_weights",
    [
        {key: value for key, value in SIGNAL_WEIGHTS.items() if key != "deletion"},
        {**SIGNAL_WEIGHTS, "unexpected": 0.0},
        {**SIGNAL_WEIGHTS, "temporal": -0.01},
        {**SIGNAL_WEIGHTS, "temporal": 0.30},
    ],
)
def test_invalid_signal_weight_configuration_is_rejected(
    signal_weights: dict[str, float],
) -> None:
    with pytest.raises(ValueError):
        CoordinationEngine(signal_weights=signal_weights)
