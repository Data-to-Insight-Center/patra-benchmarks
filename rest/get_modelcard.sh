#!/bin/bash

URL="http://149.165.175.102:5002/modelcard/megadetector-mc"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
OUTPUT_DIR="/home/exouser/client/rest/benchmark_results/run_${TIMESTAMP}"
OUTPUT_FILE="${OUTPUT_DIR}/get_modelcard.csv"

# Create directory
mkdir -p "$OUTPUT_DIR"

# Print CSV header
echo "response_time_ms,dns_lookup_ms,tcp_handshake_ms,ttfb_ms,prepare_ms,response_size_kb" > "$OUTPUT_FILE"

# Make 100 requests
for i in $(seq 1 100); do
    # Get response with size and timing, save to temp file
    temp_file=$(mktemp)
    timing=$(curl -w "%{time_total}:%{time_namelookup}:%{time_connect}:%{time_starttransfer}:%{time_pretransfer}:%{size_download}" \
             -s -o "$temp_file" "$URL")
    
    # Convert to milliseconds and KB using awk
    echo "$timing" | awk -F: '{
        printf "%.5f,%.5f,%.5f,%.5f,%.5f,%.2f\n", 
        $1*1000, $2*1000, $3*1000, $4*1000, $5*1000, $6/1024
    }' >> "$OUTPUT_FILE"
    
    # Clean up temp file
    rm -f "$temp_file"
    
    echo "Request $i completed"
done

echo "Results saved to $OUTPUT_FILE"
