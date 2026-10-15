# Mini-Transformer Project

Proyek kelompok: Mini-GPT kecil (decoder-only transformer) untuk next-token prediction pada teks berita bahasa Indonesia, diimplementasikan manual dari nol dengan Python + PyTorch.

Kontrak teknis dan keputusan arsitektur dikunci melalui [Issue #1](https://github.com/AI-IF-TelU/AyayoTeam_MiniTransformer/issues/1) — `[STEP 2] Lock Mini-Transformer Technical Specification and Architecture Decisions`. Sumber kebenaran: `AGENTS.md` dan enam dokumen inti di `docs/`.

## Status proyek

- Spesifikasi & ADR: baseline final untuk Issue #1 — lihat `docs/TECH_SPEC.md` dan `docs/ARCHITECTURE_DECISIONS.md`.
- Implementasi model: belum dimulai. Direktori `src/`, `tests/`, `outputs/`, `scripts/` hanya berisi placeholder.
- Logging AI: plugin aktif; smoke test terverifikasi untuk satu anggota (lihat bagian Logging).

## Struktur proyek (target)

| Path | Isi (kontrak) |
|---|---|
| `src/data/` | `tokenizer.py`, `dataset.py` |
| `src/model/` | `positional_encoding.py`, `attention.py`, `decoder_block.py`, `minigpt.py` |
| `src/train.py` | training loop (loss, optimizer, logging metrics) |
| `src/generate.py` | greedy generation |
| `tests/` | unit test per modul |
| `outputs/metrics/` | catatan train/val loss |
| `docs/` | PRD, TECH_SPEC, ADR, dataset card, aturan AI, template log AI |
| `docs/ai-logs/` | raw JSONL + laporan Markdown interaksi AI |
| `scripts/ai_logging/` | placeholder tooling pendukung logging |

Struktur di atas adalah target berdasar kontrak modul. Keberadaan direktori tidak berarti fitur sudah selesai.

## Branch utama dan alur kerja

- Branch utama repository: **`master`**. Jangan mengubah nama branch atau pengaturan repository GitHub tanpa persetujuan.
- Satu GitHub Issue per unit kerja. Kerjakan pada feature branch:

```powershell
git checkout -b issue-<nomor>-<slug>
```

- Setelah selesai, buka Pull Request ke `master`. Tulis pesan commit ringkas sesuai gaya repo.
- Review oleh anggota selain pembuat; tes wajib lulus sebelum merge. Jangan merge langsung ke `master`.
- Jangan menandai Issue Done sebelum acceptance criteria terpenuhi.

## Setup

1. Python 3.x + PyTorch (instal via selector resmi pytorch.org), lalu dependensi pada `requirements.txt`.
2. Salin `.kilo/member.local.example copy.json` menjadi `.kilo/member.local.json`, isi `member_id` unik Anda (file ini di-ignore Git).
3. Jalankan smoke test logging di bawah sebelum mulai coding.

## Logging AI

Plugin `.kilo/plugin/mini-transformer-logger.ts` merekam event sesi Kilo:

- Raw: `docs/ai-logs/raw/<member-id>/<session-id>.jsonl`
- Laporan: `docs/ai-logs/reports/AI-LOG-<member-id>-<session-id>.md`

Redaction aktif untuk API key, token, password. Jangan menulis data sensitif ke log.

### Smoke-test prompt

> LOGGING SMOKE TEST. Do not edit any files or run commands. Reply exactly: `LOGGER-TEST-2026-01` and explain that this is only a test. This prompt and your response must be recorded by the project logger.

Setelah sesi, periksa raw JSONL berisi teks prompt dan respons Anda.

### Status verifikasi logging

- Bukti tersedia untuk anggota `raihanfahrifi-80017`: dua sesi terekam (62 dan 1174 baris event), prompt dan respons tertangkap.
- Bahwa satu anggota lolos **tidak** berarti semua lolos: setiap anggota wajib menjalankan smoke test pada instalasi/versi Kilo masing-masing dan mengonfirmasi capture sebelum coding.

## Aturan proyek

- Ikuti `AGENTS.md` dan enam dokumen inti `docs/`.
- Jangan mulai implementasi model sebelum Issue #1 selesai dan smoke test logging Anda lulus.
- Jangan mengubah keputusan arsitektur tanpa mencatatnya di `docs/ARCHITECTURE_DECISIONS.md` dan memperoleh persetujuan tim.