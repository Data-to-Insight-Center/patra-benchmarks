"""
Benchmark script for the Patra REST MCP Server.

This script benchmarks the MCP server endpoints and writes results to CSV files.
Note: This requires the MCP server to be running.
"""

import asyncio
import os
import time
from pathlib import Path
from datetime import datetime
import csv
from mcp import ClientSession
from mcp.client.sse import sse_client

CSV_HEADERS = ['total_time']

def write_latency_row(csv_file, total_time):
    """Write latency row with total MCP round-trip time"""
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([total_time])

def init_csv_file(csv_file):
    """Initialize CSV file with headers"""
    with open(csv_file, "w", newline="") as f:
        csv.writer(f).writerow(CSV_HEADERS)

async def main():
    server_url = os.getenv("SERVER_URL", "http://localhost:8051/sse")
    results_dir = os.getenv("BENCHMARK_RESULTS_DIR", "/app/benchmark_results")
    runs = int(os.getenv("BENCHMARK_RUNS", "1000"))
    modelcard_id = os.getenv("MODELCARD_ID", "3f7b2c82-75fa-4335-a3b8-e1930893a974")
    search_query = os.getenv("SEARCH_QUERY", "AlexNet")
    
    # Setup output directory
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    run_dir = Path(results_dir) / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    get_modelcard_file = run_dir / "get_modelcard.csv"
    search_modelcards_file = run_dir / "search_modelcards.csv"
    
    init_csv_file(get_modelcard_file)
    init_csv_file(search_modelcards_file)
    
    print(f"Connecting to MCP server at {server_url}")
    print(f"Benchmark runs: {runs}")
    print(f"Results will be saved to: {run_dir}")
    
    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            for _ in range(runs):
                start = time.perf_counter()
                await session.call_tool("get_modelcard", arguments={"mc_id": modelcard_id})
                write_latency_row(get_modelcard_file, time.perf_counter() - start)
                
            for _ in range(runs):
                start = time.perf_counter()
                await session.call_tool("search_modelcards", arguments={"query": search_query})
                write_latency_row(search_modelcards_file, time.perf_counter() - start)

if __name__ == "__main__":
    asyncio.run(main())

