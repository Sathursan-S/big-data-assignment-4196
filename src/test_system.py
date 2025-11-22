"""
Test Suite - Comprehensive testing script for the Kafka Order Processing System
Validates all components and demonstrates system functionality
"""

import subprocess
import time
import sys
from pathlib import Path


def print_header(title):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70 + "\n")


def check_kafka_running():
    """Check if Kafka is running."""
    print_header("Checking Kafka Infrastructure")
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=kafka", "--format", "{{.Names}}"],
            capture_output=True,
            text=True,
            check=True,
        )
        if "kafka" in result.stdout:
            print("✅ Kafka is running")
            return True
        else:
            print("❌ Kafka is not running")
            print("\nStart Kafka with: docker-compose up -d")
            return False
    except Exception as e:
        print(f"❌ Error checking Kafka: {e}")
        return False


def check_dependencies():
    """Check if required Python packages are installed."""
    print_header("Checking Python Dependencies")
    try:
        import confluent_kafka

        print(f"✅ confluent-kafka {confluent_kafka.__version__}")
    except ImportError:
        print("❌ confluent-kafka not installed")
        return False

    try:
        import fastavro

        print(f"✅ fastavro {fastavro.__version__}")
    except ImportError:
        print("❌ fastavro not installed")
        return False

    return True


def check_schema_file():
    """Check if Avro schema file exists."""
    print_header("Checking Schema File")
    schema_file = Path("order.avsc")
    if schema_file.exists():
        print(f"✅ Schema file found: {schema_file.absolute()}")
        return True
    else:
        print(f"❌ Schema file not found: {schema_file.absolute()}")
        return False


def run_integration_test():
    """Run a quick integration test."""
    print_header("Running Integration Test")
    print("This will produce 20 test orders and consume them...")
    print("\nStarting consumer in background...")

    try:
        # Start consumer in background
        consumer_process = subprocess.Popen(
            [sys.executable, "consumer.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        # Wait for consumer to initialize
        time.sleep(3)

        print("Starting producer...")
        # Run producer
        producer_result = subprocess.run(
            [sys.executable, "producer.py", "20", "0.3"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        print("\nProducer output:")
        print(producer_result.stdout)

        # Wait for consumer to process
        time.sleep(5)

        # Stop consumer
        print("\nStopping consumer...")
        consumer_process.terminate()
        consumer_output, consumer_error = consumer_process.communicate(timeout=5)

        print("\nConsumer output:")
        print(consumer_output.decode("utf-8"))

        print("\n✅ Integration test completed!")
        print("\nTo view DLQ messages, run: python dlq_consumer.py")

        return True

    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        consumer_process.kill()
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        try:
            consumer_process.kill()
        except:
            pass
        return False


def main():
    """Run all tests."""
    print_header("Kafka Order Processing System - Test Suite")

    # Run checks
    checks_passed = True

    if not check_dependencies():
        checks_passed = False
        print("\n⚠️  Install dependencies with: uv sync")
        print("Or: pip install confluent-kafka fastavro")

    if not check_schema_file():
        checks_passed = False

    if not check_kafka_running():
        checks_passed = False

    if not checks_passed:
        print("\n❌ Pre-flight checks failed. Please fix the issues above.")
        return False

    print("\n✅ All pre-flight checks passed!")

    # Ask user if they want to run integration test
    print("\n" + "-" * 70)
    response = input("Run integration test? (y/N): ")

    if response.lower() == "y":
        return run_integration_test()
    else:
        print("\nSkipping integration test.")
        print("\nManual testing:")
        print("  Terminal 1: python consumer.py")
        print("  Terminal 2: python producer.py 100 0.5")
        print("  Terminal 3: python dlq_consumer.py")
        return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
