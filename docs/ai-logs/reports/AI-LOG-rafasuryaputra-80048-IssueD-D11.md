# AI Log — Issue D Subtask D11 (Tes Integrasi Lintas Modul)

> Laporan ini disusun dari sesi yang direkam otomatis. Semua angka berasal dari output run yang
> tercantum; tidak ada prompt, hasil test, atau keputusan yang dikarang.

## Metadata

- **Log ID:** AI-LOG-rafasuryaputra-80048-IssueD-D11
- **Tanggal/waktu:** 2026-10-24 21:11–21:45 WIB (UTC+07:00)
- **Anggota:** Rafa Suryaputra — `rafasuryaputra-80048`
- **Agent/tool:** Assistant Vengentic (Kilo Code CLI), tools: shell (PowerShell), file read/write/edit
- **Model:** Assistant Vengentic
- **Session ID:** `ses_e91bf8dfdffe39t80aphREXAm0`
- **GitHub Issue/PR:** [STEP 3] Issue D — Unit Test, Integrasi & Dokumentasi Teknis, subtask D11
- **Target modul:** `tests/` (integrasi lintas modul A/B/C), `docs/TESTING.md`, `README.md`
- **Raw log path:** `docs/ai-logs/raw/rafasuryaputra-80048/ses_e91bf8dfdffe39t80aphREXAm0.jsonl`
- **Share link:** tidak tersedia (lokal)

## Kronologi prompt dan respons

| # | Waktu (WIB) | Jenis | Isi ringkas | File terdampak |
|---|---|---|---|---|
| 1 | 21:11 | Prompt anggota | `SUBTASK PLANNING` D11: verifikasi repo/branch/Git/logging, baca Issue + AC + dependensi, jelaskan tujuan/algoritma/shapes/kompleksitas/edge cases/unit test, sebutkan file yang akan diubah, jangan menulis kode, jangan operasi Git | — |
| 2 | 21:11–21:14 | Respons asisten | Verifikasi: branch `master`, HEAD `68ff3df`, hanya 1 laporan logger untracked, raw log aktif, `.venv` Python 3.10.6/pytest 9.1.1/torch 2.14.1+cpu, `data/processed/` 720/80/200, baseline `162 tests collected`. Rencana: aktifkan marker `integration`, tambah `tests/test_end_to_end_pipeline.py`, perbarui `docs/TESTING.md` + `README.md`, tanpa menyentuh `src/`. Dilaporkan blocker: F-D9-01/F-D9-02 masih `OPEN` sehingga jalur restore→generate dan `context_length != 64` tidak bisa diintegrasikan | tidak ada |
| 3 | 21:14 | Prompt anggota | `SUBTASK IMPLEMENTATION` D11: implementasikan rencana, jelaskan kode/algoritma, buat/perbarui tes, jalankan dan tampilkan output aktual, tampilkan file berubah, pastikan logging, laporkan AC/kegagalan/keterbatasan, tanpa operasi Git | — |
| 4 | 21:15–21:25 | Respons asisten | Menulis `tests/test_end_to_end_pipeline.py` (7 tes), menambahkan `pytestmark = pytest.mark.integration` pada `test_integration_components.py` dan `test_train_integration.py`; dua iterasi debugging (arah relasi shift, jumlah token generasi); menjalankan suite; memperbarui `docs/TESTING.md` dan `README.md`; menulis laporan ini | `tests/test_end_to_end_pipeline.py`, `tests/test_integration_components.py`, `tests/test_train_integration.py`, `docs/TESTING.md`, `README.md`, laporan ini |

## Debugging

Semua pesan error di bawah adalah output aktual dari pytest pada sesi ini.

### Error 1 — arah relasi shift (`test_tokenizer_dataset_model_shapes`)

```text
E       AssertionError: x[i, t] != y[i, t-1] for non-pad positions (TECH_SPEC 4)
E       assert False
E        +  where False = <built-in method equal ...>(tensor([ 1, 15, 22, 18, ...]), tensor([22, 18, 10, 16, ...]))
```

Diagnosis: batch `[B, 64]` hasil collate punya padding independen di `x` dan `y`. Relasi yang benar
(`x[i,t] == y[i,t-1]`) hanya berlaku bila **kedua** sisi non-pad; pada posisi `t` di mana dokumen
pendek sudah habis, `x[t]` adalah pad sementara `y[t-1]` masih token nyata. Perbaikan: mask
`(y[:, :-1] != 0) & (x[:, 1:] != 0)` lalu bandingkan `x[:, 1:]` dengan `y[:, :-1]`.

### Error 2 — jumlah token generasi (`_RecordingTokenizer`)

```text
E       AssertionError: generation appended tokens after <eos>: [22]
E       assert [22] == [1, 22]
```

Diagnosis: `src/generate.py:24` mengembalikan `tokenizer.decode(ids[1:])` (bos dibuang), sehingga
perekam menerima id tanpa `<bos>`. Perbaikan: ekspektasi `prompt_ids[1:]`.

### Error 3 — asersi string generasi terlalu lemah

Run pertama memakai `long.startswith(short)`. Asersi itu bisa lolos palsu bila `decode` membuang id
special (pad/bos/eos/unk) dari token yang dihasilkan. Perbaikan: hitung **jumlah id** yang didekode
lewat `_RecordingTokenizer` dan bandingkan dengan `len(prompt) + max_new_tokens` untuk
`max_new_tokens` 0/3/8, serta uji stop `<eos>` dengan membandingkan id yang didekode secara eksak.

### Perubahan yang dilakukan pada tes generasi

`_force_next_token` memakai forward hook pada `lm_head` untuk mengambil hidden state akhir, lalu
menetapkan seluruh baris `lm_head.weight = -h/||h||` dan baris target `= +10 h/||h||`. Ini membuat
argmax deterministik tanpa mengganti model: embedding, PE, decoder block, LayerNorm, dan forward
pass tetap nyata. Hasil setelah perbaikan: `7 passed in 16.91s`.

## Verifikasi

- **Perintah test yang dijalankan:**

```powershell
.\.venv\Scripts\python.exe -m pytest --collect-only -q --run-integration
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pytest -q --run-integration
.\.venv\Scripts\python.exe -m pytest -q -m integration --run-integration
.\.venv\Scripts\python.exe -m pytest tests/test_end_to_end_pipeline.py -v --run-integration
```

- **Output aktual:**

```text
169 tests collected in 9.87s
154 passed, 15 skipped in 26.13s
169 passed in 23.80s
15 passed, 154 deselected in 20.22s
7 passed in 16.91s
```

- **Commit SHA:** `68ff3df` (`feat(Issue D): Substask D10`), branch `master`, tanpa operasi Git.
- **Acceptance criteria yang terpenuhi (D11):**
  - Seluruh tes kontrak A/B/C dapat dijalankan bersama dalam satu perintah
    (`python -m pytest -q --run-integration` → `169 passed`).
  - Marker `integration` benar-benar dipakai: 15 tes, tiga berkas; `-q` dan `-q --run-integration`
    kini berbeda secara nyata (154+15 vs 169), menghapus keterbatasan D8 nomor 1.
  - Tes integrasi memeriksa perilaku kontraktual dengan komponen nyata: relasi shift, padding
    diabaikan loss, pembaruan parameter, `max_new_tokens`, stop `<eos>`, sliding window, dan
    jumlah window korpus nyata per dokumen.
  - Tidak ada perubahan `src/`, kontrak publik, `pytest.ini`, atau dependency.
- **Acceptance criteria yang belum terpenuhi (D11):**
  - F-D9-01/F-D9-02/F-D9-03 masih `OPEN`; jalur restore checkpoint→`generate` dan
    `generate` pada `context_length != 64` sengaja tidak diintegrasikan sampai pemilik Issue C
    memperbaiki. D11 tidak menutup temuan tersebut.

## Refleksi yang diverifikasi anggota

- **Mengapa pendekatan dipilih:** D11 menuntut "satu perintah menjalankan seluruh suite". Sebelum
  D11, opsi `--run-integration` tidak mengubah apa pun karena tidak ada tes bertanda. Menandai
  tes lintas modul yang sudah ada (komponen B, training C11) dan menambah satu berkas alur penuh
  A→B→C memberi sinyal berbeda antara suite cepat dan suite integrasi, tanpa memperlambat
  pekerjaan sehari-hari.
- **Pelajaran teknis:** (1) Relasi `x[i,t] == y[i,t-1]` hanya valid bila kedua sisi non-pad;
  padding independen pada `x` dan `y` membuat asersi naif gagal. (2) Menguji aturan berhenti
  generasi lewat string hasil `decode` tidak cukup, karena id special dibuang saat decode —
  jumlah id harus diukur sebelum decode. (3) Menentukan argmax secara deterministik bisa dilakukan
  dengan mengatur arah `lm_head` (tanpa bias) memakai hidden state nyata, sehingga model asli tetap
  diuji.
- **Keterbatasan dan langkah selanjutnya:** CPU-only; korpus nyata dibatasi 60 dokumen; tidak
  melatih hingga konvergen. Temuan baru F-D11-01 (`helpers.make_batch` arah shift terbalik, saat
  ini tidak dipakai tes mana pun) dicatat di `docs/TESTING.md` dan perlu keputusan pemilik
  Issue D/koordinator. Langkah selanjutnya: perbaikan Issue C untuk F-D9-01/F-D9-02, lalu
  pemindahan tes regresi dari `docs/D10_FIX_VERIFICATION.md` §12 ke `tests/` dan D12 (dokumentasi
  pengujian) setelah keputusan tersebut.
