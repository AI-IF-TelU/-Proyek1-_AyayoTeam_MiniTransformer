import json
import pytest
from pathlib import Path
from scripts.process_and_split import normalize_text, process_and_split, PROCESSED_DIR

def test_normalize_text():
    raw = "  Halo \n Dunia! \t Ini   TESTING.  "
    expected = "halo dunia! ini testing."
    assert normalize_text(raw) == expected

def test_splits_and_leakage():
    stats = process_and_split()
    
    total = stats["total_unique_docs"]
    train_len = stats["train_docs"]
    val_len = stats["val_docs"]

    # Test splitting counts (90% train, 10% val)
    assert total == train_len + val_len
    assert val_len == int(total * 0.1)
    assert train_len == total - val_len

    # Test no leakage across files
    def load_contents(file_path: Path):
        contents = set()
        with file_path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    item = json.loads(line)
                    contents.add(normalize_text(item["content"]))
        return contents

    train_set = load_contents(PROCESSED_DIR / "train.jsonl")
    val_set = load_contents(PROCESSED_DIR / "val.jsonl")

    assert len(train_set) == train_len
    assert len(val_set) == val_len

    assert len(train_set.intersection(val_set)) == 0
