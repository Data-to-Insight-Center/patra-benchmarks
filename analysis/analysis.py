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
REST_MCP_DIR = Path(os.getenv("REST_MCP_RESULTS_DIR", "/home/exouser/client/rest_mcp/benchmark_results"))
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
    """Read DB latency from timestamps CSV and return (mean, std) in ms."""
    path = run_dir / filename
    if not path.exists():
        return None
    
    # Read the first line to check if it's a header
    with open(path, 'r') as f:
        first_line = f.readline().strip()
    
    # Check if first line contains column names (has 'timestamp' in it)
    has_header = 'timestamp' in first_line.lower()
    
    if has_header:
        df = pd.read_csv(path)
        if df.empty:
            return None
        # Strip whitespace from column names
        df.columns = df.columns.str.strip()
        # Calculate latency: enrich_xai_analysis_timestamp - start_timestamp
        latencies = (df['enrich_xai_analysis_timestamp'] - df['start_timestamp']) * 1000.0
    else:
        # No header, just start and end timestamps in two columns
        df = pd.read_csv(path, header=None)
        if df.empty or df.shape[1] < 2:
            return None
        latencies = (df.iloc[:, 1] - df.iloc[:, 0]) * 1000.0  # Convert to ms
    
    return float(latencies.mean()), float(latencies.std())

def plot_stacked_latency_comparison(rest_mean_ms: float, rest_std_ms: float,
                                     mcp_mean_ms: float, mcp_std_ms: float,
                                     rest_mcp_mean_ms: float, rest_mcp_std_ms: float,
                                     db_mean_ms: float, db_std_ms: float,
                                     title: str, out_path: Path) -> None:
    """Plot stacked bar chart comparing MCP and REST+MCP latencies with DB baseline."""
    x = np.arange(2)  # Two bars: MCP and REST+MCP
    width = 0.6
    
    # Color scheme
    db_color = "#4C78A8"      # Blue for Database
    rest_color = "#59A14F"    # Green for REST overhead
    mcp_color = "#F28E2B"     # Orange for MCP overhead
    
    fig, ax = plt.subplots(figsize=(7, 5))
    
    # MCP bar: DB + MCP overhead
    ax.bar(x[0], db_mean_ms, width, color=db_color, label="Database", 
           yerr=db_std_ms, capsize=4, error_kw={'capthick': 1})
    ax.bar(x[0], mcp_mean_ms - db_mean_ms, width, bottom=db_mean_ms,
           color=mcp_color, label="MCP overhead",
           yerr=np.sqrt(mcp_std_ms**2 + db_std_ms**2), capsize=4, error_kw={'capthick': 1})
    
    # REST+MCP bar: DB + REST overhead + MCP overhead
    ax.bar(x[1], db_mean_ms, width, color=db_color,
           yerr=db_std_ms, capsize=4, error_kw={'capthick': 1})
    ax.bar(x[1], rest_mean_ms - db_mean_ms, width, bottom=db_mean_ms,
           color=rest_color, label="REST overhead",
           yerr=np.sqrt(rest_std_ms**2 + db_std_ms**2), capsize=4, error_kw={'capthick': 1})
    ax.bar(x[1], rest_mcp_mean_ms - rest_mean_ms, width, bottom=rest_mean_ms,
           color=mcp_color,
           yerr=np.sqrt(rest_mcp_std_ms**2 + rest_std_ms**2), capsize=4, error_kw={'capthick': 1})
    
    ax.set_ylabel("Latency (ms)")
    ax.set_xticks(x)
    ax.set_xticklabels(["MCP", "REST+MCP"])
    ax.set_title(title)
    ax.grid(True, axis='y', alpha=0.3)
    ax.legend(loc='upper left', fontsize=10)
    
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)

def process_operation(operation_name: str, rest_run: Path, mcp_run: Path, 
                      rest_mcp_run: Path, db_run: Path) -> None:
    """Process and plot results for a single operation."""
    filename = f"{operation_name}.csv"
    
    # Read data from all sources
    rest_data = read_durations(rest_run, filename)
    mcp_data = read_durations(mcp_run, filename)
    rest_mcp_data = read_durations(rest_mcp_run, filename)
    db_latency = read_db_latency(db_run, filename)
    
    # Check for missing data
    if rest_data is None or mcp_data is None or rest_mcp_data is None:
        print(f"\nMissing {filename} in REST, MCP, or REST+MCP results.")
        return
    if db_latency is None:
        print(f"\nMissing {filename} in DB results.")
        return
    
    # Convert to milliseconds and calculate statistics
    rest_ms = rest_data * 1000.0
    mcp_ms = mcp_data * 1000.0
    rest_mcp_ms = rest_mcp_data * 1000.0
    
    rest_mean, rest_std = float(rest_ms.mean()), float(rest_ms.std())
    mcp_mean, mcp_std = float(mcp_ms.mean()), float(mcp_ms.std())
    rest_mcp_mean, rest_mcp_std = float(rest_mcp_ms.mean()), float(rest_mcp_ms.std())
    db_mean, db_std = db_latency
    
    # Generate plot
    out_path = OUTPUT_DIR / f"latency_{operation_name}_comparison.png"
    plot_stacked_latency_comparison(rest_mean, rest_std, mcp_mean, mcp_std,
                                    rest_mcp_mean, rest_mcp_std, db_mean, db_std,
                                    operation_name, out_path)
    
    # Print results
    print(f"\n{operation_name} Results (mean ± std):")
    print(f"  Database: {db_mean:.1f} ± {db_std:.1f} ms")
    print(f"  REST:     {rest_mean:.1f} ± {rest_std:.1f} ms (overhead: {rest_mean - db_mean:.1f} ms)")
    print(f"  MCP:      {mcp_mean:.1f} ± {mcp_std:.1f} ms (overhead: {mcp_mean - db_mean:.1f} ms)")
    print(f"  REST+MCP: {rest_mcp_mean:.1f} ± {rest_mcp_std:.1f} ms (overhead: {rest_mcp_mean - db_mean:.1f} ms)")

def main():
    try:
        rest_run = latest_run_dir(REST_DIR)
        mcp_run = latest_run_dir(MCP_DIR)
        rest_mcp_run = latest_run_dir(REST_MCP_DIR)
    except FileNotFoundError as e:
        print(f"Missing results directory: {e}")
        return
    
    # Process each operation
    process_operation("get_modelcard", rest_run, mcp_run, rest_mcp_run, DB_DIR)
    process_operation("search_modelcards", rest_run, mcp_run, rest_mcp_run, DB_DIR)

if __name__ == "__main__":
    main()