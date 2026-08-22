"""Platform and research-data adapter boundaries."""

from sagduyu.adapters.jsonl import iter_campaign_records, write_campaign_records

__all__ = ["iter_campaign_records", "write_campaign_records"]
