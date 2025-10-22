import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Defaults for result directories
MCP_DIR = Path(os.getenv("MCP_RESULTS_DIR", "/home/exouser/client/mcp/benchmark_results"))
REST_DIR = Path(os.getenv("REST_RESULTS_DIR", "/home/exouser/client/rest/benchmark_results"))
LAYERED_MCP_DIR = Path(os.getenv("LAYERED_MCP_RESULTS_DIR", "/home/exouser/client/layered_mcp/benchmark_results"))
DB_DIR = Path(os.getenv("DB_RESULTS_DIR", "/home/exouser/client/db/benchmark_results"))
OUTPUT_DIR = Path(os.getenv("ANALYSIS_OUTPUT_DIR", "/home/exouser/client/analysis/outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def latest_run_dir(root: Path) -> Path:
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    run_dirs = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("run_")]
    if not run_dirs:
        return root
    return sorted(run_dirs)[-1]

def read_durations(run_dir: Path, filename: str) -> pd.Series | None:
    """Return durations (seconds) from a CSV that is either [start,end] or [duration]."""
    path = run_dir / filename
    if not path.exists():
        return None
    df = pd.read_csv(path, header=None)
    if df.empty:
        return None
    if df.shape[1] >= 2:
        durations = df.iloc[:, 1] - df.iloc[:, 0]
    else:
        durations = df.iloc[:, 0]
    return durations.astype(float)

def read_db_latency(run_dir: Path, filename: str) -> tuple[float, float] | None:
    """Read DB latency from CSV with [start, end] timestamps and return (mean, std) in ms."""
    path = run_dir / filename
    if not path.exists():
        return None
    
    df = pd.read_csv(path, header=None)
    if df.empty or df.shape[1] < 2:
        return None
    
    # Calculate latency: end - start, convert to milliseconds
    latencies_ms = (df.iloc[:, 1] - df.iloc[:, 0]) * 1000.0
    return float(latencies_ms.mean()), float(latencies_ms.std())

def plot_combined_latency_comparison(get_data: dict, search_data: dict, out_path: Path) -> None:
    """Plot combined bar chart comparing REST, Native MCP, and Layered MCP latency for both operations."""
    fig, ax = plt.subplots(figsize=(5, 3))
    
    # Bar positioning
    x = np.arange(2)  # Two groups: Get Model Card and Search Model Cards
    width = 0.22
    
    # Color scheme - different colors for each approach
    rest_color = "#4C78A8"       # Blue for REST
    mcp_color = "#F28E2B"        # Orange for Native MCP
    layered_color = "#59A14F"    # Green for Layered MCP
    
    # Get Model Card bars
    ax.bar(x[0] - width, get_data['rest_mean'], width, color=rest_color, label="REST",
           yerr=get_data['rest_std'], capsize=4, error_kw={'capthick': 1})
    ax.bar(x[0], get_data['mcp_mean'], width, color=mcp_color, label="Native MCP",
           yerr=get_data['mcp_std'], capsize=4, error_kw={'capthick': 1})
    ax.bar(x[0] + width, get_data['rest_mcp_mean'], width, color=layered_color, label="Layered MCP",
           yerr=get_data['rest_mcp_std'], capsize=4, error_kw={'capthick': 1})
    
    # Search Model Cards bars
    ax.bar(x[1] - width, search_data['rest_mean'], width, color=rest_color,
           yerr=search_data['rest_std'], capsize=4, error_kw={'capthick': 1})
    ax.bar(x[1], search_data['mcp_mean'], width, color=mcp_color,
           yerr=search_data['mcp_std'], capsize=4, error_kw={'capthick': 1})
    ax.bar(x[1] + width, search_data['rest_mcp_mean'], width, color=layered_color,
           yerr=search_data['rest_mcp_std'], capsize=4, error_kw={'capthick': 1})
    
    ax.set_ylabel("Latency (ms)", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(["Get Model Card", "Search Model Cards"], fontsize=10)
    # ax.set_title("Latency Comparison: REST vs Native MCP vs Layered MCP", fontsize=14)
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend(loc='upper right', fontsize=8)
    
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

def process_operation(operation_name: str, rest_run: Path, mcp_run: Path, 
                      layered_mcp_run: Path, db_run: Path) -> dict | None:
    """Process results for a single operation and return statistics."""
    filename = f"{operation_name}.csv"
    
    # Read data from all sources
    rest_data = read_durations(rest_run, filename)
    mcp_data = read_durations(mcp_run, filename)
    layered_mcp_data = read_durations(layered_mcp_run, filename)
    db_latency = read_db_latency(db_run, filename)
    
    # Check for missing data
    if rest_data is None or mcp_data is None or layered_mcp_data is None:
        print(f"\nMissing {filename} in REST, MCP, or Layered MCP results.")
        return None
    if db_latency is None:
        print(f"\nMissing {filename} in DB results.")
        return None
    
    # Convert to milliseconds and calculate statistics
    rest_ms = rest_data * 1000.0
    mcp_ms = mcp_data * 1000.0
    layered_mcp_ms = layered_mcp_data * 1000.0
    
    rest_mean, rest_std = float(rest_ms.mean()), float(rest_ms.std())
    mcp_mean, mcp_std = float(mcp_ms.mean()), float(mcp_ms.std())
    layered_mcp_mean, layered_mcp_std = float(layered_mcp_ms.mean()), float(layered_mcp_ms.std())
    db_mean, db_std = db_latency
    
    # Print results
    print(f"\n{operation_name} Results (mean ± std):")
    print(f"  Database: {db_mean:.1f} ± {db_std:.1f} ms")
    print(f"  REST:     {rest_mean:.1f} ± {rest_std:.1f} ms (overhead: {rest_mean - db_mean:.1f} ms)")
    print(f"  MCP:      {mcp_mean:.1f} ± {mcp_std:.1f} ms (overhead: {mcp_mean - db_mean:.1f} ms)")
    print(f"  Layered MCP: {layered_mcp_mean:.1f} ± {layered_mcp_std:.1f} ms (overhead: {layered_mcp_mean - db_mean:.1f} ms)")
    
    return {
        'rest_mean': rest_mean,
        'rest_std': rest_std,
        'mcp_mean': mcp_mean,
        'mcp_std': mcp_std,
        'rest_mcp_mean': layered_mcp_mean,
        'rest_mcp_std': layered_mcp_std,
        'db_mean': db_mean,
        'db_std': db_std
    }

def main():
    try:
        rest_run = latest_run_dir(REST_DIR)
        mcp_run = latest_run_dir(MCP_DIR)
        layered_mcp_run = latest_run_dir(LAYERED_MCP_DIR)
    except FileNotFoundError as e:
        print(f"Missing results directory: {e}")
        return
    
    # Process each operation
    get_data = process_operation("get_modelcard", rest_run, mcp_run, layered_mcp_run, DB_DIR)
    search_data = process_operation("search_modelcards", rest_run, mcp_run, layered_mcp_run, DB_DIR)
    
    # Generate combined plot
    if get_data and search_data:
        out_path = OUTPUT_DIR / "latency_comparison.png"
        plot_combined_latency_comparison(get_data, search_data, out_path)
        print(f"\nGenerated combined plot: {out_path}")

if __name__ == "__main__":
    main()