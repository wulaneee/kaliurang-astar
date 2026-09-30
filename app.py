"""
Step 6: Aplikasi web sederhana. Pengguna klik dua titik di peta,
sistem mencari rute paling hemat energi (A*) dan menampilkannya,
lengkap dengan profil elevasi dan perbandingan dengan rute terpendek.

Cara pakai:
    streamlit run app.py
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import streamlit as st
import osmnx as ox
import folium
from streamlit_folium import st_folium
import matplotlib.pyplot as plt

from energy_cost import compute_edge_costs, haversine_m, min_possible_cost
from pathfinding import a_star_search

# Warna untuk membedakan rute di peta
COLOR_ENERGY = "#1f77ff"     # biru: rute hemat energi (rute utama sistem ini)
COLOR_SHORTEST = "#ff7f0e"   # oranye putus-putus: rute terpendek (pembanding)

GRAPH_PATH = "data/graph_with_elevation.graphml"

st.set_page_config(page_title="Rute Jogging Hemat Energi - Kaliurang", layout="wide")
st.title("🏃 Rute Jogging/Pendakian Paling Hemat Energi - Kaliurang")
st.caption("A* dengan biaya berbasis kemiringan (Minetti et al., 2002) pada data OSM + SRTM")


@st.cache_resource
def load_graph():
    G = ox.load_graphml(GRAPH_PATH)
    G = compute_edge_costs(G)
    return G


def make_heuristic(G, min_cost_per_meter):
    def h(node, goal):
        lat1, lon1 = G.nodes[node]["y"], G.nodes[node]["x"]
        lat2, lon2 = G.nodes[goal]["y"], G.nodes[goal]["x"]
        return haversine_m(lat1, lon1, lat2, lon2) * min_cost_per_meter
    return h


def path_latlon(G, path):
    """
    Ubah urutan node jadi daftar koordinat untuk digambar di peta.

    PENTING: satu ruas (edge) di OSM bisa berbentuk berkelok meskipun cuma
    menghubungkan 2 node persimpangan. Kelokannya disimpan sebagai atribut
    'geometry' pada edge, terpisah dari posisi node. Kalau kita cuma
    menggambar garis lurus antar-node, hasilnya jadi "memotong" jalur asli.
    Fungsi ini mengambil geometry itu kalau ada, supaya garis di peta
    benar-benar mengikuti bentuk jalur sebenarnya.
    """
    coords = [(G.nodes[path[0]]["y"], G.nodes[path[0]]["x"])]

    for u, v in zip(path[:-1], path[1:]):
        edge_dict = G.get_edge_data(u, v)
        # Kalau ada beberapa edge paralel, pilih yang jaraknya paling pendek
        # (konsisten dengan cara kita menghitung biaya di energy_cost.py)
        best_key = min(edge_dict, key=lambda k: edge_dict[k].get("length", float("inf")))
        edge_data = edge_dict[best_key]
        geom = edge_data.get("geometry")

        added = False
        if geom is not None:
            try:
                pts = [(lat, lon) for lon, lat in geom.coords]
                u_point = (G.nodes[u]["y"], G.nodes[u]["x"])
                if haversine_m(pts[0][0], pts[0][1], u_point[0], u_point[1]) > \
                   haversine_m(pts[-1][0], pts[-1][1], u_point[0], u_point[1]):
                    pts = list(reversed(pts))
                coords.extend(pts[1:])
                added = True
            except Exception:
                added = False

        if not added:
            coords.append((G.nodes[v]["y"], G.nodes[v]["x"]))

    return coords


def path_elevation_profile(G, path):
    dist = 0.0
    xs, ys = [0.0], [G.nodes[path[0]]["elevation"]]
    for i in range(len(path) - 1):
        u, v = path[i], path[i + 1]
        d = min(data["weight_distance"] for data in G.get_edge_data(u, v).values())
        dist += d
        xs.append(dist)
        ys.append(G.nodes[v]["elevation"])
    return xs, ys


def path_stats(G, path):
    """Hitung jarak total, energi total, dan elevasi naik total sepanjang path."""
    distance = sum(
        min(d["weight_distance"] for d in G.get_edge_data(path[i], path[i + 1]).values())
        for i in range(len(path) - 1)
    )
    energy = sum(
        min(d["weight_energy"] for d in G.get_edge_data(path[i], path[i + 1]).values())
        for i in range(len(path) - 1)
    )
    elevations = [G.nodes[n]["elevation"] for n in path]
    gain = sum(max(0, elevations[i + 1] - elevations[i]) for i in range(len(elevations) - 1))
    return {"distance_m": distance, "energy_J_per_kg": energy, "elevation_gain_m": gain}


try:
    G = load_graph()
except FileNotFoundError:
    st.error(
        "Data graf belum ada. Jalankan dulu di terminal:\n\n"
        "1. `python src/fetch_data.py`\n"
        "2. `python src/add_elevation.py`\n\n"
        "Baru jalankan `streamlit run app.py` lagi."
    )
    st.stop()

if "points" not in st.session_state:
    st.session_state.points = []

center_lat = sum(G.nodes[n]["y"] for n in G.nodes) / len(G.nodes)
center_lon = sum(G.nodes[n]["x"] for n in G.nodes) / len(G.nodes)

col_map, col_info = st.columns([2, 1])

# Hitung dulu rute (kalau sudah ada 2 titik), supaya bisa langsung digambar di peta
path_energy = path_shortest = None
start_node = goal_node = None

if len(st.session_state.points) == 2:
    start_latlon, goal_latlon = st.session_state.points
    start_node = ox.distance.nearest_nodes(G, start_latlon[1], start_latlon[0])
    goal_node = ox.distance.nearest_nodes(G, goal_latlon[1], goal_latlon[0])

    # Seberapa jauh titik klik asli dari node jalur terdekat yang dipakai
    # sistem (kalau jauh, berarti di lokasi itu tidak ada jalur yang
    # terpetakan di OSM sampai sedekat itu).
    start_snap_dist = haversine_m(
        start_latlon[0], start_latlon[1], G.nodes[start_node]["y"], G.nodes[start_node]["x"]
    )
    goal_snap_dist = haversine_m(
        goal_latlon[0], goal_latlon[1], G.nodes[goal_node]["y"], G.nodes[goal_node]["x"]
    )

    min_cost = min_possible_cost()
    h_energy = make_heuristic(G, min_cost)
    h_distance = make_heuristic(G, 1.0)  # heuristik jarak: haversine langsung (biaya min per meter = 1)

    path_energy, total_energy, expanded_energy = a_star_search(
        G, start_node, goal_node, h_energy, "weight_energy"
    )
    path_shortest, total_shortest, expanded_shortest = a_star_search(
        G, start_node, goal_node, h_distance, "weight_distance"
    )

with col_map:
    st.write("Klik **titik awal**, lalu klik **titik tujuan** di peta.")
    st.markdown(
        f"<span style='color:{COLOR_ENERGY}'>&#9644;&#9644;</span> Rute hemat energi &nbsp;&nbsp;"
        f"<span style='color:{COLOR_SHORTEST}'>&#9644;&#9644;</span> Rute terpendek (pembanding)",
        unsafe_allow_html=True,
    )
    show_full_network = st.checkbox(
        "🔍 Tampilkan seluruh jaringan jalur (untuk cek: apakah dua jalur "
        "yang kelihatan dekat itu benar-benar tersambung?)",
        value=False,
    )

    m = folium.Map(location=[center_lat, center_lon], zoom_start=14)

    if show_full_network:
        # Gambar SEMUA ruas jalur yang berhasil diambil sistem, sebagai
        # garis abu-abu tipis. Kalau dua jalur di peta terlihat berdekatan
        # tapi TIDAK ada garis abu-abu yang menyambungkan keduanya, berarti
        # keduanya memang terpisah di data OSM (bukan satu jalur bercabang).
        edges_gdf = ox.graph_to_gdfs(G, nodes=False)
        folium.GeoJson(
            edges_gdf.__geo_interface__,
            style_function=lambda feat: {"color": "#999999", "weight": 1.5, "opacity": 0.6},
        ).add_to(m)

    # Marker biru: titik persis tempat kamu klik
    for lat, lon in st.session_state.points:
        folium.Marker([lat, lon], icon=folium.Icon(color="blue")).add_to(m)

    # Marker hijau: node jalur terdekat yang BENAR-BENAR dipakai algoritma.
    # Kalau posisinya jauh dari marker biru, berarti jalur di OSM tidak
    # sampai sedekat itu ke titik yang kamu klik.
    if start_node is not None:
        folium.Marker(
            [G.nodes[start_node]["y"], G.nodes[start_node]["x"]],
            icon=folium.Icon(color="green", icon="play"),
            tooltip=f"Titik awal (jarak snap: {start_snap_dist:.0f} m)",
        ).add_to(m)
    if goal_node is not None:
        folium.Marker(
            [G.nodes[goal_node]["y"], G.nodes[goal_node]["x"]],
            icon=folium.Icon(color="green", icon="flag"),
            tooltip=f"Titik tujuan (jarak snap: {goal_snap_dist:.0f} m)",
        ).add_to(m)

    # Gambar rute terpendek dulu (garis putus-putus, oranye) di bawah,
    # baru rute hemat energi (garis solid, biru) di atasnya, supaya
    # kalau dua rute sama persis, garis biru tetap terlihat jelas.
    if path_shortest:
        folium.PolyLine(
            path_latlon(G, path_shortest),
            color=COLOR_SHORTEST, weight=5, opacity=0.9, dash_array="8,8",
            tooltip="Rute terpendek",
        ).add_to(m)

    if path_energy:
        folium.PolyLine(
            path_latlon(G, path_energy),
            color=COLOR_ENERGY, weight=5, opacity=0.9,
            tooltip="Rute hemat energi",
        ).add_to(m)

    map_data = st_folium(m, height=550, width=None)

    if map_data and map_data.get("last_clicked"):
        latlon = (map_data["last_clicked"]["lat"], map_data["last_clicked"]["lng"])
        if len(st.session_state.points) >= 2:
            st.session_state.points = []
        st.session_state.points.append(latlon)
        st.rerun()

    if st.button("Reset titik"):
        st.session_state.points = []
        st.rerun()

with col_info:
    if len(st.session_state.points) < 2:
        st.info("Klik dua titik di peta untuk mulai (titik awal lalu titik tujuan).")
    elif path_energy is None or path_shortest is None:
        st.warning("Tidak ditemukan rute antara dua titik ini (mungkin di luar jaringan jalur, "
                   "coba klik lebih dekat ke jalur yang ada).")
    else:
        if start_snap_dist > 30 or goal_snap_dist > 30:
            st.warning(
                f"⚠️ Titik yang kamu klik cukup jauh dari jalur yang terpetakan di OSM: "
                f"titik awal meleset {start_snap_dist:.0f} m, titik tujuan meleset "
                f"{goal_snap_dist:.0f} m dari jalur terdekat. Lihat marker **hijau** di peta "
                f"untuk posisi asli yang dipakai sistem — coba klik lebih dekat ke garis "
                f"jalur (putus-putus) yang ada."
            )

        stats_energy = path_stats(G, path_energy)
        stats_shortest = path_stats(G, path_shortest)
        same_route = path_energy == path_shortest

        st.subheader("Rute hemat energi")
        st.metric("Jarak tempuh", f"{stats_energy['distance_m']:.0f} m")
        st.metric("Estimasi energi", f"{stats_energy['energy_J_per_kg']:.0f} J/kg")
        st.metric("Elevasi naik", f"{stats_energy['elevation_gain_m']:.0f} m")

        st.divider()
        st.subheader("Rute terpendek (pembanding)")
        st.metric("Jarak tempuh", f"{stats_shortest['distance_m']:.0f} m")
        st.metric("Estimasi energi", f"{stats_shortest['energy_J_per_kg']:.0f} J/kg")
        st.metric("Elevasi naik", f"{stats_shortest['elevation_gain_m']:.0f} m")

        st.divider()
        if same_route:
            st.info("Kedua rute ini **sama persis** — di titik ini, rute terpendek "
                     "kebetulan juga paling hemat energi (medannya relatif landai/tidak "
                     "ada jalur alternatif). Coba titik lain yang melewati tanjakan curam "
                     "untuk melihat perbedaannya.")
        else:
            energy_saved_pct = (
                (stats_shortest["energy_J_per_kg"] - stats_energy["energy_J_per_kg"])
                / stats_shortest["energy_J_per_kg"] * 100
            )
            extra_distance_pct = (
                (stats_energy["distance_m"] - stats_shortest["distance_m"])
                / stats_shortest["distance_m"] * 100
            )
            st.success(
                f"Rute hemat energi menghemat **{energy_saved_pct:.1f}% energi** "
                f"dibanding rute terpendek, dengan menempuh jarak "
                f"**{extra_distance_pct:+.1f}%** dari jarak rute terpendek."
            )

        st.caption(f"Node dieksplorasi A* (tujuan energi): {expanded_energy} | "
                   f"(tujuan jarak): {expanded_shortest}")

        xs, ys = path_elevation_profile(G, path_energy)
        xs2, ys2 = path_elevation_profile(G, path_shortest)
        fig, ax = plt.subplots()
        ax.plot(xs, ys, color=COLOR_ENERGY, label="Hemat energi")
        ax.plot(xs2, ys2, color=COLOR_SHORTEST, linestyle="--", label="Terpendek")
        ax.set_xlabel("Jarak (m)")
        ax.set_ylabel("Elevasi (m)")
        ax.set_title("Profil elevasi: rute hemat energi vs terpendek")
        ax.legend()
        st.pyplot(fig)
