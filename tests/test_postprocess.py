"""Tests for display-layer post-processing (Tier 1, no retrain)."""

from src.postprocess import (build_case_map, detokenize, postprocess,
                             restore_case, strip_prompt, trim_to_sentence)

ID_TO_TOKEN = {
    0: "<pad>", 1: "<bos>", 2: "<eos>", 3: "<unk>",
    4: "jakarta", 5: "-", 6: "menteri", 7: "koordinator", 8: "(", 9: "joko",
    10: "widodo", 11: ")", 12: ".", 13: "viva", 14: ",", 15: "dia", 16: "menilai",
}


def ids(*tokens):
    return [k for k in tokens]


def test_detokenize_attaches_terminators_and_closing_brackets():
    out = detokenize([4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], ID_TO_TOKEN)
    assert out == "jakarta - menteri koordinator (joko widodo). viva, dia"


def test_detokenize_drops_special_tokens():
    assert detokenize([1, 4, 3, 2], ID_TO_TOKEN) == "jakarta"
    assert detokenize([3], ID_TO_TOKEN) == ""


def test_trim_to_sentence_cuts_trailing_fragment():
    text = "satu. dua? tiga , potong"
    assert trim_to_sentence(text) == "satu. dua?"


def test_trim_to_sentence_keeps_text_without_terminator():
    assert trim_to_sentence("tanpa titik") == "tanpa titik"


def test_strip_prompt_removes_echoed_prompt():
    assert strip_prompt("presiden indonesia (jokowi).", "presiden indonesia") == "(jokowi)."
    assert strip_prompt("hal lain", "presiden indonesia") == "hal lain"


def test_build_case_map_keeps_only_words_that_are_mostly_capitalized():
    corpus = ["Para menteri ke Jakarta Menteri Koordinator",
              "dua menteri ke Jakarta menteri Koordinator",
              "tiga menteri koordinator di Jakarta"]
    case_map = build_case_map(corpus, min_count=2)
    assert case_map["jakarta"] == "Jakarta"
    assert case_map["koordinator"] == "Koordinator", "2 of 3 capitalized is a majority"
    assert "menteri" not in case_map, "mostly-lowercase word is not a proper noun"


def test_build_case_map_rejects_low_confidence_entries():
    corpus = ["kata Aku pergi", "kata aku pergi", "kata aku pergi", "kata aku pergi"]
    assert "aku" not in build_case_map(corpus, min_count=1, min_share=0.5)


def test_build_case_map_skips_sentence_initial_words():
    corpus = ["Saat itu hujan.", "Saat itu panas.", "Saat itu dingin."]
    case_map = build_case_map(corpus, min_count=2)
    assert "saat" not in case_map, "sentence-initial capitals are not proper nouns"


def test_restore_case_capitalizes_sentence_start_and_proper_nouns():
    out = restore_case("menteri jakarta. dia menilai", {"jakarta": "Jakarta",
                                                       "menteri": "Menteri"})
    assert out == "Menteri Jakarta. Dia menilai"


def test_postprocess_end_to_end_ends_at_sentence_boundary():
    text = postprocess([4, 5, 6, 7, 12, 13, 14, 15, 16], ID_TO_TOKEN,
                       prompt="jakarta - menteri", trim=True)
    assert text == "Koordinator."


def test_postprocess_without_trim_keeps_trailing_fragment():
    text = postprocess([4, 5, 6, 7, 12, 13, 14, 15, 16], ID_TO_TOKEN,
                       prompt="jakarta - menteri", trim=False)
    assert text == "Koordinator. Viva, dia menilai"
