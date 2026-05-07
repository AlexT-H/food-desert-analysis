import geopandas as gpd
import osmnx as ox
from pathlib import Path
from rapidfuzz import process, fuzz

# -----------------------------------
# PATH SETUP
# -----------------------------------
project_root = Path(__file__).resolve().parents[1]

input_path = project_root / "data/raw/stores/osm_stores.geojson"
graph_path = project_root / "data/raw/network/stl_network.graphml"
output_path = project_root / "data/processed/stores_ready.geojson"

output_path.parent.mkdir(parents=True, exist_ok=True)

# -----------------------------------
# LOAD DATA
# -----------------------------------
stores = gpd.read_file(input_path)
print(f"Initial store count: {len(stores)}")

# -----------------------------------
# CLEAN STORE DATA
# -----------------------------------

# Remove null geometries
stores = stores[stores.geometry.notnull()]

# Keep only points
stores = stores[stores.geometry.type == "Point"]

# Remove duplicate locations
stores["coords"] = stores.geometry.apply(lambda p: (round(p.x, 5), round(p.y, 5)))
stores = stores.drop_duplicates(subset=["coords"])
stores = stores.drop(columns=["coords"])

# Filter valid store types
valid_types = ["supermarket", "grocery", "convenience"]
stores = stores[stores["shop"].isin(valid_types)]

# Clean names
stores["name"] = stores["name"].fillna("Unknown Store")
stores = stores[stores["name"].str.len() > 2]

# Normalize name for matching
stores["name_clean"] = stores["name"].str.lower().str.strip()

stores = stores.reset_index(drop=True)

print(f"After cleaning: {len(stores)} stores")

# -----------------------------------
# BRAND STANDARDIZATION (FUZZY)
# -----------------------------------

# Known brands
known_brands = [
    "walmart",
    "aldi",
    "kroger",
    "target",
    "schnucks",
    "save a lot",
    "dollar general",
    "family dollar",
    "whole foods",
    "trader joe's"
]

def match_brand(name):
    # Try exact keyword match first
    for brand in known_brands:
        if brand in name:
            return brand.title()

    # Fuzzy match (handles misspellings)
    match, score, _ = process.extractOne(
        name,
        known_brands,
        scorer=fuzz.partial_ratio
    )

    # Only accept strong matches
    if score >= 85:
        return match.title()

    return "Independent"

stores["brand"] = stores["name_clean"].apply(match_brand)


# -----------------------------------
# ENRICH STORE DATA
# -----------------------------------

def classify_store(shop_type):
    if shop_type == "supermarket":
        return "large"
    elif shop_type == "grocery":
        return "medium"
    else:
        return "small"

    stores["store_size"] = stores["shop"].apply(classify_store)

    # Size weights
    size_weights = {
        "large": 1.0,
        "medium": 0.7,
        "small": 0.4
}

stores["size_weight"] = stores["store_size"].map(size_weights)

# Optional: brand weights
brand_weights = {
    "Walmart": 1.0,
    "Kroger": 1.0,
    "Aldi": 0.9,
    "Schnucks": 0.9,
    "Target": 0.8,
    "Save A Lot": 0.7,
    "Dollar General": 0.4,
    "Family Dollar": 0.4,
    "Whole Foods": 0.9,
    "Trader Joe'S": 0.9,
    "Independent": 0.6
}

stores["brand_weight"] = stores["brand"].map(brand_weights)

# Combine weights
stores["final_weight"] = (
    stores["size_weight"] * stores["brand_weight"]
)

# Add ID
stores["store_id"] = stores.index.astype(str)


# -----------------------------------
# NETWORK PREP
# -----------------------------------

# Ensure CRS
stores = stores.to_crs(epsg=4326)

# Load graph
print("Loading road network...")
G = ox.load_graphml(graph_path)

# Snap to nodes
print("Snapping stores to network nodes...")
stores["node"] = stores.geometry.apply(
    lambda point: ox.distance.nearest_nodes(G, point.x, point.y)
)


# -----------------------------------
# SAVE
# -----------------------------------
stores.to_file(output_path, driver="GeoJSON")

print("Stores ready for analysis.")
print(f"Final store count: {len(stores)}")
print(f"Saved to: {output_path}")