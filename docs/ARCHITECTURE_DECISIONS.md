# Architecture Decision Records (ADR)

Format tiap entri: konteks, keputusan, alasan, trade-off, status. Jangan mengubah keputusan yang disetujui secara diam-diam; perubahan harus lewat ADR baru atau revisi berstatus.

Status yang dipakai: `Accepted` (disetujui), `Proposed` (masih perlu persetujuan). Basis persetujuan pada Issue #1 (Step 2) adalah pengesahan koordinator atas daftar keputusan baseline; persetujuan anggota lain dan verifikasi bentuk tensor pada tahap implementasi tetap wajib dicatat, bukan dikarang.

## ADR-001 — Mini-GPT berbasis Decoder-only Transformer
- Konteks: Tugas meminta model bahasa kecil dari-nol; tim 4 anggota, durasi 2 minggu.
- Keputusan: Membangun model bahasa untuk next-token prediction menggunakan arsitektur decoder-only.
- Alasan: Sesuai tugas Mini-Transformer dan rubrik implementasi manual Multi-Head Self-Attention.
- Trade-off: Model kecil mudah dilatih, tetapi kualitas generasi terbatas.
- Status: Accepted.

## ADR-002 — Implementasi attention dan positional encoding manual
- Konteks: Rubrik mengharuskan implementasi dari-nol; `nn.Transformer*`/`nn.MultiheadAttention` dilarang menggantikan inti.
- Keputusan: Menerapkan causal Multi-Head Self-Attention dan sinusoidal positional encoding sendiri dengan operasi dasar PyTorch.
- Alasan: Memenuhi tujuan pembelajaran dan batas library `AGENTS.md`/`TECH_SPEC.md` §2.
- Trade-off: Lebih banyak kode dan pengujian dibanding modul Transformer lengkap.
- Status: Accepted.

## ADR-003 — Dataset berita bahasa Indonesia
- Konteks: Perlu korpus teks untuk language modeling tanpa scrap dari nol.
- Keputusan: Memakai subset Indonesian News Datasets (kolom `content`), 500–2.000 artikel untuk pipeline awal.
- Alasan: Mempercepat penyiapan korpus dan menyediakan teks berbahasa Indonesia.
- Trade-off: Label belum dikurasi; provenance dan lisensi (CC BY-NC 4.0) serta hak sumber wajib ditinjau; hasil generasi hanya demonstrasi pendidikan.
- Status: Accepted.

## ADR-004 — Konfigurasi awal kecil
- Konteks: Model pertama harus bisa di-debug dan dilatih CPU; dimensi harus konsisten antar modul.
- Keputusan: Mulai dari `n_layers=2`, `n_heads=4`, `d_model=64`, `context_length=64`, `d_ff=256`. `d_model % n_heads == 0` (head_dim 16).
- Alasan: Dimensi kecil memudahkan debugging; `B·H·T² = 32·4·4096` ≈ 2 MiB per matriks attention.
- Trade-off: Kapasitas model dan kualitas generasi terbatas.
- Status: Accepted (baseline disahkan via Issue #1 Step 2). Catatan: verifikasi bentuk tensor aktual dilakukan pada langkah implementasi; jika shape test menemukan ketidakcocokan, revisi ADR wajib dicatat.

## ADR-005 — Contract-first parallel development
- Konteks: Empat anggota memakai AI coding agent berbeda; risiko drift interface antar modul tinggi.
- Keputusan: Definisikan interface, nama fungsi/kelas, parameter, dan tensor shapes sebelum modul dikerjakan paralel.
- Alasan: Mengurangi konflik integrasi dan perbedaan output antar agent.
- Trade-off: Perlu disiplin menjaga kontrak tetap konsisten selama implementasi.
- Status: Accepted.

## ADR-006 — Pencatatan log AI
- Konteks: `AI_RULES.md` §6 mewajibkan prompt, respons, event tool, dan error terekam; bentuk event tiap agent berbeda.
- Keputusan: Adapter logging per tool; format raw distandarkan ke JSONL di `docs/ai-logs/raw/<member-id>/` dan laporan Markdown mengikuti `docs/AI_LOG_TEMPLATE.md`; konten rahasia di-redact.
- Alasan: Tool berbeda mengekspos event/transcript secara berbeda; raw log wajib jadi bukti.
- Trade-off: Setiap adapter perlu diuji; laporan otomatis masih meninggalkan field manual `[Isi manual]` yang wajib dilengkapi anggota.
- Status keputusan: Accepted.
- Tingkat implementasi/verifikasi (terpisah dari keputusan): plugin `.kilo/plugin/mini-transformer-logger.ts` aktif dan teruji pada Kilo untuk anggota `raihanfahrifi-80017` (dua sesi, prompt + respons tertangkap: 62 dan 1174 baris event; redaction rahasia aktif). Ini **bukan** bukti seluruh anggota lulus: tiap anggota wajib menjalankan smoke test pada instalasinya sendiri sebelum coding.

## ADR-007 — Internals Decoder Block: pre-norm, FFN, aktivasi, dropout, epsilon
- Konteks: `TECH_SPEC.md` lama menunda keputusan pre-norm/post-norm; FFN, GELU, dropout, epsilon belum eksplisit; Issue #1 mencantumkannya sebagai kandidat.
- Keputusan: Pre-LayerNorm pada Decoder Block; `d_ff = 4 * d_model`; aktivasi GELU; dropout `0.1` (pada skor attention, output attention, dan FFN); LayerNorm epsilon `1e-5`.
- Alasan: Pre-norm lebih stabil untuk model kecil dan sejalan GPT-2 style; komponen lain mengikuti kandidat baseline Issue #1 yang telah disetujui.
- Trade-off: Pre-norm berbeda dari formulasi post-norm klasik dan menggeser beban ke residual; dropout mengurangi kapasitas model.
- Status: Accepted (Issue #1 Step 2).

## ADR-008 — Tokenizer regex, lowercase, special tokens, dan padding
- Konteks: Tokenizer lama hanya menyebut "regex berbasis kata dan tanda baca"; aturan padding dan `<pad>` belum ada; Issue #1 menuntut aturan token khusus tidak ambigu.
- Keputusan: Regex `r"\w+|[^\w\s]"`; lowercase sebelum tokenisasi; vocab hanya dari train. Special tokens ber-ID tetap: `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3`. `<bos>`/`<eos>` disisipkan sebagai token id setelah tokenisasi (bukan string literal ke regex). Padding dilakukan pada batching; loss memakai `ignore_index=pad_id`.
- Alasan: Lowercase mengecilkan vocab untuk model kecil; penambahan `<pad>` memungkinkan batch panjang seragam tanpa membuang dokumen pendek.
- Trade-off: Lowercase menghilangkan beda case proper noun; `decode` tidak menjamin roundtrip eksak.
- Status: Accepted (Issue #1 Step 2).

## ADR-009 — Strategi generation greedy
- Konteks: Kontrak generation belum ada di dokumen lama; Issue #1 meminta perilaku generation eksplisit.
- Keputusan: Generation v1 greedy (argmax); berhenti pada `<eos>` atau `max_new_tokens`; konteks dibatasi `context_length` (window geser); `temperature` sampling opsional, tidak wajib pada implementasi pertama.
- Alasan: Sederhana, deterministik, cukup untuk demonstrasi dan test; sampling bisa ditambahkan belakangan tanpa ubah arsitektur.
- Trade-off: Greedy cenderung repetitif dibanding sampling.
- Status: Accepted (Issue #1 Step 2).

## ADR-010 — Strategi split dan pembuatan window
- Konteks: `TECH_SPEC.md` §5 dan `DATASET_CARD.md` menuntut split per dokumen dan cegah kebocoran; rasio dan seed belum ditetapkan.
- Keputusan: Urutan — deduplikasi, split per dokumen (80/10/10, seed 42) hanya sebagai fallback jika split bawaan tidak tersedia/tidak layak; split bawaan yang terverifikasi dipertahankan tanpa resplit. Setelah split: tokenisasi, sisipkan `bos_id`/`eos_id`, lalu window sliding panjang 65 stride 1; dokumen pendek dipakai sebagai pasangan pendek + pad saat batching; dilarang window lintas dokumen.
- Alasan: Split per dokumen mencegah kebocoran antarartikel; window stride 1 memaksimalkan data dari subset kecil.
- Trade-off: Stride 1 menambah jumlah training sample (redudansi antar window overlapping); seed tetap menjadikan hasil reproducible.
- Status: Accepted (Issue #1 Step 2).

## ADR-011 — Format metrik output: JSONL
- Konteks: `TECH_SPEC.md` §6 membiarkan dua opsi format metrik ("CSV/JSONL"); Issue C butuh satu format pasti.
- Keputusan: Metrik training per-epoch ditulis sebagai JSONL ke `outputs/metrics/` (satu objek JSON per baris).
- Alasan: JSONL append-friendly untuk logging per-epoch, mudah dibaca ulang dengan `pandas`/`json`; konsisten dengan raw AI log yang sudah JSONL.
- Trade-off: Kurang tabular dibanding CSV untuk spreadsheet langsung.
- Status: Accepted (disetujui koordinator 2026-10-19; verifikasi implementasi dicatat di Issue C).

## ADR-012 — Jumlah subset dataset dan strategi validation split
- Konteks: `TECH_SPEC.md` §1 dan `DATASET_CARD.md` membiarkan range subset 500–2.000 artikel dan hanya menyebut fallback split 80/10/10; dataset bawaan menyediakan split train (25.8k) dan test (6.46k) tetapi tidak ada split validation.
- Keputusan: Subset = 1.000 artikel. Pertahankan split bawaan train/test tanpa resplit (ADR-010). Validation diambil 10% dari split train (seed 42). Fallback 80/10/10 tidak dipakai.
- Alasan: Data HF diverifikasi punya split bawaan; test bawaan tidak boleh diresplit; validation tetap dibutuhkan untuk memantau loss per-epoch (Issue C) sehingga disisihkan dari train secara deterministik. 1.000 artikel cukup untuk model kecil d64 di CPU dengan waktu training realistis.
- Trade-off: Rasio akhir bukan 80/10/10 murni (~72/8/20 terhadap total dataset); subset kecil membatasi kualitas generasi.
- Status: Accepted (disetujui koordinator 2026-10-19; angka aktual diverifikasi pada Issue A dan dicatat di DATASET_CARD).