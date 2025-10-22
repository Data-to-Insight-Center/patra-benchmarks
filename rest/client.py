import os
from datetime import datetime
from pathlib import Path
import time
import csv
import asyncio
import socket
import ssl
from urllib.parse import urlparse

async def measure_detailed_latency(url, path):
    """Measure detailed latency breakdown with granular metrics"""
    parsed_url = urlparse(url)
    host = parsed_url.hostname
    port = parsed_url.port or (443 if parsed_url.scheme == 'https' else 80)
    is_https = parsed_url.scheme == 'https'
    
    # Initialize timing variables
    dns_lookup_time = 0
    socket_creation_time = 0
    tcp_connect_time = 0
    ssl_context_creation_time = 0
    ssl_handshake_time = 0
    request_send_time = 0
    time_to_first_byte = 0
    response_read_time = 0
    socket_close_time = 0
    server_processing_time = 0
    total_time = 0
    
    start_total = time.perf_counter()
    sock = None
    
    try:
        # DNS lookup timing
        dns_start = time.perf_counter()
        ip_address = socket.gethostbyname(host)
        dns_end = time.perf_counter()
        dns_lookup_time = dns_end - dns_start
        
        # Socket creation timing
        socket_create_start = time.perf_counter()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(10)
        socket_create_end = time.perf_counter()
        socket_creation_time = socket_create_end - socket_create_start
        
        # TCP connection timing (3-way handshake)
        tcp_start = time.perf_counter()
        sock.connect((ip_address, port))
        tcp_end = time.perf_counter()
        tcp_connect_time = tcp_end - tcp_start
        
        # SSL/TLS handshake timing (if HTTPS)
        if is_https:
            # SSL context creation
            ssl_context_start = time.perf_counter()
            context = ssl.create_default_context()
            ssl_context_end = time.perf_counter()
            ssl_context_creation_time = ssl_context_end - ssl_context_start
            
            # SSL handshake
            ssl_start = time.perf_counter()
            ssl_sock = context.wrap_socket(sock, server_hostname=host)
            ssl_end = time.perf_counter()
            ssl_handshake_time = ssl_end - ssl_start
            sock = ssl_sock
        
        # HTTP request sending timing
        request_start = time.perf_counter()
        request = f"GET {path} HTTP/1.1\r\nHost: {host}\r\nConnection: close\r\n\r\n"
        sock.send(request.encode())
        request_end = time.perf_counter()
        request_send_time = request_end - request_start
        
        # Time to first byte (TTFB) - server processing time
        ttfb_start = time.perf_counter()
        sock.settimeout(5)
        first_byte = sock.recv(1, socket.MSG_PEEK)
        ttfb_end = time.perf_counter()
        time_to_first_byte = ttfb_end - ttfb_start
        
        # Response reading timing
        response_read_start = time.perf_counter()
        response = sock.recv(4096)
        response_read_end = time.perf_counter()
        response_read_time = response_read_end - response_read_start
        
        # Socket close timing
        close_start = time.perf_counter()
        sock.close()
        close_end = time.perf_counter()
        socket_close_time = close_end - close_start
        
        # Server processing = time from request sent to first byte received
        server_processing_time = time_to_first_byte
        
    except Exception as e:
        print(f"Error in detailed latency measurement: {e}")
        if sock:
            try:
                sock.close()
            except:
                pass
    
    end_total = time.perf_counter()
    total_time = end_total - start_total
    
    return {
        'dns_lookup': dns_lookup_time,
        'socket_creation': socket_creation_time,
        'tcp_connect': tcp_connect_time,
        'ssl_context_creation': ssl_context_creation_time,
        'ssl_handshake': ssl_handshake_time,
        'request_send': request_send_time,
        'time_to_first_byte': time_to_first_byte,
        'response_read': response_read_time,
        'socket_close': socket_close_time,
        'server_processing': server_processing_time,
        'total_time': total_time
    }

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
    
    # Write CSV headers with granular breakdown
    csv_headers = [
        'timestamp', 
        'dns_lookup', 
        'socket_creation', 
        'tcp_connect', 
        'ssl_context_creation',
        'ssl_handshake', 
        'request_send',
        'time_to_first_byte',
        'response_read',
        'socket_close',
        'server_processing', 
        'total_time'
    ]
    
    with open(get_modelcard_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
    
    with open(search_modelcards_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)

    # Endpoint paths (override via env if your API differs)
    get_modelcard_path = os.getenv("GET_MODELCARD_PATH", "/modelcard/{mc_id}")
    search_modelcards_path = os.getenv("SEARCH_MODELCARDS_PATH", "/modelcards/search")

    modelcard_id = os.getenv("MODELCARD_ID", "3f7b2c82-75fa-4335-a3b8-e1930893a974")
    search_query = os.getenv("SEARCH_QUERY", "AlexNet")

    # Run benchmarks using raw sockets only
    for _ in range(runs):
        # Measure detailed latency breakdown
        detailed_latency = await measure_detailed_latency(base_url, get_modelcard_path.format(mc_id=modelcard_id))
        
        # Write to CSV with all granular metrics
        with open(get_modelcard_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                detailed_latency['dns_lookup'],
                detailed_latency['socket_creation'],
                detailed_latency['tcp_connect'],
                detailed_latency['ssl_context_creation'],
                detailed_latency['ssl_handshake'],
                detailed_latency['request_send'],
                detailed_latency['time_to_first_byte'],
                detailed_latency['response_read'],
                detailed_latency['socket_close'],
                detailed_latency['server_processing'],
                detailed_latency['total_time']
            ])
        
    for _ in range(runs):
        # Measure detailed latency breakdown with query parameter
        detailed_latency = await measure_detailed_latency(base_url, f"{search_modelcards_path}?q={search_query}")
        
        # Write to CSV with all granular metrics
        with open(search_modelcards_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                time.time(),
                detailed_latency['dns_lookup'],
                detailed_latency['socket_creation'],
                detailed_latency['tcp_connect'],
                detailed_latency['ssl_context_creation'],
                detailed_latency['ssl_handshake'],
                detailed_latency['request_send'],
                detailed_latency['time_to_first_byte'],
                detailed_latency['response_read'],
                detailed_latency['socket_close'],
                detailed_latency['server_processing'],
                detailed_latency['total_time']
            ])


if __name__ == "__main__":
    asyncio.run(main())