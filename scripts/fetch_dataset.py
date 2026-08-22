from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
import tomllib
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import TypedDict

CHUNK_SIZE = 1024 * 1024
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = PROJECT_ROOT / "configs" / "data-sources.toml"
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "raw"


class SourceConfig(TypedDict):
    description: str
    url: str
    filename: str
    license: str


def load_sources(path: Path) -> dict[str, SourceConfig]:
    with path.open("rb") as handle:
        raw = tomllib.load(handle)
    return {
        name: SourceConfig(
            description=values["description"],
            url=values["url"],
            filename=values["filename"],
            license=values["license"],
        )
        for name, values in raw.items()
    }


def fetch_source(
    source_name: str,
    source: SourceConfig,
    output_dir: Path,
    *,
    attempts: int = 3,
) -> Path:
    if attempts < 1:
        raise ValueError("attempts must be positive")
    output_dir.mkdir(parents=True, exist_ok=True)
    destination = (output_dir / source["filename"]).resolve()
    if output_dir.resolve() not in destination.parents:
        raise ValueError("source filename escapes the output directory")
    if destination.exists():
        raise FileExistsError(f"destination already exists: {destination}")

    temporary = destination.with_suffix(f"{destination.suffix}.part")
    digest = hashlib.sha256()
    byte_count = 0
    request = urllib.request.Request(
        source["url"],
        headers={"User-Agent": "Sagduyu-Research-Downloader/0.1"},
    )
    for attempt in range(attempts):
        try:
            with (
                urllib.request.urlopen(request, timeout=60) as response,
                temporary.open("xb") as output,
            ):
                while chunk := response.read(CHUNK_SIZE):
                    output.write(chunk)
                    digest.update(chunk)
                    byte_count += len(chunk)
            os.replace(temporary, destination)
            break
        except (OSError, urllib.error.URLError):
            temporary.unlink(missing_ok=True)
            digest = hashlib.sha256()
            byte_count = 0
            if attempt == attempts - 1:
                raise
            time.sleep(2**attempt)

    metadata = {
        "source": source_name,
        "description": source["description"],
        "url": source["url"],
        "license_note": source["license"],
        "downloaded_at": datetime.now(UTC).isoformat(),
        "filename": destination.name,
        "bytes": byte_count,
        "sha256": digest.hexdigest(),
    }
    metadata_path = destination.with_suffix(f"{destination.suffix}.metadata.json")
    metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return destination


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Kayıtlı bir public veri kaynağını indir ve bütünlük bilgisini kaydet."
    )
    parser.add_argument("source", help="configs/data-sources.toml içindeki kaynak adı")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    sources = load_sources(args.manifest)
    try:
        source = sources[args.source]
    except KeyError as error:
        available = ", ".join(sorted(sources))
        raise SystemExit(f"Bilinmeyen kaynak: {args.source}. Seçenekler: {available}") from error

    destination = fetch_source(args.source, source, args.output_dir)
    print(destination)


if __name__ == "__main__":
    main()
