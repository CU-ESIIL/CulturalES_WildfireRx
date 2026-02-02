# Notebook Overviews

This document centralizes the high-level descriptions, inputs, outputs, and parameters for the project notebooks while retaining the original markdown cells within each notebook.

---

## 01 — Process Grid and Treatment Sites (CO + CA)

This notebook builds analysis-ready spatial layers for Colorado (grid attributes) and California (treatment sites). It:

- Derives burn history (2000–2024) for a Colorado grid from MTBS + FIRED perimeters.
- Computes trail length per Colorado grid cell.
- Adds public land management type (PADUS) and counts proxy points per cell.
- Identifies California treatment cells intersecting Rx burn perimeters and trails, subtracts roads/urban, and clips to PADUS.

### Key Inputs

- Colorado
  - `...processed_colorado_grid_final.shp` — Base grid for Colorado.
  - `...mtbs_perims_2020_2024.shp` — MTBS fire perimeters; requires field `Ig_Date` (used to derive ignition year).
  - `...fired_conus_ak_2000_to_2024_events.shp` — FIREDpy events; requires `ig_year` (already present/derived).
  - `...Trails_USWest.shp` — Trail lines for intersection and length.
  - `...PADUS4_0Comb_CO.shp` — PADUS polygons for management type.
  - `...ProxiesMerged.shp` — Point proxies to count within grid.
- California
  - `...california_grid_manag_prox_trail_access.shp` — Base grid with attributes used for treatment export.
  - `...cleaned_dissolved_clustered_rx_CA.shp` — Rx burn perimeters.
  - `...Trails_USWest.shp` — Trails for intersect checks.
  - `...PADUS_Comb_CA.shp` — PADUS polygons (clipping to public lands).
  - `...tl_2020_us_uac20.shp` — Urban areas (to subtract from treatments).
  - `...tl_2023_08_prisecroads.shp` — Primary/secondary roads (to buffer/subtract).

### Key Outputs

- `...colorado_grid_with_burn_history.shp` — Adds `last_year_burned`, `prior_burn_years`, `avg_burn_interval_years`.
- `...colorado_grid_with_trail_length.shp` — Adds `grid_id`, `trail_length` (length in grid CRS units).
- `...colorado_grid_manag_prox_trail_access.shp` — Adds `Mang_Name` (majority PADUS) and `proxy_count`.
- `...processed_Rx_sites_CA_final.shp` — CA treatment cells with fire/trail flags and geometries clipped to PADUS, minus roads/urban.

### Key Parameters and Assumptions

- Year filter: 2000–2024 for burn history.
- CRS handling: All layers reprojected to the grid CRS; if the Colorado grid is geographic, it is reprojected to `EPSG:26913` for accurate lengths.
- Spatial predicates: `intersects` for perimeters/trails-on-grid; `within` for points-in-grid.
- Roads buffer: 100 m before subtracting from treatment geometries.
- Burn interval: computed as 25 years divided by the number of burns in 2000–2024.
- Management type: most frequent PADUS `Mang_Name` within each grid cell.
- De-duplication: FIRED years minus MTBS years to avoid double counting.

### Usage Notes

- Update the `...` file paths to your local data locations before running.
- Ensure required fields exist (e.g., `Ig_Date` in MTBS, `ig_year` in FIRED, and columns referenced in CA processing).
- Verify CRSs match when supplying alternate datasets; results depend on consistent projections.

---

## 02 — Matching Code: Control Site Selection for Treatments

This notebook selects matched control sites for each treatment (e.g., Rx-burn) by rotating/translating the treatment geometry over eligible grid cells and minimizing feature distance under spatial/land constraints.

### Key Inputs

- `grid_path`: Grid of candidate cells with attributes used for matching.
- `treatment_path`: Polygons with treatments; requires `Incid_Name` to identify each site.
- `padus_path`: Public lands (PADUS) polygons to constrain controls to public land.
- `mtbs_path`: MTBS perimeters with `Ig_Date` to derive `ig_year` for burn filtering.
- `urban_path`: Urban polygons used to exclude urban areas from final control shapes.
- `roads_path`: Road lines used with a buffer to exclude from final controls.
- `output_dir`: Directory to write outputs; created if missing.

### Key Outputs

- `control_raw_{Incid_Name}.shp`: Candidate control cluster (union of grid cells) before exclusions.
- `control_final_{Incid_Name}.shp`: Final control geometry after PADUS clip and subtracting urban + buffered roads.
- `comparison_{Incid_Name}.csv`: Feature table comparing treatment vs. selected control with absolute differences.
- `all_controls_merged.shp`: Merge of all final controls (if any exist).

### Key Parameters and Logic
- CRS: All inputs reprojected to the grid CRS; PADUS + MTBS clipped to the grid bounding box for speed.
- MTBS year filter: `ig_year >= 2010` (derived from `Ig_Date`).
- Public land flags: precompute `public_overlap` (PADUS intersects cell) and `touches_public` (cell centroid intersects PADUS).
- Burn exclusion: exclude cells where `burned_since_2010` is true (intersects MTBS ≥ 2010).
- Rotation sweep: rotate treatment geometry by 0–315° in 45° steps, then translate to candidate seed centroids.
- Distance threshold: seed centroid must be ≥ 80,467.2 m (~50 miles) from the treatment centroid.
- Area band: candidate cluster total area must be within [0.5×, 1.5×] of treatment area.
- Feature match: minimize Euclidean distance across features `Access_U_1`, `trail_leng`, `proxy_coun`, `Elevation`, `Slope`, `Temperatur`, `Precipitat`.
  - Aggregation: sum for `trail_leng`, `proxy_coun`; mean for others.
- Final control cleaning: clip to PADUS; subtract urban polygons and roads buffered by 100 m.

### Usage Notes
- Set the file paths and `output_dir` before running; ensure fields (`Incid_Name`, `Ig_Date`) exist in inputs.
- Keep all datasets in consistent CRS for valid distance/area calculations.
- Outputs are written per treatment and merged at the end if present.

---

## 03 — Final Visitation Model: Treatment vs Control Predictions
This notebook fits the final visitation model and produces out-of-sample predictions for treatment and matched control sites to support downstream DiD analyses.

### Key Inputs
- `data/RecWildfire_Datasets - Model Covariates.csv`: Model-ready covariates for visitation prediction.
- Treatment sites from prior steps (e.g., `...processed_Rx_sites_CA_final.shp`).
- Matched control clusters from prior steps (e.g., `control_final_{Incid_Name}.shp`).
- Optional: grid-level attributes (access, trails, proxies, elevation, climate) assembled in earlier notebooks.

### Key Outputs
- `outputs/TreatmentControl_Predictions_CA.csv`: Predicted visitation for CA treatments and matched controls.
- `outputs/TreatmentControl_Predictions_CO.csv`: Predicted visitation for CO treatments and matched controls.
- Optional: model artifacts (metrics, feature importances, diagnostic plots).

### Key Parameters and Modeling Choices
- Feature set: derived from model covariates and grid attributes.
- Estimator: specify algorithm (e.g., GLM, RF, GBM) and hyperparameters.
- Train/validation strategy: data splits or cross-validation.
- Temporal handling: pre/post periods and any lag structure to align with DiD.
- CRS/joins: ensure any geospatial merges use consistent CRS before tabular modeling.

### Usage Notes
- Confirm paths to covariates and geospatial inputs; update any `...` placeholders.
- Validate feature columns exist and are clean; align units/scales as needed.
- Run end-to-end to populate prediction CSVs for use in DiD notebooks.

---

## 04 — Difference-in-Differences by Fire Type
This notebook estimates visitation impacts using a Difference-in-Differences (DiD) design, stratified by fire type (e.g., Rx vs. Wildfire), leveraging predictions and covariates assembled earlier.

### Key Inputs
- `outputs/TreatmentControl_Predictions_CA.csv`: Predicted visitation for CA treatments vs controls.
- `outputs/TreatmentControl_Predictions_CO.csv`: Predicted visitation for CO treatments vs controls.
- `data/RecWildfire_Datasets - Model Covariates.csv`: Covariates for adjustment and subgrouping.
- Treatment metadata from earlier steps (e.g., `Ig_Date`, fire type labels) for event timing and type classification.

### Key Outputs
- `outputs/RecWildfire_Datasets - DiD_FireType.csv`: DiD estimates by fire type with standard errors and model controls.
- Optional: summary tables/figures for pre-trends, effect sizes, and robustness checks.

### Key Parameters and Design Choices
- Pre/post window: define event time window around ignition.
- Fire type classification: rules/columns used to label Rx vs Wildfire.
- Fixed effects: time and unit FE (e.g., grid/site) as applicable.
- Controls: covariates included for precision/robustness.
- Standard errors: clustering level (e.g., by site or time).

### Usage Notes
- Ensure prediction CSVs exist and align on unit IDs/time indexes.
- Verify event dates and fire type labels are present and consistent.
- Inspect pre-trends before finalizing DiD estimates.

---

## 05 — DiD Heterogeneity Analysis
This notebook extends the DiD framework to assess heterogeneity of visitation impacts across key dimensions (e.g., management type, access, trails, elevation, climate).

### Key Inputs
- `outputs/TreatmentControl_Predictions_CA.csv` and `outputs/TreatmentControl_Predictions_CO.csv`: Treatment vs control predictions.
- `data/RecWildfire_Datasets - Model Covariates.csv`: Covariates for subgroup definitions and interactions.
- Grid/site attributes from earlier steps (e.g., `Mang_Name`, `Access_U_1`, `trail_leng`, `proxy_coun`, elevation, climate).

### Key Outputs
- `outputs/RecWildfire_Datasets - DiD_Heterogeneity.csv`: DiD estimates with interaction terms/subgroup splits.
- Optional: plots/tables showing effect variation across heterogeneity dimensions.

### Key Parameters and Design Choices
- Subgroup variables: which attributes define heterogeneity (categorical or continuous).
- Interaction specification: model interactions between treatment and subgroup variables.
- Fixed effects and controls: consistent with the base DiD setup.
- Standard errors: clustering strategy.

### Usage Notes
- Confirm subgroup variables are available and well-defined.
- Check balance and overlap across subgroups; consider binning continuous variables.
- Compare baseline DiD results with heterogeneity models for robustness.
