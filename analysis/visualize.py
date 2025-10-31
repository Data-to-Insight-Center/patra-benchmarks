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
    # 'axes.spines.top': False,
    # 'axes.spines.right': False,
    
    # Tick settings
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    
    # Legend settings - professional appearance
    'legend.frameon': True,
    # 'legend.framealpha': 0.95,
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
    'db_transparent': '#e8f2f7',      # light blue
    'rest_transparent': '#ffe6cc',    # Very light orange for REST
    'mcp_transparent': '#e6ffe6',     # Very light green for MCP
}

# Plot configuration
PLOT_CONFIG = {
    'figsize': (4, 3.5),
    'bar_width': 0.75,
    'fontsize': {
        'xticks': 10,
        'ylabel': 10,
        'legend': 7
    },
    'fontweight': {
        'xticks': 'bold',
        'ylabel': 'bold',
        'legend': 'bold'
    },
    'hatch_patterns': {
        'database': '..',
        'rest': 'xx',
        'mcp': '//'
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
    # Define directory paths for today's run
    today = "2025_10_31"
    REST_DIR = Path(f"/home/exouser/patra-benchmarks/rest/benchmark_results/run_{today}")
    MCP_LAYERED_DIR = Path(f"/home/exouser/patra-benchmarks/mcp/benchmark_results/run_{today}/layered")
    MCP_NATIVE_DIR = Path(f"/home/exouser/patra-benchmarks/mcp/benchmark_results/run_{today}/native")
    
    # Load get_modelcard data for today's run
    get_modelcard_data = {
        'rest_db': pd.read_csv(REST_DIR / "get_modelcard_db.csv", header=None, names=['total_time']),
        'rest_total': pd.read_csv(REST_DIR / "get_modelcard_rtt.csv")[['response_time_ms', 'response_size_kb']].rename(columns={'response_time_ms': 'total_time'}),
        'mcp_db': pd.read_csv(MCP_NATIVE_DIR / "get_modelcard_db.csv", header=None, names=['total_time']),
        'mcp_total': pd.read_csv(MCP_NATIVE_DIR / "get_modelcard_rtt.csv")[['response_time_ms', 'response_size_kb']].rename(columns={'response_time_ms': 'total_time'}),
        'layered_mcp_db': pd.read_csv(MCP_LAYERED_DIR / "get_modelcard_db.csv", header=None, names=['total_time']),
        'layered_mcp_rest': pd.read_csv(MCP_LAYERED_DIR / "get_modelcard_rest.csv", header=None, names=['total_time']),
        'layered_mcp_total': pd.read_csv(MCP_LAYERED_DIR / "get_modelcard_rtt.csv")[['response_time_ms', 'response_size_kb']].rename(columns={'response_time_ms': 'total_time'})
    }
    
    # For now, we only have get_modelcard data, so we'll return empty search data
    search_modelcards_data = {
        'rest_db': pd.DataFrame({'total_time': []}),
        'rest_total': pd.DataFrame({'total_time': [], 'response_size_kb': []}),
        'mcp_db': pd.DataFrame({'total_time': []}),
        'mcp_total': pd.DataFrame({'total_time': [], 'response_size_kb': []}),
        'layered_mcp_db': pd.DataFrame({'total_time': []}),
        'layered_mcp_rest': pd.DataFrame({'total_time': []}),
        'layered_mcp_total': pd.DataFrame({'total_time': [], 'response_size_kb': []})
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
    rest_response_size = data_dict['rest_total']["response_size_kb"].mean()
    
    # Native MCP metrics
    mcp_total = data_dict['mcp_total']["total_time"].mean()
    mcp_db = data_dict['mcp_db']["total_time"].mean()
    mcp_net = mcp_total - mcp_db
    mcp_response_size = data_dict['mcp_total']["response_size_kb"].mean()
    
    # Layered MCP metrics - use REST network overhead and MCP network overhead
    layered_mcp_total = data_dict['layered_mcp_total']["total_time"].mean()
    layered_mcp_rest = data_dict['layered_mcp_rest']["total_time"].mean()
    layered_mcp_db = data_dict['layered_mcp_db']["total_time"].mean()
    layered_mcp_response_size = data_dict['layered_mcp_total']["response_size_kb"].mean()
    
    layered_mcp_rest_net = layered_mcp_rest - layered_mcp_db
    layered_mcp_net = layered_mcp_total - layered_mcp_rest
    
    return {
        'rest': {'total': rest_total, 'db': rest_db, 'net': rest_net, 'response_size_kb': rest_response_size},
        'native_mcp': {'total': mcp_total, 'db': mcp_db, 'net': mcp_net, 'response_size_kb': mcp_response_size},
        'layered_mcp': {'total': layered_mcp_total, 'db': layered_mcp_db, 'rest': layered_mcp_rest_net, 'net': layered_mcp_net, 'response_size_kb': layered_mcp_response_size}
    }


def calculate_standard_deviations(data_dict):
    """Calculate standard deviations for error bars."""
    # REST standard deviations
    rest_db_std = data_dict['rest_db']["total_time"].std()
    rest_std = data_dict['rest_total']["total_time"].std()
    
    # Native MCP standard deviations
    mcp_db_std = data_dict['mcp_db']["total_time"].std()
    mcp_std = data_dict['mcp_total']["total_time"].std()
    
    # Layered MCP standard deviations - use REST and MCP network stds
    layered_mcp_db_std = data_dict['layered_mcp_db']["total_time"].std()
    layered_mcp_rest_std = data_dict['layered_mcp_rest']["total_time"].std()
    layered_mcp_std = data_dict['layered_mcp_total']["total_time"].std()
    
    return {
        'rest': {'db_std': rest_db_std, 'rest_std': rest_std},
        'native_mcp': {'db_std': mcp_db_std, 'mcp_std': mcp_std},
        'layered_mcp': {'db_std': layered_mcp_db_std, 'rest_std': layered_mcp_rest_std, 'mcp_std': layered_mcp_std}
    }

# =============================================================================
# PLOTTING FUNCTIONS
# =============================================================================

def create_stacked_bar_plot(metrics, std_devs, title, output_path):
    """Create a stacked bar plot showing performance breakdown."""
    plt.figure(figsize=PLOT_CONFIG['figsize'])
    bar_width = PLOT_CONFIG['bar_width']
    x = [0, 1, 2]
    alpha_value = 1  # Lower alpha for transparency
    
    # Extract metrics and standard deviations
    rest = metrics['rest']
    native_mcp = metrics['native_mcp']
    layered_mcp = metrics['layered_mcp']
    
    rest_std = std_devs['rest']
    native_mcp_std = std_devs['native_mcp']
    layered_mcp_std = std_devs['layered_mcp']
    
    # REST bar: Database + REST Network Overhead
    plt.bar(x[0], rest['db'], width=bar_width, label='Database',
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=alpha_value)
    plt.bar(x[0], rest['net'], width=bar_width, bottom=rest['db'], label='REST',
            color=COLORS['rest_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['rest'], alpha=alpha_value)
    
    # Native MCP bar: Database + MCP Network Overhead
    plt.bar(x[1], native_mcp['db'], width=bar_width,
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=alpha_value)
    plt.bar(x[1], native_mcp['net'], width=bar_width, bottom=native_mcp['db'], label='MCP',
            color=COLORS['mcp_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['mcp'], alpha=alpha_value)
    
    # Layered MCP bar: Database + REST Network + MCP Network
    plt.bar(x[2], layered_mcp['db'], width=bar_width,
            color=COLORS['db_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['database'], alpha=alpha_value)
    plt.bar(x[2], layered_mcp['rest'], width=bar_width, bottom=layered_mcp['db'],
            color=COLORS['rest_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['rest'], alpha=alpha_value)
    plt.bar(x[2], layered_mcp['net'], width=bar_width, 
            bottom=layered_mcp['db'] + layered_mcp['rest'],
            color=COLORS['mcp_transparent'], edgecolor=COLORS['black'],
            linewidth=1.2, hatch=PLOT_CONFIG['hatch_patterns']['mcp'], alpha=alpha_value)
    
    # # REST error bars
    # plt.errorbar(x[0], rest['total'], yerr=rest_std['rest_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    # plt.errorbar(x[0], rest['db'], yerr=rest_std['db_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    
    # # Native MCP error bars
    # plt.errorbar(x[1], native_mcp['total'], yerr=native_mcp_std['mcp_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    # plt.errorbar(x[1], native_mcp['db'], yerr=native_mcp_std['db_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    
    # # Layered MCP error bars
    # plt.errorbar(x[2], layered_mcp['total'], yerr=layered_mcp_std['mcp_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    # plt.errorbar(x[2], layered_mcp['rest'] + layered_mcp['db'], yerr=layered_mcp_std['rest_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    # plt.errorbar(x[2], layered_mcp['db'], yerr=layered_mcp_std['db_std'], 
    #             fmt='none', color='black', capsize=5, capthick=1.5, elinewidth=1.5)
    
    # Configure plot appearance
    # plt.title(title, fontsize=14, fontweight='bold')
    plt.xticks(x, ["REST", "Native\nMCP", "Layered\nMCP"], 
               fontsize=PLOT_CONFIG['fontsize']['xticks'], fontweight=PLOT_CONFIG['fontweight']['xticks'])
    plt.ylabel("Latency (ms)", fontsize=PLOT_CONFIG['fontsize']['ylabel'], fontweight=PLOT_CONFIG['fontweight']['ylabel'])
    plt.legend(fontsize=PLOT_CONFIG['fontsize']['legend'], loc='best', 
               frameon=True, framealpha=0.98, 
               edgecolor=COLORS['lightgray'], facecolor='white')
    plt.grid(True, alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def print_performance_summary(metrics, endpoint_name):
    """Print a formatted performance summary."""
    print(f"\n{endpoint_name.upper()}:")
    rest = metrics['rest']
    native_mcp = metrics['native_mcp']
    layered_mcp = metrics['layered_mcp']
    
    import csv

    # Prepare metrics data for CSV
    csv_data = [
        {
            'Implementation': 'REST',
            'Response Size (KB)': rest['response_size_kb'].mean(),
            'Total Latency (ms)': rest['total'],
            'DB Latency (ms)': rest['db'],
            'REST Layer (ms)': rest['net'],  # Not applicable
            'MCP Layer (ms)': ''    # Not applicable
        },
        {
            'Implementation': 'Native MCP',
            'Response Size (KB)': native_mcp['response_size_kb'].mean(),
            'Total Latency (ms)': native_mcp['total'],
            'DB Latency (ms)': native_mcp['db'],
            'REST Layer (ms)': '',   # Not applicable
            'MCP Layer (ms)': native_mcp['net']
        },
        {
            'Implementation': 'Layered MCP',
            'Response Size (KB)': layered_mcp['response_size_kb'].mean(),
            'Total Latency (ms)': layered_mcp['total'],
            'DB Latency (ms)': layered_mcp['db'],
            'REST Layer (ms)': layered_mcp['rest'],
            'MCP Layer (ms)': layered_mcp['net']
        },
    ]
    fieldnames = [
        'Implementation',
        'Response Size (KB)',
        'Total Latency (ms)',
        'DB Latency (ms)',
        'REST Layer (ms)',
        'MCP Layer (ms)'
    ]
    # Compose output csv path
    output_csv = f"/home/exouser/patra-benchmarks/analysis/outputs/{endpoint_name.lower()}_metrics_summary.csv"
    with open(output_csv, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        # Only write header if file is empty
        if csvfile.tell() == 0:
            writer.writeheader()
        for row in csv_data:
            writer.writerow(row)
    print(f"Performance metrics written to {output_csv}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    # Load benchmark data
    get_modelcard_data, search_modelcards_data = load_benchmark_data()
        
    # Calculate metrics for get_modelcard
    get_modelcard_metrics = calculate_metrics(get_modelcard_data)
    get_modelcard_std = calculate_standard_deviations(get_modelcard_data)
    
    # Create output directory if it doesn't exist
    output_dir = Path("/home/exouser/patra-benchmarks/analysis/outputs")
    output_dir.mkdir(exist_ok=True)
    
    # Create get_modelcard plot
    create_stacked_bar_plot(
        get_modelcard_metrics, 
        get_modelcard_std,
        "Model Card Retrieval",
        str(output_dir / "get_modelcard_breakdown.png")
    )
    
    # Print get_modelcard summary
    print_performance_summary(get_modelcard_metrics, "GET_MODELCARD")
    
    # Only process search_modelcards if we have data
    if not search_modelcards_data['rest_total'].empty:
        # Calculate metrics for search_modelcards
        search_modelcards_metrics = calculate_metrics(search_modelcards_data)
        search_modelcards_std = calculate_standard_deviations(search_modelcards_data)
        
        # Create search_modelcards plot
        create_stacked_bar_plot(
            search_modelcards_metrics,
            search_modelcards_std,
            "Model Cards Search", 
            str(output_dir / "search_modelcards_breakdown.png")
        )
        
        # Print search_modelcards summary
        print_performance_summary(search_modelcards_metrics, "SEARCH_MODELCARDS")
    else:
        print("No search_modelcards data available - skipping search visualization")

if __name__ == "__main__":
    main()