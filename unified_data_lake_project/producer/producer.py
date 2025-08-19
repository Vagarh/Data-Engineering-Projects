
import time
import json
import requests
from kafka import KafkaProducer

# --- Kafka Producer Configuration ---
def create_producer():
    """Creates and returns a Kafka producer."""
    try:
        # Note: bootstrap_servers points to the Kafka service in docker-compose
        producer = KafkaProducer(
            bootstrap_servers=['localhost:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        print("Kafka Producer connected successfully.")
        return producer
    except Exception as e:
        print(f"Error connecting to Kafka: {e}")
        # Exit if we can't connect to Kafka, as it's essential for the script
        exit()

# --- API Data Fetching ---
def fetch_crypto_data():
    """Fetches cryptocurrency data from the CoinGecko API."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,dogecoin&vs_currencies=usd"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raises an HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        # Add a timestamp to the data
        data['timestamp'] = time.time()
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    KAFKA_TOPIC = "crypto_prices"
    producer = create_producer()

    print(f"Starting to send data to Kafka topic: {KAFKA_TOPIC}")
    while True:
        crypto_data = fetch_crypto_data()
        if crypto_data:
            print(f"Sending data: {crypto_data}")
            producer.send(KAFKA_TOPIC, crypto_data)
            producer.flush() # Ensure all messages are sent
        
        # Wait for 5 seconds before fetching data again
        time.sleep(5)
