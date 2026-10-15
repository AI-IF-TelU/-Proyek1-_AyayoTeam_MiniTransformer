# Product Requirements Document (PRD)

## 1. Tujuan
Membangun Mini-GPT berukuran kecil yang mempelajari pola teks berita bahasa Indonesia dan memprediksi token berikutnya berdasarkan konteks sebelumnya.

## 2. Target pengguna
- Mahasiswa yang mempelajari Generative AI dan Natural Language Processing.
- Dosen/evaluator yang memeriksa implementasi, training, evaluasi, kompleksitas, dan dokumentasi proyek.

## 3. Ruang lingkup
- Menggunakan subset dari Indonesian News Datasets.
- Tokenisasi, vocabulary, dan pembuatan data next-token prediction.
- Implementasi manual sinusoidal positional encoding dan causal Multi-Head Self-Attention.
- Decoder-only Transformer kecil dengan training loop.
- Evaluasi loss dan contoh text generation.
- Unit test, dokumentasi, riwayat Git, dan log interaksi AI.

## 4. Di luar ruang lingkup
- Chatbot produksi atau aplikasi publik.
- Menggunakan pretrained GPT atau API GPT sebagai model utama.
- Mengklaim bahwa hasil generasi berita adalah fakta terkini atau terverifikasi.
- Membangun UI kompleks sebelum model inti selesai.

## 5. Kriteria keberhasilan
- Kode dapat dijalankan dari instruksi README.
- Bentuk tensor sesuai kontrak teknis.
- Causal mask mencegah akses ke token masa depan.
- Training batch berjalan dan parameter model berubah.
- Training/validation loss tercatat dan dianalisis.
- Model dapat menghasilkan kelanjutan teks setelah training.
- Tes, keputusan arsitektur, provenance dataset, dan log AI tersedia.

## 6. Batasan proyek
- Tim: 4 anggota.
- Durasi target: 2 minggu.
- Framework: Python + PyTorch.
- Workflow: Agile Kanban + Contract-First Development + GitHub Flow.
