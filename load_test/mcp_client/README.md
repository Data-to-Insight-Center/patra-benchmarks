# MCP API Async Benchmarking Client

Quick start:

```bash
cd /home/exouser/patra-kg/mcp_client
docker compose up
```

This will:
- Connect to the MCP server container on the shared network
- Run experiments, analyze results, and generate plots
- Save everything to `experiments/` and exit when complete

Configuration: edit `experiment_config.json` and rerun `docker compose up --build`.

Results saved under `experiments/MCP_API_Concurrency_Analysis_[timestamp]/`.


