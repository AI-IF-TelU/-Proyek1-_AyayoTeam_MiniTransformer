# Dataset Card — Indonesian News Datasets

## Identitas
- Repository: https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets
- Tujuan penggunaan: language modeling eksperimental untuk next-token prediction.
- Dataset utama yang dipilih tim: Indonesian News Datasets.

## Pemakaian yang direncanakan
- Utamakan kolom `content`; `title` bersifat opsional.
- Jangan memuat kolom embedding jika tidak dibutuhkan.
- Subset = 1.000 artikel (keputusan koordinator 2026-10-19, ADR-012) untuk uji pipeline dan training awal.
- Jangan menyebut subset sebagai korpus Karhutla kecuali setiap artikel telah disaring dan diverifikasi relevansinya.

## Lisensi dan provenance
Repositori mencantumkan lisensi CC BY-NC 4.0. Label kategori dilaporkan dibuat dengan LLM dan belum dikurasi. Tim wajib memeriksa metadata dataset dan syarat penggunaan terkini sebelum mengunduh, mengubah, atau mendistribusikan korpus hasil olahan. Lisensi repository tidak otomatis menyelesaikan hak atas tiap artikel sumber.

## Preprocessing
1. Periksa kolom dan split yang benar-benar tersedia.
2. Hapus baris dengan konten kosong.
3. Normalisasi seperlunya: ubah huruf ke lowercase (sesuai kontrak tokenizer TECH_SPEC §3); jangan menghapus tanda baca yang berguna untuk bahasa.
4. Deduplikasi berdasarkan konten yang telah dinormalisasi.
5. Pisahkan data berdasarkan dokumen sebelum tokenisasi dan pembuatan window. Pertahankan split bawaan dataset (train/test) jika tersedia dan terverifikasi; validation diambil 10% dari split train dengan seed 42 (ADR-012). Fallback 80/10/10 tidak dipakai pada proyek ini. Dilarang me-resplit test split bawaan secara sembarangan.
6. Tokenisasi tiap dokumen, sisipkan `bos_id`/`eos_id` setelah tokenisasi, lalu bangun window sliding 65 stride 1 (kontrak detail: TECH_SPEC §4).
7. Bangun vocabulary hanya dari training split.

## Keterbatasan dan risiko
- Berita dapat berisi informasi yang sudah usang atau tidak lagi akurat.
- Label kategori tidak dijamin benar.
- Model kecil dapat mengulang teks, menghasilkan fakta keliru, atau mempelajari bias korpus.
- Hasil generation hanya demonstrasi pendidikan, bukan sumber berita tepercaya.

## Catatan eksperimen yang harus diisi
> Diisi pada langkah dataset (setelah dataset diunduh dan diproses, bukan pada Issue #1).
- Tanggal akses:
- Versi/revision dataset:
- Split asli dan jumlah baris:
- Filter yang diterapkan:
- Jumlah artikel train/validation/test:
- Jumlah token dan ukuran vocabulary:
- Pemeriksaan lisensi/provenance:
