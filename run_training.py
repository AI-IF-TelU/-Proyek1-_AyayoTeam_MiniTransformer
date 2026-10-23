"""End-to-end training script for C14 experiment.

Usage (local / inside Modal container):
    python run_training.py [--epochs N] [--max-epochs N]
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

import torch
from src.config import Config, ModelConfig, TrainConfig
from src.data.dataset import TextDataset, create_dataloader
from src.data.tokenizer import Tokenizer
from src.model.minigpt import MiniGPT
from src.train import train, write_metrics_jsonl, save_checkpoint, get_device
from src.generate import generate


def load_jsonl(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--max-epochs", type=int, default=None,
                        help="Stop after this many epochs (for budget fallback)")
    parser.add_argument("--metrics-dir", type=str, default="outputs/metrics")
    parser.add_argument("--checkpoint-name", type=str, default="minigpt_c14.pt")
    parser.add_argument("--data-dir", type=str, default="data/processed")
    parser.add_argument("--train-file", type=str, default="train.jsonl",
                        help="Override train file name (e.g. _tiny_train.jsonl)")
    parser.add_argument("--val-file", type=str, default="val.jsonl",
                        help="Override val file name (e.g. _tiny_val.jsonl)")
    args = parser.parse_args()

    start_time = time.time()
    device = get_device()
    print(f"[C14] Device: {device}", flush=True)
    print(f"[C14] Torch version: {torch.__version__}", flush=True)

    # --- Data ---
    data_dir = Path(args.data_dir)
    train_docs = load_jsonl(str(data_dir / args.train_file))
    val_docs = load_jsonl(str(data_dir / args.val_file))
    train_texts = [d["content"] for d in train_docs]
    val_texts = [d["content"] for d in val_docs]
    print(f"[C14] Articles: train={len(train_texts)}, val={len(val_texts)}", flush=True)

    # --- Tokenizer (fit on train ONLY to avoid leakage) ---
    tok = Tokenizer()
    tok.fit(train_texts)
    print(f"[C14] Vocab size: {tok.vocab_size}", flush=True)

    # --- Datasets + DataLoaders ---
    ds_train = TextDataset(train_texts, tok, context_length=64)
    ds_val = TextDataset(val_texts, tok, context_length=64)
    dl_train = create_dataloader(ds_train, batch_size=32, shuffle=True,
                                 pad_id=0, context_length=64)
    dl_val = create_dataloader(ds_val, batch_size=32, shuffle=False,
                               pad_id=0, context_length=64)
    print(f"[C14] Segments: train={len(ds_train)}, val={len(ds_val)}", flush=True)
    print(f"[C14] Batches/epoch: train={len(dl_train)}, val={len(dl_val)}", flush=True)

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
            epochs=args.epochs,
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
    print(f"[C14] Model params: {n_params:,}", flush=True)

    # --- Training ---
    metrics_path = os.path.join(args.metrics_dir, "c14_metrics.jsonl")
    checkpoint_path = os.path.join(args.metrics_dir, args.checkpoint_name)
    os.makedirs(args.metrics_dir, exist_ok=True)

    history = []
    for epoch in range(1, cfg.train.epochs + 1):
        epoch_start = time.time()
        from src.train import make_optimizer, make_criterion, training_step, evaluate
        optimizer = make_optimizer(model, lr=cfg.train.lr,
                                   weight_decay=cfg.train.weight_decay)
        criterion = make_criterion(pad_id=cfg.train.pad_id)

        # Train one epoch
        model.train()
        total_loss, n_samples = 0.0, 0
        for x, y in dl_train:
            x, y = x.to(device), y.to(device)
            loss = training_step(model, x, y, optimizer, criterion)
            total_loss += loss * x.size(0)
            n_samples += x.size(0)
        train_loss = total_loss / max(n_samples, 1)

        # Validate
        val_loss = evaluate(model, dl_val, criterion)
        elapsed = time.time() - epoch_start
        rec = {"epoch": epoch, "train_loss": train_loss,
               "val_loss": val_loss, "epoch_sec": round(elapsed, 2)}
        history.append(rec)
        print(f"[C14] Epoch {epoch:02d}/{cfg.train.epochs} | "
              f"train={train_loss:.4f} val={val_loss:.4f} ({elapsed:.1f}s)",
              flush=True)

        if args.max_epochs and epoch >= args.max_epochs:
            print(f"[C14] Stopped early at epoch {epoch} (max_epochs={args.max_epochs})",
                  flush=True)
            break

    total_time = time.time() - start_time
    print(f"[C14] Total training time: {total_time:.1f}s", flush=True)

    # --- Write metrics ---
    write_metrics_jsonl(history, metrics_path)
    print(f"[C14] Metrics written to: {metrics_path}", flush=True)

    # --- Save checkpoint ---
    save_checkpoint(checkpoint_path, model,
                    vocab=tok.token_to_id, config=cfg.to_dict())
    print(f"[C14] Checkpoint saved to: {checkpoint_path}", flush=True)

    # --- Generate example ---
    model.eval()
    prompt = "presiden indonesia"
    generated = generate(model, tok, prompt=prompt,
                         max_new_tokens=40,
                         context_length=cfg.model.context_length,
                         bos_id=cfg.train.bos_id,
                         eos_id=cfg.train.eos_id)
    print(f"[C14] Prompt   : '{prompt}'", flush=True)
    print(f"[C14] Generated: '{generated}'", flush=True)

    # Append generation result to metrics
    with open(metrics_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({
            "event": "generation",
            "prompt": prompt,
            "generated": generated,
            "total_seconds": round(total_time, 2),
            "device": str(device),
            "torch_version": torch.__version__,
            "vocab_size": tok.vocab_size,
            "n_train_segments": len(ds_train),
            "n_val_segments": len(ds_val),
            "n_params": n_params,
        }) + "\n")
    print(f"[C14] Done.", flush=True)


if __name__ == "__main__":
    main()

