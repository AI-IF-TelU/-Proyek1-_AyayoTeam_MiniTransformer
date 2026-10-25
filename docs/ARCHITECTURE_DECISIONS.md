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
## ADR-013 â€” Batas frekuensi vocabulary (`min_freq`) untuk C15

- Konteks: `TECH_SPEC.md` Â§3 versi baseline menyatakan "tidak ada batas vocab tetap". Pada percobaan C14, vocabulary hasil `fit` dari 720 dokumen berisi 19.192 tipe dengan 8.173 hapax (42,6% tipe). Token hapax mustahil diprediksi dan tidak mungkin dilatih dengan baik, tetapi tetap memakan parameter: 8.173 x 64 x 2 (embedding + LM head tak di-tie) = 1.046.144 parameter, 40,9% dari total model. Vocabulary juga menyebabkan 5,73% token val dan 4,97% token test menjadi `<unk>`.
- Keputusan: `Tokenizer.fit(texts, min_freq=1)` menerima parameter `min_freq` (default `1` = perilaku baseline, tanpa batas). Eksperimen C15 memakai `min_freq=2` sehingga vocabulary menjadi 11.019 dan coverage token train 97,19%. Perubahan ini aditif: pemanggil lama tanpa argumen tetap mendapat perilaku persis seperti baseline.
- Alasan: Menghapus hapax mengurangi parameter yang tidak terlatih sebesar ~1,05 juta (41% model) dan menurunkan biaya komputasi tanpa mengubah arsitektur. Default `1` menjaga kompatibilitas kontrak dan reproducibility artefak lama.
- Trade-off: `min_freq=2` menaikkan UNK val dari 5,73% menjadi 8,13% dan UNK test dari 4,97% menjadi 7,03%. Sebagian penurunan perplexity yang terukur adalah artefak metrik: `<unk>` menjadi token yang sering dan mudah diprediksi, bukan bukti model lebih memahami bahasa. Karena itu laporan C15 wajib mencantumkan (a) coverage token train, (b) UNK rate per split, dan (c) loss yang dihitung dengan token `<unk>` dikecualikan, agar perbandingan dengan C14 tetap jujur.
- Status: Accepted (diminta pemilik proyek 2026-10-24; menggantikan klausul "tidak ada batas vocab tetap" pada TECH_SPEC Â§3 untuk eksperimen C15).

## ADR-014 â€” Weight tying embedding dan LM head untuk C15

- Konteks: `TECH_SPEC.md` Â§6 versi baseline menyatakan bobot LM head tidak di-tie ke embedding. Pada C14, `embedding + LM head` menyerap 2.456.576 dari 2.556.672 parameter (96%). Dua matriks berukuran `V x d` yang tidak berbagi apa pun adalah pemborosan pada model `d_model=64`, dan matriks kedua tidak menerima sinyal gradien yang cukup dari 290.920 token latih.
- Keputusan: `MiniGPT(..., tie_embeddings: bool = False)` menerima flag opsional; default `False` mempertahankan perilaku baseline. Saat `True`, `lm_head` memakai `token_emb.weight` yang sama (transpose), dan `d_ff` tetap `4 * d_model`. Eksperimen C15 memakai `tie_embeddings=True` dengan `n_layers=4` sehingga total parameter menjadi ~1,43 juta, bukan ~2,56 juta.
- Alasan: Weight tying adalah praktik standar untuk language model kecil dan menghemat 1.228.288 parameter tanpa mengurangi `d_model`. Parameter yang dihemat dialihkan ke kedalaman (`n_layers` 2 -> 4), yang menurut literatur lebih bernilai daripada lebar embedding pada anggaran parameter tetap.
- Trade-off: Tying mengasumsikan ruang embedding input dan ruang logits output sebaiknya identik; asumsi ini bisa merugikan bila distribusi token masuk dan keluar sangat berbeda. `n_layers=4` menaikkan biaya attention dan waktu training sekitar 2x dibanding 2 layer. Kedua efek harus diukur, bukan diasumsikan menguntungkan.
- Status: Accepted (diminta pemilik proyek 2026-10-24; menggantikan klausul "tidak di-tie" pada TECH_SPEC Â§6 untuk eksperimen C15).

## ADR-015 â€” `context_length` 128 dan subset 1.800 artikel untuk C15

- Konteks: ADR-004 menetapkan `context_length=64` dan ADR-012 menetapkan subset 1.000 artikel. Data aktual menunjukkan median panjang dokumen 363 token, sehingga konteks 64 hanya mencakup ~18% artikel dan model tidak pernah melihat akhir dokumen. Rasio data terhadap parameter pada C14 adalah 290.920 token latih untuk 2.556.672 parameter (0,114 token/parameter), jauh di bawah titik di mana regularisasi bisa menolong.
- Keputusan: Eksperimen C15 memakai `context_length=128` dan subset 1.800 artikel (1.600 dari split `train`, 200 dari split `test`), dengan validasi tetap 10% dari train (160 artikel, seed 42). Arsitektur inti tidak berubah: tetap decoder-only, sinusoidal PE, causal MHA manual, pre-LayerNorm. `SinCosPositionalEncoding` tetap menerima `max_len` dari `context_length`, sehingga tidak ada perubahan kontrak modul.
- Alasan: Konteks 128 mencakup ~35% median dokumen dan memungkinkan model melihat batas kalimat, yang merupakan syarat minimum untuk koherensi lintas kalimat. Menambah data ke 1.800 artikel menurunkan rasio parameter/token dari 8,8 menjadi ~3,9, yang merupakan knob paling besar dan paling tidak berisiko terhadap kualitas. Keduanya masih berada dalam rentang yang diizinkan `DATASET_CARD.md` (subset 500-2.000 artikel) dan tidak mengubah arsitektur inti yang dilindungi ADR-001/ADR-002.
- Trade-off: Attention menjadi 4x lebih mahal (`O(B*T^2*d)`), dan jumlah segmen turun ~0,82x, sehingga waktu per epoch naik. Unduhan ulang dataset dari Hugging Face diperlukan dan jumlah artikel aktual setelah deduplikasi bisa sedikit di bawah 1.600. Semua angka aktual wajib dicatat di `DATASET_CARD.md`.
- Status: Accepted (diminta pemilik proyek 2026-10-24; menggantikan `context_length=64` pada ADR-004 dan subset 1.000 artikel pada ADR-012 untuk eksperimen C15).

## ADR-016 — Jumlah epoch C15: 20, bukan 10

- Konteks: `TECH_SPEC.md` §6 menetapkan `epochs=10` sebagai titik awal. C14 berhenti di epoch 10 dengan `val_loss` masih turun (6,4604 pada e10 vs 6,4813 pada e6, selisih di luar CI 95% per dokumen) sementara jadwal cosine sudah mencapai `LR_MIN=3e-5`. Artinya 10 epoch berhenti sebelum plateau, bukan sesudah.
- Keputusan: Eksperimen C15 memakai `epochs=20`. Tidak ada early stopping: seluruh 20 epoch dijalankan, dan artefak final tetap checkpoint `val_loss` per dokumen terendah (bukan epoch terakhir).
- Alasan: `epochs` adalah hiperparameter, bukan kontrak arsitektur, sehingga boleh diubah melalui eksperimen terdokumentasi (TECH_SPEC §1). Menambah epoch tidak menambah parameter dan tidak mengubah bentuk tensor apa pun, jadi risiko kontraknya nol. Pada C15 biaya per epoch juga lebih tinggi (context 128, 4 layer), sehingga 20 epoch tetap berada jauh di bawah batas waktu Kaggle.
- Trade-off: Waktu training berlipat dua dibanding C14. Bila `val_loss` justru naik sebelum epoch 20, notebook tetap menyelesaikan seluruh epoch (tidak berhenti otomatis) tetapi melaporkan epoch terbaik beserta daftar `tied_epochs`, sehingga tidak ada klaim "best" yang tidak didukung data.
- Status: Accepted (diminta pemilik proyek 2026-10-24; menggantikan angka `epochs=10` pada TECH_SPEC §6 untuk eksperimen C15).
