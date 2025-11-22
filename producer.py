"""
Kafka Producer with Avro Serialization
Produces order messages with proper error handling, delivery callbacks, and monitoring.
"""

import io
import json
import random
import time
import logging
from typing import Dict, Any
from confluent_kafka import Producer
from fastavro import schemaless_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load Avro schema
with open("order.avsc", "r") as f:
    schema = json.load(f)

# Producer configuration
producer_config = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "order-producer",
    "acks": "all",  # Wait for all replicas
    "retries": 3,
    "max.in.flight.requests.per.connection": 5,
    "compression.type": "snappy",
    "linger.ms": 10,  # Batch messages for 10ms
    "batch.size": 16384,
}

# Metrics tracking
metrics = {"produced": 0, "failed": 0, "total_latency": 0.0}


def delivery_callback(err, msg):
    """
    Callback function invoked for each message produced.
    Handles delivery confirmation and errors.
    """
    if err:
        metrics["failed"] += 1
        logger.error(f"Message delivery failed: {err}")
    else:
        metrics["produced"] += 1
        latency = time.time() - msg.timestamp()[1] / 1000.0
        metrics["total_latency"] += latency
        logger.info(
            f"Message delivered to {msg.topic()} [{msg.partition()}] "
            f"at offset {msg.offset()} (latency: {latency*1000:.2f}ms)"
        )


def serialize_order(order: Dict[str, Any]) -> bytes:
    """Serialize order using Avro schema."""
    # Randomly corrupt messages to simulate DLQ scenarios
    if random.random() < 0.15:  # 15% chance of corruption
        logger.warning(
            f"🔥 Intentionally corrupting message for order {order['orderId']} to simulate DLQ"
        )
        # Corrupt the data in various ways
        corruption_type = random.choice(
            ["invalid_schema", "truncated_data", "invalid_utf8", "wrong_data_type"]
        )

        if corruption_type == "invalid_schema":
            # Create data that doesn't match the schema
            corrupted_order = {
                "orderId": order["orderId"],
                "product": order["product"],
                "price": "not_a_number",  # Invalid price type
                "extra_field": "should_not_be_here",  # Extra field
            }
            output = io.BytesIO()
            schemaless_writer(output, schema, corrupted_order)
            return output.getvalue()

        elif corruption_type == "truncated_data":
            # Serialize normally then truncate
            output = io.BytesIO()
            schemaless_writer(output, schema, order)
            data = output.getvalue()
            # Truncate to random length
            truncated_length = random.randint(1, len(data) - 1)
            return data[:truncated_length]

        elif corruption_type == "invalid_utf8":
            # Corrupt UTF-8 encoding
            output = io.BytesIO()
            schemaless_writer(output, schema, order)
            data = output.getvalue()
            # Flip some bytes to create invalid UTF-8
            if len(data) > 10:
                corrupted_data = bytearray(data)
                for i in random.sample(range(len(data)), min(5, len(data))):
                    corrupted_data[i] = (corrupted_data[i] + 128) % 256
                return bytes(corrupted_data)
            return data

        else:  # wrong_data_type
            # Put wrong data type in the stream
            return b"This is not Avro data at all!"

    # Normal serialization
    output = io.BytesIO()
    schemaless_writer(output, schema, order)
    return output.getvalue()


def generate_order(order_id: int) -> Dict[str, Any]:
    """Generate a random order."""
    products = [
        "Laptop",
        "Smartphone",
        "Tablet",
        "Headphones",
        "Monitor",
        "Keyboard",
        "Mouse",
        "Camera",
        "Speaker",
        "Charger",
    ]

    return {
        "orderId": f"ORD-{order_id:05d}",
        "product": random.choice(products),
        "price": round(random.uniform(10.0, 999.99), 2),
    }


def produce_orders(count: int = 100, delay: float = 0.5):
    """
    Produce order messages to Kafka.

    Args:
        count: Number of orders to produce
        delay: Delay between messages in seconds
    """
    producer = Producer(producer_config)
    logger.info(f"Starting to produce {count} orders...")

    try:
        for i in range(1, count + 1):
            # Generate order
            order = generate_order(i)

            try:
                # Serialize order
                serialized_order = serialize_order(order)

                # Produce message with callback
                producer.produce(
                    topic="orders",
                    value=serialized_order,
                    key=order["orderId"].encode("utf-8"),
                    callback=delivery_callback,
                )

                logger.info(f"Produced order: {order}")

                # Trigger callbacks
                producer.poll(0)

                # Simulate real-time production with delay
                time.sleep(delay)

            except BufferError:
                # Queue is full, wait for messages to be delivered
                logger.warning("Producer queue full, waiting...")
                producer.poll(1)

            except Exception as e:
                logger.error(f"Error producing message: {e}")
                metrics["failed"] += 1

        # Wait for all messages to be delivered
        logger.info("Flushing remaining messages...")
        producer.flush(timeout=30)

        # Print metrics
        print_metrics()

    except KeyboardInterrupt:
        logger.info("Interrupted by user, flushing messages...")
        producer.flush(timeout=10)
        print_metrics()

    except Exception as e:
        logger.error(f"Producer error: {e}")
        raise
    finally:
        producer.flush(timeout=10)


def print_metrics():
    """Print production metrics."""
    logger.info("=" * 60)
    logger.info("PRODUCER METRICS")
    logger.info("=" * 60)
    logger.info(f"Messages produced: {metrics['produced']}")
    logger.info(f"Messages failed: {metrics['failed']}")
    if metrics["produced"] > 0:
        avg_latency = metrics["total_latency"] / metrics["produced"]
        logger.info(f"Average latency: {avg_latency*1000:.2f}ms")
    logger.info("=" * 60)


if __name__ == "__main__":
    import sys

    # Allow customizing number of messages
    num_orders = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    message_delay = float(sys.argv[2]) if len(sys.argv) > 2 else 0.5

    produce_orders(count=num_orders, delay=message_delay)
