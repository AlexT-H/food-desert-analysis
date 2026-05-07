# Data Directory

Large raw and intermediate GIS datasets are not committed to this repository due to repository size limits and deployment efficiency.

The deployed web application uses optimized GeoJSON files stored in:

`frontend/public/data/`

Raw and intermediate datasets used during analysis included Census boundary data, demographic data, grocery store data, OpenStreetMap-derived network data, processed accessibility outputs, and severity model outputs.

The project workflow is reproducible through the preprocessing and analysis scripts in the `scripts/` directory. Web-ready layers are generated from processed analytical outputs and copied into the frontend public data directory for static deployment. See `workflow.md / methodology.md` for more details.