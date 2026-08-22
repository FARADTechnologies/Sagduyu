from datetime import timedelta
from pathlib import Path

import pytest

from sagduyu.adapters.jsonl import CampaignDataError, iter_campaign_records, write_campaign_records
from sagduyu.evaluation import CampaignRecord, evaluate_campaigns, temporal_group_split
from sagduyu.scenarios import announced_campaign, coordinated_campaign, organic_discussion


def _record(
    campaign_id: str,
    *,
    events: list,
    expected: bool,
    day_offset: int = 0,
) -> CampaignRecord:
    shifted_events = [
        event.model_copy(update={"created_at": event.created_at + timedelta(days=day_offset)})
        for event in events
    ]
    return CampaignRecord(
        campaign_id=campaign_id,
        split_group=campaign_id,
        source="synthetic-demo",
        dataset_version="1",
        is_coordinated_campaign=expected,
        events=shifted_events,
    )


def test_evaluation_reports_false_positive_and_versioned_metrics() -> None:
    report = evaluate_campaigns(
        [
            _record("coordinated", events=coordinated_campaign(), expected=True),
            _record("organic", events=organic_discussion(), expected=False),
            _record("announced", events=announced_campaign(), expected=False),
        ],
        split="synthetic-contract-test",
    )

    assert report.sample_count == 3
    assert report.synthetic_only is True
    assert report.engine_version == "0.1.0"
    assert report.source_versions == {"synthetic-demo": ["1"]}
    assert report.confusion.model_dump() == {
        "true_positive": 1,
        "true_negative": 1,
        "false_positive": 1,
        "false_negative": 0,
    }
    assert report.metrics.precision == 0.5
    assert report.metrics.recall == 1.0
    assert report.metrics.false_positive_rate == 0.5
    assert report.metrics.latency_p95_ms >= report.metrics.latency_p50_ms


def test_temporal_split_keeps_groups_disjoint_and_latest_for_test() -> None:
    records = [
        _record(f"group_{index}", events=organic_discussion(), expected=False, day_offset=index)
        for index in range(5)
    ]

    train, test = temporal_group_split(records, test_fraction=0.4)

    assert {record.campaign_id for record in train} == {"group_0", "group_1", "group_2"}
    assert {record.campaign_id for record in test} == {"group_3", "group_4"}
    assert {record.split_group for record in train}.isdisjoint(
        record.split_group for record in test
    )


def test_jsonl_adapter_round_trip_and_duplicate_rejection(tmp_path: Path) -> None:
    record = _record("campaign", events=coordinated_campaign(), expected=True)
    dataset_path = tmp_path / "campaigns.jsonl"
    write_campaign_records(dataset_path, [record])

    assert list(iter_campaign_records(dataset_path)) == [record]

    duplicate_path = tmp_path / "duplicates.jsonl"
    duplicate_path.write_text(
        f"{record.model_dump_json()}\n{record.model_dump_json()}\n",
        encoding="utf-8",
    )
    with pytest.raises(CampaignDataError, match="duplicate campaign_id"):
        list(iter_campaign_records(duplicate_path))


def test_split_rejects_leakage_prone_single_group() -> None:
    record = _record("only", events=organic_discussion(), expected=False)
    with pytest.raises(ValueError, match="at least two split groups"):
        temporal_group_split([record])
