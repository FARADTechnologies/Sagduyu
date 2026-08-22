from __future__ import annotations

import json
from collections.abc import Iterable, Iterator
from pathlib import Path

from pydantic import ValidationError

from sagduyu.evaluation import CampaignRecord


class CampaignDataError(ValueError):
    pass


def iter_campaign_records(path: Path) -> Iterator[CampaignRecord]:
    seen_ids: set[str] = set()
    with path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                record = CampaignRecord.model_validate_json(line)
            except (ValidationError, json.JSONDecodeError) as error:
                raise CampaignDataError(f"invalid record at line {line_number}: {error}") from error
            if record.campaign_id in seen_ids:
                raise CampaignDataError(
                    f"duplicate campaign_id at line {line_number}: {record.campaign_id}"
                )
            seen_ids.add(record.campaign_id)
            yield record


def write_campaign_records(path: Path, records: Iterable[CampaignRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(record.model_dump_json() + "\n")
