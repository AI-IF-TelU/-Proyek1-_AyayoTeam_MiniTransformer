"""Display-layer post-processing for generated token ids.

`Tokenizer.decode` (TECH_SPEC §3) is untouched: it joins tokens with a space.
These helpers live outside the tokenizer contract and only shape text that is
shown in a report, so `decode` roundtrip behaviour stays as documented.
"""

from typing import Dict, Iterable, List, Sequence

# Deliberately conservative: hyphen and quotes stay space-separated because the
# tokenizer cannot tell "anak - anak" from "JAKARTA - Menteri" after the fact.
NO_SPACE_BEFORE = frozenset(".,;:!?)]}%")
NO_SPACE_AFTER = frozenset("([{")
SPECIAL_IDS = frozenset({0, 1, 2, 3})
SENTENCE_END = ".!?"


def detokenize(ids: Sequence[int], id_to_token: Dict[int, str]) -> str:
    """Join tokens without spaces around punctuation brackets and terminators."""
    out = ""
    for token_id in ids:
        if token_id in SPECIAL_IDS:
            continue
        token = id_to_token.get(token_id)
        if not token:
            continue
        if not out or token in NO_SPACE_BEFORE or out[-1] in NO_SPACE_AFTER:
            out += token
        else:
            out += " " + token
    return out


def trim_to_sentence(text: str) -> str:
    """Cut at the last sentence terminator so output never ends mid-sentence."""
    stripped = text.strip()
    cut = max(stripped.rfind(ch) for ch in SENTENCE_END)
    return stripped[: cut + 1] if cut >= 0 else stripped


def build_case_map(texts: Iterable[str], min_count: int = 3,
                   min_share: float = 0.5) -> Dict[str, str]:
    """Map lowercase word -> dominant cased surface form (proper nouns only).

    A word qualifies only if its mixed-case occurrences are a **majority** of all
    occurrences (`min_share`). Without that rule the map picks up common words
    that happen to follow a capital (`Aku`, `Dalam`, `Di`) and uppercases them
    mid-sentence, which looks worse than plain lowercase.

    Sentence-initial words are skipped: every sentence starts with a capital, so
    counting them would promote ordinary words. All-caps forms are skipped too,
    so a headline ``JAKARTA`` cannot uppercase everything.
    """
    import re
    from collections import Counter

    totals: Counter = Counter()
    surfaces: Dict[str, Counter] = {}
    for text in texts:
        for sentence in re.split(r"(?<=[.!?])\s+", text):
            for word in re.findall(r"\w+", sentence)[1:]:
                totals[word.lower()] += 1
                if word != word.lower() and word != word.upper():
                    surfaces.setdefault(word.lower(), Counter())[word] += 1

    case_map: Dict[str, str] = {}
    for key, forms in surfaces.items():
        top, count = forms.most_common(1)[0]
        if count >= min_count and count / totals[key] > min_share:
            case_map[key] = top
    return case_map


def restore_case(text: str, case_map: Dict[str, str] | None = None) -> str:
    """Capitalize sentence starts and known proper nouns."""
    case_map = case_map or {}
    out: List[str] = []
    at_start = True
    for word in text.split(" "):
        if word and word[0].isalnum():
            core = word.rstrip(".,;:!?)]}%")
            tail = word[len(core):]
            mapped = case_map.get(core.lower())
            if mapped is not None and core.islower():
                core = mapped
            elif at_start:
                core = core[0].upper() + core[1:]
            word = core + tail
            at_start = False
        if word and word[-1] in SENTENCE_END:
            at_start = True
        out.append(word)
    return " ".join(out)


def strip_prompt(text: str, prompt: str) -> str:
    """Remove the echoed prompt from the start of a completion."""
    text, prompt = text.strip(), prompt.strip()
    if prompt and text.lower().startswith(prompt.lower()):
        return text[len(prompt):].lstrip()
    return text


def postprocess(ids: Sequence[int], id_to_token: Dict[int, str],
                prompt: str = "", case_map: Dict[str, str] | None = None,
                trim: bool = True) -> str:
    """Token ids -> presentable text: drop specials, strip prompt, detokenize."""
    text = strip_prompt(detokenize(ids, id_to_token), prompt)
    text = restore_case(text, case_map)
    return trim_to_sentence(text) if trim else text
