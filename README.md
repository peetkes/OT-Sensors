# IoT Sensor Simulator for Solace MQTT

A Python-based sensor simulator that generates temperature and vibration readings and publishes them to a Solace broker using MQTT protocol.

## Features

- **10 Temperature Sensors** (TEMP_000 to TEMP_009)
  - Normal range: 20-25°C
  - Sensor TEMP_003 simulates gradual temperature increase (anomaly detection scenario)

- **15 Vibration Sensors** (VIB_000 to VIB_014)
  - Normal range: 0.5-2.0 mm/s
  - Sensor VIB_007 simulates gradual vibration increase (anomaly detection scenario)

- **MQTT Publishing**
  - Publishes to Solace broker
  - QoS level 1 (at least once delivery)
  - JSON payload format
  - Hierarchical topic structure: `sensors/{type}/{sensor_id}`

## Prerequisites

- Python 3.7 or higher
- Access to a Solace broker (cloud or on-premises)
- MQTT credentials (if authentication is enabled)

## Installation

1. Clone or download this project

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

### Option 1: Edit the main script directly

Open `sensor_simulator.py` and update the configuration values in the `main()` function:

```python
BROKER_HOST = "your-solace-broker.messaging.solace.cloud"
BROKER_PORT = 1883
USERNAME = "your-username"  # or None if not required
PASSWORD = "your-password"  # or None if not required
```

### Option 2: Use a configuration file

1. Copy the example configuration:
```bash
cp config_example.py config.py
```

2. Edit `config.py` with your Solace broker details

3. Modify the script to import from `config.py`

## Usage

### Basic Usage

Run the simulator with default settings:

```bash
python sensor_simulator.py
```

This will:
- Connect to the configured Solace broker
- Publish readings every 5 seconds
- Run indefinitely (press Ctrl+C to stop)
- Gradually increase anomaly sensor readings

### Customization

You can customize the simulation by modifying parameters in the `main()` function:

```python
INTERVAL = 5          # Publish every 5 seconds
DURATION = 300        # Run for 300 seconds (5 minutes)
ANOMALY_RATE = 0.1    # Increase anomaly by 0.1 units per interval
```

## MQTT Topic Structure

The simulator publishes to the following topic structure:

- Temperature readings: `sensors/temperature/{sensor_id}`
  - Example: `sensors/temperature/TEMP_003`

- Vibration readings: `sensors/vibration/{sensor_id}`
  - Example: `sensors/vibration/VIB_007`

## Message Format

Each sensor reading is published as a JSON object:

```json
{
  "sensor_id": "TEMP_003",
  "sensor_type": "temperature",
  "value": 25.47,
  "unit": "°C",
  "timestamp": "2026-01-31T10:30:45.123456",
  "status": "warning"
}
```

Fields:
- `sensor_id`: Unique identifier for the sensor
- `sensor_type`: Type of sensor (temperature or vibration)
- `value`: Sensor reading value
- `unit`: Unit of measurement (°C or mm/s)
- `timestamp`: ISO 8601 formatted UTC timestamp
- `status`: "normal" or "warning" (based on anomaly threshold)

## Monitoring

The simulator logs all activities to the console:

```
2026-01-31 10:30:45,123 - __main__ - INFO - Connected to Solace broker at localhost:1883
2026-01-31 10:30:45,234 - __main__ - INFO - Published temperature reading: TEMP_003 = 25.47 °C [warning]
2026-01-31 10:30:45,345 - __main__ - INFO - Published vibration reading: VIB_007 = 2.34 mm/s [warning]
```

## Solace Broker Setup

### Using Solace Cloud

1. Sign up for a free account at https://solace.com/try-it-now/
2. Create a new messaging service
3. Note down the MQTT connection details:
   - Host
   - Port (typically 1883 or 8883 for TLS)
   - Username
   - Password

### Using Local Solace Broker

You can also run a local Solace broker using Docker:

```bash
docker run -d -p 8080:8080 -p 1883:1883 -p 8008:8008 -p 9000:9000 \
  --shm-size=2g --env username_admin_globalaccesslevel=admin \
  --env username_admin_password=admin --name=solace solace/solace-pubsub-standard
```

Then use:
- BROKER_HOST = "localhost"
- BROKER_PORT = 1883
- USERNAME = "admin"
- PASSWORD = "admin"

## Testing

### Subscribe to Topics

You can test the simulator by subscribing to the MQTT topics using an MQTT client:

Using `mosquitto_sub`:
```bash
mosquitto_sub -h your-broker-host -p 1883 -u username -P password -t "sensors/#" -v
```

Using Solace Try-Me tool:
1. Log into Solace Cloud Console
2. Go to your messaging service
3. Click "Try Me!"
4. Subscribe to `sensors/>`

## Troubleshooting

### Connection Issues

If you can't connect to the broker:
1. Verify the broker hostname and port
2. Check firewall settings
3. Ensure credentials are correct
4. For Solace Cloud, verify the service is running

### No Messages Received

If you're not receiving messages:
1. Verify you're subscribed to the correct topic pattern
2. Check the QoS settings
3. Review the simulator logs for errors

## Project Structure

```
.
├── sensor_simulator.py    # Main simulator script
├── requirements.txt       # Python dependencies
├── config_example.py      # Example configuration file
└── README.md             # This file
```

## Advanced Usage

### Running as a Background Service

On Linux with systemd:

1. Create a service file `/etc/systemd/system/sensor-simulator.service`:

```ini
[Unit]
Description=IoT Sensor Simulator
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/sensor-simulator
ExecStart=/usr/bin/python3 /path/to/sensor-simulator/sensor_simulator.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

2. Enable and start the service:
```bash
sudo systemctl enable sensor-simulator
sudo systemctl start sensor-simulator
```

## License

This project is provided as-is for demonstration and educational purposes.

## Support

For issues related to:
- This simulator: Check the code and logs
- Solace broker: Visit https://solace.com/support/
- MQTT protocol: Visit https://mqtt.org/
