# CulturalES_WildfireRx

Reproducible Python workflow for the analysis of wildfire, prescribed fire, and public-land recreation in California and Colorado.

The repository contains the processed inputs and analysis code required to reproduce the manuscript's causal estimates, heterogeneity analyses, summary tables, and figures.

## Analysis

The final sample includes 185 wildfire treatment sites and 54 prescribed-fire treatment sites with matched never-treated controls. Monthly visitation is represented by state-specific machine-learning predictions and analyzed using saturated Sun-Abraham event studies.

The event-study outcome is the prediction produced by the selected visitation model on the scale on which that model was fit. Colorado predictions are on the square-root outcome scale and California predictions are on the identity scale. Models adjust for monthly mean temperature.

Heterogeneity is estimated by fire size, fire severity, vegetation type, and recreation context. Fire size is calculated directly from the treatment polygons in `data/01_fire_perimeters/` after reprojection to CONUS Albers Equal Area (`EPSG:5070`). State-specific size classes are defined from terciles of treated-site area. Continuous response functions additionally estimate how fire effects vary with weighted CBI and fire area.

## Repository structure

```text
CulturalES_WildfireRx/
├── README.md
├── LICENSE
├── pyproject.toml
├── run_all.py
├── data/
│   ├── 01_fire_perimeters/     # treatment polygons used for fire-size calculations
│   ├── 02_site_features/       # site covariates and covariate documentation
│   ├── 03_visitation/          # visitation predictions and treatment timing
│   └── 04_analysis/            # generated intermediate analysis tables
├── src/recfire/                # reusable analysis functions
├── scripts/
│   ├── 01_validate_inputs.py
│   ├── 02_calculate_fire_size.py
│   ├── 03_build_analysis_data.py
│   ├── 04_describe_sample.py
│   ├── 05_estimate_firetype.py
│   ├── 06_estimate_heterogeneity.py
│   ├── 07_plot_firetype.py
│   ├── 08_plot_heterogeneity.py
│   └── 09_continuous_response_functions.py
└── outputs/
    ├── tables/
    └── figures/
```

## Installation

```bash
git clone https://github.com/CU-ESIIL/CulturalES_WildfireRx.git
cd CulturalES_WildfireRx
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e .
```

## Run the analysis

```bash
python run_all.py
```

The workflow calculates fire area, builds the analysis panels, summarizes the treatment sample, estimates overall and heterogeneous fire effects, recreates the manuscript figures, and estimates continuous response functions for fire severity and size.

## Inputs

`data/01_fire_perimeters/CO_treatment_perimeters.gpkg` contains the 44 wildfire and 22 prescribed-fire treatment sites in the Colorado analysis.

`data/01_fire_perimeters/CA_treatment_perimeters.gpkg` contains the 141 wildfire and 32 prescribed-fire treatment sites in the California analysis.

`data/02_site_features/` contains the monthly and static covariates used by the analysis. `ModelCovariates.xlsx` documents the candidate visitation-model predictors.

`data/03_visitation/` contains state-specific monthly visitation predictions, treatment labels, and treatment timing.

## Outputs

Result tables are written to `outputs/tables/`:

- `did_results_firetype.csv`: overall wildfire and prescribed-fire event-study estimates.
- `did_heterogeneity_results.csv`: event-study estimates by fire size, severity, vegetation, and recreation context.
- `fire_characteristics_summary.csv`: treatment-sample fire characteristics.
- `size_class_counts.csv`: treatment-site counts by fire-size class.
- `continuous_moderator_effects_comprehensive.csv`: annual baseline and interaction coefficients for continuous severity and fire-size models.
- `severity_response_function_coefficients.csv`: severity response-function coefficients.
- `severity_response_function_lookup.csv`: effects evaluated at common CBI values.
- `severity_response_function_wildfire_summary.csv`: wildfire effects at representative low-, moderate-, and high-severity CBI values for Years 1, 3, and 5.
- `size_response_function_coefficients.csv`: fire-size response-function coefficients using corrected polygon area.
- `size_response_function_lookup.csv`: effects evaluated at the 10th, 25th, 50th, 75th, and 90th percentiles of observed fire size.
- `size_response_function_wildfire_summary.csv`: wildfire effects evaluated at representative corrected areas for the small, medium, and large size classes in Years 1, 3, and 5.
- `continuous_response_function_curves.csv`: values used to reproduce the continuous response-function figures.

Figures are written to `outputs/figures/`:

- `Overall_Effects.png`
- `Overall_Effects.pdf`
- `Heterogeneous_Effects.png`
- `Heterogeneous_Effects.pdf`
- `FigS_Severity_Response_Functions.png`
- `FigS_Severity_Response_Functions.pdf`
- `FigS_Size_Response_Functions.png`
- `FigS_Size_Response_Functions.pdf`

## Citation

Manley, K. et al. *Large Recreation Declines Persist for Years after Severe Wildfire but Not after Low-Severity or Prescribed Fire.*
