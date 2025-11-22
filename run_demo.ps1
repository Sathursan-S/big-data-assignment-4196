# Kafka Order Processing System - Demo Script
# Run this script to start a complete demonstration

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Kafka Order Processing System - Live Demo" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

# Check if Kafka is running
Write-Host "Checking Kafka infrastructure..." -ForegroundColor Yellow
$kafkaRunning = docker ps --filter "name=kafka" --format "{{.Names}}" | Select-String "kafka"

if (-not $kafkaRunning) {
    Write-Host "❌ Kafka is not running!" -ForegroundColor Red
    Write-Host "`nStarting Kafka with docker-compose..." -ForegroundColor Yellow
    docker-compose up -d
    Write-Host "`nWaiting for Kafka to initialize (30 seconds)..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30
}
else {
    Write-Host "✅ Kafka is running" -ForegroundColor Green
}

# Check Python dependencies
Write-Host "`nChecking Python dependencies..." -ForegroundColor Yellow
try {
    uv python -c "import confluent_kafka, fastavro" 2>$null
    Write-Host "✅ Dependencies installed" -ForegroundColor Green
}
catch {
    Write-Host "❌ Missing dependencies!" -ForegroundColor Red
    Write-Host "Installing with uv..." -ForegroundColor Yellow
    uv sync
}

Write-Host "`n============================================================" -ForegroundColor Cyan
Write-Host "  Starting Demo - Opening 3 terminals" -ForegroundColor Cyan
Write-Host "============================================================`n" -ForegroundColor Cyan

Write-Host "Terminal 1: Consumer (with retry logic and DLQ)" -ForegroundColor Green
Write-Host "Terminal 2: Producer (generating 50 orders)" -ForegroundColor Green
Write-Host "Terminal 3: DLQ Monitor (tracking failed messages)" -ForegroundColor Green

# Start Consumer in new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Write-Host 'CONSUMER - Processing Orders with Retry Logic' -ForegroundColor Green; uv run consumer.py"

# Wait a bit for consumer to start
Start-Sleep -Seconds 2

# Start Producer in new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Write-Host 'PRODUCER - Generating Order Messages' -ForegroundColor Yellow; uv run producer.py 50 0.5"

# Wait for some messages to be produced
Start-Sleep -Seconds 5

# Start DLQ Monitor in new terminal
Start-Process pwsh -ArgumentList "-NoExit", "-Command", "Write-Host 'DLQ MONITOR - Tracking Failed Messages' -ForegroundColor Red; Start-Sleep -Seconds 25; uv run dlq_consumer.py"

Write-Host "`n✅ Demo started successfully!" -ForegroundColor Green
Write-Host "`nWatch the terminals to see:" -ForegroundColor Cyan
Write-Host "  • Producer sending messages with delivery confirmations" -ForegroundColor White
Write-Host "  • Consumer processing with retry logic and running average" -ForegroundColor White
Write-Host "  • Failed messages being sent to Dead Letter Queue" -ForegroundColor White
Write-Host "  • DLQ monitor showing failed message summary" -ForegroundColor White

Write-Host "`n============================================================`n" -ForegroundColor Cyan
