import asyncio
import os
import time
from pathlib import Path
from datetime import datetime
import csv
from mcp import ClientSession
from mcp.client.sse import sse_client

async def main():
    # Default to FastMCP SSE endpoint
    server_url = os.getenv("SERVER_URL", "http://localhost:8050/sse")

    results_dir = os.getenv("BENCHMARK_RESULTS_DIR", "/app/benchmark_results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(results_dir) / f"run_{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    # Output CSV files
    get_modelcard_file = run_dir / "get_modelcard.csv"
    search_modelcards_file = run_dir / "search_modelcards.csv"
    runs = int(os.getenv("BENCHMARK_RUNS", "10"))
    modelcard_id = os.getenv("MODELCARD_ID", "3f7b2c82-75fa-4335-a3b8-e1930893a974")
    search_query = os.getenv("SEARCH_QUERY", "AlexNet")
    
    # Connect via SSE to FastMCP
    async with sse_client(server_url) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()

            for _ in range(runs):
                req_start_time = time.perf_counter()
                resp = await session.call_tool("get_modelcard", arguments={"mc_id": modelcard_id})
                req_end_time = time.perf_counter()
            
                # Write to CSV
                with open(get_modelcard_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([req_start_time, req_end_time])
                
            for _ in range(runs):
                req_start_time = time.perf_counter()
                resp = await session.call_tool("search_modelcards", arguments={"query": search_query})
                req_end_time = time.perf_counter()
                
                # Write to CSV
                with open(search_modelcards_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([req_start_time, req_end_time])

            
if __name__ == "__main__":
    asyncio.run(main())