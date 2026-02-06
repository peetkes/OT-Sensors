"""
MQTT Subscriber for testing the sensor simulator
Subscribes to all sensor topics and displays received messages
"""

import paho.mqtt.client as mqtt
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SensorSubscriber:
    """MQTT subscriber for sensor data"""
    
    def __init__(self, broker_host: str, broker_port: int = 1883,
                 username: str = None, password: str = None):
        """
        Initialize the subscriber
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT port
            username: MQTT username (optional)
            password: MQTT password (optional)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # Statistics
        self.message_count = 0
        self.temp_readings = {}
        self.vib_readings = {}
        self.hygiene_readings = {}
        self.production_lines = set()
        
        # Create MQTT client
        self.client = mqtt.Client(client_id="sensor_subscriber")
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
    
    def on_connect(self, client, userdata, flags, rc):
        """Callback when connected to broker"""
        if rc == 0:
            logger.info(f"Connected to broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to all sensor topics
            client.subscribe("sensors/#", qos=1)
            logger.info("Subscribed to sensors/#")
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from broker"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Callback when message is received"""
        try:
            # Parse the JSON payload
            payload = json.loads(msg.payload.decode())

            self.message_count += 1

            # Extract data
            sensor_id = payload.get('sensor_id')
            sensor_type = payload.get('sensor_type')
            value = payload.get('value')
            unit = payload.get('unit')
            status = payload.get('status', 'normal')
            timestamp = payload.get('timestamp')

            # Parse topic to extract production line
            # New format: sensors/LINE_ID/TYPE/SENSOR_ID
            # Legacy format: sensors/TYPE/SENSOR_ID
            topic_parts = msg.topic.split('/')
            if len(topic_parts) == 4:  # New hierarchical format
                _, line_id, _, _ = topic_parts
                self.production_lines.add(line_id)
            elif len(topic_parts) == 3:  # Legacy format (backward compatible)
                line_id = "LEGACY"
            else:
                line_id = "UNKNOWN"

            # Store latest reading with line context
            reading_key = f"{line_id}_{sensor_id}"
            if sensor_type == 'temperature':
                self.temp_readings[reading_key] = value
            elif sensor_type == 'vibration':
                self.vib_readings[reading_key] = value
            elif sensor_type == 'hygiene':
                self.hygiene_readings[reading_key] = value

            # Display the reading
            status_symbol = "⚠️" if status == "warning" else "✓"
            logger.info(f"{status_symbol} [{line_id}] [{sensor_type.upper()}] {sensor_id}: "
                       f"{value} {unit} (status: {status})")

            # Log anomaly warnings
            if status == "warning":
                logger.warning(f"ANOMALY DETECTED on {line_id}: {sensor_id} reading {value} {unit}")

        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def display_statistics(self):
        """Display current statistics"""
        print("\n" + "="*60)
        print("SENSOR STATISTICS")
        print("="*60)
        print(f"Total messages received: {self.message_count}")
        print(f"Production lines detected: {len(self.production_lines)}")
        print(f"\nTemperature Sensors: {len(self.temp_readings)}")
        print(f"Vibration Sensors: {len(self.vib_readings)}")
        print(f"Hygiene Sensors: {len(self.hygiene_readings)}")

        if self.temp_readings:
            print("\nLatest Temperature Readings:")
            for sensor_id in sorted(self.temp_readings.keys()):
                value = self.temp_readings[sensor_id]
                print(f"  {sensor_id}: {value}°C")

        if self.vib_readings:
            print("\nLatest Vibration Readings:")
            for sensor_id in sorted(self.vib_readings.keys()):
                value = self.vib_readings[sensor_id]
                print(f"  {sensor_id}: {value} mm/s")

        if self.hygiene_readings:
            print("\nLatest Hygiene Readings:")
            for sensor_id in sorted(self.hygiene_readings.keys()):
                value = self.hygiene_readings[sensor_id]
                print(f"  {sensor_id}: {value}%")

        print("="*60 + "\n")
    
    def run(self):
        """Connect and start listening for messages"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            logger.info("Starting MQTT subscriber...")
            logger.info("Press Ctrl+C to stop and show statistics")
            self.client.loop_forever()
        except KeyboardInterrupt:
            logger.info("\nStopping subscriber...")
            self.display_statistics()
        except Exception as e:
            logger.error(f"Error: {e}")
        finally:
            self.client.disconnect()


def main():
    """Main function"""
    
    # Configuration - Update these for your Solace broker
    BROKER_HOST = "localhost"
    BROKER_PORT = 1883
    USERNAME = None  # Set if authentication is required
    PASSWORD = None  # Set if authentication is required
    
    # Create and run subscriber
    subscriber = SensorSubscriber(
        broker_host=BROKER_HOST,
        broker_port=BROKER_PORT,
        username=USERNAME,
        password=PASSWORD
    )
    
    subscriber.run()


if __name__ == "__main__":
    main()
