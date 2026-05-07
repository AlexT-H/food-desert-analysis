import geopandas as gpd
import pandas as pd
from pathlib import Path

project_root = Path(__file__).resolve().parents[1]

tracts_path = project_root / "data/processed/stl_tracts.geojson"
census_path = project_root / "data/raw/census/census_data.csv"

output_path = project_root / "data/processed/stl_tracts_with_data.geojson"

# Load
tracts = gpd.read_file(tracts_path)
census = pd.read_csv(census_path)


# -----------------------------
# FIX GEOID TYPES (IMPORTANT)
# -----------------------------
tracts["GEOID"] = tracts["GEOID"].astype(str)
census["GEOID"] = census["GEOID"].astype(str)

# Ensure 11-digit format
census["GEOID"] = census["GEOID"].str.zfill(11)


# -----------------------------
# Merge
# -----------------------------
merged = tracts.merge(census, on="GEOID", how="left")


# -----------------------------
# DERIVED METRICS
# -----------------------------

# Avoid division errors
merged["pct_no_vehicle"] = (
    merged["no_vehicle_households"] / merged["total_households"]
)

merged["poverty_rate"] = (
    merged["below_poverty"] / merged["poverty_universe"]
)

# population density (if area exists)
if "ALAND" in merged.columns:
    merged["area_km2"] = merged["ALAND"] / 1_000_000
    merged["pop_density"] = (
        merged["total_population"] / merged["area_km2"]
    )

def normalize(series):
    return (series - series.min()) / (series.max() - series.min())

merged["norm_no_vehicle"] = normalize(merged["pct_no_vehicle"])
merged["norm_poverty"] = normalize(merged["poverty_rate"])


# -----------------------------
# Clean values
# -----------------------------

merged.replace([float("inf"), -float("inf")], None, inplace=True)

merged["pct_no_vehicle"] = merged["pct_no_vehicle"].fillna(0)
merged["poverty_rate"] = merged["poverty_rate"].fillna(0)


# -----------------------------
# Save
# -----------------------------

merged.to_file(output_path, driver="GeoJSON")

print("Saved joined dataset with derived metrics.")
# Save
merged.to_file(output_path, driver="GeoJSON")

print("Saved joined dataset.")