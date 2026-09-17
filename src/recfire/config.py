"""Central analysis settings."""

MONTHS_PRE_FIRE = 12
REFERENCE_MONTH = -2
MIN_SAMPLE_PERCENT = 0.10
CONTROLS = ["temperature_mean"]
EQUAL_AREA_CRS = "EPSG:5070"

EXPECTED_FINAL_SITES = {
    "CO": {
        "wildfire_treated": 44,
        "wildfire_control": 40,
        "rx_treated": 22,
        "rx_control": 22,
    },
    "CA": {
        "wildfire_treated": 141,
        "wildfire_control": 142,
        "rx_treated": 32,
        "rx_control": 35,
    },
}
