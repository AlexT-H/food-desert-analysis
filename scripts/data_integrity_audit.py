import geopandas as gpd
from pathlib import Path

# --------------------------------------------
# PATHS
# --------------------------------------------

project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "data" / "processed"

severity_path = data_dir / "food_desert_severity_model.geojson"

print("Working directory:", project_root)


# --------------------------------------------
# LOAD DATA
# --------------------------------------------

bg = gpd.read_file(severity_path)

print("\n====================================")
print("BASIC INFO")
print("====================================")

print(f"Total block groups: {len(bg)}")
print("Columns:", list(bg.columns))


# --------------------------------------------
# TOTAL POPULATION CHECK
# --------------------------------------------

print("\n====================================")
print("TOTAL POPULATION CHECK")
print("====================================")

total_pop = bg["allocated_population"].sum()
print(f"Total allocated population: {total_pop:,.0f}")


# --------------------------------------------
# ZERO / MISSING POPULATION
# --------------------------------------------

print("\n====================================")
print("ZERO / LOW POPULATION CHECK")
print("====================================")

zero_pop = (bg["allocated_population"] == 0).sum()
low_pop = (bg["allocated_population"] < 50).sum()

print(f"Block groups with 0 population: {zero_pop}")
print(f"Block groups with <50 population: {low_pop}")


# --------------------------------------------
# AREA CHECK
# --------------------------------------------

print("\n====================================")
print("AREA CHECK")
print("====================================")

# Reproject properly for area
bg_proj = bg.to_crs(epsg=26915)

bg_proj["area_km2"] = bg_proj.geometry.area / 1_000_000

print(bg_proj["area_km2"].describe())


# --------------------------------------------
# POPULATION DENSITY CHECK
# --------------------------------------------

print("\n====================================")
print("POPULATION DENSITY CHECK")
print("====================================")

bg_proj["pop_density"] = bg_proj["allocated_population"] / bg_proj["area_km2"]

print(bg_proj["pop_density"].describe())


# --------------------------------------------
# EXTREME VALUES CHECK
# --------------------------------------------

print("\n====================================")
print("EXTREME VALUES CHECK")
print("====================================")

print("Top 5 densities:")
print(bg_proj.nlargest(5, "pop_density")[["allocated_population", "area_km2", "pop_density"]])

print("\nLowest 5 densities:")
print(bg_proj.nsmallest(5, "pop_density")[["allocated_population", "area_km2", "pop_density"]])


# --------------------------------------------
# OPTIONAL: EXPORT DEBUG FILE
# --------------------------------------------

debug_out = data_dir / "debug_density_check.geojson"
bg_proj.to_file(debug_out, driver="GeoJSON")

print("\nDebug file saved:", debug_out)