# Fire and Recreation in the U.S. West: Modeling Impacts of Wildfire and Prescribed Fire on Nature's Non-Material Contributions to People

**A comprehensive analysis of fire effects on public land visitation across California and Colorado (2020-2024)**

This repository contains code and data for quantifying how wildfire and prescribed fire reshape recreational visitation on public lands. Recreation is among the most prominent non-material contributions of nature (cultural ecosystem services) to human well-being, supporting local economies, cultural connection, and place-based values across the western United States. This work is part of the [MORPHO Rx Working Group](https://rx-char.github.io/) and a Cooperative Institute for Research in Environmental Sciences Visiting Fellowship Program project.

## Citation

Manley, K., Wood, S., Evers, C., Nowell, H., Balch, J.K., Braun, L., Cale, A., LoPresti, A., McIntosh, T.L., Peeler, J., Siegel, K., & Dee, L.E. (2025). Fire and Recreation in the U.S. West: Modeling Impacts of Wildfire and Prescribed Fire on Nature's Non-Material Contributions to People. *In preparation*.

## Research Questions

**1. How do wildfire and prescribed fire differentially affect public land visitation?**
- Does prescribed fire mitigate recreational losses compared to wildfire?
- How do impacts vary by fire characteristics (type, severity, size)?
- How do impacts vary by landscape context (state, vegetation type, land manager)?
- How persistent are impacts and do sites recover over time?

**2. Who bears the burden of fire impacts on recreation?**
- Do recreation-dependent counties experience disproportionate wildfire exposure and impacts?
- What are the implications for environmental justice and equitable fire management?

## Key Findings

- **Wildfire reduces visitation substantially** (15-18% in Year 1) with multi-year persistence, while **prescribed fire shows neutral-to-positive effects** (+1-5% in Year 1)
- **Fire size and severity drive impacts**: Large, high-severity wildfires reduce visitation by 24-58%, while low-severity fires show smaller, transient effects more negatie, but comparable to prescribed fire
- **Geographic heterogeneity matters**: Colorado wildfire sites show 46% recovery by Year 5, while California sites show minimal recovery (13%)
- **Vegetation context is critical**: Forested sites experience 4-5× greater impacts (-25-26%) than grassland sites (-5-6%)
- **Environmental justice implications**: Recreation-dependent counties in Colorado experienced a 1.45× exposure-impact gap, bearing disproportionate wildfire burdens despite lower fire exposure
- **Recovery trajectories diverge**: High-severity impacts persist for years, while low-severity sites show partial recovery by Year 5, particularly in Colorado

## Study Overview

**Study Area:** Public lands across California and Colorado (2020-2024)

**Treatment Sites:**
- California: 141 wildfires, 32 prescribed fire clusters
- Colorado: 44 wildfires, 22 prescribed fire clusters

**Data Sources:**
- Fire perimeters: MTBS (2020-2024), USFS Activity Tracking System
- Visitation counts: USFS, NPS, FWS, BLM (16 sites CO, 27 sites CA)
- Digital mobility: Flickr, eBird, AllTrails, Reveal mobile phone data
- Environmental: LandFire (vegetation, topography), TerraClimate (weather), PADUS (land management), RIDB (recreation facilities)

## Repository Organization

**code/** - Analysis scripts organized by workflow stage: data processing (fire perimeter processing, control site matching), visitation modeling (ML model training and prediction), and causal analysis (DiD estimation, heterogeneity analysis)

**data/** - Processed datasets used in the analysis

**outputs/** - Publication-quality figures, summary statistics tables, model results, and trained visitation models

## Methods Summary

### Fire Treatment Sites
Wildfire perimeters from MTBS (2020-2024) and prescribed fire perimeters from USFS Activity Tracking System were clipped to public lands, removing urban areas and road buffers. Prescribed fires were spatiotemporally clustered (20km, 30 days) to create continuous treatment polygons. Grid cells (1km resolution) overlapping fire perimeters were extracted with associated confounders.

### Control Site Matching
Unburned control sites were identified through a moving-window grid search matching treatment geometry and covariate balance across 9 confounders: accessibility (travel time to cities), trail density, elevation, slope, temperature, precipitation, tree cover, shrub cover, and grass cover. Sites were required to be unburned since 2010 and located on public lands at least 50 miles from treatment sites to minimize spillover effects.

### Visitation Modeling
Machine learning models were trained on monthly visitation counts from 16 Colorado sites and 27 California sites using digital mobility proxies (Flickr uploads, eBird observations, AllTrails reviews, mobile phone location data), weather variables, landscape attributes, and recreation facilities. Feature selection via Boruta algorithm identified 66-69 most predictive variables per state. Models were validated using grouped cross-validation (holding out entire sites) to ensure out-of-sample predictive performance.

### Causal Analysis
Dynamic difference-in-differences event study design estimated fire effects relative to month t=-2 as reference period (conservative buffer against ignition date uncertainty). Colorado analysis used two-way fixed effects with site and month fixed effects. California analysis used Sun-Abraham interaction-weighted estimator with season-by-year cohort fixed effects to address treatment effect heterogeneity. Both models controlled for temperature and residual covariate imbalance through explicit regression adjustment (doubly robust approach).

### Fire Severity Classification
Fire severity quantified using bias-corrected Composite Burn Index (CBI) following Parks et al. 2019. Sites classified as high severity (>33% high-severity area), moderate severity (>33% moderate+high but ≤33% high), or low severity (otherwise). All grassland-dominated sites classified as low severity as CBI is forest-specific. Continuous severity measured via weighted CBI combining fractions of unburned, low, moderate, and high severity areas.

## Code and Reproducibility

All analysis code is written in Python with R used for robustness checks. Key packages include pyfixest (difference-in-differences), scikit-learn/xgboost/lightgbm (machine learning), geopandas (spatial analysis), and matplotlib/seaborn (visualization).

To reproduce the analysis, run scripts sequentially: (1) process fire perimeters and match control sites, (2) train visitation models, (3) run DiD analysis, (4) generate figures. Detailed instructions and environment specifications are provided in code directories.

## Data Availability

Due to file size constraints and data use agreements, raw data are not included in this repository. Processed analysis datasets and trained models are available from the lead author upon reasonable request. Data processing scripts and full provenance documentation are included to enable reproduction with original data sources.

## Contact

**Lead Author:** Kyle Manley (kyle.manley@colorado.edu)  
Earth Lab, University of Colorado Boulder

**Principal Investigators:**  
- Laura Dee (University of Colorado Boulder)
- Jennifer K. Balch (University of Colorado Boulder)
- Spencer Wood (University of Washington)

Questions, suggestions, or issues can be submitted via GitHub Issues or by contacting the lead author directly.

## Acknowledgments

This research was supported by the CIRES Visiting Fellowship Program and the MORPHO Rx Working Group. We thank the USFS, NPS, FWS, and BLM for providing visitation data, and the University of Washington Outdoor R&D Lab for curated recreation datasets. We are grateful to all co-authors and collaborators who contributed to this work.

## License

This project is licensed under the MIT License. See LICENSE file for details.


## How does fire impact public land visitation?

![Cultural Ecosystem Services Model](https://github.com/CU-ESIIL/CulturalES_WildfireRx/blob/main/Figures/concept_fig.png)

## How do quantify fire's imapct on recreation?

1. **Visitation Modeling**: Machine learning models trained with on-site visitation counts from federal and local agencies. Model performance: R² = 0.63-0.81 across states using Gradient Boosting (CA) and Extra Trees (CO) algorithms with predictors including mobility proxies, weather, landscape attributes, and recreation facilities.

2. **Causal Inference**: Difference-in-differences event study design comparing treated fire sites to matched unburned control sites. Matching of treatment and control sites based on 9 confounders (accessibility, trail density, elevation, slope, shrub cover, tree cover, grass cover, temperature, precipitation).

3. **Heterogeneity Analysis**: Effects stratified by fire size (small/medium/large), severity (CBI-based low/moderate/high), and vegetation type (grass/shrub/forest).

![Our Approach](https://github.com/CU-ESIIL/CulturalES_WildfireRx/blob/main/Figures/MethodsFigure.png)

## Collaborators and Co-Authors 
- Dr. Kyle Manley: Cooperative Institute for Research in Environmental Sciences; University of Colorado Boulder; Earth Lab
- Dr. Laura Dee: University of Colorado Boulder; Department of Ecology and Evolutionary Biology
- Dr. Jennifer Balch: The Environmental Data Science Innovation & Impact Lab; University of Colorado Boulder; Department of Geography
- Anna LoPresti: University of Colorado Boulder; Department of Ecology and Evolutionary Biology
- Dr. Cody Evers: Portland State University; Department of Environmental Science and Management
- Dr. Holly Nowell: Tall Timbers Research Station & Land Conservancy
- Dr. Spencer Wood: University of Washington; School of Environmental and Forest Sciences
- Dr. Katherine Siegel: Cooperative Institute for Research in Environmental Sciences; The Environmental Data Science Innovation & Impact Lab; University of Colorado Boulder; Department of Geography
- Dr. Jamie Peeler:  University of Montana; Department of Ecosystem and Conservation Sciences
- Tyler McIntosh: University of Colorado Boulder; Department of Geography; Department of Ecology and Evolutionary Biology
- Dr. Ash Cale: University of Nevada Reno; Department of Natural Resources and Environmental Sciences


