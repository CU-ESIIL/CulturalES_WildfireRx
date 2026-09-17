#!/usr/bin/env python3
"""Calculate treatment area from the committed final treatment polygons."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from recfire.fire_size import calculate_fire_size_table


def main() -> None:
    table = calculate_fire_size_table()
    print("FIRE SIZE FROM FINAL TREATMENT POLYGONS")
    print("=" * 72)
    print(table.groupby("state")["fire_area_km2"].describe().to_string())


if __name__ == "__main__":
    main()
