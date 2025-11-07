#!/usr/bin/env python3
"""
Simple MCP timing benchmark - equivalent to curl timing breakdown.

Measures individual request timings broken down into phases:
- SSE connection time
- MCP initialization/handshake time
- Resource read time
- Total time
"""

import asyncio
import time
import csv
from datetime import datetime
from mcp import ClientSession
from mcp.client.sse import sse_client


# Configuration
SERVER_URL = "http://149.165.175.102:8051"  # Update with actual MCP server URL
SSE_URL = f"{SERVER_URL}/sse"
MODELCARD_ID = "megadetector-mc"
NUM_REQUESTS = 100
OUTPUT_FILE = "mcp_timing_results.txt"
CSV_FILE = "mcp_timing_results.csv"


async def single_timed_request(request_id: int) -> dict:
    """Execute a single MCP request with timing breakdown."""
    timings = {
        'request_id': request_id,
        'connection_ms': 0,
        'handshake_ms': 0,
        'resource_read_ms': 0,
        'total_time_ms': 0,
        'status': 'failed'
    }

    start_total = time.perf_counter()

    try:
        # Phase 1: SSE Connection
        start_connection = time.perf_counter()
        transport = sse_client(url=SSE_URL)
        read_stream, write_stream = await transport.__aenter__()
        session = ClientSession(read_stream, write_stream)
        await session.__aenter__()
        end_connection = time.perf_counter()
        timings['connection_ms'] = (end_connection - start_connection) * 1000

        # Phase 2: MCP Handshake
        start_handshake = time.perf_counter()
        await session.initialize()
        end_handshake = time.perf_counter()
        timings['handshake_ms'] = (end_handshake - start_handshake) * 1000

        # Phase 3: Resource Read
        start_read = time.perf_counter()
        uri = f"modelcard://{MODELCARD_ID}"
        result = await session.read_resource(uri)
        end_read = time.perf_counter()
        timings['resource_read_ms'] = (end_read - start_read) * 1000

        # Success
        timings['status'] = 'success'

        # Cleanup
        try:
            await session.__aexit__(None, None, None)
            await transport.__aexit__(None, None, None)
        except Exception:
            pass

    except Exception as e:
        timings['status'] = f'error: {str(e)[:50]}'

    end_total = time.perf_counter()
    timings['total_time_ms'] = (end_total - start_total) * 1000

    return timings


async def run_benchmark():
    """Run the complete benchmark."""
    print(f"Running {NUM_REQUESTS} MCP requests with timing breakdown...")
    print(f"Server URL: {SSE_URL}")
    print(f"Results will be saved to: {OUTPUT_FILE} and {CSV_FILE}")
    print("")

    # Clear output files
    with open(OUTPUT_FILE, 'w') as f:
        f.write("=" * 70 + "\n")
        f.write(f"MCP Timing Breakdown - {NUM_REQUESTS} Requests\n")
        f.write(f"Server URL: {SSE_URL}\n")
        f.write(f"ModelCard ID: {MODELCARD_ID}\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 70 + "\n\n")

    # CSV header
    with open(CSV_FILE, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([
            'request_id',
            'connection_ms',
            'handshake_ms',
            'resource_read_ms',
            'total_time_ms',
            'status'
        ])

    # Warm-up phase
    print("Running warm-up phase (10 requests)...")
    for i in range(1, 11):
        print(f"Warm-up request {i}/10... ", end='', flush=True)
        await single_timed_request(0)  # Request ID 0 for warm-up
        print("Done")
    print("Warm-up complete! Starting measurements...")
    print("")

    # Run requests sequentially (like curl script)
    results = []
    for i in range(1, NUM_REQUESTS + 1):
        print(f"Request {i}/{NUM_REQUESTS}... ", end='', flush=True)

        timing = await single_timed_request(i)
        results.append(timing)

        # Write to text file
        with open(OUTPUT_FILE, 'a') as f:
            f.write(f"--- Request {i} ---\n")
            f.write(f"SSE Connection:        {timing['connection_ms']:.3f} ms\n")
            f.write(f"MCP Handshake:         {timing['handshake_ms']:.3f} ms\n")
            f.write(f"Resource Read:         {timing['resource_read_ms']:.3f} ms\n")
            f.write(f"Total Time:            {timing['total_time_ms']:.3f} ms\n")
            f.write(f"Status:                {timing['status']}\n\n")

        # Write to CSV
        with open(CSV_FILE, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                timing['request_id'],
                f"{timing['connection_ms']:.3f}",
                f"{timing['handshake_ms']:.3f}",
                f"{timing['resource_read_ms']:.3f}",
                f"{timing['total_time_ms']:.3f}",
                timing['status']
            ])

        print("Done")

    # Final summary
    with open(OUTPUT_FILE, 'a') as f:
        f.write("\n" + "=" * 70 + "\n")
        f.write("Benchmark Complete!\n")
        f.write("=" * 70 + "\n")

    print("")
    print("Benchmark complete!")
    print("Results saved to:")
    print(f"  - Text format: {OUTPUT_FILE}")
    print(f"  - CSV format:  {CSV_FILE}")

    # Calculate and print summary statistics
    successful = [r for r in results if r['status'] == 'success']
    if successful:
        avg_connection = sum(r['connection_ms'] for r in successful) / len(successful)
        avg_handshake = sum(r['handshake_ms'] for r in successful) / len(successful)
        avg_read = sum(r['resource_read_ms'] for r in successful) / len(successful)
        avg_total = sum(r['total_time_ms'] for r in successful) / len(successful)

        print(f"\nSummary Statistics ({len(successful)}/{NUM_REQUESTS} successful):")
        print(f"  Avg SSE Connection:    {avg_connection:.3f} ms")
        print(f"  Avg MCP Handshake:     {avg_handshake:.3f} ms")
        print(f"  Avg Resource Read:     {avg_read:.3f} ms")
        print(f"  Avg Total Time:        {avg_total:.3f} ms")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
