## 0. Pemilik tugas

- **Pemilik (rekomendasi):** Rafa Suryaputra — Documentarian & Error Handler.

## 1. Tujuan

Menyiapkan struktur unit test berbasis kontrak `docs/TECH_SPEC.md`, mengintegrasikan hasil tes Issues A, B, dan C, menyediakan pemeriksaan otomatis acceptance criteria yang wajib benar-benar diuji, serta memelihara dokumentasi proses pengujian, debugging, dan hasil eksperimen. Tidak menggantikan tanggung jawab penulis modul memperbaiki kode mereka.

## 2. Konteks teknis dan file terkait

- `docs/TECH_SPEC.md` §3–§6 (seluruh kontrak modul), §7 (kompleksitas); `docs/ARCHITECTURE_DECISIONS.md` ADR-005 (contract-first).
- `docs/AI_RULES.md` §5 (output AI), §7 (review dan push master-only).
- Target: struktur `tests/` (conftest + helpers; susunan final dikonfirmasi saat integrasi), dokumentasi proses testing di `docs/`.

## 3. Ruang lingkup

1. Menyiapkan struktur `tests/` dan runner yang disepakati (verifikasi dulu apakah `pytest` boleh dipakai; tanpa dependency baru tanpa persetujuan koordinator).
2. Menyusun tes kontrak: tensor shapes, causal masking, tokenizer, data loader, training, generation — memeriksa perilaku yang diharapkan, bukan hanya "tidak error".
3. Menyiapkan pemeriksaan otomatis acceptance criteria wajib (vocabulary leakage, window lintas dokumen, causal mask, padding ignore di loss, aturan stop generation, dsb).
4. Mengintegrasikan tes dari Issues A, B, dan C; menjalankan bersama saat seluruh modul tersedia.
5. Mendokumentasikan proses pengujian, debugging, dan hasil eksperimen (berdasarkan output aktual).
6. Melaporkan kegagalan ke penulis modul dan menindaklanjuti; tidak memperbaiki kode modul sendiri tanpa persetujuan.

## 4. Di luar scope

- Implementasi/perbaikan kode modul A/B/C tanpa persetujuan pemiliknya.
- Mengubah kontrak publik modul secara sepihak.
- Mengklaim keberhasilan tes yang belum dijalankan.

## 5. Dependensi

- Pengerjaan pengujian dapat dimulai paralel menggunakan kontrak yang sudah dikunci (paralel dengan A/B/C/E).
- Integrasi penuh tes menunggu modul dari Issues A, B, C tersedia dan lulus tes lokalnya.
- Hasil kegagalan menjadi umpan balik untuk A/B/C.

## 6. Interface dan kontrak yang diuji (dari TECH_SPEC)

Ringkasan kontrak yang harus jadi dasar test case:
- §3 Tokenizer: `fit`, `encode`, `decode`, `vocab_size`; urutan id special `<pad>=0, <bos>=1, <eos>=2, <unk>=3`; regex `r"\w+|[^\w\s]"` setelah lowercase.
- §4 Dataset: batch `x/y [B, 64]` int64; `x[i,t] == y[i,t-1]` posisi non-pad; tanpa window lintas dokumen.
- §5 Loss: `CrossEntropyLoss(ignore_index=pad_id)`; posisi pad tidak berkontribusi.
- §6 Model: shapes PE/Attention/DecoderBlock/MiniGPT; `ValueError` pada `T > max_len` dan `d_model % n_heads != 0`; causal mask; training seed 42; generation greedy berhenti di `eos_id`/`max_new_tokens`.

## 7. Task checklist berurutan

Kerjakan **satu subtask pada satu waktu**, dari atas ke bawah. Setiap pemilik modul (A/B/C) tetap wajib membuat dan menjalankan unit test atas kode mereka sendiri; Issue ini mengoordinasikan dan melengkapi pengujian lintas modul.

- [ ] **D1. Periksa acceptance criteria pada Issue #2–#4.** Kumpulkan daftar kontrak dan kriteria yang wajib diverifikasi lintas modul; tandai mana yang sudah dituliskan tes lokal oleh pemilik modul. *Hasil:* matriks kontrak→test→status.
- [ ] **D2. Terapkan framework testing resmi `pytest` (ditetapkan koordinator 2026-10-19).** Pakai `pytest` (sudah di `requirements.txt`); catat keputusan dan perintah runner di laporan. *Hasil:* keputusan runner terdokumentasi.
- [ ] **D3. Siapkan struktur unit test berdasarkan kontrak modul.** Buat `tests/` (conftest + helper shape/data) sesuai `TECH_SPEC.md` §3–§6. *Hasil:* struktur test ter-commit, bisa dijalankan (meski sebagian test menunggu modul).
- [ ] **D4. Buat tes tokenizer dan data pipeline.** Id special, lowercase, `<unk>`, urutan frekuensi, relasi `x[i,t]==y[i,t-1]`, no-window-crossing, padding. *Hasil:* test kontrak pipeline data siap; hasil aktual saat modul A tersedia.
- [ ] **D5. Buat tes Positional Encoding dan causal masking.** Shape, buffer non-trainable, `ValueError T > max_len`, invariance causal mask. *Hasil:* test kontrak PE/MHA siap.
- [ ] **D6. Buat tes Decoder Block dan MiniGPT.** Shape forward, residual/pre-norm, gradient mengalir; `ValueError T > context_length` hanya untuk MiniGPT (DecoderBlock tidak mewajibkannya — kontrak TECH_SPEC §6). *Hasil:* test kontrak model siap.
- [ ] **D7. Buat tes training step, loss, dan pembaruan parameter.** Loss finite, bobot berubah setelah step, posisi pad diabaikan di loss. *Hasil:* test kontrak training siap.
- [ ] **D8. Jalankan tes ketika tiap modul tersedia.** Jalankan per modul saat Issue A/B/C menyelesaikan komponennya; catat command, output, dan status pass/fail aktual. *Hasil:* status tes lintas modul terbaharui.
- [ ] **D9. Identifikasi error dan catat bukti reproduksinya.** Tiap kegagalan dicatat dengan traceback/error aktual dan langkah reproduksi; laporkan ke pemilik modul. *Hasil:* log kegagalan berdasar bukti.
- [ ] **D10. Verifikasi perbaikan berdasarkan tes aktual.** Setelah pemilik modul memperbaiki, jalankan ulang tes dan catat output. *Hasil:* temuan tertutup dengan bukti tes lulus.
- [ ] **D11. Jalankan tes integrasi setelah komponen yang dibutuhkan tersedia.** Seluruh tes kontrak A/B/C dijalankan bersama dalam satu run (e.g. tokenizer→dataset→model→loss→generation). *Hasil:* satu perintah menjalankan seluruh suite tanpa mengubah kontrak sepihak.
- [ ] **D12. Susun dokumentasi pengujian dan hasil eksperimen.** Rangkum perintah runner, matriks kontrak→test, hasil integrasi, dan riwayat debugging di `docs/` serta README. *Hasil:* dokumentasi testing lengkap.
- [ ] **D13. Susun laporan akhir berdasarkan bukti aktual.** Rekap seluruh acceptance criteria Issues #2–#6 terverifikasi/tidak, dengan bukti konkret; tanpa klaim keberhasilan yang belum dijalankan. *Hasil:* laporan akhir ber-evidence.

## 8. Instruksi pengerjaan setiap subtask

1. Baca kembali bagian spesifikasi yang relevan (`TECH_SPEC.md` §3–§7, ADR-005, `AI_RULES.md` §5/§7).
2. Minta AI menjelaskan tujuan subtask, kontrak yang diuji, dan bagaimana test membuktikan perilaku (bukan sekadar "tidak error") SEBELUM menulis kode.
3. Implementasikan satu subtask saja; test bukan dimaksudkan menggantikan tanggung jawab pemilik modul.
4. Jalankan test dan amati output aktual; jangan mengarang hasil.
5. Jika integrasi menemukan ketidakcocokan kontrak, laporkan ke pemilik modul dan koordinator — jangan mengubah kontrak sepihak (ADR bila perlu).
6. Simpan log AI (raw JSONL + laporan Markdown) sesuai ADR-006.
7. Minta review kepada koordinator/anggota lain sebelum menyatakan subtask selesai.
8. Centang checkbox subtask hanya setelah hasil dan test benar-benar terverifikasi.

## 9. Aturan berhenti

- Setelah satu subtask selesai dan diverifikasi, **berhenti**. Jangan mengerjakan subtask berikutnya tanpa instruksi eksplisit.
- Jangan memperbaiki kode modul A/B/C sendiri tanpa persetujuan pemilik; laporkan kegagalan dan tunggu tindak lanjut.
- Jika hasil test gagal atau log AI belum tersimpan, **jangan lanjut**; tangani dulu.
- Jangan mengklaim test lulus jika belum dijalankan; jangan mengarang error, traceback, atau hasil integrasi.

## 10. Acceptance criteria (wajib benar-benar diuji)

- [ ] Seluruh tes dapat dijalankan secara konsisten (runner yang disepakati, semua anggota bisa mereproduksi).
- [ ] Test case memeriksa perilaku yang diharapkan (masking, leakage, stop rule, dsb), bukan sekadar memastikan kode tidak error.
- [ ] Hasil tes dan error dicatat berdasarkan output aktual; tidak dikarang.
- [ ] Integrasi dilakukan tanpa mengubah kontrak publik secara sepihak (perubahan berkoordinasi dengan penulis modul + ADR bila perlu).
- [ ] Seluruh kegagalan relevan dilaporkan dan ditindaklanjuti dengan bukti.
- [ ] Matriks kontrak→test→status (D1) lengkap dan mencerminkan acceptance criteria Issues #2–#6.
- [ ] Setiap subtask D1–D13 memiliki bukti berupa output aktual atau test yang dijalankan.

## 11. Unit test yang diperlukan

- Kontrak lintas modul: shape test, causal mask invariance, vocab leakage, no-window-crossing, padding + ignore_index, checkpoint roundtrip, aturan stop generation.
- Koordinasi: test yang ditulis Issue A/B/C disatukan; konflik/resolusi didokumentasikan.

## 12. Aturan logging AI

- Ikuti `docs/AI_RULES.md` §6, `docs/AI_LOG_TEMPLATE.md`, dan ADR-006.
- Raw log di `docs/ai-logs/raw/<member-id>/`, laporan di `docs/ai-logs/reports/`; dilarang menulis API key, token, password, atau data sensitif.

## 13. Dokumentasi yang harus diperbarui

- Dokumentasi proses pengujian, perintah runner, dan hasil integrasi di `docs/` (bukan mengubah `TECH_SPEC.md` tanpa proses ADR).
- Laporan AI di `docs/ai-logs/reports/`.
- README — instruksi menjalankan seluruh tes.