import geopandas as gpd
from pathlib import Path


# -----------------------------------
# Project paths
# -----------------------------------

project_root = Path(__file__).resolve().parents[1]

tract_path = project_root / "data/raw/census/tracts/tl_2025_29_tract.shp"
bg_path = project_root / "data/raw/census/block_groups/tl_2025_29_bg.shp"
county_path = project_root / "data/raw/census/county_boundary/tl_2025_us_county.shp"

output_dir = project_root / "data/processed"
output_dir.mkdir(parents=True, exist_ok=True)


# -----------------------------------
# Load layers
# -----------------------------------

tracts = gpd.read_file(tract_path)
block_groups = gpd.read_file(bg_path)
counties = gpd.read_file(county_path)

print("Loaded tracts:", len(tracts))
print("Loaded block groups:", len(block_groups))
print("Loaded counties:", len(counties))


# -----------------------------------
# St. Louis County + City FIPS
# -----------------------------------

study_county_codes = ["189", "510"]


# -----------------------------------
# Filter tracts
# -----------------------------------

stl_tracts = tracts[
    tracts["COUNTYFP"].astype(str).str.zfill(3).isin(study_county_codes)
].copy()


# -----------------------------------
# Filter block groups
# -----------------------------------

stl_block_groups = block_groups[
    block_groups["COUNTYFP"].astype(str).str.zfill(3).isin(study_county_codes)
].copy()

# ---------------------
# --------------
# Filter county + city boundaries
# -----------------------------------

stl_boundary = counties[
    (counties["STATEFP"] == "29") &
    (counties["COUNTYFP"].astype(str).str.zfill(3).isin(study_county_codes))
].copy()


# -----------------------------------
# Save outputs
# -----------------------------------

stl_tracts.to_file(
    output_dir / "stl_tracts.geojson",
    driver="GeoJSON"
)

stl_block_groups.to_file(
    output_dir / "stl_block_groups.geojson",
    driver="GeoJSON"
)

stl_boundary.to_file(
    output_dir / "stl_boundary.geojson",
    driver="GeoJSON"
)

print("Saved processed study area files successfully.")