from confluent_kafka import Consumer, Producer
from fastavro import schemaless_reader
import io, random

consumer = Consumer({
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'order-group'
})

producer = Producer({'bootstrap.servers': 'localhost:9092'})

schema = {...}  # same as above

consumer.subscribe(['orders'])

total = 0
count = 0

def process(order):
    # Randomly fail to simulate real world failures
    if random.random() < 0.2:
        raise Exception("Simulated failure")
    return True

while True:
    msg = consumer.poll(1.0)
    if msg is None:
        continue

    buf = io.BytesIO(msg.value())
    order = schemaless_reader(buf, schema)

    attempts = 0
    MAX_RETRIES = 3

    while True:
        try:
            process(order)

            # Update average
            global total, count
            total += order["price"]
            count += 1
            avg = total / count

            print("Order:", order, "Running Avg:", avg)
            break

        except:
            attempts += 1
            if attempts >= MAX_RETRIES:
                print("Send to DLQ:", order)
                producer.produce("orders-dlq", msg.value())
                break
            else:
                print("Retry:", attempts)

consumer.close()
