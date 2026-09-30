# Outline Laporan (maks. 6 halaman)

Isi tiap bagian dengan pemahamanmu sendiri — ini kerangka, bukan isi jadi.
Bagian yang ditandai (*) WAJIB dites lisan, jadi pastikan kamu paham betul.

## 1. Pendahuluan (~0.5 halaman)
- Masalah: rute terpendek untuk jalur pendakian/jogging sering tidak
  optimal secara energi karena mengabaikan kemiringan.
- Tujuan: mencari rute paling hemat energi memakai A*.
- Link repo GitHub.

## 2. Formalisasi Masalah (*) (~1 halaman)
- State, initial/goal state, actions, path cost, strategi (isi tabel di README).
- **Definisi g(n)**: jelaskan rumus Minetti, kenapa memilih model ini
  dibanding alternatif (Tobler dsb).
- **Definisi h(n)**: jelaskan haversine × biaya minimum per meter.
- **Bukti admissibility (*)**: tulis dengan kata-katamu sendiri kenapa
  h(n) tidak pernah melebih-lebihkan biaya sebenarnya. Intinya: karena
  tidak ada ruas jalur yang bisa lebih murah per meter daripada nilai
  minimum polinomial Minetti, dan jarak garis lurus selalu ≤ jarak jalur
  sebenarnya, maka h(n) ≤ biaya asli ke goal.

## 3. Data (~0.5-1 halaman)
- Sumber: OpenStreetMap (jalur), OpenTopoData/SRTM (elevasi).
- Area yang dipakai (nama, koordinat pusat, radius) + alasan memilihnya
  (beda tinggi, kepadatan jalur).
- Statistik graf akhir: jumlah node, edge, beda elevasi min-max.
- Screenshot area di peta.

## 4. Implementasi (*) (~1 halaman)
- Struktur data graf (networkx MultiDiGraph, kenapa directed).
- Implementasi A* dan UCS: jelaskan cara kerja heapq, g(n), f(n).
- Potongan kode kunci (heuristik + loop utama A*).
- Halaman ini yang paling sering ditanya "kenapa begini" saat oral.

## 5. Hasil & Evaluasi (~1-1.5 halaman)
- Screenshot aplikasi web dengan satu contoh rute.
- Tabel: rute hemat energi vs rute terpendek (jarak, energi, elevasi naik).
- Tabel/grafik: node dieksplorasi UCS vs A* (bukti efisiensi heuristik).
- Minimal 2-3 pasang titik awal-tujuan berbeda untuk pembanding, bukan cuma satu.

## 6. Diskusi & Keterbatasan (*) (~0.5-1 halaman)
- Keterbatasan resolusi SRTM.
- Model energi Minetti untuk populasi umum, bukan personal.
- Kapan rute hemat energi = rute terpendek (area datar) dan kapan berbeda jauh.
- Potensi pengembangan (personalisasi berat badan, cuaca, permukaan jalur).

## 7. Referensi
- Minetti et al. (2002) — cantumkan sitasi lengkap dari paper asli.
- OpenStreetMap contributors.
- OpenTopoData / SRTM.
- Dokumentasi osmnx, networkx (kalau dirujuk langsung).

---

### Checklist sebelum submit
- [ ] Judul laporan = judul yang didaftarkan di ugm.id/aitbproject (persis sama)
- [ ] Link GitHub repo ada di laporan
- [ ] Repo GitHub public / dibagikan ke staff
- [ ] README repo lengkap (cara menjalankan)
- [ ] Laporan ≤ 6 halaman
- [ ] Semua sumber data/kode yang dikutip dicantumkan
- [ ] Kamu bisa jelaskan bagian (*) tanpa membaca catatan
