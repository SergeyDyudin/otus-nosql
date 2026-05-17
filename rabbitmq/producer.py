import json

import pika

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()

channel.exchange_declare(exchange='subscriptions', exchange_type='direct', durable=True)

channel.queue_declare(queue='subscription_created', durable=True)
channel.queue_declare(queue='subscription_cancelled', durable=True)

channel.queue_bind(exchange='subscriptions', queue='subscription_created', routing_key='subscription.create')
channel.queue_bind(exchange='subscriptions', queue='subscription_cancelled', routing_key='subscription.cancel')

message_created = {"id": 1}
routing_key_created = 'subscription.created'

channel.basic_publish(
    exchange='subscriptions',
    routing_key=routing_key_created,
    body=json.dumps(message_created),
    properties=pika.BasicProperties(delivery_mode=2)
)

print(f"Sent: {message_created} with routing key: {routing_key_created}")

message_canceled = {"id": 2}
routing_key_canceled = 'subscription.canceled'

channel.basic_publish(
    exchange='subscriptions',
    routing_key=routing_key_canceled,
    body=json.dumps(message_canceled),
    properties=pika.BasicProperties(delivery_mode=2)
)

print(f"Sent: {message_canceled} with routing key: {routing_key_canceled}")

connection.close()