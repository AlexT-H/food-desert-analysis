import geopandas as gpd
import pandas as pd
import numpy as np
from pathlib import Path


# --------------------------------------------
# PROJECT PATH SETUP
# --------------------------------------------


PROJECT_ROOT = Path(__file__).resolve().parents[1]

data_dir = PROJECT_ROOT / "data" / "processed"
data_dir.mkdir(parents=True, exist_ok=True)

bg_path = data_dir / "block_group_access_scores.geojson"
tract_path = data_dir / "stl_tracts_with_data.geojson"

output_geojson = data_dir / "food_desert_severity_model.geojson"
output_csv = data_dir / "food_desert_summary.csv"

print("Working directory:", PROJECT_ROOT)


# --------------------------------------------
# LOAD DATA
# --------------------------------------------

bg = gpd.read_file(bg_path)
tracts = gpd.read_file(tract_path)

# Ensure CRS match
bg = bg.to_crs(tracts.crs)


# --------------------------------------------
# SPATIAL JOIN (TRACT -> BLOCK GROUP)
# --------------------------------------------

bg = gpd.sjoin(
    bg,
    tracts[[
        "GEOID",
        "total_population",
        "norm_no_vehicle",
        "norm_poverty",
        "geometry"
    ]],
    how="left",
    predicate="intersects"
)

# Join clean up
bg = bg.drop(columns=["index_right"], errors="ignore")
bg = bg.rename(columns={"GEOID_right": "TRACT_GEOID"})


# --------------------------------------------
# ACCESS SEVERITY (INVERT ACCESS SCORE)
# --------------------------------------------

bg["access_severity"] = 6 - bg["access_score"]

bg["access_severity_norm"] = (
    bg["access_severity"] - bg["access_severity"].min()
) / (
    bg["access_severity"].max() - bg["access_severity"].min()
)


# --------------------------------------------
# DEMOGRAPHIC VULNERABILITY INDEX
# --------------------------------------------

bg["demo_vulnerability"] = (
    bg["norm_no_vehicle"] +
    bg["norm_poverty"]
) / 2


# --------------------------------------------
# FOOD DESERT SEVERITY MODEL (BASELINE)
# --------------------------------------------

bg["food_desert_severity"] = (
    0.5 * bg["access_severity_norm"] +
    0.5 * bg["demo_vulnerability"]
)


# --------------------------------------------
# THRESHOLD-BASED CLASSIFICATION (7 CLASSES)
# --------------------------------------------

bins = [
    0.0,
    0.2,
    0.35,
    0.5,
    0.65,
    0.8,
    0.9,
    1.0
]

labels = [
    "Minimal",
    "Very Low",
    "Low",
    "Moderate",
    "High",
    "Very High",
    "Extreme"
]

bg["severity_classification"] = pd.cut(
    bg["food_desert_severity"],
    bins=bins,
    labels=labels,
    include_lowest=True
)


# --------------------------------------------
# POPULATION CALCULATION
# --------------------------------------------

# Reproject to projected CRS for accurate area
bg = bg.to_crs(epsg=3857)

# Calculate block group area
bg["bg_area"] = bg.geometry.area

# Sum area per tract
bg["tract_area"] = bg.groupby("TRACT_GEOID")["bg_area"].transform("sum")

# Allocate tract population proportionally
bg["allocated_population"] = (
    bg["total_population"] * (bg["bg_area"] / bg["tract_area"])
)


# --------------------------------------------
# POPULATION IMPACT ANALYSIS
# --------------------------------------------

high_risk = bg[
    bg["severity_classification"].isin(["High", "Very High", "Extreme"])
]

affected_population = high_risk["allocated_population"].sum()

print("====================================")
print("FOOD DESERT IMPACT SUMMARY")
print("====================================")
print(f"Total affected population: {int(affected_population):,}")


# --------------------------------------------
# SENSITIVITY TESTING
# --------------------------------------------

bg["severity_access_heavy"] = (
    0.7 * bg["access_severity_norm"] +
    0.3 * bg["demo_vulnerability"]
)

bg["severity_demo_heavy"] = (
    0.3 * bg["access_severity_norm"] +
    0.7 * bg["demo_vulnerability"]
)


# --------------------------------------------
# EXPORT OUTPUTS
# --------------------------------------------

# Convert back to WGS84 for GeoJSON compatibility
bg = bg.to_crs(epsg=4326)

bg.to_file(output_geojson, driver="GeoJSON")

summary = bg[[
    "food_desert_severity",
    "severity_classification",
    "allocated_population"
]]

summary.to_csv(output_csv, index=False)

print("Outputs successfully saved:")
print(output_geojson)
print(output_csv)