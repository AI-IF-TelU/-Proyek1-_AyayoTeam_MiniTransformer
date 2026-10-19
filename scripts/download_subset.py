"""Unduh subset 1.000 artikel (kolom `content`) sesuai docs/DATA_SUBSET_PLAN.md.

Streaming + kolom tunggal: kolom `embedding` (~1.25 GB) tidak dimaterialisasi.
Revision dipin agar urutan shard deterministik. Output: data/raw/.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from datasets import load_dataset

DATASET_ID = "fahadh4ilyas/indonesian_news_datasets"
SPLIT = "train"
REVISION = "13f841935cf1adbe3e41e474bf926e49a0e2943e"
TARGET = 1000
RAW_DIR = Path("data/raw")
OUT_JSONL = RAW_DIR / "indonesian_news_1000.jsonl"
OUT_META = RAW_DIR / "indonesian_news_1000.metadata.json"


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    accessed_at = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")

    ds = load_dataset(
        DATASET_ID,
        split=SPLIT,
        streaming=True,
        revision=REVISION,
    ).select_columns(["content"])

    rows, read, skipped = [], 0, 0
    for row in ds:
        read += 1
        content = (row.get("content") or "").strip()
        if not content:
            skipped += 1
            continue
        rows.append({"content": content})
        if len(rows) >= TARGET:
            break

    with OUT_JSONL.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": DATASET_ID,
        "split": SPLIT,
        "revision": REVISION,
        "license": "CC BY-NC 4.0",
        "accessed_at_utc_plus_7": accessed_at,
        "filter": "content tidak kosong setelah strip()",
        "rows_read": read,
        "rows_skipped": skipped,
        "rows_saved": len(rows),
        "output": str(OUT_JSONL).replace("\\", "/"),
    }
    OUT_META.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
