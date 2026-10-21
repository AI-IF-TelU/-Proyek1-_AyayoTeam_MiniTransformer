"""Process dataset: deduplicate and perform document-level splitting.

Input: data/raw/indonesian_news_1000.jsonl
Output: data/processed/train.jsonl, val.jsonl
"""

import json
import re
import random
from pathlib import Path

RAW_FILE = Path("data/raw/indonesian_news_1000.jsonl")
PROCESSED_DIR = Path("data/processed")
SEED = 42

def normalize_text(text: str) -> str:
    """Normalize text for deduplication."""
    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def process_and_split():
    if not RAW_FILE.exists():
        raise FileNotFoundError(f"Raw data file {RAW_FILE} not found.")

    documents = []
    seen_hashes = set()

    with RAW_FILE.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            content = item.get("content", "")
            
            norm_content = normalize_text(content)
            if not norm_content:
                continue

            if norm_content not in seen_hashes:
                seen_hashes.add(norm_content)
                documents.append({"content": content})

    total_docs = len(documents)
    
    # Shuffle documents for split
    random.seed(SEED)
    random.shuffle(documents)

    # Split: 90% train, 10% validation from train split (no test carved from train)
    val_count = int(total_docs * 0.1)
    val_docs = documents[:val_count]
    train_docs = documents[val_count:]

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    def write_jsonl(file_path: Path, docs: list):
        with file_path.open("w", encoding="utf-8", newline="\n") as f:
            for doc in docs:
                f.write(json.dumps(doc, ensure_ascii=False) + "\n")

    write_jsonl(PROCESSED_DIR / "train.jsonl", train_docs)
    write_jsonl(PROCESSED_DIR / "val.jsonl", val_docs)

    stats = {
        "total_unique_docs": total_docs,
        "train_docs": len(train_docs),
        "val_docs": len(val_docs),
    }

    print(json.dumps(stats, indent=2))
    return stats

if __name__ == "__main__":
    process_and_split()
