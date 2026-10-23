"""Central configuration for MiniTransformer (JSON-serializable).

Values are the baseline defaults from TECH_SPEC.md / ADR-004, ADR-009-012.
They may be overridden via a JSON file or environment; architecture choices
require an ADR to change.
"""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    vocab_size: int = 0  # filled after tokenizer.fit
    n_layers: int = 2
    n_heads: int = 4
    d_model: int = 64
    context_length: int = 64
    d_ff: int = 256
    dropout: float = 0.1
    layer_norm_eps: float = 1e-5


@dataclass
class TrainConfig:
    seed: int = 42
    batch_size: int = 32
    epochs: int = 10
    lr: float = 3e-4
    weight_decay: float = 0.01
    pad_id: int = 0
    bos_id: int = 1
    eos_id: int = 2
    unk_id: int = 3
    metrics_dir: str = "outputs/metrics"
    checkpoint_name: str = "minigpt.pt"


@dataclass
class GenConfig:
    max_new_tokens: int = 64


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    gen: GenConfig = field(default_factory=GenConfig)

    def to_dict(self) -> dict:
        return asdict(self)

    def to_json(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        return cls(
            model=ModelConfig(**data.get("model", {})),
            train=TrainConfig(**data.get("train", {})),
            gen=GenConfig(**data.get("gen", {})),
        )

    @classmethod
    def from_json(cls, path: str | Path) -> "Config":
        return cls.from_dict(json.loads(Path(path).read_text(encoding="utf-8")))


DEFAULT_CONFIG = Config()
"""Module-level default; mutate a copy, never this instance in place."""