"""
Generate publication-quality visualizations of experimental results.

Creates comprehensive plots for research presentation and analysis.
"""

import sys
import csv
import argparse
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib as mpl

# Set publication-quality defaults
mpl.rcParams['font.size'] = 12
mpl.rcParams['font.family'] = 'serif'
mpl.rcParams['axes.labelsize'] = 12
mpl.rcParams['axes.titlesize'] = 14
mpl.rcParams['xtick.labelsize'] = 10
mpl.rcParams['ytick.labelsize'] = 10
mpl.rcParams['legend.fontsize'] = 10
mpl.rcParams['figure.titlesize'] = 14


def load_csv_data(csv_file: Path):
    """Load CSV data into lists."""
    data = {}
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for key, value in row.items():
                if key not in data:
                    data[key] = []
                try:
                    data[key].append(float(value))
                except ValueError:
                    data[key].append(value)
    return data


def plot_throughput_vs_concurrency(data, output_file: Path):
    """Plot throughput vs concurrency level with error bars."""
    fig, ax = plt.subplots(figsize=(10, 6))

    concurrency = data['concurrency_level']
    throughput = data['throughput_mean']
    throughput_err = data['throughput_stdev']

    ax.errorbar(concurrency, throughput, yerr=throughput_err,
                marker='o', markersize=8, linewidth=2, capsize=5,
                label='Measured Throughput', color='#2E86AB')

    # Theoretical linear scaling
    if concurrency and throughput:
        baseline_throughput = throughput[0]
        theoretical = [baseline_throughput * c / concurrency[0] for c in concurrency]
        ax.plot(concurrency, theoretical, '--', linewidth=2, color='#A23B72',
                label='Ideal Linear Scaling', alpha=0.7)

    ax.set_xlabel('Concurrency Level (simultaneous requests)', fontweight='bold')
    ax.set_ylabel('Throughput (requests/second)', fontweight='bold')
    ax.set_title('MCP Server Throughput vs. Concurrency Level', fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.9)

    # Add value labels on points
    for i, (x, y) in enumerate(zip(concurrency, throughput)):
        ax.annotate(f'{y:.1f}', (x, y), textcoords="offset points",
                   xytext=(0, 10), ha='center', fontsize=9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_speedup_efficiency(data, output_file: Path):
    """Plot speedup and efficiency vs concurrency."""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    concurrency = data['concurrency_level']
    speedup = data['speedup']
    efficiency = data['efficiency']

    # Speedup plot
    ax1.plot(concurrency, speedup, marker='o', markersize=8, linewidth=2,
            color='#2E86AB', label='Actual Speedup')
    ax1.plot(concurrency, concurrency, '--', linewidth=2, color='#A23B72',
            label='Ideal Linear Speedup', alpha=0.7)

    ax1.set_xlabel('Concurrency Level', fontweight='bold')
    ax1.set_ylabel('Speedup (relative to baseline)', fontweight='bold')
    ax1.set_title('Scalability: Speedup vs. Concurrency', fontweight='bold', pad=20)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.legend(loc='best', framealpha=0.9)

    # Efficiency plot
    ax2.plot(concurrency, efficiency, marker='s', markersize=8, linewidth=2,
            color='#F18F01', label='Parallel Efficiency')
    ax2.axhline(y=100, linestyle='--', color='#A23B72', linewidth=2,
               label='Ideal Efficiency (100%)', alpha=0.7)

    ax2.set_xlabel('Concurrency Level', fontweight='bold')
    ax2.set_ylabel('Efficiency (%)', fontweight='bold')
    ax2.set_title('Parallel Efficiency vs. Concurrency', fontweight='bold', pad=20)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='best', framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_latency_vs_concurrency(data, output_file: Path):
    """Plot response time percentiles vs concurrency."""
    fig, ax = plt.subplots(figsize=(10, 6))

    concurrency = data['concurrency_level']
    mean_latency = data['mean_ms']
    median_latency = data['median_ms']
    p95_latency = data['p95_ms']
    p99_latency = data['p99_ms']

    ax.plot(concurrency, median_latency, marker='o', markersize=8, linewidth=2,
           label='Median (p50)', color='#2E86AB')
    ax.plot(concurrency, mean_latency, marker='s', markersize=8, linewidth=2,
           label='Mean', color='#F18F01')
    ax.plot(concurrency, p95_latency, marker='^', markersize=8, linewidth=2,
           label='95th Percentile', color='#C73E1D')
    ax.plot(concurrency, p99_latency, marker='d', markersize=8, linewidth=2,
           label='99th Percentile', color='#6A0572')

    ax.set_xlabel('Concurrency Level', fontweight='bold')
    ax.set_ylabel('Response Time (milliseconds)', fontweight='bold')
    ax.set_title('Response Time Distribution vs. Concurrency', fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def plot_comprehensive_dashboard(throughput_data, latency_data, output_file: Path):
    """Create a comprehensive 4-panel dashboard."""
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)

    concurrency = throughput_data['concurrency_level']

    # Panel 1: Throughput
    ax1 = fig.add_subplot(gs[0, 0])
    throughput = throughput_data['throughput_mean']
    throughput_err = throughput_data['throughput_stdev']
    ax1.errorbar(concurrency, throughput, yerr=throughput_err,
                marker='o', markersize=6, linewidth=2, capsize=4, color='#2E86AB')
    ax1.set_xlabel('Concurrency Level', fontweight='bold')
    ax1.set_ylabel('Throughput (req/s)', fontweight='bold')
    ax1.set_title('(A) Throughput vs. Concurrency', fontweight='bold', loc='left')
    ax1.grid(True, alpha=0.3, linestyle='--')

    # Panel 2: Speedup
    ax2 = fig.add_subplot(gs[0, 1])
    speedup = throughput_data['speedup']
    ax2.plot(concurrency, speedup, marker='o', markersize=6, linewidth=2,
            color='#2E86AB', label='Actual')
    ax2.plot(concurrency, concurrency, '--', linewidth=2, color='#A23B72',
            label='Ideal', alpha=0.7)
    ax2.set_xlabel('Concurrency Level', fontweight='bold')
    ax2.set_ylabel('Speedup', fontweight='bold')
    ax2.set_title('(B) Speedup Factor', fontweight='bold', loc='left')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.legend(loc='best', framealpha=0.9)

    # Panel 3: Latency Percentiles
    ax3 = fig.add_subplot(gs[1, 0])
    median_latency = latency_data['median_ms']
    p95_latency = latency_data['p95_ms']
    p99_latency = latency_data['p99_ms']
    ax3.plot(concurrency, median_latency, marker='o', markersize=6, linewidth=2,
            label='p50 (median)', color='#2E86AB')
    ax3.plot(concurrency, p95_latency, marker='^', markersize=6, linewidth=2,
            label='p95', color='#C73E1D')
    ax3.plot(concurrency, p99_latency, marker='d', markersize=6, linewidth=2,
            label='p99', color='#6A0572')
    ax3.set_xlabel('Concurrency Level', fontweight='bold')
    ax3.set_ylabel('Response Time (ms)', fontweight='bold')
    ax3.set_title('(C) Latency Percentiles', fontweight='bold', loc='left')
    ax3.grid(True, alpha=0.3, linestyle='--')
    ax3.legend(loc='best', framealpha=0.9)

    # Panel 4: Efficiency
    ax4 = fig.add_subplot(gs[1, 1])
    efficiency = throughput_data['efficiency']
    ax4.plot(concurrency, efficiency, marker='s', markersize=6, linewidth=2,
            color='#F18F01')
    ax4.axhline(y=100, linestyle='--', color='#A23B72', linewidth=2, alpha=0.7)
    ax4.set_xlabel('Concurrency Level', fontweight='bold')
    ax4.set_ylabel('Efficiency (%)', fontweight='bold')
    ax4.set_title('(D) Parallel Efficiency', fontweight='bold', loc='left')
    ax4.grid(True, alpha=0.3, linestyle='--')

    fig.suptitle('MCP API Performance Analysis - Complete Dashboard',
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"Saved: {output_file}")
    plt.close()


def main():
    """Main visualization function."""
    parser = argparse.ArgumentParser(description='Generate visualizations from experimental results')
    parser.add_argument('experiment_dir', type=str, help='Path to experiment directory')
    args = parser.parse_args()

    experiment_dir = Path(args.experiment_dir)

    if not experiment_dir.exists():
        print(f"Error: Directory {experiment_dir} does not exist")
        sys.exit(1)

    # Load plotting data
    throughput_file = experiment_dir / "throughput_vs_concurrency.csv"
    latency_file = experiment_dir / "latency_vs_concurrency.csv"

    if not throughput_file.exists() or not latency_file.exists():
        print("Error: Plotting CSV files not found. Run analyze_results.py first.")
        sys.exit(1)

    print("Loading data...")
    throughput_data = load_csv_data(throughput_file)
    latency_data = load_csv_data(latency_file)

    # Create plots directory
    plots_dir = experiment_dir / "plots"
    plots_dir.mkdir(exist_ok=True)

    print("\nGenerating visualizations...")

    # Individual plots
    plot_throughput_vs_concurrency(throughput_data, plots_dir / "throughput_vs_concurrency.png")
    plot_speedup_efficiency(throughput_data, plots_dir / "speedup_and_efficiency.png")
    plot_latency_vs_concurrency(latency_data, plots_dir / "latency_vs_concurrency.png")

    # Comprehensive dashboard
    plot_comprehensive_dashboard(throughput_data, latency_data, plots_dir / "comprehensive_dashboard.png")

    print(f"\nAll visualizations saved to: {plots_dir}")
    print("\nGenerated plots:")
    print("  1. throughput_vs_concurrency.png - Throughput scaling analysis")
    print("  2. speedup_and_efficiency.png - Speedup and parallel efficiency")
    print("  3. latency_vs_concurrency.png - Response time percentiles")
    print("  4. comprehensive_dashboard.png - Complete 4-panel overview")


if __name__ == "__main__":
    main()
