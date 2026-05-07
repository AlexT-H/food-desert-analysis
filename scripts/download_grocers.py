import osmnx as ox
import geopandas as gpd
from pathlib import Path


# -----------------------------------
# Project paths
# -----------------------------------

project_root = Path(__file__).resolve().parents[1]

boundary_path = project_root / "data/processed/stl_boundary.geojson"
output_path = project_root / "data/raw/stores/osm_stores.geojson"


# -----------------------------------
# Load study area boundary
# -----------------------------------

boundary = gpd.read_file(boundary_path)

# Ensure it's in lat/lon (OSM requires EPSG:4326)
boundary = boundary.to_crs(epsg=4326)

# Convert to a single geometry (important)
study_area_geom = boundary.unary_union

print("Boundary loaded.")


# -----------------------------------
# Define OSM tags for food stores
# -----------------------------------

tags = {
    "shop": ["supermarket", "grocery", "convenience"]
}


# -----------------------------------
# Download data from OSM
# -----------------------------------

print("Downloading store data from OSM...")

stores = ox.features_from_polygon(study_area_geom, tags)

print("Downloaded features:", len(stores))

# -----------------------------------
# Keep only points (optional but recommended)
# -----------------------------------

stores = stores[stores.geometry.type.isin(["Point", "Polygon"])]

# Convert polygons to centroids (important)
stores["geometry"] = stores.geometry.centroid


# -----------------------------------
# Clean fields
# -----------------------------------

keep_cols = ["name", "shop", "geometry"]
stores = stores[[col for col in keep_cols if col in stores.columns]]


# -----------------------------------
# Save output
# -----------------------------------

stores.to_file(output_path, driver="GeoJSON")

print("Saved to:", output_path)