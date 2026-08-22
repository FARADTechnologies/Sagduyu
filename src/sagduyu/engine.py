from __future__ import annotations

import hashlib
import math
import re
import unicodedata
from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from itertools import combinations

from sagduyu.models import (
    CoordinationAlert,
    EventType,
    GraphEvidence,
    RiskLevel,
    SignalContribution,
    SocialEvent,
    TargetEvidence,
)

ACTIVE_EVENT_TYPES = {
    EventType.POST,
    EventType.RESHARE,
    EventType.REPLY,
    EventType.MENTION,
}

SIGNAL_WEIGHTS: dict[str, float] = {
    "temporal": 0.22,
    "content": 0.18,
    "shared_target": 0.18,
    "repetition": 0.18,
    "density": 0.14,
    "deletion": 0.10,
}

SIGNAL_LABELS: dict[str, str] = {
    "temporal": "Eşzamanlılık",
    "content": "İçerik benzerliği",
    "shared_target": "Ortak hedef yoğunluğu",
    "repetition": "Tekrarlanan birlikte hareket",
    "density": "Ağ yoğunluğu",
    "deletion": "Toplu silme davranışı",
}


@dataclass(frozen=True, slots=True)
class _PairEvidence:
    left: str
    right: str
    temporal: float
    shared_target: float
    content: float
    repetition: float
    strength: float
    shared_targets: frozenset[str]


class CoordinationEngine:
    """Build explainable coordination candidates from platform-neutral events."""

    version = "0.1.0"

    def __init__(
        self,
        *,
        window_seconds: int = 300,
        edge_threshold: float = 0.70,
        min_cluster_size: int = 3,
        min_alert_score: float = 55.0,
    ) -> None:
        if window_seconds <= 0:
            raise ValueError("window_seconds must be positive")
        if not 0.0 <= edge_threshold <= 1.0:
            raise ValueError("edge_threshold must be between zero and one")
        if min_cluster_size < 2:
            raise ValueError("min_cluster_size must be at least two")
        if not 0.0 <= min_alert_score <= 100.0:
            raise ValueError("min_alert_score must be between zero and one hundred")

        self.window_seconds = window_seconds
        self.edge_threshold = edge_threshold
        self.min_cluster_size = min_cluster_size
        self.min_alert_score = min_alert_score

    def analyze(self, events: Sequence[SocialEvent]) -> list[CoordinationAlert]:
        ordered_events = sorted(
            events,
            key=lambda event: (_as_utc(event.created_at), event.event_id),
        )
        active_events = [
            event for event in ordered_events if event.event_type in ACTIVE_EVENT_TYPES
        ]
        if len(active_events) < self.min_cluster_size:
            return []

        events_by_account: dict[str, list[SocialEvent]] = defaultdict(list)
        for event in active_events:
            events_by_account[event.account_id].append(event)

        account_ids = sorted(events_by_account)
        adjacency: dict[str, set[str]] = {account_id: set() for account_id in account_ids}
        edges: dict[tuple[str, str], _PairEvidence] = {}

        for left, right in combinations(account_ids, 2):
            evidence = self._pair_evidence(
                left,
                right,
                events_by_account[left],
                events_by_account[right],
            )
            if evidence.strength < self.edge_threshold:
                continue
            adjacency[left].add(right)
            adjacency[right].add(left)
            edges[(left, right)] = evidence

        deleted_event_ids = {
            event.reference_event_id
            for event in ordered_events
            if event.event_type is EventType.DELETE and event.reference_event_id
        }

        alerts: list[CoordinationAlert] = []
        for component in _connected_components(adjacency):
            if len(component) < self.min_cluster_size:
                continue
            component_events = [event for event in active_events if event.account_id in component]
            component_edges = {
                pair: evidence
                for pair, evidence in edges.items()
                if pair[0] in component and pair[1] in component
            }
            alert = self._build_alert(
                component,
                component_events,
                component_edges,
                deleted_event_ids,
            )
            if alert.risk_score >= self.min_alert_score:
                alerts.append(alert)

        return sorted(alerts, key=lambda alert: (-alert.risk_score, alert.alert_id))

    def _pair_evidence(
        self,
        left: str,
        right: str,
        left_events: Sequence[SocialEvent],
        right_events: Sequence[SocialEvent],
    ) -> _PairEvidence:
        min_delta = math.inf
        max_content_similarity = 0.0
        shared_targets: set[str] = set()

        left_targets = set().union(*(event.target_keys() for event in left_events))
        right_targets = set().union(*(event.target_keys() for event in right_events))
        shared_targets.update(left_targets & right_targets)

        for left_event in left_events:
            for right_event in right_events:
                delta = abs(
                    (
                        _as_utc(left_event.created_at) - _as_utc(right_event.created_at)
                    ).total_seconds()
                )
                min_delta = min(min_delta, delta)
                if delta <= self.window_seconds:
                    max_content_similarity = max(
                        max_content_similarity,
                        _text_similarity(left_event.text, right_event.text),
                    )

        temporal = max(0.0, 1.0 - (min_delta / self.window_seconds))
        shared_target = 1.0 if shared_targets else 0.0
        repetition = min(1.0, max(0, len(shared_targets) - 1) / 2)
        strength = (
            (0.30 * temporal)
            + (0.30 * shared_target)
            + (0.25 * max_content_similarity)
            + (0.15 * repetition)
        )

        return _PairEvidence(
            left=left,
            right=right,
            temporal=round(temporal, 6),
            shared_target=shared_target,
            content=round(max_content_similarity, 6),
            repetition=round(repetition, 6),
            strength=round(strength, 6),
            shared_targets=frozenset(shared_targets),
        )

    def _build_alert(
        self,
        component: set[str],
        events: Sequence[SocialEvent],
        edges: dict[tuple[str, str], _PairEvidence],
        deleted_event_ids: set[str],
    ) -> CoordinationAlert:
        target_participants: dict[str, set[str]] = defaultdict(set)
        target_events: dict[str, list[SocialEvent]] = defaultdict(list)
        for event in events:
            for target in event.target_keys():
                target_participants[target].add(event.account_id)
                target_events[target].append(event)

        temporal_values: list[float] = []
        target_values: list[float] = []
        for target, participants in target_participants.items():
            if len(participants) < 2:
                continue
            target_values.append(len(participants) / len(component))
            timestamps = [_as_utc(event.created_at) for event in target_events[target]]
            span = (max(timestamps) - min(timestamps)).total_seconds()
            temporal_values.append(max(0.0, 1.0 - (span / self.window_seconds)))

        possible_edges = len(component) * (len(component) - 1) / 2
        density = len(edges) / possible_edges if possible_edges else 0.0
        content = _mean(evidence.content for evidence in edges.values())
        repetition = _mean(evidence.repetition for evidence in edges.values())
        temporal = _mean(temporal_values)
        shared_target = _mean(sorted(target_values, reverse=True)[:3])
        deletion = sum(event.event_id in deleted_event_ids for event in events) / len(events)

        signal_values = {
            "temporal": temporal,
            "content": content,
            "shared_target": shared_target,
            "repetition": repetition,
            "density": density,
            "deletion": deletion,
        }
        risk_score = round(
            sum(signal_values[key] * weight for key, weight in SIGNAL_WEIGHTS.items()) * 100,
            2,
        )

        ordered_accounts = sorted(component)
        ordered_events = sorted(
            events,
            key=lambda event: (_as_utc(event.created_at), event.event_id),
        )
        alert_id = _stable_alert_id(ordered_accounts, [event.event_id for event in ordered_events])
        targets = sorted(
            (
                TargetEvidence(
                    key=target,
                    event_count=len(target_events[target]),
                    account_count=len(participants),
                )
                for target, participants in target_participants.items()
                if len(participants) >= 2
            ),
            key=lambda item: (-item.account_count, -item.event_count, item.key),
        )[:10]
        strongest_pairs = sorted(
            ((evidence.left, evidence.right, evidence.strength) for evidence in edges.values()),
            key=lambda pair: (-pair[2], pair[0], pair[1]),
        )[:12]

        return CoordinationAlert(
            alert_id=alert_id,
            created_at=ordered_events[-1].created_at,
            window_start=ordered_events[0].created_at,
            window_end=ordered_events[-1].created_at,
            risk_score=risk_score,
            risk_level=_risk_level(risk_score),
            summary=(
                f"{len(component)} hesap, {len(events)} olay ve "
                f"{len(targets)} ortak hedefte koordinasyon adayı oluşturdu."
            ),
            account_ids=ordered_accounts,
            event_ids=[event.event_id for event in ordered_events],
            signals=[_signal_contribution(key, signal_values[key]) for key in SIGNAL_WEIGHTS],
            targets=targets,
            graph=GraphEvidence(
                node_count=len(component),
                edge_count=len(edges),
                density=round(density, 6),
                strongest_pairs=strongest_pairs,
            ),
            synthetic=all(event.synthetic for event in ordered_events),
            engine_version=self.version,
        )


def _connected_components(adjacency: dict[str, set[str]]) -> list[set[str]]:
    components: list[set[str]] = []
    unseen = set(adjacency)
    while unseen:
        start = min(unseen)
        stack = [start]
        component: set[str] = set()
        while stack:
            node = stack.pop()
            if node in component:
                continue
            component.add(node)
            unseen.discard(node)
            stack.extend(sorted(adjacency[node] - component, reverse=True))
        components.append(component)
    return components


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _normalize_text(value: str) -> str:
    lowered = value.lower()
    for source, replacement in (
        ("ı", "i"),
        ("ğ", "g"),
        ("ü", "u"),
        ("ş", "s"),
        ("ö", "o"),
        ("ç", "c"),
    ):
        lowered = lowered.replace(source, replacement)
    decomposed = unicodedata.normalize("NFKD", lowered)
    without_urls = re.sub(r"https?://\S+", " ", decomposed)
    return " ".join(re.findall(r"[a-z0-9]+", without_urls))


def _text_similarity(left: str, right: str) -> float:
    left_tokens = set(_normalize_text(left).split())
    right_tokens = set(_normalize_text(right).split())
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)


def _mean(values: Iterable[float]) -> float:
    collected = list(values)
    return sum(collected) / len(collected) if collected else 0.0


def _risk_level(score: float) -> RiskLevel:
    if score >= 85.0:
        return RiskLevel.CRITICAL
    if score >= 70.0:
        return RiskLevel.HIGH
    if score >= 55.0:
        return RiskLevel.MEDIUM
    return RiskLevel.LOW


def _stable_alert_id(account_ids: Sequence[str], event_ids: Sequence[str]) -> str:
    payload = "|".join([*account_ids, "::", *event_ids]).encode()
    return f"alert_{hashlib.sha256(payload).hexdigest()[:16]}"


def _signal_contribution(key: str, value: float) -> SignalContribution:
    weight = SIGNAL_WEIGHTS[key]
    rounded_value = round(max(0.0, min(1.0, value)), 6)
    contribution = round(rounded_value * weight * 100, 2)
    explanations = {
        "temporal": "Ortak hedeflerdeki hareketlerin kısa zaman aralıklarında kümelenme düzeyi.",
        "content": "Bağlantılı hesapların metinlerindeki sözcük örtüşmesi.",
        "shared_target": "Aynı hedeflere yönelen hesapların küme içindeki payı.",
        "repetition": "Aynı hesap çiftlerinin birden fazla hedefte birlikte hareket etmesi.",
        "density": "Aday kümedeki güçlü hesap bağlantılarının olası bağlantılara oranı.",
        "deletion": "Aday kümedeki olayların sonradan silinme oranı.",
    }
    return SignalContribution(
        key=key,
        label=SIGNAL_LABELS[key],
        value=rounded_value,
        weight=weight,
        contribution=contribution,
        explanation=explanations[key],
    )
