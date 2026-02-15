#! /bin/bash

# Создаем bucket
docker exec couchbase1 couchbase-cli bucket-create \
    --cluster couchbase1 \
    --username admin \
    --password password \
    --bucket meflix \
    --bucket-type couchbase \
    --bucket-ramsize 256 \
    --bucket-replica 1 \
    --num-vbuckets 128

# Создаем scope
docker exec couchbase1 couchbase-cli collection-manage \
    --cluster couchbase1 \
    --username admin \
    --password password \
    --bucket meflix \
    --create-scope public

# Создаем collection
docker exec couchbase1 couchbase-cli collection-manage \
    --cluster couchbase1 \
    --username admin \
    --password password \
    --bucket meflix \
    --create-collection public.users

# Импортируем документы в коллекцию
docker exec couchbase1 cbimport json \
    --cluster couchbase1 \
    --dataset file:///users.json --format list \
    --username admin \
    --password password \
    --bucket meflix \
    --scope-collection-exp public.users \
    --generate-key %id%
