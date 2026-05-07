from census import Census
import pandas as pd
from pathlib import Path

# -----------------------------------
# CONFIG
# -----------------------------------
API_KEY = "4dcb25f222521677786e4f07ff898848cb29960c"

c = Census(API_KEY)

project_root = Path(__file__).resolve().parents[1]
output_path = project_root / "data/raw/census/census_data.csv"

# Missouri FIPS
STATE_FIPS = "29"

# St. Louis County + City
COUNTIES = ["189", "510"]


# -----------------------------------
# VARIABLES
# -----------------------------------
variables = [
    "B01003_001E",  # total population
    "B19013_001E",  # median income
    "B08201_001E",  # total households
    "B08201_002E",  # no vehicle
    "B17001_001E",  # total poverty universe
    "B17001_002E"   # below poverty
]


# -----------------------------------
# DOWNLOAD DATA
# -----------------------------------
all_data = []

for county in COUNTIES:
    print(f"Downloading county {county}...")

    data = c.acs5.state_county_tract(
        variables,
        STATE_FIPS,
        county,
        Census.ALL
    )

    df = pd.DataFrame(data)
    all_data.append(df)

# Combine counties
df = pd.concat(all_data, ignore_index=True)


# -----------------------------------
# CREATE GEOID
# -----------------------------------
df["GEOID"] = (
    df["state"] +
    df["county"] +
    df["tract"]
)


# -----------------------------------
# Rename columns
# -----------------------------------

df = df.rename(columns={
    "B01003_001E": "total_population",
    "B19013_001E": "median_income",
    "B08201_001E": "total_households",
    "B08201_002E": "no_vehicle_households",
    "B17001_001E": "poverty_universe",
    "B17001_002E": "below_poverty"
})


# -----------------------------------
# Save
# -----------------------------------

df.to_csv(output_path, index=False)

print("Saved census data to:", output_path)