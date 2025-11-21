from confluent_kafka import Producer
from fastavro import schemaless_writer
import io, json, random

schema = {
    "type": "record",
    "name": "Order",
    "fields": [
        {"name": "orderId", "type": "string"},
        {"name": "product", "type": "string"},
        {"name": "price", "type": "float"}
    ]
}

p = Producer({'bootstrap.servers': 'localhost:9092'})

for i in range(1, 20):
    order = {
        "orderId": str(i),
        "product": "Item" + str(i),
        "price": round(random.uniform(10, 500), 2)
    }

    out = io.BytesIO()
    schemaless_writer(out, schema, order)

    p.produce('orders', out.getvalue())
    print("Produced:", order)

p.flush()
