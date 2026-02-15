#!/bin/bash

docker exec couchbase1 couchbase-cli cluster-init -c couchbase1 \
    --cluster-username admin \
    --cluster-password password \
    --services data,index,query \
    --cluster-ramsize 512 \
    --cluster-index-ramsize 256 \
    --index-storage-setting default\
    --cluster-eventing-ramsize 256 \
    --cluster-fts-ramsize 256 \
    --cluster-analytics-ramsize 1024 \
    --cluster-fts-ramsize 256

docker exec couchbase1 couchbase-cli server-add -c couchbase1.demo.local \
    -u admin \
    -p password \
    --server-add couchbase2.demo.local \
    --server-add-username admin \
    --server-add-password password \
    --services data,index

docker exec couchbase1 couchbase-cli server-add -c couchbase1.demo.local \
    -u admin \
    -p password \
    --server-add couchbase3.demo.local \
    --server-add-username admin \
    --server-add-password password \
    --services fts,eventing,analytics

docker exec couchbase1 couchbase-cli rebalance -c couchbase1 \
    -u admin \
    -p password
