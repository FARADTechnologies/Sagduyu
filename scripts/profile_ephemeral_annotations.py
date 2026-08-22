from __future__ import annotations

import argparse
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

REQUIRED_COLUMNS = {"id", "tweet_type", "attack_annotation"}


def profile_annotations(input_path: Path) -> dict[str, object]:
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    annotation_counts: Counter[str] = Counter()
    tweet_type_counts: Counter[str] = Counter()
    seen_ids: set[str] = set()
    duplicate_count = 0

    with input_path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"missing required columns: {', '.join(sorted(missing))}")
        for row in reader:
            tweet_id = row["id"].strip()
            if not tweet_id:
                raise ValueError("empty tweet id")
            if tweet_id in seen_ids:
                duplicate_count += 1
            seen_ids.add(tweet_id)
            annotation_counts[row["attack_annotation"].strip()] += 1
            tweet_type_counts[row["tweet_type"].strip()] += 1

    return {
        "schema_version": "1",
        "source_filename": input_path.name,
        "source_sha256": digest,
        "row_count": sum(annotation_counts.values()),
        "unique_id_count": len(seen_ids),
        "duplicate_id_count": duplicate_count,
        "annotation_distribution": dict(sorted(annotation_counts.items())),
        "tweet_type_distribution": dict(sorted(tweet_type_counts.items())),
        "contains_event_text": False,
        "contains_account_id": False,
        "model_input_ready": False,
        "limitation": (
            "Bu dosya yalnızca kimlik ve etiket içerir; olay zamanı, metin ve hesap alanları "
            "olmadan koordinasyon motoru girdisine dönüştürülemez."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ephemeral etiket dosyasından kimliksiz toplu veri profili üret."
    )
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    profile = profile_annotations(args.input)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(args.output)


if __name__ == "__main__":
    main()
