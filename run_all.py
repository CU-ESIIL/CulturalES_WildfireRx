#!/usr/bin/env python3
"""Run the complete analysis workflow."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = [
    "01_validate_inputs.py",
    "02_calculate_fire_size.py",
    "03_build_analysis_data.py",
    "04_describe_sample.py",
    "05_estimate_firetype.py",
    "06_estimate_heterogeneity.py",
    "07_plot_firetype.py",
    "08_plot_heterogeneity.py",
    "09_continuous_response_functions.py",
]

for step in STEPS:
    print(f"\n{'=' * 72}\nRUNNING {step}\n{'=' * 72}", flush=True)
    subprocess.run([sys.executable, str(ROOT / "scripts" / step)], check=True)
