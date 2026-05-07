# SAFE - Spatial Accessibility to Food Explorer

## Project Overview

SAFE is a full GIS analysis and web mapping application that identifies food access severity across **St. Louis City and St. Louis County**.

The project combines census demographics, grocery store locations, road network data, network-based travel time analysis, and weighted severity modeling to highlight areas where residents may face the greatest barriers to healthy food access.

The final output is an interactive **React + Leaflet web GIS application** that allows users to explore food desert severity, compare model assumptions, inspect block group-level metrics, and toggle contextual GIS layers.

Rather than functioning as a one-off local map, SAFE serves as a reusable GIS framework for building food access severity models in other study areas using public Census and OpenStreetMap data.

**Live Deployment Link: https://spatial-accessibility-to-food-explorer.vercel.app/**

---

## Project Goals

The purpose of this project was to build a complete GIS Developer portfolio project that demonstrates:

- geospatial data collection and cleaning
- census and demographic data integration
- OpenStreetMap data processing
- network-based accessibility modeling
- food desert severity scoring
- sensitivity analysis
- GeoJSON preparation for web mapping
- interactive frontend GIS development
- deployment-ready static web GIS architecture

---

## Study Area

The study area includes:

- St. Louis City, Missouri
- St. Louis County, Missouri

These areas were combined into one regional study boundary to capture both urban and suburban food access patterns.

---

## Main Technologies Used

### GIS and Data Processing

- Python
- GeoPandas
- Pandas
- OSMnx
- NetworkX
- Shapely
- RapidFuzz
- Census API
- QGIS

### Web GIS

- React
- Vite
- Leaflet
- React-Leaflet
- GeoJSON
- CSS

---

## Data Sources

The project uses publicly available geospatial and demographic data:

- U.S. Census TIGER/Line boundary shapefiles
- American Community Survey demographic data
- OpenStreetMap grocery store features
- OpenStreetMap road network data

Key input categories include:

- census tracts
- census block groups
- county boundaries
- population data
- poverty indicators
- vehicle access indicators
- grocery store locations
- road network edges and nodes

---

## Scalability and Reusability

AlthoughSAFE was implemented for St. Louis City and St. Louis County, the pipeline was designed to be reusable for other study areas.

Most of the workflow can be adapted to a new region by changing the study area boundary, county/place identifiers, and data download parameters. The same process can then be used to collect census data, download OpenStreetMap grocery stores, build road networks, calculate accessibility, generate severity scores, and prepare web-ready GeoJSON outputs.

This makes the project more than a single local case study. It serves as a reusable GIS framework for food access analysis in other cities, counties, or regions.

---

## Project Phases

## Phase 1 - Data Collection and Preparation

Phase 1 created the base datasets needed for analysis.

This phase included:

- defining the St. Louis study area
- preparing tract and block group geometries
- downloading ACS demographic data
- joining census attributes to tract geometries
- downloading grocery store locations from OpenStreetMap
- cleaning and standardizing grocery store records
- downloading and preparing the road network

### Main Python Scripts

- `filter_stl_study_area.py`
- `download_census_data.py`
- `join_census_to_tracts.py`
- `download_grocers.py`
- `download_network.py`
- `prepare_network_layers.py`
- `clean_store_data.py`

---

## Phase 2 - Network Accessibility Analysis

Phase 2 measured realistic access to grocery stores using network travel time.

Instead of using straight-line distance, this phase used OpenStreetMap road and pedestrian networks to calculate travel time from each census block group to the nearest grocery store.

This phase produced:

- walking time to nearest grocery store
- driving time to nearest grocery store
- block group access scores
- 10-minute walk isochrones
- 15-minute drive isochrones

### Main Python Script

- `accessibility_analysis.py`

---

## Phase 3 - Food Desert Severity Modeling

Phase 3 combined accessibility results with demographic vulnerability indicators to create the food desert severity model.

The model used:

- network-based grocery access
- poverty rate
- no-vehicle household rate
- allocated population
- normalized demographic vulnerability
- weighted severity scoring

The project created three severity scenarios:

- baseline severity model
- access-heavy model
- demographic-heavy model

Sensitivity analysis was used to compare model outputs and identify stable high-severity areas.

### Main Python Scripts

- `f_d_severity_analysis.py`
- `severity_sensitivity_analysis.py`
- `data_integrity_audit.py`

---

## Phase 4 - Web GIS Frontend and Deployment Preparation

Phase 4 converted the completed GIS analysis into an interactive web application.

This phase included:

- preparing browser-ready GeoJSON files
- filtering fields for frontend use
- fixing geometries
- verifying final web-ready layers are assigned `EPSG:4326`
- rounding values for readable popups
- converting area values to square miles
- building the React/Leaflet interface
- adding map view controls
- adding optional reference layers
- adding block group popups
- preparing the app for static deployment

### Main Python Script

- `prepare_web_data.py`

---

## Key Outputs

The project produces several major outputs:

- cleaned grocery store dataset
- processed census tract and block group layers
- road network node and edge layers
- block group accessibility scores
- walk and drive isochrones
- food desert severity model
- sensitivity and stability analysis outputs
- web-ready GeoJSON layers
- interactive React/Leaflet web GIS application

---

## Main Web Map Features

The final web map includes:

- multiple food desert severity views
- baseline severity classification
- access-heavy severity model
- demographic-heavy severity model
- access score view
- access severity view
- stability classification view
- grocery store markers
- census tract boundaries
- walk isochrones
- drive isochrones
- road network context layer
- interactive block group popups
- dynamic legend
- sidebar layer controls

---

## Repository Structure

```text
food-desert-severity/
├── data/
│   ├── raw/
│   ├── processed/
│   └── web_ready/
├── frontend/
│   ├── public/
│   │   └── data/
│   ├── src/
│   │   └── App.jsx
│   ├── package.json
│   └── vite.config.js
├── scripts/
│   ├── filter_stl_study_area.py
│   ├── download_census_data.py
│   ├── join_census_to_tracts.py
│   ├── download_grocers.py
│   ├── download_network.py
│   ├── prepare_network_layers.py
│   ├── clean_store_data.py
│   ├── accessibility_analysis.py
│   ├── f_d_severity_analysis.py
│   ├── severity_sensitivity_analysis.py
│   ├── data_integrity_audit.py
│   └── prepare_web_data.py
├── README.md
├── methodology.md
├── workflow.md
├── data_sources.md
└── stl_food_desert_model.qgz

```

---

## Running the Project Locally

### 1. Run the Python GIS Pipeline

The Python scripts are intended to be run in phase order from the project root.

General order:

```text
Phase 1:
python scripts/filter_stl_study_area.py
python scripts/download_census_data.py
python scripts/join_census_to_tracts.py
python scripts/download_grocers.py
python scripts/download_network.py
python scripts/prepare_network_layers.py
python scripts/clean_store_data.py

Phase 2:
python scripts/accessibility_analysis.py

Phase 3:
python scripts/f_d_severity_analysis.py
python scripts/severity_sensitivity_analysis.py
python scripts/data_integrity_audit.py

Phase 4:
python scripts/prepare_web_data.py
```

After Phase 4, copy the web-ready GeoJSON files into:

```text
frontend/public/data/
```

---

### 2. Run the Frontend

From the frontend folder:

```bash
cd frontend
npm install
npm run dev
```

To test a production build:

```bash
npm run build
npm run preview
```

---

## Deployment Notes

The final web app can be deployed as a static frontend project because it loads preprocessed GeoJSON files directly from the public data folder.

Recommended deployment settings:

```text
Root directory: frontend
Build command: npm run build
Output directory: dist
```

Suitable platforms include:

- Vercel
- Netlify
- GitHub Pages, with configuration adjustments

---

## Methodology Summary

SAFE uses network-based travel time instead of straight-line distance because travel time better represents real-world food access.

Demographic vulnerability was measured using normalized poverty and no-vehicle household indicators. These were combined with accessibility severity to create a composite food desert severity score.

The baseline model weights access and demographic vulnerability equally. Alternative access-heavy and demographic-heavy models were created to test whether high-severity areas remain stable under different assumptions.

Sensitivity analysis identifies areas that are consistently high severity across model scenarios, as well as areas that are primarily access-driven or demographically driven.

---

## Limitations

SAFE is a relative food access severity model and should not be interpreted as an official food desert designation.

Important limitations include:

- OpenStreetMap provides opensource grocery store data which may be incomplete or outdated.
- Store type does not fully capture food quality, price, or availability.
- Population was allocated from tracts to block groups using area share.
- Transit access was not directly modeled.
- Quantile severity score projections are relative to the study area.
- The model does not directly account for individual mobility, income variation within block groups, or household-level behavior.

---

## Final Result

The final project demonstrates a full GIS development workflow from raw data to deployed web GIS product.

It shows how Python, GeoPandas, OSMnx, NetworkX, QGIS, React, and Leaflet can be combined to build a reproducible spatial analysis pipeline and an interactive public-facing map application.
