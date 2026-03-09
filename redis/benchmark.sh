#!/bin/bash
JSON_FILE="./data/large-file.json"
TIMEFORMAT='%3R'

# Точное количество элементов JSON
NUM=$(jq '. | length' $JSON_FILE)
echo "Количество элементов в тестовом файле: $NUM"
echo ""

# Новый элемент для теста
NEW_KEY=$NUM
NEW_VAL=$(jq -c '.[] | . as $line | $line' $JSON_FILE | head -n1)


echo "Очищаем базу данных..."
redis-cli FLUSHALL

#######################
# STRING
#######################
echo "Заполняем STRING..."
jq -c '.[]' $JSON_FILE | nl -v0 | while read i elem; do
  redis-cli SET test:string:$i "$elem" > /dev/null
done
echo "Готово"

echo "Вставляем новый и читаем новый элемент..."
STRING_WRITE=$( { time redis-cli SET test:string:$NEW_KEY "$NEW_VAL" > /dev/null; } 2>&1 )
STRING_READ=$( { time redis-cli GET test:string:$NEW_KEY > /dev/null; } 2>&1 )
echo "STRING: запись $STRING_WRITE сек, чтение $STRING_READ сек"
echo ""

#######################
# LIST
#######################
echo "Заполняем LIST..."
jq -c '.[]' $JSON_FILE | while read elem; do
  redis-cli RPUSH test:list "$elem" > /dev/null
done
echo "Готово"

echo "Вставляем новый и читаем новый элемент..."
LIST_WRITE=$( { time redis-cli RPUSH test:list "$NEW_VAL" > /dev/null; } 2>&1 )
LIST_READ=$( { time redis-cli LINDEX test:list -1 > /dev/null; } 2>&1 )
echo "LIST: запись $LIST_WRITE сек, чтение $LIST_READ сек"
echo ""

#######################
# HASH
#######################
echo "Заполняем HASH..."
jq -c '.[]' $JSON_FILE | nl -v0 | while read i elem; do
  redis-cli HSET test:hash $i "$elem" > /dev/null
done
echo "Готово"

echo "Вставляем новый и читаем новый элемент..."
HASH_WRITE=$( { time redis-cli HSET test:hash $NEW_KEY "$NEW_VAL" > /dev/null; } 2>&1 )
HASH_READ=$( { time redis-cli HGET test:hash $NEW_KEY > /dev/null; } 2>&1 )
echo "HASH: запись $HASH_WRITE сек, чтение $HASH_READ сек"
echo ""

#######################
# ZSET
#######################
echo "Заполняем ZSET..."
jq -c '.[]' $JSON_FILE | nl -v0 | while read i elem; do
  redis-cli ZADD test:zset $i "$elem" > /dev/null
done
echo "Готово"

echo "Вставляем новый и читаем новый элемент..."
ZSET_WRITE=$( { time redis-cli ZADD test:zset $NEW_KEY "$NEW_VAL" > /dev/null; } 2>&1 )
ZSET_READ=$( { time redis-cli ZRANGE test:zset $NEW_KEY $NEW_KEY > /dev/null; } 2>&1 )
echo "ZSET: запись $ZSET_WRITE сек, чтение $ZSET_READ сек"
echo ""