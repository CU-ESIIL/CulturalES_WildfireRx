#!/usr/bin/env python3
"""Validate the committed inputs required by the analysis."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import geopandas as gpd

from recfire.config import EXPECTED_FINAL_SITES, MONTHS_PRE_FIRE
from recfire.io import load_feature_matrix, load_predictions, normalize_siteid
from recfire.paths import treatment_perimeter_path


def main() -> None:
    for state in ("CO", "CA"):
        pred = load_predictions(state)
        fm = load_feature_matrix(state)
        final = pred[
            pred["rel_month"].notna() & (pred["rel_month"] >= -MONTHS_PRE_FIRE)
        ].copy()

        counts = final.groupby("treatment_group")["siteid"].nunique().to_dict()
        if counts != EXPECTED_FINAL_SITES[state]:
            raise AssertionError(
                f"{state}: observed final sample {counts}; expected {EXPECTED_FINAL_SITES[state]}"
            )

        perimeter_path = treatment_perimeter_path(state)
        if not perimeter_path.exists():
            raise FileNotFoundError(f"{state}: required perimeter file not found: {perimeter_path}")

        perimeters = gpd.read_file(perimeter_path)
        perimeters.columns = [str(c).strip().lower() for c in perimeters.columns]
        if "siteid" not in perimeters.columns:
            raise KeyError(f"{state}: perimeter file lacks siteid")
        if perimeters.crs is None:
            raise ValueError(f"{state}: perimeter file has no CRS")

        perimeters["siteid"] = normalize_siteid(perimeters["siteid"])
        final_treated_ids = set(final.loc[final["treated"].eq(1), "siteid"].unique())
        perimeter_ids = set(perimeters["siteid"].unique())
        if perimeter_ids != final_treated_ids:
            missing_ids = sorted(final_treated_ids - perimeter_ids)
            extra_ids = sorted(perimeter_ids - final_treated_ids)
            raise AssertionError(
                f"{state}: treatment perimeter IDs do not match the final treated sample; "
                f"missing={missing_ids[:10]}, extra={extra_ids[:10]}"
            )

        if "temperature_mean" not in fm.columns:
            raise KeyError(f"{state}: temperature_mean missing from feature matrix")

        monthly = fm[["siteid", "year", "month", "temperature_mean"]].drop_duplicates(
            ["siteid", "year", "month"]
        )
        check = final[["siteid", "year", "month"]].merge(
            monthly,
            on=["siteid", "year", "month"],
            how="left",
            validate="many_to_one",
        )
        missing_temp = int(check["temperature_mean"].isna().sum())
        if missing_temp:
            raise AssertionError(f"{state}: {missing_temp} analysis rows lack temperature_mean")

        print(f"{state}: inputs validated")


if __name__ == "__main__":
    main()
