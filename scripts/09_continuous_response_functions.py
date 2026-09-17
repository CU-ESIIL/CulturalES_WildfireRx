#!/usr/bin/env python3
"""Continuous fire-severity and fire-size moderator analyses.

This script reproduces the continuous moderator workflow used for the
supplementary response-function analyses. For each state and fire type, it:

1. standardizes weighted CBI and corrected fire area across treated sites;
2. estimates event-time treatment effects and treatment × moderator interactions;
3. aggregates monthly coefficients to Years 1–5;
4. saves a comprehensive baseline/interaction result table;
5. builds response-function coefficient and lookup tables for severity and size;
6. plots marginal response functions for Years 1, 3, and 5.

Fire size is the corrected treatment-polygon area calculated in EPSG:5070.
"""
from __future__ import annotations

import math
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from recfire.config import CONTROLS, MIN_SAMPLE_PERCENT, MONTHS_PRE_FIRE, REFERENCE_MONTH
from recfire.paths import FIGURES, TABLES, ensure_output_dirs, panel_path, site_table_path

warnings.filterwarnings("ignore", message=".*variables dropped due to multicollinearity.*")

PLOT_YEARS = (1, 3, 5)
MAX_EFFECT = 500
MIN_SITES = 10
MIN_LATE_SAMPLE_RATIO = 0.20

MODERATORS = {
    "severity": {
        "column": "cbi_weighted",
        "label": "Fire Severity (CBI)",
        "unit": "CBI",
    },
    "area": {
        "column": "fire_area_km2",
        "label": "Fire Size (km²)",
        "unit": "km²",
    },
}


YEAR_COLORS = {
    "wildfire": {1: "#F4A261", 3: "#D55E00", 5: "#8B3A00"},
    "prescribed": {1: "#5EBFA1", 3: "#009E73", 5: "#005C43"},
}

CBI_THRESHOLDS = {"Low": 0.1, "Moderate": 1.25, "High": 2.25}
SEVERITY_LOOKUP_VALUES = [0.1, 0.5, 1.0, 1.25, 1.5, 2.0, 2.25, 2.5, 2.75]
SIZE_PERCENTILES = [10, 25, 50, 75, 90]

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 600,
        "figure.dpi": 150,
        "font.family": "sans-serif",
    }
)


def safe_event_name(relative_month: int) -> str:
    return f"m{abs(relative_month)}" if relative_month < 0 else f"p{relative_month}"


def normal_two_sided_p(z_value: float) -> float:
    return math.erfc(abs(z_value) / math.sqrt(2.0))


def unique_treated_values(panel: pd.DataFrame, column: str) -> pd.Series:
    values = (
        panel.loc[panel["treated"].eq(1), ["siteid", column]]
        .drop_duplicates("siteid")[column]
    )
    return (
        pd.to_numeric(values, errors="coerce")
        .replace([np.inf, -np.inf], np.nan)
        .dropna()
    )


def annualize_continuous(
    baseline_monthly: dict[int, dict[str, float]],
    interaction_monthly: dict[int, dict[str, float]],
    treated_sites_by_month: dict[int, tuple[str, ...]],
    control_sites_by_month: dict[int, tuple[str, ...]],
) -> list[dict[str, object]]:
    """Aggregate monthly baseline and interaction terms to common annual windows."""
    common_months = sorted(set(baseline_monthly) & set(interaction_monthly))
    if not common_months:
        return []

    rows = []
    for month in common_months:
        rows.append(
            {
                "month": month,
                "base_coef": baseline_monthly[month]["coef"],
                "base_se": baseline_monthly[month]["se"],
                "int_coef": interaction_monthly[month]["coef"],
                "int_se": interaction_monthly[month]["se"],
                "treated_sites": treated_sites_by_month.get(month, tuple()),
                "control_sites": control_sites_by_month.get(month, tuple()),
            }
        )

    frame = pd.DataFrame(rows).set_index("month")
    frame["n_treated_month"] = frame["treated_sites"].apply(len)

    peak_n = int(frame["n_treated_month"].max())
    min_n = max(1, int(np.floor(peak_n * MIN_SAMPLE_PERCENT)))

    frame = frame[
        (frame.index >= 0)
        & frame["n_treated_month"].ge(min_n)
    ].copy()
    if frame.empty:
        return []

    frame["year"] = np.floor(frame.index / 12).astype(int) + 1
    frame.loc[frame["year"] > 5, "year"] = 5

    annual = []
    for year, group in frame.groupby("year"):
        base_inv_var = 1.0 / (group["base_se"].astype(float) ** 2 + 1e-10)
        base_w = base_inv_var / base_inv_var.sum()
        base_coef = float((group["base_coef"].astype(float) * base_w).sum())
        base_se = float(1.0 / np.sqrt(base_inv_var.sum()))

        int_inv_var = 1.0 / (group["int_se"].astype(float) ** 2 + 1e-10)
        int_w = int_inv_var / int_inv_var.sum()
        int_coef = float((group["int_coef"].astype(float) * int_w).sum())
        int_se = float(1.0 / np.sqrt(int_inv_var.sum()))

        treated_union: set[str] = set()
        control_union: set[str] = set()
        for sites in group["treated_sites"]:
            treated_union.update(map(str, sites))
        for sites in group["control_sites"]:
            control_union.update(map(str, sites))

        annual.append(
            {
                "year": int(year),
                "base_coef": base_coef,
                "base_se": base_se,
                "int_coef": int_coef,
                "int_se": int_se,
                "n_treated": len(treated_union),
                "n_control": len(control_union),
                "n_months": int(len(group)),
            }
        )

    return annual


def estimate_continuous_model(
    data: pd.DataFrame,
    state: str,
    fire_type: str,
    moderator: str,
) -> list[dict[str, object]]:
    """Estimate one state × fire-type × moderator continuous event-study model."""
    try:
        import pyfixest as pf
    except ImportError as exc:
        raise ImportError("Install repository dependencies with `pip install -e .`") from exc

    moderator_col = MODERATORS[moderator]["column"]
    if moderator_col not in data.columns:
        raise KeyError(f"{state}: analysis panel is missing {moderator_col}")

    panel = data[data["fire_type"].eq(fire_type)].copy()
    panel = panel[
        panel["rel_month"].notna()
        & panel["rel_month"].ge(-MONTHS_PRE_FIRE)
    ].copy()
    panel["rel_month"] = panel["rel_month"].astype(int)

    n_treated_total = int(panel.loc[panel["treated"].eq(1), "siteid"].nunique())
    n_control_total = int(panel.loc[panel["treated"].eq(0), "siteid"].nunique())
    if n_treated_total < 2 or n_control_total < 1:
        return []

    mod_values = unique_treated_values(panel, moderator_col)
    if len(mod_values) < 2:
        return []

    mod_mean = float(mod_values.mean())
    mod_sd = float(mod_values.std(ddof=1))
    mod_min = float(mod_values.min())
    mod_max = float(mod_values.max())
    if not np.isfinite(mod_sd) or mod_sd <= 0:
        return []

    panel["moderator_z"] = 0.0
    treated_mask = panel["treated"].eq(1)
    treated_values = pd.to_numeric(panel.loc[treated_mask, moderator_col], errors="coerce")
    panel.loc[treated_mask, "moderator_z"] = (treated_values - mod_mean) / mod_sd

    if panel.loc[treated_mask, "moderator_z"].isna().any():
        missing = (
            panel.loc[treated_mask & panel["moderator_z"].isna(), "siteid"]
            .drop_duplicates()
            .astype(str)
            .tolist()
        )
        raise ValueError(f"{state} {fire_type} {moderator}: missing moderator for {missing}")

    baseline_mean = float(
        panel.loc[
            panel["treated"].eq(1) & panel["rel_month"].lt(0),
            "outcome",
        ].mean()
    )
    if not np.isfinite(baseline_mean) or baseline_mean == 0:
        raise ValueError(f"{state} {fire_type}: pre-treatment mean outcome is undefined")

    missing_controls = [c for c in CONTROLS if c not in panel.columns]
    if missing_controls:
        raise KeyError(f"{state} {fire_type}: missing controls {missing_controls}")
    if CONTROLS and panel[CONTROLS].isna().any().any():
        raise ValueError(f"{state} {fire_type}: event-study controls contain missing values")

    panel["calendar_time"] = panel["year"].astype(int) * 12 + panel["month"].astype(int)

    treated_sites_by_month = (
        panel.loc[panel["treated"].eq(1)]
        .groupby("rel_month")["siteid"]
        .agg(lambda x: tuple(pd.unique(x.astype(str))))
        .to_dict()
    )
    control_sites_by_month = (
        panel.loc[panel["treated"].eq(0)]
        .groupby("rel_month")["siteid"]
        .agg(lambda x: tuple(pd.unique(x.astype(str))))
        .to_dict()
    )

    relative_months = sorted(int(v) for v in panel["rel_month"].unique())
    relative_months = [v for v in relative_months if v != REFERENCE_MONTH]

    baseline_cols: list[str] = []
    interaction_cols: list[str] = []
    baseline_to_month: dict[str, int] = {}
    interaction_to_month: dict[str, int] = {}

    for relative_month in relative_months:
        suffix = safe_event_name(relative_month)
        base_name = f"evt_{suffix}"
        int_name = f"evt_mod_{suffix}"

        event_indicator = (
            panel["treated"].eq(1)
            & panel["rel_month"].eq(relative_month)
        ).astype(int)

        panel[base_name] = event_indicator
        panel[int_name] = event_indicator * panel["moderator_z"]

        baseline_cols.append(base_name)
        interaction_cols.append(int_name)
        baseline_to_month[base_name] = relative_month
        interaction_to_month[int_name] = relative_month

    rhs = baseline_cols + interaction_cols + CONTROLS
    formula = f"outcome ~ {' + '.join(rhs)} | siteid + calendar_time"

    # This matches the original continuous-moderator implementation: site and
    # calendar-time fixed effects with HC1 inference and event-time interactions.
    fit = pf.feols(formula, data=panel, vcov="HC1")

    coefs = fit.coef().to_dict()
    ses = fit.se().to_dict()

    baseline_monthly: dict[int, dict[str, float]] = {}
    interaction_monthly: dict[int, dict[str, float]] = {}

    for name, value in coefs.items():
        if name in baseline_to_month:
            baseline_monthly[baseline_to_month[name]] = {
                "coef": float(value),
                "se": float(ses[name]),
            }
        elif name in interaction_to_month:
            interaction_monthly[interaction_to_month[name]] = {
                "coef": float(value),
                "se": float(ses[name]),
            }

    annual = annualize_continuous(
        baseline_monthly,
        interaction_monthly,
        treated_sites_by_month,
        control_sites_by_month,
    )

    rows: list[dict[str, object]] = []
    for item in annual:
        for effect_type, coef_key, se_key in [
            ("baseline", "base_coef", "base_se"),
            ("interaction", "int_coef", "int_se"),
        ]:
            coef_pct = 100.0 * float(item[coef_key]) / baseline_mean
            se_pct = 100.0 * float(item[se_key]) / baseline_mean
            z_stat = coef_pct / se_pct if se_pct > 0 else np.nan
            p_value = normal_two_sided_p(z_stat) if np.isfinite(z_stat) else np.nan

            rows.append(
                {
                    "state": state,
                    "moderator": moderator,
                    "fire_type": fire_type,
                    "effect_type": effect_type,
                    "year": int(item["year"]),
                    "coef_pct": coef_pct,
                    "se_pct": se_pct,
                    "ci_lower_pct": coef_pct - 1.96 * se_pct,
                    "ci_upper_pct": coef_pct + 1.96 * se_pct,
                    "p_value": p_value,
                    "mod_mean": mod_mean,
                    "mod_sd": mod_sd,
                    "mod_min": mod_min,
                    "mod_max": mod_max,
                    "n_treated": int(item["n_treated"]),
                    "n_control": int(item["n_control"]),
                    "n_treated_total": n_treated_total,
                    "n_control_total": n_control_total,
                    "n_months": int(item["n_months"]),
                }
            )

    return rows


def filter_for_response_functions(results: pd.DataFrame) -> pd.DataFrame:
    """Apply the same presentation filters used by the original response-function code."""
    out = results[
        results["coef_pct"].abs().le(MAX_EFFECT)
        & results["n_treated"].ge(MIN_SITES)
    ].copy()

    drop_index: set[int] = set()
    for keys, sub in out.groupby(["state", "moderator", "fire_type", "effect_type"]):
        year1 = sub[sub["year"].eq(1)]
        year5 = sub[sub["year"].eq(5)]
        if year1.empty or year5.empty:
            continue
        n_year1 = int(year1["n_treated"].iloc[0])
        n_year5 = int(year5["n_treated"].iloc[0])
        if n_year5 < MIN_LATE_SAMPLE_RATIO * n_year1:
            drop_index.update(year5.index.tolist())

    if drop_index:
        out = out.drop(index=list(drop_index))
    return out.reset_index(drop=True)


def combine_effects(results: pd.DataFrame, moderator: str) -> pd.DataFrame:
    base = results[
        results["effect_type"].eq("baseline")
        & results["moderator"].eq(moderator)
    ].copy()
    interaction = results[
        results["effect_type"].eq("interaction")
        & results["moderator"].eq(moderator)
    ].copy()

    return base.merge(
        interaction,
        on=["state", "moderator", "fire_type", "year"],
        suffixes=("_base", "_int"),
        validate="one_to_one",
    )


def response_at_value(row: pd.Series, value: float) -> tuple[float, float, float, float]:
    z = (value - float(row["mod_mean_base"])) / float(row["mod_sd_base"])
    est = float(row["coef_pct_base"]) + float(row["coef_pct_int"]) * z
    # Matches the original response-function code. This conservative approximation
    # omits covariance between the annual baseline and interaction coefficients.
    se = math.sqrt(
        float(row["se_pct_base"]) ** 2
        + (z * float(row["se_pct_int"])) ** 2
    )
    return est, se, est - 1.96 * se, est + 1.96 * se


def severity_class_from_cbi(cbi: float) -> str:
    if cbi < 0.1:
        return "unburned"
    if cbi < 1.25:
        return "low"
    if cbi < 2.25:
        return "moderate"
    return "high"


def build_severity_tables(results: pd.DataFrame) -> None:
    combined = combine_effects(results, "severity")

    coefficients = combined[
        [
            "state",
            "fire_type",
            "year",
            "coef_pct_base",
            "se_pct_base",
            "coef_pct_int",
            "se_pct_int",
            "mod_mean_base",
            "mod_sd_base",
            "n_treated_base",
            "n_control_base",
        ]
    ].rename(
        columns={
            "coef_pct_base": "baseline_effect_pct",
            "se_pct_base": "baseline_se_pct",
            "coef_pct_int": "slope_per_sd_pct",
            "se_pct_int": "slope_per_sd_se_pct",
            "mod_mean_base": "mean_cbi",
            "mod_sd_base": "sd_cbi",
            "n_treated_base": "n_treated",
            "n_control_base": "n_control",
        }
    )
    coefficients["slope_per_cbi_unit_pct"] = (
        coefficients["slope_per_sd_pct"] / coefficients["sd_cbi"]
    )
    coefficients["slope_per_cbi_unit_se_pct"] = (
        coefficients["slope_per_sd_se_pct"] / coefficients["sd_cbi"]
    )
    coefficients = coefficients[
        [
            "state",
            "fire_type",
            "year",
            "baseline_effect_pct",
            "baseline_se_pct",
            "slope_per_cbi_unit_pct",
            "slope_per_cbi_unit_se_pct",
            "slope_per_sd_pct",
            "slope_per_sd_se_pct",
            "mean_cbi",
            "sd_cbi",
            "n_treated",
            "n_control",
        ]
    ].sort_values(["state", "fire_type", "year"])
    coefficients.to_csv(TABLES / "severity_response_function_coefficients.csv", index=False)

    lookup_rows = []
    for _, row in combined.iterrows():
        for cbi in SEVERITY_LOOKUP_VALUES:
            est, se, lo, hi = response_at_value(row, cbi)
            lookup_rows.append(
                {
                    "state": row["state"],
                    "fire_type": row["fire_type"],
                    "year": int(row["year"]),
                    "cbi": cbi,
                    "severity_class": severity_class_from_cbi(cbi),
                    "effect_pct": est,
                    "se_pct": se,
                    "ci_lower_pct": lo,
                    "ci_upper_pct": hi,
                }
            )
    pd.DataFrame(lookup_rows).to_csv(
        TABLES / "severity_response_function_lookup.csv",
        index=False,
    )

    focus_rows = []
    levels = [("Low", 0.5), ("Moderate", 1.75), ("High", 2.5)]
    for _, row in combined[combined["fire_type"].eq("wildfire")].iterrows():
        if int(row["year"]) not in PLOT_YEARS:
            continue
        for label, cbi in levels:
            est, _, lo, hi = response_at_value(row, cbi)
            focus_rows.append(
                {
                    "state": row["state"],
                    "year": int(row["year"]),
                    "severity": label,
                    "cbi": cbi,
                    "effect_pct": est,
                    "ci_lower_pct": lo,
                    "ci_upper_pct": hi,
                }
            )
    pd.DataFrame(focus_rows).to_csv(
        TABLES / "severity_response_function_wildfire_summary.csv",
        index=False,
    )


def size_distribution_table(panels: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for state, panel in panels.items():
        treated = panel[panel["treated"].eq(1)][
            ["siteid", "fire_type", "fire_area_km2", "size_class"]
        ].drop_duplicates("siteid")
        for fire_type, sub in treated.groupby("fire_type"):
            values = pd.to_numeric(sub["fire_area_km2"], errors="coerce").dropna()
            for percentile in SIZE_PERCENTILES:
                rows.append(
                    {
                        "state": state,
                        "fire_type": fire_type,
                        "percentile": percentile,
                        "fire_area_km2": float(np.percentile(values, percentile)),
                    }
                )
    return pd.DataFrame(rows)


def build_size_tables(results: pd.DataFrame, panels: dict[str, pd.DataFrame]) -> None:
    combined = combine_effects(results, "area")

    coefficients = combined[
        [
            "state",
            "fire_type",
            "year",
            "coef_pct_base",
            "se_pct_base",
            "coef_pct_int",
            "se_pct_int",
            "mod_mean_base",
            "mod_sd_base",
            "n_treated_base",
            "n_control_base",
        ]
    ].rename(
        columns={
            "coef_pct_base": "baseline_effect_pct",
            "se_pct_base": "baseline_se_pct",
            "coef_pct_int": "slope_per_sd_pct",
            "se_pct_int": "slope_per_sd_se_pct",
            "mod_mean_base": "mean_fire_area_km2",
            "mod_sd_base": "sd_fire_area_km2",
            "n_treated_base": "n_treated",
            "n_control_base": "n_control",
        }
    )
    coefficients["slope_per_km2_pct"] = (
        coefficients["slope_per_sd_pct"] / coefficients["sd_fire_area_km2"]
    )
    coefficients["slope_per_km2_se_pct"] = (
        coefficients["slope_per_sd_se_pct"] / coefficients["sd_fire_area_km2"]
    )
    coefficients = coefficients[
        [
            "state",
            "fire_type",
            "year",
            "baseline_effect_pct",
            "baseline_se_pct",
            "slope_per_km2_pct",
            "slope_per_km2_se_pct",
            "slope_per_sd_pct",
            "slope_per_sd_se_pct",
            "mean_fire_area_km2",
            "sd_fire_area_km2",
            "n_treated",
            "n_control",
        ]
    ].sort_values(["state", "fire_type", "year"])
    coefficients.to_csv(TABLES / "size_response_function_coefficients.csv", index=False)

    distribution = size_distribution_table(panels)
    lookup_rows = []
    for _, row in combined.iterrows():
        values = distribution[
            distribution["state"].eq(row["state"])
            & distribution["fire_type"].eq(row["fire_type"])
        ]
        for _, point in values.iterrows():
            size = float(point["fire_area_km2"])
            est, se, lo, hi = response_at_value(row, size)
            lookup_rows.append(
                {
                    "state": row["state"],
                    "fire_type": row["fire_type"],
                    "year": int(row["year"]),
                    "size_percentile": int(point["percentile"]),
                    "fire_area_km2": size,
                    "effect_pct": est,
                    "se_pct": se,
                    "ci_lower_pct": lo,
                    "ci_upper_pct": hi,
                }
            )
    pd.DataFrame(lookup_rows).to_csv(
        TABLES / "size_response_function_lookup.csv",
        index=False,
    )

    # Wildfire summary evaluated at the median corrected area within each
    # categorical size class. This directly links the continuous response to the
    # corrected small / medium / large groupings in the manuscript.
    representative_rows = []
    for state, panel in panels.items():
        sites = panel[
            panel["treated"].eq(1) & panel["fire_type"].eq("wildfire")
        ][["siteid", "size_class", "fire_area_km2"]].drop_duplicates("siteid")
        for size_class, sub in sites.groupby("size_class"):
            representative_rows.append(
                {
                    "state": state,
                    "size_class": size_class,
                    "fire_area_km2": float(sub["fire_area_km2"].median()),
                }
            )
    representative = pd.DataFrame(representative_rows)

    focus_rows = []
    for _, row in combined[combined["fire_type"].eq("wildfire")].iterrows():
        if int(row["year"]) not in PLOT_YEARS:
            continue
        reps = representative[representative["state"].eq(row["state"])]
        for _, rep in reps.iterrows():
            size = float(rep["fire_area_km2"])
            est, _, lo, hi = response_at_value(row, size)
            focus_rows.append(
                {
                    "state": row["state"],
                    "year": int(row["year"]),
                    "size_class": rep["size_class"],
                    "representative_fire_area_km2": size,
                    "effect_pct": est,
                    "ci_lower_pct": lo,
                    "ci_upper_pct": hi,
                }
            )
    pd.DataFrame(focus_rows).sort_values(
        ["state", "year", "size_class"]
    ).to_csv(
        TABLES / "size_response_function_wildfire_summary.csv",
        index=False,
    )


def build_curve_table(results: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for moderator in ("severity", "area"):
        combined = combine_effects(results, moderator)
        for _, row in combined.iterrows():
            if int(row["year"]) not in PLOT_YEARS:
                continue

            mean = float(row["mod_mean_base"])
            sd = float(row["mod_sd_base"])
            observed_min = float(row["mod_min_base"])
            observed_max = float(row["mod_max_base"])

            if moderator == "severity":
                plot_min, plot_max = 0.0, 3.0
            else:
                plot_min = max(0.0, observed_min, mean - 2 * sd)
                plot_max = min(observed_max, mean + 2 * sd)
                if plot_max <= plot_min:
                    plot_min, plot_max = observed_min, observed_max

            for value in np.linspace(plot_min, plot_max, 200):
                est, se, lo, hi = response_at_value(row, float(value))
                rows.append(
                    {
                        "state": row["state"],
                        "fire_type": row["fire_type"],
                        "moderator": moderator,
                        "year": int(row["year"]),
                        "moderator_value": float(value),
                        "effect_pct": est,
                        "se_pct": se,
                        "ci_lower_pct": lo,
                        "ci_upper_pct": hi,
                        "mod_mean": mean,
                        "mod_sd": sd,
                    }
                )
    return pd.DataFrame(rows)


def plot_response_function(
    ax,
    combined: pd.DataFrame,
    state: str,
    fire_type: str,
    moderator: str,
) -> None:
    sub = combined[
        combined["state"].eq(state)
        & combined["fire_type"].eq(fire_type)
    ]
    if sub.empty:
        ax.axis("off")
        return

    mean = float(sub["mod_mean_base"].iloc[0])
    sd = float(sub["mod_sd_base"].iloc[0])
    observed_min = float(sub["mod_min_base"].iloc[0])
    observed_max = float(sub["mod_max_base"].iloc[0])
    n = int(sub["n_treated_total_base"].iloc[0])

    if moderator == "severity":
        x_min = max(0.0, observed_min)
        x_max = min(3.0, observed_max)
    else:
        x_min = max(0.0, observed_min)
        x_max = observed_max

    if x_max <= x_min:
        x_min, x_max = observed_min, observed_max

    x_values = np.linspace(x_min, x_max, 200)

    for year in PLOT_YEARS:
        yr = sub[sub["year"].eq(year)]
        if yr.empty:
            continue
        row = yr.iloc[0]
        z = (x_values - mean) / sd
        est = float(row["coef_pct_base"]) + float(row["coef_pct_int"]) * z
        se = np.sqrt(
            float(row["se_pct_base"]) ** 2
            + (z * float(row["se_pct_int"])) ** 2
        )
        color = YEAR_COLORS[fire_type][year]
        ax.plot(x_values, est, color=color, linewidth=2.5, label=f"Year {year}", zorder=10)
        ax.fill_between(x_values, est - 1.96 * se, est + 1.96 * se, color=color, alpha=0.15, zorder=5)

    support_lo = max(x_min, mean - 2 * sd)
    support_hi = min(x_max, mean + 2 * sd)

    # Gray tails indicate moderator values more than 2 SD from the treated-site mean.
    # Estimates are shown for completeness but should be interpreted cautiously.
    if x_min < support_lo:
        ax.axvspan(x_min, support_lo, color="#BDBDBD", alpha=0.22, zorder=1)
    if support_hi < x_max:
        ax.axvspan(support_hi, x_max, color="#BDBDBD", alpha=0.22, zorder=1)

    ax.axvline(mean, color="black", linestyle=":", linewidth=1.2, alpha=0.7, zorder=2)
    ax.axhline(0, color="black", linewidth=0.8, alpha=0.6, zorder=2)

    if moderator == "severity":
        for threshold in CBI_THRESHOLDS.values():
            ax.axvline(threshold, color="#888888", linestyle="--", linewidth=0.8, alpha=0.5, zorder=1)
        ax.set_xlim(0, 3)
        ax.set_xlabel("Fire Severity (weighted CBI)", fontsize=11, fontweight="bold")
    else:
        ax.set_xlim(x_min, x_max)
        ax.set_xlabel("Fire Size (km²)", fontsize=11, fontweight="bold")

    ax.set_ylabel("Estimated Change in Visitation (%)", fontsize=11, fontweight="bold")
    state_name = "Colorado" if state == "CO" else "California"
    fire_name = "Wildfire" if fire_type == "wildfire" else "Prescribed Fire"
    ax.set_title(f"{state_name} — {fire_name} (n = {n})", fontsize=12, fontweight="bold")
    ax.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax.grid(axis="y", alpha=0.25, linewidth=0.5)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def plot_response_grid(results: pd.DataFrame, moderator: str, filename: str) -> None:
    combined = combine_effects(results, moderator)
    fig, axes = plt.subplots(2, 2, figsize=(13, 10), sharey=False)
    fig.patch.set_facecolor("white")

    for i, state in enumerate(("CO", "CA")):
        for j, fire_type in enumerate(("wildfire", "prescribed")):
            plot_response_function(axes[i, j], combined, state, fire_type, moderator)

    if moderator == "severity":
        for ax in axes[0, :]:
            ylim = ax.get_ylim()
            y_annot = ylim[1] - (ylim[1] - ylim[0]) * 0.05
            for label, threshold in CBI_THRESHOLDS.items():
                ax.text(
                    threshold + 0.02,
                    y_annot,
                    label,
                    fontsize=8,
                    color="#666666",
                    style="italic",
                    va="top",
                )
        title = "Fire Severity and Recreational Visitation"
    else:
        title = "Fire Size and Recreational Visitation"

    fig.suptitle(title, fontsize=14, fontweight="bold", y=0.99)
    fig.text(
        0.5,
        0.01,
        "Colored bands = 95% CI   |   Dotted vertical line = treated-site mean   |   "
        "Gray area = >2 SD from the mean (limited support; interpret cautiously)",
        ha="center",
        va="bottom",
        fontsize=9,
        color="#555555",
    )
    plt.tight_layout(rect=[0, 0.04, 1, 0.96])
    fig.savefig(FIGURES / f"{filename}.png", dpi=600, bbox_inches="tight")
    fig.savefig(FIGURES / f"{filename}.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    ensure_output_dirs()

    panels: dict[str, pd.DataFrame] = {}
    result_rows: list[dict[str, object]] = []

    for state in ("CO", "CA"):
        path = panel_path(state)
        if not path.exists():
            raise FileNotFoundError(
                f"Missing {path.relative_to(ROOT)}. Run scripts/03_build_analysis_data.py first."
            )
        panel = pd.read_csv(path)
        panels[state] = panel

        for fire_type in ("wildfire", "prescribed"):
            for moderator in ("severity", "area"):
                print(f"Estimating {state} {fire_type} continuous {moderator} response...")
                result_rows.extend(
                    estimate_continuous_model(panel, state, fire_type, moderator)
                )

    comprehensive = pd.DataFrame(result_rows)
    if comprehensive.empty:
        raise RuntimeError("No continuous moderator estimates were produced.")

    comprehensive = comprehensive.sort_values(
        ["moderator", "state", "fire_type", "effect_type", "year"]
    ).reset_index(drop=True)
    comprehensive.to_csv(
        TABLES / "continuous_moderator_effects_comprehensive.csv",
        index=False,
    )

    presentation = filter_for_response_functions(comprehensive)
    build_severity_tables(presentation)
    build_size_tables(presentation, panels)

    curves = build_curve_table(presentation)
    curves.to_csv(TABLES / "continuous_response_function_curves.csv", index=False)

    plot_response_grid(
        presentation,
        moderator="severity",
        filename="FigS_Severity_Response_Functions",
    )
    plot_response_grid(
        presentation,
        moderator="area",
        filename="FigS_Size_Response_Functions",
    )

    print(f"Saved {TABLES.relative_to(ROOT) / 'continuous_moderator_effects_comprehensive.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'severity_response_function_coefficients.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'severity_response_function_lookup.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'severity_response_function_wildfire_summary.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'size_response_function_coefficients.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'size_response_function_lookup.csv'}")
    print(f"Saved {TABLES.relative_to(ROOT) / 'size_response_function_wildfire_summary.csv'}")
    print(f"Saved {FIGURES.relative_to(ROOT) / 'FigS_Severity_Response_Functions.png'}")
    print(f"Saved {FIGURES.relative_to(ROOT) / 'FigS_Size_Response_Functions.png'}")


if __name__ == "__main__":
    main()
