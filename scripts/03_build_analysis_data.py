#!/usr/bin/env python3
"""Build the state-specific analysis panels."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from recfire.paths import ensure_output_dirs, panel_path, site_table_path
from recfire.sample import build_state_panel


def main() -> None:
    ensure_output_dirs()

    for state in ("CO", "CA"):
        panel, sites, breaks = build_state_panel(state, validate=True)
        panel.to_csv(panel_path(state), index=False)
        sites.to_csv(site_table_path(state), index=False)

        print(f"{state}: wrote {panel_path(state).relative_to(ROOT)}")
        print(f"{state}: wrote {site_table_path(state).relative_to(ROOT)}")
        if breaks is not None:
            print(
                f"{state}: fire-size terciles = "
                f"{breaks[0]:.2f}, {breaks[1]:.2f} km²"
            )


if __name__ == "__main__":
    main()
