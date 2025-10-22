"""
Visualize timestamps.csv as a Gantt chart.

This script reads a CSV with the following columns and draws a Gantt chart
for the processing pipeline stages:
    - start_timestamp
    - base_model_card_timestamp
    - remove_embedding_timestamp
    - enrich_ai_model_timestamp
    - enrich_bias_analysis_timestamp
    - enrich_xai_analysis_timestamp  (treated as end)

By default, it aggregates across all rows using the mean. You can select a
specific row or alternate aggregations via CLI flags.
"""

import argparse
from pathlib import Path
from typing import List, Tuple

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch


REQUIRED_COLUMNS: List[str] = [
    "start_timestamp",
    "base_model_card_timestamp",
    "remove_embedding_timestamp",
    "enrich_ai_model_timestamp",
    "enrich_bias_analysis_timestamp",
    "enrich_xai_analysis_timestamp",
]


def validate_columns(df: pd.DataFrame) -> None:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")


def compute_stage_starts_and_durations(
    timestamps: List[float],
    include_overhead: bool,
    exclude_embedding: bool,
) -> Tuple[List[float], List[float], List[str]]:
    stage_labels_all = [
        "Base Model Card",        # 0: start -> base
        "Remove Embedding",       # 1: base -> remove_embedding
        "AI Model",               # 2: remove_embedding -> enrich_ai
        "Bias Analysis",          # 3: enrich_ai -> enrich_bias
        "XAI Analysis",           # 4: enrich_bias -> enrich_xai
    ]

    # durations between consecutive timestamps, in milliseconds
    durations_ms_all = [
        (timestamps[i + 1] - timestamps[i]) * 1000.0 for i in range(len(timestamps) - 1)
    ]

    # Filter stages according to options
    indices = list(range(len(durations_ms_all)))
    if exclude_embedding and len(indices) > 1:
        # Drop the Remove Embedding segment (index 1 in the original order)
        indices = [i for i in indices if i != 1]

    durations_ms = [durations_ms_all[i] for i in indices]
    stage_labels = [stage_labels_all[i] for i in indices]

    # Compute left positions after filtering to avoid gaps
    starts_ms: List[float] = []
    cumulative = 0.0
    for d in durations_ms:
        starts_ms.append(cumulative)
        cumulative += d

    return starts_ms, durations_ms, stage_labels


def plot_gantt(starts_ms: List[float], durations_ms: List[float], stage_labels: List[str], title: str, output_path: Path, include_overhead: bool) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(6, 3))

    # Color last stage differently if we include overhead
    colors: List[str] = []
    for i in range(len(stage_labels)):
        if include_overhead and i == len(stage_labels) - 1:
            colors.append("orange")
        else:
            colors.append("skyblue")

    ax.barh(stage_labels, durations_ms, left=starts_ms, height=1, color=colors)
    ax.set_xlabel("Time (ms)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Query Task", fontsize=12, fontweight="bold")
    plt.tight_layout()
    plt.grid(axis="both", alpha=0.3)
    plt.savefig(str(output_path), dpi=300, bbox_inches="tight")
    print(f"Plot saved to: {output_path}")
    plt.show()


def aggregate_series(df: pd.DataFrame, agg: str) -> pd.Series:
    agg = agg.lower()
    if agg == "mean":
        return df.mean(numeric_only=True)
    if agg == "median":
        return df.median(numeric_only=True)
    if agg in ("p95", "p_95", "quantile95"):
        return df.quantile(0.95, numeric_only=True)
    raise ValueError(f"Unsupported aggregation: {agg}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a Gantt chart from timestamps.csv")
    parser.add_argument(
        "--csv",
        type=str,
        default="/home/exouser/client/analysis/timestamps.csv",
        help="Path to timestamps CSV",
    )
    parser.add_argument(
        "--row",
        type=int,
        default=None,
        help="Specific row index to visualize (0-based). If omitted, uses aggregation.",
    )
    parser.add_argument(
        "--agg",
        type=str,
        choices=["mean", "median", "p95"],
        default="mean",
        help="Aggregation to use when --row is not provided.",
    )
    parser.add_argument(
        "--exclude-overhead",
        action="store_true",
        default=True,
        help="Exclude the final segment from enrich_xai to end (Finalize/Overhead).",
    )
    parser.add_argument(
        "--include-overhead",
        action="store_true",
        help="Include the final segment (Finalize/Overhead). Overrides --exclude-overhead.",
    )
    parser.add_argument(
        "--exclude-embedding",
        action="store_true",
        default=True,
        help="Exclude the Remove Embedding stage.",
    )
    parser.add_argument(
        "--include-embedding",
        action="store_true",
        help="Include the Remove Embedding stage. Overrides --exclude-embedding.",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output image path. Defaults to analysis/outputs/timestamps_gantt_<mode>.png",
    )

    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    # Handle potential leading spaces in header names
    df = pd.read_csv(csv_path, skipinitialspace=True)
    df.columns = [c.strip() for c in df.columns]
    validate_columns(df)

    # Choose row vs aggregation
    if args.row is not None:
        if args.row < 0 or args.row >= len(df):
            raise IndexError(f"Row index out of range: {args.row} (0..{len(df)-1})")
        s = df.iloc[args.row]
        mode_desc = f"row {args.row}"
    else:
        s = aggregate_series(df, args.agg)
        mode_desc = args.agg

    timestamps = [
        float(s["start_timestamp"]),
        float(s["base_model_card_timestamp"]),
        float(s["remove_embedding_timestamp"]),
        float(s["enrich_ai_model_timestamp"]),
        float(s["enrich_bias_analysis_timestamp"]),
        float(s["enrich_xai_analysis_timestamp"]),
    ]

    include_overhead = args.include_overhead and not args.exclude_overhead
    exclude_embedding = args.exclude_embedding and not args.include_embedding

    starts_ms, durations_ms, stage_labels = compute_stage_starts_and_durations(
        timestamps,
        include_overhead=include_overhead,
        exclude_embedding=exclude_embedding,
    )

    if args.output:
        output_path = Path(args.output)
    else:
        parts = []
        parts.append("with_overhead" if include_overhead else "no_overhead")
        parts.append("with_embed" if not exclude_embedding else "no_embed")
        suffix = "_".join(parts)
        output_dir = Path("/home/exouser/client/analysis/outputs")
        output_path = output_dir / f"timestamps_gantt_{mode_desc}_{suffix}.png"

    title = f"Gantt - Timestamps ({mode_desc})"
    plot_gantt(starts_ms, durations_ms, stage_labels, title, output_path, include_overhead=include_overhead)


if __name__ == "__main__":
    main()


