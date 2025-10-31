# REST API Async Benchmarking Client

Research-grade benchmarking of async REST API performance across multiple concurrency levels.

## Quick Start

```bash
cd /home/exouser/patra-kg/rest_client
docker compose up
```

**That's it!** This will:
- Connect to the async REST server container
- Run systematic experiments (6 concurrency levels: 1, 5, 10, 20, 50, 100)
- Analyze results with statistical rigor (5 trials per level, 200 requests per trial)
- Generate publication-quality visualizations
- Save everything to `experiments/` directory
- Exit automatically when complete (~15-20 minutes)

## Prerequisites

Ensure the REST server is running:

```bash
cd /home/exouser/patra-kg/benchmarking
docker compose up -d rest-server
```

## Results

All results saved to:
```
experiments/REST_API_Concurrency_Analysis_[timestamp]/
├── analysis_report.txt              # Statistical findings
├── summary_statistics.csv           # Raw data
├── throughput_vs_concurrency.csv    # Plot data
├── latency_vs_concurrency.csv       # Plot data
└── plots/
    ├── comprehensive_dashboard.png  # Main overview
    ├── throughput_vs_concurrency.png
    ├── speedup_and_efficiency.png
    └── latency_vs_concurrency.png
```

View results:
```bash
cat experiments/REST_API_Concurrency_Analysis_*/analysis_report.txt
```

## Configuration

Edit `experiment_config.json` to customize:
- `concurrency_levels`: List of concurrency levels to test
- `trials_per_level`: Number of trials per level (for statistical significance)
- `requests_per_trial`: Requests per trial
- `warmup_requests`: Warmup requests (not counted)
- `cooldown_seconds`: Cool-down between trials

Then rebuild: `docker compose up --build`

## What Gets Measured

- **Throughput** (req/s) with mean and standard deviation
- **Response Time** percentiles (p50, p75, p90, p95, p99)
- **Speedup** vs baseline (concurrency=1)
- **Parallel Efficiency** (speedup/concurrency %)
- **Success Rate**

## Research Standards

✅ Multiple trials for statistical significance
✅ Warmup phase to eliminate cold-start effects
✅ Cool-down periods between trials
✅ Error bars showing measurement variance
✅ Raw data preservation for reproducibility
✅ Publication-quality visualizations (300 DPI)

## Methodology

For complete research methodology details, see: `EXPERIMENT_README.md`

## Architecture

```
Neo4j Database → REST Server (Async) → Benchmark Client
     ↓                   ↓                    ↓
  neo4j_db          rest_server      rest_client_benchmark
                  AsyncGraphDatabase     httpx async
```

Connected via Docker network: `benchmarking_patra-network`

## Files

```
rest_client/
├── docker-compose.yml      # Main entry point
├── Dockerfile              # Container definition
├── requirements.txt        # Python dependencies
├── experiment_config.json  # Benchmark configuration
├── run_experiment.py       # Experiment orchestration
├── analyze_results.py      # Statistical analysis
└── visualize_results.py    # Visualization generation
```
