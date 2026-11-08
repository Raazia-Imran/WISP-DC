"""Generate publication-ready S2 figures from the auditable CSV outputs."""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import numpy as np


BASE = Path(__file__).resolve().parent
OUT = BASE / "generated_outputs"


def load_csv(path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def throughput_chart():
    rows = load_csv(BASE / "s2_benchmark_data.csv")
    labels = [r["config_id"] for r in rows]
    values = [float(r["output_tokens_per_s"]) for r in rows]
    colors = ["#4E79A7", "#4E79A7", "#F28E2B", "#59A14F"]
    fig, ax = plt.subplots(figsize=(8.3, 4.8))
    bars = ax.bar(labels, values, color=colors, edgecolor="#2F3B4B", linewidth=0.6)
    ax.set_title("Official MLPerf Llama 2 70B Server Throughput", weight="bold")
    ax.set_ylabel("Completed output tokens/s")
    ax.grid(axis="y", alpha=0.25)
    ax.set_axisbelow(True)
    for bar, value in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width()/2, value + 500, f"{value:,.0f}",
                ha="center", va="bottom", fontsize=9)
    ax.set_ylim(0, max(values) * 1.16)
    fig.text(0.5, 0.01, "Source: official MLPerf Inference v5.0 HPE submissions; values are measured benchmark results.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / "s2_throughput.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


def sensitivity_chart():
    rows = load_csv(OUT / "s2_sensitivity_results.csv")
    throughput_values = sorted({int(r["required_output_tokens_per_s"]) for r in rows})
    limits = [1, 2, 8]
    code = {"None": 0, "HPE-GH200-1": 1, "HPE-GH200-2": 2, "HPE-H100-8": 3, "HPE-H200-8": 4}
    matrix = np.zeros((len(limits), len(throughput_values)))
    lookup = {(int(r["max_accelerators"]), int(r["required_output_tokens_per_s"])): r["recommendation"] for r in rows}
    for i, limit in enumerate(limits):
        for j, throughput in enumerate(throughput_values):
            matrix[i, j] = code[lookup[(limit, throughput)]]

    cmap = ListedColormap(["#E15759", "#76B7B2", "#4E79A7", "#F28E2B", "#59A14F"])
    fig, ax = plt.subplots(figsize=(10, 3.8))
    ax.imshow(matrix, aspect="auto", cmap=cmap, vmin=-0.5, vmax=4.5)
    tick_idx = list(range(0, len(throughput_values), 4))
    ax.set_xticks(tick_idx, [f"{throughput_values[i]/1000:.0f}k" for i in tick_idx])
    ax.set_yticks(range(len(limits)), [str(x) for x in limits])
    ax.set_xlabel("Required output throughput (tokens/s)")
    ax.set_ylabel("Maximum accelerators")
    ax.set_title("S2 Recommendation Sensitivity to Workload and Accelerator Limit", weight="bold")
    handles = [plt.Rectangle((0,0),1,1,color=cmap(i)) for i in range(5)]
    ax.legend(handles, ["Infeasible", "GH200×1", "GH200×2", "H100×8", "H200×8"],
              loc="upper center", bbox_to_anchor=(0.5, -0.23), ncol=5, frameon=False)
    fig.text(0.5, 0.01, "Declared workload sweep; recommendations use only the four evaluated MLPerf configurations.",
             ha="center", fontsize=8, color="#555555")
    fig.tight_layout(rect=(0, 0.10, 1, 1))
    fig.savefig(OUT / "s2_sensitivity_map.png", dpi=220, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    throughput_chart()
    sensitivity_chart()
    print(OUT / "s2_throughput.png")
    print(OUT / "s2_sensitivity_map.png")
