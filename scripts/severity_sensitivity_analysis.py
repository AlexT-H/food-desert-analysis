import geopandas as gpd
import pandas as pd
from pathlib import Path


# --------------------------------------------
# CONFIG
# --------------------------------------------

# Column names
BASE_COL = "food_desert_severity"
ACCESS_COL = "severity_access_heavy"
DEMO_COL = "severity_demo_heavy"
POP_COL = "allocated_population"

# Quantile threshold for "high severity"
HIGH_Q = 0.80  # top 20%


# --------------------------------------------
# PATHS
# --------------------------------------------

project_root = Path(__file__).resolve().parents[1]
data_dir = project_root / "data" / "processed"

in_path = data_dir / "food_desert_severity_model.geojson"

if not in_path.exists():
    raise FileNotFoundError(f"Missing file: {in_path}")

print("Working directory:", project_root)


# --------------------------------------------
# LOAD
# --------------------------------------------

bg = gpd.read_file(in_path)

required = [BASE_COL, ACCESS_COL, DEMO_COL, POP_COL]
missing = [c for c in required if c not in bg.columns]
if missing:
    raise ValueError(f"Missing required columns: {missing}")


# --------------------------------------------
# HIGH SEVERITY THRESHOLDS (CONSISTENT)
# --------------------------------------------

# Use BASE model to define threshold for all comparisons
threshold = bg[BASE_COL].quantile(HIGH_Q)

bg["high_base"] = bg[BASE_COL] > threshold
bg["high_access"] = bg[ACCESS_COL] > threshold
bg["high_demo"] = bg[DEMO_COL] > threshold


# --------------------------------------------
# STABILITY CLASSIFICATION
# --------------------------------------------

def classify(row):
    if row["high_base"] and row["high_access"] and row["high_demo"]:
        return "Stable High (All Models)"
    elif row["high_access"] and not row["high_demo"]:
        return "Access Driven"
    elif row["high_demo"] and not row["high_access"]:
        return "Demographic Driven"
    elif row["high_base"]:
        return "Base Only"
    else:
        return "Not High"

bg["stability_class"] = bg.apply(classify, axis=1)


# --------------------------------------------
# POPULATION IMPACT
# --------------------------------------------

pop_total = bg[POP_COL].sum()

pop_base = bg.loc[bg["high_base"], POP_COL].sum()
pop_access = bg.loc[bg["high_access"], POP_COL].sum()
pop_demo = bg.loc[bg["high_demo"], POP_COL].sum()

pop_stable = bg.loc[
    bg["high_base"] & bg["high_access"] & bg["high_demo"],
    POP_COL
].sum()


# --------------------------------------------
# JACCARD SIMILARITY (for assessing stability)
# --------------------------------------------

def jaccard(a, b):
    intersection = ((a == True) & (b == True)).sum()
    union = ((a == True) | (b == True)).sum()
    return intersection / union if union != 0 else 0

j_base_access = jaccard(bg["high_base"], bg["high_access"])
j_base_demo = jaccard(bg["high_base"], bg["high_demo"])
j_access_demo = jaccard(bg["high_access"], bg["high_demo"])


# --------------------------------------------
# SUMMARY TABLE
# --------------------------------------------

summary = pd.DataFrame({
    "metric": [
        "Total Population",
        "High Severity (Base)",
        "High Severity (Access)",
        "High Severity (Demographic)",
        "Stable High (All Models)"
    ],
    "population": [
        pop_total,
        pop_base,
        pop_access,
        pop_demo,
        pop_stable
    ]
})

agreement = pd.DataFrame({
    "comparison": [
        "Base vs Access",
        "Base vs Demographic",
        "Access vs Demographic"
    ],
    "jaccard_score": [
        j_base_access,
        j_base_demo,
        j_access_demo
    ]
})


# --------------------------------------------
# PRINT RESULTS
# --------------------------------------------

print("\n====================================")
print("SEVERITY MODEL COMPARISON SUMMARY")
print("====================================")

print("\nPopulation Impact:")
print(summary)

print("\nAgreement (Jaccard Scores):")
print(agreement)

print("\nStability Class Counts:")
print(bg["stability_class"].value_counts())


# --------------------------------------------
# EXPORT
# --------------------------------------------

data_dir.mkdir(parents=True, exist_ok=True)

geo_out = data_dir / "severity_stability_analysis.geojson"
csv_summary_out = data_dir / "severity_population_summary.csv"
csv_agreement_out = data_dir / "severity_agreement_scores.csv"

bg.to_file(geo_out, driver="GeoJSON")
summary.to_csv(csv_summary_out, index=False)
agreement.to_csv(csv_agreement_out, index=False)

print("\nOutputs saved:")
print(geo_out)
print(csv_summary_out)
print(csv_agreement_out)