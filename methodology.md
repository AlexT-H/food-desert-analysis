# SAFE - Spatial Accessibility to Food Explorer - Methodology

## Project Overview

SAFE models food access severity across **St. Louis City and St. Louis County** using a combination of demographic vulnerability, grocery store accessibility, road network travel time, and sensitivity analysis.

The goal is not only to identify areas with limited grocery access, but to estimate where limited access overlaps with socioeconomic vulnerability.

The methodology is organized into four phases:

1. **Phase 1 - Data Preparation**
2. **Phase 2 - Network Accessibility Analysis**
3. **Phase 3 - Food Desert Severity Modeling**
4. **Phase 4 - Web GIS Preparation**

---

## Reusable Study Area Design

The methodology was designed around a configurable study area rather than a hardcoded map extent. St. Louis City and St. Louis County were used as the demonstration region, but the same approach can be applied to other regions by changing the boundary selection and related Census/OpenStreetMap download parameters.

Because the pipeline uses public census boundaries, ACS demographic variables, OpenStreetMap grocery data, and OSMnx network extraction, the overall method can be reproduced for other U.S. cities or counties with similar input adjustments.

---

## Coordinate Reference System Strategy

SAFE uses `EPSG:4326` as the standard coordinate reference system for stored GeoJSON outputs and web mapping compatibility.

Because `EPSG:4326` is a geographic coordinate system, it is not used for all analytical calculations. When accurate geometry measurements are required, layers are temporarily reprojected into projected coordinate systems. For example, projected CRS transformations are used for centroid creation, area calculation, population allocation, and density checks.

After these analytical steps are completed, layers are converted back to `EPSG:4326` so that project outputs remain consistent, portable, and compatible with browser-based mapping tools such as Leaflet.

---

# Phase 1 - Data Preparation

## Purpose

Phase 1 established the base geospatial and demographic datasets used in the model.

The study area was defined as the combined region of:

- St. Louis City
- St. Louis County

This combined boundary captures both urban and suburban food access patterns.

## Data Sources

The project used three main data sources:

- U.S. Census boundary shapefiles
- American Community Survey demographic data
- OpenStreetMap grocery store and road network data

## Census and Demographic Data

Census tracts and block groups were prepared for the study area. ACS demographic variables were downloaded and joined to tract geometries.

The main demographic indicators used were:

- total population
- poverty indicators
- households without vehicle access
- median income

From these, the project calculated:

- poverty rate
- no-vehicle household rate
- normalized poverty
- normalized no-vehicle access

These variables were selected because poverty and lack of vehicle access can increase the practical burden of reaching healthy food retailers.

## Grocery Store Data

Grocery store locations were collected from OpenStreetMap using store-related tags such as:

- supermarket
- grocery
- convenience

The store dataset was cleaned by removing invalid geometries, duplicate locations, and unusable records. Store names and brands were standardized where possible.

Stores were also classified by size and assigned weights to distinguish larger food retailers from smaller convenience-oriented stores.

## Road Network Data

A road network was downloaded from OpenStreetMap using OSMnx. This network provided the foundation for routing and travel-time analysis in Phase 2.

## Python Files Used

- `filter_stl_study_area.py`
- `download_census_data.py`
- `join_census_to_tracts.py`
- `download_grocers.py`
- `download_network.py`
- `prepare_network_layers.py`
- `clean_store_data.py`

---

# Phase 2 - Network Accessibility Analysis

## Purpose

Phase 2 measured grocery accessibility using **network travel time** rather than straight-line distance.

Network travel time was used because it better represents real-world access. A grocery store may be physically nearby, but difficult to reach if the street network, walkability, or driving route is inefficient.

## Origin and Destination Design

The analysis used:

- census block groups as origins
- cleaned grocery store locations as destinations

Block groups were used because they provide more localized spatial detail than census tracts.

Block group centroids and grocery store points were snapped to the nearest road network nodes before routing.

## Travel Time Modeling

Two travel modes were modeled:

- walking
- driving

Drive travel times were based on OSM-derived road network attributes. Walking travel times were calculated using a constant walking speed assumption of **1.4 meters per second**.

Multi-source Dijkstra shortest path analysis was used to calculate the minimum travel time from each block group to the nearest grocery store.

This produced:

- `walk_time_min`
- `drive_time_min`

## Accessibility Score

Travel times were converted into a 1-5 accessibility score:

- **5** = strong walk access
- **4** = moderate walk access
- **3** = short drive access
- **2** = longer drive access
- **1** = poor access

This score became the primary accessibility input for the severity model.

## Isochrones

The project also generated service area isochrones:

- 10-minute walk access
- 15-minute drive access

These layers were used for visual interpretation and web map context.

## Python File Used

- `accessibility_analysis.py`

---

# Phase 3 - Food Desert Severity Modeling

## Purpose

Phase 3 combined accessibility and demographic vulnerability into a composite food desert severity model.

The goal was to move beyond a simple food desert / not food desert classification and instead produce a continuous severity score for each block group.

## Spatial Unit of Analysis

The main modeling unit was the **census block group**.

Block groups were selected because they provide a more detailed spatial unit than tracts and can better reveal neighborhood-level variation.

## Demographic Vulnerability

Demographic vulnerability was based on normalized indicators related to socioeconomic constraint:

- normalized poverty
- normalized no-vehicle household access

These were combined into a demographic vulnerability index.

## Access Severity

The access score from Phase 2 was inverted so that worse access produced higher severity.

This created an `access_severity` measure that could be combined with demographic vulnerability.

## Baseline Severity Model

The baseline model weighted access severity and demographic vulnerability equally.

```text
food_desert_severity =
0.5 * access_severity_norm +
0.5 * demographic_vulnerability
```

This produced a continuous food desert severity score for each block group.

## Severity Classification

The continuous severity score was also grouped into readable classes for mapping:

- Minimal
- Very Low
- Low
- Moderate
- High
- Very High
- Extreme

These classes help make the final map easier to interpret while still preserving the underlying continuous score.

## Population Allocation

Because demographic data was joined at the tract level, population was allocated to block groups using area share.

This created an estimated `allocated_population` field.

The main assumption is that tract population is evenly distributed across the tract area. This is useful for estimation, but it may smooth over real population density differences.

## Sensitivity Analysis

Two alternative severity models were created:

- **Access-heavy model:** places more weight on physical grocery access
- **Demographic-heavy model:** places more weight on socioeconomic vulnerability

These models test whether high-severity areas remain stable when weighting assumptions change.

High-severity areas were identified using the top 20% of baseline severity scores.

The model comparison produced:

- stable high-severity areas
- access-driven areas
- demographic-driven areas
- base-only high-severity areas
- not-high areas

Jaccard similarity was used to measure overlap between model scenarios.

## Quality Control

A final data audit checked population totals, low-population areas, area calculations, population density, and extreme values.

This helped identify possible issues before preparing the data for the web map.

## Python Files Used

- `f_d_severity_analysis.py`
- `severity_sensitivity_analysis.py`
- `data_integrity_audit.py`

---

# Phase 4 - Web GIS Preparation

## Purpose

Phase 4 prepared the final model outputs for a browser-based GIS application.

The goal was to convert analytical GIS outputs into clean, lightweight, web-ready GeoJSON layers.

## Web Data Preparation

The final processed layers were cleaned for frontend use by:

- fixing invalid geometries
- verifies and standardizes final web-ready layers to `EPSG:4326`
- retaining only web-relevant fields
- rounding numeric values for readable popups
- converting block group area values to square miles
- adding readable block group IDs
- merging stability classification into the main severity layer

## Geometry Optimization

Block group and tract polygons were not simplified because simplification caused visible gaps between adjacent polygons.

Simplification was limited to heavier context layers where small geometry changes were less visually damaging, such as:

- walk isochrones
- drive isochrones
- network edges

## Web Map Design

The final web application uses one primary block group layer with multiple map modes.

Main map views include:

- severity classification
- food desert severity score
- access-heavy severity
- demographic-heavy severity
- access score
- access severity
- stability classification

Optional reference layers include:

- grocery stores
- census tracts
- walk isochrones
- drive isochrones
- network edges

This structure keeps the web app efficient while allowing users to compare model outputs.

## Frontend Approach

The web app was built with:

- React
- Vite
- Leaflet
- React-Leaflet

The app loads static GeoJSON files from the frontend public data folder, so no backend is required at runtime.

## Python File Used

- `prepare_web_data.py`

---

# Key Assumptions

This model depends on several important assumptions:

- Network travel time is a better proxy for access than straight-line distance.
- Poverty and vehicle access are useful indicators of food access vulnerability.
- Block groups provide a suitable spatial scale for neighborhood-level analysis.
- Area-weighted population allocation is an acceptable estimate where block-group population values are not directly available.
- Severity is relative to the St. Louis study area, not an official federal food desert classification.

---

# Limitations

SAFE has limitations:

- Grocery store data may be incomplete or outdated.
- Store type does not fully represent food quality, price, or availability.
- Transit accessibility was not directly modeled.
- Population allocation may not reflect real residential density patterns.
- The model does not include household-level income or mobility behavior.
- The final severity score is a relative index, not an official designation.

---

# Final Outcome

The methodology produces a reproducible food access severity model that combines:

- demographic vulnerability
- network-based grocery accessibility
- weighted severity scoring
- sensitivity analysis
- web-ready GIS outputs

The final result is an interactive web GIS application that allows users to explore and compare food access severity across St. Louis City and St. Louis County.
