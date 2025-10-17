import os
from datetime import datetime
from pathlib import Path
import time
import httpx
import csv
import asyncio

async def main():
    base_url = os.getenv("SERVER_URL", "http://localhost:5002")

    results_dir = os.getenv("BENCHMARK_RESULTS_DIR", "/app/benchmark_results")
    Path(results_dir).mkdir(parents=True, exist_ok=True)
    run_stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = Path(results_dir) / f"run_{run_stamp}"
    run_dir.mkdir(parents=True, exist_ok=True)

    # Output CSV files
    get_modelcard_file = run_dir / "get_modelcard.csv"
    search_modelcards_file = run_dir / "search_modelcards.csv"
    runs = int(os.getenv("BENCHMARK_RUNS", "1000"))

    # Endpoint paths (override via env if your API differs)
    get_modelcard_path = os.getenv("GET_MODELCARD_PATH", "/modelcard/{mc_id}")
    search_modelcards_path = os.getenv("SEARCH_MODELCARDS_PATH", "/modelcards/search")

    modelcard_id = os.getenv("MODELCARD_ID", "3f7b2c82-75fa-4335-a3b8-e1930893a974")
    search_query = os.getenv("SEARCH_QUERY", "AlexNet")

    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        for _ in range(runs):
            req_start_time = time.perf_counter()
            resp = await client.get(get_modelcard_path.format(mc_id=modelcard_id))
            req_end_time = time.perf_counter()
            
            # Write to CSV
            with open(get_modelcard_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([req_start_time, req_end_time])
            
        for _ in range(runs):
            req_start_time = time.perf_counter()
            resp = await client.get(search_modelcards_path, params={"query": search_query})
            req_end_time = time.perf_counter()
            
            # Write to CSV
            with open(search_modelcards_file, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([req_start_time, req_end_time])


if __name__ == "__main__":
    asyncio.run(main())