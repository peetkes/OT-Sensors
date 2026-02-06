"""
MongoDB Consumer for Sensor Data
Subscribes to all sensor MQTT topics and stores data in MongoDB for analysis
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime, timezone
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import signal
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MongoDBSensorConsumer:
    """MQTT consumer that stores sensor data in MongoDB"""

    def __init__(self, mqtt_broker_host: str, mqtt_broker_port: int = 1883,
                 mqtt_username: str = None, mqtt_password: str = None,
                 mqtt_topic_filter: str = "sensors/reading/#",
                 mongodb_uri: str = "mongodb://localhost:27017/",
                 database_name: str = "iot_sensors",
                 collection_name: str = "sensor_readings"):
        """
        Initialize the MongoDB sensor consumer

        Args:
            mqtt_broker_host: MQTT broker hostname
            mqtt_broker_port: MQTT port
            mqtt_username: MQTT username (optional)
            mqtt_password: MQTT password (optional)
            mqtt_topic_filter: MQTT topic filter to subscribe to (default "sensors/reading/#")
            mongodb_uri: MongoDB connection URI
            database_name: MongoDB database name
            collection_name: MongoDB collection name
        """
        self.mqtt_broker_host = mqtt_broker_host
        self.mqtt_broker_port = mqtt_broker_port
        self.mqtt_topic_filter = mqtt_topic_filter

        # Statistics
        self.message_count = 0
        self.insert_count = 0
        self.error_count = 0

        # MongoDB setup
        self.mongodb_uri = mongodb_uri
        self.database_name = database_name
        self.collection_name = collection_name
        self.mongo_client = None
        self.db = None
        self.collection = None

        # MQTT client setup
        self.mqtt_client = mqtt.Client(client_id="mongodb_sensor_consumer")

        if mqtt_username and mqtt_password:
            self.mqtt_client.username_pw_set(mqtt_username, mqtt_password)

        # Set MQTT callbacks
        self.mqtt_client.on_connect = self.on_mqtt_connect
        self.mqtt_client.on_message = self.on_mqtt_message
        self.mqtt_client.on_disconnect = self.on_mqtt_disconnect

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def connect_mongodb(self):
        """Connect to MongoDB and setup collection with indexes"""
        try:
            logger.info(f"Connecting to MongoDB at {self.mongodb_uri}")
            self.mongo_client = MongoClient(
                self.mongodb_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )

            # Test connection
            self.mongo_client.admin.command('ping')
            logger.info("MongoDB connection successful")

            # Get database and collection
            self.db = self.mongo_client[self.database_name]
            self.collection = self.db[self.collection_name]

            # Create indexes for efficient querying
            self._create_indexes()

        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def _create_indexes(self):
        """Create MongoDB indexes for common query patterns"""
        try:
            # Index for querying by line and timestamp
            self.collection.create_index([("line_id", ASCENDING), ("timestamp", DESCENDING)])

            # Index for querying by sensor type and timestamp
            self.collection.create_index([("sensor_type", ASCENDING), ("timestamp", DESCENDING)])

            # Index for querying anomalies
            self.collection.create_index([("status", ASCENDING), ("timestamp", DESCENDING)])

            # Index on timestamp for time-range queries
            self.collection.create_index([("timestamp", DESCENDING)])

            # Optional: TTL index to auto-delete old data after 30 days
            # Uncomment if you want automatic data expiration
            # self.collection.create_index("created_at", expireAfterSeconds=2592000)

            logger.info("MongoDB indexes created successfully")
        except Exception as e:
            logger.warning(f"Error creating indexes: {e}")

    def on_mqtt_connect(self, client, userdata, flags, rc):
        """Callback when MQTT client connects to broker"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker at {self.mqtt_broker_host}:{self.mqtt_broker_port}")
            # Subscribe to sensor topics using configured filter
            client.subscribe(self.mqtt_topic_filter, qos=1)
            logger.info(f"Subscribed to {self.mqtt_topic_filter} topic")
        else:
            logger.error(f"MQTT connection failed with code {rc}")

    def on_mqtt_disconnect(self, client, userdata, rc):
        """Callback when MQTT client disconnects"""
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection. Code: {rc}")

    def on_mqtt_message(self, client, userdata, msg):
        """Callback when MQTT message is received"""
        try:
            # Parse the JSON payload
            payload = json.loads(msg.payload.decode())

            self.message_count += 1

            # Parse topic to extract line_id
            # Flexible parsing: supports both formats
            # Format 1 (with prefix): sensors/reading/LINE_ID/TYPE/SENSOR_ID (5 parts)
            # Format 2 (without prefix): sensors/LINE_ID/TYPE/SENSOR_ID (4 parts)
            topic_parts = msg.topic.split('/')

            line_id = None
            if len(topic_parts) == 5:  # Format: sensors/reading/LINE_ID/TYPE/SENSOR_ID
                _, _, line_id, _, _ = topic_parts
            elif len(topic_parts) == 4:  # Format: sensors/LINE_ID/TYPE/SENSOR_ID
                _, line_id, _, _ = topic_parts
            else:
                logger.warning(f"Unexpected topic format: {msg.topic}")
                return

            # Extract data from payload
            sensor_id = payload.get('sensor_id')
            sensor_type = payload.get('sensor_type')
            value = payload.get('value')
            unit = payload.get('unit')
            status = payload.get('status', 'normal')
            timestamp = payload.get('timestamp')

            # Create document for MongoDB
            document = {
                "line_id": line_id,
                "sensor_id": sensor_id,
                "sensor_type": sensor_type,
                "value": value,
                "unit": unit,
                "status": status,
                "timestamp": timestamp,
                "created_at": datetime.now(timezone.utc)  # MongoDB insertion time
            }

            # Insert into MongoDB
            result = self.collection.insert_one(document)

            if result.acknowledged:
                self.insert_count += 1
                logger.info(f"Stored [{line_id}] [{sensor_type}] {sensor_id}: "
                           f"{value} {unit} [status: {status}]")
            else:
                self.error_count += 1
                logger.error(f"Failed to store document for {sensor_id}")

        except json.JSONDecodeError:
            self.error_count += 1
            logger.error(f"Failed to decode JSON from topic {msg.topic}")
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error processing message: {e}")

    def display_statistics(self):
        """Display consumer statistics"""
        print("\n" + "="*60)
        print("MONGODB CONSUMER STATISTICS")
        print("="*60)
        print(f"Total messages received: {self.message_count}")
        print(f"Successfully inserted: {self.insert_count}")
        print(f"Errors: {self.error_count}")

        if self.collection:
            try:
                total_docs = self.collection.count_documents({})
                print(f"\nTotal documents in database: {total_docs}")

                # Show breakdown by production line
                pipeline = [
                    {"$group": {"_id": "$line_id", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ]
                line_counts = list(self.collection.aggregate(pipeline))
                if line_counts:
                    print("\nDocuments per production line:")
                    for item in line_counts:
                        print(f"  {item['_id']}: {item['count']}")

                # Show breakdown by sensor type
                pipeline = [
                    {"$group": {"_id": "$sensor_type", "count": {"$sum": 1}}},
                    {"$sort": {"_id": 1}}
                ]
                type_counts = list(self.collection.aggregate(pipeline))
                if type_counts:
                    print("\nDocuments per sensor type:")
                    for item in type_counts:
                        print(f"  {item['_id']}: {item['count']}")

            except Exception as e:
                logger.error(f"Error querying statistics: {e}")

        print("="*60 + "\n")

    def signal_handler(self, sig, frame):
        """Handle shutdown signals gracefully"""
        logger.info("\nReceived shutdown signal. Stopping consumer...")
        self.display_statistics()
        self.disconnect()
        sys.exit(0)

    def connect_mqtt(self):
        """Connect to MQTT broker"""
        try:
            self.mqtt_client.connect(self.mqtt_broker_host, self.mqtt_broker_port, 60)
            logger.info("MQTT client connected")
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            raise

    def disconnect(self):
        """Disconnect from MQTT and MongoDB"""
        if self.mqtt_client:
            self.mqtt_client.disconnect()
            logger.info("Disconnected from MQTT broker")

        if self.mongo_client:
            self.mongo_client.close()
            logger.info("Disconnected from MongoDB")

    def run(self):
        """Run the consumer"""
        try:
            # Connect to MongoDB first
            self.connect_mongodb()

            # Connect to MQTT
            self.connect_mqtt()

            logger.info("Starting MongoDB sensor consumer...")
            logger.info("Press Ctrl+C to stop and show statistics")

            # Start MQTT loop
            self.mqtt_client.loop_forever()

        except KeyboardInterrupt:
            logger.info("\nStopping consumer...")
            self.display_statistics()
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            logger.info("\nDisconnecting...")
            self.disconnect()


def main():
    """Main function"""

    # Configuration - Update these for your environment
    # Or better: import from a config file
    MQTT_BROKER_HOST = "localhost"
    MQTT_BROKER_PORT = 1883
    MQTT_USERNAME = "consumer"  # Set if authentication is required
    MQTT_PASSWORD = "consumer"  # Set if authentication is required
    MQTT_TOPIC_FILTER = "sensors/reading/#"  # Topic filter to subscribe to

    # MongoDB with authentication
    # Using your existing appuser
    MONGODB_USERNAME = "sensor_subscriber"  # Your MongoDB username
    MONGODB_PASSWORD = "sensor_subscriber"  # Your MongoDB password
    # IMPORTANT: Add authSource parameter to specify where the user was created
    MONGODB_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@localhost:27017/?authSource=admin"
    # Or use this format directly:
    # MONGODB_URI = "mongodb://appuser:MyUserPassword123!@localhost:27017/?authSource=appdb"

    DATABASE_NAME = "iot_sensors"
    COLLECTION_NAME = "sensor_readings"

    # Create and run consumer
    consumer = MongoDBSensorConsumer(
        mqtt_broker_host=MQTT_BROKER_HOST,
        mqtt_broker_port=MQTT_BROKER_PORT,
        mqtt_username=MQTT_USERNAME,
        mqtt_password=MQTT_PASSWORD,
        mqtt_topic_filter=MQTT_TOPIC_FILTER,
        mongodb_uri=MONGODB_URI,
        database_name=DATABASE_NAME,
        collection_name=COLLECTION_NAME
    )

    consumer.run()


if __name__ == "__main__":
    main()
