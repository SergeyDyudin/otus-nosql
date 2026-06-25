#!/usr/bin/env python3
"""Generate charts from load test results."""

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from scripts.utils import percentile

DEGRADATION_PHASES = [
    ("0–30s\nwarmup", 0, 30, "#2ecc71"),
    ("30–60s\n−1 replica", 30, 60, "#f39c12"),
    ("60–90s\n−2 replicas", 60, 90, "#e74c3c"),
    ("90–120s\nrestore", 90, 120, "#f39c12"),
    ("120–180s\ncooldown", 120, 180, "#2ecc71"),
]


def _read_rows(csv_path):
    rows = []
    with open(csv_path) as fh_csv:
        for row in csv.DictReader(fh_csv):
            rows.append({
                "ts": float(row["timestamp"]),
                "sent_ts": float(row["sent_ts"]),
                "lat": float(row["latency_ms"]),
                "ok": row["status"] == "200",
            })
    return rows


def plot_degradation(csv_path: str, out_path: str):
    rows = _read_rows(csv_path)
    if not rows:
        print("No data")
        return

    t0 = rows[0]["sent_ts"]
    times = [row["sent_ts"] - t0 for row in rows]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 9),
        gridspec_kw={"height_ratios": [2, 1]},
    )

    ok_x = [times[i] for i, row in enumerate(rows) if row["ok"]]
    ok_y = [rows[i]["lat"] for i in range(len(rows)) if rows[i]["ok"]]
    err_x = [times[i] for i, row in enumerate(rows) if not row["ok"]]
    err_y = [rows[i]["lat"] for i in range(len(rows)) if not rows[i]["ok"]]

    ax1.scatter(ok_x, ok_y, s=2, alpha=0.4, c="#2ecc71", label="200 OK",
                rasterized=True)
    ax1.scatter(err_x, err_y, s=8, alpha=0.9, c="#e74c3c", marker="x",
                label="error", rasterized=True)

    for label, start, end, color in DEGRADATION_PHASES:
        ax1.axvline(start, color=color, linewidth=1, linestyle="--", alpha=0.5)
        ax1.axvspan(start, end, alpha=0.06, color=color)
        ylim = ax1.get_ylim()[1]
        ypos = ylim * 0.98 if ylim > 0 else 100
        ax1.text(
            (start + end) / 2, ypos, label,
            ha="center", va="top", fontsize=7,
            color=color, fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.2",
                      facecolor="white", alpha=0.7),
        )

    ax1.set_ylabel("Latency (ms)")
    ax1.set_xlabel("Time (seconds)")
    ax1.legend(loc="upper left", markerscale=3)
    ax1.set_title("Degradation test — latency with replica failures", fontweight="bold")
    ax1.set_xlim(0, max(times) * 1.01)

    labels, rates, colors = [], [], []
    for label, start, end, color in DEGRADATION_PHASES:
        bucket = [row for row in rows if start <= row["sent_ts"] - t0 < end]
        rate = sum(1 for rw in bucket if rw["ok"]) / len(bucket) * 100 if bucket else 0
        labels.append(label)
        rates.append(rate)
        colors.append(color)

    bars = ax2.bar(range(len(labels)), rates, color=colors,
                   edgecolor="white", linewidth=0.5)
    ax2.set_xticks(range(len(labels)))
    ax2.set_xticklabels(labels, fontsize=8)
    ax2.set_ylabel("Success rate (%)")
    ax2.set_ylim(0, 105)
    ax2.axhline(100, color="#2ecc71", linewidth=1, linestyle="--", alpha=0.5)
    for bar, rate in zip(bars, rates):
        ax2.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 1,
            f"{rate:.0f}%",
            ha="center", va="bottom",
            fontsize=9, fontweight="bold",
        )

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")


def plot_rampup(csv_path: str, out_path: str):
    rows = _read_rows(csv_path)
    if not rows:
        print("No data")
        return

    t0 = rows[0]["sent_ts"]
    times = [row["ts"] - t0 for row in rows]

    fig, ax = plt.subplots(figsize=(14, 6))

    ok_x = [times[i] for i, row in enumerate(rows) if row["ok"]]
    ok_y = [rows[i]["lat"] for i in range(len(rows)) if rows[i]["ok"]]
    err_x = [times[i] for i, row in enumerate(rows) if not row["ok"]]
    err_y = [rows[i]["lat"] for i in range(len(rows)) if not rows[i]["ok"]]

    ax.scatter(ok_x, ok_y, s=2, alpha=0.4, c="#2ecc71", label="200 OK",
               rasterized=True)
    if err_x:
        ax.scatter(err_x, err_y, s=8, alpha=0.9, c="#e74c3c", marker="x",
                   label="error", rasterized=True)

    window = 5
    chart_max_t = max(times)
    p50_x, p50_y, p90_y, p99_y = [], [], [], []
    for w_start in range(0, int(chart_max_t), window):
        bucket = [
            row["lat"]
            for i, row in enumerate(rows)
            if row["ok"] and w_start <= times[i] < w_start + window
        ]
        if bucket:
            p50_x.append(w_start + window / 2)
            p50_y.append(percentile(bucket, 50))
            p90_y.append(percentile(bucket, 90))
            p99_y.append(percentile(bucket, 99))
    if p50_x:
        ax.plot(p50_x, p50_y, "b-", linewidth=2, label="p50")
        ax.plot(p50_x, p90_y, "orange", linewidth=2, label="p90")
        ax.plot(p50_x, p99_y, "r-", linewidth=2, label="p99")

    ax.set_ylabel("Latency (ms)")
    ax.set_xlabel("Time (seconds)")

    xmax = 120
    ax.set_xlim(0, xmax)

    ax2 = ax.twiny()
    ax2.set_xlim(0, xmax)
    tick_times = [0, 30, 60, 90, 120]
    tick_rps = [int(10 + 70 * tick_sec / 120) for tick_sec in tick_times]
    ax2.set_xticks(tick_times)
    ax2.set_xticklabels([str(rps_val) for rps_val in tick_rps])
    ax2.set_xlabel("RPS")

    baseline_limit = 30
    baseline_vals = [
        row["lat"] for row in rows
        if row["ok"] and 0 <= row["sent_ts"] - t0 < baseline_limit
    ]
    baseline_p50 = percentile(baseline_vals, 50) if baseline_vals else 0

    sat_t = None
    if baseline_p50 > 0 and p50_x:
        for win_x, win_p50 in zip(p50_x, p50_y):
            if win_x > baseline_limit and win_p50 > baseline_p50 * 2:
                sat_t = win_x
                break

    if sat_t is not None:
        sat_rps = int(10 + 70 * sat_t / 120)
        ax.axvline(sat_t, color="#e74c3c", linestyle="--",
                   linewidth=1.5, alpha=0.7)
        ax.text(
            sat_t + 2, ax.get_ylim()[1] * 0.95,
            f"saturation\n~{sat_rps} RPS",
            color="#e74c3c", fontsize=9, fontweight="bold", va="top",
            bbox=dict(boxstyle="round,pad=0.3",
                      facecolor="white", alpha=0.8),
        )

    display_limit = sat_t if sat_t is not None else baseline_limit

    ax.legend(loc="upper left", markerscale=3)
    ax.set_title(
        "Ramp-up test — latency under increasing RPS (10→80)",
        fontweight="bold",
    )

    baseline = sorted(
        row["lat"]
        for row in rows
        if row["ok"] and 0 <= row["sent_ts"] - t0 < display_limit
    )
    if baseline:
        count = len(baseline)
        bl_p50 = baseline[count // 2]
        bl_p90 = baseline[int(count * 0.9)]
        bl_p99 = baseline[int(count * 0.99)]
        ax.text(
            0.98, 0.95,
            f"Baseline (0–{display_limit:.0f}s):\n"
            f"p50: {bl_p50:.0f}ms\n"
            f"p90: {bl_p90:.0f}ms\n"
            f"p99: {bl_p99:.0f}ms",
            transform=ax.transAxes, fontsize=9, fontfamily="monospace",
            va="top", ha="right",
            bbox=dict(boxstyle="round,pad=0.5",
                      facecolor="white", edgecolor="#ccc", alpha=0.9),
        )

    fig.tight_layout()
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    results_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None

    if results_dir:
        rampup_dir = results_dir.parent / \
            results_dir.name.replace("_degradation", "_rampup")
        degrad_csv = results_dir / "results.csv"
        rampup_csv = rampup_dir / "results.csv"
        if not degrad_csv.exists():
            degrad_csv = None
        if not rampup_csv.exists():
            rampup_csv = None
    else:
        base = Path(__file__).resolve().parent.parent / "results"
        degrad_dirs = sorted(base.glob("*_degradation"))
        degrad_csv = degrad_dirs[-1] / "results.csv" if degrad_dirs else None
        if degrad_dirs:
            ts = degrad_dirs[-1].name.replace("_degradation", "")
            rampup_csv = base / f"{ts}_rampup" / "results.csv"
        else:
            rampup_csv = None

    if degrad_csv and degrad_csv.exists():
        plot_degradation(str(degrad_csv),
                         str(degrad_csv.parent / "degradation_chart.png"))
    else:
        print("No degradation results found")

    if rampup_csv and rampup_csv.exists():
        plot_rampup(str(rampup_csv),
                    str(rampup_csv.parent / "rampup_chart.png"))
    else:
        print("No ramp-up results found")
