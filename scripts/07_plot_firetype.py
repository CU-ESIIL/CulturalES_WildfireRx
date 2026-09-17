#!/usr/bin/env python3
"""Plot overall wildfire and prescribed-fire effects."""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from recfire.paths import FIGURES, TABLES, ensure_output_dirs

warnings.filterwarnings("ignore")
logging.getLogger("fontTools").setLevel(logging.WARNING)
logging.getLogger("fontTools.subset").setLevel(logging.WARNING)

plt.rcParams.update(
    {
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "savefig.dpi": 600,
        "figure.dpi": 150,
        "font.family": "sans-serif",
    }
)

# Intuitive colorblind-safe colors used in the final manuscript figure.
FIRE_COLORS = {
    "wildfire": "#D55E00",      # vermillion
    "prescribed": "#009E73",    # teal
}


def plot_state(ax, df, state, state_name, panel_label, marker, show_ylabel):
    """Plot overall wildfire and prescribed-fire effects for one state."""
    for fire_type in ["wildfire", "prescribed"]:
        data = df[
            df["state"].eq(state) & df["fire_type"].eq(fire_type)
        ].sort_values("year")

        if data.empty:
            continue

        color = FIRE_COLORS[fire_type]
        linestyle = "-" if fire_type == "wildfire" else "--"
        linewidth = 3.0 if fire_type == "wildfire" else 2.5

        ax.plot(
            data["year"],
            data["effect_pct"],
            marker=marker,
            markersize=10,
            linewidth=linewidth,
            linestyle=linestyle,
            color=color,
            alpha=0.95,
            zorder=10,
        )

        ax.fill_between(
            data["year"],
            data["ci_lower"],
            data["ci_upper"],
            alpha=0.18,
            color=color,
            zorder=5,
        )

    ax.axhline(
        0,
        color="#333333",
        linestyle=":",
        linewidth=1.5,
        zorder=1,
    )

    ax.set_xlabel(
        "Years After Fire",
        fontsize=16,
        fontweight="bold",
    )

    if show_ylabel:
        ax.set_ylabel(
            "Change in Visitation (%)",
            fontsize=16,
            fontweight="bold",
        )

    ax.text(
        0.02,
        0.98,
        panel_label,
        transform=ax.transAxes,
        fontsize=20,
        fontweight="bold",
        va="top",
        ha="left",
    )

    ax.set_title(
        state_name,
        fontsize=17,
        fontweight="normal",
        pad=12,
        loc="left",
        x=0.08,
    )

    ax.set_xticks(range(6))
    ax.set_xticklabels(
        ["0", "1", "2", "3", "4", "5+"],
        fontsize=15,
    )
    ax.tick_params(axis="y", labelsize=15, which="both")

    ax.yaxis.grid(
        True,
        linestyle="-",
        linewidth=0.6,
        alpha=0.3,
        zorder=0,
    )
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["bottom"].set_linewidth(1.0)

    if show_ylabel:
        ax.spines["left"].set_linewidth(1.0)
    else:
        ax.spines["left"].set_visible(False)

    ax.set_xlim(-0.3, 5.3)


def main() -> None:
    ensure_output_dirs()
    df = pd.read_csv(TABLES / "did_results_firetype.csv")

    fig, (ax_co, ax_ca) = plt.subplots(
        1,
        2,
        figsize=(16, 6),
        sharey=True,
    )

    plot_state(
        ax_co,
        df,
        "CO",
        "Colorado",
        "A",
        marker="o",
        show_ylabel=True,
    )

    plot_state(
        ax_ca,
        df,
        "CA",
        "California",
        "B",
        marker="s",
        show_ylabel=False,
    )

    legend_handles = [
        Line2D(
            [0],
            [0],
            color=FIRE_COLORS["wildfire"],
            linewidth=3.0,
            linestyle="-",
            marker="o",
            markersize=10,
            label="Wildfire",
        ),
        Line2D(
            [0],
            [0],
            color=FIRE_COLORS["prescribed"],
            linewidth=2.5,
            linestyle="--",
            marker="o",
            markersize=10,
            label="Prescribed Fire",
        ),
    ]

    fig.legend(
        handles=legend_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.04),
        ncol=2,
        fontsize=14,
        frameon=True,
        fancybox=False,
        edgecolor="#333333",
        framealpha=0.98,
        columnspacing=3.0,
        handlelength=3.0,
        handletextpad=1.0,
    )

    fig.suptitle(
        "Fire Effects on Recreational Visitation",
        fontsize=19,
        fontweight="bold",
        y=0.98,
    )

    plt.tight_layout(rect=[0, 0.02, 1, 0.96])

    fig.savefig(
        FIGURES / "Overall_Effects.png",
        bbox_inches="tight",
        dpi=600,
    )
    fig.savefig(
        FIGURES / "Overall_Effects.pdf",
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"Saved {FIGURES.relative_to(ROOT) / 'Overall_Effects.png'}")
    print(f"Saved {FIGURES.relative_to(ROOT) / 'Overall_Effects.pdf'}")


if __name__ == "__main__":
    main()
