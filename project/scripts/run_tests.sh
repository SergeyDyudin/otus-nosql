#!/bin/bash
set -e

cd "$(dirname "$0")/.."

TIMESTAMP=$(date +%Y%m%d_%H%M%S)

echo ""
echo "Restarting cluster for clean state..."
docker compose -f docker-compose.yaml restart
sleep 15

echo "=============================================="
echo " Test 1: Ramp-up (10→80 RPS, 2 min)"
echo "=============================================="
echo ""

uv run python load_tester.py -c load_rampup.yaml

R1=$(ls -td results/*/ 2>/dev/null | head -1)
if [ -n "$R1" ]; then
    mv "$R1" "results/${TIMESTAMP}_rampup"
    echo "Results saved: results/${TIMESTAMP}_rampup"
fi

echo ""
echo "=============================================="
echo " Test 2: Degradation — replicas only (15 RPS, 3 min)"
echo "=============================================="
echo ""

echo "Restarting cluster for clean state..."
docker compose -f docker-compose.yaml restart
sleep 15

echo "Nodes will be killed/restored on schedule:"
echo "   0-30s:  warmup (all nodes alive)"
echo "  30-60s: -1 replica per shard  (clickhouse-03 + clickhouse-04)"
echo "  60-90s: -2 replicas per shard (03+05, 04+06)"
echo "  90-120s: restore all replicas"
echo " 120-180s: cooldown"
echo ""

uv run python load_tester.py -c load_degradation.yaml &
TESTER_PID=$!

sleep 30
echo "[030s] Killing clickhouse-03 + clickhouse-04 (1 replica down per shard)"
docker stop clickhouse-03 clickhouse-04

sleep 30
echo "[060s] Killing clickhouse-05 + clickhouse-06 (2 replicas down per shard)"
docker stop clickhouse-05 clickhouse-06

sleep 30
echo "[090s] Restoring all replicas"
docker start clickhouse-03 clickhouse-04 clickhouse-05 clickhouse-06

sleep 90
echo "[180s] Waiting for tester to finish..."
wait $TESTER_PID

R2=$(ls -td results/*/ 2>/dev/null | head -1)
if [ -n "$R2" ] && [ "$R2" != "results/${TIMESTAMP}_rampup" ]; then
    mv "$R2" "results/${TIMESTAMP}_degradation"
    echo "Results saved: results/${TIMESTAMP}_degradation"
fi

echo ""
echo "=== All tests complete ==="
echo "Results:"
ls -d results/*_rampup results/*_degradation 2>/dev/null || true
