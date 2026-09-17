# Fire treatment perimeters

This directory contains the final treated-site geometries used to calculate fire size:

- `CO_treatment_perimeters.gpkg`: 44 wildfire and 22 prescribed-fire treatment sites.
- `CA_treatment_perimeters.gpkg`: 141 wildfire and 32 prescribed-fire treatment sites.

Each GeoPackage contains a `siteid` field matching the visitation-analysis inputs and a `fire_type` field identifying wildfire or prescribed fire. Prescribed-fire polygons represent the clustered treatment units used in the study.

The analysis dissolves multiple geometry parts by `siteid`, reprojects them to CONUS Albers Equal Area (`EPSG:5070`), and calculates `fire_area_km2` directly from geometry. The general site-area covariate in the feature matrices is not used to define fire size.
