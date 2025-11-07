#!/usr/bin/env python3
"""
Side-by-side stacked bar plot comparing REST and MCP request latency breakdowns.
Ignores latency components < 5ms for cleaner publication-ready plots.
Labels are displayed directly on bars with contrasting colors.
"""

import csv
import statistics
import matplotlib.pyplot as plt
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

    # Tick settings
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'xtick.direction': 'out',
    'ytick.direction': 'out',

    # Legend settings - professional appearance
    'legend.frameon': True,
    'legend.edgecolor': '#cccccc',
    'legend.fancybox': False,
    'legend.shadow': False,

    # Use LaTeX-style math rendering
    'mathtext.default': 'regular',
})

# Color scheme - high contrast colors for publication
COLORS = {
    'black': '#000000',      # Primary text/borders
    'white': '#ffffff',      # Background/text on dark
    # REST component colors
    'dns': '#1f77b4',        # Strong blue
    'tcp': '#ff7f0e',        # Bright orange
    'tls': '#2ca02c',        # Green
    'server': '#d62728',     # Red
    'transfer': '#9467bd',   # Purple
    'db': '#8c564b',         # Brown
    # MCP component colors
    'connection': '#1f77b4',  # Strong blue
    'handshake': '#ff7f0e',   # Bright orange
    'resource': '#2ca02c',    # Green
    'rest_latency': '#d62728', # Red
    'db_mcp': '#9467bd',      # Purple
}


# =============================================================================
# DATA LOADING AND ANALYSIS
# =============================================================================

def load_and_analyze_data(csv_file='curl_timing_results.csv', db_file='db.csv'):
    """Load CSV data and calculate statistics."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Extract metrics
    dns_lookups = [float(row['dns_lookup_ms']) for row in data]
    tcp_connects = [float(row['tcp_connect_ms']) for row in data]
    tls_handshakes = [float(row['tls_handshake_ms']) for row in data]
    time_pretransfers = [float(row['time_pretransfer_ms']) for row in data]
    ttfbs = [float(row['time_to_first_byte_ms']) for row in data]
    total_times = [float(row['total_time_ms']) for row in data]

    # Calculate derived metrics
    tcp_only = [tcp_connects[i] - dns_lookups[i] for i in range(len(data))]
    server_processing = [ttfbs[i] - time_pretransfers[i] for i in range(len(data))]
    content_transfer = [total_times[i] - ttfbs[i] for i in range(len(data))]

    # Load database latency if available
    db_latencies = []
    try:
        with open(db_file, 'r') as f:
            db_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {db_file} not found, skipping database latency overlay")

    components = {
        'DNS Lookup': dns_lookups,
        'TCP Connection': tcp_only,
        'TLS Handshake': tls_handshakes,
        'Server Processing': server_processing,
        'Content Transfer': content_transfer,
    }

    if db_latencies:
        components['Database Latency'] = db_latencies

    # Calculate statistics
    stats = {}
    for name, values in components.items():
        stats[name] = {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
        }

    return stats

def load_and_analyze_mcp_data(csv_file='../mcp/mcp_timing_results.csv', db_file='../mcp/db.csv', rest_file='../mcp/rest.csv'):
    """Load MCP CSV data and calculate statistics."""
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        data = list(reader)

    # Extract metrics
    connections = [float(row['connection_ms']) for row in data]
    handshakes = [float(row['handshake_ms']) for row in data]
    resources = [float(row['resource_read_ms']) for row in data]

    # Load REST latency if available
    rest_latencies = []
    try:
        with open(rest_file, 'r') as f:
            rest_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {rest_file} not found, skipping REST latency overlay")

    # Load database latency if available
    db_latencies = []
    try:
        with open(db_file, 'r') as f:
            db_latencies = [float(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Warning: {db_file} not found, skipping database latency overlay")

    components = {
        'Connection Setup': connections,
        'MCP Handshake': handshakes,
        'Resource Read': resources,
    }

    if rest_latencies:
        components['REST Latency'] = rest_latencies

    if db_latencies:
        components['Database Latency'] = db_latencies

    # Calculate statistics
    stats = {}
    for name, values in components.items():
        stats[name] = {
            'mean': statistics.mean(values),
            'median': statistics.median(values),
            'min': min(values),
            'max': max(values),
            'p95': sorted(values)[int(len(values) * 0.95)],
        }

    return stats

# =============================================================================
# VISUALIZATION FUNCTIONS
# =============================================================================

def create_comparison_plot(rest_stats, mcp_stats, output_path='latency_comparison.png'):
    """Create side-by-side stacked bar plots comparing REST and MCP latency breakdowns."""

    fig, ax = plt.subplots(figsize=(6, 3.5))

    # Define REST components with colors
    rest_components = [
        ('DNS Lookup', COLORS['dns']),
        ('TCP Connection', COLORS['tcp']),
        ('TLS Handshake', COLORS['tls']),
        ('Server Processing', COLORS['server']),
        ('Content Transfer', COLORS['transfer']),
    ]
    if 'Database Latency' in rest_stats:
        rest_components.insert(4, ('Database Latency', COLORS['db']))

    # Define MCP components with colors
    mcp_components = [
        ('Connection Setup', COLORS['connection']),
        ('MCP Handshake', COLORS['handshake']),
        ('Resource Read', COLORS['resource']),
    ]
    if 'REST Latency' in mcp_stats:
        mcp_components.append(('REST Latency', COLORS['rest_latency']))
    if 'Database Latency' in mcp_stats:
        mcp_components.append(('Database Latency', COLORS['db_mcp']))

    # Filter REST components >= 5ms
    rest_significant = []
    for label, color in rest_components:
        if label in rest_stats:
            duration = rest_stats[label]['mean']
            if duration >= 5.0:
                rest_significant.append((label, color, duration))

    # Filter MCP components >= 5ms
    mcp_significant = []
    for label, color in mcp_components:
        if label in mcp_stats:
            duration = mcp_stats[label]['mean']
            if duration >= 5.0:
                mcp_significant.append((label, color, duration))

    # Create REST stacked bar
    bar_width = 0.35
    rest_x = 0
    bottom = 0
    for label, color, height in rest_significant:
        ax.bar(rest_x, height, bottom=bottom, color=color,
              edgecolor=COLORS['black'], linewidth=1.2, alpha=1.0,
              width=bar_width)

        # Add text label on the bar
        ax.text(rest_x, bottom + height/2, label,
               ha='center', va='center', fontsize=8, fontweight='bold',
               color=COLORS['white'])

        bottom += height

    # Create MCP stacked bar
    mcp_x = 0.5
    bottom = 0
    for label, color, height in mcp_significant:
        ax.bar(mcp_x, height, bottom=bottom, color=color,
              edgecolor=COLORS['black'], linewidth=1.2, alpha=1.0,
              width=bar_width)

        # Add text label on the bar
        ax.text(mcp_x, bottom + height/2, label,
               ha='center', va='center', fontsize=8, fontweight='bold',
               color=COLORS['white'])

        bottom += height

    # Configure axes
    ax.set_xticks([rest_x, mcp_x])
    ax.set_xticklabels(['REST', 'MCP'], fontsize=10, fontweight='bold')
    ax.set_ylabel('Latency (ms)', fontsize=10, fontweight='bold')

    # Set y-axis limit with some padding
    max_height = max(
        sum(h for _, _, h in rest_significant),
        sum(h for _, _, h in mcp_significant)
    )
    ax.set_ylim(0, max_height * 1.1)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"Comparison plot saved to: {output_path}")
    plt.close()

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main execution function."""
    print("="*80)
    print("Creating REST vs MCP Latency Comparison Plot")
    print("="*80)

    # Load and analyze REST data
    print("\nLoading REST data...")
    rest_stats = load_and_analyze_data()

    # Load and analyze MCP data
    print("Loading MCP data...")
    mcp_stats = load_and_analyze_mcp_data()

    # Create comparison plot
    output_file = 'latency_comparison.png'
    create_comparison_plot(rest_stats, mcp_stats, output_file)

    print("\n" + "="*80)
    print("Visualization created successfully!")
    print("="*80)
    print(f"\nGenerated file: {output_file}")

if __name__ == "__main__":
    main()
