from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from uuid import uuid4

from sagduyu.models import (
    CoordinationAlert,
    ModerationDecision,
    ModerationDecisionCreate,
    ReviewStatus,
)


class AlertNotFoundError(LookupError):
    pass


class InMemoryModerationStore:
    """Thread-safe prototype store behind a replaceable persistence boundary."""

    def __init__(self) -> None:
        self._alerts: dict[str, CoordinationAlert] = {}
        self._decisions: dict[str, list[ModerationDecision]] = {}
        self._lock = RLock()

    def upsert_alerts(self, alerts: list[CoordinationAlert]) -> None:
        """Add newly produced alerts without discarding the review audit trail."""
        with self._lock:
            for alert in alerts:
                existing = self._alerts.get(alert.alert_id)
                if existing is not None:
                    alert = alert.model_copy(update={"status": existing.status})
                self._alerts[alert.alert_id] = alert

    def list_alerts(
        self,
        *,
        min_risk_score: float = 0.0,
        status: ReviewStatus | None = None,
    ) -> list[CoordinationAlert]:
        with self._lock:
            alerts = [
                alert
                for alert in self._alerts.values()
                if alert.risk_score >= min_risk_score and (status is None or alert.status is status)
            ]
            return sorted(alerts, key=lambda alert: (-alert.risk_score, alert.alert_id))

    def get_alert(self, alert_id: str) -> CoordinationAlert:
        with self._lock:
            try:
                return self._alerts[alert_id]
            except KeyError as error:
                raise AlertNotFoundError(alert_id) from error

    def add_decision(
        self,
        alert_id: str,
        request: ModerationDecisionCreate,
    ) -> ModerationDecision:
        with self._lock:
            alert = self.get_alert(alert_id)
            decision = ModerationDecision(
                decision_id=f"decision_{uuid4().hex}",
                alert_id=alert_id,
                status=request.status,
                reason=request.reason,
                reviewer=request.reviewer,
                decided_at=datetime.now(UTC),
            )
            self._decisions.setdefault(alert_id, []).append(decision)
            self._alerts[alert_id] = alert.model_copy(update={"status": request.status})
            return decision

    def list_decisions(self, alert_id: str) -> list[ModerationDecision]:
        with self._lock:
            self.get_alert(alert_id)
            return list(self._decisions.get(alert_id, []))

    def reset(self) -> None:
        with self._lock:
            self._alerts.clear()
            self._decisions.clear()
