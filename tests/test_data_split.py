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
    
    train_len = stats["train_docs"]
    val_len = stats["val_docs"]
    test_len = stats["test_docs"]

    # Val = 10% dari train (720 train / 80 val)
    assert val_len == int((train_len + val_len) * 0.1)
    
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
    test_set = load_contents(PROCESSED_DIR / "test.jsonl")

    assert len(train_set) == train_len
    assert len(val_set) == val_len
    assert len(test_set) == test_len

    assert len(train_set.intersection(val_set)) == 0
    assert len(train_set.intersection(test_set)) == 0
    assert len(val_set.intersection(test_set)) == 0
