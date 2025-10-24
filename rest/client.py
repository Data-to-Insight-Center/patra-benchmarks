import os
import csv
import requests
import time

REST_API_BASE_URL = os.getenv("REST_API_BASE_URL")
BENCHMARK_RUNS = int(os.getenv("BENCHMARK_RUNS"))
MODELCARD_ID = os.getenv("MODELCARD_ID")
QUERY = os.getenv("QUERY")
RESULTS_DIR = os.getenv("RESULTS_DIR")

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

def main():
    get_modelcards_file = os.path.join(RESULTS_DIR, "get_modelcards.csv")
    get_modelcard_file = os.path.join(RESULTS_DIR, "get_modelcard.csv")

    init_csv_file(get_modelcards_file)
    init_csv_file(get_modelcard_file)

    for _ in range(BENCHMARK_RUNS):
        start_time = time.perf_counter()
        response = requests.get(f"{REST_API_BASE_URL}/modelcards/search", params={"q": QUERY})        
        end_time = time.perf_counter()
        write_latency_row(get_modelcards_file, end_time - start_time)

    for _ in range(BENCHMARK_RUNS):
        start_time = time.perf_counter()
        response = requests.get(f"{REST_API_BASE_URL}/modelcard/{MODELCARD_ID}")        
        end_time = time.perf_counter()
        write_latency_row(get_modelcard_file, end_time - start_time)

if __name__ == "__main__":
    main()