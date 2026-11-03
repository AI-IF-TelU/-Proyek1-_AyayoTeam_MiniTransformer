Ayayo MiniTransformer — Project Walkthrough &
Learning Guide
Repository: AI-IF-TelU/AyayoTeam_MiniTransformer Branch: master (master-only, tanpa branch/PR)
Commit acuan audit: 8f5fd09 ( feat(issues): hapus di project, karena sudah ada di menu issues
github , 2026-10-26 02:39:34 +0700) Jumlah commit pada master : 110 Tanggal audit: 2026-10-26
Disusun oleh: audit teknis otomatis (kode, artefak, test, history Git, issue lokal + GitHub) Anggota
tim: Dzaki Alwan Firjatullah (103012580006) · Muhammad Raihan Fahrifi (103012580017) · Firdaus
Akbar Amrullah (103012580011) · Rafa Suryaputra (103012580048)


0. Ringkasan Proyek dan Peta Pembelajaran

0.1 Apa yang dibangun
Ayayo MiniTransformer adalah model bahasa generatif kecil (Mini-GPT) berbahasa Indonesia yang
dilatih dari nol dengan PyTorch. Arsitekturnya decoder-only Transformer untuk next-token
prediction: diberikan potongan teks berita, model memprediksi token berikutnya, lalu token itu
ditambahkan ke konteks dan proses diulang sampai menghasilkan kalimat atau mencapai batas
token.
Yang membuat proyek ini bukan sekadar "memanggil library":
Komponen                                     Status implementasi                         Bukti
Sinusoidal positional encoding               manual, register_buffer non-trainable       src/model/positional_en
                                                                                         coding.py
Causal multi-head self-attention             manual (Q/K/V/O nn.Linear , reshape head,   src/model/attention.py
                                             mask aditif, softmax)
Decoder block Pre-LayerNorm + residual       manual                                      src/model/decoder_block
+ FFN GELU                                                                               .py
Tokenizer regex + vocabulary train-only      manual                                      src/data/tokenizer.py
Sliding window, shifting, padding, collate   manual                                      src/data/dataset.py
Training loop, loss, checkpoint, metrik      manual                                      src/train.py
JSONL
Greedy + sampling decoding terkontrol        manual                                      src/generate.py
Post-processing tampilan (detokenisasi,      manual                                      src/postprocess.py
kapitalisasi, trim)

Pemindaian sumber case-sensitive pada src/ untuk pola nn.Transformer , MultiheadAttention ,
torch.transformer , dan multi_head_attention_forward menghasilkan nol kemunculan (dijalankan ulang
pada audit ini). Artinya batasan tugas ("jangan pakai modul Transformer siap pakai untuk inti") benar-
benar dipatuhi.

0.2 Mengapa proyek ini dibuat
Tujuan pembelajaran, bukan produk. docs/PRD.md menetapkan lima sasaran yang bisa diuji: kode jalan
dari README, bentuk tensor sesuai kontrak, causal mask mencegah melihat masa depan, satu batch
training mengubah parameter, dan loss tercatat serta dianalisis. docs/PRD.md juga melarang klaim
bahwa keluaran model adalah berita faktual.