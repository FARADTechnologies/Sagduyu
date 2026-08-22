from __future__ import annotations

import argparse
from pathlib import Path

from sagduyu.adapters import iter_campaign_records
from sagduyu.evaluation import evaluate_campaigns, temporal_group_split


def main() -> None:
    parser = argparse.ArgumentParser(description="Kampanya kayıtlarında SAĞDUYU ölçümü çalıştır.")
    parser.add_argument("input", type=Path, help="Kampanya kayıtlarını içeren JSONL dosyası")
    parser.add_argument("--output", type=Path, required=True, help="Sonuç JSON dosyası")
    parser.add_argument("--test-fraction", type=float, default=0.2)
    args = parser.parse_args()

    records = list(iter_campaign_records(args.input))
    _, test_records = temporal_group_split(records, test_fraction=args.test_fraction)
    report = evaluate_campaigns(test_records, split="temporal-group-holdout")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(report.model_dump_json(indent=2) + "\n", encoding="utf-8")
    print(args.output)


if __name__ == "__main__":
    main()
