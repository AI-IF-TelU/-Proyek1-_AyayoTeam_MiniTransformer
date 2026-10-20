import re
from typing import Sequence, Dict, List

class Tokenizer:
    def __init__(self):
        self.pad_token = "<pad>"
        self.bos_token = "<bos>"
        self.eos_token = "<eos>"
        self.unk_token = "<unk>"
        self.special_tokens = {self.pad_token: 0, self.bos_token: 1, self.eos_token: 2, self.unk_token: 3}
        self.token_to_id: Dict[str, int] = self.special_tokens.copy()
        self.id_to_token: Dict[int, str] = {v: k for k, v in self.token_to_id.items()}
        self._vocab_size = 4

    def fit(self, texts: Sequence[str]) -> None:
        token_counts = {}
        for text in texts:
            tokens = re.findall(r"\w+|[^\w\s]", text.lower())
            for token in tokens:
                if token not in self.token_to_id:
                    token_counts[token] = token_counts.get(token, 0) + 1
        
        # Sort by frequency
        sorted_tokens = sorted(token_counts.items(), key=lambda x: x[1], reverse=True)
        
        current_id = self._vocab_size
        for token, _ in sorted_tokens:
            self.token_to_id[token] = current_id
            self.id_to_token[current_id] = token
            current_id += 1
        self._vocab_size = current_id

    def encode(self, text: str) -> List[int]:
        tokens = re.findall(r"\w+|[^\w\s]", text.lower())
        ids = []
        for token in tokens:
            ids.append(self.token_to_id.get(token, self.token_to_id[self.unk_token]))
        return ids

    def decode(self, ids: Sequence[int]) -> str:
        tokens = []
        for id in ids:
            if id in self.id_to_token:
                token = self.id_to_token[id]
                if token not in ["<pad>", "<bos>", "<eos>", "<unk>"]:
                    tokens.append(token)
        return " ".join(tokens).strip()

    @property
    def vocab_size(self) -> int:
        return self._vocab_size
