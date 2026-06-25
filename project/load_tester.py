#!/usr/bin/env python3
"""
Load tester for ClickHouse HTTP interface.
Generates controlled RPS, measures latency, saves CSV + summary.
"""

import asyncio
import csv
import random
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml
import httpx

sys.path.insert(0, str(Path(__file__).resolve().parent))
from scripts.utils import parse_schedule, percentile

QUERIES = {
    "light": "SELECT count(), avg(tip_amount), avg(total_amount) FROM taxi.trips_distributed",
    "medium": (
        "SELECT passenger_count, count(), round(avg(tip_amount), 2), "
        "round(avg(total_amount), 2) FROM taxi.trips_distributed "
        "GROUP BY passenger_count ORDER BY passenger_count"
    ),
    "heavy": (
        "SELECT pickup_ntaname, count(), round(avg(total_amount), 2) "
        "FROM taxi.trips_distributed WHERE pickup_ntaname != '' "
        "GROUP BY pickup_ntaname ORDER BY count() DESC LIMIT 20"
    ),
}

WEIGHTS = {"light": 55, "medium": 30, "heavy": 15}


def build_pool():
    pool = []
    for qtype, weight in WEIGHTS.items():
        pool.extend([qtype] * weight)
    return pool


def count_status(results, ok=True):
    if ok:
        return sum(1 for entry in results if entry["status"] == 200)
    return sum(1 for entry in results if entry["status"] != 200)


async def fire_request(client, url, query, results):
    sent = time.time()
    t0 = time.monotonic()
    try:
        resp = await client.post(url, content=query, timeout=30.0)
        lat = (time.monotonic() - t0) * 1000
        results.append({
            "sent_ts": sent,
            "timestamp": time.time(),
            "latency_ms": lat,
            "status": resp.status_code,
        })
    except Exception as exc:
        lat = (time.monotonic() - t0) * 1000
        results.append({
            "sent_ts": sent,
            "timestamp": time.time(),
            "latency_ms": lat,
            "status": 0,
            "error": str(exc),
        })


async def _run_test(client, url, pool, results, sched, out):
    stype = sched[0]
    start = time.monotonic()

    if stype == "const":
        await _run_const(client, url, pool, results, sched, start)
    elif stype == "line":
        await _run_line(client, url, pool, results, sched, start)


async def _run_const(client, url, pool, results, sched, start):
    rps, dur = sched[1], sched[2]
    end = start + dur
    tick = 0
    rng = random.Random()
    print(f"Test: const({rps}, {dur}s) → {url}")
    while time.monotonic() < end:
        t0 = time.monotonic()
        for _ in range(rps):
            query_text = QUERIES[rng.choice(pool)]
            asyncio.create_task(
                fire_request(client, url, query_text, results)
            )
        tick += 1
        dt = time.monotonic() - t0
        if dt < 1.0:
            await asyncio.sleep(1.0 - dt)
        if tick % 10 == 0:
            elapsed = int(time.monotonic() - start)
            ok = count_status(results, True)
            err = count_status(results, False)
            print(f"  [{elapsed}s] RPS={rps}  ok={ok}  err={err}")


async def _run_line(client, url, pool, results, sched, start):
    r0, r1, dur = sched[1], sched[2], sched[3]
    end = start + dur
    tick = 0
    rng = random.Random()
    print(f"Test: line({r0}, {r1}, {dur}s) → {url}")
    while time.monotonic() < end:
        t0 = time.monotonic()
        elapsed = tick * 1.0
        frac = min(elapsed / dur, 1.0)
        current = max(1, int(r0 + (r1 - r0) * frac))
        for _ in range(current):
            query_text = QUERIES[rng.choice(pool)]
            asyncio.create_task(
                fire_request(client, url, query_text, results)
            )
        tick += 1
        dt = time.monotonic() - t0
        if dt < 1.0:
            await asyncio.sleep(1.0 - dt)
        if tick % 5 == 0:
            elapsed = int(time.monotonic() - start)
            ok = count_status(results, True)
            err = count_status(results, False)
            print(f"  [{elapsed}s] RPS={current}  ok={ok}  err={err}")


async def run(config_path):
    with open(config_path) as fh_config:
        cfg = yaml.safe_load(fh_config)
    target = cfg["target"]
    url = f"http://{target}/"
    sched = parse_schedule(cfg["load_profile"]["schedule"])
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = Path(cfg.get("output", "results")) / ts
    out.mkdir(parents=True, exist_ok=True)

    pool = build_pool()
    results = []

    limits = httpx.Limits(max_connections=200, max_keepalive_connections=50)
    async with httpx.AsyncClient(limits=limits) as client:
        await _run_test(client, url, pool, results, sched, out)

    print(f"\nTest finished. Total requests: {len(results)}")

    csv_path = out / "results.csv"
    fields = ["sent_ts", "timestamp", "latency_ms", "status", "error"]
    with open(csv_path, "w", newline="") as fh_csv:
        writer = csv.DictWriter(fh_csv, fieldnames=fields)
        writer.writeheader()
        for entry in results:
            writer.writerow({col: entry.get(col, "") for col in fields})

    ok_list = [entry for entry in results if entry["status"] == 200]
    errs = [entry for entry in results if entry["status"] != 200]
    lats = [entry["latency_ms"] for entry in ok_list]

    summary_path = out / "summary.txt"
    lines = [f"Total: {len(results)}",
             f"  200 OK: {len(ok_list)}",
             f"  Errors: {len(errs)}"]
    if lats:
        lines += [
            "Latency (ms):",
            f"  avg: {sum(lats) / len(lats):.1f}",
            f"  p50: {percentile(lats, 50):.1f}",
            f"  p90: {percentile(lats, 90):.1f}",
            f"  p95: {percentile(lats, 95):.1f}",
            f"  p99: {percentile(lats, 99):.1f}",
            f"  max: {max(lats):.1f}",
        ]
    summary_path.write_text("\n".join(lines) + "\n")

    print(f"\nResults: {out}/")
    print(f"  200 OK: {len(ok_list)}")
    print(f"  Errors: {len(errs)}")
    if lats:
        avg = sum(lats) / len(lats)
        print(
            f"  avg: {avg:.1f}ms  p50: {percentile(lats, 50):.1f}ms  "
            f"p90: {percentile(lats, 90):.1f}ms  "
            f"p95: {percentile(lats, 95):.1f}ms  "
            f"p99: {percentile(lats, 99):.1f}ms"
        )


if __name__ == "__main__":
    if len(sys.argv) < 3 or sys.argv[1] != "-c":
        print("Usage: python3 load_tester.py -c <config.yaml>", file=sys.stderr)
        sys.exit(1)
    asyncio.run(run(sys.argv[2]))
