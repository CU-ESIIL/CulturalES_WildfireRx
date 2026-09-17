#!/usr/bin/env python3
"""Plot heterogeneous wildfire and prescribed-fire effects."""
from __future__ import annotations

import logging
import sys
import warnings
from pathlib import Path

import matplotlib.gridspec as gridspec
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

# Final manuscript palettes.
SIZE_COLORS = {
    "small": "#9ECAE1",
    "medium": "#3182BD",
    "large": "#08519C",
}

SEVERITY_COLORS = {
    "low": "#FED976",
    "moderate": "#FD8D3C",
    "high": "#D32F2F",
}

VEGETATION_COLORS = {
    "grass": "#A6D854",
    "shrub": "#D2B48C",
    "tree": "#228B22",
}

RECREATION_COLORS = {
    "high_recreation": "#00897B",
    "non_recreation": "#9E9E9E",
}


def plot_panel(
    ax,
    df,
    state,
    stratification,
    category_colors,
    categories,
    *,
    show_ylabel=False,
    show_xlabel=False,
    title="",
    panel_label="",
):
    """Plot wildfire (solid) and prescribed fire (dashed) for one moderator."""
    panel_data = df[
        df["state"].eq(state)
        & df["stratification"].eq(stratification)
    ]

    for category in categories:
        for fire_type in ["wildfire", "prescribed"]:
            data = panel_data[
                panel_data["stratum"].eq(category)
                & panel_data["fire_type"].eq(fire_type)
            ].sort_values("year")

            if data.empty:
                continue

            color = category_colors[category]
            linestyle = "-" if fire_type == "wildfire" else "--"
            linewidth = 3.0 if fire_type == "wildfire" else 2.5

            ax.plot(
                data["year"],
                data["effect_pct"],
                marker="o",
                markersize=8,
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
                alpha=0.15,
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

    if show_xlabel:
        ax.set_xlabel(
            "Years After Fire",
            fontsize=13,
            fontweight="bold",
        )
    else:
        ax.set_xlabel("")

    if show_ylabel:
        ax.set_ylabel(
            "Change in Visitation (%)",
            fontsize=13,
            fontweight="bold",
        )
    else:
        ax.set_ylabel("")

    ax.set_xticks(range(6))
    if show_xlabel:
        ax.set_xticklabels(
            ["0", "1", "2", "3", "4", "5+"],
            fontsize=12,
        )
    else:
        ax.set_xticklabels([])

    ax.tick_params(
        axis="y",
        labelsize=12,
        which="both",
    )

    ax.yaxis.grid(
        True,
        linestyle="-",
        linewidth=0.6,
        alpha=0.3,
        zorder=0,
    )
    ax.xaxis.grid(False)
    ax.set_axisbelow(True)

    ax.text(
        0.02,
        0.98,
        panel_label,
        transform=ax.transAxes,
        fontsize=15,
        fontweight="bold",
        va="top",
        ha="left",
    )

    ax.set_title(
        title,
        loc="left",
        fontsize=13,
        fontweight="normal",
        pad=8,
        x=0.08,
    )

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_linewidth(1.0)
    ax.spines["bottom"].set_linewidth(1.0)


def sync_ylims_row(axes):
    """Use common y limits across all panels in one state row."""
    all_lims = []

    for ax in axes:
        all_lims.extend(ax.get_ylim())

    if not all_lims:
        return

    ymin, ymax = min(all_lims), max(all_lims)
    span = ymax - ymin
    pad = 0.08 * span if span > 0 else 1

    for ax in axes:
        ax.set_ylim(ymin - pad, ymax + pad)


def add_category_legend(ax, title, items):
    """Add the moderator legend to a bottom-row panel."""
    handles = [
        Line2D(
            [0],
            [0],
            color=color,
            linewidth=4.0,
            marker="o",
            markersize=7,
            label=label,
        )
        for label, color in items
    ]

    legend = ax.legend(
        handles=handles,
        loc="lower left",
        bbox_to_anchor=(0.02, 0.02),
        bbox_transform=ax.transAxes,
        ncol=1,
        fontsize=9,
        frameon=True,
        fancybox=False,
        edgecolor="#CCCCCC",
        framealpha=0.95,
        title=title,
        title_fontsize=9,
        handlelength=1.6,
        handletextpad=0.5,
        labelspacing=0.3,
        borderpad=0.4,
    )

    legend.get_frame().set_linewidth(0.8)


def main() -> None:
    ensure_output_dirs()
    df = pd.read_csv(TABLES / "did_heterogeneity_results.csv")

    fig = plt.figure(figsize=(18, 10))
    gs = gridspec.GridSpec(
        2,
        4,
        figure=fig,
        hspace=0.22,
        wspace=0.10,
        left=0.06,
        right=0.98,
        top=0.90,
        bottom=0.12,
    )

    # Colorado
    ax_co_size = fig.add_subplot(gs[0, 0])
    plot_panel(
        ax_co_size,
        df,
        "CO",
        "size",
        SIZE_COLORS,
        ["small", "medium", "large"],
        show_ylabel=True,
        show_xlabel=False,
        title="Colorado: Fire Size",
        panel_label="A",
    )

    ax_co_sev = fig.add_subplot(gs[0, 1])
    plot_panel(
        ax_co_sev,
        df,
        "CO",
        "severity",
        SEVERITY_COLORS,
        ["low", "moderate", "high"],
        title="Colorado: Fire Severity",
        panel_label="B",
    )

    ax_co_veg = fig.add_subplot(gs[0, 2])
    plot_panel(
        ax_co_veg,
        df,
        "CO",
        "vegetation",
        VEGETATION_COLORS,
        ["grass", "tree"],
        title="Colorado: Vegetation",
        panel_label="C",
    )

    ax_co_rec = fig.add_subplot(gs[0, 3])
    plot_panel(
        ax_co_rec,
        df,
        "CO",
        "recreation",
        RECREATION_COLORS,
        ["high_recreation", "non_recreation"],
        title="Colorado: County Type",
        panel_label="D",
    )

    # California
    ax_ca_size = fig.add_subplot(gs[1, 0])
    plot_panel(
        ax_ca_size,
        df,
        "CA",
        "size",
        SIZE_COLORS,
        ["small", "medium", "large"],
        show_ylabel=True,
        show_xlabel=True,
        title="California: Fire Size",
        panel_label="E",
    )

    ax_ca_sev = fig.add_subplot(gs[1, 1])
    plot_panel(
        ax_ca_sev,
        df,
        "CA",
        "severity",
        SEVERITY_COLORS,
        ["low", "moderate", "high"],
        show_xlabel=True,
        title="California: Fire Severity",
        panel_label="F",
    )

    ax_ca_veg = fig.add_subplot(gs[1, 2])
    plot_panel(
        ax_ca_veg,
        df,
        "CA",
        "vegetation",
        VEGETATION_COLORS,
        ["grass", "shrub", "tree"],
        show_xlabel=True,
        title="California: Vegetation",
        panel_label="G",
    )

    ax_ca_rec = fig.add_subplot(gs[1, 3])
    plot_panel(
        ax_ca_rec,
        df,
        "CA",
        "recreation",
        RECREATION_COLORS,
        ["high_recreation", "non_recreation"],
        show_xlabel=True,
        title="California: County Type",
        panel_label="H",
    )

    sync_ylims_row(
        [ax_co_size, ax_co_sev, ax_co_veg, ax_co_rec]
    )
    sync_ylims_row(
        [ax_ca_size, ax_ca_sev, ax_ca_veg, ax_ca_rec]
    )

    fig.suptitle(
        "Heterogeneous Fire Effects on Recreation",
        fontsize=17,
        fontweight="bold",
        y=0.96,
    )

    # Fire-type legend shared across the whole figure.
    fire_type_handles = [
        Line2D(
            [0],
            [0],
            color="black",
            linewidth=3.0,
            linestyle="-",
            label="Wildfire",
        ),
        Line2D(
            [0],
            [0],
            color="black",
            linewidth=2.5,
            linestyle="--",
            label="Prescribed Fire",
        ),
    ]

    fire_type_legend = fig.legend(
        handles=fire_type_handles,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=2,
        fontsize=11,
        frameon=True,
        fancybox=False,
        edgecolor="#333333",
        framealpha=0.98,
        title="Fire Type",
        title_fontsize=11,
        columnspacing=2.0,
        handlelength=2.5,
    )
    fire_type_legend.get_frame().set_linewidth(1.0)

    # Moderator legends appear once, in the bottom row.
    add_category_legend(
        ax_ca_size,
        "Fire Size",
        [
            ("Small", SIZE_COLORS["small"]),
            ("Medium", SIZE_COLORS["medium"]),
            ("Large", SIZE_COLORS["large"]),
        ],
    )

    add_category_legend(
        ax_ca_sev,
        "Fire Severity",
        [
            ("Low", SEVERITY_COLORS["low"]),
            ("Moderate", SEVERITY_COLORS["moderate"]),
            ("High", SEVERITY_COLORS["high"]),
        ],
    )

    add_category_legend(
        ax_ca_veg,
        "Vegetation Type",
        [
            ("Grass", VEGETATION_COLORS["grass"]),
            ("Shrub", VEGETATION_COLORS["shrub"]),
            ("Tree", VEGETATION_COLORS["tree"]),
        ],
    )

    add_category_legend(
        ax_ca_rec,
        "County Type",
        [
            ("High Recreation", RECREATION_COLORS["high_recreation"]),
            ("Other Counties", RECREATION_COLORS["non_recreation"]),
        ],
    )

    fig.savefig(
        FIGURES / "Heterogeneous_Effects.png",
        dpi=600,
        bbox_inches="tight",
    )
    fig.savefig(
        FIGURES / "Heterogeneous_Effects.pdf",
        bbox_inches="tight",
    )
    plt.close(fig)

    print(f"Saved {FIGURES.relative_to(ROOT) / 'Heterogeneous_Effects.png'}")
    print(f"Saved {FIGURES.relative_to(ROOT) / 'Heterogeneous_Effects.pdf'}")


if __name__ == "__main__":
    main()
