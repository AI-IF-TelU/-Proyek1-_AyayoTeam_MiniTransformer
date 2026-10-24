import unittest
from src.data.tokenizer import Tokenizer

class TestTokenizerBasic(unittest.TestCase):
    def setUp(self):
        self.tokenizer = Tokenizer()
        self.tokenizer.fit(["halo dunia 123!!!"])

    def test_tokenizer_basic(self):
        # Test lowercase, splitting using encode or checking encode behavior
        encoded = self.tokenizer.encode("Halo Dunia")
        # Since 'halo' and 'dunia' are in vocab, they shouldn't be unk (3)
        self.assertNotIn(3, encoded)
        self.assertEqual(len(encoded), 2)

    def test_tokenizer_special_chars(self):
        # Test symbols and digits
        encoded = self.tokenizer.encode("!!! 123")
        self.assertNotIn(3, encoded)
        self.assertEqual(len(encoded), 4)

    def test_tokenizer_unknown(self):
        # Test <unk> fallback
        encoded = self.tokenizer.encode("xyz")
        self.assertEqual(encoded, [3]) # <unk> id is 3

class TestTokenizerLeakage(unittest.TestCase):
    def test_no_vocab_leakage(self):
        train_texts = ["halo dunia ini latihan training."]
        val_texts = ["halo dunia baru, validation test."]

        tokenizer = Tokenizer()
        tokenizer.fit(train_texts)

        # Cek token baru di val/test seperti "baru" dan "," (koma) tidak ada di vocab train
        train_vocab = set(tokenizer.token_to_id.keys())
        
        self.assertIn("halo", train_vocab)
        self.assertIn("dunia", train_vocab)
        self.assertNotIn("baru", train_vocab)
        self.assertNotIn(",", train_vocab)

        # Cek encoding val/test menggunakan <unk> (id 3) untuk token asing
        encoded_val = tokenizer.encode("baru")
        self.assertEqual(encoded_val, [3])

        # Cek ukuran vocab sesuai train saja + special tokens (4)
        # special tokens: <pad>=0, <bos>=1, <eos>=2, <unk>=3
        # train tokens unik: halo, dunia, ini, latihan, training, .
        expected_size = 4 + 6
        self.assertEqual(tokenizer.vocab_size, expected_size)


class TestTokenizerFromVocab(unittest.TestCase):
    """Jalur restore resmi dari checkpoint (F-D9-01)."""

    def setUp(self):
        self.fitted = Tokenizer()
        self.fitted.fit(["presiden indonesia mengumumkan kebijakan baru", "jakarta cuaca cerah"])

    def test_from_vocab_restores_both_mappings_and_size(self):
        restored = Tokenizer.from_vocab(self.fitted.token_to_id)
        self.assertEqual(restored.token_to_id, self.fitted.token_to_id)
        self.assertEqual(restored.id_to_token, self.fitted.id_to_token)
        self.assertEqual(restored.vocab_size, self.fitted.vocab_size)

    def test_from_vocab_makes_decode_work(self):
        restored = Tokenizer.from_vocab(self.fitted.token_to_id)
        text = "presiden indonesia"
        self.assertEqual(restored.decode(restored.encode(text)), text)

    def test_from_vocab_keeps_special_token_ids(self):
        restored = Tokenizer.from_vocab(self.fitted.token_to_id)
        self.assertEqual(restored.encode("halo"), [3])
        self.assertEqual(restored.decode([1, 2, 0]), "")

    def test_from_vocab_rejects_empty_vocab(self):
        with self.assertRaises(ValueError):
            Tokenizer.from_vocab({})

    def test_from_vocab_rejects_duplicate_ids(self):
        with self.assertRaises(ValueError):
            Tokenizer.from_vocab({"a": 4, "b": 4})


class TestTokenizerOrder(unittest.TestCase):
    def test_encode_preserves_text_order(self):
        """encode mengembalikan id sesuai urutan kemunculan, bukan urutan vocab."""
        tokenizer = Tokenizer()
        tokenizer.fit(["b a c"])
        encoded = tokenizer.encode("c a b b")
        expected = [
            tokenizer.token_to_id["c"],
            tokenizer.token_to_id["a"],
            tokenizer.token_to_id["b"],
            tokenizer.token_to_id["b"],
        ]
        self.assertEqual(encoded, expected)

    def test_vocab_size_equals_specials_plus_unique_train_tokens(self):
        """vocab_size = 4 special token + jumlah token unik train."""
        tokenizer = Tokenizer()
        tokenizer.fit(["halo dunia halo", "dunia tes"])
        # unik: halo, dunia, tes -> 3 + 4 = 7
        self.assertEqual(tokenizer.vocab_size, 4 + 3)

if __name__ == "__main__":
    unittest.main()
