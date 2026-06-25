#!/usr/bin/env python3
"""Analyze degradation test results — per-phase statistics."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import percentile

PHASES = [
    ("0-30s   warmup", 0, 30),
    ("30-60s  -1 replica", 30, 60),
    ("60-90s  -2 replicas", 60, 90),
    ("90-120s restore", 90, 120),
    ("120-180s cooldown", 120, 180),
]


def analyze(csv_path: str):
    rows = []
    with open(csv_path) as fh_csv:
        for row in csv.DictReader(fh_csv):
            rows.append({
                "sent": float(row["sent_ts"]),
                "lat": float(row["latency_ms"]),
                "ok": row["status"] == "200",
            })

    if not rows:
        print("No data")
        return

    t0 = rows[0]["sent"]

    header = (
        f"{'Phase':<20} {'Sent':>6} {'OK':>6} {'Err':>6} "
        f"{'OK%':>6}  {'p50':>8} {'p90':>8} {'p99':>8}"
    )
    print(header)
    print("-" * 80)

    for label, t_start, t_end in PHASES:
        bucket = [row for row in rows if t_start <= row["sent"] - t0 < t_end]
        sent = len(bucket)
        ok_list = [row for row in bucket if row["ok"]]
        err_list = [row for row in bucket if not row["ok"]]
        lats = [row["lat"] for row in ok_list]
        rate = f"{len(ok_list) / sent * 100:.0f}%" if sent else "-"
        if lats:
            p50 = percentile(lats, 50)
            p90 = percentile(lats, 90)
            p99 = percentile(lats, 99)
            print(
                f"{label:<20} {sent:>6} {len(ok_list):>6} "
                f"{len(err_list):>6} {rate:>6}  "
                f"{p50:>7.0f}ms {p90:>7.0f}ms {p99:>7.0f}ms"
            )
        else:
            print(
                f"{label:<20} {sent:>6} {len(ok_list):>6} "
                f"{len(err_list):>6} {rate:>6}"
            )


if __name__ == "__main__":
    if len(sys.argv) < 2:
        latest = sorted(
            (Path(__file__).resolve().parent.parent / "results")
            .glob("*_degradation/results.csv")
        )
        if latest:
            csv_path = str(latest[-1])
            print(f"Using latest: {csv_path}\n")
        else:
            print("Usage: python3 analyze.py <path to results.csv>")
            sys.exit(1)
    else:
        csv_path = sys.argv[1]
    analyze(csv_path)
