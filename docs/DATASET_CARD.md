# Dataset Card — Indonesian News Datasets

## Identitas
- Repository: https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets
- Tujuan penggunaan: language modeling eksperimental untuk next-token prediction.
- Dataset utama yang dipilih tim: Indonesian News Datasets.

## Pemakaian yang direncanakan
- Utamakan kolom `content`; `title` bersifat opsional.
- Jangan memuat kolom embedding jika tidak dibutuhkan.
- Subset = 1.000 artikel awal (800 dari `train` split, 200 dari `test` split) untuk uji pipeline dan training awal.
- Jangan menyebut subset sebagai korpus Karhutla kecuali setiap artikel telah disaring dan diverifikasi relevansinya.

## Lisensi dan provenance
Repositori mencantumkan lisensi CC BY-NC 4.0. Label kategori dilaporkan dibuat dengan LLM dan belum dikurasi. Tim wajib memeriksa metadata dataset dan syarat penggunaan terkini sebelum mengunduh, mengubah, atau mendistribusikan korpus hasil olahan. Lisensi repository tidak otomatis menyelesaikan hak atas tiap artikel sumber.

## Preprocessing
1. Periksa kolom dan split yang benar-benar tersedia.
2. Hapus baris dengan konten kosong.
3. Normalisasi seperlunya: ubah huruf ke lowercase (sesuai kontrak tokenizer TECH_SPEC §3); jangan menghapus tanda baca yang berguna untuk bahasa.
4. Deduplikasi berdasarkan konten yang telah dinormalisasi.
5. Pisahkan data berdasarkan dokumen sebelum tokenisasi dan pembuatan window. Split train (800) dan test (200) diunduh terpisah. Dedup dilakukan lintas split (buang dari test jika ada di train). Validation diambil 10% dari split train dengan seed 42 (ADR-012).
6. Tokenisasi tiap dokumen, sisipkan `bos_id`/`eos_id` setelah tokenisasi, lalu bangun window sliding 65 stride 1 (kontrak detail: TECH_SPEC §4).
7. Bangun vocabulary hanya dari training split.

## Keterbatasan dan risiko
- Berita dapat berisi informasi yang sudah usang atau tidak lagi akurat.
- Label kategori tidak dijamin benar.
- Model kecil dapat mengulang teks, menghasilkan fakta keliru, atau mempelajari bias korpus.
- Hasil generation hanya demonstrasi pendidikan, bukan sumber berita tepercaya.

## Catatan eksperimen aktual
- **Tanggal akses:** 2026-10-22 (test diunduh ulang 2026-10-22; unduhan pertama gagal 429 dan menghasilkan data tidak valid).
- **Versi/revision dataset:** 13f841935cf1adbe3e41e474bf926e49a0e2943e
- **Split asli dan jumlah baris:** 800 artikel dari `train` split, 200 artikel dari `test` split (test saat ini 200 baris unik, bukan duplikat 100 doc × 2).
- **Filter yang diterapkan:** Pembuangan konten kosong, deduplikasi per split, dedup lintas split (hasil `process_and_split.py`: `cross_split_dropped=0`).
- **Jumlah artikel (Train/Val/Test):** 720 / 80 / 200.
- **Definisi "jumlah token":** total panjang hasil `Tokenizer.encode()` (regex `\w+|[^\w\s]`, lowercase) per dokumen, dijumlahkan per split; **tidak termasuk** id `<bos>`/`<eos>` yang disisipkan pada tahap dataset (TECH_SPEC §4). Dengan bos/eos totalnya lebih besar 2×jumlah dokumen.
- **Jumlah token (Train/Val/Test):** 290.920 / 33.157 / 77.330.
- **Ukuran vocabulary:** 19.192.
- **Padding (Train):** 0.00% pada training set (64 context length).
- **Pemeriksaan lisensi:** CC BY-NC 4.0 terkonfirmasi pada metadata unduhan.
