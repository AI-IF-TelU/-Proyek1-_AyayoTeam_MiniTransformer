import unittest
from src.data.tokenizer import Tokenizer

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
