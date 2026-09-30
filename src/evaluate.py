"""
Step 5: Evaluasi & perbandingan. Jalankan setelah data siap.

Menghasilkan tabel perbandingan yang bisa langsung kamu tempel ke laporan:
  1. Rute A* berbasis energi  vs  Rute A* berbasis jarak terpendek
  2. Jumlah node yang dieksplorasi: UCS vs A* (bukti A* lebih efisien
     karena heuristik memandu pencarian)

Cara pakai:
    python src/evaluate.py
"""

import osmnx as ox

from energy_cost import compute_edge_costs, haversine_m, min_possible_cost
from pathfinding import a_star_search, uniform_cost_search

GRAPH_PATH = "data/graph_with_elevation.graphml"

# GANTI dua node ini dengan node id nyata dari graf areamu.
# Cara dapat node id: buka data eksplorasi di notebooks/, atau klik di app.py.
START_NODE = None
GOAL_NODE = None


def make_heuristic(G, min_cost_per_meter):
    def h(node, goal):
        lat1, lon1 = G.nodes[node]["y"], G.nodes[node]["x"]
        lat2, lon2 = G.nodes[goal]["y"], G.nodes[goal]["x"]
        straight_line = haversine_m(lat1, lon1, lat2, lon2)
        return straight_line * min_cost_per_meter
    return h


def zero_heuristic(node, goal):
    return 0.0


def path_stats(G, path):
    dist = sum(_min_weight(G, path[i], path[i+1], "weight_distance")
               for i in range(len(path) - 1))
    energy = sum(_min_weight(G, path[i], path[i+1], "weight_energy")
                 for i in range(len(path) - 1))
    elevations = [G.nodes[n]["elevation"] for n in path]
    gain = sum(max(0, elevations[i+1] - elevations[i]) for i in range(len(elevations)-1))
    return {"distance_m": dist, "energy_J_per_kg": energy, "elevation_gain_m": gain}


def _min_weight(G, u, v, key):
    return min(d[key] for d in G.get_edge_data(u, v).values())


def run_evaluation(start=None, goal=None):
    print(f"Memuat graf dari {GRAPH_PATH} ...")
    G = ox.load_graphml(GRAPH_PATH)
    G = compute_edge_costs(G)

    if start is None:
        start = START_NODE or list(G.nodes)[0]
    if goal is None:
        goal = GOAL_NODE or list(G.nodes)[-1]

    print(f"Start: {start}, Goal: {goal}\n")

    min_cost = min_possible_cost()
    h_energy = make_heuristic(G, min_cost)

    # --- 1. Rute hemat energi (A*) vs rute terpendek (A* dengan bobot jarak) ---
    path_energy, cost_energy, exp_energy = a_star_search(G, start, goal, h_energy, "weight_energy")
    h_dist = make_heuristic(G, 1.0)  # heuristik untuk versi jarak: haversine langsung
    path_short, cost_short, exp_short = a_star_search(G, start, goal, h_dist, "weight_distance")

    print("=== Rute hemat energi (A*, weight_energy) ===")
    if path_energy:
        print(path_stats(G, path_energy))
    else:
        print("Tidak ditemukan jalur.")

    print("\n=== Rute terpendek (A*, weight_distance) ===")
    if path_short:
        print(path_stats(G, path_short))
    else:
        print("Tidak ditemukan jalur.")

    # --- 2. UCS vs A* pada tujuan energi: bandingkan jumlah node dieksplorasi ---
    _, _, exp_ucs = uniform_cost_search(G, start, goal, "weight_energy")
    print(f"\n=== Efisiensi pencarian (tujuan: minimasi energi) ===")
    print(f"UCS  node dieksplorasi : {exp_ucs}")
    print(f"A*   node dieksplorasi : {exp_energy}")

    return {
        "path_energy": path_energy, "path_shortest": path_short,
        "nodes_expanded_ucs": exp_ucs, "nodes_expanded_astar": exp_energy,
    }


if __name__ == "__main__":
    run_evaluation()
