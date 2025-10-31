"""
Statistical analysis and visualization of experimental results.

Generates publication-quality plots and statistical analysis of benchmarking data.
"""

import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any
import statistics


def load_summary_data(experiment_dir: Path) -> List[Dict[str, Any]]:
    """Load summary statistics from experiment."""
    summary_file = experiment_dir / "summary_statistics.csv"

    data = []
    with open(summary_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Convert numeric fields
            converted_row = {}
            for key, value in row.items():
                try:
                    # Try to convert to float
                    converted_row[key] = float(value)
                except (ValueError, TypeError):
                    converted_row[key] = value
            data.append(converted_row)

    return data


def calculate_speedup(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate speedup relative to baseline (concurrency=1)."""
    if not data:
        return data

    # Find baseline throughput (concurrency = 1)
    baseline = next((d for d in data if d['concurrency_level'] == 1), None)

    if not baseline:
        print("Warning: No baseline (concurrency=1) found, using first entry")
        baseline = data[0]

    baseline_throughput = float(baseline.get('throughput_req_per_sec_mean', 0.0) or 0.0)

    # Calculate speedup for each configuration
    for entry in data:
        thr = float(entry.get('throughput_req_per_sec_mean', 0.0) or 0.0)
        if baseline_throughput > 0:
            entry['speedup'] = thr / baseline_throughput
            entry['efficiency'] = (entry['speedup'] / entry['concurrency_level']) * 100  # percentage
        else:
            entry['speedup'] = 0.0
            entry['efficiency'] = 0.0

    return data


def generate_text_report(data: List[Dict[str, Any]], output_file: Path):
    """Generate detailed text report with statistical analysis."""
    with open(output_file, 'w') as f:
        f.write("="*80 + "\n")
        f.write("STATISTICAL ANALYSIS REPORT\n")
        f.write("="*80 + "\n\n")

        # Table 1: Throughput Analysis
        f.write("Table 1: Throughput Analysis\n")
        f.write("-"*95 + "\n")
        f.write(f"{'Concurrency':<12} {'Throughput (req/s)':<25} {'Speedup':<12} {'Efficiency (%)':<15} {'Success Rate (%)':<15}\n")
        f.write(f"{'Level':<12} {'Mean ± StdDev':<25} {'':<12} {'':<15} {'':<15}\n")
        f.write("-"*95 + "\n")

        for entry in data:
            concurrency = int(entry['concurrency_level'])
            throughput_mean = entry['throughput_req_per_sec_mean']
            throughput_stdev = entry['throughput_req_per_sec_stdev']
            speedup = entry.get('speedup', 0)
            efficiency = entry.get('efficiency', 0)
            success_rate = entry.get('success_rate_mean', 0)

            f.write(f"{concurrency:<12} {throughput_mean:>7.2f} ± {throughput_stdev:<6.2f}      "
                   f"{speedup:>6.2f}x      {efficiency:>6.2f}%         {success_rate:>6.2f}%\n")

        # Table 2: Latency Analysis
        f.write("\n\nTable 2: Response Time Analysis (ms)\n")
        f.write("-"*80 + "\n")
        f.write(f"{'Concurrency':<12} {'Mean':<12} {'Median':<12} {'p95':<12} {'p99':<12}\n")
        f.write("-"*80 + "\n")

        for entry in data:
            concurrency = int(entry['concurrency_level'])
            mean_rt = entry['response_time_mean_ms_mean']
            median_rt = entry['response_time_median_ms_mean']
            p95 = entry['p95_mean']
            p99 = entry['p99_mean']

            f.write(f"{concurrency:<12} {mean_rt:<12.2f} {median_rt:<12.2f} "
                   f"{p95:<12.2f} {p99:<12.2f}\n")

        # Key Findings
        f.write("\n\nKey Findings:\n")
        f.write("-"*80 + "\n")

        # Find optimal concurrency
        max_throughput_entry = max(data, key=lambda x: x['throughput_req_per_sec_mean'])
        f.write(f"1. Maximum Throughput:\n")
        f.write(f"   - Achieved at concurrency level {int(max_throughput_entry['concurrency_level'])}\n")
        f.write(f"   - Throughput: {max_throughput_entry['throughput_req_per_sec_mean']:.2f} req/s\n")
        f.write(f"   - Speedup: {max_throughput_entry.get('speedup', 0):.2f}x over baseline\n\n")

        # Find best efficiency
        max_efficiency_entry = max(data, key=lambda x: x.get('efficiency', 0))
        f.write(f"2. Best Efficiency:\n")
        f.write(f"   - At concurrency level {int(max_efficiency_entry['concurrency_level'])}\n")
        f.write(f"   - Efficiency: {max_efficiency_entry.get('efficiency', 0):.2f}%\n\n")

        # Scalability analysis
        f.write(f"3. Scalability Analysis:\n")
        if len(data) >= 2:
            # Compare first and last
            first = data[0]
            last = data[-1]
            concurrency_increase = last['concurrency_level'] / first['concurrency_level']
            first_thr = float(first.get('throughput_req_per_sec_mean', 0.0) or 0.0)
            last_thr = float(last.get('throughput_req_per_sec_mean', 0.0) or 0.0)
            throughput_increase = (last_thr / first_thr) if first_thr > 0 else 0.0

            f.write(f"   - Concurrency increased {concurrency_increase:.1f}x "
                   f"(from {int(first['concurrency_level'])} to {int(last['concurrency_level'])})\n")
            f.write(f"   - Throughput increased {throughput_increase:.2f}x "
                   f"({first['throughput_req_per_sec_mean']:.2f} to {last['throughput_req_per_sec_mean']:.2f} req/s)\n")

            if throughput_increase < concurrency_increase * 0.5:
                f.write(f"   - System shows sub-linear scaling (possible bottleneck)\n")
            elif throughput_increase >= concurrency_increase * 0.8:
                f.write(f"   - System shows near-linear scaling (good parallelization)\n")
            else:
                f.write(f"   - System shows moderate scaling\n")

        # Latency trends
        f.write(f"\n4. Latency Trends:\n")
        min_latency = min(data, key=lambda x: x['response_time_median_ms_mean'])
        max_latency = max(data, key=lambda x: x['response_time_median_ms_mean'])
        f.write(f"   - Lowest median latency: {min_latency['response_time_median_ms_mean']:.2f} ms "
               f"at concurrency {int(min_latency['concurrency_level'])}\n")
        f.write(f"   - Highest median latency: {max_latency['response_time_median_ms_mean']:.2f} ms "
               f"at concurrency {int(max_latency['concurrency_level'])}\n")

        min_med = float(min_latency.get('response_time_median_ms_mean', 0.0) or 0.0)
        max_med = float(max_latency.get('response_time_median_ms_mean', 0.0) or 0.0)
        latency_increase = (max_med / min_med) if min_med > 0 else 0.0
        f.write(f"   - Latency increased {latency_increase:.2f}x from lowest to highest concurrency\n")

        # Success rate analysis
        f.write(f"\n5. Reliability:\n")
        avg_success_rate = statistics.mean([d['success_rate_mean'] for d in data])
        min_success_rate = min(data, key=lambda x: x['success_rate_mean'])
        f.write(f"   - Average success rate: {avg_success_rate:.2f}%\n")
        f.write(f"   - Minimum success rate: {min_success_rate['success_rate_mean']:.2f}% "
               f"at concurrency {int(min_success_rate['concurrency_level'])}\n")

        if avg_success_rate >= 99.9:
            f.write(f"   - System is highly reliable across all concurrency levels\n")
        elif avg_success_rate >= 95:
            f.write(f"   - System is generally reliable with some errors at high concurrency\n")
        else:
            f.write(f"   - System shows reliability issues - investigate error patterns\n")

        f.write("\n" + "="*80 + "\n")


def generate_csv_for_plotting(data: List[Dict[str, Any]], output_dir: Path):
    """Generate simplified CSV files for easy plotting."""

    # Throughput vs Concurrency
    throughput_file = output_dir / "throughput_vs_concurrency.csv"
    with open(throughput_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['concurrency_level', 'throughput_mean', 'throughput_stdev',
                        'speedup', 'efficiency'])
        for entry in data:
            writer.writerow([
                int(entry['concurrency_level']),
                entry['throughput_req_per_sec_mean'],
                entry['throughput_req_per_sec_stdev'],
                entry.get('speedup', 0),
                entry.get('efficiency', 0)
            ])

    # Latency vs Concurrency
    latency_file = output_dir / "latency_vs_concurrency.csv"
    with open(latency_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['concurrency_level', 'mean_ms', 'median_ms', 'p95_ms', 'p99_ms'])
        for entry in data:
            writer.writerow([
                int(entry['concurrency_level']),
                entry['response_time_mean_ms_mean'],
                entry['response_time_median_ms_mean'],
                entry['p95_mean'],
                entry['p99_mean']
            ])

    print(f"\nGenerated plotting CSVs:")
    print(f"  - {throughput_file}")
    print(f"  - {latency_file}")


def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(description='Analyze experimental results')
    parser.add_argument('experiment_dir', type=str, help='Path to experiment directory')
    args = parser.parse_args()

    experiment_dir = Path(args.experiment_dir)

    if not experiment_dir.exists():
        print(f"Error: Directory {experiment_dir} does not exist")
        sys.exit(1)

    # Load data
    print(f"Loading data from {experiment_dir}...")
    data = load_summary_data(experiment_dir)

    if not data:
        print("Error: No data found in summary_statistics.csv")
        sys.exit(1)

    print(f"Loaded {len(data)} concurrency configurations")

    # Calculate derived metrics
    data = calculate_speedup(data)

    # Generate analysis report
    report_file = experiment_dir / "analysis_report.txt"
    print(f"\nGenerating statistical analysis report...")
    generate_text_report(data, report_file)
    print(f"Report saved to: {report_file}")

    # Generate plotting CSVs
    generate_csv_for_plotting(data, experiment_dir)

    # Print summary to console
    print("\n" + "="*80)
    print("QUICK SUMMARY")
    print("="*80)
    for entry in data:
        concurrency = int(entry['concurrency_level'])
        throughput = entry['throughput_req_per_sec_mean']
        speedup = entry.get('speedup', 0)
        p95 = entry['p95_mean']
        print(f"Concurrency {concurrency:>3}: {throughput:>7.2f} req/s "
              f"(speedup: {speedup:>5.2f}x, p95: {p95:>7.2f} ms)")
    print("="*80 + "\n")

    print(f"\nFull analysis available in: {report_file}")


if __name__ == "__main__":
    main()
