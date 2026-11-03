import json
import re

from src.data.tokenizer import Tokenizer

# Baca data training C15
with open("data/processed/train.jsonl", encoding="utf-8") as f:
    train_texts = [
        json.loads(line)["content"]
        for line in f
    ]

# Bangun vocabulary seperti konfigurasi C15
tokenizer = Tokenizer()
tokenizer.fit(train_texts, min_freq=2)

# Coba tokenisasi sebuah kalimat
text = "Presiden Indonesia membaca berita."

tokens = re.findall(r"\w+|[^\w\s]", text.lower())
token_ids = tokenizer.encode(text)

print("Teks asli :", text)
print("Token     :", tokens)
print("Token ID  :", token_ids)