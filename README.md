# A* untuk Rute Jogging/Pendakian Paling Hemat Energi di Kawasan Kaliurang

Proyek Tugas Akhir - Artificial Intelligence, DTETI, Universitas Gadjah Mada.

Sistem ini mencari rute paling hemat energi (bukan sekadar paling pendek)
antara dua titik di kawasan Kaliurang, menggunakan algoritma **A\*** dengan
biaya per ruas jalur dihitung dari **kemiringan** (data elevasi SRTM) lewat
model biaya energi berjalan (Minetti et al., 2002).

## Fitur

- Graf jalur diambil dari OpenStreetMap (`osmnx`), area Kaliurang.
- Elevasi tiap node diambil dari SRTM 30m lewat API OpenTopoData.
- Biaya tiap ruas dihitung dari kemiringan pakai fungsi biaya energi Minetti.
- A* dan Uniform-Cost Search diimplementasikan dari nol (`src/pathfinding.py`),
  dengan heuristik jarak-garis-lurus (haversine) x biaya minimum per meter,
  yang terbukti admissible (lihat laporan untuk pembuktian lengkap).
- Aplikasi web interaktif (Streamlit + Folium): klik dua titik di peta,
  sistem menampilkan rute, jarak, total energi, elevasi naik, dan profil
  elevasi.

## Cara menjalankan

### 1. Install dependency

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Ambil data (butuh koneksi internet)

```bash
cd src
python fetch_data.py       # mengambil graf jalur OSM -> data/raw_graph.graphml
python add_elevation.py    # menambahkan elevasi SRTM  -> data/graph_with_elevation.graphml
cd ..
```

Proses `add_elevation.py` bisa memakan waktu beberapa menit tergantung
jumlah node, karena API elevasi dibatasi rate-nya.

### 3. Jalankan evaluasi (opsional, untuk data di laporan)

```bash
python src/evaluate.py
```

### 4. Jalankan aplikasi web

```bash
streamlit run app.py
```

Buka browser di alamat yang ditampilkan (biasanya `http://localhost:8501`).

## Struktur project

```
kaliurang-astar/
├── app.py                    # Aplikasi web Streamlit
├── requirements.txt
├── data/                     # Data graf (dihasilkan oleh script, bukan di-commit)
├── src/
│   ├── fetch_data.py         # Step 1: ambil graf dari OSM
│   ├── add_elevation.py      # Step 2: tambahkan elevasi SRTM
│   ├── energy_cost.py        # Step 3: fungsi biaya energi (Minetti) + haversine
│   ├── pathfinding.py        # Step 4: implementasi A* dan UCS dari nol
│   └── evaluate.py           # Step 5: evaluasi & perbandingan rute
└── README.md
```

## Formalisasi masalah

| Komponen | Definisi |
|---|---|
| State | Node (persimpangan/titik jalur) pada graf OSM |
| Initial / Goal state | Titik awal dan tujuan yang dipilih pengguna |
| Actions | Berpindah ke node tetangga melalui satu ruas jalur |
| Path cost g(n) | Total energi (J/kg), dari fungsi biaya Minetti dikali panjang ruas |
| Heuristic h(n) | Jarak haversine ke goal × biaya minimum per meter (admissible) |
| Strategi | A*, dibandingkan dengan Uniform-Cost Search sebagai baseline |

## Sumber data

- Jalur & jalan: © OpenStreetMap contributors, diambil lewat `osmnx`.
- Elevasi: SRTM 30m via [OpenTopoData](https://www.opentopodata.org/).
- Model biaya energi: Minetti et al. (2002), *"Energy cost of walking and
  running at extreme uphill and downhill slopes"*, European Journal of
  Applied Physiology. **(Cek dan kutip ulang dari paper aslinya di
  laporanmu.)**

## Keterbatasan

- Resolusi SRTM 30m bisa membuat estimasi kemiringan pada ruas pendek
  kurang presisi.
- Model Minetti dikalibrasi untuk berjalan/berlari manusia dewasa secara
  umum, belum disesuaikan per individu (berat badan, kebugaran).
- Heuristik yang dipakai valid (admissible) tapi longgar, sehingga A* pada
  graf ini belum tentu jauh lebih cepat dari UCS pada graf sekecil ini.

## Lisensi & Author

Dikerjakan oleh [nama kamu] untuk mata kuliah Artificial Intelligence,
DTETI UGM, 2026.
