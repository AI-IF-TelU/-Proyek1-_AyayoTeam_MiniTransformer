"""Process dataset: deduplicate and perform document-level splitting.

Input (dipilih dengan --train-raw / --test-raw):
  - data/raw/indonesian_news_train_<N>.jsonl
  - data/raw/indonesian_news_test_<M>.jsonl
Output:
  - data/processed/train.jsonl
  - data/processed/val.jsonl
  - data/processed/test.jsonl

Baseline (ADR-012) memakai 800/200. Eksperimen C15 (ADR-015) memakai 1600/200:
  python scripts/process_and_split.py --train-raw data/raw/indonesian_news_train_1600.jsonl
"""

import argparse
import json
import re
import random
from pathlib import Path

TRAIN_RAW_FILE = Path("data/raw/indonesian_news_train_800.jsonl")
TEST_RAW_FILE = Path("data/raw/indonesian_news_test_200.jsonl")
PROCESSED_DIR = Path("data/processed")
SEED = 42

def normalize_text(text: str) -> str:
    """Normalize text for deduplication."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def load_and_dedup(file_path: Path):
    if not file_path.exists():
        raise FileNotFoundError(f"Raw data file {file_path} not found.")

    docs = []
    seen = set()
    with file_path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            content = item.get("content", "")
            norm = normalize_text(content)
            if not norm:
                continue
            if norm not in seen:
                seen.add(norm)
                docs.append({"content": content, "norm": norm})
    return docs

def process_and_split(train_raw: Path = TRAIN_RAW_FILE,
                      test_raw: Path = TEST_RAW_FILE,
                      processed_dir: Path = PROCESSED_DIR):
    train_docs_raw = load_and_dedup(train_raw)
    test_docs_raw = load_and_dedup(test_raw)

    # Dedup lintas split: buang dari test jika ada di train
    train_norms = {d["norm"] for d in train_docs_raw}
    test_docs_clean = [d for d in test_docs_raw if d["norm"] not in train_norms]

    # Val = 10% dari train unik (seed 42)
    random.seed(SEED)
    random.shuffle(train_docs_raw)

    val_count = int(len(train_docs_raw) * 0.1)
    val_docs = train_docs_raw[:val_count]
    train_docs = train_docs_raw[val_count:]

    processed_dir.mkdir(parents=True, exist_ok=True)

    def write_jsonl(file_path: Path, docs: list):
        with file_path.open("w", encoding="utf-8", newline="\n") as f:
            for doc in docs:
                f.write(json.dumps({"content": doc["content"]}, ensure_ascii=False) + "\n")

    write_jsonl(processed_dir / "train.jsonl", train_docs)
    write_jsonl(processed_dir / "val.jsonl", val_docs)
    write_jsonl(processed_dir / "test.jsonl", test_docs_clean)

    stats = {
        "train_docs": len(train_docs),
        "val_docs": len(val_docs),
        "test_docs": len(test_docs_clean),
        "cross_split_dropped": len(test_docs_raw) - len(test_docs_clean),
        "output_dir": str(processed_dir).replace("\\", "/"),
    }

    print(json.dumps(stats, indent=2))
    return stats

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--train-raw", type=Path, default=TRAIN_RAW_FILE)
    parser.add_argument("--test-raw", type=Path, default=TEST_RAW_FILE)
    cli = parser.parse_args()
    process_and_split(cli.train_raw, cli.test_raw)
