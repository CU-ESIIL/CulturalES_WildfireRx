#!/usr/bin/env python3
"""Estimate overall wildfire and prescribed-fire effects by state."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import pandas as pd

from recfire.config import CONTROLS
from recfire.event_study import annual_percent_rows, estimate_event_study
from recfire.paths import TABLES, ensure_output_dirs, panel_path


def main() -> None:
    ensure_output_dirs()
    rows = []

    for state in ("CO", "CA"):
        data = pd.read_csv(panel_path(state))

        for fire_type in ("wildfire", "prescribed"):
            result = estimate_event_study(data, fire_type, controls=CONTROLS)
            if result is None:
                continue

            for row in annual_percent_rows(result):
                rows.append(
                    {
                        "state": state,
                        "fire_type": fire_type,
                        "year": row["year"],
                        "effect_pct": row["effect_pct"],
                        "ci_lower": row["ci_lower"],
                        "ci_upper": row["ci_upper"],
                        "n_treated": result["n_treated_total"],
                        "n_control": result["n_control_total"],
                    }
                )

    out = pd.DataFrame(rows)
    path = TABLES / "did_results_firetype.csv"
    out.to_csv(path, index=False)
    print(out.to_string(index=False))
    print(f"\nSaved {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
