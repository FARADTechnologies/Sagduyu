from __future__ import annotations

import argparse
import json
import math
import platform
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from fastapi.testclient import TestClient

from sagduyu.api import create_app

SCENARIO_EXPECTATIONS = {
    "coordinated-campaign": {"event_count": 30, "alert_count": 1},
    "organic-discussion": {"event_count": 12, "alert_count": 0},
    "announced-campaign": {"event_count": 6, "alert_count": 1},
}


def collect_demo_evidence(*, repetitions: int = 30) -> dict[str, Any]:
    if repetitions < 5:
        raise ValueError("repetitions must be at least five")

    with TestClient(create_app()) as client:
        health = _successful_json(client.get("/health"), "health")
        scenarios: dict[str, dict[str, Any]] = {}
        for name, expected in SCENARIO_EXPECTATIONS.items():
            payload = _successful_json(client.post(f"/api/v1/replays/{name}"), name)
            actual = {
                "event_count": payload["event_count"],
                "alert_count": payload["alert_count"],
            }
            if actual != expected:
                raise RuntimeError(f"{name} expectation failed: {actual!r} != {expected!r}")

            summary: dict[str, Any] = {**actual, "expectation_passed": True}
            if payload["alerts"]:
                alert = payload["alerts"][0]
                summary.update(
                    risk_score=alert["risk_score"],
                    risk_level=alert["risk_level"],
                    graph_nodes=alert["graph"]["node_count"],
                    graph_edges=alert["graph"]["edge_count"],
                    context_evidence_count=len(alert["context_evidence"]),
                )
            scenarios[name] = summary

        coordinated = _successful_json(
            client.post("/api/v1/replays/coordinated-campaign"),
            "coordinated decision replay",
        )
        alert_id = coordinated["alerts"][0]["alert_id"]
        decision = _successful_json(
            client.post(
                f"/api/v1/alerts/{alert_id}/decisions",
                json={
                    "status": "confirmed",
                    "reason": "Çoklu davranış sinyalleri birlikte incelendi.",
                    "reviewer": "demo-moderator",
                },
            ),
            "moderation decision",
        )
        courtesy = _successful_json(
            client.post(
                "/api/v1/text/courtesy-check",
                json={"text": "Bu fikri s 4 l 4 k buluyorum."},
            ),
            "courtesy check",
        )

        latencies_ms = []
        for _ in range(repetitions):
            started = perf_counter()
            response = client.post("/api/v1/replays/coordinated-campaign")
            latencies_ms.append((perf_counter() - started) * 1_000)
            _successful_json(response, "latency replay")

    ordered_latencies = sorted(latencies_ms)
    return {
        "schema_version": "1.0",
        "generated_at": datetime.now(UTC).isoformat(),
        "environment": {
            "execution_mode": "in_process_test_client",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "engine_version": health["engine_version"],
            "moderation_store": health["moderation_store"],
            "graph_store": health["graph_store"],
        },
        "scenarios": scenarios,
        "moderation_decision": {
            "status": decision["status"],
            "audit_record_created": bool(decision["decision_id"]),
        },
        "courtesy": {
            "should_warn": courtesy["should_warn"],
            "canonical_forms": [match["canonical_form"] for match in courtesy["matches"]],
            "user_may_continue": courtesy["user_may_continue"],
        },
        "latency_ms": {
            "repetitions": repetitions,
            "p50": round(_percentile(ordered_latencies, 0.50), 3),
            "p95": round(_percentile(ordered_latencies, 0.95), 3),
            "maximum": round(ordered_latencies[-1], 3),
            "scope": "local smoke measurement; not a production load test",
        },
        "privacy": {
            "contains_raw_events": False,
            "contains_personal_data": False,
            "contains_secrets": False,
        },
    }


def _successful_json(response: Any, step: str) -> dict[str, Any]:
    if response.status_code not in {200, 201}:
        raise RuntimeError(f"{step} failed with HTTP {response.status_code}")
    payload = response.json()
    if not isinstance(payload, dict):
        raise RuntimeError(f"{step} returned a non-object payload")
    return payload


def _percentile(ordered_values: list[float], quantile: float) -> float:
    index = max(
        0,
        min(len(ordered_values) - 1, math.ceil(len(ordered_values) * quantile) - 1),
    )
    return ordered_values[index]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify the end-to-end demo and write aggregate evidence."
    )
    parser.add_argument("--repetitions", type=int, default=30)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    evidence = collect_demo_evidence(repetitions=args.repetitions)
    rendered = json.dumps(evidence, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(f"{rendered}\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
