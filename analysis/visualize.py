import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# =============================================================================
# CONFIGURATION
# =============================================================================

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

# Color scheme for visualization
COLORS = {
    'network': '#e8f2f7',    # Very light blue tint - for overhead
    'database': '#fff4e6',   # Very light warm tint - for database
    'darkgray': '#444444',   # Text/borders
    'lightgray': '#dddddd',  # Grid/backgrounds
    'black': '#000000',      # Primary text/pattern lines
    'white': '#ffffff',      # Background
    # Transparent colors for layered visualization
    'db_transparent': '#f0f0f0',      # Very light gray for database
    'rest_transparent': '#ffe6cc',    # Very light orange for REST
    'mcp_transparent': '#e6ffe6',     # Very light green for MCP
}

# Plot configuration
PLOT_CONFIG = {
    'figsize': (5, 4),
    'bar_width': 0.75,
    'fontsize': {
        'xticks': 12,
        'ylabel': 12,
        'legend': 10
    },
    'hatch_patterns': {
        'database': 'o',
        'rest': '+',
        'mcp': '*'
    }
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def latest_run_dir(root: Path) -> Path:
    """Find the most recent benchmark run directory."""
    if not root.exists():
        raise FileNotFoundError(f"Directory does not exist: {root}")
    run_dirs = [p for p in root.iterdir() if p.is_dir() and p.name.startswith("run_")]
    if not run_dirs:
        return root
    return sorted(run_dirs)[-1]

def load_benchmark_data():
    """Load all benchmark data from CSV files."""
    # Define directory paths
    REST_DIR = Path("/home/exouser/client/rest/benchmark_results")
    REST_DB_DIR = REST_DIR / "database"

    MCP_DIR = Path("/home/exouser/client/mcp/benchmark_results")
    MCP_DB_DIR = MCP_DIR / "database"
    
    LAYERED_MCP_DIR = Path("/home/exouser/client/layered_mcp/benchmark_results")
    LAYERED_MCP_DB_DIR = LAYERED_MCP_DIR / "database"
    LAYERED_MCP_REST_DIR = LAYERED_MCP_DIR / "rest"
    
    # Load get_modelcard data
    get_modelcard_data = {
        'rest_db': pd.read_csv(latest_run_dir(REST_DB_DIR) / "get_modelcard.csv"),
        'rest_total': pd.read_csv(latest_run_dir(REST_DIR) / "get_modelcard.csv"),
        'mcp_db': pd.read_csv(latest_run_dir(MCP_DB_DIR) / "get_modelcard.csv"),
        'mcp_total': pd.read_csv(latest_run_dir(MCP_DIR) / "get_modelcard.csv"),
        'layered_mcp_db': pd.read_csv(latest_run_dir(LAYERED_MCP_DB_DIR) / "get_modelcard.csv", 
                                   header=None, names=['total_time']),
        'layered_mcp_rest': pd.read_csv(latest_run_dir(LAYERED_MCP_REST_DIR) / "get_modelcard.csv", 
                                    header=None, names=['total_time']),
        'layered_mcp_total': pd.read_csv(latest_run_dir(LAYERED_MCP_DIR) / "get_modelcard.csv")
    }
    
    # Load search_modelcards data
    search_modelcards_data = {
        'rest_db': pd.read_csv(latest_run_dir(REST_DB_DIR) / "search_modelcard.csv"),
        'rest_total': pd.read_csv(latest_run_dir(REST_DIR) / "search_modelcards.csv"),
        'mcp_db': pd.read_csv(latest_run_dir(MCP_DB_DIR) / "search_modelcard.csv"),
        'mcp_total': pd.read_csv(latest_run_dir(MCP_DIR) / "search_modelcards.csv"),
        'layered_mcp_db': pd.read_csv(latest_run_dir(LAYERED_MCP_DB_DIR) / "search_modelcard.csv", 
                                  header=None, names=['total_time']),
        'layered_mcp_rest': pd.read_csv(latest_run_dir(LAYERED_MCP_REST_DIR) / "search_modelcard.csv", 
                                    header=None, names=['total_time']),
        'layered_mcp_total': pd.read_csv(latest_run_dir(LAYERED_MCP_DIR) / "search_modelcards.csv")
    }
    
    return get_modelcard_data, search_modelcards_data

def convert_to_milliseconds(data_dict):
    """Convert all total_time columns from seconds to milliseconds."""
    for key, df in data_dict.items():
        if 'total' in key and 'db' not in key:
            df["total_time"] = df["total_time"] * 1000.0

def calculate_metrics(data_dict):
    """Calculate performance metrics from benchmark data."""
    # REST metrics
    rest_total = data_dict['rest_total']["total_time"].mean()
    rest_db = data_dict['rest_db']["total_time"].mean()
    rest_net = rest_total - rest_db
    
    # Native MCP metrics
    mcp_total = data_dict['mcp_total']["total_time"].mean()
    mcp_db = data_dict['mcp_db']["total_time"].mean()
    mcp_net = mcp_total - mcp_db
    
    # Layered MCP metrics
    layered_mcp_total = data_dict['layered_mcp_total']["total_time"].mean()
    layered_mcp_db = data_dict['layered_mcp_db']["total_time"].mean()
    layered_mcp_rest = data_dict['layered_mcp_rest']["total_time"].mean()
    layered_mcp_net = layered_mcp_total - layered_mcp_rest
    
    return {
        'rest': {'total': rest_total, 'db': rest_db, 'net': rest_net},
        'native_mcp': {'total': mcp_total, 'db': mcp_db, 'net': mcp_net},
        'layered_mcp': {'total': layered_mcp_total, 'db': layered_mcp_db, 'rest': layered_mcp_rest, 'net': layered_mcp_net}
    }

def calculate_standard_deviations(data_dict):
    """Calculate standard deviations for error bars."""
    # REST standard deviations
    rest_db_std = data_dict['rest_db']["total_time"].std()
    rest_net_std = (data_dict['rest_total']["total_time"] - data_dict['rest_db']["total_time"]).std()
    
    # Native MCP standard deviations
    mcp_db_std = data_dict['mcp_db']["total_time"].std()
    mcp_net_std = (data_dict['mcp_total']["total_time"] - data_dict['mcp_db']["total_time"]).std()
    
    # Layered MCP standard deviations
    layered_mcp_db_std = data_dict['layered_mcp_db']["total_time"].std()
    layered_mcp_rest_std = data_dict['layered_mcp_rest']["total_time"].std()
    layered_mcp_net_std = (data_dict['layered_mcp_total']["total_time"] - 
                        data_dict['layered_mcp_db']["total_time"] - 
                        data_dict['layered_mcp_rest']["total_time"]).std()
    
    return {
        'rest': {'db_std': rest_db_std, 'net_std': rest_net_std},
        'native_mcp': {'db_std': mcp_db_std, 'net_std': mcp_net_std},
        'layered_mcp': {'db_std': layered_mcp_db_std, 'rest_std': layered_mcp_rest_std, 'net_std': layered_mcp_net_std}
    }

# =============================================================================
# PLOTTING FUNCTIONS
# =============================================================================

def create_stacked_bar_plot(metrics, std_devs, title, output_path):
    """Create a stacked bar plot showing performance breakdown."""
    plt.figure(figsize=PLOT_CONFIG['figsize'])
    bar_width = PLOT_CONFIG['bar_width']
    x = [0, 1, 2]
    
    # Extract metrics
    rest = metrics['rest']
    native_mcp = metrics['native_mcp']
    layered_mcp = metrics['layered_mcp']
    
    # REST bar: Database + REST Overhead
    plt.bar(x[0], rest['db'], width=bar_width, label='Database Overhead',
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=0.8)
    plt.bar(x[0], rest['net'], width=bar_width, bottom=rest['db'], label='REST Overhead',
            color=COLORS['rest_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['rest'], alpha=0.8)
    
    # Native MCP bar: Database + MCP Overhead
    plt.bar(x[1], native_mcp['db'], width=bar_width,
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=0.8)
    plt.bar(x[1], native_mcp['net'], width=bar_width, bottom=native_mcp['db'], label='MCP Overhead',
            color=COLORS['mcp_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['mcp'], alpha=0.8)
    
    # Layered MCP bar: Database + REST + MCP
    plt.bar(x[2], layered_mcp['db'], width=bar_width,
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=0.8)
    plt.bar(x[2], layered_mcp['rest'], width=bar_width, bottom=layered_mcp['db'],
            color=COLORS['rest_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['rest'], alpha=0.8)
    plt.bar(x[2], layered_mcp['net'], width=bar_width, 
            bottom=layered_mcp['db'] + layered_mcp['rest'],
            color=COLORS['mcp_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['mcp'], alpha=0.8)
    
    # Configure plot appearance
    plt.title(title, fontsize=14, fontweight='bold')
    plt.xticks(x, ["REST", "Native MCP", "Layered MCP"], 
               fontsize=PLOT_CONFIG['fontsize']['xticks'])
    plt.ylabel("Latency (ms)", fontsize=PLOT_CONFIG['fontsize']['ylabel'])
    plt.legend(fontsize=PLOT_CONFIG['fontsize']['legend'], loc='upper left', 
               frameon=True, framealpha=0.98, 
             edgecolor=COLORS['lightgray'], facecolor='white')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def print_performance_summary(metrics, endpoint_name):
    """Print a formatted performance summary."""
    print(f"\n{endpoint_name.upper()}:")
    rest = metrics['rest']
    native_mcp = metrics['native_mcp']
    layered_mcp = metrics['layered_mcp']
    
    print(f"REST: total={rest['total']:.2f}ms, db={rest['db']:.2f}ms, net={rest['net']:.2f}ms")
    print(f"Native MCP: total={native_mcp['total']:.2f}ms, db={native_mcp['db']:.2f}ms, net={native_mcp['net']:.2f}ms")
    print(f"Layered MCP: total={layered_mcp['total']:.2f}ms, db={layered_mcp['db']:.2f}ms, "
          f"rest={layered_mcp['rest']:.2f}ms, mcp={layered_mcp['net']:.2f}ms")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    # Load benchmark data
    get_modelcard_data, search_modelcards_data = load_benchmark_data()
    
    # Convert to milliseconds
    convert_to_milliseconds(get_modelcard_data)
    convert_to_milliseconds(search_modelcards_data)
    
    # Calculate metrics for get_modelcard
    get_modelcard_metrics = calculate_metrics(get_modelcard_data)
    get_modelcard_std = calculate_standard_deviations(get_modelcard_data)
    
    # Create get_modelcard plot
    create_stacked_bar_plot(
        get_modelcard_metrics, 
        get_modelcard_std,
        "Model Card Retrieval",
        "/home/exouser/client/analysis/outputs/get_modelcard_breakdown.png"
    )
    
    # Print get_modelcard summary
    print_performance_summary(get_modelcard_metrics, "GET_MODELCARD")
    
    # Calculate metrics for search_modelcards
    search_modelcards_metrics = calculate_metrics(search_modelcards_data)
    search_modelcards_std = calculate_standard_deviations(search_modelcards_data)
    
    # Create search_modelcards plot
    create_stacked_bar_plot(
        search_modelcards_metrics,
        search_modelcards_std,
        "Model Cards Search", 
        "/home/exouser/client/analysis/outputs/search_modelcards_breakdown.png"
    )
    
    # Print search_modelcards summary
    print_performance_summary(search_modelcards_metrics, "SEARCH_MODELCARDS")

if __name__ == "__main__":
    main()