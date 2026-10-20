import re
from collections import Counter
from typing import Sequence, List, Dict

class Tokenizer:
    def __init__(self):
        # Pemetaan berdasarkan TECH_SPEC.md §3 dan ADR-008
        self.special_tokens = {
            "<pad>": 0,
            "<bos>": 1,
            "<eos>": 2,
            "<unk>": 3
        }
        self.token_to_id: Dict[str, int] = {}
        self.id_to_token: Dict[int, str] = {}
        self._vocab_size = 0

    def fit(self, texts: Sequence[str]) -> None:
        """Bangun vocab dari train set."""
        counts = Counter()
        for text in texts:
            tokens = re.findall(r"\w+|[^\w\s]", text.lower())
            counts.update(tokens)

        # Urutkan frekuensi (tie-breaker: alfabetis)
        sorted_tokens = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
        
        self.token_to_id = self.special_tokens.copy()
        self.id_to_token = {v: k for k, v in self.special_tokens.items()}
        
        for token, _ in sorted_tokens:
            if token not in self.token_to_id:
                token_id = len(self.token_to_id)
                self.token_to_id[token] = token_id
                self.id_to_token[token_id] = token
        
        self._vocab_size = len(self.token_to_id)

    def encode(self, text: str) -> List[int]:
        """Lowercase -> tokenisasi -> to_id."""
        tokens = re.findall(r"\w+|[^\w\s]", text.lower())
        return [self.token_to_id.get(t, self.special_tokens["<unk>"]) for t in tokens]

    def decode(self, ids: Sequence[int]) -> str:
        """to_token -> gabung spasi."""
        tokens = [self.id_to_token.get(i, "") for i in ids if i not in [0, 1, 2, 3]]
        return " ".join(tokens).strip()

    @property
    def vocab_size(self) -> int:
        return self._vocab_size
