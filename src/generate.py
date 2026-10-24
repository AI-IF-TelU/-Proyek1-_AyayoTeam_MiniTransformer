"""Greedy text generation (contract: TECH_SPEC 6, ADR-009)."""

import torch


@torch.no_grad()
def generate(model, tokenizer, prompt: str, max_new_tokens: int = 64,
            context_length: int = None, bos_id: int = 1, eos_id: int = 2) -> str:
    model.eval()
    # Default mengikuti model agar model non-baseline tidak melempar ValueError
    # di tengah generasi (F-D9-02).
    if context_length is None:
        context_length = getattr(model, "context_length", 64)
    param = next(model.parameters(), None)
    device = param.device if param is not None else torch.device("cpu")
    ids = [bos_id] + tokenizer.encode(prompt.lower())
    generated = 0
    while generated < max_new_tokens:
        ctx = ids[-context_length:]
        x = torch.tensor([ctx], dtype=torch.long, device=device)
        logits = model(x)
        next_id = int(torch.argmax(logits[0, -1]).item())
        if next_id == eos_id:
            break
        ids.append(next_id)
        generated += 1
    # decode excluding bos
    return tokenizer.decode(ids[1:])