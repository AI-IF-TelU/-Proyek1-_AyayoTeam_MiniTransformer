import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.train import load_checkpoint
from src.model.minigpt import MiniGPT
from src.data.tokenizer import Tokenizer
from src.generate import DecodeConfig, generate_ids
from src.postprocess import build_case_map, postprocess

CKPT = "outputs/metrics/c15/minigpt_c15_kaggle_best.pt"

ck = load_checkpoint(CKPT)
model = MiniGPT.from_config(ck["config"]["model"])   # jangan MiniGPT(**config)
model.load_state_dict(ck["state_dict"])
model.eval()
tok = Tokenizer.from_vocab(ck["vocab"])

train = [json.loads(l)["content"] for l in open("data/processed/train.jsonl", encoding="utf-8")]
case_map = build_case_map(train, min_count=3)        # kapitalisasi nama diri

cfg = DecodeConfig(do_sample=True, temperature=1.1, top_p=0.9,
                   repetition_penalty=1.1, no_repeat_ngram_size=3,
                   ban_unk=True, seed=1234)

prompt = input("Prompt: ")
g = generate_ids(model, tok, prompt=prompt, max_new_tokens=60,
                 context_length=model.context_length, cfg=cfg)

print("\n" + postprocess(g.ids, tok.id_to_token, prompt=prompt,
                         case_map=case_map, trim=True))