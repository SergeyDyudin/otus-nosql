import pika

credentials = pika.PlainCredentials('guest', 'guest')
connection = pika.BlockingConnection(pika.ConnectionParameters('localhost', 5672, '/', credentials))
channel = connection.channel()


def callback(ch, method, properties, body):
    print(f"Received from {method.routing_key}: {body.decode()}")


channel.basic_qos(prefetch_count=1)
channel.basic_consume(queue='subscription_created', on_message_callback=callback, auto_ack=True)
channel.basic_consume(queue='subscription_canceled', on_message_callback=callback, auto_ack=True)

print('Waiting for messages...')
try:
    channel.start_consuming()
except KeyboardInterrupt:
    channel.stop_consuming()
connection.close()