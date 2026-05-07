import osmnx as ox
import geopandas as gpd
from pathlib import Path


# -----------------------------------
# Project paths
# -----------------------------------

project_root = Path(__file__).resolve().parents[1]

boundary_path = project_root / "data/processed/stl_boundary.geojson"
output_graph = project_root / "data/raw/network/stl_network.graphml"

# Ensure output folder exists
output_graph.parent.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# Load study area
# -----------------------------------

boundary = gpd.read_file(boundary_path)

# OSM requires lat/lon
boundary = boundary.to_crs(epsg=4326)

# Merge geometry into one polygon
study_area = boundary.unary_union

print("Boundary loaded.")

# -----------------------------------
# Configure OSMnx
# -----------------------------------

ox.settings.use_cache = True
ox.settings.log_console = True
ox.settings.timeout = 180


# -----------------------------------
# Download road network
# -----------------------------------

print("Downloading road network...")

G = ox.graph_from_polygon(
    study_area,
    network_type="drive"
)

print("Network downloaded.")

# -----------------------------------
# Save graph
# -----------------------------------

ox.save_graphml(G, output_graph)

print("Saved network to:", output_graph)
