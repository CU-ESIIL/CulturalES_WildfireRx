# Analysis data

## `01_fire_perimeters/`
Final wildfire and clustered prescribed-fire treatment polygons for Colorado and California. These geometries are reprojected to EPSG:5070 and used to calculate treatment area for the fire-size heterogeneity analysis.

## `02_site_features/`
Monthly and static site covariates. The causal-analysis workflow uses these files to add monthly temperature, vegetation composition, fire-severity measures, and recreation context to the visitation prediction panel. `ModelCovariates.xlsx` documents candidate visitation-model predictors.

## `03_visitation/`
State-specific monthly visitation predictions, treatment labels, and treatment timing. These model predictions are the outcomes used by the event-study analysis.

## `04_analysis/`
Generated intermediate files created by the workflow. This directory is ignored by git.
