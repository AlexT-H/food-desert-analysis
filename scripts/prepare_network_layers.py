import osmnx as ox
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]

graph_path = project_root / "data/raw/network/stl_network.graphml"
nodes_path = project_root / "data/processed/network_nodes.geojson"
edges_path = project_root / "data/processed/network_edges.geojson"

# Load graph
G = ox.load_graphml(graph_path)

# Convert to GeoDataFrames
nodes, edges = ox.graph_to_gdfs(G)

# Save
nodes.to_file(nodes_path, driver="GeoJSON")
edges.to_file(edges_path, driver="GeoJSON")

print("Saved nodes and edges.")