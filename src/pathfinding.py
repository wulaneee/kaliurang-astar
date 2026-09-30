"""
Step 4: Implementasi A* dan Uniform-Cost Search dari nol.

Ini SENGAJA ditulis manual (bukan networkx.astar_path / dijkstra_path)
karena syarat tugas: algoritma inti harus kamu pahami dan tulis sendiri.
networkx hanya dipakai untuk struktur graf (get neighbor, atribut edge),
bukan untuk mencari jalurnya.

Setiap fungsi mengembalikan:
    path            : list of node id, dari start ke goal (None kalau tidak ada jalur)
    total_cost      : total bobot sepanjang path
    nodes_expanded  : jumlah node yang di-pop dari priority queue (untuk evaluasi)
"""

import heapq
import networkx as nx


def _min_edge_weight(G, u, v, weight_key):
    """Kalau ada beberapa edge paralel u->v (MultiDiGraph), ambil yang termurah."""
    edges = G.get_edge_data(u, v)
    return min(data[weight_key] for data in edges.values())


def uniform_cost_search(G: nx.MultiDiGraph, start, goal, weight_key="weight_energy"):
    """UCS: Dijkstra tanpa heuristik. Dipakai sebagai baseline pembanding A*."""
    frontier = [(0.0, start)]
    came_from = {start: None}
    cost_so_far = {start: 0.0}
    nodes_expanded = 0

    while frontier:
        current_cost, current = heapq.heappop(frontier)
        nodes_expanded += 1

        if current == goal:
            return _reconstruct_path(came_from, start, goal), current_cost, nodes_expanded

        # Kalau entry ini sudah usang (sudah ada jalur lebih murah), lewati.
        if current_cost > cost_so_far.get(current, float("inf")):
            continue

        for neighbor in G.successors(current):
            edge_cost = _min_edge_weight(G, current, neighbor, weight_key)
            new_cost = cost_so_far[current] + edge_cost

            if new_cost < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_cost
                came_from[neighbor] = current
                heapq.heappush(frontier, (new_cost, neighbor))

    return None, float("inf"), nodes_expanded


def a_star_search(G: nx.MultiDiGraph, start, goal, heuristic_fn, weight_key="weight_energy"):
    """
    A*: f(n) = g(n) + h(n)
      g(n) = biaya nyata dari start ke n (weight_key di sepanjang edge)
      h(n) = heuristic_fn(n, goal) -> estimasi biaya n ke goal, harus admissible
             (tidak pernah melebih-lebihkan biaya sebenarnya)
    """
    start_h = heuristic_fn(start, goal)
    frontier = [(start_h, start)]          # f(n) = g(n) + h(n), g(start) = 0
    came_from = {start: None}
    cost_so_far = {start: 0.0}             # ini menyimpan g(n), bukan f(n)
    nodes_expanded = 0

    while frontier:
        _, current = heapq.heappop(frontier)
        nodes_expanded += 1

        if current == goal:
            return _reconstruct_path(came_from, start, goal), cost_so_far[current], nodes_expanded

        for neighbor in G.successors(current):
            edge_cost = _min_edge_weight(G, current, neighbor, weight_key)
            new_g = cost_so_far[current] + edge_cost

            if new_g < cost_so_far.get(neighbor, float("inf")):
                cost_so_far[neighbor] = new_g
                priority = new_g + heuristic_fn(neighbor, goal)
                heapq.heappush(frontier, (priority, neighbor))
                came_from[neighbor] = current

    return None, float("inf"), nodes_expanded


def _reconstruct_path(came_from, start, goal):
    path = [goal]
    node = goal
    while node != start:
        node = came_from[node]
        path.append(node)
    path.reverse()
    return path
