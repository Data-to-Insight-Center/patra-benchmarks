import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Configure matplotlib for professional appearance
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Times New Roman', 'DejaVu Serif', 'Computer Modern Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'figure.dpi': 100,
    'figure.facecolor': 'white',
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.05,
    'savefig.format': 'png',
    'savefig.facecolor': 'white',
    'savefig.edgecolor': 'none',
    'grid.alpha': 0.25,
    'grid.linewidth': 0.5,
    'grid.color': '#cccccc',
    'axes.linewidth': 0.8,
    'axes.edgecolor': '#333333',
    'axes.labelcolor': '#333333',
    'axes.grid': True,
    'axes.axisbelow': True,
    'axes.facecolor': 'white',
    'xtick.color': '#333333',
    'ytick.color': '#333333',
    'xtick.direction': 'out',
    'ytick.direction': 'out',
    'legend.frameon': True,
    'legend.edgecolor': '#cccccc',
    'legend.fancybox': False,
    'legend.shadow': False,
})

# Color scheme
COLORS = {
    'REST': '#2E86AB',        # Blue
    'Native MCP': '#A23B72',  # Purple
    'Layered MCP': '#F18F01', # Orange
    'Database': '#fff4e6',    # Light warm tint
    'REST Layer': '#e8f2f7',  # Light blue
    'MCP Layer': '#e6ffe6',   # Light green
}

HATCH_PATTERNS = {
    'Database': '..',
    'REST Layer': 'xx', 
    'MCP Layer': '//'
}

def load_and_group_by_implementation(csv_path):
    """Load CSV data and group by implementation."""
    df = pd.read_csv(csv_path)
    
    # Remove empty rows
    df = df.dropna(subset=['Implementation'])
    
    # Group by implementation
    grouped_by_impl = df.groupby('Implementation')
    
    impl_groups = []
    for impl, group in grouped_by_impl:
        impl_groups.append({
            'implementation': impl,
            'data': group
        })
    
    # Sort by implementation order
    impl_order = ['REST', 'Native MCP', 'Layered MCP']
    impl_groups.sort(key=lambda x: impl_order.index(x['implementation']) if x['implementation'] in impl_order else 999)
    
    return impl_groups

def create_implementation_breakdown_plots(impl_groups, output_dir):
    """Create separate horizontal stacked bar plots for each implementation showing breakdown by model card size."""
    
    for impl_group in impl_groups:
        impl = impl_group['implementation']
        impl_data = impl_group['data']
        
        # Sort data by model card size
        impl_data = impl_data.sort_values('Model Card Size (KB)')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        # Create horizontal bars
        y_pos = np.arange(len(impl_data))
        bar_width = 0.8  # Width of each bar
        
        # Calculate percentages for each model card size
        db_percentages = []
        rest_percentages = []
        mcp_percentages = []
        
        for _, row in impl_data.iterrows():
            # Get latency components
            db_latency = row['DB Latency (ms)']
            rest_layer = row[' REST Layer (ms)'] if pd.notna(row[' REST Layer (ms)']) else 0
            mcp_layer = row['MCP Layer (ms)'] if pd.notna(row['MCP Layer (ms)']) else 0
            total_latency = row['Total Latency (ms)']
            
            # Calculate percentages
            db_pct = (db_latency / total_latency) * 100
            rest_pct = (rest_layer / total_latency) * 100
            mcp_pct = (mcp_layer / total_latency) * 100
            
            db_percentages.append(db_pct)
            rest_percentages.append(rest_pct)
            mcp_percentages.append(mcp_pct)
        
        # Create horizontal stacked bars
        bottom = np.zeros(len(impl_data))
        
        # Database layer
        ax.barh(y_pos, db_percentages, 
               height=bar_width,
               left=bottom,
               color=COLORS['Database'], 
               edgecolor='black', 
               linewidth=1.2, 
               alpha=0.8,
               hatch=HATCH_PATTERNS['Database'],
               label='Database')
        
        # REST layer
        bottom += np.array(db_percentages)
        ax.barh(y_pos, rest_percentages, 
               height=bar_width,
               left=bottom,
               color=COLORS['REST Layer'], 
               edgecolor='black', 
               linewidth=1.2, 
               alpha=0.8,
               hatch=HATCH_PATTERNS['REST Layer'],
               label='REST Layer')
        
        # MCP layer
        bottom += np.array(rest_percentages)
        ax.barh(y_pos, mcp_percentages, 
               height=bar_width,
               left=bottom,
               color=COLORS['MCP Layer'], 
               edgecolor='black', 
               linewidth=1.2, 
               alpha=0.8,
               hatch=HATCH_PATTERNS['MCP Layer'],
               label='MCP Layer')
        
        # Create size labels for Y-axis
        size_labels = []
        for _, row in impl_data.iterrows():
            size_kb = row['Model Card Size (KB)']
            if size_kb < 1000:
                size_labels.append(f'{size_kb:.0f} KB')
            elif size_kb < 10000:
                size_labels.append(f'{size_kb/1000:.1f} MB')
            else:
                size_labels.append(f'{size_kb/1000:.0f} MB')
        
        # Customize plot
        ax.set_yticks(y_pos)
        ax.set_yticklabels(size_labels, fontweight='bold')
        ax.set_xlabel('Percentage (%)', fontweight='bold')
        ax.set_title(f'{impl} - Latency Breakdown by Model Card Size', 
                    fontweight='bold', fontsize=14)
        
        # Set x-axis to show percentages
        ax.set_xlim(0, 100)
        
        # Add grid
        ax.grid(True, alpha=0.3, axis='x')
        
        # Add latency values in white boxes on bars
        for i, (_, row) in enumerate(impl_data.iterrows()):
            db_latency = row['DB Latency (ms)']
            rest_layer = row[' REST Layer (ms)'] if pd.notna(row[' REST Layer (ms)']) else 0
            mcp_layer = row['MCP Layer (ms)'] if pd.notna(row['MCP Layer (ms)']) else 0
            
            # Add labels for each component
            if db_percentages[i] > 5:  # Only show if significant percentage
                ax.text(db_percentages[i]/2, i,
                       f'{db_latency:.0f}\nms', ha='center', va='center',
                       fontweight='bold', fontsize=12,
                       bbox=dict(boxstyle="round,pad=0.4", facecolor='white', alpha=0.9, edgecolor='black'))
            
            if rest_percentages[i] > 5:
                ax.text(db_percentages[i] + rest_percentages[i]/2, i,
                       f'{rest_layer:.0f}\nms', ha='center', va='center',
                       fontweight='bold', fontsize=12,
                       bbox=dict(boxstyle="round,pad=0.4", facecolor='white', alpha=0.9, edgecolor='black'))
            
            if mcp_percentages[i] > 5:
                ax.text(db_percentages[i] + rest_percentages[i] + mcp_percentages[i]/2, i,
                       f'{mcp_layer:.0f}\nms', ha='center', va='center',
                       fontweight='bold', fontsize=12,
                       bbox=dict(boxstyle="round,pad=0.4", facecolor='white', alpha=0.9, edgecolor='black'))
        
        # Create legend with only elements present in this implementation
        legend_elements = []
        if any(pct > 5 for pct in db_percentages):
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLORS['Database'], 
                                               hatch=HATCH_PATTERNS['Database'], edgecolor='black', label='Database'))
        if any(pct > 5 for pct in rest_percentages):
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLORS['REST Layer'], 
                                               hatch=HATCH_PATTERNS['REST Layer'], edgecolor='black', label='REST Layer'))
        if any(pct > 5 for pct in mcp_percentages):
            legend_elements.append(plt.Rectangle((0,0),1,1, facecolor=COLORS['MCP Layer'], 
                                               hatch=HATCH_PATTERNS['MCP Layer'], edgecolor='black', label='MCP Layer'))
        
        if legend_elements:
            ax.legend(handles=legend_elements, loc='lower right', frameon=True, framealpha=0.98)
        
        plt.tight_layout()
        
        # Save plot with implementation name
        safe_impl_name = impl.replace(' ', '_').lower()
        output_path = output_dir / f"{safe_impl_name}_breakdown.png"
        plt.savefig(output_path)
        plt.close()
        
        print(f"Created plot for {impl}: {output_path}")

def main():
    """Main execution function."""
    csv_path = "/home/exouser/client/analysis/outputs/get_modelcard_metrics_summary.csv"
    output_dir = Path("/home/exouser/client/analysis/outputs")
    
    # Load and group data by implementation
    impl_groups = load_and_group_by_implementation(csv_path)
    
    print("Implementation Groups:")
    for group in impl_groups:
        print(f"Implementation: {group['implementation']}")
        print(group['data'][['Model Card Size (KB)', 'DB Latency (ms)', ' REST Layer (ms)', 'MCP Layer (ms)', 'Total Latency (ms)']])
        print()
    
    # Create visualizations
    create_implementation_breakdown_plots(impl_groups, output_dir)
    
    print(f"\nVisualizations saved to {output_dir}")
    print("Created separate plots for each implementation showing breakdown by model card size")

if __name__ == "__main__":
    main()
