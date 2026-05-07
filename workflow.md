# SAFE - Spatial Accessibility to Food Explorer

## Project Overview

SAFE builds a reproducible GIS pipeline for identifying food access severity across St. Louis City and St. Louis County. The workflow moves from raw census, grocery store, and road network data into a modeled food desert severity layer and a deployment-ready web GIS application.

The project is organized into four phases:

1. **Phase 1 - Data Collection and Preparation**
2. **Phase 2 - Network Accessibility Analysis**
3. **Phase 3 - Food Desert Severity Modeling**
4. **Phase 4 - Web GIS Preparation and Deployment**

---

## Adapting the Workflow to Another Region

The workflow was built around St. Louis City and St. Louis County, but it can be adapted to another study area.

To apply the pipeline to a new region, update:

- the study area boundary or county/place identifiers
- Census FIPS codes used for tract and block group filtering
- ACS download geography parameters
- OSMnx place name or polygon used for grocery and network downloads
- output file names if needed
- frontend map center and zoom
- any region-specific styling or labels

After those changes, the same phase structure can be reused:

1. prepare study area and demographic data
2. download and clean grocery store data
3. build the road/walk network
4. calculate accessibility scores
5. generate severity and sensitivity outputs
6. prepare web-ready GeoJSON files
7. display the results in the React/Leaflet frontend

---

## Coordinate Reference System Workflow

SAFE uses `EPSG:4326` as the standard CRS for GeoJSON storage, project consistency, and web mapping.

Throughout the pipeline, layers are reprojected when specific operations require a projected CRS. For example:

- centroid creation uses a projected CRS before converting results back to `EPSG:4326`
- area calculations use projected CRS units for accurate measurement
- final GeoJSON outputs are standardized back to `EPSG:4326`
- web-ready layers are explicitly checked and converted to `EPSG:4326`

This approach keeps the project compatible with Leaflet while still allowing more accurate spatial calculations where needed.

---

# Phase 1 - Data Collection and Preparation

## Purpose

Phase 1 creates the cleaned, analysis-ready base datasets used throughout the project. This includes the study area boundary, census tract and block group geometries, ACS demographic data, grocery store locations, and the road network.

## Python Files Used

- `filter_stl_study_area.py`
- `download_census_data.py`
- `join_census_to_tracts.py`
- `download_grocers.py`
- `download_network.py`
- `prepare_network_layers.py`
- `clean_store_data.py`

## Workflow Summary

### 1. Define the Study Area

`filter_stl_study_area.py` filters Missouri census shapefiles to isolate:

- St. Louis City
- St. Louis County

It exports the project boundary, census tracts, and block groups as processed GeoJSON files.

### 2. Download and Join Census Data

`download_census_data.py` downloads ACS demographic variables for the study area, including:

- total population
- median income
- vehicle access
- poverty indicators

`join_census_to_tracts.py` joins the ACS data to census tract geometries and calculates derived demographic fields:

- poverty rate
- no-vehicle household rate
- normalized poverty
- normalized no-vehicle access
- population density

### 3. Download and Clean Grocery Store Data

`download_grocers.py` queries OpenStreetMap for grocery-related features, including supermarkets, grocery stores, and convenience stores.

`clean_store_data.py` prepares the store layer by:

- removing invalid geometries
- removing duplicate store points
- filtering to valid store categories
- standardizing names and brands
- classifying stores by size
- assigning store weights
- snapping stores to the road network

### 4. Download and Prepare the Road Network

`download_network.py` downloads the drivable OpenStreetMap road network for the study area.

`prepare_network_layers.py` converts the network graph into GeoJSON node and edge layers for mapping and inspection.

## Phase 1 Outputs

### Data Outputs

- `data/processed/stl_boundary.geojson`
- `data/processed/stl_tracts.geojson`
- `data/processed/stl_block_groups.geojson`
- `data/raw/census/census_data.csv`
- `data/processed/stl_tracts_with_data.geojson`
- `data/raw/stores/osm_stores.geojson`
- `data/processed/stores_ready.geojson`
- `data/raw/network/stl_network.graphml`
- `data/processed/network_nodes.geojson`
- `data/processed/network_edges.geojson`

### Python Files

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

Phase 2 measures grocery store accessibility using realistic network travel time instead of straight-line distance.

## Python Files Used

- `accessibility_analysis.py`

## Workflow Summary

### 1. Build or Load Transportation Networks

`accessibility_analysis.py` creates or loads cached drive and walk networks for the study area.

The drive network uses OSM-derived travel speeds. The walk network uses a walking speed assumption of 1.4 meters per second.

### 2. Snap Origins and Destinations to the Network

The script snaps:

- grocery stores to nearest network nodes
- block group centroids to nearest network nodes

This prepares the data for routing analysis.

### 3. Calculate Travel Times

Multi-source Dijkstra shortest path analysis is used to calculate the minimum travel time from each block group to the nearest grocery store.

The script calculates:

- walking time to nearest store
- driving time to nearest store

### 4. Create Access Scores and Isochrones

Travel times are converted into a 1–5 access score.

The script also generates:

- 10-minute walk isochrones
- 15-minute drive isochrones

## Phase 2 Outputs

### Data Outputs

- `data/processed/block_group_access_scores.geojson`
- `data/processed/walk_isochrones.geojson`
- `data/processed/drive_isochrones.geojson`
- `data/processed/stl_drive_network.graphml`
- `data/processed/stl_walk_network.graphml`

### Python Files

- `accessibility_analysis.py`

---

# Phase 3 - Food Desert Severity Modeling

## Purpose

Phase 3 combines accessibility results with demographic vulnerability indicators to create the main food desert severity model.

## Python Files Used

- `f_d_severity_analysis.py`
- `severity_sensitivity_analysis.py`
- `data_integrity_audit.py`

## Workflow Summary

### 1. Build the Main Severity Model

`f_d_severity_analysis.py` combines:

- access score
- walking travel time
- driving travel time
- normalized poverty
- normalized no-vehicle access
- population data

The script creates:

- `access_severity`
- `demo_vulnerability`
- `food_desert_severity`
- `severity_classification`

The baseline model weights access severity and demographic vulnerability equally.

### 2. Create Alternative Model Scenarios

The script also creates two comparison models:

- `severity_access_heavy`
- `severity_demo_heavy`

These scenarios test how results change when accessibility or demographics are weighted more heavily.

### 3. Allocate Population to Block Groups

Because demographic data is joined at the tract level, population is allocated to block groups using area share.

This creates:

- `allocated_population`

### 4. Run Sensitivity Analysis

`severity_sensitivity_analysis.py` compares the baseline, access-heavy, and demographic-heavy models.

It identifies:

- high-severity areas
- stable high-severity areas
- access-driven areas
- demographic-driven areas
- population impact by scenario
- agreement between models using Jaccard similarity

### 5. Audit the Final Model

`data_integrity_audit.py` checks the final severity layer for:

- total allocated population
- zero or very low population block groups
- area values
- population density
- extreme records

This serves as a final quality-control check before web preparation.

## Phase 3 Outputs

### Data Outputs

- `data/processed/food_desert_severity_model.geojson`
- `data/processed/food_desert_summary.csv`
- `data/processed/severity_stability_analysis.geojson`
- `data/processed/severity_population_summary.csv`
- `data/processed/severity_agreement_scores.csv`
- `data/processed/debug_density_check.geojson`

### Python Files

- `f_d_severity_analysis.py`
- `severity_sensitivity_analysis.py`
- `data_integrity_audit.py`

---

# Phase 4 - Web GIS Preparation and Deployment

## Purpose

Phase 4 converts the completed GIS analysis into a browser-ready web GIS application.

## Python Files Used

- `prepare_web_data.py`

## Workflow Summary

### 1. Prepare Web-Ready GIS Layers

`prepare_web_data.py` converts the final processed GIS outputs into frontend-ready GeoJSON files.

The script:

- fixes invalid geometries
- verifies and standardizes final web-ready layers to `EPSG:4326`
- keeps only web-relevant fields
- rounds numeric values
- converts block group area to square miles
- adds readable block group numbers
- merges `stability_class` into the main severity layer

### 2. Optimize Geometry for Web Use

Block group and tract polygons are not simplified to avoid visible gaps between neighboring polygons.

Heavier context layers may be simplified, including:

- walk isochrones
- drive isochrones
- network edges

### 3. Copy Web Data into the Frontend

The final web-ready GeoJSON files are copied into:

```text
frontend/public/data/
```

The React application loads these files directly in the browser.

### 4. Build the React/Leaflet Frontend

The frontend uses:

- React
- Vite
- Leaflet
- React-Leaflet

The interface includes:

- sidebar controls
- multiple map view modes
- optional reference layers
- block group popups
- dynamic legend
- full-screen responsive map layout

### 5. Prepare for Deployment

Because the app uses static GeoJSON files, no backend is required for deployment.

Recommended static deployment settings:

```text
Root directory: frontend
Build command: npm run build
Output directory: dist
```

## Phase 4 Outputs

### Data Outputs

- `data/web_ready/severity_model.geojson`
- `data/web_ready/stability.geojson`
- `data/web_ready/tracts.geojson`
- `data/web_ready/stores.geojson`
- `data/web_ready/walk_iso.geojson`
- `data/web_ready/drive_iso.geojson`
- `data/web_ready/edges.geojson`
- `data/web_ready/metadata.json`

### Frontend Outputs

- `frontend/src/App.jsx`
- `frontend/public/data/`
- production-ready Vite build

### Python Files

- `prepare_web_data.py`

---

# Final Project Output

The final result is a reproducible GIS pipeline and web GIS application that allows users to explore food access severity across St. Louis City and St. Louis County.

The project produces:

- cleaned census and grocery store datasets
- road network layers
- network-based grocery accessibility scores
- food desert severity scores
- model sensitivity and stability outputs
- web-ready GeoJSON layers
- an interactive React/Leaflet map application

This workflow demonstrates the full process of moving from raw geospatial data to an interactive, portfolio-ready GIS product.
