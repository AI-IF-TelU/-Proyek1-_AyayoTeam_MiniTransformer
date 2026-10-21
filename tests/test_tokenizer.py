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

if __name__ == "__main__":
    unittest.main()
