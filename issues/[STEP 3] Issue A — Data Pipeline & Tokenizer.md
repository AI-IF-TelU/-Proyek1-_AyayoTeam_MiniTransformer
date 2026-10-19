## 0. Pemilik tugas

- **Pemilik (rekomendasi):** Dzaki Alwan — Data Pipeline Engineer.

## 1. Tujuan

Membangun pipeline data end-to-end: mengakses Indonesian News Datasets, memilih subset 1.000 artikel, memvalidasi isi/metadata/lisensi, membangun tokenizer regex + vocabulary dari data train, membangun pasangan input-target (sliding window + padding), dan data loader sesuai kontrak `docs/TECH_SPEC.md`.

## 2. Konteks teknis dan file terkait

- `docs/TECH_SPEC.md` §3 (tokenizer), §4 (dataset), §8 (split).
- `docs/DATASET_CARD.md`, `docs/ARCHITECTURE_DECISIONS.md` ADR-003, ADR-008, ADR-010.
- Dataset: https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets (kolom `content`).
- File target: `src/data/tokenizer.py`, `src/data/dataset.py` (susunan folder final dikonfirmasi koordinator 2026-10-19 — Opsi 1, tetap per kontrak TECH_SPEC §6).
- Konfigurasi: `context_length=64`, `<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3`, seed 42.
- Subset & split (keputusan koordinator 2026-10-19, ADR-012): **1.000 artikel**; pertahankan split bawaan train/test (25.8k/6.46k) tanpa resplit; validation diambil 10% dari split train (seed 42). Fallback 80/10/10 **tidak dipakai**.
- Lokasi penyimpanan: unduhan subset di `data/raw/`; hasil olahan (dedup/split/tokenized) di `data/processed/` (keputusan koordinator 2026-10-19).

## 3. Ruang lingkup

1. Unduh dataset; pilih subset 1.000 artikel kolom `content`.
2. Periksa metadata kolom/split yang tersedia, lisensi (CC BY-NC 4.0) dan syarat penggunaan terkini, baris kosong, duplikasi konten ternormalisasi.
3. Implementasi tokenizer sesuai kontrak §3: `fit(texts)`, `encode(text)`, `decode(ids)`, properti `vocab_size`.
4. Implementasi dataset sesuai §4: deduplikasi → split per dokumen → tokenisasi → sisipkan `bos_id`/`eos_id` → sliding window (65, stride 1; dokumen pendek → pasangan pendek, pad saat batching) → `DataLoader` dengan collate pad (0).
5. Vocabulary dibangun HANYA dari split train.
6. Unit test (bagian 8).
7. Mengisi kolom "Catatan eksperimen" di `docs/DATASET_CARD.md` dengan hasil aktual terverifikasi.

## 4. Di luar scope

- Implementasi komponen inti model (Issue B), MiniGPT/training/generation (Issue C), integrasi tes (Issue D), validasi logging (Issue E).
- Me-resplit test split bawaan yang terverifikasi.
- Fit vocab dari validation/test.
- Menambah dependency baru tanpa persetujuan koordinator.

## 5. Dependensi

- Bergantung pada kontrak final: `docs/TECH_SPEC.md` §3–4, §8 (sudah dikunci di Issue #1).
- Paralel penuh dengan Issue B, C, D, E.
- Tidak menunggu komponen model mana pun.

## 6. Interface dan kontrak (dari TECH_SPEC)

- `tokenizer.py`:
  - `fit(texts: Sequence[str]) -> None` — vocab hanya dari data train; urutan id `<pad>=0, <bos>=1, <eos>=2, <unk>=3`, lalu token hasil regex `r"\w+|[^\w\s]"` diurutkan berdasarkan frekuensi (tanpa batas vocab tetap).
  - `encode(text: str) -> list[int]` — lowercase → tokenisasi regex → token di luar vocab menjadi `<unk>`.
  - `decode(ids: Sequence[int]) -> str` — gabung dengan spasi lalu `strip`; special token tidak dirender. Roundtrip `decode(encode(t)) == t` TIDAK dijamin (perilaku terdokumentasi, bukan bug).
  - `vocab_size: int` tersedia setelah `fit`.
  - `<bos>`/`<eos>` disisipkan sebagai token id pada tahap dataset, bukan string literal ke regex.
- `dataset.py` (urutan wajib): deduplikasi → split per dokumen 80/10/10 seed 42 (fallback, hanya jika split bawaan tidak tersedia/tidak layak; split bawaan yang terverifikasi dipertahankan) → tokenisasi → bos/eos → window.
- Output batch: `x [B, T] int64`, `y [B, T] int64`, `T = context_length = 64`; `x[i, t] == y[i, t-1]` untuk semua posisi non-pad; posisi pad di `y` = `pad_id`.

## 7. Task checklist berurutan

Kerjakan **satu subtask pada satu waktu**, dari atas ke bawah. Jangan melompat atau menggabungkan beberapa subtask sekaligus.

- [ ] **A1. Baca spesifikasi dan periksa metadata dataset.** Baca `TECH_SPEC.md` §3–§4, §8, `DATASET_CARD.md`, ADR-003/008/010. Periksa metadata aktual dataset (kolom atau split yang tersedia, lisensi, syarat penggunaan). *Hasil:* ringkasan metadata aktual ditulis di laporan AI.
- [ ] **A2. Identifikasi kolom, lisensi, sumber, data kosong, dan duplikasi.** Periksa kolom `content` vs opsional lain, catat jumlah baris kosong, contoh duplikasi konten ternormalisasi, dan status lisensi/provenance. *Hasil:* tabel kualitas data kasar.
- [ ] **A3. Tentukan metode pengambilan subset 1.000 artikel tanpa mengunduh data yang tidak diperlukan.** Pilih strategi (streaming/select/head) yang hanya memuat kolom dan jumlah artikel yang dibutuhkan; dokumentasikan trade-off. *Hasil:* rencana subset tertulis.
- [ ] **A4. Ambil subset dan simpan metadata sumber.** Eksekusi strategi A3, catat tanggal akses, versi/revision, jumlah baris, filter yang diterapkan; simpan unduhan ke `data/raw/`. *Hasil:* subset terunduh di `data/raw/` + metadata sumber tersimpan.

> **Referensi — unduh dataset via HuggingFace (streaming, tanpa kolom `embedding` 1.25 GB):**
>
> ```python
> from datasets import load_dataset
>
> ds = load_dataset(
>     "fahadh4ilyas/indonesian_news_datasets",
>     split="train",
>     streaming=True,
> )
>
> rows = []
> for row in ds:
>     content = (row.get("content") or "").strip()
>     if not content:
>         continue
>     rows.append({"content": content})
>     if len(rows) >= 1000:
>         break
>
> # rows siap untuk langkah selanjutnya (deduplikasi + split)
> ```
>
> Catatan: `streaming=True` hanya memuat seperlunya; kolom `embedding` (1.25 GB file) tidak ikut terunduh karena tidak dipilih. Simpan metadata (tanggal akses, versi/revision, jumlah baris sebelum/sesudah filter) untuk A13 (DATASET_CARD). Lisensi CC BY-NC 4.0 wajib diperiksa ulang di halaman HF (A1/A2).
- [ ] **A5. Terapkan deduplikasi dan split berdasarkan dokumen.** Normalisasi-deduplikasi; pertahankan split bawaan train/test; validation diambil 10% dari split train (seed 42). Fallback 80/10/10 tidak dipakai (ADR-012). *Hasil:* dokumen unik, jumlah train/val/test tercatat.
- [ ] **A6. Implementasikan tokenizer regex lowercase.** Buat fungsi tokenisasi `re.findall(r"\w+|[^\w\s]", text)` setelah lowercase. *Hasil:* unit test tokenisasi dasar.
- [ ] **A7. Implementasikan `fit`, `encode`, `decode`.** Bangun kelas tokenizer: urutan special token 0–3, vocab hasil regex diurutkan frekuensi, `encode`/`decode`/`vocab_size` sesuai §3. *Hasil:* kelas tokenizer lengkap + test unit.
- [ ] **A8. Uji special tokens dan pastikan vocabulary hanya dibuat dari data training.** Tulis test yang membuktikan semua token id validation/test ada di vocab train (tanpa leakage). *Hasil:* test leakage lulus dengan output aktual.
- [ ] **A9. Implementasikan penambahan BOS/EOS ID setelah tokenisasi.** Sisipkan `bos_id` di awal dan `eos_id` di akhir setiap dokumen, bukan sebagai string literal ke regex. *Hasil:* test keberadaan bos/eos.
- [ ] **A10. Implementasikan sliding window, pasangan input-target, dan penanganan dokumen pendek.** Window panjang 65 stride 1 (`x = ids[:64]`, `y = ids[1:65]`); dokumen pendek jadi pasangan pendek; dokumen kosong dibuang, dokumen 1 token tidak menghasilkan pasangan; tanpa window lintas dokumen. *Hasil:* test no-window-crossing + relasi `x[i,t] == y[i,t-1]`.
- [ ] **A11. Implementasikan padding dan data loader sesuai kontrak.** `DataLoader` dengan collate pad `pad_id=0`, batch `x [B, 64]`, `y [B, 64]`. *Hasil:* batch shape `[B, 64]` dan posisi pad benar teruji.
- [ ] **A12. Jalankan unit test secara bertahap.** Jalankan seluruh test pipeline data, catat perintah dan output aktual, perbaiki temuan. *Hasil:* seluruh test lulus, output aktual dilampirkan.
- [ ] **A13. Perbarui `DATASET_CARD.md` menggunakan hasil aktual.** Isi seluruh kolom "Catatan eksperimen" dengan angka dan fakta yang benar-benar diukur. *Hasil:* Dataset Card lengkap dan diverifikasi.

## 8. Instruksi pengerjaan setiap subtask

1. Baca kembali bagian spesifikasi yang relevan (`TECH_SPEC.md` §3–§4/§8, `DATASET_CARD.md`).
2. Minta AI menjelaskan tujuan subtask, rencana, tensor shapes, kompleksitas, dan edge cases SEBELUM menulis kode.
3. Implementasikan satu subtask saja (perubahan sekecil mungkin).
4. Jalankan test yang relevan untuk subtask itu dan amati output aktual.
5. Jika ada error, pahami dan perbaiki; catat bukti reproduksi error dan hasil akhir.
6. Simpan log AI (raw JSONL + laporan Markdown) sesuai ADR-006.
7. Minta review kepada koordinator/anggota lain sebelum menyatakan subtask selesai.
8. Centang checkbox subtask hanya setelah hasil dan test benar-benar terverifikasi.

## 9. Aturan berhenti

- Setelah satu subtask selesai dan diverifikasi, **berhenti**. Jangan mengerjakan subtask berikutnya tanpa instruksi eksplisit.
- Jika hasil test gagal atau log AI belum tersimpan, **jangan lanjut**; perbaiki dulu.
- Jangan mengklaim test lulus jika belum dijalankan; jangan mengarang metadata dataset, jumlah artikel, jumlah token, atau ukuran vocab.

## 10. Acceptance criteria (wajib benar-benar diuji)

- [ ] `fit`/`encode`/`decode`/`vocab_size` memenuhi kontrak §3.
- [ ] Tidak ada vocabulary leakage: seluruh token id di validation/test sudah ada di vocab train (dibuktikan test yang dijalankan).
- [ ] Tidak ada window yang melintasi batas dokumen.
- [ ] Bentuk batch `[B, 64]` dan perilaku padding sesuai §4.
- [ ] Dokumen hasil tokenisasi kosong dibuang; dokumen 1 token tidak menghasilkan pasangan.
- [ ] `docs/DATASET_CARD.md` mencatat tanggal akses, versi/revision, split aktual, jumlah artikel per split, jumlah token, ukuran vocab, dan hasil pemeriksaan lisensi/provenance — semuanya diverifikasi, tidak dikarang.
- [ ] Setiap subtask A1–A13 memiliki bukti berupa output aktual atau test yang dijalankan (bukan sekadar klaim).

## 11. Unit test yang diperlukan

- Tokenizer: urutan id special, lowercase, fallback `<unk>`, pengurutan frekuensi, perilaku `decode` untuk special token.
- Dataset: shape `[B, 64]`, relasi `x[i,t] == y[i,t-1]` pada posisi non-pad, tidak ada window lintas dokumen, posisi pad benar, keberadaan bos/eos, deduplikasi bekerja, split reproduktif dengan seed 42.

## 12. Aturan logging AI

- Ikuti `docs/AI_RULES.md` §6, `docs/AI_LOG_TEMPLATE.md`, dan ADR-006.
- Smoke test logging personal (Issue E) WAJIB lolos sebelum coding dimulai.
- Raw log di `docs/ai-logs/raw/<member-id>/`, laporan Markdown di `docs/ai-logs/reports/`; dilarang menulis API key, token, password, atau data sensitif.

## 13. Dokumentasi yang harus diperbarui

- `docs/DATASET_CARD.md` — kolom "Catatan eksperimen".
- Laporan AI di `docs/ai-logs/reports/` sesuai template.
- README — instruksi menjalankan pipeline data (hanya jika bagian terkait sudah ada).