"""Modal entrypoint for C14 real training run on T4 GPU.

Prerequisites:
  - modal CLI installed:  pip install modal
  - Modal token configured:  modal token new   (or env MODAL_TOKEN_ID / MODAL_TOKEN_SECRET)

Run:
    python -m modal run modal_app.py          # build image, run 10 epochs, stream logs
    python -m modal volume ls ayayo-c14-vol    # list persisted outputs after run
    python -m modal volume get ayayo-c14-vol c14_metrics.jsonl ./outputs/metrics/full/
    python -m modal volume get ayayo-c14-vol minigpt_c14.pt ./outputs/metrics/full/

Note: the volume is mounted at /vol (its own root), so files land at the
volume root, not under /outputs/metrics. vol.commit() is called after writing
so results persist after the container exits.
"""

import modal
from pathlib import Path

APP_NAME = "ayayo-c14"

# ── image (torch CUDA wheel directly from PyTorch) ──────────────────────────
image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch",
        "--index-url", "https://download.pytorch.org/whl/cu121",
    )
    .pip_install("numpy", "datasets", "huggingface-hub")
    # Copy project source (src/*) into the container at /repo/src
    .add_local_dir(".", "/repo", exclude=["node_modules", "__pycache__", ".git"])
)

# ── persistent volume (outputs survive between runs) ────────────────────────
vol = modal.Volume.from_name("ayayo-c14-vol", create_if_missing=True)

# ── app ──────────────────────────────────────────────────────────────────────
app = modal.App(name=APP_NAME, image=image, secrets=[])


@app.function(
    gpu="T4",
    timeout=7200,      # 2 h — comfortably covers 10 epochs on T4
    volumes={"/vol": vol},  # volume root mounted at /vol
)
def run_c14_training():
    """Full 10-epoch training on T4, write metrics + checkpoint to volume."""
    import os
    import sys
    import time
    import json
    import torch

    # Ensure /repo is the working directory so relative imports resolve
    repo_root = Path("/repo")
    os.chdir(repo_root)
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    from src.config import Config, ModelConfig, TrainConfig
    from src.data.dataset import TextDataset, create_dataloader
    from src.data.tokenizer import Tokenizer
    from src.model.minigpt import MiniGPT
    from src.train import (
        get_device,
        write_metrics_jsonl,
        save_checkpoint,
        make_optimizer,
        make_criterion,
        training_step,
        evaluate,
    )
    from src.generate import generate

    device = get_device()
    print(f"[C14] Torch {torch.__version__} · device {device}", flush=True)

    # --- Data ---
    def load_jsonl(path: str) -> list[str]:
        with open(path, encoding="utf-8") as f:
            return [json.loads(line)["content"] for line in f]

    train_texts = load_jsonl("data/processed/train.jsonl")
    val_texts = load_jsonl("data/processed/val.jsonl")
    print(f"[C14] Articles: train={len(train_texts)} val={len(val_texts)}", flush=True)

    # --- Tokenizer (fit on train ONLY — no leakage) ---
    tok = Tokenizer()
    tok.fit(train_texts)
    print(f"[C14] Vocab size: {tok.vocab_size}", flush=True)

    # --- Datasets / DataLoaders ---
    ds_tr = TextDataset(train_texts, tok, context_length=64)
    ds_va = TextDataset(val_texts, tok, context_length=64)
    dl_tr = create_dataloader(ds_tr, batch_size=32, shuffle=True,
                              pad_id=0, context_length=64)
    dl_va = create_dataloader(ds_va, batch_size=32, shuffle=False,
                              pad_id=0, context_length=64)
    print(f"[C14] Segments: train={len(ds_tr)} val={len(ds_va)}", flush=True)
    print(f"[C14] Batches/epoch: train={len(dl_tr)} val={len(dl_va)}", flush=True)

    # --- Config ---
    cfg = Config(
        model=ModelConfig(
            vocab_size=tok.vocab_size,
            n_layers=2,
            n_heads=4,
            d_model=64,
            context_length=64,
            dropout=0.1,
            layer_norm_eps=1e-5,
        ),
        train=TrainConfig(
            seed=42,
            batch_size=32,
            epochs=10,
            lr=3e-4,
            weight_decay=0.01,
            pad_id=0,
            bos_id=1,
            eos_id=2,
            unk_id=3,
        ),
    )

    # --- Model ---
    model = MiniGPT(
        vocab_size=tok.vocab_size,
        n_layers=cfg.model.n_layers,
        n_heads=cfg.model.n_heads,
        d_model=cfg.model.d_model,
        context_length=cfg.model.context_length,
        dropout=cfg.model.dropout,
        layer_norm_eps=cfg.model.layer_norm_eps,
    ).to(device)
    n_params = sum(p.numel() for p in model.parameters())
    print(f"[C14] Params: {n_params:,}", flush=True)

    # --- Training ---
    # Write into the mounted volume (volume root = /vol)
    metrics_path = "/vol/c14_metrics.jsonl"
    checkpoint_path = "/vol/minigpt_c14.pt"

    history = []
    t0 = time.time()
    for epoch in range(1, cfg.train.epochs + 1):
        ep_t0 = time.time()
        optimizer = make_optimizer(model, lr=cfg.train.lr,
                                   weight_decay=cfg.train.weight_decay)
        criterion = make_criterion(pad_id=cfg.train.pad_id)

        model.train()
        total_loss, n_samples = 0.0, 0
        for x, y in dl_tr:
            x, y = x.to(device), y.to(device)
            loss = training_step(model, x, y, optimizer, criterion)
            total_loss += loss * x.size(0)
            n_samples += x.size(0)
        train_loss = total_loss / max(n_samples, 1)

        val_loss = evaluate(model, dl_va, criterion)
        elapsed = time.time() - ep_t0
        rec = {
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "epoch_sec": round(elapsed, 2),
        }
        history.append(rec)
        print(
            f"[C14] Epoch {epoch:02d}/10 | train={train_loss:.4f} "
            f"val={val_loss:.4f} ({elapsed:.1f}s)",
            flush=True,
        )

    total_time = time.time() - t0
    print(f"[C14] Total training time: {total_time:.1f}s", flush=True)

    # --- Persist metrics & checkpoint ---
    write_metrics_jsonl(history, metrics_path)
    save_checkpoint(checkpoint_path, model,
                    vocab=tok.token_to_id, config=cfg.to_dict())
    vol.commit()  # persist writes to the volume
    print(f"[C14] Metrics  -> {metrics_path}", flush=True)
    print(f"[C14] Checkpoint -> {checkpoint_path}", flush=True)

    # --- Generation example ---
    model.eval()
    prompt = "presiden indonesia"
    generated = generate(
        model, tok,
        prompt=prompt,
        max_new_tokens=40,
        context_length=cfg.model.context_length,
        bos_id=cfg.train.bos_id,
        eos_id=cfg.train.eos_id,
    )
    print(f"[C14] Prompt   : '{prompt}'", flush=True)
    print(f"[C14] Generated: '{generated}'", flush=True)

    with open(metrics_path, "a", encoding="utf-8") as f:
        f.write(
            json.dumps({
                "event": "generation",
                "prompt": prompt,
                "generated": generated,
                "total_seconds": round(total_time, 2),
                "device": str(device),
                "torch_version": torch.__version__,
                "vocab_size": tok.vocab_size,
                "n_train_segments": len(ds_tr),
                "n_val_segments": len(ds_va),
                "n_params": n_params,
                "history": history,
            })
            + "\n"
        )
    print("[C14] Done.", flush=True)


@app.local_entrypoint()
def main():
    """Local wrapper: triggers the remote Modal run and streams logs."""
    run_c14_training.remote()
