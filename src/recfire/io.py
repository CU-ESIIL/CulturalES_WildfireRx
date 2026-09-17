"""Input readers and treatment-label harmonization."""
from __future__ import annotations

import pandas as pd

from .paths import RECREATION_STATUS, feature_matrix_path, predictions_path


def normalize_siteid(values: pd.Series) -> pd.Series:
    return values.astype(str).str.strip().str.upper()


def classify_treatment_type(value: object, state: str) -> str:
    """Map state-specific treatment labels to a common four-group scheme."""
    if pd.isna(value):
        return "unknown"
    tt = str(value).strip().lower()
    state = state.upper()

    if state == "CO":
        mapping = {
            "fire": "wildfire_treated",
            "controlfire": "wildfire_control",
            "rx": "rx_treated",
            "controlrx": "rx_control",
        }
        return mapping.get(tt, "unknown")

    if "wildfire" in tt and "treated" in tt:
        return "wildfire_treated"
    if "wildfire" in tt and "control" in tt:
        return "wildfire_control"
    if "rx" in tt and "treated" in tt:
        return "rx_treated"
    if "rx" in tt and "control" in tt:
        return "rx_control"
    return "unknown"


def load_predictions(state: str) -> pd.DataFrame:
    state = state.upper()
    df = pd.read_csv(predictions_path(state), low_memory=False)
    df.columns = df.columns.str.strip().str.lower()
    df["siteid"] = normalize_siteid(df["siteid"])
    df["treatment_group"] = df["treatment_type"].apply(
        lambda x: classify_treatment_type(x, state)
    )
    df["treated"] = df["treatment_group"].str.endswith("_treated").astype(int)
    df["fire_type"] = df["treatment_group"].map(
        {
            "wildfire_treated": "wildfire",
            "wildfire_control": "wildfire",
            "rx_treated": "prescribed",
            "rx_control": "prescribed",
        }
    )
    return df


def load_feature_matrix(state: str) -> pd.DataFrame:
    df = pd.read_csv(feature_matrix_path(state), low_memory=False)
    df.columns = df.columns.str.strip().str.lower()
    df["siteid"] = normalize_siteid(df["siteid"])
    return df


def load_recreation_status() -> pd.DataFrame:
    df = pd.read_csv(RECREATION_STATUS)
    df.columns = df.columns.str.strip().str.lower()
    df["siteid"] = normalize_siteid(df["siteid"])
    df["state"] = df["state"].astype(str).str.upper()
    return df
