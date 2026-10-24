# AI Log — Issue D Subtask D10 (Verifikasi Perbaikan)

> Laporan ini disusun dari sesi yang direkam otomatis. Semua angka berasal dari output run yang
> tercantum; tidak ada prompt, hasil test, atau keputusan yang dikarang.

## Metadata

- **Log ID:** AI-LOG-rafasuryaputra-80048-IssueD-D10
- **Tanggal/waktu:** 2026-10-24 20:19–21:05 WIB (UTC+07:00)
- **Anggota:** Rafa Suryaputra — `rafasuryaputra-80048`
- **Agent/tool:** Assistant Vengentic (Kilo Code CLI), tools: shell (PowerShell), file read/write/edit
- **Model:** Assistant Vengentic
- **Session ID:** `ses_e91eec218ffeyD2TXSoQynSit9`
- **GitHub Issue/PR:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis, subtask D10
- **Target modul:** dokumentasi pengujian (`docs/`); verifikasi `src/generate.py`,
  `src/data/tokenizer.py`, `src/train.py`, `README.md` tanpa mengubahnya
- **Raw log path:** `docs/ai-logs/raw/rafasuryaputra-80048/ses_e91eec218ffeyD2TXSoQynSit9.jsonl`
- **Share link:** tidak tersedia (lokal)

## Kronologi prompt dan respons

| # | Waktu (WIB) | Jenis | Isi ringkas | File terdampak |
|---|---|---|---|---|
| 1 | 20:19 | Prompt anggota | `MINI-TRANSFORMER — SUBTASK PLANNING` untuk D10: verifikasi repo/branch/Git/logging, baca Issue + AC, jelaskan rencana, jangan menulis kode, jangan operasi Git, tunggu persetujuan | — |
| 2 | 20:20–20:29 | Respons asisten | Verifikasi awal (branch `master`, HEAD `b5c2b80`, working tree bersih + 1 laporan logger, 162 tes terkoleksi), pembacaan Issue D/TECH_SPEC/AI_RULES/D9_FAILURE_LOG/TESTING/README/src, lalu laporan **blocker**: prasyarat D10 ("setelah pemilik modul memperbaiki") belum terpenuhi karena tidak ada perubahan `src/`/`tests/`/`README.md` sejak D9 | tidak ada |
| 3 | 20:29 | Keputusan anggota | Memilih opsi **"Verification attempt sekarang"**: jalankan ulang probe D9, catat status masih gagal sebagai bukti, tanpa menyentuh `src/` dan tanpa menambahkan tes gagal ke suite | — |
| 4 | 20:51 | Prompt anggota | `MINI-TRANSFORMER — SUBTASK IMPLEMENTATION` untuk D10 dengan instruksi yang sama seperti AGENTS.md (implementasi satu subtask, jelaskan algoritma, tes, tampilkan output aktual, tanpa operasi Git) | — |
| 5 | 20:51–21:05 | Respons asisten | Baseline suite, penulisan probe `%TEMP%\kilo\d10\d10_verify.py`, eksekusi 21 pemeriksaan, koreksi probe atas dua hasil tak terduga, penulisan dokumen | `docs/D10_FIX_VERIFICATION.md`, `docs/TESTING.md`, laporan ini |

Keputusan teknis yang diambil selama implementasi (semua tercatat di dokumen D10):

1. **Probe di luar repo** (`%TEMP%\kilo\d10\`) agar repository tetap bersih dan tidak ada tes
   gagal yang masuk suite bersama. Alasan: persetujuan yang diberikan adalah *verification
   attempt*, bukan penambahan tes regresi ke `tests/`.
2. **Kontrol negatif untuk setiap temuan**, agar status `OPEN` tidak berasal dari kesalahan skrip.
3. **Isolasi determinisme pada F-D9-02** setelah run pertama tidak mereproduksi kegagalan
   (lihat bagian Debugging).

## Debugging

### Error/kegagalan aktual

Tidak ada kegagalan suite: `162 passed in 26.37s`, `162 passed in 24.90s`, dan
`162 passed in 25.08s` setelah seluruh probe. Yang tercatat di sini adalah **dua hasil yang tidak
sesuai harapan probe**, yang keduanya berasal dari probe sendiri, bukan dari modul.

**Masalah 1 — F-D9-02 tidak tereproduksi pada run pertama.**
Pesan aktual dari run pertama (console):

```text
  model.context_length          : 8
  default call returned         : '5 6 7 4 7 4 6'
[CLOSED   ] F-D9-02 | generate(model, tok, prompt, max_new_tokens=10) on context_length=8
            expected: returns str without exception
            actual  : returned str
```

Diagnosis: `generate` berhenti lebih dulu karena `<eos>` (id 2) muncul pada argmax sebelum
konteks melampaui `context_length=8`. Inisialisasi bobot tidak di-seed, sehingga tiap run berbeda.
Artinya reproduksi F-D9-02 **intermiten**, bukan deterministik.

**Masalah 2 — kontrol sliding window melaporkan 100 token, bukan 105.**
Pesan aktual:

```text
[UNEXPECTED] F-D9-02 | control: sliding window on baseline 64 still works
            expected: 105 tokens, no exception
            actual  : 100 tokens, no exception
```

Diagnosis sama: `<eos>` muncul pada iterasi pertama sehingga 0 token baru dihasilkan dan
`ids[1:]` hanya berisi 100 token prompt.

**Masalah 3 — perbandingan signature di V3 salah secara metodologis.**
Pemeriksaan kedua sempat melaporkan `CLOSED` karena string spesifikasi masih membawa backtick
trailing, sehingga perbandingan dengan rekaman D9 menghasilkan `spec=False` secara palsu.
Perbaikan: ekstraksi dilakukan dengan regex code span pada kedua sisi.

### Perubahan yang dilakukan pada probe (bukan pada `src/`)

1. `torch.manual_seed(42)` sebelum run natural, **plus** run terisolasi dengan `eos_id=-1`
   (id yang tidak mungkin menjadi argmax) sehingga loop dipaksa melewati batas konteks.
2. Kontrol sliding window juga memakai `eos_id=-1` agar jumlah token deterministik (105).
3. Ditambahkan V2c: pengulangan pada seed 0..9 untuk mengukur frekuensi kegagalan.
4. V5 tidak lagi memperlakukan dokumen D10 sebagai "errata" yang menutup F-D9-05; pencarian
   `hasattr(Tokenizer, "from_vocab")` ditambahkan sebagai kriteria jalur restore resmi.
5. V3 membandingkan signature saat ini dengan **rekaman di `docs/D9_FAILURE_LOG.md`**, bukan
   asumsi statis.

### Hasil setelah perbaikan probe

```text
  (a) natural run (eos_id=2)    : ValueError: sequence length T=9 exceeds context_length=8
  (b) forced run (eos_id=-1)    : ValueError: sequence length T=9 exceeds context_length=8
  CONTROL explicit ctx returned : '5 6 3 3 3 3 3 3 3 3 3 3'
  generated tokens     : 105 (100 prompt + 5 generated = 105)
  raised on 7/10 seeds
  checks=21 closed=0 open=16
VERDICT: D10 findings are NOT closed; defects remain reproducible.
```

## Verifikasi

- **Perintah test yang dijalankan:**

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --run-integration
.\.venv\Scripts\python.exe "$env:TEMP%\kilo\d10\d10_verify.py"
.\.venv\Scripts\python.exe -m pytest -q          # setelah seluruh probe
```

- **Output aktual:** `162 passed in 26.37s`; `162 passed in 24.90s`; probe: `checks=21
  closed=0 open=16`; suite ulang `162 passed in 25.08s`.
- **Commit SHA:** `b5c2b80` (`feat(Issue D): Substask D9`), branch `master`, tanpa operasi Git.
- **Acceptance criteria yang terpenuhi (D10):**
  - Seluruh jalur verifikasi dijalankan pada commit aktual dan output dicatat apa adanya.
  - Setiap temuan dinilai dengan perilaku yang diharapkan + kontrol negatif, bukan "tidak error".
  - Tidak ada perubahan `src/`, `tests/`, `README.md`, kontrak publik, atau dependency.
  - Temuan yang masih terbuka didokumentasikan beserta kriteria penutupan dan kandidat tes regresi.
- **Acceptance criteria yang belum terpenuhi (D10):**
  - "Temuan tertutup dengan bukti tes lulus" — belum ada perbaikan modul, sehingga 6/6 temuan
    masih `OPEN`. D10 belum dapat ditandai selesai.

### Status per temuan (ringkas)

| ID | Status | Bukti kunci |
|---|---|---|
| F-D9-01 | OPEN | `id_to_token 0`, `vocab_size 0`, `generate ''`; sama pada checkpoint nyata (vocab 3.981); kontrol berfungsi |
| F-D9-02 | OPEN | `ValueError: sequence length T=9 exceeds context_length=8`; 7/10 seed; kontrol eksplisit & sliding window berfungsi |
| F-D9-03 | OPEN | spec 2 parameter vs implementasi 7 parameter; tidak berubah sejak D9 |
| F-D9-04 | OPEN | `src/train.py:31` → `ADR-014`, ADR hanya 001–012 |
| F-D9-05 | OPEN | tiga dokumen D1–D3 `Test-Path` `False` |
| F-D9-06 | OPEN | `outputs/` tidak ada |

## Refleksi yang diverifikasi anggota

- **Mengapa pendekatan dipilih:** D10 bergantung pada pekerjaan pihak lain. Menjalankan ulang
  probe lebih jujur daripada menunggu tanpa bukti, dan menghasilkan artefak yang bisa langsung
  dipakai untuk menutup temuan. Karena suite tetap hijau, status `OPEN` harus dibuktikan dengan
  probe terarah, bukan dengan warna suite.
- **Pelajaran teknis:** (1) Defect yang bergantung pada output model bisa **intermiten**; tes
  regresinya harus menetralkan sumber nondeterminisme (`<eos>`) agar tidak flaky. (2) Kontrol
  negatif harus ikut deterministik — kontrol yang gagal karena `<eos>` sempat menyesatkan
  ("sliding window rusak") padahal mekanismenya benar. (3) Membandingkan kontrak sebaiknya
  terhadap rekaman bukti sebelumnya (D9), bukan terhadap asumsi.
- **Keterbatasan dan langkah selanjutnya:** CPU-only; V1b memakai artefak checkpoint D9 (50
  artikel), bukan C14 asli; akses volume Modal tidak tersedia sehingga F-D9-06 hanya sampai
  tingkat "berkas tidak ada di repo"; probe di luar pytest sehingga belum menjadi bagian suite.
  Langkah selanjutnya: perbaikan F-D9-01/F-D9-02 oleh pemilik Issue C, keputusan koordinator untuk
  F-D9-03/F-D9-05, lalu D10 dijalankan ulang dengan kriteria penutupan di
  `docs/D10_FIX_VERIFICATION.md` §12 dan tes regresi dipindahkan ke `tests/` pada D11.
