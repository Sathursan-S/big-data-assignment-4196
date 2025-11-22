# Kafka Order Processing System with Avro Serialization

A production-grade Kafka-based system demonstrating real-time order message processing with Avro serialization, comprehensive error handling, retry logic, and Dead Letter Queue (DLQ) implementation.

##  Features

### Core Requirements 
- **Avro Serialization**: All messages use Apache Avro schema for efficient serialization
- **Real-time Aggregation**: Running average of order prices with min/max tracking
- **Retry Logic**: Exponential backoff retry mechanism for transient failures
- **Dead Letter Queue (DLQ)**: Permanent failure handling with detailed error tracking
- **Production-Ready**: Comprehensive logging, metrics, and graceful shutdown

### Advanced Features 
- **Delivery Callbacks**: Confirmation and latency tracking for produced messages
- **Message Batching**: Optimized throughput with configurable batch sizes
- **Graceful Shutdown**: Proper cleanup and metrics reporting on exit
- **DLQ Monitoring**: Separate consumer for analyzing failed messages
- **Manual Offset Management**: Ensures exactly-once processing semantics
- **Comprehensive Metrics**: Success rates, latency, and aggregation statistics

##  Prerequisites

- **Python**: 3.12+
- **Docker**: For running Kafka and Zookeeper
- **uv** (optional): For fast dependency management

##  Quick Start

### 2. Start Kafka Infrastructure

```powershell
# Start Kafka, Zookeeper, and Kafka UI
docker-compose up -d

# Verify services are running
docker-compose ps
```

### 3. Access Kafka UI

Once all services are running, you can access Kafka UI at:
- **Kafka UI**: http://localhost:8080

Kafka UI provides a web interface to:
- View topics and messages
- Monitor consumer groups
- Browse schemas (if Schema Registry is added)
- Manage Kafka cluster

### 2. Install Dependencies

```powershell
# Using uv (recommended)
uv sync

# Or using pip
pip install confluent-kafka fastavro
```

### 3. Run the System

**Terminal 1 - Start Consumer:**
```powershell
python consumer.py
```

**Terminal 2 - Start Producer:**
```powershell
# Produce 100 orders with 0.5s delay between messages
python producer.py 100 0.5

# Or with custom parameters
python producer.py <number_of_orders> <delay_in_seconds>
```

**Terminal 3 - Monitor DLQ (Optional):**
```powershell
python dlq_consumer.py
```

##  Project Structure

```
big-data-assignment-4196/
├── producer.py           # Kafka producer with Avro serialization
├── consumer.py           # Kafka consumer with retry logic & DLQ
├── dlq_consumer.py       # Dead Letter Queue monitor
├── order.avsc            # Avro schema definition
├── docker-compose.yml    # Kafka infrastructure setup
├── pyproject.toml        # Python project configuration
├── .gitignore           # Git ignore patterns
└── README.md            # This file
```

## 🔧 Architecture

### Message Flow

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│  Producer   │ ──────> │    Kafka    │ ──────> │  Consumer   │
│             │         │   Topic:    │         │             │
│ - Generate  │         │   orders    │         │ - Retry     │
│ - Serialize │         │             │         │ - Aggregate │
│ - Deliver   │         │             │         │ - Process   │
└─────────────┘         └─────────────┘         └─────────────┘
                                                       │
                                                       │ Failed after
                                                       │ max retries
                                                       ▼
                              ┌─────────────────────────────────┐
                              │  Dead Letter Queue (orders-dlq) │
                              │                                 │
                              │  - Error metadata               │
                              │  - Timestamp tracking           │
                              │  - Manual review/reprocessing   │
                              └─────────────────────────────────┘
```

### Retry Strategy

1. **Attempt 1**: Immediate processing
2. **Attempt 2**: Wait 1 second (exponential backoff)
3. **Attempt 3**: Wait 2 seconds
4. **Failed**: Send to DLQ with error details

##  Avro Schema

```json
{
  "type": "record",
  "name": "Order",
  "fields": [
    {"name": "orderId", "type": "string"},
    {"name": "product", "type": "string"},
    {"name": "price", "type": "float"}
  ]
}
```

## 💡 Key Implementation Details

### Producer Features
- **Delivery Callbacks**: Track message delivery success/failure
- **Compression**: Snappy compression for reduced network usage
- **Batching**: Configurable batch size and linger time
- **Reliability**: `acks=all` for full replica acknowledgment
- **Metrics**: Production count, failure count, average latency

### Consumer Features
- **Manual Offset Commit**: Ensures at-least-once delivery
- **Exponential Backoff**: `1s → 2s → 4s` retry intervals
- **Graceful Shutdown**: Signal handling for clean termination
- **Real-time Aggregation**: 
  - Running average price
  - Min/Max price tracking
  - Total revenue calculation
  - Order count
- **DLQ Integration**: Failed messages preserved with error context

### Error Handling
- **Transient Failures**: Automatically retried with backoff
- **Permanent Failures**: Sent to DLQ with error metadata
- **Bad Messages**: Logged and skipped to avoid blocking
- **Network Issues**: Automatic reconnection and retry

##  Sample Output

### Producer Output
```
INFO - Produced order: {'orderId': 'ORD-00001', 'product': 'Laptop', 'price': 799.99}
INFO - Message delivered to orders [0] at offset 0 (latency: 15.23ms)
INFO - Produced order: {'orderId': 'ORD-00002', 'product': 'Mouse', 'price': 29.99}
INFO - Message delivered to orders [0] at offset 1 (latency: 12.45ms)
...
INFO - ============================================================
INFO - PRODUCER METRICS
INFO - ============================================================
INFO - Messages produced: 100
INFO - Messages failed: 0
INFO - Average latency: 14.32ms
INFO - ============================================================
```

### Consumer Output
```
INFO - 🚀 Consumer started, listening for orders...
INFO - 📨 Received order: {'orderId': 'ORD-00001', 'product': 'Laptop', 'price': 799.99}
INFO - ✅ Successfully processed order: ORD-00001 ($799.99)
INFO - 📊 Aggregation Update - Count: 1, Running Avg: $799.99, Min: $799.99, Max: $799.99
INFO - 📨 Received order: {'orderId': 'ORD-00002', 'product': 'Mouse', 'price': 29.99}
WARNING - ⚠️  Processing failed for ORD-00002 (attempt 1/3): Simulated processing failure. Retrying in 1.0s...
INFO - ✅ Successfully processed order: ORD-00002 ($29.99)
INFO - 📊 Aggregation Update - Count: 2, Running Avg: $414.99, Min: $29.99, Max: $799.99
...
INFO - ======================================================================
INFO - CONSUMER METRICS
INFO - ======================================================================
INFO - Messages consumed: 100
INFO - Messages processed successfully: 87
INFO - Messages failed: 13
INFO - Messages sent to DLQ: 13
INFO - Total retries: 26
INFO - Success rate: 87.00%
INFO - ======================================================================
INFO - AGGREGATION RESULTS
INFO - ======================================================================
INFO - Total orders aggregated: 87
INFO - Running average price: $312.45
INFO - Min price: $12.99
INFO - Max price: $989.99
INFO - Total revenue: $27,183.15
INFO - ======================================================================
```

### DLQ Monitor Output
```
INFO - 💀 DLQ Consumer started, monitoring dead letter queue...
WARNING - DLQ Message #1: OrderID=ORD-00005, Product=Tablet, Price=$499.99, Error='Max retries exceeded'
WARNING - DLQ Message #2: OrderID=ORD-00023, Product=Camera, Price=$1299.00, Error='Max retries exceeded'
...
INFO - ======================================================================
INFO - DEAD LETTER QUEUE SUMMARY
INFO - ======================================================================
INFO - Total failed messages: 13
INFO - 
INFO - Errors by type:
INFO -   - Max retries exceeded: Simulated processing failure: 13 occurrences
INFO - 
INFO - Total value of failed orders: $4,156.84
INFO - ======================================================================
```

## 🧪 Testing the System

### Test Scenario 1: Normal Operation
```powershell
# Terminal 1
python consumer.py

# Terminal 2
python producer.py 20 0.5
```
**Expected**: Most messages processed successfully, some retries, few DLQ entries

### Test Scenario 2: High Volume
```powershell
# Terminal 1
python consumer.py

# Terminal 2
python producer.py 1000 0.1
```
**Expected**: Demonstrates batching and throughput optimization

### Test Scenario 3: DLQ Analysis
```powershell
# After running producer/consumer
python dlq_consumer.py
```
**Expected**: Shows all failed messages with error details

##  Configuration

### Producer Configuration
- `bootstrap.servers`: Kafka broker address
- `acks`: Acknowledgment level (`all` for maximum durability)
- `retries`: Number of retry attempts (default: 3)
- `compression.type`: Compression algorithm (snappy)
- `batch.size`: Batch size in bytes (16384)
- `linger.ms`: Batching delay in milliseconds (10)

### Consumer Configuration
- `group.id`: Consumer group identifier
- `auto.offset.reset`: Offset reset policy (`earliest`)
- `enable.auto.commit`: Manual commit (False)
- `max.poll.interval.ms`: Maximum poll interval (300000)
- `session.timeout.ms`: Session timeout (10000)

### Retry Configuration
- `MAX_RETRIES`: 3 attempts
- `INITIAL_BACKOFF`: 1.0 second
- `BACKOFF_MULTIPLIER`: 2.0x (exponential)

##  Troubleshooting

### Kafka Not Starting
```powershell
# Check if ports are in use
docker-compose down
docker-compose up -d
```

### Consumer Not Receiving Messages
```powershell
# Check topic exists
docker exec -it <kafka-container> kafka-topics --list --bootstrap-server localhost:9092

# Create topic manually if needed
docker exec -it <kafka-container> kafka-topics --create --topic orders --bootstrap-server localhost:9092 --partitions 1 --replication-factor 1
```

### Schema Errors
- Ensure `order.avsc` file exists in the project root
- Verify schema matches in producer and consumer

## 📚 Technologies Used

- **Apache Kafka**: Distributed streaming platform
- **Apache Avro**: Data serialization framework
- **Python 3.12**: Programming language
- **confluent-kafka-python**: Kafka client library
- **fastavro**: Fast Avro implementation
- **Docker**: Container platform

## 🎓 Learning Outcomes

This project demonstrates:
1. **Kafka Fundamentals**: Topics, producers, consumers, partitions
2. **Avro Serialization**: Schema-based message encoding
3. **Error Handling**: Retry logic, backoff strategies, DLQ patterns
4. **Real-time Processing**: Stream aggregation and analytics
5. **Production Best Practices**: Logging, metrics, graceful shutdown
6. **Distributed Systems**: Message delivery guarantees, fault tolerance

## 📝 Assignment Compliance

✅ **Kafka-based system** with producer and consumer  
✅ **Avro serialization** for all messages  
✅ **Real-time aggregation** (running average of prices)  
✅ **Retry logic** with exponential backoff  
✅ **Dead Letter Queue** for permanent failures  
✅ **Live demonstration** ready  
✅ **Git repository** with comprehensive documentation  
✅ **Independent implementation** with Python  

## 🚦 Next Steps

1. **Run the system**: Follow Quick Start guide
2. **Observe metrics**: Monitor logs for insights
3. **Test failure scenarios**: See retry and DLQ in action
4. **Analyze DLQ**: Use dlq_consumer.py to inspect failures
5. **Experiment**: Adjust configuration parameters
6. **Document**: Take screenshots for submission

## 📧 Author

Big Data Assignment - Kafka Order Processing System

---

**Built with ❤️ for Big Data class**
