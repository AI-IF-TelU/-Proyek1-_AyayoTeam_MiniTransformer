"""Greedy and sampled text generation (contract: TECH_SPEC 6, ADR-009).

`generate` keeps the ADR-009 contract: greedy, first-step argmax, stop on
`<eos>` or `max_new_tokens`. `generate_ids` adds decoding knobs that only
change *selection* of the next token, never the model.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Sequence, Tuple

import torch

UNK_ID = 3


@dataclass
class DecodeConfig:
    """Next-token selection knobs.

    Defaults are greedy, i.e. identical to `generate` (ADR-009). Sampling is
    opt-in via `do_sample=True`.
    """

    do_sample: bool = False
    temperature: float = 1.0
    top_k: int = 0
    top_p: float = 1.0
    repetition_penalty: float = 1.0
    no_repeat_ngram_size: int = 0
    ban_unk: bool = True
    seed: Optional[int] = None
    stop_on_eos: bool = True


@dataclass
class Generation:
    ids: List[int] = field(default_factory=list)
    stopped_on_eos: bool = False


def _ban_repeats(logits: torch.Tensor, generated: Sequence[int], n: int) -> None:
    """Forbid any n-gram that would repeat one already seen (in place)."""
    if n <= 0 or len(generated) < n:
        return
    prefix = tuple(generated[len(generated) - (n - 1):]) if n > 1 else ()
    for i in range(len(generated) - n + 1):
        if tuple(generated[i:i + n - 1]) == prefix:
            logits[generated[i + n - 1]] = float("-inf")


def _filter_logits(logits: torch.Tensor, generated: Sequence[int],
                   prompt_ids: Sequence[int], cfg: DecodeConfig) -> torch.Tensor:
    logits = logits.float().clone()
    if cfg.repetition_penalty != 1.0:
        for token_id in set(prompt_ids) | set(generated):
            logits[token_id] = (logits[token_id] / cfg.repetition_penalty
                                if logits[token_id] > 0
                                else logits[token_id] * cfg.repetition_penalty)
    _ban_repeats(logits, generated, cfg.no_repeat_ngram_size)
    if cfg.ban_unk and logits.numel() > UNK_ID:
        logits[UNK_ID] = float("-inf")

    logits = logits / max(cfg.temperature, 1e-6)

    if cfg.top_k and cfg.top_k < logits.numel():
        kth = torch.topk(logits, cfg.top_k).values[-1]
        logits[logits < kth] = float("-inf")
    if cfg.top_p < 1.0:
        ordered = torch.sort(logits, descending=True).values
        cumulative = torch.softmax(ordered, dim=-1).cumsum(dim=-1)
        over = (cumulative > cfg.top_p).nonzero()
        cut = int(over[0]) + 1 if len(over) else ordered.numel()
        logits[logits < ordered[cut - 1]] = float("-inf")
    return logits


def _pick(logits: torch.Tensor, cfg: DecodeConfig,
          generator: Optional[torch.Generator]) -> int:
    if not cfg.do_sample:
        return int(torch.argmax(logits))
    probs = torch.softmax(logits, dim=-1)
    if not torch.isfinite(probs).all() or float(probs.sum()) <= 0.0:
        # Every candidate was masked; fall back instead of NaN.
        return int(torch.argmax(torch.nan_to_num(logits, neginf=-1e9)))
    return int(torch.multinomial(probs, 1, generator=generator))


@torch.no_grad()
def generate_ids(model, tokenizer, prompt: str, max_new_tokens: int = 64,
                 context_length: int = None, bos_id: int = 1, eos_id: int = 2,
                 cfg: DecodeConfig = None) -> Generation:
    """Generate and return the new token ids plus why generation stopped."""
    cfg = cfg or DecodeConfig()
    model.eval()
    if context_length is None:
        context_length = getattr(model, "context_length", 64)
    param = next(model.parameters(), None)
    device = param.device if param is not None else torch.device("cpu")

    prompt_ids = tokenizer.encode(prompt.lower())
    ids = [bos_id] + prompt_ids
    generated: List[int] = []
    generator = None
    if cfg.do_sample and cfg.seed is not None:
        generator = torch.Generator(device="cpu")
        generator.manual_seed(cfg.seed)

    for _ in range(max_new_tokens):
        x = torch.tensor([ids[-context_length:]], dtype=torch.long, device=device)
        logits = model(x)[0, -1].cpu()
        next_id = _pick(_filter_logits(logits, generated, prompt_ids, cfg),
                        cfg, generator)
        if cfg.stop_on_eos and next_id == eos_id:
            return Generation(generated, True)
        ids.append(next_id)
        generated.append(next_id)
    return Generation(generated, False)


@torch.no_grad()
def generate(model, tokenizer, prompt: str, max_new_tokens: int = 64,
            context_length: int = None, bos_id: int = 1, eos_id: int = 2) -> str:
    """Greedy generation (ADR-009). Unchanged behaviour, delegates to `generate_ids`."""
    model.eval()
    if context_length is None:
        context_length = getattr(model, "context_length", 64)
    param = next(model.parameters(), None)
    device = param.device if param is not None else torch.device("cpu")
    ids = [bos_id] + tokenizer.encode(prompt.lower())
    generated = 0
    while generated < max_new_tokens:
        x = torch.tensor([ids[-context_length:]], dtype=torch.long, device=device)
        logits = model(x)
        next_id = int(torch.argmax(logits[0, -1]).item())
        if next_id == eos_id:
            break
        ids.append(next_id)
        generated += 1
    return tokenizer.decode(ids[1:])


@torch.no_grad()
def nll_and_ece(model, batches, temperature: float = 1.0) -> Tuple[float, float, float]:
    """Teacher-forced NLL, accuracy and ECE (15 bins) at a given temperature."""
    model.eval()
    total_nll, total_tokens, correct = 0.0, 0, 0
    conf_bins = torch.zeros(15, dtype=torch.float64)
    acc_bins = torch.zeros(15, dtype=torch.float64)
    count_bins = torch.zeros(15, dtype=torch.float64)

    for x, y in batches:
        logits = model(x).float() / max(temperature, 1e-6)
        flat = logits.reshape(-1, logits.size(-1))
        target = y.reshape(-1)
        keep = target != 0
        flat, target = flat[keep], target[keep]
        if target.numel() == 0:
            continue

        total_nll += float(torch.nn.functional.cross_entropy(flat, target, reduction="sum"))
        total_tokens += int(target.numel())

        probs = torch.softmax(flat, dim=-1)
        conf, pred = probs.max(dim=-1)
        hit = (pred == target).float()
        correct += int(hit.sum())
        idx = torch.clamp((conf * 15).long(), 0, 14)
        count_bins.index_add_(0, idx, torch.ones_like(conf, dtype=torch.float64))
        conf_bins.index_add_(0, idx, conf.double())
        acc_bins.index_add_(0, idx, hit.double())

    if total_tokens == 0:
        return float("nan"), 0.0, float("nan")
    seen = count_bins > 0
    gaps = (conf_bins[seen] - acc_bins[seen]).abs() / count_bins[seen]
    ece = float((gaps * count_bins[seen] / count_bins.sum()).sum())
    return total_nll / total_tokens, correct / total_tokens, ece


def tune_temperature(model, batches, grid=(0.7, 0.85, 1.0, 1.15, 1.3, 1.5, 1.7, 2.0)):
    """Pick the temperature with lowest teacher-forced NLL on held-out data.

    Returns (best_temperature, rows, at_boundary) where rows is
    [(T, nll, acc, ece), ...]. `at_boundary` is True when the best grid point is
    the smallest or largest entry: the optimum lies outside the grid, so the
    reported temperature must not be trusted without widening it.

    This is a *calibration* measurement, not a sampling recommendation. On a
    small overfit model the NLL optimum often sits at T>1.5, where generations
    drift into word salad. Use `pick_sampling_temperature` for decoding.
    """
    rows = [(t, *nll_and_ece(model, batches, t)) for t in grid]
    best = min(rows, key=lambda r: (r[1] if r[1] == r[1] else float("inf")))
    at_boundary = best[0] in (grid[0], grid[-1])
    return best[0], rows, at_boundary


def _sample_stats(ids: Sequence[int]) -> Tuple[float, int]:
    """(distinct-1 ratio, repeated trigram count) of one generated sequence."""
    if not ids:
        return 0.0, 0
    trigrams = [tuple(ids[i:i + 3]) for i in range(len(ids) - 2)]
    return len(set(ids)) / len(ids), len(trigrams) - len(set(trigrams))


def pick_sampling_temperature(model, tokenizer, prompts, grid=(0.8, 0.9, 1.0, 1.1, 1.2, 1.3),
                              max_new_tokens: int = 60, min_distinct1: float = 0.75,
                              calibration=None):
    """Pick a sampling temperature that stays coherent on held-out prompts.

    For each candidate T the model generates from every prompt and we measure
    repetition and lexical diversity. A temperature is *feasible* when it never
    repeats a trigram and keeps distinct-1 above `min_distinct1`. Among feasible
    values the one with the lowest ECE from `calibration` wins, because ECE is
    what says the probabilities can be trusted; ties fall back to the smallest T.

    Returns (best_temperature, rows) with rows = [(T, distinct1, dup_trigrams)].
    """
    rows = []
    for temperature in grid:
        cfg = DecodeConfig(do_sample=True, temperature=temperature, top_p=0.9,
                           repetition_penalty=1.1, no_repeat_ngram_size=3,
                           ban_unk=True, seed=1234)
        distinct, duplicate = [], 0
        for prompt in prompts:
            gen = generate_ids(model, tokenizer, prompt=prompt,
                               max_new_tokens=max_new_tokens, cfg=cfg)
            d1, dup = _sample_stats(gen.ids)
            distinct.append(d1)
            duplicate += dup
        rows.append((temperature, sum(distinct) / max(len(distinct), 1), duplicate))

    feasible = [r for r in rows if r[2] == 0 and r[1] >= min_distinct1]
    if not feasible:
        return grid[0], rows

    ece_by_temp = {row[0]: row[3] for row in (calibration or [])}
    best = min(feasible, key=lambda r: (ece_by_temp.get(r[0], 1.0), r[0]))
    return best[0], rows
