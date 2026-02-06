# Sensor Simulator Configuration
# Copy this file to config.py and update with your Solace broker details

# Solace MQTT Broker Configuration
BROKER_HOST = "mr-connection-xxxxx.messaging.solace.cloud"  # Your Solace broker hostname
BROKER_PORT = 1883  # MQTT port (1883 for non-TLS, 8883 for TLS)

# Authentication (if required by your Solace broker)
USERNAME = "solace-cloud-client"  # Your MQTT username
PASSWORD = "your-password-here"   # Your MQTT password

# Production Line Configuration
NUM_PRODUCTION_LINES = 1  # Number of production lines to simulate

# Sensor Configuration (per production line)
NUM_TEMP_SENSORS = 10       # Temperature sensors per line
NUM_VIBRATION_SENSORS = 15  # Vibration sensors per line
NUM_HYGIENE_SENSORS = 5     # Hygiene sensors per line

# Simulation Parameters
PUBLISH_INTERVAL = 5  # Time between readings in seconds
SIMULATION_DURATION = None  # Total duration in seconds (None for infinite)

# Anomaly Control
# Anomalies are now controlled dynamically via MQTT commands
# Use the API to target specific sensors across any production line
# Example sensor IDs: TEMP_001_LINE_001, VIB_003_LINE_002, HYG_002_LINE_001
ANOMALY_RATE = 0.1  # Default rate of increase for anomaly sensors per interval

# MQTT Topic Structure (Hierarchical)
# Temperature: sensors/{line_id}/temperature/{sensor_id}
# Vibration: sensors/{line_id}/vibration/{sensor_id}
# Hygiene: sensors/{line_id}/hygiene/{sensor_id}
#
# Example: sensors/LINE_001/temperature/TEMP_001
#          sensors/LINE_002/hygiene/HYG_003

# Sensor Ranges
# Temperature: 20-25°C (normal operation)
# Vibration: 0.5-2.0 mm/s (normal operation)
# Hygiene: 40-60% humidity (normal operation)
