"""Create a tiny subset for rapid validation of run_training.py.

Only used for sanity-checking the pipeline (not for final metrics).
Final real run must use data/processed/train.jsonl via Modal T4.
"""

import json
from pathlib import Path


def main():
    src = Path("data/processed/train.jsonl")
    tmp = Path("data/processed/_tiny_train.jsonl")
    with src.open(encoding="utf-8") as f:
        lines = [json.loads(l) for l in f]
    n = min(50, len(lines))
    print(f"[tiny] keeping {n} of {len(lines)} articles from train")
    with tmp.open("w", encoding="utf-8") as f:
        for rec in lines[:n]:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[tiny] written to {tmp}")


if __name__ == "__main__":
    main()
