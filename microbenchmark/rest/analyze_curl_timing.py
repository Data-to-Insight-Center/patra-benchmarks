#!/usr/bin/env python3
import csv
import statistics

# Read CSV file
with open('curl_timing_results.csv', 'r') as f:
    reader = csv.DictReader(f)
    data = list(reader)

# Extract metrics
dns_lookups = [float(row['dns_lookup_ms']) for row in data]
tcp_connects = [float(row['tcp_connect_ms']) for row in data]
tls_handshakes = [float(row['tls_handshake_ms']) for row in data]
time_pretransfers = [float(row['time_pretransfer_ms']) for row in data]
ttfbs = [float(row['time_to_first_byte_ms']) for row in data]
total_times = [float(row['total_time_ms']) for row in data]

# Calculate derived metrics
tcp_only = [tcp_connects[i] - dns_lookups[i] for i in range(len(data))]
server_processing = [ttfbs[i] - time_pretransfers[i] for i in range(len(data))]
content_transfer = [total_times[i] - ttfbs[i] for i in range(len(data))]

def calc_stats(values):
    return {
        'min': min(values),
        'max': max(values),
        'mean': statistics.mean(values),
        'median': statistics.median(values),
        'stdev': statistics.stdev(values) if len(values) > 1 else 0,
        'p50': statistics.median(values),
        'p95': sorted(values)[int(len(values) * 0.95)],
        'p99': sorted(values)[int(len(values) * 0.99)]
    }

print("="*80)
print("LATENCY BREAKDOWN ANALYSIS - 100 Requests")
print("="*80)
print()

print("Component Breakdown (in milliseconds):")
print("-" * 80)
print(f"{'Component':<30} {'Mean':<10} {'Median':<10} {'p95':<10} {'p99':<10}")
print("-" * 80)

components = [
    ("DNS Lookup", dns_lookups),
    ("TCP Connection (excl DNS)", tcp_only),
    ("TLS Handshake", tls_handshakes),
    ("Request Sent (pre-transfer)", time_pretransfers),
    ("Server Processing (TTFB)", server_processing),
    ("Content Transfer", content_transfer),
    ("TOTAL", total_times)
]

for name, values in components:
    stats = calc_stats(values)
    print(f"{name:<30} {stats['mean']:>8.2f}  {stats['median']:>8.2f}  {stats['p95']:>8.2f}  {stats['p99']:>8.2f}")

print()
print("="*80)
print("DETAILED STATISTICS")
print("="*80)

for name, values in components:
    stats = calc_stats(values)
    print(f"\n{name}:")
    print(f"  Min:    {stats['min']:.3f} ms")
    print(f"  Max:    {stats['max']:.3f} ms")
    print(f"  Mean:   {stats['mean']:.3f} ms")
    print(f"  Median: {stats['median']:.3f} ms")
    print(f"  Stdev:  {stats['stdev']:.3f} ms")
    print(f"  p50:    {stats['p50']:.3f} ms")
    print(f"  p95:    {stats['p95']:.3f} ms")
    print(f"  p99:    {stats['p99']:.3f} ms")

# Calculate percentages
print()
print("="*80)
print("PERCENTAGE BREAKDOWN (of total time)")
print("="*80)
total_mean = statistics.mean(total_times)

for name, values in components[:-1]:  # Exclude TOTAL
    mean_val = statistics.mean(values)
    percentage = (mean_val / total_mean) * 100
    print(f"{name:<30} {mean_val:>8.2f} ms ({percentage:>5.1f}%)")
print("-" * 80)
print(f"{'TOTAL':<30} {total_mean:>8.2f} ms (100.0%)")

