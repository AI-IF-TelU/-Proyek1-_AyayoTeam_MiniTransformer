"""Tes regresi jalur restore checkpoint -> generate (F-D9-01, D14).

Mengikuti persis langkah README §11 "Memuat checkpoint dan melakukan generate":
load checkpoint, bangun MiniGPT dari config, pulihkan bobot, pulihkan tokenizer
lewat `Tokenizer.from_vocab`, lalu hasilkan teks.
"""

import os
import tempfile

from src.data.tokenizer import Tokenizer
from src.generate import generate
from src.model.minigpt import MiniGPT
from src.train import load_checkpoint, save_checkpoint

CORPUS = [
    "presiden indonesia mengumumkan kebijakan baru",
    "jakarta cuaca cerah sepanjang hari",
]


def _fit_tokenizer() -> Tokenizer:
    tok = Tokenizer()
    tok.fit(CORPUS)
    return tok


def _config(vocab_size: int) -> dict:
    return {
        "model": {
            "vocab_size": vocab_size,
            "n_layers": 1,
            "n_heads": 2,
            "d_model": 8,
            "context_length": 64,
            "d_ff": 32,
            "dropout": 0.0,
            "layer_norm_eps": 1e-5,
        }
    }


def _restore(path: str):
    ck = load_checkpoint(path)
    model_cfg = {k: v for k, v in ck["config"]["model"].items() if k != "d_ff"}
    model = MiniGPT(**model_cfg)
    model.load_state_dict(ck["state_dict"])
    tokenizer = Tokenizer.from_vocab(ck["vocab"])
    return model, tokenizer, ck


def test_restore_checkpoint_then_generate_is_not_empty():
    tok = _fit_tokenizer()
    model = MiniGPT(vocab_size=tok.vocab_size, n_layers=1, n_heads=2, d_model=8,
                    context_length=64, dropout=0.0)
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ckpt.pt")
        save_checkpoint(path, model, vocab=tok.token_to_id, config=_config(tok.vocab_size))
        restored_model, restored_tok, ck = _restore(path)

    assert restored_tok.vocab_size == len(ck["vocab"])
    assert len(restored_tok.id_to_token) == len(ck["vocab"])
    assert restored_tok.decode(restored_tok.encode("presiden indonesia")) == "presiden indonesia"

    # eos dinetralkan: hasil greedy pada bobot acak tidak boleh bergantung pada <eos>.
    out = generate(restored_model, restored_tok, "presiden indonesia",
                   max_new_tokens=5, eos_id=-1)
    assert isinstance(out, str)
    assert out.strip() != ""


def test_restored_vocab_size_builds_minigpt():
    tok = _fit_tokenizer()
    with tempfile.TemporaryDirectory() as d:
        path = os.path.join(d, "ckpt.pt")
        model = MiniGPT(vocab_size=tok.vocab_size, n_layers=1, n_heads=2, d_model=8,
                        context_length=64, dropout=0.0)
        save_checkpoint(path, model, vocab=tok.token_to_id, config=_config(tok.vocab_size))
        _, restored_tok, _ = _restore(path)

    rebuilt = MiniGPT(vocab_size=restored_tok.vocab_size, n_layers=1, n_heads=2,
                      d_model=8, context_length=64, dropout=0.0)
    assert rebuilt.lm_head.out_features == tok.vocab_size
