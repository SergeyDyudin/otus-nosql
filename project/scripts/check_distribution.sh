#!/bin/bash
set -e

echo "=== Checking cluster health ==="
echo ""

echo "--- Keeper RAFT status ---"
echo stat | nc 127.0.0.1 9181 2>/dev/null | grep -E "Mode|Node count"

echo ""
echo "--- Cluster topology ---"
docker exec clickhouse-01 clickhouse-client --query "
SELECT cluster, shard_num, replica_num, host_name, port
FROM system.clusters WHERE cluster = 'cluster_2S_3R'
ORDER BY shard_num, replica_num
"

echo ""
echo "--- Data distribution ---"
echo "Total rows (trips_distributed):"
docker exec clickhouse-01 clickhouse-client --query "SELECT count() FROM taxi.trips_distributed"

echo ""
echo "Rows per node (trips_local):"
for NODE in clickhouse-01 clickhouse-02 clickhouse-03 clickhouse-04 clickhouse-05 clickhouse-06; do
    ROWS=$(docker exec "$NODE" clickhouse-client --query "SELECT count() FROM taxi.trips_local" 2>/dev/null || echo "offline")
    echo "  $NODE: $ROWS"
done

echo ""
echo "--- Shard 1 unique + Shard 2 unique ---"
S1=$(docker exec clickhouse-01 clickhouse-client --query "SELECT count() FROM taxi.trips_local")
S2=$(docker exec clickhouse-02 clickhouse-client --query "SELECT count() FROM taxi.trips_local")
echo "  Shard 1 (node-01): $S1"
echo "  Shard 2 (node-02): $S2"
echo "  Sum: $((S1 + S2))"
