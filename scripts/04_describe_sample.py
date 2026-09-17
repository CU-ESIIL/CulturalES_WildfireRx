#!/usr/bin/env python3
"""Summarize the final treated-site sample."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from recfire.paths import TABLES, ensure_output_dirs, site_table_path


def main() -> None:
    ensure_output_dirs()
    tables = []
    for state in ("CO", "CA"):
        df = pd.read_csv(site_table_path(state))
        df = df[df["treated"].eq(1)].copy()
        df["state"] = state
        tables.append(df)
    treated = pd.concat(tables, ignore_index=True)

    rows = []
    for (state, fire_type), group in treated.groupby(["state", "fire_type"]):
        severity = group["severity_class"].value_counts()
        row = {
            "state": state,
            "fire_type": fire_type,
            "n": group["siteid"].nunique(),
            "cbi_median": group["cbi_weighted"].median() if "cbi_weighted" in group else float("nan"),
            "cbi_q1": group["cbi_weighted"].quantile(0.25) if "cbi_weighted" in group else float("nan"),
            "cbi_q3": group["cbi_weighted"].quantile(0.75) if "cbi_weighted" in group else float("nan"),
            "n_low_severity": int(severity.get("low", 0)),
            "n_moderate_severity": int(severity.get("moderate", 0)),
            "n_high_severity": int(severity.get("high", 0)),
        }
        if group["fire_area_km2"].notna().all():
            row.update(
                fire_area_median_km2=group["fire_area_km2"].median(),
                fire_area_q1_km2=group["fire_area_km2"].quantile(0.25),
                fire_area_q3_km2=group["fire_area_km2"].quantile(0.75),
            )
        else:
            row.update(
                fire_area_median_km2=float("nan"),
                fire_area_q1_km2=float("nan"),
                fire_area_q3_km2=float("nan"),
            )
        rows.append(row)

    summary = pd.DataFrame(rows).sort_values(["state", "fire_type"])
    summary.to_csv(TABLES / "fire_characteristics_summary.csv", index=False)
    print(summary.to_string(index=False, float_format=lambda x: f"{x:.2f}"))

    if treated["size_class"].isin(["small", "medium", "large"]).any():
        size_counts = (
            treated[treated["size_class"].isin(["small", "medium", "large"])]
            .groupby(["state", "fire_type", "size_class"])["siteid"]
            .nunique()
            .rename("n")
            .reset_index()
        )
        size_counts.to_csv(TABLES / "size_class_counts.csv", index=False)
        print("\nSize classes:")
        print(size_counts.to_string(index=False))


if __name__ == "__main__":
    main()
