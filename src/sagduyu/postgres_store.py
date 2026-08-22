from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from sagduyu.models import (
    CoordinationAlert,
    ModerationDecision,
    ModerationDecisionCreate,
    ReviewStatus,
)
from sagduyu.store import AlertNotFoundError

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS moderation_alerts (
    alert_id TEXT PRIMARY KEY,
    risk_score DOUBLE PRECISION NOT NULL,
    review_status TEXT NOT NULL,
    payload JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS moderation_alerts_priority_idx
    ON moderation_alerts (risk_score DESC, alert_id);
CREATE INDEX IF NOT EXISTS moderation_alerts_status_idx
    ON moderation_alerts (review_status);

CREATE TABLE IF NOT EXISTS moderation_decisions (
    decision_id TEXT PRIMARY KEY,
    alert_id TEXT NOT NULL REFERENCES moderation_alerts(alert_id) ON DELETE RESTRICT,
    decided_at TIMESTAMPTZ NOT NULL,
    payload JSONB NOT NULL
);

CREATE INDEX IF NOT EXISTS moderation_decisions_alert_idx
    ON moderation_decisions (alert_id, decided_at);
"""


class PostgresModerationStore:
    mode = "postgresql"

    def __init__(self, database_url: str, *, initialize: bool = True) -> None:
        self.database_url = database_url
        if initialize:
            self.initialize_schema()

    def initialize_schema(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute(SCHEMA_SQL)

    def upsert_alerts(self, alerts: list[CoordinationAlert]) -> None:
        if not alerts:
            return
        statement = """
            INSERT INTO moderation_alerts (alert_id, risk_score, review_status, payload)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (alert_id) DO UPDATE SET
                risk_score = EXCLUDED.risk_score,
                payload = jsonb_set(
                    EXCLUDED.payload,
                    '{status}',
                    to_jsonb(moderation_alerts.review_status),
                    true
                ),
                updated_at = NOW()
        """
        with (
            psycopg.connect(self.database_url) as connection,
            connection.cursor() as cursor,
        ):
            cursor.executemany(
                statement,
                [
                    (
                        alert.alert_id,
                        alert.risk_score,
                        alert.status.value,
                        Jsonb(alert.model_dump(mode="json")),
                    )
                    for alert in alerts
                ],
            )

    def list_alerts(
        self,
        *,
        min_risk_score: float = 0.0,
        status: ReviewStatus | None = None,
    ) -> list[CoordinationAlert]:
        query = "SELECT payload FROM moderation_alerts WHERE risk_score >= %s"
        parameters: list[object] = [min_risk_score]
        if status is not None:
            query += " AND review_status = %s"
            parameters.append(status.value)
        query += " ORDER BY risk_score DESC, alert_id"
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            rows = connection.execute(query, parameters).fetchall()
        return [CoordinationAlert.model_validate(row["payload"]) for row in rows]

    def get_alert(self, alert_id: str) -> CoordinationAlert:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                "SELECT payload FROM moderation_alerts WHERE alert_id = %s",
                (alert_id,),
            ).fetchone()
        if row is None:
            raise AlertNotFoundError(alert_id)
        return CoordinationAlert.model_validate(row["payload"])

    def add_decision(
        self,
        alert_id: str,
        request: ModerationDecisionCreate,
    ) -> ModerationDecision:
        decision = ModerationDecision(
            decision_id=f"decision_{uuid4().hex}",
            alert_id=alert_id,
            status=request.status,
            reason=request.reason,
            reviewer=request.reviewer,
            decided_at=datetime.now(UTC),
        )
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            exists = connection.execute(
                "SELECT 1 AS present FROM moderation_alerts WHERE alert_id = %s FOR UPDATE",
                (alert_id,),
            ).fetchone()
            if exists is None:
                raise AlertNotFoundError(alert_id)
            connection.execute(
                """
                INSERT INTO moderation_decisions (decision_id, alert_id, decided_at, payload)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    decision.decision_id,
                    alert_id,
                    decision.decided_at,
                    Jsonb(decision.model_dump(mode="json")),
                ),
            )
            connection.execute(
                """
                UPDATE moderation_alerts
                SET review_status = %s,
                    payload = jsonb_set(payload, '{status}', to_jsonb(%s::text), true),
                    updated_at = NOW()
                WHERE alert_id = %s
                """,
                (request.status.value, request.status.value, alert_id),
            )
        return decision

    def list_decisions(self, alert_id: str) -> list[ModerationDecision]:
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            exists = connection.execute(
                "SELECT 1 AS present FROM moderation_alerts WHERE alert_id = %s",
                (alert_id,),
            ).fetchone()
            if exists is None:
                raise AlertNotFoundError(alert_id)
            rows = connection.execute(
                """
                SELECT payload FROM moderation_decisions
                WHERE alert_id = %s ORDER BY decided_at, decision_id
                """,
                (alert_id,),
            ).fetchall()
        return [ModerationDecision.model_validate(row["payload"]) for row in rows]

    def reset(self) -> None:
        with psycopg.connect(self.database_url) as connection:
            connection.execute("TRUNCATE moderation_decisions, moderation_alerts")

    def raw_alert_payload(self, alert_id: str) -> dict[str, Any]:
        """Return the persisted JSON document for integration verification."""
        with psycopg.connect(self.database_url, row_factory=dict_row) as connection:
            row = connection.execute(
                "SELECT payload FROM moderation_alerts WHERE alert_id = %s",
                (alert_id,),
            ).fetchone()
        if row is None:
            raise AlertNotFoundError(alert_id)
        return cast(dict[str, Any], row["payload"])
