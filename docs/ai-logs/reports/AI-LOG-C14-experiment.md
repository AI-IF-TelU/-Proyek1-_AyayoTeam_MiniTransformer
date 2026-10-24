# Laporan Eksperimen C14 — Training MiniGPT (4 Epoch, Modal CPU)

> Semua angka pada laporan ini diambil langsung dari `outputs/metrics/full/c14_metrics.jsonl` dan `outputs/metrics/full/minigpt_c14.pt`. Tidak ada nilai yang dikarang. Laporan ini bukan laporan log interaksi AI; laporan log interaksi tetap mengikuti `docs/AI_LOG_TEMPLATE.md`.

## 1. Metadata eksperimen

| Field | Nilai |
|---|---|
| Subtask | C14 — jalankan eksperimen serta dokumentasikan hasil aktual |
| Issue | [STEP 3] Issue C — MiniGPT, Training Loop & Text Generation |
| Tanggal run | 2026-10-24 (perilisan artefak ke repo) |
| Device | CPU 8 core (Modal) |
| PyTorch | `2.5.1+cu121` |
| Epochs | 4 |
| Durasi total | 5304,64 s (≈ 88,4 menit) |
| Jumlah parameter | 2.556.672 |
| Ukuran vocab | 19.192 (fit pada split train saja) |
| Segmen train | 246.290 |
| Segmen validasi | 28.229 |
| Konteks | `context_length = 64` |
| Arsitektur | `n_layers=2`, `n_heads=4`, `d_model=64`, `d_ff=256`, dropout 0.1, pre-LayerNorm |
| Optimizer | AdamW, `lr=3e-4`, `weight_decay=0.01` |
| Batch size | 32 |
| Seed | 42 |
| File metrics | `outputs/metrics/full/c14_metrics.jsonl` |
| File checkpoint | `outputs/metrics/full/minigpt_c14.pt` |
| Entry point skrip | `modal_app.py` (`python -m modal run modal_app.py`) |

## 2. Loss per epoch

| Epoch | Train loss | Val loss | Durasi epoch (s) |
|---:|---:|---:|---:|
| 1 | 5.568583 | 7.135150 | 1123.65 |
| 2 | 4.152143 | 7.856671 | 921.85 |
| 3 | 3.640476 | 8.304918 | 1115.32 |
| 4 | 3.335589 | 8.649888 | 2120.66 |

Perubahan train loss: −1.4164 (epoch 1→2), −0.5117 (2→3), −0.3049 (3→4). Total penurunan 2,2330.
Perubahan val loss: +0.7215 (1→2), +0.4482 (2→3), +0.3450 (3→4). Total kenaikan 1,5147.

## 3. Contoh text generation

Model terlatih (checkpoint epoch 4), greedy decoding (`max_new_tokens = 40`):

- **Prompt:** `presiden indonesia`
- **Output:**

```text
presiden indonesia , jokowi mengutus erick thohir bertemu dengan presiden jokowi . jokowi
menyebut bahwa pertemuan itu tidak ada campur tangan dengan ppp . " saya tidak ada
pembicaraan formal . saya pikir itu , " kata dia . saya , saya
```

Hasil ini diamati pada `c14_metrics.jsonl` (event `generation`) dan **direproduksi ulang** saat verifikasi lokal dengan memuat `minigpt_c14.pt` lalu memanggil `src/generate.py:generate` — keluaran identik, sehingga checkpoint terbukti konsisten dengan metrik yang tercatat.

## 4. Verifikasi artefak

Perintah verifikasi yang dijalankan (Python, root proyek):

```python
from src.train import load_checkpoint
from src.model.minigpt import MiniGPT
from src.data.tokenizer import Tokenizer

ck = load_checkpoint("outputs/metrics/full/minigpt_c14.pt")
```

Output aktual:

```text
CHECKPOINT OK
  state_dict tensors: 37
  vocab size: 19192
  model params: 2556672
  pos_enc.pe shape: (64, 64)
  config keys: ['model', 'train', 'gen']
GEN OK 'presiden indonesia , jokowi mengutus erick thohir bertemu dengan presiden jokowi'
```

Kesimpulan:

- Checkpoint berisi tiga kunci wajib: `state_dict`, `vocab`, `config` (sesuai Issue C §3.3 dan ADR-011).
- `state_dict` berisi 37 tensor dan dapat dimuat ke `MiniGPT` **tanpa key yang hilang/tidak dikenal** (`load_state_dict` strict).
- Jumlah parameter hasil muat ulang (2.556.672) sama dengan nilai yang tercatat di metrik.
- `config.model` berisi `vocab_size`, `n_layers`, `n_heads`, `d_model`, `context_length`, `d_ff`, `dropout`, `layer_norm_eps`. Catatan: `d_ff` tersimpan di config tetapi **bukan** argumen konstruktor `MiniGPT` (nilainya diturunkan sebagai `4 * d_model`), sehingga perlu dibuang sebelum instansiasi — bukan bug checkpoint, hanya detail pemuatan.
- Vocabulary pada checkpoint berukuran 19.192 termasuk 4 special token (`<pad>=0`, `<bos>=1`, `<eos>=2`, `<unk>=3`).

## 5. Analisis

### 5.1 Train loss turun, val loss naik → indikasi overfitting

Train loss turun monoton (5,5686 → 3,3356, −40%), sedangkan val loss **naik** monoton (7,1352 → 8,6499, +21%). Gap train–val melebar dari 1,57 nats pada epoch 1 menjadi 5,31 nats pada epoch 4. Pola ini adalah tanda klasik **overfitting**: model makin menghafal distribusi train sementara kemampuannya menggeneralisasi ke data validasi justru memburuk.

Faktor yang masuk akal (asumsi, bukan hasil pengukuran tambahan):

1. **Kapasitas vs data tidak seimbang arah.** Model hanya ~2,5 juta parameter, tetapi korpus train sangat besar (246.290 segmen). Overfitting pada model sekecil ini biasanya bukan karena parameter terlalu banyak, melainkan karena **vocab sangat besar (19.192)** dengan token langka berfrekuensi rendah. Ekor vocab dipelajari sebagai hapalan, dan di data validasi token tersebut bermunculan dengan konteks berbeda.
2. **Val loss absolut lebih tinggi dari train sejak epoch 1** (7,14 vs 5,57). Ini bukan gap nol, mengindikasikan distribusi val memang berbeda atau vocab/segmentasi val menghasilkan banyak posisi sulit.
3. **Kurva val naik konsisten tanpa titik minimum.** Tidak ada epoch di mana val loss lebih rendah dari epoch sebelumnya, sehingga "early stopping" tidak akan menyelamatkan run ini kecuali berdasarkan train loss — yang justru menyesatkan.
4. **Tidak ada learning-rate scheduling, weight decay kecil (0,01), dan dropout 0,1.** Kombinasi ini tidak memberi tekanan regularisasi yang cukup kuat untuk mengimbangi dominasi data train.

### 5.2 Keterbatasan pengamatan

- Hanya 4 epoch; tren val loss belum tentu berlanjut sama bentuknya pada run lebih panjang. Kesimpulan "overfitting" valid **untuk run ini**, bukan klaim umum.
- Val loss dihitung dengan `evaluate()` yang mengambil rata-rata per batch, bukan per token — bobot sampel pendek/pad berbeda dari metrik per-token murni. Perbandingan antar-epoch tetap sah karena prosedurnya identik, tetapi angka absolut tidak identik dengan metrik per-token.
- Tidak ada seed alternatif, tidak ada run baseline tanpa regularisasi, sehingga atribusi penyebab belum diuji secara eksperimental.

### 5.3 Kualitas generation

Keluaran terdengar koheren secara lokal: sintaks berita Indonesia, tanda kutip, frasa "kata dia", dan entitas (Jokowi, Erick Thohir, PPP). Ini **bukan bukti** model memahami fakta — model hanya memprediksi token berikutnya. Kalimat akhir terpotong di `", saya , saya"` karena batas `max_new_tokens` (40), bukan karena model selesai. Klaim "berita valid/terkini" tidak boleh dibuat.

## 6. Langkah selanjutnya (rekomendasi, belum dijalankan)

1. Tambahkan **early stopping pada val loss** dan simpan checkpoint terbaik (epoch 1 pada run ini) alih-alih checkpoint epoch terakhir.
2. Kurangi overfitting: naikkan `dropout` (0,1 → 0,2–0,3), naikkan `weight_decay`, atau batasi vocabulari ke token frekuensi ≥ N untuk memperkecil ekor vocab.
3. Tambahkan **learning-rate warmup + cosine decay** untuk run lebih dari 4 epoch.
4. Catat metrik per-token (bukan rata-rata per batch) agar perbandingan antar-run lebih ketat.
5. Uji ulang dengan seed berbeda untuk memastikan tren val naik bukan artefak satu run.

---

*Dokumen ini hanya mendokumentasikan hasil aktual dan analisisnya. Status overfitting adalah indikasi dari data yang ada, bukan hasil pengujian hipotesis terkontrol.*
