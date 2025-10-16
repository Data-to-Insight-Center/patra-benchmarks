"""
Model Card Retrieval Performance Visualization

This script generates Gantt charts comparing REST API vs MCP performance
for model card retrieval operations, showing both processing breakdown
and total request latency.
"""

import os
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from pathlib import Path


def find_latest_run_directory(root_dir: Path) -> Path:
    """
    Find the most recent benchmark run directory.
    
    Args:
        root_dir: Root directory containing run_* subdirectories
        
    Returns:
        Path to the latest run directory
        
    Raises:
        FileNotFoundError: If root directory doesn't exist
    """
    if not root_dir.exists():
        raise FileNotFoundError(f"Directory does not exist: {root_dir}")
    
    run_dirs = [p for p in root_dir.iterdir() 
                if p.is_dir() and p.name.startswith("run_")]
    
    if not run_dirs:
        # If no run_* directories, assume CSV files are directly in root
        return root_dir
    
    return sorted(run_dirs)[-1]


def create_gantt_chart(csv_file: Path, title_suffix: str = "") -> None:
    """
    Create a Gantt chart showing processing stages and total request latency.
    
    Args:
        csv_file: Path to the benchmark results CSV file
        title_suffix: Suffix to add to the chart title
    """
    if not csv_file.exists():
        print(f"Warning: File does not exist: {csv_file}")
        return
    
    # Load and process data
    df = pd.read_csv(csv_file)
    mean_timestamps = df.mean()
    
    # Define processing stages
    processing_stages = [
        'Base Model Card',
        'AI Model',
        'Bias Analysis',
        'XAI Analysis'
    ]
    
    # Extract timestamp values
    stage_timestamps = [
        mean_timestamps['start_timestamp'],
        mean_timestamps['base_model_card_timestamp'],
        mean_timestamps['enrich_ai_model_timestamp'],
        mean_timestamps['enrich_bias_analysis_timestamp'],
        mean_timestamps['enrich_xai_analysis_timestamp']
    ]
    
    # Calculate relative start times and durations (in milliseconds)
    reference_time = stage_timestamps[0]
    stage_starts = [(timestamp - reference_time) * 1000 
                   for timestamp in stage_timestamps[:-1]]
    stage_durations = [(stage_timestamps[i+1] - stage_timestamps[i]) * 1000 
                      for i in range(len(stage_timestamps)-1)]
    
    # Create DataFrame for Gantt chart
    gantt_data = pd.DataFrame({
        'Task': processing_stages,
        'Start': stage_starts,
        'Duration': stage_durations
    })
    
    # Note: Protocol overhead is excluded from the Gantt chart
    
    # Create the plot
    fig, ax = plt.subplots(figsize=(12, 6))
    
    # Draw bars for processing stages
    ax.barh(gantt_data['Task'], gantt_data['Duration'], 
            left=gantt_data['Start'], height=0.5, color='skyblue')
    
    # No vertical line
    
    # Format the plot
    ax.set_xlabel('Time (ms)', fontsize=12)
    ax.set_ylabel('Processing Stage', fontsize=12)
    ax.set_title(f'Model Card Retrieval Performance - {title_suffix}', 
                fontsize=14, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    # Add legend
    legend_elements = [
        Patch(facecolor='skyblue', label='Processing Time')
    ]
    ax.legend(handles=legend_elements, loc='upper right')
    
    plt.tight_layout()
    
    # Save the plot
    output_filename = f'/home/exouser/client/analysis/outputs/{title_suffix}.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_filename}")
    plt.show()


def create_query_vs_overhead_chart(rest_csv: Path, mcp_csv: Path) -> None:
    """Render stacked bars for Query Time vs Protocol Overhead for REST and MCP."""
    def compute_query_and_overhead(csv_path: Path):
        if not csv_path.exists():
            return None
        df = pd.read_csv(csv_path)
        mt = df.mean()
        timestamps = [
            mt['start_timestamp'],
            mt['base_model_card_timestamp'],
            mt['enrich_ai_model_timestamp'],
            mt['enrich_bias_analysis_timestamp'],
            mt['enrich_xai_analysis_timestamp']
        ]
        # Query time is the sum of accounted stage durations
        stage_ms = [
            (timestamps[1] - timestamps[0]) * 1000,
            (timestamps[2] - timestamps[1]) * 1000,
            (timestamps[3] - timestamps[2]) * 1000,
            (timestamps[4] - timestamps[3]) * 1000,
        ]
        total_latency_ms = (mt['req_end_time'] - mt['req_start_time']) * 1000
        query_time_ms = max(sum(stage_ms), 0)
        overhead_ms = max(total_latency_ms - query_time_ms, 0)
        return query_time_ms, overhead_ms

    entries = []
    labels = []
    rest_vals = compute_query_and_overhead(rest_csv)
    if rest_vals is not None:
        labels.append('REST')
        entries.append(rest_vals)
    mcp_vals = compute_query_and_overhead(mcp_csv)
    if mcp_vals is not None:
        labels.append('MCP')
        entries.append(mcp_vals)

    if not entries:
        print('Warning: No data available for Query vs Overhead chart.')
        return

    query = [e[0] for e in entries]
    overhead = [e[1] for e in entries]

    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(labels))
    bars_query = ax.bar(x, query, color='skyblue', label='Query Time')
    bars_overhead = ax.bar(x, overhead, bottom=query, color='orange', label='Protocol Overhead')

    ax.set_xticks(list(x))
    ax.set_xticklabels(labels)
    ax.set_ylabel('Time (ms)', fontsize=12)
    ax.set_title('Query Time vs Protocol Overhead', fontsize=14, fontweight='bold')
    # ax.legend(loc='upper right')
    ax.grid(axis='y', alpha=0.3)

    plt.tight_layout()
    output_filename = '/home/exouser/client/analysis/outputs/query_vs_overhead.png'
    plt.savefig(output_filename, dpi=300, bbox_inches='tight')
    print(f"Plot saved to: {output_filename}")
    plt.show()


def main():
    """Main function to generate performance comparison plots."""
    # Set up paths with environment variable fallbacks
    rest_results_dir = os.getenv("REST_RESULTS_DIR", 
                                "/home/exouser/client/rest/benchmark_results")
    mcp_results_dir = os.getenv("MCP_RESULTS_DIR", 
                               "/home/exouser/client/mcp/benchmark_results")
    
    # Find latest run directories and CSV files
    rest_csv = find_latest_run_directory(Path(rest_results_dir)) / "get_modelcard.csv"
    mcp_csv = find_latest_run_directory(Path(mcp_results_dir)) / "get_modelcard.csv"
    
    # Generate comparison plots
    create_gantt_chart(rest_csv, "REST")
    create_gantt_chart(mcp_csv, "MCP")
    create_query_vs_overhead_chart(rest_csv, mcp_csv)


if __name__ == "__main__":
    main()