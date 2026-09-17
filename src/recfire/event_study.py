"""Sun-Abraham event-study estimation and annual aggregation."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import MIN_SAMPLE_PERCENT, MONTHS_PRE_FIRE, REFERENCE_MONTH


def estimate_event_study(
    data: pd.DataFrame,
    fire_type: str,
    controls: list[str] | None = None,
    subgroup_col: str | None = None,
    subgroup_value: str | None = None,
):
    """Estimate one saturated Sun-Abraham event study.

    Subgroup models restrict treated sites to the requested stratum while
    retaining the full matched never-treated control pool for that fire type.
    """
    try:
        import pyfixest as pf
    except ImportError as exc:
        raise ImportError("Install dependencies with `pip install -e .`") from exc

    controls = controls or []
    panel = data[data["fire_type"].eq(fire_type)].copy()
    full_control = panel[panel["treated"].eq(0)].copy()

    if subgroup_col is not None:
        treated = panel[
            panel["treated"].eq(1) & panel[subgroup_col].eq(subgroup_value)
        ].copy()
        panel = pd.concat([treated, full_control], ignore_index=True)

    panel = panel[panel["rel_month"].notna() & (panel["rel_month"] >= -MONTHS_PRE_FIRE)].copy()
    panel["rel_month"] = panel["rel_month"].astype(int)

    n_treated_total = panel.loc[panel["treated"].eq(1), "siteid"].nunique()
    n_control_total = panel.loc[panel["treated"].eq(0), "siteid"].nunique()
    if n_treated_total < 2 or n_control_total < 1:
        return None

    missing_controls = [c for c in controls if c not in panel.columns]
    if missing_controls:
        raise KeyError(f"Missing required event-study controls: {missing_controls}")
    if controls and panel[controls].isna().any().any():
        missing = panel[controls].isna().sum()
        missing = missing[missing.gt(0)].to_dict()
        raise ValueError(f"Event-study controls contain missing values: {missing}")

    baseline = panel.loc[
        panel["treated"].eq(1) & panel["rel_month"].lt(0), "outcome"
    ].mean()
    if pd.isna(baseline) or baseline == 0:
        raise ValueError("Pre-treatment mean outcome is missing or zero; percent scaling is undefined")

    panel["year_month_int"] = panel["year"].astype(int) * 12 + panel["month"].astype(int)
    treated_sites = panel.loc[panel["treated"].eq(1), "siteid"].unique()
    cohort: dict[str, int] = {}
    for siteid in treated_sites:
        values = panel.loc[
            panel["siteid"].eq(siteid) & panel["rel_month"].eq(0), "year_month_int"
        ]
        if len(values):
            cohort[siteid] = int(values.iloc[0])

    panel["cohort"] = panel["siteid"].map(cohort)
    panel.loc[panel["treated"].eq(0), "cohort"] = np.nan
    panel = panel[~(panel["treated"].eq(1) & panel["cohort"].isna())].copy()

    treated_by_month = (
        panel[panel["treated"].eq(1)]
        .groupby("rel_month")["siteid"]
        .agg(lambda x: tuple(pd.unique(x)))
        .to_dict()
    )
    controls_by_month = (
        panel[panel["treated"].eq(0)]
        .groupby("rel_month")["siteid"]
        .agg(lambda x: tuple(pd.unique(x)))
        .to_dict()
    )

    xfml = " + ".join(controls) if controls else None
    fit = pf.event_study(
        data=panel,
        yname="outcome",
        idname="siteid",
        tname="year_month_int",
        gname="cohort",
        xfml=xfml,
        estimator="saturated",
    )
    aggregate = fit.aggregate(weighting="shares")

    effects: dict[int, dict[str, object]] = {}
    for relative_time, row in aggregate.iterrows():
        month = int(round(float(relative_time)))
        estimate = float(row["Estimate"])
        se = float(row["Std. Error"])
        effects[month] = {
            "coef": estimate,
            "se": se,
            "ci_lower": estimate - 1.96 * se,
            "ci_upper": estimate + 1.96 * se,
            "treated_sites": treated_by_month.get(month, tuple()),
            "control_sites": controls_by_month.get(month, tuple()),
        }

    if REFERENCE_MONTH not in effects:
        effects[REFERENCE_MONTH] = {
            "coef": 0.0,
            "se": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "treated_sites": treated_by_month.get(REFERENCE_MONTH, tuple()),
            "control_sites": controls_by_month.get(REFERENCE_MONTH, tuple()),
        }

    return {
        "monthly": dict(sorted(effects.items())),
        "baseline": float(baseline),
        "n_treated_total": int(n_treated_total),
        "n_control_total": int(n_control_total),
        "controls": tuple(controls),
    }


def annual_percent_rows(result: dict) -> list[dict[str, object]]:
    """Aggregate monthly effects to years and express them relative to the pre-fire mean."""
    monthly = result["monthly"]
    frame = pd.DataFrame.from_dict(monthly, orient="index")
    frame.index = frame.index.astype(int)

    peak_n = max(len(v) for v in frame["treated_sites"])
    minimum_n = max(1, int(np.floor(peak_n * MIN_SAMPLE_PERCENT)))

    frame = frame[frame.index >= 0].copy()
    frame["n_treated"] = frame["treated_sites"].apply(len)
    frame["n_control"] = frame["control_sites"].apply(len)
    frame = frame[frame["n_treated"] >= minimum_n].copy()
    if frame.empty:
        return []

    frame["year"] = np.floor(frame.index / 12).astype(int) + 1
    frame.loc[frame["year"] > 5, "year"] = 5

    rows: list[dict[str, object]] = []
    baseline = float(result["baseline"])
    for year, group in frame.groupby("year"):
        weights = 1 / (group["se"].astype(float) ** 2 + 1e-10)
        weights = weights / weights.sum()
        coef = float((group["coef"].astype(float) * weights).sum())
        se = float(1 / np.sqrt((1 / (group["se"].astype(float) ** 2 + 1e-10)).sum()))

        treated_union: set[str] = set()
        control_union: set[str] = set()
        for sites in group["treated_sites"]:
            treated_union.update(sites)
        for sites in group["control_sites"]:
            control_union.update(sites)

        rows.append(
            {
                "year": int(year),
                "effect_pct": 100 * coef / baseline,
                "ci_lower": 100 * (coef - 1.96 * se) / baseline,
                "ci_upper": 100 * (coef + 1.96 * se) / baseline,
                "n_treated": len(treated_union),
                "n_control": len(control_union),
                "n_months": int(len(group)),
            }
        )

    reference = monthly.get(REFERENCE_MONTH, {})
    rows.insert(
        0,
        {
            "year": 0,
            "effect_pct": 0.0,
            "ci_lower": 0.0,
            "ci_upper": 0.0,
            "n_treated": len(reference.get("treated_sites", tuple())),
            "n_control": len(reference.get("control_sites", tuple())),
            "n_months": 1,
        },
    )
    return rows
