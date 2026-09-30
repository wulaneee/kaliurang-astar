"""
Step 1: Ambil graf jalur jalan kaki dari OpenStreetMap di sekitar Kaliurang.

Cara pakai:
    python src/fetch_data.py

Catatan: script ini butuh akses internet ke server OpenStreetMap (lewat
osmnx), jadi jalankan di komputermu sendiri, bukan di sandbox/container
tanpa internet.

Output:
    data/raw_graph.graphml  -> graf mentah (belum ada elevasi)
"""

import osmnx as ox

# ---------------------------------------------------------------------------
# UBAH BAGIAN INI kalau kamu ingin pindah titik pusat atau memperbesar radius.
# Titik ini adalah perkiraan area Kaliurang (Tlogo Putri - Plawangan).
# Cek & sesuaikan koordinatnya di openstreetmap.org sebelum dipakai serius.
# ---------------------------------------------------------------------------
CENTER_POINT = (-7.5980, 110.4235)   # (lat, lon) -> GANTI sesuai area finalmu
RADIUS_METERS = 2500                 # radius area yang diambil, dalam meter
NETWORK_TYPE = "walk"                # jalur untuk pejalan kaki/pendaki

OUTPUT_PATH = "data/raw_graph.graphml"


def fetch_graph():
    print(f"Mengambil graf jalur 'walk' di sekitar {CENTER_POINT}, "
          f"radius {RADIUS_METERS} m ...")

    G = ox.graph_from_point(
        CENTER_POINT,
        dist=RADIUS_METERS,
        network_type=NETWORK_TYPE,
        simplify=True,
    )

    print(f"Berhasil: {len(G.nodes)} node, {len(G.edges)} edge.")

    # Buang node yang tidak terhubung ke komponen utama supaya A* tidak
    # gagal saat mencoba rute ke node yang tidak terjangkau.
    largest_cc = max(
        (G.subgraph(c).copy() for c in ox_connected_components(G)),
        key=lambda g: len(g.nodes),
    )
    print(f"Komponen terhubung terbesar: {len(largest_cc.nodes)} node "
          f"(dari total {len(G.nodes)} node).")

    ox.save_graphml(largest_cc, OUTPUT_PATH)
    print(f"Graf disimpan ke {OUTPUT_PATH}")
    return largest_cc


def ox_connected_components(G):
    # osmnx graf 'walk' berupa MultiDiGraph; pakai versi undirected
    # untuk mencari komponen terhubung, supaya jalur dua-arah lebih akurat.
    import networkx as nx
    return nx.connected_components(G.to_undirected())


if __name__ == "__main__":
    fetch_graph()
