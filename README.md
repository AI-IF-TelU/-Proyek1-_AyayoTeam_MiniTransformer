# Mini-Transformer — Mini-GPT Bahasa Indonesia

Implementasi model bahasa generatif kecil menggunakan arsitektur **Decoder-only Transformer** dengan Python dan PyTorch. Model dilatih dari nol untuk memprediksi token berikutnya berdasarkan korpus berita bahasa Indonesia.

## 1. Tujuan Proyek

- Mengimplementasikan Causal Multi-Head Self-Attention dan Sinusoidal Positional Encoding secara manual.
- Melatih model untuk melakukan prediksi token berikutnya dan menghasilkan kelanjutan teks.
- Memahami algoritma, kompleksitas, pengujian, serta proses pengembangan menggunakan Vibe Coding.
- Merekam interaksi AI secara otomatis sebagai dokumentasi proyek.

**Batasan:** Tidak menggunakan model pretrained GPT atau API GPT sebagai model utama. Komponen inti Transformer tidak boleh digantikan oleh `nn.Transformer` atau `nn.MultiheadAttention`.

## 2. Teknologi dan Dataset

- Python dan PyTorch.
- VS Code dan Kilo Code.
- Git dan GitHub.
- Dataset: [Indonesian News Datasets](https://huggingface.co/datasets/fahadh4ilyas/indonesian_news_datasets).

Dataset awal menggunakan subset 1.000 artikel (keputusan koordinator 19 Okt 2026; ADR-012). Pemrosesan, split berdasarkan dokumen, tokenizer, dan pembentukan data training mengikuti [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md).

## 3. Instalasi dari Awal

### Prasyarat

Siapkan Git, Python yang kompatibel dengan konfigurasi proyek, VS Code, ekstensi Kilo Code, dan akses repository GitHub organisasi. Bun diperlukan apabila digunakan oleh plugin logging Kilo Code.

### Clone repository

Buka terminal PowerShell:

```powershell
git clone https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer.git
cd AyayoTeam_MiniTransformer
```

Pastikan branch yang digunakan adalah `master`:

```powershell
git branch --show-current
git pull --ff-only origin master
```

### Siapkan environment Python

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
```

Instal dependency jika `requirements.txt` sudah tersedia dan terisi:

```powershell
python -m pip install -r requirements.txt
```

Periksa versi Python dan PyTorch sesuai konfigurasi proyek. Jangan memasang versi dependency berbeda tanpa persetujuan tim.

### Buka proyek di VS Code

```powershell
code .
```

Pastikan folder root proyek terbuka, bukan hanya salah satu subfolder. Kilo Code harus dapat membaca [`AGENTS.md`](AGENTS.md) dan dokumen dalam `docs/`.

## 4. Konfigurasi Anggota dan Logging AI

Setiap anggota menggunakan `member_id` unik, yang disimpan dalam konfigurasi lokal dan tidak di-commit. Format `member_id`: nama tanpa spasi (lowercase) + `-` + 5 digit terakhir NIM. Contoh: `raihanfahrifi-80017`.

Contoh konfigurasi Raihan:

```json
{
  "member_id": "raihanfahrifi-80017"
}
```

Salin `.kilo/member.local.example.json` menjadi `.kilo/member.local.json`. Sesuaikan `member_id` dengan identitas masing-masing (lihat format di atas).

### Uji logging sebelum coding

1. Pastikan plugin logging berhasil dimuat.
2. Kirim prompt smoke test berikut melalui Kilo Code:

```text
LOGGING SMOKE TEST. Do not edit any files or run commands. Reply exactly: LOGGER-TEST-2026-01 and explain that this is only a test. This prompt and your response must be recorded by the project logger.
```

3. Periksa apakah prompt dan respons tercatat pada `docs/ai-logs/raw/<member-id>/`.
4. Pastikan laporan Markdown terbentuk pada `docs/ai-logs/reports/`.
5. Verifikasi isi laporan terhadap raw log.

Setiap anggota wajib melakukan smoke test sendiri. Bukti keberhasilan satu anggota tidak membuktikan bahwa logging anggota lainnya sudah berfungsi.

Jangan mulai pekerjaan coding yang wajib direkam sebelum logging pada environment anggota tersebut terverifikasi.

### Pencatatan dokumentasi interaksi AI

Seluruh interaksi (prompt, respons, dan aktivitas coding) yang dilakukan setiap anggota melalui Kilo Code tercatat otomatis oleh plugin logging. Dokumentasi lengkap hasil interaksi AI tersimpan sebagai laporan Markdown di folder `docs/ai-logs/reports/` dengan nama `AI-LOG-<member-id>-<session-id>.md`, sedangkan data mentah per event tersimpan di `docs/ai-logs/raw/<member-id>/`. Log ini menjadi bukti verifikasi proses Vibe Coding dan tidak boleh dihapus atau dipalsukan.

## 5. Pembagian Tugas GitHub

| Anggota | Issue | Tanggung jawab |
|---|---|---|
| Dzaki Alwan | [#2](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/2) | Data Pipeline & Tokenizer |
| Firdaus Akbar Amrullah | [#3](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/3) | MiniGPT, Training & Generation |
| Muhammad Raihan Fahrifi | [#4](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/4) | Komponen Inti Transformer |
| Rafa Suryaputra | [#5](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/5) | Unit Test, Integrasi & Dokumentasi |
| Rafa + seluruh anggota | [#6](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/6) | Validasi Logging Otomatis |
| Seluruh tim | [#7](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/7) | Tracking pekerjaan |

Issue #1 untuk spesifikasi teknis telah ditutup. Seluruh implementasi harus mengikuti `AGENTS.md`, `docs/TECH_SPEC.md`, dan acceptance criteria Issue terkait.

## 6. Workflow Pengerjaan Berurutan

Tim menggunakan pengerjaan bergantian, satu anggota aktif pada satu waktu. Setiap subtask harus diselesaikan dan diverifikasi sebelum anggota melanjutkan ke subtask berikutnya. Repository **master-only**: dilarang membuat branch baru, pull request, atau merge.

Urutan kerja:

1. Anggota mengumumkan giliran, Issue, dan subtask di grup.
2. Pastikan working tree bersih (`git status`).
3. Gunakan Prompt A untuk analisis dan perencanaan.
4. Periksa serta setujui rencana.
5. Gunakan Prompt B untuk implementasi satu subtask.
6. Jalankan tes, tinjau diff, verifikasi logging, dan pahami hasil.
7. Setelah direview anggota lain, commit dan push langsung ke `master`.
8. Anggota berikutnya menjalankan `git pull --ff-only origin master` **hanya** jika anggota sebelumnya mengabarkan telah push perubahan.

**Penting:** workflow master-only ini konsisten dengan `AGENTS.md` dan `docs/AI_RULES.md`. Seluruh Issue tersedia lokal di folder `issues/`; AI agent tidak perlu akses GitHub untuk membaca atau mengerjakan Issue.

## 7. Prompt A — Analisis dan Perencanaan Subtask

Gunakan sebelum menulis kode. Isi bagian anggota, Issue, dan subtask sesuai pekerjaan yang sedang dikerjakan.

**Template:**

```text
# MINI-TRANSFORMER — SUBTASK PLANNING

Repository: AI-IF-TelU/AyayoTeam_MiniTransformer

Anggota: [NAMA ANGGOTA]
Member ID: [MEMBER_ID]
Issue: [NOMOR DAN JUDUL ISSUE] (dari folder `issues/`)
Subtask: [KODE DAN NAMA SUBTASK]

Ikuti AGENTS.md, docs/TECH_SPEC.md, docs/AI_RULES.md,
dan deskripsi lengkap Issue yang ditugaskan (folder `issues/`).

Sebelum coding:
1. Verifikasi repository, branch (harus `master`, tanpa membuat branch baru), kondisi Git, dan logging.
2. Baca Issue beserta acceptance criteria dan dependensinya (lokal di folder `issues/`).
3. Jelaskan tujuan, algoritma, tensor shapes, kompleksitas,
   edge cases, dependensi, serta unit test.
4. Sebutkan file yang perlu diubah dan rencana implementasinya.

Jangan menulis kode atau mengerjakan subtask berikutnya.
Jangan menjalankan operasi Git apa pun (commit, push, pull,
branch, merge, staging) — seluruh kerja Git dilakukan oleh
anggota; repo tetap master-only (tanpa branch baru).
Jika ada konflik spesifikasi atau masalah Git, berhenti
dan laporkan.

Tunggu persetujuan saya sebelum implementasi.
```

### Contoh pengisian untuk Raihan

```text
Anggota: Muhammad Raihan Fahrifi
Member ID: raihanfahrifi-80017
Issue: #4 — [STEP 3] Issue B — Implementasi Komponen Inti Transformer
Subtask: B1 — Periksa kontrak tensor dan parameter pada TECH_SPEC.md
```

Kode dan nama subtask harus mengikuti checklist aktual pada Issue (lokal di folder `issues/`).

## 8. Prompt B — Implementasi Satu Subtask

Gunakan setelah rencana Prompt A disetujui.

**Template:**

```text
# MINI-TRANSFORMER — SUBTASK IMPLEMENTATION

Lanjutkan subtask yang sudah disetujui.

Anggota: [NAMA ANGGOTA]
Issue: [NOMOR ISSUE] (dari folder `issues/`)
Subtask: [KODE DAN NAMA SUBTASK]

Ikuti rencana yang disetujui, AGENTS.md,
docs/TECH_SPEC.md, dan docs/AI_RULES.md.

1. Implementasikan hanya subtask ini.
2. Jelaskan kode, algoritma, dan alasan teknisnya.
3. Buat atau perbarui unit test.
4. Jalankan tes dan tampilkan output aktual.
5. Tampilkan seluruh file yang berubah untuk direview
   (jangan menjalankan operasi Git apa pun).
6. Pastikan logging otomatis merekam sesi.
7. Laporkan kriteria yang terpenuhi, kegagalan,
   keterbatasan, dan hal yang perlu dipahami.

Jangan mengerjakan subtask selanjutnya atau mengubah
kontrak publik tanpa persetujuan.

Berhenti setelah checkpoint selesai. Tunggu review
sebelum melanjutkan.

Jangan menjalankan operasi Git apa pun (commit, push, pull,
branch, merge, staging). Seluruh kerja Git dilakukan oleh
anggota; repo tetap master-only (tanpa branch baru,
tanpa PR/merge).
```

## 9. Checkpoint Sebelum Melanjutkan

Setiap subtask hanya boleh dinyatakan selesai jika:

- [ ] Implementasi sesuai spesifikasi.
- [ ] Unit test relevan dijalankan dan hasilnya diverifikasi.
- [ ] Anggota memahami kode dan algoritma yang dibuat.
- [ ] Logging AI tersimpan dan dapat diperiksa.
- [ ] Diff bersih dari perubahan di luar scope.
- [ ] Hasil mendapat review sebelum dilanjutkan.

Jika tes gagal, perbaiki terlebih dahulu. Jangan menandai task selesai atau mengarang hasil tes.

## 10. Dokumentasi Proyek

| Dokumen | Fungsi |
|---|---|
| [`AGENTS.md`](AGENTS.md) | Instruksi utama untuk AI coding agent |
| [`docs/PRD.md`](docs/PRD.md) | Tujuan dan ruang lingkup |
| [`docs/TECH_SPEC.md`](docs/TECH_SPEC.md) | Arsitektur dan kontrak teknis |
| [`docs/AI_RULES.md`](docs/AI_RULES.md) | Aturan prompting dan coding |
| [`docs/DATASET_CARD.md`](docs/DATASET_CARD.md) | Sumber data dan preprocessing |
| [`docs/AI_LOG_TEMPLATE.md`](docs/AI_LOG_TEMPLATE.md) | Format laporan interaksi AI |
| [`docs/ARCHITECTURE_DECISIONS.md`](docs/ARCHITECTURE_DECISIONS.md) | Keputusan arsitektur dan trade-off |

**Prinsip utama:** satu spesifikasi, satu standar pengujian, logging yang dapat diverifikasi, dan satu subtask aktif pada satu waktu. Tujuan proyek bukan hanya menghasilkan kode yang berjalan, tetapi juga memahami bagaimana Mini-Transformer dibangun.
