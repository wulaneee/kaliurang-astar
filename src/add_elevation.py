"""
Step 2: Tambahkan elevasi (SRTM 30m) ke setiap node graf.

Sumber elevasi: API gratis OpenTopoData (https://www.opentopodata.org/),
dataset SRTM 30m. API ini punya batas rate (sekitar 1 request/detik,
maks 100 titik per request), jadi script ini mengirim per-batch dan
memberi jeda supaya tidak diblokir.

Cara pakai:
    python src/add_elevation.py

Input:  data/raw_graph.graphml
Output: data/graph_with_elevation.graphml
"""

import time
import requests
import networkx as nx
import osmnx as ox

INPUT_PATH = "data/raw_graph.graphml"
OUTPUT_PATH = "data/graph_with_elevation.graphml"

API_URL = "https://api.opentopodata.org/v1/srtm30m"
BATCH_SIZE = 100     # maksimum titik per request sesuai batas API
SLEEP_SECONDS = 1.1  # jeda antar request supaya tidak kena rate limit


def get_elevations(coords):
    """coords: list of (lat, lon) -> list of elevation (meter), None kalau gagal."""
    elevations = []
    for i in range(0, len(coords), BATCH_SIZE):
        batch = coords[i:i + BATCH_SIZE]
        locations = "|".join(f"{lat},{lon}" for lat, lon in batch)
        resp = requests.get(API_URL, params={"locations": locations}, timeout=30)
        resp.raise_for_status()
        results = resp.json()["results"]
        elevations.extend(r["elevation"] for r in results)
        print(f"  ... {min(i + BATCH_SIZE, len(coords))}/{len(coords)} titik selesai")
        time.sleep(SLEEP_SECONDS)
    return elevations


def add_elevation_to_graph():
    print(f"Memuat graf dari {INPUT_PATH} ...")
    G = ox.load_graphml(INPUT_PATH)

    node_ids = list(G.nodes)
    coords = [(float(G.nodes[n]["y"]), float(G.nodes[n]["x"])) for n in node_ids]

    print(f"Mengambil elevasi untuk {len(coords)} node dari OpenTopoData ...")
    elevations = get_elevations(coords)

    missing = sum(1 for e in elevations if e is None)
    if missing:
        print(f"PERINGATAN: {missing} titik gagal dapat elevasi, akan diisi "
              f"dengan rata-rata elevasi yang berhasil.")
        valid = [e for e in elevations if e is not None]
        avg = sum(valid) / len(valid)
        elevations = [e if e is not None else avg for e in elevations]

    for node_id, elev in zip(node_ids, elevations):
        G.nodes[node_id]["elevation"] = float(elev)

    elev_values = [G.nodes[n]["elevation"] for n in G.nodes]
    print(f"Elevasi min: {min(elev_values):.1f} m, max: {max(elev_values):.1f} m, "
          f"beda tinggi: {max(elev_values) - min(elev_values):.1f} m")

    ox.save_graphml(G, OUTPUT_PATH)
    print(f"Graf dengan elevasi disimpan ke {OUTPUT_PATH}")
    return G


if __name__ == "__main__":
    add_elevation_to_graph()
