"""Unduh raw dataset (kolom `content`) untuk subset train + test.

Streaming + kolom tunggal: kolom `embedding` tidak dimaterialisasi.
Revision dipin agar urutan shard deterministik.

Default adalah baseline 800/200 (ADR-012). Eksperimen C15 memakai 1600/200
(ADR-015): `python scripts/download_subset.py --train 1600 --test 200`.

Output:
  - data/raw/indonesian_news_train_<N>.jsonl + metadata
  - data/raw/indonesian_news_test_<M>.jsonl + metadata
"""

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from datasets import load_dataset

DATASET_ID = "fahadh4ilyas/indonesian_news_datasets"
REVISION = "13f841935cf1adbe3e41e474bf926e49a0e2943e"
RAW_DIR = Path("data/raw")

def splits_config(train_n: int, test_n: int) -> list:
    return [
        {
            "split": "train",
            "target": train_n,
            "out_jsonl": RAW_DIR / f"indonesian_news_train_{train_n}.jsonl",
            "out_meta": RAW_DIR / f"indonesian_news_train_{train_n}.metadata.json",
        },
        {
            "split": "test",
            "target": test_n,
            "out_jsonl": RAW_DIR / f"indonesian_news_test_{test_n}.jsonl",
            "out_meta": RAW_DIR / f"indonesian_news_test_{test_n}.metadata.json",
        },
    ]


def download_split(split: str, target: int, out_jsonl: Path, out_meta: Path) -> dict:
    accessed_at = datetime.now(timezone(timedelta(hours=7))).isoformat(timespec="seconds")

    ds = load_dataset(
        DATASET_ID,
        split=split,
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
        if len(rows) >= target:
            break

    with out_jsonl.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    meta = {
        "dataset_id": DATASET_ID,
        "split": split,
        "revision": REVISION,
        "license": "CC BY-NC 4.0",
        "accessed_at_utc_plus_7": accessed_at,
        "filter": "content tidak kosong setelah strip()",
        "rows_read": read,
        "rows_skipped": skipped,
        "rows_saved": len(rows),
        "output": str(out_jsonl).replace("\\", "/"),
    }
    out_meta.write_text(json.dumps(meta, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return meta


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--train", type=int, default=800,
                        help="jumlah artikel split train (default 800, C15: 1600)")
    parser.add_argument("--test", type=int, default=200,
                        help="jumlah artikel split test (default 200)")
    args = parser.parse_args()
    if args.train < 1 or args.test < 1:
        raise SystemExit("--train dan --test harus >= 1")

    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Hapus file lama jika ada
    old_files = [
        RAW_DIR / "indonesian_news_1000.jsonl",
        RAW_DIR / "indonesian_news_1000.metadata.json",
    ]
    for old_file in old_files:
        if old_file.exists():
            old_file.unlink()

    for config in splits_config(args.train, args.test):
        meta = download_split(
            split=config["split"],
            target=config["target"],
            out_jsonl=config["out_jsonl"],
            out_meta=config["out_meta"],
        )
        print(json.dumps(meta, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
