# Data Sources

## Project

**St. Louis Food Desert Severity Web GIS**

This document summarizes the main datasets used to build the food desert severity model and web GIS application.

Because the project relies mostly on national Census data and OpenStreetMap data, the same source structure can be reused for other U.S. study areas with updated geography parameters.

---

## Source Summary

| Source | Data Type | Project Use |
|---|---|---|
| U.S. Census TIGER/Line | Boundary geometries | Study area, tracts, block groups |
| American Community Survey | Demographic data | Poverty, population, vehicle access |
| OpenStreetMap | Grocery store features | Food retailer destinations |
| OpenStreetMap / OSMnx | Road network | Network travel-time analysis |
| Project-derived outputs | Modeled GIS layers | Accessibility, severity, stability, web map data |

---

# 1. Census Boundary Data

## Source

U.S. Census Bureau TIGER/Line shapefiles.

## Data Used

- county boundaries
- census tracts
- census block groups

## Study Area

The study area includes:

- St. Louis City, Missouri
- St. Louis County, Missouri

These were selected using county FIPS codes:

| Area | FIPS Code |
|---|---:|
| St. Louis County | `189` |
| St. Louis City | `510` |

## Project Use

Census boundary data was used to define the study area and create the main spatial units for analysis. Tracts were used for demographic joins, while block groups were used as the primary unit for accessibility and severity modeling.

## Main Outputs

- `data/processed/stl_boundary.geojson`
- `data/processed/stl_tracts.geojson`
- `data/processed/stl_block_groups.geojson`

## Notes

Census boundaries are useful for standardized analysis, but they do not always match lived neighborhood boundaries. Tracts and block groups can also hide variation within each polygon.

---

# 2. ACS Demographic Data

## Source

U.S. Census Bureau American Community Survey.

## Data Used

The project downloaded ACS tract-level variables related to:

- total population
- median income
- total households
- households without vehicle access
- poverty universe
- population below poverty level

## Derived Fields

The project calculated:

- poverty rate
- no-vehicle household rate
- normalized poverty
- normalized no-vehicle access
- population density

## Project Use

ACS data was used to estimate demographic vulnerability. Poverty and lack of vehicle access were treated as important indicators because they can increase the burden of reaching healthy food retailers.

## Main Outputs

- `data/raw/census/census_data.csv`
- `data/processed/stl_tracts_with_data.geojson`

## Notes

ACS data is survey-based and includes uncertainty. The demographic data was joined at the tract level, then used in later block group modeling through spatial joins and area-based population allocation.

---

# 3. OpenStreetMap Grocery Store Data

## Source

OpenStreetMap, accessed with OSMnx.

## Tags Used

The grocery store dataset was built from OpenStreetMap features tagged as:

- `shop=supermarket`
- `shop=grocery`
- `shop=convenience`

## Project Use

Grocery store locations were used as destination points in the accessibility model.

The raw store data was cleaned by:

- removing invalid records
- removing duplicate locations
- filtering to relevant store types
- standardizing store names and brands where possible
- classifying stores by size
- assigning store weights
- snapping stores to road network nodes

## Main Outputs

- `data/raw/stores/osm_stores.geojson`
- `data/processed/stores_ready.geojson`

## Notes

OpenStreetMap is community-maintained, so store data may be incomplete, outdated, or inconsistently tagged. Store type also does not fully capture food quality, price, or availability.

---

# 4. OpenStreetMap Road Network Data

## Source

OpenStreetMap road network data, accessed with OSMnx.

## Project Use

The road network was used to calculate realistic travel time to grocery stores instead of straight-line distance.

The project used the network for:

- snapping grocery stores and block group centroids to network nodes
- walking travel-time analysis
- driving travel-time analysis
- shortest-path accessibility modeling
- isochrone generation

## Travel-Time Assumptions

| Mode | Method |
|---|---|
| Driving | OSMnx-derived speed and travel-time estimates |
| Walking | Edge length divided by walking speed |
| Walking speed | 1.4 meters per second |

## Main Outputs

- `data/raw/network/stl_network.graphml`
- `data/processed/network_nodes.geojson`
- `data/processed/network_edges.geojson`
- `data/processed/stl_drive_network.graphml`
- `data/processed/stl_walk_network.graphml`

## Notes

Road network travel times are estimates. The model does not directly account for traffic, sidewalk quality, safety, crossings, slope, transit access, or time-of-day conditions.

---

# 5. Project-Derived Outputs

The project also created several derived datasets from the original sources.

## Accessibility Outputs

- `data/processed/block_group_access_scores.geojson`
- `data/processed/walk_isochrones.geojson`
- `data/processed/drive_isochrones.geojson`

These layers include walking time, driving time, accessibility score, and service-area polygons.

## Severity Model Outputs

- `data/processed/food_desert_severity_model.geojson`
- `data/processed/food_desert_summary.csv`

These files include access severity, demographic vulnerability, food desert severity score, severity classification, allocated population, and alternate model scores.

## Sensitivity Analysis Outputs

- `data/processed/severity_stability_analysis.geojson`
- `data/processed/severity_population_summary.csv`
- `data/processed/severity_agreement_scores.csv`

These files compare the baseline, access-heavy, and demographic-heavy severity models.

## Web-Ready Outputs

- `data/web_ready/severity_model.geojson`
- `data/web_ready/stores.geojson`
- `data/web_ready/tracts.geojson`
- `data/web_ready/walk_iso.geojson`
- `data/web_ready/drive_iso.geojson`
- `data/web_ready/edges.geojson`
- `data/web_ready/metadata.json`

These files are used by the React/Leaflet web map.

---

# Coordinate Reference System Notes

The project uses `EPSG:4326` as the standard CRS for stored GeoJSON outputs and web mapping.

When accurate spatial measurements are needed, layers are temporarily reprojected into projected coordinate systems. This is used for operations such as centroid creation, area calculation, population allocation, and density checks.

After those analytical steps, outputs are returned to `EPSG:4326` for consistency and Leaflet compatibility.

---

# Data Quality and Limitations

This project is a portfolio-level food access severity model, not an official food desert designation.

Main limitations:

- ACS data contains survey uncertainty.
- OpenStreetMap grocery store data may be incomplete or outdated.
- Store type does not fully describe food affordability, quality, or inventory.
- Road network travel times are estimates.
- Transit access was not directly modeled.
- Population allocation from tracts to block groups is approximate.
- The severity score is relative to the St. Louis study area.

---

# Attribution

This project uses or derives data from:

- U.S. Census Bureau TIGER/Line shapefiles
- U.S. Census Bureau American Community Survey
- OpenStreetMap contributors
- OSMnx

---

# Summary

The project combines public boundary, demographic, grocery store, and road network data into a reproducible GIS workflow. These datasets support the final accessibility model, food desert severity model, sensitivity analysis, and interactive web GIS application.
