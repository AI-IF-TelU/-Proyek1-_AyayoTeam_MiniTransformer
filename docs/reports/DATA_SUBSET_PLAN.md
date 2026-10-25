# Rencana Pengambilan Subset Dataset

Status: SUDAH DIEKSEKUSI. Dokumen ini menggantikan rencana A3/A4 lama
(`Subtask A3`/`Subtask A4` pada versi sebelumnya).
Referensi: `docs/TECH_SPEC.md` §8, `docs/DATASET_CARD.md`, ADR-003, ADR-010, ADR-012, Issue A.

## 1. Tujuan

Mengambil **1.000 artikel** kolom `content` dari
`fahadh4ilyas/indonesian_news_datasets` dengan komposisi:

- **800** baris dari split `train`,
- **200** baris dari split `test`,

tanpa mengunduh kolom `embedding` (~1.25 GB) dan tanpa memuat baris melebihi
kebutuhan.

## 2. Kondisi aktual (bukan rencana)

Split `test` **DIUNDUH** untuk menyusun subset 200 baris, berbeda dari rencana
lama yang menyatakan "tidak menyentuh split test".

Luaran aktual:

- `data/raw/indonesian_news_train_800.jsonl` — 800 objek `{"content": ...}`.
- `data/raw/indonesian_news_test_200.jsonl` — 200 objek `{"content": ...}`.
- Metadata sumber per file (`*.metadata.json`): tanggal akses, `revision` yang
  dipakai, split, jumlah baris dibaca, jumlah baris di-skip, jumlah baris
  tersimpan.

## 3. Strategi

1. Streaming, bukan unduh penuh:
   `load_dataset("fahadh4ilyas/indonesian_news_datasets", split="train"/"test", streaming=True, revision=<revision terverifikasi A1/A2>)`.
2. Seleksi kolom sebelum iterasi: hanya `content`
   (`ds.select_columns(["content"])`), sehingga kolom `embedding` tidak
   dimaterialisasi ke row/dict maupun memori.
3. Iterasi berhenti lebih awal (*early break*): ambil `row.get("content")`,
   `strip()`; baris `None`/kosong dihitung lalu dilewati; berhenti setelah
   **800** konten non-kosong dari `train` dan **200** konten non-kosong dari
   `test` terkumpul.
4. Catat metadata sumber untuk A13: tanggal akses, `revision` yang dipakai,
   split, jumlah baris dibaca, jumlah baris di-skip, jumlah baris tersimpan.

## 4. Trade-off dan alternatif yang ditolak

| Alternatif | Alasan ditolak |
|---|---|
| `load_dataset(..., split="train[:800]")` (non-streaming) | Mengunduh seluruh file shard yang memuat `embedding`; jauh lebih besar dari kebutuhan. |
| `shuffle(seed=42)` pada iterable | Menambah baris yang harus dibaca dan menambah langkah non-deterministik; seed 42 pada proyek ini untuk split, bukan pemilihan subset (ADR-010). |
| Sampel acak dari seluruh korpus | Perlu traverse/unduh jauh lebih banyak; tidak sepadan untuk uji pipeline. |

Konsekuensi yang diterima: subset = **baris non-kosong pertama** pada urutan
shard (head-of-shard bias), bukan sampel acak. Determinisme dijamin selama
`revision` di-pin.

## 5. Kompleksitas dan sumber daya

- Waktu: `O(R)`, dengan `R` = baris dibaca sampai 800 (train) dan 200 (test)
  non-kosong terkumpul (harapan ≈800 + 200).
- Memori: `O(1)` per iterasi streaming; hasil akhir 1.000 dict `{"content": ...}`.
- Tensor shapes: tidak berlaku (teks mentah); bentuk `[B, 64]` baru muncul di A10/A11.

## 6. Edge cases

- Row tanpa key `content` atau nilai `None` → di-skip dan dihitung.
- String kosong / hanya whitespace → di-skip dan dihitung.
- Konten duplikat → **tidak** di-dedup di sini; dedup resmi di A5 agar A5 punya bukti jumlah duplikat aktual.
- Tidak ada lagi baris sebelum 800/200 terkumpul → hentikan dan catat jumlah aktual (jangan mengarang angka).
- Urutan berubah antar revision → wajib pin `revision`.

## 7. Catatan verifikasi

- Angka aktual (baris dibaca vs tersimpan, metadata) menjadi isi kolom
  "Catatan eksperimen" `docs/DATASET_CARD.md` pada A13.
- Bukti sesi ada pada raw JSONL plugin (`docs/ai-logs/raw/`).
  Laporan Markdown plugin ditulis ulang otomatis setiap event, sehingga field
  manualnya diisi anggota setelah sesi berhenti.
