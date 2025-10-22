import os
from pathlib import Path
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Configure matplotlib for publication-quality figures
plt.rcParams.update({
    # Font settings - professional serif fonts
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    
    # Figure quality and output
    'figure.dpi': 100,
    'figure.facecolor': 'white',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'savefig.format': 'png',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',
    
    # Grid settings - subtle and professional
    'grid.alpha': 0.25,
    'grid.linewidth': 0.5,
    'grid.color': '#cccccc',
    'grid.linestyle': '-',
    
    # Axis settings - clean and minimal
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'axes.grid': True,
    'axes.axisbelow': True,
    'axes.facecolor': 'white',
    'axes.spines.top': False,
    'axes.spines.right': False,
    
    # Tick settings
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    
    # Legend settings - professional appearance
    'legend.frameon': True,
    'legend.framealpha': 0.95,
    'legend.edgecolor': '#cccccc',
    'legend.fancybox': False,
    'legend.shadow': False,
    
    # Use LaTeX-style math rendering
    'mathtext.default': 'regular',
})

# Defaults for result directories
REST_DIR = Path(os.getenv("REST_RESULTS_DIR", "/home/exouser/client/rest/benchmark_results"))
MCP_DIR = Path(os.getenv("MCP_RESULTS_DIR", "/home/exouser/client/mcp/benchmark_results"))
LAYERED_MCP_DIR = Path(os.getenv("LAYERED_MCP_RESULTS_DIR", "/home/exouser/client/layered_mcp/benchmark_results"))
OUTPUT_DIR = Path(os.getenv("ANALYSIS_OUTPUT_DIR", "/home/exouser/client/analysis/outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Professional color palette - patterns are primary, colors are subtle hints
COLORS = {
    'network': '#e8f2f7',    # Very light blue tint - for overhead
    'database': '#fff4e6',   # Very light warm tint - for database
    'darkgray': '#444444',   # Text/borders
    'lightgray': '#dddddd',  # Grid/backgrounds
    'black': '#000000',      # Primary text/pattern lines
    'white': '#ffffff',      # Background
}

def latest_run_dir(root: Path) -> Path:
    """Find the most recent run directory."""
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    run_dirs = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("run_")]
    if not run_dirs:
        return root
    return sorted(run_dirs)[-1]

def read_latency_breakdown(csv_path: Path) -> pd.DataFrame:
    """Read the detailed latency breakdown CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    # Convert to milliseconds
    for col in df.columns:
        if col != 'timestamp':
            df[col] = df[col] * 1000.0
    
    return df

def read_db_breakdown(csv_path: Path) -> pd.DataFrame:
    """Read the database-level breakdown CSV."""
    if not csv_path.exists():
        return None
    
    df = pd.read_csv(csv_path)
    # All time columns are already in milliseconds
    return df

def plot_single_system_stack(network_df: pd.DataFrame, db_df: pd.DataFrame, 
                            system_name: str, out_path: Path):
    """Create a single stacked bar plot for one system."""
    
    if network_df is None or db_df is None:
        print(f"Skipping {system_name}: missing data")
        return
    
    # Calculate components
    db_latency = db_df['total_ms'].mean()
    total_latency = network_df['total_time'].mean()
    overhead = total_latency - db_latency
    
    fig, ax = plt.subplots(figsize=(3.5, 4))
    
    x_pos = [0]
    width = 0.6
    
    # Create stacked bar - patterns are primary, colors are hints
    bars1 = ax.bar(x_pos, db_latency, width,
                   label='Database',
                   color=COLORS['database'],
                   edgecolor=COLORS['black'],
                   linewidth=1.2,
                   hatch='//////',
                   alpha=1.0)
    
    bars2 = ax.bar(x_pos, overhead, width,
                   bottom=db_latency,
                   label='Overhead',
                   color=COLORS['network'],
                   edgecolor=COLORS['black'],
                   linewidth=1.2,
                   hatch='....',
                   alpha=1.0)
    
    # Formatting
    ax.set_ylabel("Latency (ms)")
    ax.set_title(system_name, pad=10)
    ax.set_xticks([0])
    ax.set_xticklabels(['Request'])
    ax.set_ylim(0, total_latency * 1.15)
    
    # Legend
    ax.legend(loc='upper right', frameon=True, framealpha=0.98,
             edgecolor=COLORS['lightgray'], facecolor='white')
    
    # Grid
    ax.grid(True, axis='y')
    ax.grid(False, axis='x')
    
    fig.tight_layout()
    fig.savefig(out_path, dpi=300, bbox_inches='tight')
    plt.close(fig)
    
    print(f"Saved {system_name} stacked plot to: {out_path}")

def main():
    try:
        # Find latest run directories for all systems
        rest_run = latest_run_dir(REST_DIR)
        print(f"Analyzing REST results from: {rest_run}")
        
        # Try to find MCP and REST+MCP runs
        try:
            mcp_run = latest_run_dir(MCP_DIR)
            print(f"Analyzing Native MCP results from: {mcp_run}")
        except FileNotFoundError:
            mcp_run = None
            print("Native MCP results not found")
        
        try:
            layered_mcp_run = latest_run_dir(LAYERED_MCP_DIR)
            print(f"Analyzing Layered MCP results from: {layered_mcp_run}")
        except FileNotFoundError:
            layered_mcp_run = None
            print("Layered MCP results not found")
        
        # Process both operations
        for operation in ['get_modelcard', 'search_modelcards']:
            operation_title = operation.replace('_', ' ').title()
            
            # Read REST data
            rest_csv_path = rest_run / f"{operation}.csv"
            rest_db_csv_path = rest_run / f"{operation}_db.csv"
            
            if not rest_csv_path.exists():
                print(f"Skipping {operation}: REST CSV not found")
                continue
            
            rest_df = read_latency_breakdown(rest_csv_path)
            rest_db_df = read_db_breakdown(rest_db_csv_path)
            
            # Read MCP data (if available)
            mcp_df = None
            mcp_db_df = None
            if mcp_run:
                mcp_csv_path = mcp_run / f"{operation}.csv"
                mcp_db_csv_path = mcp_run / f"{operation}_db.csv"
                if mcp_csv_path.exists():
                    mcp_df = read_latency_breakdown(mcp_csv_path)
                    mcp_db_df = read_db_breakdown(mcp_db_csv_path)
            
            # Read Layered MCP data (if available)
            layered_mcp_df = None
            layered_mcp_db_df = None
            if layered_mcp_run:
                layered_mcp_csv_path = layered_mcp_run / f"{operation}.csv"
                layered_mcp_db_csv_path = layered_mcp_run / f"{operation}_db.csv"
                if layered_mcp_csv_path.exists():
                    layered_mcp_df = read_latency_breakdown(layered_mcp_csv_path)
                    layered_mcp_db_df = read_db_breakdown(layered_mcp_db_csv_path)
            
            # Create 3 separate stacked plots for each system
            if rest_db_df is not None:
                plot_single_system_stack(
                    network_df=rest_df,
                    db_df=rest_db_df,
                    system_name="REST",
                    out_path=OUTPUT_DIR / f"{operation}_rest.png"
                )
            
            if mcp_df is not None and mcp_db_df is not None:
                plot_single_system_stack(
                    network_df=mcp_df,
                    db_df=mcp_db_df,
                    system_name="Native MCP",
                    out_path=OUTPUT_DIR / f"{operation}_native_mcp.png"
                )
            
            if layered_mcp_df is not None and layered_mcp_db_df is not None:
                plot_single_system_stack(
                    network_df=layered_mcp_df,
                    db_df=layered_mcp_db_df,
                    system_name="Layered MCP",
                    out_path=OUTPUT_DIR / f"{operation}_layered_mcp.png"
                )
        
        print(f"\nAll visualizations saved to: {OUTPUT_DIR}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
