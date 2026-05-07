from pathlib import Path
import geopandas as gpd
import osmnx as ox
import networkx as nx
from shapely.ops import unary_union
import time

# =========================
# PATHS
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

INPUT_STORES = PROCESSED_DIR / "stores_ready.geojson"
INPUT_BLOCK_GROUPS = PROCESSED_DIR / "stl_block_groups.geojson"

OUTPUT_ACCESS = PROCESSED_DIR / "block_group_access_scores.geojson"
OUTPUT_WALK_ISO = PROCESSED_DIR / "walk_isochrones.geojson"
OUTPUT_DRIVE_ISO = PROCESSED_DIR / "drive_isochrones.geojson"

DRIVE_GRAPH_CACHE = PROCESSED_DIR / "stl_drive_network.graphml"
WALK_GRAPH_CACHE = PROCESSED_DIR / "stl_walk_network.graphml"

WALK_SPEED_MPS = 1.4


# =========================
# STUDY AREA
# =========================

def build_study_area():
    print("Loading study area polygons...")

    city = ox.geocode_to_gdf("St. Louis, Missouri, USA")
    county = ox.geocode_to_gdf("St. Louis County, Missouri, USA")

    return unary_union([
        city.geometry.iloc[0],
        county.geometry.iloc[0]
    ])


# =========================
# NETWORKS
# =========================

def build_networks(study_area):
    if DRIVE_GRAPH_CACHE.exists() and WALK_GRAPH_CACHE.exists():
        print("Loading cached networks...")
        G_drive = ox.load_graphml(DRIVE_GRAPH_CACHE)
        G_walk = ox.load_graphml(WALK_GRAPH_CACHE)
        return G_drive, G_walk

    print("Building drive network...")
    G_drive = ox.graph_from_polygon(
        study_area,
        network_type="drive"
    )

    print("Building walk network...")
    G_walk = ox.graph_from_polygon(
        study_area,
        network_type="walk"
    )

    print("Adding drive travel times...")
    G_drive = ox.routing.add_edge_speeds(G_drive)
    G_drive = ox.routing.add_edge_travel_times(G_drive)

    print("Adding walk travel times...")
    for _, _, _, data in G_walk.edges(keys=True, data=True):
        data["travel_time"] = data["length"] / WALK_SPEED_MPS

    print("Saving cached networks...")
    ox.save_graphml(G_drive, DRIVE_GRAPH_CACHE)
    ox.save_graphml(G_walk, WALK_GRAPH_CACHE)

    return G_drive, G_walk


# =========================
# LOAD DATA
# =========================

def load_data():
    print("Loading stores and block groups...")

    stores = gpd.read_file(INPUT_STORES).to_crs(epsg=4326)
    blocks = gpd.read_file(INPUT_BLOCK_GROUPS).to_crs(epsg=4326)

    return stores, blocks


# =========================
# SNAP TO NETWORK
# =========================

def snap_stores(stores, G_drive, G_walk):
    print("Snapping stores...")

    stores["drive_node"] = stores.geometry.apply(
        lambda g: ox.distance.nearest_nodes(
            G_drive, g.x, g.y
        )
    )

    stores["walk_node"] = stores.geometry.apply(
        lambda g: ox.distance.nearest_nodes(
            G_walk, g.x, g.y
        )
    )

    return stores


def snap_block_groups(blocks, G_drive, G_walk):
    print("Creating block group centroids...")

    # project to metric CRS for accurate centroids
    blocks_proj = blocks.to_crs(epsg=3857)
    blocks_proj["centroid_geom"] = blocks_proj.geometry.centroid

    # convert centroids back to WGS84
    centroids = gpd.GeoSeries(
        blocks_proj["centroid_geom"],
        crs="EPSG:3857"
    ).to_crs(epsg=4326)

    blocks["centroid_geom"] = centroids

    print("Snapping block groups (vectorized)...")

    # vectorized x/y extraction
    x_coords = blocks["centroid_geom"].x.values
    y_coords = blocks["centroid_geom"].y.values

    # more optimal than .apply()
    blocks["drive_node"] = ox.distance.nearest_nodes(
        G_drive,
        x_coords,
        y_coords
    )

    blocks["walk_node"] = ox.distance.nearest_nodes(
        G_walk,
        x_coords,
        y_coords
    )

    return blocks


# =========================
# FAST ACCESS CALCULATION
# =========================

def calculate_fast_access(blocks, stores, G_walk, G_drive):
    print("Running fast multi-source Dijkstra...")

    walk_sources = stores["walk_node"].tolist()
    drive_sources = stores["drive_node"].tolist()

    walk_times = nx.multi_source_dijkstra_path_length(
        G_walk,
        walk_sources,
        weight="travel_time"
    )

    drive_times = nx.multi_source_dijkstra_path_length(
        G_drive,
        drive_sources,
        weight="travel_time"
    )

    blocks["walk_time_min"] = blocks["walk_node"].map(
        lambda n: walk_times.get(n, None) / 60
        if n in walk_times else None
    )

    blocks["drive_time_min"] = blocks["drive_node"].map(
        lambda n: drive_times.get(n, None) / 60
        if n in drive_times else None
    )

    def score(row):
        walk = row["walk_time_min"]
        drive = row["drive_time_min"]

        if walk is not None and walk <= 10:
            return 5
        elif walk is not None and walk <= 20:
            return 4
        elif drive is not None and drive <= 10:
            return 3
        elif drive is not None and drive <= 20:
            return 2
        return 1

    blocks["access_score"] = blocks.apply(score, axis=1)

    return blocks


# =========================
# ISOCHRONES
# =========================

def make_isochrones(stores, graph, node_col, minutes):
    polygons = []

    for node in stores[node_col]:
        try:
            subgraph = nx.ego_graph(
                graph,
                node,
                radius=minutes * 60,
                distance="travel_time"
            )

            if len(subgraph.edges) == 0:
                continue

            nodes, _ = ox.graph_to_gdfs(subgraph)

            if nodes.empty:
                continue

            polygons.append(nodes.union_all().convex_hull)

        except Exception as e:
            print(f"Skipping node {node}: {e}")
            continue

    return polygons


# =========================
# MAIN
# =========================

def main():

    start = time.time()
    print("START")


    study_area = build_study_area()
    print(f"study area finished: {time.time() - start:1f}")

    G_drive, G_walk = build_networks(study_area)
    print(f"drive and walk networks finished: {time.time() - start:1f}")

    stores, blocks = load_data()
    print(f"stores and blocks loaded: {time.time() - start:1f}")

    print(blocks.columns)

    stores = snap_stores(stores, G_drive, G_walk)
    print(f"store snaps finished: {time.time() - start:1f}")
    blocks = snap_block_groups(blocks, G_drive, G_walk)
    print(f"block snaps finished: {time.time() - start:1f}")

    blocks = calculate_fast_access(
        blocks,
        stores,
        G_walk,
        G_drive
    )

    print("Saving access scores...", time.time()-start)
    blocks_output = blocks.drop(columns=["centroid_geom"])
    blocks_output.to_file(OUTPUT_ACCESS, driver="GeoJSON")

    print("Saving isochrones...", time.time()-start)
    walk_iso = gpd.GeoDataFrame(
        geometry=make_isochrones(stores, G_walk, "walk_node", 10),
        crs="EPSG:4326"
    )

    drive_iso = gpd.GeoDataFrame(
        geometry=make_isochrones(stores, G_drive, "drive_node", 15),
        crs="EPSG:4326"
    )

    walk_iso.to_file(OUTPUT_WALK_ISO, driver="GeoJSON")
    drive_iso.to_file(OUTPUT_DRIVE_ISO, driver="GeoJSON")

    print("ACCESSIBILITY ANALYSIS COMPLETE")
    print("Time:", time.time()-start)


if __name__ == "__main__":
    main()