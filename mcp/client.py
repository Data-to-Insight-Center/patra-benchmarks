import asyncio
import os
import time
from pathlib import Path
from datetime import datetime
import csv
from mcp import ClientSession
from mcp.client.sse import sse_client

async def benchmark_latency(session, tool_name, arguments, runs, output_file):
    """Measure latency with sequential MCP tool calls."""
    latencies = []
    
    for _ in range(runs):
        req_start_time = time.perf_counter()
        resp = await session.call_tool(tool_name, arguments=arguments)
        req_end_time = time.perf_counter()
        
        latency = req_end_time - req_start_time
        latencies.append(latency)
        
        # Write to CSV
        with open(output_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([req_start_time, req_end_time])
    
    return latencies

async def benchmark_throughput(session, tool_name, arguments, duration_seconds, max_concurrent):
    """Measure throughput with concurrent MCP tool calls."""
    total_requests = 0
    errors = 0
    latencies = []
    start_time = time.perf_counter()
    end_time = start_time + duration_seconds
    
    async def worker():
        nonlocal total_requests, errors
        while time.perf_counter() < end_time:
            try:
                req_start = time.perf_counter()
                await session.call_tool(tool_name, arguments=arguments)
                req_end = time.perf_counter()
                latencies.append(req_end - req_start)
                total_requests += 1
            except Exception as e:
                errors += 1
    
    # Run workers concurrently
    await asyncio.gather(*[worker() for _ in range(max_concurrent)])
    
    actual_duration = time.perf_counter() - start_time
    throughput = total_requests / actual_duration if actual_duration > 0 else 0
    
    return {
        'total_requests': total_requests,
        'errors': errors,
        'duration': actual_duration,
        'throughput': throughput,
        'latencies': latencies
    }

async def main():
    server_url = os.getenv("SERVER_URL", "http://localhost:8050/sse")
    results_dir = os.getenv("BENCHMARK_RESULTS_DIR", "/app/benchmark_results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(results_dir) / f"run_{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuration
    latency_runs = int(os.getenv("BENCHMARK_RUNS", "1000"))
    throughput_duration = int(os.getenv("THROUGHPUT_DURATION", "10"))
    max_concurrent = int(os.getenv("MAX_CONCURRENT", "50"))
    measure_throughput = os.getenv("MEASURE_THROUGHPUT", "false").lower() == "true"
    
    modelcard_id = os.getenv("MODELCARD_ID", "3f7b2c82-75fa-4335-a3b8-e1930893a974")
    search_query = os.getenv("SEARCH_QUERY", "AlexNet")
    
    # Connect via SSE to FastMCP
    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            print(f"Benchmarking MCP server at {server_url}")
            print(f"Results directory: {run_dir}")
            
            # ===== LATENCY BENCHMARKS =====
            print(f"\n=== Latency Benchmark (sequential, {latency_runs} runs) ===")
            
            # get_modelcard latency
            print(f"Running get_modelcard...")
            get_latencies = await benchmark_latency(
                session,
                "get_modelcard",
                {"mc_id": modelcard_id},
                latency_runs,
                run_dir / "get_modelcard.csv"
            )
            avg_get_latency = sum(get_latencies) / len(get_latencies) * 1000
            print(f"  Avg latency: {avg_get_latency:.2f} ms")
            
            # search_modelcards latency
            print(f"Running search_modelcards...")
            search_latencies = await benchmark_latency(
                session,
                "search_modelcards",
                {"query": search_query},
                latency_runs,
                run_dir / "search_modelcards.csv"
            )
            avg_search_latency = sum(search_latencies) / len(search_latencies) * 1000
            print(f"  Avg latency: {avg_search_latency:.2f} ms")
            
            # ===== THROUGHPUT BENCHMARKS =====
            if measure_throughput:
                print(f"\n=== Throughput Benchmark ({throughput_duration}s, {max_concurrent} concurrent) ===")
                
                # get_modelcard throughput
                print(f"Running get_modelcard...")
                get_throughput = await benchmark_throughput(
                    session,
                    "get_modelcard",
                    {"mc_id": modelcard_id},
                    throughput_duration,
                    max_concurrent
                )
                print(f"  Throughput: {get_throughput['throughput']:.2f} req/s")
                print(f"  Total requests: {get_throughput['total_requests']}")
                print(f"  Errors: {get_throughput['errors']}")
                
                # search_modelcards throughput
                print(f"Running search_modelcards...")
                search_throughput = await benchmark_throughput(
                    session,
                    "search_modelcards",
                    {"query": search_query},
                    throughput_duration,
                    max_concurrent
                )
                print(f"  Throughput: {search_throughput['throughput']:.2f} req/s")
                print(f"  Total requests: {search_throughput['total_requests']}")
                print(f"  Errors: {search_throughput['errors']}")
                
                # Save throughput results
                with open(run_dir / "throughput_results.csv", "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["operation", "throughput_rps", "total_requests", "errors", "duration_s", "avg_latency_ms"])
                    writer.writerow([
                        "get_modelcard",
                        f"{get_throughput['throughput']:.2f}",
                        get_throughput['total_requests'],
                        get_throughput['errors'],
                        f"{get_throughput['duration']:.2f}",
                        f"{(sum(get_throughput['latencies']) / len(get_throughput['latencies']) * 1000):.2f}" if get_throughput['latencies'] else "0"
                    ])
                    writer.writerow([
                        "search_modelcards",
                        f"{search_throughput['throughput']:.2f}",
                        search_throughput['total_requests'],
                        search_throughput['errors'],
                        f"{search_throughput['duration']:.2f}",
                        f"{(sum(search_throughput['latencies']) / len(search_throughput['latencies']) * 1000):.2f}" if search_throughput['latencies'] else "0"
                    ])
            
            print(f"\n✓ Benchmark complete. Results saved to {run_dir}")

if __name__ == "__main__":
    asyncio.run(main())