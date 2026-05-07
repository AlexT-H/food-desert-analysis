import json
import geopandas as gpd
import pandas as pd
from shapely.validation import make_valid
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

# Project root = one folder above /scripts
BASE_DIR = Path(__file__).resolve().parent.parent

INPUT_FILES = {
    "severity_model": BASE_DIR / "data/processed/food_desert_severity_model.geojson",
    "stability": BASE_DIR / "data/processed/severity_stability_analysis.geojson",
    "tracts": BASE_DIR / "data/processed/stl_tracts.geojson",
    "stores": BASE_DIR / "data/processed/stores_cleaned.geojson",
    "walk_iso": BASE_DIR / "data/processed/walk_isochrones.geojson",
    "drive_iso": BASE_DIR / "data/processed/drive_isochrones.geojson",
    "edges": BASE_DIR / "data/processed/network_edges.geojson",
}

OUTPUT_DIR = BASE_DIR / "data/web_ready"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# SETTINGS
# ============================================================

# General simplification tolerance after reprojection to EPSG:4326.
# Higher = smaller file but rougher shapes.
SIMPLIFY_TOLERANCE = 0.001

# Square meters per square mile
SQ_METERS_PER_SQ_MILE = 2_589_988.110336

# Numeric display precision for web-facing values
NUMERIC_DECIMALS = 3


# ============================================================
# FIELD SCHEMA
# ============================================================

CORE_FIELDS = {
    "severity_model": [
        # Classification / threshold fields
        "block_group_number",
        "severity_classification",
        "access_severity",

        # Quantile model fields
        "food_desert_severity",
        "severity_access_heavy",
        "severity_demo_heavy",
        "access_score",

        # Demographic / explanatory fields
        "allocated_population",
        "total_population",
        "norm_poverty",
        "norm_no_vehicle",

        # Area field
        "bg_area",

        # Network accessibility fields
        "walk_time_min",
        "drive_time_min",

        # Sensitivity/stability field, if present in this layer
        "stability_class",
    ],

    "stability": [
        "stability_class",
        "high_base",
        "high_access",
        "high_demo",
    ],

    "tracts": [
        "total_population",
        "norm_poverty",
        "norm_no_vehicle",
    ],

    # Keeps useful display fields if they exist.
    "stores": [
        "name",
        "store_name",
        "standardized_name",
        "brand",
        "store_type",
        "shop",
        "address",
        "full_address",
    ],

    # Isochrones may have different time-field names depending on script.
    "walk_iso": [
        "time",
        "minutes",
        "contour",
        "mode",
    ],

    "drive_iso": [
        "time",
        "minutes",
        "contour",
        "mode",
    ],

    "edges": [
        "highway",
        "length",
        "travel_time",
        "mode",
    ],
}


# ============================================================
# HELPERS
# ============================================================

def print_header(message):
    print("\n" + "=" * 60)
    print(message)
    print("=" * 60)

# Fix invalid geometries and remove null/broken geometries.
def fix_geometries(gdf):

    def safe_fix(geom):
        try:
            if geom is None:
                return None

            if geom.is_valid:
                return geom

            return make_valid(geom)

        except Exception:
            return None

    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].apply(safe_fix)
    gdf = gdf[gdf["geometry"].notnull()]

    return gdf

def reproject_to_web(gdf):

    if gdf.crs is None:
        print("WARNING: Layer has no CRS. Assuming EPSG:4326.")
        gdf = gdf.set_crs(epsg=4326)

    return gdf.to_crs(epsg=4326)


def simplify_geometries(gdf, layer_key):

    layers_to_simplify = {
        "walk_iso",
        "drive_iso",
        "edges",
    }

    if layer_key not in layers_to_simplify:
        print(f"Skipping simplification for {layer_key}.")
        return gdf

    print(f"Simplifying geometries for {layer_key}...")

    gdf = gdf.copy()
    gdf["geometry"] = gdf["geometry"].simplify(
        SIMPLIFY_TOLERANCE,
        preserve_topology=True
    )

    return gdf

# Keep only web-relevant fields plus geometry.
def filter_fields(gdf, layer_key):

    allowed_fields = CORE_FIELDS.get(layer_key)

    if not allowed_fields:
        return gdf

    existing_fields = [field for field in allowed_fields if field in gdf.columns]

    missing_fields = [field for field in allowed_fields if field not in gdf.columns]
    if missing_fields:
        print(f"Fields not found in {layer_key}, skipping: {missing_fields}")

    return gdf[existing_fields + ["geometry"]]


def convert_bg_area_to_square_miles(gdf):

    if "bg_area" not in gdf.columns:
        return gdf

    gdf = gdf.copy()

    gdf["bg_area"] = pd.to_numeric(gdf["bg_area"], errors="coerce")

    gdf["bg_area_sq_mi"] = gdf["bg_area"] / SQ_METERS_PER_SQ_MILE

    # Keep bg_area for compatibility with current App.jsx,
    # but make it square miles now.
    gdf["bg_area"] = gdf["bg_area_sq_mi"]

    return gdf


def clean_and_round_fields(gdf):

    gdf = gdf.copy()

    # Convert likely numeric fields to numeric if present
    likely_numeric_fields = [
        "food_desert_severity",
        "severity_access_heavy",
        "severity_demo_heavy",
        "access_score",
        "allocated_population",
        "total_population",
        "norm_poverty",
        "norm_no_vehicle",
        "bg_area",
        "bg_area_sq_mi",
        "walk_time_min",
        "drive_time_min",
        "length",
        "travel_time",
        "time",
        "minutes",
        "contour",
    ]

    for field in likely_numeric_fields:
        if field in gdf.columns:
            gdf[field] = pd.to_numeric(gdf[field], errors="coerce")

    # Clamp normalized / quantile fields to 0–1
    normalized_fields = [
        "food_desert_severity",
        "severity_access_heavy",
        "severity_demo_heavy",
        "norm_poverty",
        "norm_no_vehicle",
    ]

    for field in normalized_fields:
        if field in gdf.columns:
            gdf[field] = gdf[field].clip(0, 1)

    # Round population fields to whole integers
    integer_fields = [
        "allocated_population",
        "total_population",
    ]

    for field in integer_fields:
        if field in gdf.columns:
            gdf[field] = gdf[field].round(0).astype("Int64")

    # Round all other numeric columns to 3 decimals
    numeric_columns = gdf.select_dtypes(include=["number", "Float64", "float64", "float32"]).columns

    for field in numeric_columns:
        if field not in integer_fields:
            gdf[field] = gdf[field].round(NUMERIC_DECIMALS)

    return gdf


def export_geojson(gdf, layer_key):

    output_path = OUTPUT_DIR / f"{layer_key}.geojson"

    gdf.to_file(output_path, driver="GeoJSON")

    print(f"Exported: {output_path}")
    print(f"Feature count: {len(gdf)}")
    print(f"Fields: {list(gdf.columns)}")


# Adds web-ids to identify Block Groups
def add_web_ids(gdf, layer_key):

    gdf = gdf.copy()

    if layer_key == "severity_model":
        gdf["block_group_number"] = range(1, len(gdf) + 1)

    return gdf


def merge_stability_into_severity(severity_gdf, stability_path):

    if "stability_class" in severity_gdf.columns and severity_gdf["stability_class"].notna().any():
        print("severity_model already has stability_class. Skipping merge.")
        return severity_gdf

    if not stability_path.exists():
        print("WARNING: stability file missing. Cannot merge stability_class.")
        return severity_gdf

    print("Merging stability_class into severity_model...")

    stability_gdf = gpd.read_file(str(stability_path))

    if "stability_class" not in stability_gdf.columns:
        print("WARNING: stability_class not found in stability layer.")
        return severity_gdf

    # Fix geometry before joining
    severity_gdf = fix_geometries(severity_gdf)
    stability_gdf = fix_geometries(stability_gdf)

    # Make sure both layers have CRS
    if severity_gdf.crs is None:
        print("WARNING: severity_model has no CRS. Assuming EPSG:4326.")
        severity_gdf = severity_gdf.set_crs(epsg=4326)

    if stability_gdf.crs is None:
        print("WARNING: stability layer has no CRS. Assuming EPSG:4326.")
        stability_gdf = stability_gdf.set_crs(epsg=4326)

    join_crs = "EPSG:4326"

    severity_projected = severity_gdf.to_crs(join_crs).copy()
    stability_projected = stability_gdf.to_crs(join_crs).copy()

    # Preserve original row identity
    severity_projected["__severity_index"] = severity_projected.index

    # representative_point stays inside polygon, better than centroid for irregular polygons
    severity_points = severity_projected.copy()
    severity_points["geometry"] = severity_points.geometry.representative_point()

    # Spatial join: each block group point gets the stability polygon it falls within
    joined = gpd.sjoin(
        severity_points[["__severity_index", "geometry"]],
        stability_projected[["stability_class", "geometry"]],
        how="left",
        predicate="within"
    )

    # Collapse duplicate matches if any occur.
    # This guarantees one stability_class value per severity feature.
    stability_by_index = (
        joined
        .dropna(subset=["stability_class"])
        .drop_duplicates(subset="__severity_index")
        .set_index("__severity_index")["stability_class"]
    )

    severity_gdf = severity_gdf.copy()
    severity_gdf["stability_class"] = severity_gdf.index.map(stability_by_index)

    missing_count = severity_gdf["stability_class"].isna().sum()
    print(f"stability_class merged. Missing values: {missing_count}")

    return severity_gdf


def process_layer(layer_key, input_path):

    print_header(f"Processing layer: {layer_key}")

    print(f"Looking for file at: {input_path}")
    print(f"Exists: {input_path.exists()}")

    if not input_path.exists():
        print(f"WARNING: Missing file for {layer_key}. Skipping.")
        return None

    gdf = gpd.read_file(str(input_path))

    print(f"Original feature count: {len(gdf)}")
    print(f"Original CRS: {gdf.crs}")

    gdf = fix_geometries(gdf)

    if layer_key == "severity_model":
        gdf = merge_stability_into_severity(gdf, INPUT_FILES["stability"])

    gdf = reproject_to_web(gdf)
    gdf = simplify_geometries(gdf, layer_key)
    gdf = filter_fields(gdf, layer_key)
    gdf = add_web_ids(gdf, layer_key)

    # Convert area only after field filtering, if bg_area exists
    gdf = convert_bg_area_to_square_miles(gdf)

    # Clean and round final web-facing values
    gdf = clean_and_round_fields(gdf)

    export_geojson(gdf, layer_key)

    return gdf


def write_metadata(processed_layers):

    metadata = {
        "description": "Web-ready GeoJSON outputs for the St. Louis food access severity application.",
        "crs": "EPSG:4326",
        "simplification_tolerance": SIMPLIFY_TOLERANCE,
        "numeric_precision_decimals": NUMERIC_DECIMALS,
        "area_units": {
            "bg_area": "square miles",
            "bg_area_sq_mi": "square miles",
            "conversion_note": "Original bg_area assumed to be square meters and converted using 2,589,988.110336 square meters per square mile."
        },
        "layers": {}
    }

    for layer_key, gdf in processed_layers.items():
        if gdf is None:
            metadata["layers"][layer_key] = {
                "status": "missing_or_skipped"
            }
        else:
            metadata["layers"][layer_key] = {
                "status": "processed",
                "feature_count": int(len(gdf)),
                "fields": list(gdf.columns),
            }

    metadata_path = OUTPUT_DIR / "metadata.json"

    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    print_header("Metadata written")
    print(metadata_path)


def main():
    print_header("Preparing web-ready GIS data")

    processed_layers = {}

    for layer_key, input_path in INPUT_FILES.items():
        processed_layers[layer_key] = process_layer(layer_key, input_path)

    write_metadata(processed_layers)

    print_header("Pipeline complete")
    print(f"Web-ready files saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()