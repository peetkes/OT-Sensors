"""
Sensor Simulator for Temperature, Vibration, and Hygiene Monitoring
Publishes sensor readings to Solace broker via MQTT
Supports multiple production lines with configurable sensor counts
"""

import paho.mqtt.client as mqtt
import json
import time
import random
import argparse
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Dict, Set
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    """Data class for sensor readings"""
    sensor_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: str
    status: str = "normal"


class SensorSimulator:
    """Simulates temperature, vibration, and hygiene sensors across multiple production lines"""

    def __init__(self, broker_host: str, broker_port: int = 1883,
                 username: str = None, password: str = None,
                 control_topic: str = "sensors/control/anomaly",
                 reading_topic_prefix: str = "sensors/reading",
                 num_production_lines: int = 1,
                 num_temp_sensors: int = 10,
                 num_pressure_sensors: int = 10,
                 num_vibration_sensors: int = 15,
                 num_hygiene_sensors: int = 5):
        """
        Initialize the sensor simulator

        Args:
            broker_host: Solace broker hostname
            broker_port: MQTT port (default 1883)
            username: MQTT username
            password: MQTT password
            control_topic: MQTT topic for control commands
            reading_topic_prefix: MQTT topic prefix for sensor readings (default "sensors/reading")
            num_production_lines: Number of production lines (default 1)
            num_temp_sensors: Temperature sensors per line (default 10)
            num_pressure_sensors: Pressure sensors per line (default 10)
            num_vibration_sensors: Vibration sensors per line (default 15)
            num_hygiene_sensors: Hygiene sensors per line (default 5)
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.username = username
        self.password = password
        self.control_topic = control_topic
        self.reading_topic_prefix = reading_topic_prefix

        # Initialize MQTT client
        self.client = mqtt.Client(client_id="sensor_simulator")

        if username and password:
            self.client.username_pw_set(username, password)

        # Set callbacks
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_publish = self.on_publish
        self.client.on_message = self.on_message

        # Production line and sensor configurations
        self.num_production_lines = num_production_lines
        self.num_temp_sensors = num_temp_sensors
        self.num_pressure_sensors = num_pressure_sensors
        self.num_vibration_sensors = num_vibration_sensors
        self.num_hygiene_sensors = num_hygiene_sensors

        # Production line tracking
        self.production_lines = [f"LINE_{i+1:03d}" for i in range(num_production_lines)]

        # Sensor structure: {line_id: {sensor_type: [sensor_ids]}}
        self.sensors: Dict[str, Dict[str, list]] = {}

        # Base values for all sensors (unified dictionary)
        self.base_values: Dict[str, float] = {}
        self.base_variation: Dict[str, float] = {}
        self.sensor_units: Dict[str, str] = {}

        # Per-sensor anomaly tracking
        self.anomaly_enabled_sensors: Set[str] = set()  # Set of sensor IDs with anomalies enabled
        self.anomaly_increments: Dict[str, float] = {}  # Per-sensor anomaly increment values
        self.anomaly_rate = 0.1  # Global anomaly rate (applied to all enabled sensors)

        # Per-production-line control
        self.active_production_lines: Set[str] = set()  # Production lines currently publishing (starts empty)
        self.simulator_control_topic = "sensors/control/simulator"  # Topic for simulator control commands

        # Initialize base values and sensor structure
        self._initialize_sensors()
        
    def _initialize_sensors(self):
        """Initialize base values for all sensors across all production lines"""
        for line_id in self.production_lines:
            # Initialize sensor structure for this line
            self.sensors[line_id] = {
                'temperature': [],
                'pressure': [],
                'vibration': [],
                'hygiene': []
            }

            # Temperature sensors: normal range 20-25°C
            for i in range(self.num_temp_sensors):
                sensor_id = f"TEMP_{i+1:03d}"
                full_sensor_id = f"{sensor_id}_{line_id}"
                self.sensors[line_id]['temperature'].append(sensor_id)
                self.base_values[full_sensor_id] = random.uniform(20.0, 25.0)
                self.base_variation[full_sensor_id] = 0.5  # Set variation for temperature sensors
                self.sensor_units=[full_sensor_id] = "°C"

            # Vibration sensors: normal range 0.5-2.0 mm/s
            for i in range(self.num_vibration_sensors):
                sensor_id = f"VIB_{i+1:03d}"
                full_sensor_id = f"{sensor_id}_{line_id}"
                self.sensors[line_id]['vibration'].append(sensor_id)
                self.base_values[full_sensor_id] = random.uniform(0.5, 2.0)
                self.base_variation[full_sensor_id] = 0.1  # Set variation for vibration sensors
                self.sensor_units[full_sensor_id] = "mm/s"

            # Pressure sensors: normal range 100-120 kPa
            for i in range(self.num_pressure_sensors):
                sensor_id = f"P_{i+1:03d}"
                full_sensor_id = f"{sensor_id}_{line_id}"
                self.sensors[line_id]['pressure'].append(sensor_id)
                self.base_values[full_sensor_id] = random.uniform(100.0, 120.0)
                self.base_variation[full_sensor_id] = 2.0  # Set variation for pressure sensors
                self.sensor_units

            # Hygiene sensors: normal range 40-60% humidity
            for i in range(self.num_hygiene_sensors):
                sensor_id = f"HYG_{i+1:03d}"
                full_sensor_id = f"{sensor_id}_{line_id}"
                self.sensors[line_id]['hygiene'].append(sensor_id)
                self.base_values[full_sensor_id] = random.uniform(40.0, 60.0)
                self.base_variation[full_sensor_id] = 2.0  # Set variation for hygiene sensors
                self.sensor_units[full_sensor_id] = "% humidity"

    def on_connect(self, client, userdata, flags, rc):
        """Callback for when client connects to broker"""
        if rc == 0:
            logger.info(f"Connected to Solace broker at {self.broker_host}:{self.broker_port}")
            # Subscribe to anomaly control topic
            client.subscribe(self.control_topic, qos=1)
            logger.info(f"Subscribed to anomaly control topic: {self.control_topic}")
            # Subscribe to simulator control topic
            client.subscribe(self.simulator_control_topic, qos=1)
            logger.info(f"Subscribed to simulator control topic: {self.simulator_control_topic}")
            # Publish simulator configuration for API discovery
            self._publish_configuration()
        else:
            logger.error(f"Connection failed with code {rc}")
    
    def on_disconnect(self, client, userdata, rc):
        """Callback for when client disconnects"""
        if rc != 0:
            logger.warning(f"Unexpected disconnection. Code: {rc}")
    
    def on_publish(self, client, userdata, mid):
        """Callback for when message is published"""
        logger.debug(f"Message {mid} published")

    def on_message(self, client, userdata, msg):
        """Callback for when a control message is received"""
        try:
            payload = json.loads(msg.payload.decode())
            command = payload.get('command')
            command_payload = payload.get('payload', {})

            logger.info(f"Received control command: {command} on topic: {msg.topic}")

            # Route based on topic
            if msg.topic == self.simulator_control_topic:
                self._handle_simulator_control(command, command_payload)
                return

            # Handle anomaly control commands (existing logic)

            if command == 'start_anomaly':
                # Get list of sensors to enable anomalies for
                target_sensors = command_payload.get('sensors', [])
                self.anomaly_rate = command_payload.get('anomalyRate', self.anomaly_rate)

                if target_sensors:
                    # Enable anomalies for specific sensors
                    for sensor_id in target_sensors:
                        self.anomaly_enabled_sensors.add(sensor_id)
                        # Initialize increment if not already present
                        if sensor_id not in self.anomaly_increments:
                            self.anomaly_increments[sensor_id] = 0.0
                    logger.info(f"Anomaly generation started for {len(target_sensors)} sensors with rate: {self.anomaly_rate}")
                    logger.info(f"Affected sensors: {', '.join(target_sensors)}")
                else:
                    logger.warning("No sensors specified in start_anomaly command")

            elif command == 'stop_anomaly':
                # Get optional list of sensors to stop anomalies for
                target_sensors = command_payload.get('sensors', [])

                if target_sensors:
                    # Stop anomalies for specific sensors
                    for sensor_id in target_sensors:
                        self.anomaly_enabled_sensors.discard(sensor_id)
                    logger.info(f"Anomaly generation stopped for sensors: {', '.join(target_sensors)}")
                else:
                    # Stop all anomalies
                    self.anomaly_enabled_sensors.clear()
                    logger.info("Anomaly generation stopped for all sensors")

            elif command == 'update_rate':
                self.anomaly_rate = command_payload.get('anomalyRate', self.anomaly_rate)
                logger.info(f"Anomaly rate updated to: {self.anomaly_rate}")

            elif command == 'reset_anomaly':
                # Get optional list of sensors to reset anomalies for
                target_sensors = command_payload.get('sensors', [])

                if target_sensors:
                    # Reset specific sensors
                    for sensor_id in target_sensors:
                        self.anomaly_increments[sensor_id] = 0.0
                    logger.info(f"Anomaly increment reset for sensors: {', '.join(target_sensors)}")
                else:
                    # Reset all sensors
                    self.anomaly_increments.clear()
                    logger.info("Anomaly increment reset for all sensors")

            else:
                logger.warning(f"Unknown command: {command}")

        except json.JSONDecodeError:
            logger.error("Failed to decode control message")
        except Exception as e:
            logger.error(f"Error processing control message: {e}")

    def _handle_simulator_control(self, command: str, command_payload: dict):
        """Handle simulator control commands (start/stop production lines)"""
        production_lines = command_payload.get('production_lines', [])

        if command == 'request_config':
            # Republish configuration on request
            logger.info("Received config request, republishing configuration")
            self._publish_configuration()

        elif command == 'start':
            # Add specified production lines to active set
            for line_id in production_lines:
                if line_id in self.production_lines:
                    self.active_production_lines.add(line_id)
                else:
                    logger.warning(f"Unknown production line: {line_id}")

            logger.info(f"Started publishing for production lines: {', '.join(production_lines)}")
            logger.info(f"Currently active lines: {sorted(self.active_production_lines)}")

        elif command == 'stop':
            # Remove specified production lines from active set
            for line_id in production_lines:
                self.active_production_lines.discard(line_id)

            logger.info(f"Stopped publishing for production lines: {', '.join(production_lines)}")
            logger.info(f"Currently active lines: {sorted(self.active_production_lines)}")

        else:
            logger.warning(f"Unknown simulator command: {command}")

    def _publish_configuration(self):
        """Publish simulator configuration for API discovery"""
        try:
            config = {
                "num_production_lines": self.num_production_lines,
                "production_lines": self.production_lines,
                "sensors_per_line": {
                    "temperature": self.num_temp_sensors,
                    "vibration": self.num_vibration_sensors,
                    "pressure": self.num_pressure_sensors,
                    "hygiene": self.num_hygiene_sensors
                },
                "total_sensors_per_line": self.num_temp_sensors + self.num_vibration_sensors + self.num_pressure_sensors + self.num_hygiene_sensors,
                "sensor_details": self.sensors,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            topic = "sensors/config/simulator"
            payload = json.dumps(config)

            result = self.client.publish(topic, payload, qos=1, retain=True)

            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Published simulator configuration to {topic}")
            else:
                logger.warning("Could not publish simulator configuration (may lack permissions)")
        except Exception as e:
            logger.warning(f"Could not publish simulator configuration: {e}")

    def connect(self):
        """Connect to the MQTT broker"""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            time.sleep(1)  # Wait for connection to establish
        except Exception as e:
            logger.error(f"Failed to connect to broker: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from the MQTT broker"""
        self.client.loop_stop()
        self.client.disconnect()
        logger.info("Disconnected from broker")

    def generate_reading(self, line_id: str, sensor_id: str, source: str) -> SensorReading:
        """
        Generate a reading for a sensor

        Args:
            line_id: The production line identifier
            sensor_id: The sensor identifier (without line prefix)
            source: The type of sensor (temperature | vibration | pressure | hygiene)
        Returns:
            SensorReading object
        """
        full_sensor_id = f"{sensor_id}_{line_id}"
        base_value = self.base_values[full_sensor_id]
        variation = self.base_variation[full_sensor_id]
        unit = self.sensor_units.get(full_sensor_id, "")

        # Add small random variation
        noise = random.uniform(-variation, variation)

        # Check if this sensor has anomaly enabled
        if full_sensor_id in self.anomaly_enabled_sensors:
            # Gradual increase over time
            anomaly_increment = self.anomaly_increments.get(full_sensor_id, 0.0)
            value = base_value + anomaly_increment + noise
            status = "warning" if anomaly_increment > 5 else "normal"
        else:
            value = base_value + noise
            status = "normal"

        return SensorReading(
            sensor_id=full_sensor_id,
            source=source,
            value=value,
            unit=unit,
            timestamp=datetime.now(timezone.utc).isoformat(),
            status=status
        )


    def publish_reading(self, line_id: str, reading: SensorReading):
        """
        Publish a sensor reading to the MQTT broker

        Args:
            line_id: The production line identifier
            reading: SensorReading object to publish
        """
        # New hierarchical topic structure: {self.reading_topic_prefix}/{line}/{type}/{sensor_id}
        topic = f"{self.reading_topic_prefix}/{line_id}/{reading.source}/{reading.sensor_id}"
        payload = json.dumps(asdict(reading))

        result = self.client.publish(topic, payload, qos=1)

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            logger.info(f"Published {reading.source} reading on {line_id}: "
                       f"{reading.sensor_id} = {reading.value} {reading.unit} "
                       f"[{reading.status}]")
        else:
            logger.error(f"Failed to publish reading for {reading.sensor_id} on {line_id}")
    
    def publish_all_sensors(self):
        """Publish readings from all sensors across active production lines only"""
        # Only publish for production lines that are currently active
        if not self.active_production_lines:
            logger.debug("No active production lines - skipping publish")
            return

        for line_id in self.active_production_lines:
            # Publish temperature readings
            for sensor_id in self.sensors[line_id]['temperature']:
                reading = self.generate_reading(line_id, sensor_id, "temperature")
                self.publish_reading(line_id, reading)

            # Publish vibration readings
            for sensor_id in self.sensors[line_id]['vibration']:
                reading = self.generate_reading(line_id, sensor_id, "vibration")
                self.publish_reading(line_id, reading)

            # Publish pressure readings
            for sensor_id in self.sensors[line_id]['pressure']:
                reading = self.generate_reading(line_id, sensor_id, "pressure")
                self.publish_reading(line_id, reading)

            # Publish hygiene readings
            for sensor_id in self.sensors[line_id]['hygiene']:
                reading = self.generate_reading(line_id, sensor_id, "hygiene")
                self.publish_reading(line_id, reading)
    
    def run(self, interval: int = 5, duration: int = None):
        """
        Run the sensor simulator

        Args:
            interval: Time between readings in seconds (default 5)
            duration: Total duration in seconds (None for infinite)

        Note:
            Anomaly rate is now controlled via MQTT control commands
        """
        logger.info(f"Starting sensor simulator...")
        logger.info(f"Production lines: {self.num_production_lines}")
        logger.info(f"Sensors per line - Temperature: {self.num_temp_sensors}, "
                   f"Vibration: {self.num_vibration_sensors}, "
                   f"Hygiene: {self.num_hygiene_sensors}")
        total_sensors = (self.num_temp_sensors + self.num_vibration_sensors +
                        self.num_hygiene_sensors) * self.num_production_lines
        logger.info(f"Total sensors: {total_sensors}")
        logger.info(f"Publishing interval: {interval} seconds")
        logger.info("Simulator started in IDLE mode - no production lines active")
        logger.info("Use the API to start production lines: POST /api/simulator/start")

        start_time = time.time()
        iteration = 0

        try:
            while True:
                # Check duration limit
                if duration and (time.time() - start_time) >= duration:
                    logger.info("Duration limit reached. Stopping...")
                    break

                # Only process iterations if at least one production line is active
                if self.active_production_lines:
                    # Publish all sensor readings
                    self.publish_all_sensors()

                    # Increment anomaly values for all enabled sensors
                    for sensor_id in self.anomaly_enabled_sensors:
                        current_increment = self.anomaly_increments.get(sensor_id, 0.0)
                        self.anomaly_increments[sensor_id] = current_increment + self.anomaly_rate

                    iteration += 1
                    active_lines_str = ', '.join(sorted(self.active_production_lines))
                    if self.anomaly_enabled_sensors:
                        logger.info(f"Iteration {iteration} complete. "
                                   f"Active lines: [{active_lines_str}], "
                                   f"Anomalies: {len(self.anomaly_enabled_sensors)} sensors")
                    else:
                        logger.info(f"Iteration {iteration} complete. Active lines: [{active_lines_str}]")
                else:
                    # No active production lines - idle state
                    logger.debug("Simulator idle - waiting for production lines to be started")

                # Wait for next interval
                time.sleep(interval)

        except KeyboardInterrupt:
            logger.info("Received interrupt signal. Stopping...")
        except Exception as e:
            logger.error(f"Error during simulation: {e}")
            raise


def main():
    """Main function to run the sensor simulator"""

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description='IoT Sensor Simulator for multiple production lines',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    # MQTT Broker Configuration
    parser.add_argument('--broker-host', type=str, default='localhost',
                       help='Solace broker hostname')
    parser.add_argument('--broker-port', type=int, default=1883,
                       help='MQTT port')
    parser.add_argument('--username', type=str, default='simulator',
                       help='MQTT username')
    parser.add_argument('--password', type=str, default='simulator',
                       help='MQTT password')

    # Production Line and Sensor Configuration
    parser.add_argument('-l', '--production-lines', type=int, default=1,
                       help='Number of production lines')
    parser.add_argument('-t', '--temp-sensors', type=int, default=10,
                       help='Temperature sensors per production line')
    parser.add_argument('-v', '--vibration-sensors', type=int, default=15,
                       help='Vibration sensors per production line')
    parser.add_argument('-g', '--hygiene-sensors', type=int, default=5,
                       help='Hygiene sensors per production line')

    # Simulation Parameters
    parser.add_argument('-i', '--interval', type=int, default=5,
                       help='Publishing interval in seconds')
    parser.add_argument('-d', '--duration', type=int, default=None,
                       help='Total duration in seconds (None for infinite)')

    # Topic Configuration
    parser.add_argument('--topic-prefix', type=str, default='sensors/reading',
                       help='MQTT topic prefix for sensor readings (e.g., sensors/reading or sensors)')

    args = parser.parse_args()

    # Validate inputs
    if args.production_lines < 1:
        parser.error("Number of production lines must be at least 1")
    if args.temp_sensors < 0 or args.vibration_sensors < 0 or args.hygiene_sensors < 0:
        parser.error("Sensor counts must be non-negative")

    # MQTT topics
    CONTROL_TOPIC = "sensors/control/anomaly"

    # Create and run simulator
    simulator = SensorSimulator(
        broker_host=args.broker_host,
        broker_port=args.broker_port,
        username=args.username,
        password=args.password,
        control_topic=CONTROL_TOPIC,
        reading_topic_prefix=args.topic_prefix,
        num_production_lines=args.production_lines,
        num_temp_sensors=args.temp_sensors,
        num_vibration_sensors=args.vibration_sensors,
        num_hygiene_sensors=args.hygiene_sensors
    )

    try:
        simulator.connect()
        simulator.run(
            interval=args.interval,
            duration=args.duration
        )
    finally:
        simulator.disconnect()


if __name__ == "__main__":
    main()
