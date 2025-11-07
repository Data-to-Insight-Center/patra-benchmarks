import asyncio
import os
import time
from pathlib import Path
from datetime import datetime
import csv
from mcp import ClientSession
from mcp.client.sse import sse_client

CSV_HEADERS = ['response_time_ms', 'response_size_kb']

def write_latency_row(csv_file, response_time_ms, response_size_kb):
    """Write latency row with response time and size"""
    with open(csv_file, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([response_time_ms, response_size_kb])

def init_csv_file(csv_file):
    """Initialize CSV file with headers"""
    with open(csv_file, "w", newline="") as f:
        csv.writer(f).writerow(CSV_HEADERS)

async def run_benchmark(server_url, client_type, runs, modelcard_id, benchmark_results_dir):
    """Run benchmark for a specific server with detailed timing breakdown"""
    # Setup output directory with date and client type
    today = datetime.now().strftime('%Y_%m_%d')
    run_dir = Path(benchmark_results_dir) / f"run_{today}" / client_type
    run_dir.mkdir(parents=True, exist_ok=True)

    get_modelcard_file = run_dir / "get_modelcard_rtt.csv"
    init_csv_file(get_modelcard_file)

    print(f"\n=== Testing {client_type.upper()} MCP Server ===")
    print(f"Server URL: {server_url}")

    # Phase 1: Connection setup (one-time for all requests)
    start_connection = time.perf_counter()
    transport = sse_client(url=server_url)
    read_stream, write_stream = await transport.__aenter__()
    session = ClientSession(read_stream, write_stream)
    await session.__aenter__()
    end_connection = time.perf_counter()
    connection_ms = (end_connection - start_connection) * 1000

    # Phase 2: Handshake (one-time initialization)
    start_handshake = time.perf_counter()
    await session.initialize()
    end_handshake = time.perf_counter()
    handshake_ms = (end_handshake - start_handshake) * 1000

    print(f"Connection setup: {connection_ms:.2f}ms")
    print(f"MCP handshake: {handshake_ms:.2f}ms")
    print(f"Running {runs + 1} get_modelcard calls (warm-up + {runs} measured)...")

    try:
        for i in range(runs + 1):
            # Phase 3: Resource read (measured per request)
            start_read = time.perf_counter()
            uri = f"modelcard://{modelcard_id}"
            result = await session.read_resource(uri)
            end_read = time.perf_counter()

            resource_read_ms = (end_read - start_read) * 1000
            total_time_ms = connection_ms + handshake_ms + resource_read_ms

            response_str = result.contents[0].text
            response_size_bytes = len(response_str.encode('utf-8'))
            response_size_kb = response_size_bytes / 1024

            # Only write to CSV after the first request (skip index 0)
            if i > 0:
                write_latency_row(get_modelcard_file, total_time_ms, response_size_kb)
                print(f"get_modelcard {i}/{runs}: conn={connection_ms:.2f}ms, "
                      f"handshake={handshake_ms:.2f}ms, read={resource_read_ms:.2f}ms, "
                      f"total={total_time_ms:.2f}ms, size={response_size_kb:.2f}KB")
            else:
                print(f"Warm-up call: read={resource_read_ms:.2f}ms, total={total_time_ms:.2f}ms")
    finally:
        # Cleanup
        try:
            await session.__aexit__(None, None, None)
            await transport.__aexit__(None, None, None)
        except Exception as e:
            print(f"Warning: cleanup error: {e}")

async def main():
    runs = int(os.getenv("BENCHMARK_RUNS", "10"))
    modelcard_id = os.getenv("MODELCARD_ID", "megadetector-mc")
    benchmark_results_dir = os.getenv("BENCHMARK_RESULTS_DIR", "/app/benchmark_results")
    
    # Test native MCP server first
    native_server_url = "http://149.165.175.102:8050/sse"
    await run_benchmark(native_server_url, "native", runs, modelcard_id, benchmark_results_dir)
    
    # Test layered MCP server second
    layered_server_url = "http://149.165.175.102:8051/sse"
    await run_benchmark(layered_server_url, "layered", runs, modelcard_id, benchmark_results_dir)
    
    print("\n=== Benchmark Complete ===")
    print("Results saved to:")
    print(f"  - Native: {benchmark_results_dir}/run_{datetime.now().strftime('%Y_%m_%d')}/native/get_modelcard_rtt.csv")
    print(f"  - Layered: {benchmark_results_dir}/run_{datetime.now().strftime('%Y_%m_%d')}/layered/get_modelcard_rtt.csv")
                
if __name__ == "__main__":
    asyncio.run(main())