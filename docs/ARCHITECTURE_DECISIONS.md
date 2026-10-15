# Architecture Decision Records (ADR)

Gunakan format: konteks, keputusan, alasan, trade-off, dan status. Jangan mengubah keputusan yang disetujui secara diam-diam.

## ADR-001 — Mini-GPT berbasis Decoder-only Transformer
- Status: Accepted
- Keputusan: Membangun model bahasa kecil untuk next-token prediction menggunakan arsitektur decoder-only.
- Alasan: Sesuai dengan tugas Mini-Transformer dan tantangan manual Multi-Head Self-Attention.
- Trade-off: Model kecil mudah dilatih, tetapi kemampuan generasinya terbatas.

## ADR-002 — Implementasi attention manual
- Status: Accepted
- Keputusan: Mengimplementasikan causal Multi-Head Self-Attention sendiri menggunakan operasi dasar PyTorch.
- Alasan: Memenuhi tujuan pembelajaran dan rubrik dari-nol.
- Trade-off: Lebih banyak kode dan pengujian dibanding memakai modul Transformer lengkap.

## ADR-003 — Dataset berita bahasa Indonesia
- Status: Accepted
- Keputusan: Menggunakan subset Indonesian News Datasets.
- Alasan: Mengurangi waktu pengumpulan korpus dan menyediakan teks untuk language modeling.
- Trade-off: Korpus bersifat umum; label belum dikurasi dan provenance serta ketentuan sumber perlu ditinjau.

## ADR-004 — Konfigurasi awal kecil
- Status: Proposed
- Keputusan: Memulai dari 2 decoder blocks, 4 heads, `d_model=64`, context length 64.
- Alasan: Memudahkan debugging dan training pada perangkat yang terbatas.
- Trade-off: Kapasitas model dan kualitas generation terbatas.
- Catatan: Ubah status menjadi Accepted setelah tim menyetujui konfigurasi dan menguji bentuk tensor.

## ADR-005 — Contract-first parallel development
- Status: Accepted
- Keputusan: Definisikan interface dan tensor shapes sebelum modul dikerjakan paralel.
- Alasan: Mengurangi konflik integrasi antaranggota dan perbedaan output antar-AI agent.
- Trade-off: Perlu disiplin menjaga kontrak tetap konsisten.

## ADR-006 — Logging berbasis adapter
- Status: Proposed
- Keputusan: Setiap tool menggunakan adapter, sementara format output diseragamkan menjadi JSONL dan laporan Markdown.
- Alasan: Tool berbeda mengekspos event dan transcript dengan cara berbeda.
- Trade-off: Setiap adapter perlu diuji; logging dianggap aktif hanya setelah smoke test berhasil.
