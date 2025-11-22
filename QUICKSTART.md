# Quick Start Guide

## 🚀 Run the Complete Demo (Easiest Method)

```powershell
# This will start everything automatically in separate terminals
.\run_demo.ps1
```

The script will:
1. Check and start Kafka if needed
2. Verify dependencies
3. Open 3 terminals:
   - **Terminal 1**: Consumer with retry logic
   - **Terminal 2**: Producer generating 50 orders
   - **Terminal 3**: DLQ monitor showing failed messages

## 📝 Manual Setup (Step by Step)

### 1. Start Kafka
```powershell
docker-compose up -d
```

### 2. Access Kafka UI (Optional)

Once services are running, access the web interface at:

- **Kafka UI**: [http://localhost:8080](http://localhost:8080)

Use this to monitor topics, consumer groups, and browse messages in real-time.

### 3. Install Dependencies

```powershell
# Using uv (recommended)
uv sync

# OR using pip
pip install -r requirements.txt
```

### 3. Run Components

**Terminal 1 - Consumer:**

```powershell
python consumer.py
```

**Terminal 2 - Producer:**

```powershell
python producer.py 100 0.5
```

**Terminal 3 - DLQ Monitor:**

```powershell
python dlq_consumer.py
```

## ✅ Verify Installation

```powershell
python test_system.py
```

## 🛑 Stop Everything

```powershell
# Stop Kafka
docker-compose down

# Stop consumers/producers: Ctrl+C in each terminal
```

## 📊 What to Observe

1. **Producer**: Messages being sent with delivery confirmations
2. **Consumer**:
   - Successful processing with running average
   - Retry attempts with exponential backoff
   - Failed messages sent to DLQ
3. **DLQ Monitor**: Summary of all failed messages with error details

## 🎯 Success Criteria

- ✅ Messages produced with Avro serialization
- ✅ Running average calculated in real-time
- ✅ Failed messages retried 3 times with backoff
- ✅ Permanently failed messages in DLQ
- ✅ Metrics showing success rate and aggregations
