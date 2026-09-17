"""Repository-relative paths used by the analysis."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
FIRE_PERIMETERS = DATA / "01_fire_perimeters"
SITE_FEATURES = DATA / "02_site_features"
VISITATION = DATA / "03_visitation"
DERIVED = DATA / "04_analysis"
OUTPUTS = ROOT / "outputs"
TABLES = OUTPUTS / "tables"
FIGURES = OUTPUTS / "figures"
RECREATION_STATUS = SITE_FEATURES / "siteid_recreation_status.csv"


def ensure_output_dirs() -> None:
    for p in (DERIVED, TABLES, FIGURES):
        p.mkdir(parents=True, exist_ok=True)


def predictions_path(state: str) -> Path:
    return VISITATION / f"TreatCon_Pred_{state.upper()}.csv"


def feature_matrix_path(state: str) -> Path:
    return SITE_FEATURES / f"fire_feature_matrix_{state.upper()}.csv"


def treatment_perimeter_path(state: str) -> Path:
    return FIRE_PERIMETERS / f"{state.upper()}_treatment_perimeters.gpkg"


def fire_size_path() -> Path:
    return DERIVED / "fire_size_by_site.csv"


def panel_path(state: str) -> Path:
    return DERIVED / f"analysis_panel_{state.upper()}.csv"


def site_table_path(state: str) -> Path:
    return DERIVED / f"site_characteristics_{state.upper()}.csv"
