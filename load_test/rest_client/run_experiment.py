"""
Research-grade benchmarking experiment runner.

Systematically tests REST API performance across multiple concurrency levels
with proper experimental controls and statistical rigor.
"""

import os
import json
import asyncio
import httpx
import time
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
import statistics


class ExperimentRunner:
    """Orchestrates systematic benchmarking experiments."""

    def __init__(self, config_path: str = "experiment_config.json"):
        """Initialize experiment runner with configuration."""
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        # Create experiment directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.experiment_dir = Path(self.config['results_dir']) / f"{self.config['experiment_name']}_{timestamp}"
        self.experiment_dir.mkdir(parents=True, exist_ok=True)

        # Save configuration
        with open(self.experiment_dir / "config.json", 'w') as f:
            json.dump(self.config, f, indent=2)

        # Initialize results storage
        self.results = []

    async def warmup(self, client: httpx.AsyncClient, num_requests: int):
        """Perform warmup requests to stabilize server state."""
        print(f"  Warmup: {num_requests} requests...", end=" ", flush=True)
        semaphore = asyncio.Semaphore(5)  # Low concurrency for warmup

        tasks = [
            self._single_request(client, semaphore, i)
            for i in range(num_requests)
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        print("✓")

    async def _single_request(self, client: httpx.AsyncClient, semaphore: asyncio.Semaphore, request_id: int) -> Dict[str, Any]:
        """Execute a single HTTP request with timing."""
        async with semaphore:
            start_time = time.perf_counter()
            try:
                response = await client.get(
                    f"{self.config['server_url']}/modelcard/{self.config['modelcard_id']}"
                )
                end_time = time.perf_counter()

                response_time_ms = (end_time - start_time) * 1000
                response_size_bytes = len(response.text.encode('utf-8'))

                return {
                    "request_id": request_id,
                    "success": True,
                    "response_time_ms": response_time_ms,
                    "response_size_kb": response_size_bytes / 1024,
                    "status_code": response.status_code,
                    "error": None,
                    "timestamp": time.time()
                }
            except Exception as e:
                end_time = time.perf_counter()
                response_time_ms = (end_time - start_time) * 1000
                return {
                    "request_id": request_id,
                    "success": False,
                    "response_time_ms": response_time_ms,
                    "response_size_kb": 0,
                    "status_code": None,
                    "error": str(e),
                    "timestamp": time.time()
                }

    async def run_trial(self, concurrency_level: int, trial_num: int) -> Dict[str, Any]:
        """Run a single trial with specified concurrency level."""
        print(f"\n  Trial {trial_num + 1}/{self.config['trials_per_level']}")

        # Configure HTTP client
        timeout = httpx.Timeout(self.config['timeout_seconds'], connect=10.0)
        limits = httpx.Limits(
            max_keepalive_connections=concurrency_level,
            max_connections=concurrency_level * 2
        )

        async with httpx.AsyncClient(timeout=timeout, limits=limits) as client:
            # Warmup phase
            await self.warmup(client, self.config['warmup_requests'])

            # Measurement phase
            print(f"  Measuring: {self.config['requests_per_trial']} requests at concurrency {concurrency_level}...", end=" ", flush=True)
            semaphore = asyncio.Semaphore(concurrency_level)

            start_time = time.perf_counter()
            tasks = [
                self._single_request(client, semaphore, i)
                for i in range(self.config['requests_per_trial'])
            ]
            results = await asyncio.gather(*tasks)
            end_time = time.perf_counter()

            total_time = end_time - start_time
            print("✓")

            # Analyze results
            trial_data = self._analyze_trial(results, total_time, concurrency_level, trial_num)

            # Save raw data
            self._save_trial_data(results, concurrency_level, trial_num)

            return trial_data

    def _analyze_trial(self, results: List[Dict[str, Any]], total_time: float,
                       concurrency_level: int, trial_num: int) -> Dict[str, Any]:
        """Analyze results from a single trial."""
        successful = [r for r in results if r["success"]]
        failed = [r for r in results if not r["success"]]

        if not successful:
            return {
                "concurrency_level": concurrency_level,
                "trial_num": trial_num,
                "total_requests": len(results),
                "successful_requests": 0,
                "failed_requests": len(failed),
                "success_rate": 0.0,
                "error": "All requests failed"
            }

        response_times = [r["response_time_ms"] for r in successful]
        response_times_sorted = sorted(response_times)

        # Calculate percentiles
        percentiles = {}
        for p in self.config['percentiles']:
            percentiles[f"p{p}"] = self._percentile(response_times_sorted, p)

        trial_data = {
            "concurrency_level": concurrency_level,
            "trial_num": trial_num,
            "total_requests": len(results),
            "successful_requests": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(results) * 100,
            "total_time_seconds": total_time,
            "throughput_req_per_sec": len(successful) / total_time,
            "response_time_mean_ms": statistics.mean(response_times),
            "response_time_median_ms": statistics.median(response_times),
            "response_time_stdev_ms": statistics.stdev(response_times) if len(response_times) > 1 else 0,
            "response_time_min_ms": min(response_times),
            "response_time_max_ms": max(response_times),
            **percentiles,
            "avg_response_size_kb": statistics.mean([r["response_size_kb"] for r in successful])
        }

        return trial_data

    def _percentile(self, sorted_data: List[float], percentile: int) -> float:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return 0.0
        index = (percentile / 100) * (len(sorted_data) - 1)
        lower = int(index)
        upper = lower + 1
        weight = index - lower

        if upper >= len(sorted_data):
            return sorted_data[-1]
        return sorted_data[lower] * (1 - weight) + sorted_data[upper] * weight

    def _save_trial_data(self, results: List[Dict[str, Any]], concurrency_level: int, trial_num: int):
        """Save raw trial data to CSV."""
        trial_dir = self.experiment_dir / f"concurrency_{concurrency_level}"
        trial_dir.mkdir(exist_ok=True)

        csv_file = trial_dir / f"trial_{trial_num}_raw.csv"
        with open(csv_file, 'w', newline='') as f:
            if results:
                writer = csv.DictWriter(f, fieldnames=results[0].keys())
                writer.writeheader()
                writer.writerows(results)

    async def run_concurrency_level(self, concurrency_level: int):
        """Run all trials for a specific concurrency level."""
        print(f"\n{'='*70}")
        print(f"Concurrency Level: {concurrency_level}")
        print(f"{'='*70}")

        trials_data = []
        for trial_num in range(self.config['trials_per_level']):
            trial_data = await self.run_trial(concurrency_level, trial_num)
            trials_data.append(trial_data)

            # Cool-down between trials
            if trial_num < self.config['trials_per_level'] - 1:
                cooldown = self.config['cooldown_seconds']
                print(f"  Cooldown: {cooldown}s...", end=" ", flush=True)
                await asyncio.sleep(cooldown)
                print("✓")

        # Aggregate statistics across trials
        aggregate_stats = self._aggregate_trials(trials_data, concurrency_level)
        self.results.append(aggregate_stats)

        # Print summary
        self._print_summary(aggregate_stats)

        return aggregate_stats

    def _aggregate_trials(self, trials_data: List[Dict[str, Any]], concurrency_level: int) -> Dict[str, Any]:
        """Aggregate statistics across multiple trials."""
        if not trials_data:
            return {}

        # Metrics to aggregate
        metrics = [
            'throughput_req_per_sec',
            'response_time_mean_ms',
            'response_time_median_ms',
            'response_time_stdev_ms',
            'response_time_min_ms',
            'response_time_max_ms',
            'success_rate'
        ]

        # Add percentiles
        for p in self.config['percentiles']:
            metrics.append(f'p{p}')

        aggregate = {
            'concurrency_level': concurrency_level,
            'num_trials': len(trials_data)
        }

        # Calculate mean and stdev for each metric across trials
        for metric in metrics:
            values = [t[metric] for t in trials_data if metric in t]
            if values:
                aggregate[f'{metric}_mean'] = statistics.mean(values)
                aggregate[f'{metric}_stdev'] = statistics.stdev(values) if len(values) > 1 else 0
                aggregate[f'{metric}_min'] = min(values)
                aggregate[f'{metric}_max'] = max(values)

        return aggregate

    def _print_summary(self, aggregate_stats: Dict[str, Any]):
        """Print summary statistics for a concurrency level."""
        print(f"\n  Summary (across {aggregate_stats['num_trials']} trials):")
        print(f"    Throughput:        {aggregate_stats['throughput_req_per_sec_mean']:.2f} ± {aggregate_stats['throughput_req_per_sec_stdev']:.2f} req/s")
        print(f"    Response Time:     {aggregate_stats['response_time_mean_ms_mean']:.2f} ± {aggregate_stats['response_time_mean_ms_stdev']:.2f} ms (mean)")
        print(f"    Response Time:     {aggregate_stats['response_time_median_ms_mean']:.2f} ms (median)")
        print(f"    Response Time p95: {aggregate_stats['p95_mean']:.2f} ms")
        print(f"    Response Time p99: {aggregate_stats['p99_mean']:.2f} ms")
        print(f"    Success Rate:      {aggregate_stats['success_rate_mean']:.2f}%")

    async def run_full_experiment(self):
        """Run the complete experiment across all concurrency levels."""
        print("\n" + "="*70)
        print(f"Starting Experiment: {self.config['experiment_name']}")
        print(f"Output Directory: {self.experiment_dir}")
        print("="*70)
        print(f"\nConfiguration:")
        print(f"  Concurrency Levels: {self.config['concurrency_levels']}")
        print(f"  Trials per Level: {self.config['trials_per_level']}")
        print(f"  Requests per Trial: {self.config['requests_per_trial']}")
        print(f"  Total Requests: {len(self.config['concurrency_levels']) * self.config['trials_per_level'] * self.config['requests_per_trial']}")

        start_time = time.time()

        for concurrency_level in self.config['concurrency_levels']:
            await self.run_concurrency_level(concurrency_level)

        end_time = time.time()
        total_duration = end_time - start_time

        # Save aggregated results
        self._save_results(total_duration)

        print("\n" + "="*70)
        print(f"Experiment Complete!")
        print(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
        print(f"Results saved to: {self.experiment_dir}")
        print("="*70 + "\n")

    def _save_results(self, total_duration: float):
        """Save aggregated experimental results."""
        # Save summary CSV
        summary_file = self.experiment_dir / "summary_statistics.csv"
        if self.results:
            with open(summary_file, 'w', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=self.results[0].keys())
                writer.writeheader()
                writer.writerows(self.results)

        # Save experiment report
        report_file = self.experiment_dir / "experiment_report.txt"
        with open(report_file, 'w') as f:
            f.write(f"Experiment: {self.config['experiment_name']}\n")
            f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)\n")
            f.write(f"\nConfiguration:\n")
            f.write(json.dumps(self.config, indent=2))
            f.write(f"\n\nResults Summary:\n")
            f.write("="*70 + "\n")

            for result in self.results:
                f.write(f"\nConcurrency Level: {result['concurrency_level']}\n")
                f.write(f"  Throughput:        {result['throughput_req_per_sec_mean']:.2f} ± {result['throughput_req_per_sec_stdev']:.2f} req/s\n")
                f.write(f"  Response Time:     {result['response_time_mean_ms_mean']:.2f} ± {result['response_time_mean_ms_stdev']:.2f} ms (mean)\n")
                f.write(f"  Response Time:     {result['response_time_median_ms_mean']:.2f} ms (median)\n")
                f.write(f"  Response Time p95: {result['p95_mean']:.2f} ms\n")
                f.write(f"  Response Time p99: {result['p99_mean']:.2f} ms\n")
                f.write(f"  Success Rate:      {result['success_rate_mean']:.2f}%\n")


async def main():
    """Main entry point for experiment runner."""
    config_path = os.getenv("EXPERIMENT_CONFIG", "experiment_config.json")

    runner = ExperimentRunner(config_path)
    await runner.run_full_experiment()


if __name__ == "__main__":
    asyncio.run(main())
