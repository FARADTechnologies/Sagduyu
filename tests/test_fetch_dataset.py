import json
from pathlib import Path

import pytest

from scripts.fetch_dataset import SourceConfig, fetch_source, load_sources
from scripts.profile_ephemeral_annotations import profile_annotations


def test_manifest_sources_have_safe_unique_filenames() -> None:
    sources = load_sources(Path("configs/data-sources.toml"))

    assert {"ephemeral_annotations", "ephemeral_trends", "len_metadata", "len_small"} <= set(
        sources
    )
    filenames = [source["filename"] for source in sources.values()]
    assert len(filenames) == len(set(filenames))
    assert all(Path(filename).name == filename for filename in filenames)


def test_fetch_source_records_integrity_metadata(tmp_path: Path) -> None:
    payload = tmp_path / "fixture.csv"
    payload.write_text("campaign,label\ndemo,1\n", encoding="utf-8")
    output = tmp_path / "raw"
    source = SourceConfig(
        description="Test fixture",
        url=payload.as_uri(),
        filename="downloaded.csv",
        license="Test only",
    )

    destination = fetch_source("fixture", source, output)
    metadata = json.loads(destination.with_suffix(".csv.metadata.json").read_text(encoding="utf-8"))

    assert destination.read_bytes() == payload.read_bytes()
    assert metadata["source"] == "fixture"
    assert metadata["bytes"] == len(payload.read_bytes())
    assert len(metadata["sha256"]) == 64


def test_fetch_source_rejects_invalid_attempt_count(tmp_path: Path) -> None:
    source = SourceConfig(
        description="Test fixture",
        url=(tmp_path / "missing.csv").as_uri(),
        filename="downloaded.csv",
        license="Test only",
    )
    with pytest.raises(ValueError, match="attempts must be positive"):
        fetch_source("fixture", source, tmp_path / "raw", attempts=0)


def test_ephemeral_profile_is_aggregate_and_records_input_limit(tmp_path: Path) -> None:
    source = tmp_path / "annotations.csv"
    source.write_text(
        "id,tweet_type,attack_annotation\n1,tweet,1\n2,retweet,0\n2,retweet,0\n",
        encoding="utf-8",
    )

    profile = profile_annotations(source)

    assert profile["row_count"] == 3
    assert profile["unique_id_count"] == 2
    assert profile["duplicate_id_count"] == 1
    assert profile["annotation_distribution"] == {"0": 2, "1": 1}
    assert profile["contains_event_text"] is False
    assert profile["model_input_ready"] is False
