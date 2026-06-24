"""End-to-end API smoke test against a running server."""

import asyncio
import json
import sys
import time

import httpx

BASE = "http://127.0.0.1:8000"


async def wait_for_run(client: httpx.AsyncClient, run_id: str, timeout: float = 30) -> dict:
    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = await client.get(f"{BASE}/api/runs/{run_id}")
        resp.raise_for_status()
        data = resp.json()["data"]
        if data["status"] in ("completed", "failed"):
            return data
        await asyncio.sleep(0.5)
    raise TimeoutError(f"Run {run_id} did not complete within {timeout}s")


async def main() -> int:
    failures: list[str] = []

    async with httpx.AsyncClient(timeout=30.0) as client:
        print("1. Health check...")
        health = await client.get(f"{BASE}/health")
        if health.status_code != 200:
            failures.append(f"health: {health.status_code}")
        else:
            print(f"   OK — {health.json()}")

        print("2. List agents...")
        agents = await client.get(f"{BASE}/api/agents")
        agents.raise_for_status()
        agent_list = agents.json()["data"]
        assert len(agent_list) >= 1
        print(f"   OK — {len(agent_list)} agents")

        print("3. Create eval run (mock agent)...")
        create = await client.post(
            f"{BASE}/api/runs",
            json={
                "agent_name": "mock",
                "llm_model": "mock-model",
                "task_description": "E2E test: summarize quarterly revenue trends",
            },
        )
        create.raise_for_status()
        run_id = create.json()["data"]["id"]
        print(f"   OK — run_id={run_id[:8]}")

        print("4. Wait for run completion...")
        run = await wait_for_run(client, run_id)
        if run["status"] != "completed":
            failures.append(f"run status: {run['status']}")
        else:
            print(
                f"   OK — composite={run['composite_score']}, steps={run.get('total_steps')}"
            )

        print("5. Fetch run steps and score...")
        steps = await client.get(f"{BASE}/api/runs/{run_id}/steps")
        score = await client.get(f"{BASE}/api/runs/{run_id}/score")
        steps.raise_for_status()
        score.raise_for_status()
        step_count = len(steps.json()["data"])
        print(f"   OK — {step_count} steps, score breakdown retrieved")

        print("6. Export JSON report...")
        report = await client.post(
            f"{BASE}/api/reports/export",
            json={"run_id": run_id, "format": "json"},
        )
        report.raise_for_status()
        print("   OK — report exported")

        print("7. Dashboard stats...")
        stats = await client.get(f"{BASE}/api/stats")
        stats.raise_for_status()
        print(f"   OK — total_runs={stats.json()['data']['total_runs']}")

        print("8. Trigger benchmark...")
        bench = await client.post(
            f"{BASE}/api/benchmarks",
            json={
                "benchmark_name": "E2E Benchmark",
                "task_description": "Compare models on revenue summary task",
                "models": ["mock-model", "gpt-4o"],
                "agent_name": "mock",
            },
        )
        bench.raise_for_status()
        print("   OK — benchmark started")

        print("9. Wait for benchmark results...")
        deadline = time.time() + 60
        benchmark_data = None
        while time.time() < deadline:
            listing = await client.get(f"{BASE}/api/benchmarks")
            listing.raise_for_status()
            items = listing.json()["data"]
            match = next((b for b in items if b["benchmark_name"] == "E2E Benchmark"), None)
            if match and match.get("winner_model") and match["winner_model"] != "pending":
                benchmark_data = match
                break
            await asyncio.sleep(1)
        if not benchmark_data:
            failures.append("benchmark did not complete in time")
        else:
            print(f"   OK — winner={benchmark_data['winner_model']}")

        print("10. List runs...")
        runs = await client.get(f"{BASE}/api/runs")
        runs.raise_for_status()
        total = runs.json()["data"]["total"]
        print(f"   OK — {total} runs in database")

    if failures:
        print("\nFAILED:")
        for f in failures:
            print(f"  - {f}")
        return 1

    print("\nAll E2E checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
