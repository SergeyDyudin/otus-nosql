import asyncio
import json
from aiokafka import AIOKafkaProducer

async def send_messages():
    producer = AIOKafkaProducer(
        bootstrap_servers='localhost:9092',
        value_serializer=lambda v: json.dumps(v).encode()
    )
    await producer.start()
    try:
        for i in range(1, 6):
            await producer.send('test-topic', {'id': i, 'msg': f'message {i}'})
            print(f'Sent: message {i}')
    finally:
        await producer.stop()

asyncio.run(send_messages())
