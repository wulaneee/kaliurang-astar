"""
Step 3: Fungsi biaya energi berbasis kemiringan, dan penambahan bobot
'weight_energy' + 'weight_distance' ke setiap edge graf.

PENTING UNTUK LAPORANMU:
Formula di bawah ini mengacu pada penelitian Minetti et al. (2002),
"Energy cost of walking and running at extreme uphill and downhill
slopes", yang memodelkan biaya metabolik berjalan (J per kg berat badan
per meter jarak tempuh) sebagai polinomial derajat 5 terhadap kemiringan i
(i = rise/run, misal i = 0.1 untuk tanjakan 10%).

    C(i) = 155.4*i^5 - 30.4*i^4 - 43.3*i^3 + 46.3*i^2 + 19.5*i + 3.6

Ini SALAH SATU pilihan yang umum dipakai di literatur locomotion energetics,
bukan satu-satunya. Sebelum dipakai di laporan resmi:
  1. Cari paper aslinya dan cek koefisiennya cocok dengan yang kamu kutip.
  2. Tuliskan alasanmu memilih formula ini dibanding alternatif lain
     (misalnya Tobler's hiking function, yang berbasis kecepatan/waktu,
     bukan energi).
  3. Formula ini valid kira-kira untuk kemiringan -0.45 <= i <= 0.45;
     di luar itu hasilnya tidak realistis, jadi kita clamp nilainya.
"""

import math
import networkx as nx

MIN_GRADIENT = -0.45
MAX_GRADIENT = 0.45


def minetti_cost(gradient: float) -> float:
    """Biaya energi berjalan (J/kg per meter jarak tempuh) untuk kemiringan i."""
    i = max(MIN_GRADIENT, min(MAX_GRADIENT, gradient))
    return (155.4 * i**5 - 30.4 * i**4 - 43.3 * i**3
            + 46.3 * i**2 + 19.5 * i + 3.6)


def min_possible_cost() -> float:
    """
    Nilai minimum C(i) di seluruh rentang kemiringan yang valid.
    Dipakai sebagai konstanta di heuristik A* supaya heuristik terbukti
    admissible (tidak pernah melebih-lebihkan biaya sebenarnya).
    """
    step = 0.001
    i = MIN_GRADIENT
    best = float("inf")
    while i <= MAX_GRADIENT:
        best = min(best, minetti_cost(i))
        i += step
    return best


def compute_edge_costs(G: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Untuk setiap edge (u -> v), hitung:
      - length         : sudah ada dari OSM (meter)
      - gradient       : (elevasi_v - elevasi_u) / length
      - weight_energy  : minetti_cost(gradient) * length   (Joule/kg, arah u->v)
      - weight_distance: sama dengan length (untuk pembanding rute terpendek)

    Karena naik dan turun beda biaya, graf tetap directed (MultiDiGraph):
    edge u->v dan v->u dihitung terpisah dan BISA berbeda bobotnya.
    """
    for u, v, k, data in G.edges(keys=True, data=True):
        length = float(data.get("length", 0.0))
        elev_u = G.nodes[u]["elevation"]
        elev_v = G.nodes[v]["elevation"]

        gradient = (elev_v - elev_u) / length if length > 0 else 0.0

        data["gradient"] = gradient
        data["weight_energy"] = minetti_cost(gradient) * length
        data["weight_distance"] = length

    return G


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    """Jarak garis lurus antara dua titik (lat, lon) dalam meter."""
    R = 6371000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = (math.sin(dphi / 2) ** 2
         + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2)
    return 2 * R * math.asin(math.sqrt(a))
