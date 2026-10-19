# Rencana Pengambilan Subset Dataset (Subtask A3)

Status: rencana disetujui pemilik tugas, menunggu eksekusi pada Subtask A4.
Subtask terkait: A3 — "Tentukan metode pengambilan subset 1.000 artikel tanpa mengunduh data yang tidak diperlukan."
Referensi: `docs/TECH_SPEC.md` §8, `docs/DATASET_CARD.md`, ADR-003, ADR-010, ADR-012, Issue A §A3–A4.

## 1. Tujuan

Menetapkan cara mengambil **1.000 artikel** kolom `content` dari
`fahadh4ilyas/indonesian_news_datasets` (split bawaan `train`) dengan
membaca seminimal mungkin: tidak mengunduh kolom `embedding` (~1.25 GB),
tidak menyentuh split `test`, dan tidak memuat baris melebihi kebutuhan.

## 2. Strategi terpilih

1. Streaming, bukan unduh penuh:
   `load_dataset("fahadh4ilyas/indonesian_news_datasets", split="train", streaming=True, revision=<revision terverifikasi A1/A2>)`.
2. Seleksi kolom sebelum iterasi: hanya `content`
   (`ds.select_columns(["content"])`), sehingga kolom `embedding` tidak
   dimaterialisasi ke row/dict maupun memori.
3. Iterasi berhenti lebih awal (*early break*): ambil `row.get("content")`,
   `strip()`; baris `None`/kosong dihitung lalu dilewati; berhenti setelah
   **1.000** konten non-kosong terkumpul.
4. Catat metadata sumber untuk A4/A13: tanggal akses, `revision` yang dipakai,
   split, jumlah baris dibaca, jumlah baris di-skip, jumlah baris tersimpan.

### Pseudocode (untuk A4, belum dieksekusi pada A3)

```python
from datasets import load_dataset

REVISION = "<revision dari A1/A2>"
ds = load_dataset(
    "fahadh4ilyas/indonesian_news_datasets",
    split="train",
    streaming=True,
    revision=REVISION,
).select_columns(["content"])

rows, read, skipped = [], 0, 0
for row in ds:
    read += 1
    content = (row.get("content") or "").strip()
    if not content:
        skipped += 1
        continue
    rows.append({"content": content})
    if len(rows) >= 1000:
        break
```

## 3. Trade-off dan alternatif yang ditolak

| Alternatif | Alasan ditolak |
|---|---|
| `load_dataset(..., split="train[:1000]")` (non-streaming) | Mengunduh seluruh file shard yang memuat `embedding`; jauh lebih besar dari kebutuhan. |
| `shuffle(seed=42)` pada iterable | Menambah baris yang harus dibaca dan menambah langkah non-deterministik; seed 42 pada proyek ini untuk split, bukan pemilihan subset (ADR-010). |
| Sampe acak 1.000 dari seluruh korpus | Perlu traverse/unduh jauh lebih banyak; tidak sepadan untuk uji pipeline. |

Konsekuensi yang diterima: subset = **1.000 baris non-kosong pertama** pada
urutan shard (head-of-shard bias), bukan sampel acak. Determinisme dijamin
selama `revision` di-pin.

## 4. Kompleksitas dan sumber daya

- Waktu: `O(R)`, dengan `R` = baris dibaca sampai 1.000 non-kosong terkumpul (harapan ≈1.000).
- Memori: `O(1)` per iterasi streaming; hasil akhir 1.000 dict `{"content": ...}`.
- Tensor shapes: tidak berlaku (teks mentah); bentuk `[B, 64]` baru muncul di A10/A11.

## 5. Edge cases

- Row tanpa key `content` atau nilai `None` → di-skip dan dihitung.
- String kosong / hanya whitespace → di-skip dan dihitung.
- Konten duplikat → **tidak** di-dedup di sini; dedup resmi di A5 agar A5 punya bukti jumlah duplikat aktual.
- Tidak ada lagi baris sebelum 1.000 terkumpul → hentikan dan catat jumlah aktual (jangan mengarang angka).
- Urutan berubah antar revision → wajib pin `revision`.

## 6. Luaran yang diharapkan pada A4

- `data/raw/indonesian_news_1000.jsonl` (1.000 objek `{"content": ...}`).
- Metadata sumber (tanggal akses, revision, split, baris dibaca/skip/simpan).
- Angka aktual ini menjadi isi kolom "Catatan eksperimen" `docs/DATASET_CARD.md` pada A13.

## 7. Catatan verifikasi

- A3 tidak menghasilkan kode dan tidak mengunduh apa pun, sehingga tidak ada
  unit test baru. Validasi metode terjadi pada A4 (jumlah baris dibaca vs
  1.000 tersimpan, metadata tercatat).
- Bukti sesi ada pada raw JSONL plugin (`docs/ai-logs/raw/raihanfahrifi-80017/`).
  Laporan Markdown plugin ditulis ulang otomatis setiap event, sehingga field
  manualnya diisi anggota setelah sesi berhenti.
