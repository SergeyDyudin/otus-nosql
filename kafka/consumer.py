import asyncio
import json
from aiokafka import AIOKafkaConsumer

async def read_messages():
    consumer = AIOKafkaConsumer(
        'test-topic',
        bootstrap_servers='localhost:9092',
        auto_offset_reset='earliest',
        value_deserializer=lambda v: json.loads(v.decode())
    )
    await consumer.start()
    try:
        async for msg in consumer:
            print(f'Received: {msg.value}')
    finally:
        await consumer.stop()

asyncio.run(read_messages())
