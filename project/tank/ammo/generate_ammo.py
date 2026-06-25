#!/usr/bin/env python3
"""Generate ammo file for Yandex Tank Phantom generator (POST format)."""

from urllib.parse import quote_plus

QUERIES = {
    "light": "SELECT count(), avg(tip_amount), avg(total_amount) FROM taxi.trips_distributed",
    "medium": "SELECT passenger_count, count(), round(avg(tip_amount), 2), round(avg(total_amount), 2) FROM taxi.trips_distributed GROUP BY passenger_count ORDER BY passenger_count",
    "heavy": "SELECT pickup_ntaname, count(), round(avg(total_amount), 2) FROM taxi.trips_distributed WHERE pickup_ntaname != '' GROUP BY pickup_ntaname ORDER BY count() DESC LIMIT 20",
}

WEIGHTS = {"light": 55, "medium": 30, "heavy": 15}


def build_ammo(query: str, host: str = "clickhouse-01:8123") -> str:
    encoded = quote_plus(query)
    request = (
        f"GET /?query={encoded} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "Connection: keep-alive\r\n"
        "\r\n"
    )
    return f"{len(request)}\n{request}"


def main():
    import random

    output_path = "ammo/analytics.ammo"

    variants = []
    for qtype, weight in WEIGHTS.items():
        variants.extend([qtype] * weight)

    with open(output_path, "w") as f:
        for _ in range(1000):
            qtype = random.choice(variants)
            f.write(build_ammo(QUERIES[qtype]))

    print(f"Generated {output_path} with 1000 requests")


if __name__ == "__main__":
    main()
