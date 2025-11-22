"""
Kafka Consumer with Avro Deserialization
Consumes order messages with retry logic, DLQ, and real-time aggregation.
Features:
- Retry logic with exponential backoff
- Dead Letter Queue (DLQ) for permanently failed messages
- Running average price calculation
- Graceful shutdown handling
- Comprehensive error handling and logging
"""

import io
import json
import time
import signal
import logging
from typing import Dict, Any
from confluent_kafka import Consumer, Producer, KafkaError, KafkaException
from fastavro import schemaless_reader, schemaless_writer

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load Avro schema
with open("order.avsc", "r") as f:
    schema = json.load(f)

# Consumer configuration
consumer_config = {
    "bootstrap.servers": "localhost:9092",
    "group.id": "order-consumer-group",
    "client.id": "order-consumer-1",
    "auto.offset.reset": "earliest",
    "enable.auto.commit": False,  # Manual commit for reliability
    "max.poll.interval.ms": 300000,
    "session.timeout.ms": 10000,
}

# Producer configuration for DLQ
producer_config = {
    "bootstrap.servers": "localhost:9092",
    "client.id": "dlq-producer",
}

# Retry configuration
MAX_RETRIES = 3
INITIAL_BACKOFF = 1.0  # seconds
BACKOFF_MULTIPLIER = 2.0

# Aggregation state
aggregation_state = {
    "total_price": 0.0,
    "count": 0,
    "running_avg": 0.0,
    "min_price": float("inf"),
    "max_price": float("-inf"),
}

# Metrics
metrics = {
    "consumed": 0,
    "processed": 0,
    "failed": 0,
    "sent_to_dlq": 0,
    "retries": 0,
}

# Graceful shutdown flag
running = True


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global running
    logger.info("Received shutdown signal, stopping consumer...")
    running = False


def deserialize_order(message_value: bytes) -> Dict[str, Any]:
    """Deserialize order from Avro bytes."""
    buffer = io.BytesIO(message_value)
    return schemaless_reader(buffer, schema)


def serialize_order(order: Dict[str, Any]) -> bytes:
    """Serialize order to Avro bytes."""
    output = io.BytesIO()
    schemaless_writer(output, schema, order)
    return output.getvalue()


def process_order(order: Dict[str, Any]) -> bool:
    """
    Process an order message.
    Simulates real-world processing with random failures.

    Args:
        order: The order to process

    Returns:
        True if processing succeeds, False otherwise

    Raises:
        Exception: If processing fails
    """
    # Simulate processing logic
    # In real world, this could be:
    # - Database insertion
    # - API calls
    # - Business logic validation

    # Simulate 15% failure rate for demonstration
    import random

    if random.random() < 0.15:
        raise Exception(f"Simulated processing failure for order {order['orderId']}")

    # Simulate processing time
    time.sleep(0.1)

    return True


def update_aggregation(order: Dict[str, Any]):
    """Update running average and other aggregations."""
    price = order["price"]

    aggregation_state["total_price"] += price
    aggregation_state["count"] += 1
    aggregation_state["running_avg"] = (
        aggregation_state["total_price"] / aggregation_state["count"]
    )
    aggregation_state["min_price"] = min(aggregation_state["min_price"], price)
    aggregation_state["max_price"] = max(aggregation_state["max_price"], price)

    logger.info(
        f"📊 Aggregation Update - "
        f"Count: {aggregation_state['count']}, "
        f"Running Avg: ${aggregation_state['running_avg']:.2f}, "
        f"Min: ${aggregation_state['min_price']:.2f}, "
        f"Max: ${aggregation_state['max_price']:.2f}"
    )


def send_to_dlq(producer: Producer, order: Dict[str, Any], error: str):
    """
    Send failed message to Dead Letter Queue.

    Args:
        producer: Kafka producer for DLQ
        order: The failed order
        error: Error description
    """
    try:
        # Add error metadata
        dlq_message = {
            "orderId": order["orderId"],
            "product": order["product"],
            "price": order["price"],
        }

        serialized = serialize_order(dlq_message)

        # Produce to DLQ with error in headers
        producer.produce(
            topic="orders-dlq",
            value=serialized,
            key=order["orderId"].encode("utf-8"),
            headers={
                "error": error.encode("utf-8"),
                "timestamp": str(int(time.time())).encode("utf-8"),
            },
        )

        producer.flush()
        metrics["sent_to_dlq"] += 1
        logger.warning(f"💀 Sent to DLQ: {order['orderId']} - Error: {error}")

    except Exception as e:
        logger.error(f"Failed to send message to DLQ: {e}")


def process_with_retry(order: Dict[str, Any], dlq_producer: Producer) -> bool:
    """
    Process order with retry logic and exponential backoff.

    Args:
        order: The order to process
        dlq_producer: Producer for sending to DLQ

    Returns:
        True if processing succeeds, False if sent to DLQ
    """
    attempt = 0
    backoff = INITIAL_BACKOFF

    while attempt < MAX_RETRIES:
        try:
            # Attempt to process the order
            process_order(order)

            # Update aggregation on success
            update_aggregation(order)
            metrics["processed"] += 1

            logger.info(
                f"✅ Successfully processed order: {order['orderId']} (${order['price']:.2f})"
            )
            return True

        except Exception as e:
            attempt += 1
            metrics["retries"] += 1

            if attempt < MAX_RETRIES:
                logger.warning(
                    f"⚠️  Processing failed for {order['orderId']} "
                    f"(attempt {attempt}/{MAX_RETRIES}): {e}. "
                    f"Retrying in {backoff:.1f}s..."
                )
                time.sleep(backoff)
                backoff *= BACKOFF_MULTIPLIER
            else:
                # Max retries reached, send to DLQ
                metrics["failed"] += 1
                error_msg = f"Max retries exceeded: {str(e)}"
                logger.error(
                    f"❌ Failed to process {order['orderId']} after {MAX_RETRIES} attempts"
                )
                send_to_dlq(dlq_producer, order, error_msg)
                return False

    return False


def consume_orders():
    """Main consumer loop with comprehensive error handling."""
    consumer = Consumer(consumer_config)
    dlq_producer = Producer(producer_config)

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        # Subscribe to orders topic
        consumer.subscribe(["orders"])
        logger.info("🚀 Consumer started, listening for orders...")
        logger.info(
            f"Configuration: Max retries={MAX_RETRIES}, Initial backoff={INITIAL_BACKOFF}s"
        )

        while running:
            # Poll for messages
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"Reached end of partition {msg.partition()}")
                else:
                    raise KafkaException(msg.error())
                continue

            try:
                # Deserialize message
                order = deserialize_order(msg.value())
                metrics["consumed"] += 1

                logger.info(f"📨 Received order: {order}")

                # Process with retry logic
                success = process_with_retry(order, dlq_producer)

                if success or not running:
                    # Commit offset only after successful processing or shutdown
                    consumer.commit(asynchronous=False)

            except Exception as e:
                # Handle deserialization or processing errors
                logger.error(f"Error deserializing/processing message: {e}")
                metrics["failed"] += 1

                # Try to send corrupted message to DLQ
                try:
                    # Create a minimal order object for DLQ with raw message data
                    corrupted_order = {
                        "orderId": "CORRUPTED-MESSAGE",
                        "product": "Unknown",
                        "price": 0.0,
                    }

                    # Send to DLQ with the actual error
                    send_to_dlq(
                        dlq_producer,
                        corrupted_order,
                        f"Deserialization/Processing failed: {str(e)}",
                    )
                except Exception as dlq_error:
                    logger.error(
                        f"Failed to send corrupted message to DLQ: {dlq_error}"
                    )

                # Still commit to avoid getting stuck on bad messages
                consumer.commit(asynchronous=False)

        logger.info("Consumer shutting down gracefully...")
        print_metrics()

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        print_metrics()

    except Exception as e:
        logger.error(f"Consumer error: {e}")
        raise

    finally:
        # Cleanup
        logger.info("Closing consumer...")
        consumer.close()
        dlq_producer.flush()
        logger.info("Consumer closed successfully")


def print_metrics():
    """Print consumer metrics and aggregation results."""
    logger.info("=" * 70)
    logger.info("CONSUMER METRICS")
    logger.info("=" * 70)
    logger.info(f"Messages consumed: {metrics['consumed']}")
    logger.info(f"Messages processed successfully: {metrics['processed']}")
    logger.info(f"Messages failed: {metrics['failed']}")
    logger.info(f"Messages sent to DLQ: {metrics['sent_to_dlq']}")
    logger.info(f"Total retries: {metrics['retries']}")
    if metrics["consumed"] > 0:
        success_rate = (metrics["processed"] / metrics["consumed"]) * 100
        logger.info(f"Success rate: {success_rate:.2f}%")
    logger.info("=" * 70)
    logger.info("AGGREGATION RESULTS")
    logger.info("=" * 70)
    logger.info(f"Total orders aggregated: {aggregation_state['count']}")
    if aggregation_state["count"] > 0:
        logger.info(f"Running average price: ${aggregation_state['running_avg']:.2f}")
        logger.info(f"Min price: ${aggregation_state['min_price']:.2f}")
        logger.info(f"Max price: ${aggregation_state['max_price']:.2f}")
        logger.info(f"Total revenue: ${aggregation_state['total_price']:.2f}")
    logger.info("=" * 70)


if __name__ == "__main__":
    consume_orders()
