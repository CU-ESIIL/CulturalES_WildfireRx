# Fire and Recreation in the U.S. West: Modeling Impacts of Wildfire and Prescribed Fire on Nature's Non-Material Contributions to People

**A comprehensive analysis of fire effects on public land visitation across California and Colorado (2020-2024)**

This repository contains code and data for quantifying how wildfire and prescribed fire reshape recreational visitation on public lands. Recreation is among the most prominent non-material contributions of nature (cultural ecosystem services) to human well-being, supporting local economies, cultural connection, and place-based values across the western United States. This work is part of the [MORPHO Rx Working Group](https://rx-char.github.io/) and a Cooperative Institute for Research in Environmental Sciences [Visiting Fellowship Program project](https://cires.colorado.edu/people/kyle-manley).

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

![Cultural Ecosystem Services Model](https://github.com/CU-ESIIL/CulturalES_WildfireRx/blob/main/outputs/figures/concept_fig.png)

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

## How do quantify fire's imapct on recreation?

1. **Visitation Modeling**: Machine learning models trained with on-site visitation counts from federal and local agencies. Model performance: R² = 0.63-0.81 across states using Gradient Boosting (CA) and Extra Trees (CO) algorithms with predictors including mobility proxies, weather, landscape attributes, and recreation facilities.

2. **Causal Inference**: Treatment sites (wildfires and prescribed fires) matched on confoudning varaibles with unburned control sites based on 9 confounders (accessibility, trail density, elevation, slope, shrub cover, tree cover, grass cover, temperature, precipitation). Dynamic difference-in-differences event study design estimated fire effects.

3. **Heterogeneity Analysis**: Effects stratified by fire size (small/medium/large), severity (CBI-based low/moderate/high), and vegetation type (grass/shrub/forest).

![Our Approach](https://github.com/CU-ESIIL/CulturalES_WildfireRx/blob/main/outputs/figures/MethodsFigure.png)

## Code and Reproducibility

All analysis code is written in Python. Key packages include pyfixest (difference-in-differences), scikit-learn/xgboost/lightgbm (machine learning), geopandas (spatial analysis), and matplotlib/seaborn (visualization).

## Contact

**Lead Author:** Kyle Manley (kyle.manley@colorado.edu)  
CIRES, Earth Lab, University of Colorado Boulder

**Collaborators:** 
- Kyle Manley: Cooperative Institute for Research in Environmental Sciences; University of Colorado Boulder; Earth Lab
- Spencer Wood: University of Washington; School of Environmental and Forest Sciences; Outdoor Recreation & Data Lab
- Cody Evers: Portland State University; Department of Environmental Science and Management
- Holly Nowell: Tall Timbers Research Station & Land Conservancy
- Katherine Siegel: Cooperative Institute for Research in Environmental Sciences; The Environmental Data Science Innovation & Impact Lab; University of Colorado Boulder; Department of Geography
- Jennifer Balch: The Environmental Data Science Innovation & Impact Lab; University of Colorado Boulder; Department of Geography
- Laura Braun: University of Washington; Outdoor Recreation & Data Lab
- Ash Cale: University of Nevada Reno; Department of Natural Resources and Environmental Sciences
- Jason Kreitler: U.S. Geological Survey, Western Geographic Science Center
- Anna LoPresti: University of Colorado Boulder; Department of Ecology and Evolutionary Biology
- Tyler McIntosh: University of Colorado Boulder; Department of Geography; Department of Ecology and Evolutionary Biology
- Jamie Peeler:  University of Montana; Department of Ecosystem and Conservation Sciences
- Miguel Villarreal: U.S. Geological Survey, Western Geographic Science Center
- Laura Dee: University of Colorado Boulder; Department of Ecology and Evolutionary Biology

Questions, suggestions, or issues can be submitted via GitHub Issues or by contacting the lead author directly.

## Acknowledgments

This research was supported by the CIRES Visiting Fellowship Program and the MORPHO Rx Working Group. We thank the USFS, NPS, FWS, BLM, and Boulder OSMP for providing visitation data, and the University of Washington Outdoor R&D Lab for curated recreation datasets. We are grateful to all co-authors and collaborators who contributed to this work.

## License

This project is licensed under Creative Commons Attribution 4.0 International License (CC BY 4.0). See LICENSE file for details.





