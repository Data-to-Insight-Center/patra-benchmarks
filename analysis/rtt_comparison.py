import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
from datetime import datetime

def read_latency_data(file_path: Path) -> pd.DataFrame:
    return pd.read_csv(file_path)

def plot_latency_comparison(rest_data: pd.DataFrame, mcp_data: pd.DataFrame, layered_mcp_data: pd.DataFrame) -> None:
    plt.figure(figsize=(7, 5))
    
    # Calculate average response sizes for legend
    rest_avg_size = rest_data['response_size_kb'].mean()
    mcp_avg_size = mcp_data['response_size_kb'].mean()
    layered_mcp_avg_size = layered_mcp_data['response_size_kb'].mean()
    
    # Plot each dataset with different colors and labels including response size
    plt.plot(rest_data['response_time_ms'], label=f'REST ({rest_avg_size:.0f} KB)', marker='.', linewidth=2)
    plt.plot(mcp_data['response_time_ms'], label=f'MCP Native ({mcp_avg_size:.0f} KB)', marker='.', linewidth=2)
    plt.plot(layered_mcp_data['response_time_ms'], label=f'MCP Layered ({layered_mcp_avg_size:.0f} KB)', marker='.', linewidth=2)
    
    plt.xlabel('Run')
    plt.ylabel('Response Time (ms)')    
    plt.title('Response Time Comparison')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig('rtt_comparison.png')

def main():
    rest_data = read_latency_data(Path('/home/exouser/client/rest/benchmark_results/run_2025_10_24/get_modelcard.csv'))
    mcp_data = read_latency_data(Path('/home/exouser/client/mcp/benchmark_results/run_2025_10_24/native/get_modelcard.csv'))
    layered_mcp_data = read_latency_data(Path('/home/exouser/client/mcp/benchmark_results/run_2025_10_24/layered/get_modelcard.csv'))
    plot_latency_comparison(rest_data, mcp_data, layered_mcp_data)

if __name__ == '__main__':
    main()