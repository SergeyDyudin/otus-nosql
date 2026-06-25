"""Shared utilities for load testing scripts."""

import re


def percentile(data, pct):
    if not data:
        return 0
    values = sorted(data)
    pos = (len(values) - 1) * pct / 100.0
    idx = int(pos)
    frac = pos - idx
    if idx + 1 < len(values):
        return values[idx] + frac * (values[idx + 1] - values[idx])
    return values[idx]


def parse_schedule(schedule_str):
    match = re.match(
        r"(const|line)\(([^,]+),\s*([^,]+)(?:,\s*([^)]+))?\)",
        schedule_str,
    )
    if not match:
        raise ValueError(f"Bad schedule: {schedule_str}")
    stype = match.group(1)
    args = [g for g in match.groups()[1:] if g]
    if stype == "const":
        return stype, _rps(args[0]), _dur(args[1])
    return stype, _rps(args[0]), _rps(args[1]), _dur(args[2])


def _rps(value):
    return int(value.strip())


def _dur(value):
    value = value.strip()
    if value.endswith("m"):
        return float(value[:-1]) * 60
    if value.endswith("s"):
        return float(value[:-1])
    return float(value)
