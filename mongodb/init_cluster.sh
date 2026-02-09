#!/bin/bash

# Функция для ожидания готовности MongoDB
wait_for_mongo() {
    local container=$1
    local max_attempts=30
    local attempt=1

    echo "Ожидание запуска MongoDB в контейнере $container..."

    while [ $attempt -le $max_attempts ]; do
        if docker exec $container mongosh --eval "db.adminCommand('ping')" --quiet > /dev/null 2>&1; then
            echo "$container готов"
            return 0
        fi
        echo "Попытка $attempt/$max_attempts: $container еще не готов..."
        sleep 2
        ((attempt++))
    done

    echo "Таймаут ожидания $container"
    return 1
}


echo "Инициализация Config Server Replica Set..."
docker exec mongo-config-srv-1 mongosh --eval "
rs.initiate(
  {
    _id: 'config-replica-set',
    configsvr: true,
    members: [
      { _id: 0, host: 'mongo-config-srv-1:27017' },
      { _id: 1, host: 'mongo-config-srv-2:27017' },
      { _id: 2, host: 'mongo-config-srv-3:27017' }
    ]
  }
)"

# Ждем инициализации config серверов
echo "Ожидание инициализации Config Server..."
sleep 5


# 2. Инициализация шардов (каждый шард - свой replica set)
echo "Инициализация шардов..."

# Шард 1
echo "Инициализация Shard 1..."
docker exec mongo-shard-1-rs-1 mongosh --eval "
rs.initiate(
  {
    _id: 'shard-replica-set-1',
    members: [
      { _id: 0, host: 'mongo-shard-1-rs-1:27017' },
      { _id: 1, host: 'mongo-shard-1-rs-2:27017' },
      { _id: 2, host: 'mongo-shard-1-rs-3:27017' }
    ]
  }
)"

# Шард 2
echo "Инициализация Shard 2..."
docker exec mongo-shard-2-rs-1 mongosh --eval "
rs.initiate(
  {
    _id: 'shard-replica-set-2',
    members: [
      { _id: 0, host: 'mongo-shard-2-rs-1:27017' },
      { _id: 1, host: 'mongo-shard-2-rs-2:27017' },
      { _id: 2, host: 'mongo-shard-2-rs-3:27017' }
    ]
  }
)"

# Шард 3
echo "Инициализация Shard 3..."
docker exec mongo-shard-3-rs-1 mongosh --eval "
rs.initiate(
  {
    _id: 'shard-replica-set-3',
    members: [
      { _id: 0, host: 'mongo-shard-3-rs-1:27017' },
      { _id: 1, host: 'mongo-shard-3-rs-2:27017' },
      { _id: 2, host: 'mongo-shard-3-rs-3:27017' }
    ]
  }
)"

# Ждем инициализации шардов
echo "Ожидание инициализации шардов..."
sleep 5

# 3. Добавление шардов в кластер через mongos (router)
echo "Добавление шардов в кластер через mongos..."

# Ждем готовности mongos
wait_for_mongo mongo-router-1

# Добавляем шарды
docker exec mongo-router-1 mongosh --eval "
sh.addShard('shard-replica-set-1/mongo-shard-1-rs-1:27017,mongo-shard-1-rs-2:27017,mongo-shard-1-rs-3:27017');
sh.addShard('shard-replica-set-2/mongo-shard-2-rs-1:27017,mongo-shard-2-rs-2:27017,mongo-shard-2-rs-3:27017');
sh.addShard('shard-replica-set-3/mongo-shard-3-rs-1:27017,mongo-shard-3-rs-2:27017,mongo-shard-3-rs-3:27017');
"

echo "Кластер MongoDB успешно инициализирован!"