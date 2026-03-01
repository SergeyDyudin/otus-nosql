#!/bin/bash

docker exec -i cassandra-1 cqlsh <<EOF
-- Создаем keyspace
CREATE KEYSPACE IF NOT EXISTS logs
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 2
};

USE logs;

-- Таблица 1: События (с составным partition key и clustering key)
CREATE TABLE IF NOT EXISTS events (
    service text,
    log_date text,
    event_time timestamp,
    level text,
    message text,
    PRIMARY KEY ((service, log_date), event_time)
) WITH CLUSTERING ORDER BY (event_time DESC);

-- Таблица 2: Сервисы
CREATE TABLE IF NOT EXISTS services (
    service text PRIMARY KEY,
    description text,
    owner text
);

-- Заполняем таблицы данными

-- Сервисы
INSERT INTO services (service, description, owner)
VALUES ('auth-service', 'Authentication service', 'Auth Team');

INSERT INTO services (service, description, owner)
VALUES ('payment-service', 'Payment processing', 'Payments Team');

INSERT INTO services (service, description, owner)
VALUES ('notification-service', 'Notifications', 'Notify Team');

-- Логи auth-service
INSERT INTO events (service, log_date, event_time, level, message)
VALUES ('auth-service', '2024-02-27', '2024-02-27 08:15:30', 'INFO', 'User login');

INSERT INTO events (service, log_date, event_time, level, message)
VALUES ('auth-service', '2024-02-27', '2024-02-27 10:05:15', 'ERROR', 'DB timeout');

INSERT INTO events (service, log_date, event_time, level, message)
VALUES ('auth-service', '2024-02-26', '2024-02-26 22:15:30', 'INFO', 'Password changed');

-- Логи payment-service
INSERT INTO events (service, log_date, event_time, level, message)
VALUES ('payment-service', '2024-02-27', '2024-02-27 08:20:10', 'INFO', 'Payment OK');

INSERT INTO events (service, log_date, event_time, level, message)
VALUES ('payment-service', '2024-02-27', '2024-02-27 09:45:20', 'ERROR', 'Payment failed');

-- Создаем вторичный индекс
CREATE INDEX IF NOT EXISTS idx_events_level ON logs.events (level);
EOF
