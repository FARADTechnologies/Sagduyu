from __future__ import annotations

import math
import time
from collections import defaultdict
from collections.abc import Sequence
from datetime import UTC, datetime

from pydantic import BaseModel, Field, model_validator

from sagduyu.engine import CoordinationEngine
from sagduyu.models import SocialEvent


class CampaignRecord(BaseModel):
    campaign_id: str = Field(min_length=1, max_length=256)
    split_group: str = Field(min_length=1, max_length=256)
    source: str = Field(min_length=1, max_length=128)
    dataset_version: str = Field(min_length=1, max_length=128)
    is_coordinated_campaign: bool
    events: list[SocialEvent] = Field(min_length=1)

    @model_validator(mode="after")
    def require_single_synthetic_domain(self) -> CampaignRecord:
        synthetic_values = {event.synthetic for event in self.events}
        if len(synthetic_values) != 1:
            raise ValueError("a campaign record cannot mix synthetic and non-synthetic events")
        return self

    @property
    def starts_at(self) -> datetime:
        return min(event.created_at for event in self.events)


class ConfusionMatrix(BaseModel):
    true_positive: int = Field(ge=0)
    true_negative: int = Field(ge=0)
    false_positive: int = Field(ge=0)
    false_negative: int = Field(ge=0)


class EvaluationMetrics(BaseModel):
    macro_f1: float = Field(ge=0.0, le=1.0)
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    false_positive_rate: float = Field(ge=0.0, le=1.0)
    latency_p50_ms: float = Field(ge=0.0)
    latency_p95_ms: float = Field(ge=0.0)


class EvaluationReport(BaseModel):
    generated_at: datetime
    engine_version: str
    source_versions: dict[str, list[str]]
    split: str
    sample_count: int = Field(ge=1)
    synthetic_only: bool
    confusion: ConfusionMatrix
    metrics: EvaluationMetrics


def temporal_group_split(
    records: Sequence[CampaignRecord],
    *,
    test_fraction: float = 0.2,
) -> tuple[list[CampaignRecord], list[CampaignRecord]]:
    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between zero and one")
    by_group: dict[str, list[CampaignRecord]] = defaultdict(list)
    for record in records:
        by_group[record.split_group].append(record)
    if len(by_group) < 2:
        raise ValueError("at least two split groups are required")

    ordered_groups = sorted(
        by_group,
        key=lambda group: (
            min(record.starts_at for record in by_group[group]),
            group,
        ),
    )
    test_group_count = min(
        len(ordered_groups) - 1,
        max(1, math.ceil(len(ordered_groups) * test_fraction)),
    )
    test_groups = set(ordered_groups[-test_group_count:])
    train = [record for record in records if record.split_group not in test_groups]
    test = [record for record in records if record.split_group in test_groups]
    return train, test


def evaluate_campaigns(
    records: Sequence[CampaignRecord],
    *,
    engine: CoordinationEngine | None = None,
    split: str = "external-test",
) -> EvaluationReport:
    if not records:
        raise ValueError("at least one campaign record is required")
    engine_instance = engine or CoordinationEngine()
    tp = tn = fp = fn = 0
    latencies_ms: list[float] = []

    for record in records:
        started = time.perf_counter_ns()
        predicted = bool(engine_instance.analyze(record.events))
        latencies_ms.append((time.perf_counter_ns() - started) / 1_000_000)
        expected = record.is_coordinated_campaign
        if predicted and expected:
            tp += 1
        elif predicted and not expected:
            fp += 1
        elif not predicted and expected:
            fn += 1
        else:
            tn += 1

    precision = _safe_divide(tp, tp + fp)
    recall = _safe_divide(tp, tp + fn)
    negative_precision = _safe_divide(tn, tn + fn)
    negative_recall = _safe_divide(tn, tn + fp)
    positive_f1 = _f1(precision, recall)
    negative_f1 = _f1(negative_precision, negative_recall)
    versions: dict[str, set[str]] = defaultdict(set)
    for record in records:
        versions[record.source].add(record.dataset_version)

    return EvaluationReport(
        generated_at=datetime.now(UTC),
        engine_version=engine_instance.version,
        source_versions={key: sorted(value) for key, value in sorted(versions.items())},
        split=split,
        sample_count=len(records),
        synthetic_only=all(all(event.synthetic for event in record.events) for record in records),
        confusion=ConfusionMatrix(
            true_positive=tp,
            true_negative=tn,
            false_positive=fp,
            false_negative=fn,
        ),
        metrics=EvaluationMetrics(
            macro_f1=round((positive_f1 + negative_f1) / 2, 6),
            precision=round(precision, 6),
            recall=round(recall, 6),
            false_positive_rate=round(_safe_divide(fp, fp + tn), 6),
            latency_p50_ms=round(_percentile(latencies_ms, 0.50), 6),
            latency_p95_ms=round(_percentile(latencies_ms, 0.95), 6),
        ),
    )


def _safe_divide(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _f1(precision: float, recall: float) -> float:
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _percentile(values: Sequence[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    fraction = position - lower
    return ordered[lower] + ((ordered[upper] - ordered[lower]) * fraction)
