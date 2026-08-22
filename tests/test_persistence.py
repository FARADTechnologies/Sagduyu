import os

import pytest

from sagduyu.engine import CoordinationEngine
from sagduyu.models import ModerationDecisionCreate, ReviewStatus
from sagduyu.persistence import build_graph_writer, build_moderation_store
from sagduyu.postgres_store import PostgresModerationStore
from sagduyu.scenarios import coordinated_campaign
from sagduyu.store import InMemoryModerationStore


def test_environment_builders_default_to_local_safe_adapters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("SAGDUYU_DATABASE_URL", raising=False)
    monkeypatch.delenv("SAGDUYU_NEO4J_URI", raising=False)

    store = build_moderation_store()
    graph_writer = build_graph_writer()

    assert isinstance(store, InMemoryModerationStore)
    assert store.mode == "memory"
    assert graph_writer.mode == "disabled"


def test_incomplete_neo4j_configuration_is_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("SAGDUYU_NEO4J_URI", "bolt://localhost:7687")
    monkeypatch.delenv("SAGDUYU_NEO4J_USERNAME", raising=False)
    monkeypatch.delenv("SAGDUYU_NEO4J_PASSWORD", raising=False)

    with pytest.raises(ValueError, match="username and password"):
        build_graph_writer()


@pytest.mark.skipif(
    "SAGDUYU_TEST_DATABASE_URL" not in os.environ,
    reason="PostgreSQL integration URL is not configured",
)
def test_postgres_store_preserves_decision_audit_on_reanalysis() -> None:
    database_url = os.environ["SAGDUYU_TEST_DATABASE_URL"]
    store = PostgresModerationStore(database_url)
    store.reset()
    alert = CoordinationEngine().analyze(coordinated_campaign())[0]

    store.upsert_alerts([alert])
    store.add_decision(
        alert.alert_id,
        ModerationDecisionCreate(
            status=ReviewStatus.CONFIRMED,
            reason="Bağımsız koordinasyon sinyalleri birlikte güçlü.",
            reviewer="integration-test",
        ),
    )
    store.upsert_alerts([alert])

    assert store.get_alert(alert.alert_id).status is ReviewStatus.CONFIRMED
    assert len(store.list_decisions(alert.alert_id)) == 1
    assert store.raw_alert_payload(alert.alert_id)["status"] == "confirmed"
    store.reset()
