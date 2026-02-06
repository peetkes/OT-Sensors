# MongoDB Consumer Configuration
# Copy this file to mongodb_config.py and update with your settings

# MQTT Broker Configuration
MQTT_BROKER_HOST = "localhost"  # Change to your MQTT broker hostname
MQTT_BROKER_PORT = 1883         # MQTT port (default 1883)
MQTT_USERNAME = None            # MQTT username (None if no auth required)
MQTT_PASSWORD = None            # MQTT password (None if no auth required)

# MQTT Topic Filter
# Subscribe to sensor readings with specific topic pattern
MQTT_TOPIC_FILTER = "sensors/reading/#"  # Default: sensors/reading/# (matches sensors/reading/LINE_001/temperature/TEMP_001)
# Or use: "sensors/#" to match sensors/LINE_001/temperature/TEMP_001

# MongoDB Configuration
# Local MongoDB without authentication (testing only)
# MONGODB_URI = "mongodb://localhost:27017/"

# Local MongoDB with authentication (recommended)
# IMPORTANT: Add ?authSource=admin if your user was created in the admin database
MONGODB_URI = "mongodb://appuser:password@localhost:27017/?authSource=admin"

# Or if user was created in a specific database
# MONGODB_URI = "mongodb://appuser:password@localhost:27017/?authSource=iot_sensors"

# Or MongoDB Atlas (Cloud)
# MONGODB_URI = "mongodb+srv://username:password@cluster.mongodb.net/"

# Database and Collection Settings
DATABASE_NAME = "iot_sensors"        # MongoDB database name
COLLECTION_NAME = "sensor_readings"  # Collection name for sensor data

# Data Retention (Optional)
# To enable automatic deletion of old data, uncomment the TTL index in mongodb_consumer.py
# Default: 30 days (2592000 seconds)
DATA_RETENTION_DAYS = 30

# Usage Example:
#
# In mongodb_consumer.py, replace the hardcoded values with:
# from mongodb_config import *
#
# consumer = MongoDBSensorConsumer(
#     mqtt_broker_host=MQTT_BROKER_HOST,
#     mqtt_broker_port=MQTT_BROKER_PORT,
#     mqtt_username=MQTT_USERNAME,
#     mqtt_password=MQTT_PASSWORD,
#     mqtt_topic_filter=MQTT_TOPIC_FILTER,
#     mongodb_uri=MONGODB_URI,
#     database_name=DATABASE_NAME,
#     collection_name=COLLECTION_NAME
# )
