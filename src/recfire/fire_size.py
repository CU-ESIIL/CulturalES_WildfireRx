"""Calculate fire size from final treatment-perimeter polygons."""
from __future__ import annotations

import geopandas as gpd
import pandas as pd

from .config import EQUAL_AREA_CRS, MONTHS_PRE_FIRE
from .io import load_predictions, normalize_siteid
from .paths import fire_size_path, treatment_perimeter_path


def calculate_fire_size_table() -> pd.DataFrame:
    """Calculate treatment area directly from the committed final polygons.

    Each state GeoPackage must contain a ``siteid`` field matching the final
    treated sites. Multiple polygon pieces for a site are dissolved before area
    is measured in EPSG:5070. The feature-matrix ``area_km2`` field is not used.
    """
    tables: list[pd.DataFrame] = []

    for state in ("CO", "CA"):
        path = treatment_perimeter_path(state)
        if not path.exists():
            raise FileNotFoundError(f"Required treatment-perimeter file not found: {path}")

        gdf = gpd.read_file(path)
        gdf.columns = [str(c).strip().lower() for c in gdf.columns]
        if "siteid" not in gdf.columns:
            raise KeyError(f"{path} must contain a siteid column")
        if gdf.crs is None:
            raise ValueError(f"{path} has no CRS; polygon area cannot be calculated safely")

        gdf["siteid"] = normalize_siteid(gdf["siteid"])
        gdf = gdf[gdf.geometry.notna() & ~gdf.geometry.is_empty].copy()

        predictions = load_predictions(state)
        final_treated = predictions[
            predictions["treated"].eq(1)
            & predictions["rel_month"].notna()
            & (predictions["rel_month"] >= -MONTHS_PRE_FIRE)
        ]["siteid"].drop_duplicates()
        final_ids = set(final_treated)

        available_ids = set(gdf["siteid"])
        missing_ids = sorted(final_ids.difference(available_ids))
        extra_ids = sorted(available_ids.difference(final_ids))
        if missing_ids:
            preview = ", ".join(missing_ids[:10])
            raise AssertionError(
                f"{state}: perimeter file is missing {len(missing_ids)} final treated site IDs "
                f"(first: {preview})."
            )
        if extra_ids:
            raise AssertionError(
                f"{state}: perimeter file contains {len(extra_ids)} IDs outside the final treated sample."
            )

        gdf = gdf.dissolve(by="siteid", as_index=False)
        gdf = gdf.to_crs(EQUAL_AREA_CRS)
        gdf["fire_area_km2"] = gdf.geometry.area / 1_000_000.0

        if (gdf["fire_area_km2"] <= 0).any():
            raise AssertionError(f"{state}: non-positive treatment area detected")

        out = gdf[["siteid", "fire_area_km2"]].copy()
        out.insert(0, "state", state)
        tables.append(out)

    result = pd.concat(tables, ignore_index=True)
    fire_size_path().parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(fire_size_path(), index=False)
    return result
