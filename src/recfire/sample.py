"""Build validated analysis panels from committed processed inputs."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .config import EXPECTED_FINAL_SITES, MONTHS_PRE_FIRE
from .io import load_feature_matrix, load_predictions, load_recreation_status
from .paths import fire_size_path


def _vegetation_class(row: pd.Series) -> str:
    values = {
        "grass": pd.to_numeric(row.get("grass_pct_mean"), errors="coerce"),
        "shrub": pd.to_numeric(row.get("shrub_pct_mean"), errors="coerce"),
        "tree": pd.to_numeric(row.get("tree_pct_mean"), errors="coerce"),
    }
    values = {k: (0.0 if pd.isna(v) else float(v)) for k, v in values.items()}
    if max(values.values()) <= 0:
        return "unknown"
    return max(values, key=values.get)


def _severity_class(row: pd.Series) -> str:
    if row.get("veg_type") == "grass":
        return "low"
    high = pd.to_numeric(row.get("pct_high_severity"), errors="coerce")
    moderate = pd.to_numeric(row.get("pct_moderate_severity"), errors="coerce")
    high = 0.0 if pd.isna(high) else float(high)
    moderate = 0.0 if pd.isna(moderate) else float(moderate)
    if high > 0.33:
        return "high"
    if high + moderate > 0.33:
        return "moderate"
    return "low"


def _add_size_classes(site_table: pd.DataFrame) -> tuple[pd.DataFrame, tuple[float, float] | None]:
    out = site_table.copy()
    if "fire_area_km2" not in out.columns or out.loc[out["treated"] == 1, "fire_area_km2"].isna().any():
        out["size_class"] = np.where(out["treated"].eq(0), "control", "unavailable")
        return out, None

    treated = out[out["treated"].eq(1)].copy()
    breaks = np.percentile(treated["fire_area_km2"].to_numpy(float), [33.33, 66.67])

    def classify(value: object) -> str:
        x = float(value)
        if x <= breaks[0]:
            return "small"
        if x <= breaks[1]:
            return "medium"
        return "large"

    out["size_class"] = out["fire_area_km2"].apply(
        lambda x: classify(x) if pd.notna(x) else "unavailable"
    )
    out.loc[out["treated"].eq(0), "size_class"] = "control"
    return out, (float(breaks[0]), float(breaks[1]))


def build_state_panel(state: str, validate: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, tuple[float, float] | None]:
    state = state.upper()
    pred = load_predictions(state)

    # Final analytic membership: valid event time and the common 12-month pre-period.
    panel = pred[pred["rel_month"].notna() & (pred["rel_month"] >= -MONTHS_PRE_FIRE)].copy()
    panel["rel_month"] = panel["rel_month"].astype(int)

    # Use the prediction on the scale produced by the selected visitation model.
    # No inverse transformation is applied before the event study.
    panel["outcome"] = pd.to_numeric(panel["y_pred"], errors="coerce")

    if "severity_class" in panel.columns:
        panel = panel.rename(columns={"severity_class": "severity_class_source"})

    fm = load_feature_matrix(state)

    # Monthly temperature is the time-varying adjustment variable used by the event study.
    monthly = fm[["siteid", "year", "month", "temperature_mean"]].drop_duplicates(
        ["siteid", "year", "month"]
    )
    panel = panel.merge(monthly, on=["siteid", "year", "month"], how="left", validate="many_to_one")

    static_cols = ["siteid", "tree_pct_mean", "shrub_pct_mean", "grass_pct_mean"]
    static = fm[static_cols].groupby("siteid", as_index=False).first()

    rec = load_recreation_status()
    rec = rec[rec["state"].eq(state)][["siteid", "recreation_status"]].drop_duplicates("siteid")
    static = static.merge(rec, on="siteid", how="left", validate="one_to_one")

    meta = panel[["siteid", "treatment_group", "fire_type", "treated"]].drop_duplicates("siteid")
    static = meta.merge(static, on="siteid", how="left", validate="one_to_one")
    static["veg_type"] = static.apply(_vegetation_class, axis=1)

    severity_columns = [
        c
        for c in [
            "siteid",
            "pct_unburned",
            "pct_low_severity",
            "pct_moderate_severity",
            "pct_high_severity",
            "cbi_weighted",
            "severity_class_source",
        ]
        if c in panel.columns
    ]
    severity = panel[severity_columns].groupby("siteid", as_index=False).first()
    static = static.merge(severity, on="siteid", how="left", validate="one_to_one")
    static["severity_class"] = static.apply(_severity_class, axis=1)

    if not fire_size_path().exists():
        raise FileNotFoundError(
            f"Required fire-size table not found: {fire_size_path()}. "
            "Run scripts/02_calculate_fire_size.py first."
        )
    fire_size = pd.read_csv(fire_size_path())
    fire_size["siteid"] = fire_size["siteid"].astype(str).str.strip().str.upper()
    fire_size = fire_size[fire_size["state"].astype(str).str.upper().eq(state)][
        ["siteid", "fire_area_km2"]
    ]
    static = static.merge(fire_size, on="siteid", how="left", validate="one_to_one")

    static, size_breaks = _add_size_classes(static)

    panel = panel.merge(
        static[
            [
                "siteid",
                "tree_pct_mean",
                "shrub_pct_mean",
                "grass_pct_mean",
                "veg_type",
                "recreation_status",
                "severity_class",
                "fire_area_km2",
                "size_class",
            ]
        ],
        on="siteid",
        how="left",
        validate="many_to_one",
    )

    if validate:
        counts = static.groupby("treatment_group")["siteid"].nunique().to_dict()
        if counts != EXPECTED_FINAL_SITES[state]:
            raise AssertionError(
                f"Final {state} sample mismatch. Observed {counts}; expected {EXPECTED_FINAL_SITES[state]}."
            )
        if panel["outcome"].isna().any():
            raise AssertionError(f"{state}: missing model-scale outcome values")
        if panel["temperature_mean"].isna().any():
            n = int(panel["temperature_mean"].isna().sum())
            raise AssertionError(f"{state}: {n} rows missing temperature_mean after merge")

    return panel, static, size_breaks
