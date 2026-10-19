# AI Rules & Vibe Engineering Standard

## 1. Sumber instruksi
Semua AI coding agent wajib membaca `AGENTS.md` serta enam dokumen inti dalam `docs/`. Jika instruksi bertentangan, hentikan perubahan dan laporkan konfliknya. Issue kerja tersedia lokal di folder `issues/`; AI agent tidak perlu akses GitHub.

## 2. Format prompt wajib
Setiap prompt coding harus memuat:
1. Context proyek dan Issue.
2. Task spesifik.
3. Specification/interface dan tensor shapes.
4. Constraints, file yang boleh diubah, dependensi yang diizinkan.
5. Expected output.
6. Acceptance criteria dan test yang diperlukan.
7. Penjelasan algoritma, kompleksitas, asumsi, edge cases, dan keterbatasan.

## 3. Template prompt

> Anda bekerja pada proyek Mini-GPT berbahasa Indonesia. Ikuti `AGENTS.md`, `docs/TECH_SPEC.md`, dan `docs/AI_RULES.md`. Kerjakan hanya modul [NAMA MODUL] pada Issue [NOMOR]. Sebelum menulis kode, jelaskan rencana implementasi, tensor shapes, dependensi, kompleksitas, dan edge cases. Setelah itu, hasilkan perubahan minimal pada file yang ditugaskan, sertakan unit test dan instruksi menjalankannya. Jangan mengubah interface modul lain atau menambah dependensi tanpa persetujuan. Jangan menyatakan tes berhasil jika belum dijalankan.

## 4. Batas perubahan
- Satu Issue per unit kerja.
- Jangan mengubah kontrak publik atau file di luar scope tanpa persetujuan.
- Jangan menambah dependency tanpa alasan dan persetujuan.
- Jangan menggunakan API/model pretrained sebagai model utama.
- Jangan menggunakan modul Transformer lengkap untuk menggantikan attention/decoder manual.
- Kode baru harus dilengkapi test atau alasan teknis yang jelas jika test belum layak dibuat.

## 5. Aturan output AI
- Nyatakan file yang akan diubah sebelum implementasi.
- Jelaskan keputusan teknis secara singkat.
- Tampilkan perintah pengujian dan hasil aktual.
- Pisahkan fakta yang diketahui dari asumsi.
- Jangan mengarang error, hasil test, metadata model, atau bukti dataset.

## 6. Logging
- Prompt, respons yang terlihat, event tool, dan error harus direkam oleh mekanisme logging yang telah diuji.
- Jangan menulis API key, token, password, atau data sensitif ke log.
- Jika logger gagal, jangan melanjutkan coding proyek tanpa memberitahu anggota tim dan memperbaiki logger.
- Raw log adalah bukti; ringkasan AI bukan pengganti raw log.
## 7. Review dan push (master-only)

- Gunakan satu branch utama `master`. Dilarang membuat branch baru, pull request, atau merge.
- Seluruh operasi Git (commit, push, pull, branch, merge, staging) dilakukan oleh anggota, bukan AI agent.
- Tes wajib harus lulus sebelum push.
- Perubahan ditinjau anggota selain pembuatnya sebelum push.
- `git pull --ff-only origin master` dilakukan anggota hanya saat anggota lain mengabarkan telah push perubahan (pengerjaan berurutan).
- Jangan menandai Issue Done sebelum acceptance criteria terpenuhi.
