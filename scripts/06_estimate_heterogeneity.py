#!/usr/bin/env python3
"""Estimate treatment-effect heterogeneity."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from recfire.config import CONTROLS
from recfire.event_study import annual_percent_rows, estimate_event_study
from recfire.paths import TABLES, ensure_output_dirs, panel_path

STRATA = {
    "size": ("size_class", ["small", "medium", "large"]),
    "severity": ("severity_class", ["low", "moderate", "high"]),
    "vegetation": ("veg_type", ["grass", "shrub", "tree"]),
    "recreation": ("recreation_status", ["high_recreation", "non_recreation"]),
}


def main() -> None:
    ensure_output_dirs()
    rows = []

    for state in ("CO", "CA"):
        data = pd.read_csv(panel_path(state))
        required = {"siteid", "fire_type", "treated", "outcome", "temperature_mean"}
        required.update(col for col, _ in STRATA.values())
        missing = sorted(required.difference(data.columns))
        if missing:
            raise KeyError(f"{state}: analysis panel missing required columns: {missing}")

        for fire_type in ("wildfire", "prescribed"):
            for dimension, (column, values) in STRATA.items():
                for value in values:
                    n_treated = data.loc[
                        data["fire_type"].eq(fire_type)
                        & data["treated"].eq(1)
                        & data[column].eq(value),
                        "siteid",
                    ].nunique()

                    if n_treated < 2:
                        continue

                    result = estimate_event_study(
                        data,
                        fire_type,
                        controls=CONTROLS,
                        subgroup_col=column,
                        subgroup_value=value,
                    )
                    if result is None:
                        continue

                    for row in annual_percent_rows(result):
                        rows.append(
                            {
                                "state": state,
                                "fire_type": fire_type,
                                "stratification": dimension,
                                "stratum": value,
                                "year": row["year"],
                                "effect_pct": row["effect_pct"],
                                "ci_lower": row["ci_lower"],
                                "ci_upper": row["ci_upper"],
                                "n_treated": result["n_treated_total"],
                                "n_control": result["n_control_total"],
                            }
                        )

    out = pd.DataFrame(rows)
    path = TABLES / "did_heterogeneity_results.csv"
    out.to_csv(path, index=False)
    print(out.to_string(index=False))
    print(f"\nSaved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
