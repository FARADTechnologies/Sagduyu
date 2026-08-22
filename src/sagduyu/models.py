from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, model_validator


class EventType(StrEnum):
    POST = "post"
    RESHARE = "reshare"
    REPLY = "reply"
    MENTION = "mention"
    DELETE = "delete"


class RiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ReviewStatus(StrEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISMISSED = "dismissed"
    NEEDS_MORE_DATA = "needs_more_data"


class SocialEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    event_id: str = Field(min_length=1, max_length=128)
    account_id: str = Field(min_length=1, max_length=128)
    event_type: EventType
    created_at: datetime
    text: str = Field(default="", max_length=10_000)
    target_id: str | None = Field(default=None, max_length=256)
    reference_event_id: str | None = Field(default=None, max_length=128)
    urls: tuple[str, ...] = ()
    hashtags: tuple[str, ...] = ()
    synthetic: bool = False

    @model_validator(mode="after")
    def validate_delete_reference(self) -> SocialEvent:
        if self.event_type is EventType.DELETE and not self.reference_event_id:
            raise ValueError("delete events require reference_event_id")
        return self

    def target_keys(self) -> frozenset[str]:
        targets: set[str] = set()
        if self.target_id:
            targets.add(f"target:{self.target_id}")
        targets.update(f"url:{url.strip().lower()}" for url in self.urls if url.strip())
        targets.update(
            f"tag:{tag.strip().lower().lstrip('#')}" for tag in self.hashtags if tag.strip()
        )
        return frozenset(targets)


class SignalContribution(BaseModel):
    key: str
    label: str
    value: float = Field(ge=0.0, le=1.0)
    weight: float = Field(gt=0.0, le=1.0)
    contribution: float = Field(ge=0.0, le=100.0)
    explanation: str


class TargetEvidence(BaseModel):
    key: str
    event_count: int = Field(ge=1)
    account_count: int = Field(ge=1)


class GraphEvidence(BaseModel):
    node_count: int = Field(ge=1)
    edge_count: int = Field(ge=0)
    density: float = Field(ge=0.0, le=1.0)
    strongest_pairs: list[tuple[str, str, float]]


class CoordinationAlert(BaseModel):
    alert_id: str
    created_at: datetime
    window_start: datetime
    window_end: datetime
    risk_score: float = Field(ge=0.0, le=100.0)
    risk_level: RiskLevel
    summary: str
    account_ids: list[str]
    event_ids: list[str]
    signals: list[SignalContribution]
    targets: list[TargetEvidence]
    graph: GraphEvidence
    status: ReviewStatus = ReviewStatus.PENDING
    synthetic: bool = False
    engine_version: str = "0.1.0"


class ModerationDecisionCreate(BaseModel):
    status: ReviewStatus
    reason: str = Field(min_length=3, max_length=2_000)
    reviewer: str = Field(default="moderator", min_length=1, max_length=128)

    @model_validator(mode="after")
    def reject_pending_status(self) -> ModerationDecisionCreate:
        if self.status is ReviewStatus.PENDING:
            raise ValueError("a moderation decision cannot remain pending")
        return self


class ModerationDecision(BaseModel):
    decision_id: str
    alert_id: str
    status: ReviewStatus
    reason: str
    reviewer: str
    decided_at: datetime


class ReplayResult(BaseModel):
    scenario: str
    event_count: int
    alert_count: int
    alerts: list[CoordinationAlert]


class EventAnalysisRequest(BaseModel):
    source_id: str = Field(min_length=1, max_length=128)
    events: list[SocialEvent] = Field(min_length=1, max_length=10_000)


class EventAnalysisResult(BaseModel):
    source_id: str
    event_count: int
    alert_count: int
    alerts: list[CoordinationAlert]
