"""Build a Kaggle-ready dataset zip (forward-slash paths).

Kaggle rejects zip entries containing '\\'. PowerShell Compress-Archive writes
Windows separators, so build the archive with Python's zipfile instead.

Usage:
    python make_kaggle_zip.py [--out ayayo_dataset.zip]
"""

import argparse
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT_DEFAULT = ROOT / "ayayo_dataset.zip"

# Only what run_training/notebook needs.
INCLUDE_DIRS = [
    ("src", None),                      # all of src/
    # train+val for training, test for the final held-out evaluation
    ("data/processed", {"train.jsonl", "val.jsonl", "test.jsonl"}),
]

# Expected document counts. The source of truth is data/processed/*.jsonl; these
# are only used to shout when the archive does not match the ADR-015 dataset.
# A test once overwrote data/processed with the old 800/200 split and the stale
# archive was uploaded silently, so the count is printed and checked here.
EXPECTED_DOCS = {"train": 1440, "val": 159, "test": 200}

SKIP_SUFFIXES = {".pyc", ".pyo"}
SKIP_NAMES = {"__pycache__", ".gitkeep"}


def iter_files(rel_dir: str, allow: set[str] | None):
    base = ROOT / rel_dir
    for path in sorted(base.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix in SKIP_SUFFIXES:
            continue
        if path.name in SKIP_NAMES:
            continue
        if allow is not None and path.name not in allow:
            continue
        yield path


def count_jsonl(path: Path) -> int:
    with path.open("r", encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(OUT_DEFAULT))
    args = parser.parse_args()

    out_path = Path(args.out)
    if out_path.exists():
        out_path.unlink()

    count = 0
    with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_dir, allow in INCLUDE_DIRS:
            for path in iter_files(rel_dir, allow):
                # posix path -> forward slashes, no leading './'
                arcname = path.relative_to(ROOT).as_posix()
                zf.write(path, arcname)
                print(f"  + {arcname}")
                count += 1

    size = out_path.stat().st_size
    print(f"\nWrote {out_path} ({count} files, {size/1024:.1f} KiB)")

    # Verify the archive carries the split the notebook expects.
    mismatches = []
    for split, expected in EXPECTED_DOCS.items():
        actual = count_jsonl(ROOT / "data" / "processed" / f"{split}.jsonl")
        flag = "OK " if actual == expected else "MISMATCH"
        print(f"  {flag} {split:<5} {actual:>5} docs (expected {expected})")
        if actual != expected:
            mismatches.append(f"{split}: {actual} != {expected}")
    if mismatches:
        raise SystemExit(
            "Dataset split does not match ADR-015 (" + ", ".join(mismatches) + "). "
            "Re-run: python scripts/download_subset.py --train 1600 --test 200 && "
            "python scripts/process_and_split.py "
            "--train-raw data/raw/indonesian_news_train_1600.jsonl"
        )


if __name__ == "__main__":
    main()
