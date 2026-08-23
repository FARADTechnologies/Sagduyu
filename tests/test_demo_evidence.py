from scripts.run_demo_evidence import collect_demo_evidence


def test_demo_evidence_checks_all_product_paths_without_raw_data() -> None:
    evidence = collect_demo_evidence(repetitions=5)

    assert evidence["scenarios"]["coordinated-campaign"]["alert_count"] == 1
    assert evidence["scenarios"]["organic-discussion"]["alert_count"] == 0
    announced = evidence["scenarios"]["announced-campaign"]
    assert announced["context_evidence_count"] == 1
    assert evidence["moderation_decision"]["audit_record_created"] is True
    assert evidence["courtesy"] == {
        "should_warn": True,
        "canonical_forms": ["salak"],
        "user_may_continue": True,
    }
    assert evidence["latency_ms"]["repetitions"] == 5
    assert evidence["latency_ms"]["p95"] >= 0
    assert evidence["privacy"] == {
        "contains_raw_events": False,
        "contains_personal_data": False,
        "contains_secrets": False,
    }
