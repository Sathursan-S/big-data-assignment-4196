"""
DLQ Consumer - Monitor and Process Dead Letter Queue Messages
Reads messages from the Dead Letter Queue for analysis and potential reprocessing.
"""
import io
import json
import logging
from confluent_kafka import Consumer, KafkaError
from fastavro import schemaless_reader

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load Avro schema
with open('order.avsc', 'r') as f:
    schema = json.load(f)

# Consumer configuration for DLQ
consumer_config = {
    'bootstrap.servers': 'localhost:9092',
    'group.id': 'dlq-consumer-group',
    'client.id': 'dlq-consumer',
    'auto.offset.reset': 'earliest',
    'enable.auto.commit': True,
}


def deserialize_order(message_value: bytes):
    """Deserialize order from Avro bytes."""
    buffer = io.BytesIO(message_value)
    return schemaless_reader(buffer, schema)


def monitor_dlq():
    """Monitor Dead Letter Queue for failed messages."""
    consumer = Consumer(consumer_config)
    consumer.subscribe(['orders-dlq'])
    
    logger.info("💀 DLQ Consumer started, monitoring dead letter queue...")
    
    dlq_messages = []
    
    try:
        while True:
            msg = consumer.poll(timeout=2.0)
            
            if msg is None:
                if dlq_messages:
                    logger.info(f"\nTotal DLQ messages: {len(dlq_messages)}")
                    break
                continue
            
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    logger.info(f"Reached end of DLQ partition {msg.partition()}")
                    if dlq_messages:
                        break
                    continue
                else:
                    logger.error(f"Consumer error: {msg.error()}")
                    continue
            
            try:
                # Deserialize the failed order
                order = deserialize_order(msg.value())
                
                # Extract error information from headers
                headers = dict(msg.headers()) if msg.headers() else {}
                error_msg = headers.get('error', b'Unknown error').decode('utf-8')
                timestamp = headers.get('timestamp', b'N/A').decode('utf-8')
                
                dlq_entry = {
                    'order': order,
                    'error': error_msg,
                    'timestamp': timestamp,
                    'partition': msg.partition(),
                    'offset': msg.offset()
                }
                
                dlq_messages.append(dlq_entry)
                
                logger.warning(
                    f"DLQ Message #{len(dlq_messages)}: "
                    f"OrderID={order['orderId']}, "
                    f"Product={order['product']}, "
                    f"Price=${order['price']:.2f}, "
                    f"Error='{error_msg}'"
                )
                
            except Exception as e:
                logger.error(f"Error processing DLQ message: {e}")
        
        # Print summary
        print_dlq_summary(dlq_messages)
        
    except KeyboardInterrupt:
        logger.info("DLQ monitoring interrupted by user")
        print_dlq_summary(dlq_messages)
        
    finally:
        consumer.close()
        logger.info("DLQ Consumer closed")


def print_dlq_summary(dlq_messages):
    """Print summary of DLQ messages."""
    if not dlq_messages:
        logger.info("✅ No messages in Dead Letter Queue")
        return
    
    logger.info("=" * 70)
    logger.info("DEAD LETTER QUEUE SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total failed messages: {len(dlq_messages)}")
    
    # Group by error type
    error_counts = {}
    for entry in dlq_messages:
        error = entry['error']
        error_counts[error] = error_counts.get(error, 0) + 1
    
    logger.info("\nErrors by type:")
    for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  - {error}: {count} occurrences")
    
    # Calculate total value of failed orders
    total_value = sum(entry['order']['price'] for entry in dlq_messages)
    logger.info(f"\nTotal value of failed orders: ${total_value:.2f}")
    logger.info("=" * 70)
    
    # List all failed orders
    logger.info("\nFailed Orders Details:")
    for i, entry in enumerate(dlq_messages, 1):
        logger.info(
            f"{i}. {entry['order']['orderId']} - "
            f"{entry['order']['product']} - "
            f"${entry['order']['price']:.2f}"
        )


if __name__ == '__main__':
    monitor_dlq()
