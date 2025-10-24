import os
import csv
import requests
import time
from pathlib import Path
from datetime import datetime

REST_API_BASE_URL = os.getenv("SERVER_URL")
BENCHMARK_RUNS = int(os.getenv("BENCHMARK_RUNS"))
MODELCARD_ID = os.getenv("MODELCARD_ID")
SEARCH_QUERY = os.getenv("SEARCH_QUERY")
BENCHMARK_RESULTS_DIR = os.getenv("BENCHMARK_RESULTS_DIR")

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

def main():
    # Setup output directory with date and client type
    today = datetime.now().strftime('%Y_%m_%d')
    run_dir = Path(BENCHMARK_RESULTS_DIR) / f"run_{today}"
    run_dir.mkdir(parents=True, exist_ok=True)
    
    get_modelcard_file = run_dir / "get_modelcard.csv"

    init_csv_file(get_modelcard_file)
    
    for i in range(BENCHMARK_RUNS):
        start_time = time.perf_counter()
        response = requests.get(f"{REST_API_BASE_URL}/modelcard/{MODELCARD_ID}")        
        end_time = time.perf_counter()
        response_time_ms = (end_time - start_time) * 1000
        response_str = response.text
        response_size_bytes = len(response_str.encode('utf-8'))
        response_size_kb = response_size_bytes / 1024
        
        # Only write to CSV after the first request (skip index 0)
        if i > 0:
            write_latency_row(get_modelcard_file, response_time_ms, response_size_kb)

if __name__ == "__main__":
    main()