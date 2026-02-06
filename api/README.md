# Sensor Anomaly Control API

A Node.js REST API that controls anomaly generation in the sensor simulator via MQTT commands.

## Architecture

This API uses **MQTT as a command channel** to control the Python sensor simulator in real-time. The Node.js API publishes control commands to an MQTT topic, and the sensor simulator subscribes to that topic to receive and execute commands.

```
┌─────────────┐         MQTT Commands          ┌──────────────────┐
│   REST API  │ ───────────────────────────────>│ Sensor Simulator │
│  (Node.js)  │  (sensors/control/anomaly)     │    (Python)      │
└─────────────┘                                 └──────────────────┘
      │                                                   │
      │                                                   │
      └───────────────────> MQTT Broker <────────────────┘
                         (Solace/Mosquitto)
```

## Features

- Start/Stop anomaly generation on demand
- Adjust anomaly rate dynamically
- Target specific sensors across multiple production lines
- Support for temperature, vibration, and hygiene sensors
- Reset anomaly increment to zero
- Get current anomaly status
- Health check endpoint
- MQTT-based real-time control

## Prerequisites

- Node.js 16+ and npm
- Python 3.8+
- MQTT broker (Solace, Mosquitto, etc.)
- Running sensor simulator

## Installation

### 1. Install Node.js Dependencies

```bash
cd api
npm install
```

### 2. Configure Environment

Copy the example environment file and update with your settings:

```bash
cp .env.example .env
```

Edit `.env`:

```env
PORT=3000
NODE_ENV=development

MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=

MQTT_CONTROL_TOPIC=sensors/control/anomaly
```

### 3. Create Logs Directory

```bash
mkdir -p logs
```

## Usage

### Start the API Server

**Development mode (with auto-reload):**
```bash
npm run dev
```

**Production mode:**
```bash
npm start
```

The server will start on port 3000 (or the port specified in `.env`).

### Start the Sensor Simulator

Ensure the Python sensor simulator is running with MQTT control enabled:

```bash
cd ..
# Run with default configuration (1 production line)
python sensor_simulator.py

# Or run with custom production line configuration
python sensor_simulator.py --production-lines 3 --temp-sensors 5 --vibration-sensors 8 --hygiene-sensors 3
```

The simulator will automatically subscribe to the control topic and respond to commands.

## Sensor ID Format

The simulator now supports multiple production lines with hierarchical sensor IDs:

**Format:** `{SENSOR_TYPE}_{NUMBER}_{LINE_ID}`

**Examples:**
- `TEMP_001_LINE_001` - Temperature sensor 1 on production line 1
- `VIB_007_LINE_002` - Vibration sensor 7 on production line 2
- `HYG_003_LINE_001` - Hygiene sensor 3 on production line 1

**Sensor Types:**
- `TEMP_XXX` - Temperature sensors (20-25°C normal range)
- `VIB_XXX` - Vibration sensors (0.5-2.0 mm/s normal range)
- `HYG_XXX` - Hygiene sensors (40-60% humidity normal range)

## API Endpoints

### Simulator Control

Control which production lines are actively publishing sensor data.

#### Start Production Lines

**POST** `/api/simulator/start`

Start publishing sensor data for specific production lines.

**Request Body:**
```json
{
  "production_lines": ["LINE_001", "LINE_002"]
}
```

**Parameters:**
- `production_lines` (required): Array of production line IDs to start (format: LINE_XXX)

**Response:**
```json
{
  "status": "success",
  "message": "Started publishing for 2 production line(s)",
  "data": {
    "active_lines": ["LINE_001", "LINE_002"],
    "lastUpdated": "2024-02-06T16:30:00.000Z"
  }
}
```

#### Stop Production Lines

**POST** `/api/simulator/stop`

Stop publishing sensor data for specific production lines.

**Request Body:**
```json
{
  "production_lines": ["LINE_001"]
}
```

**Parameters:**
- `production_lines` (required): Array of production line IDs to stop

**Response:**
```json
{
  "status": "success",
  "message": "Stopped publishing for 1 production line(s)",
  "data": {
    "active_lines": ["LINE_002"],
    "lastUpdated": "2024-02-06T16:35:00.000Z"
  }
}
```

#### Get Simulator Status

**GET** `/api/simulator/status`

Get current active production lines.

**Response:**
```json
{
  "status": "success",
  "data": {
    "active_lines": ["LINE_001", "LINE_002"],
    "mqttConnected": true
  }
}
```

#### Get Simulator Configuration

**GET** `/api/simulator/config`

Get simulator configuration including number of production lines and all sensors.

**Response:**
```json
{
  "status": "success",
  "data": {
    "num_production_lines": 3,
    "production_lines": ["LINE_001", "LINE_002", "LINE_003"],
    "sensors_per_line": {
      "temperature": 5,
      "vibration": 8,
      "hygiene": 3
    },
    "total_sensors_per_line": 16,
    "sensor_details": {
      "LINE_001": {
        "temperature": ["TEMP_001", "TEMP_002", "TEMP_003", "TEMP_004", "TEMP_005"],
        "vibration": ["VIB_001", "VIB_002", "VIB_003", "VIB_004", "VIB_005", "VIB_006", "VIB_007", "VIB_008"],
        "hygiene": ["HYG_001", "HYG_002", "HYG_003"]
      },
      "LINE_002": { ... },
      "LINE_003": { ... }
    },
    "timestamp": "2024-02-06T16:30:00.000Z"
  }
}
```

**Use Cases:**
- Discover available production lines dynamically
- Build UI dropdowns for line selection
- Validate line IDs before sending commands
- Display simulator capacity

### Health Check

**GET** `/health`

Check the API and MQTT connection health.

**Response:**
```json
{
  "status": "ok",
  "timestamp": "2024-02-06T10:30:00.000Z",
  "uptime": 123.45,
  "mqtt": {
    "connected": true
  }
}
```

### Start Anomaly Generation

**POST** `/api/anomaly/start`

Start generating anomalies in the sensor data for specific sensors.

**Request Body:**
```json
{
  "anomalyRate": 0.3,
  "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"]
}
```

**Parameters:**
- `anomalyRate` (optional): Rate of anomaly increase per interval (0-10, default: 0.1)
- `sensors` (required): Array of sensor IDs to apply anomalies to. Use format `{TYPE}_{NUM}_{LINE}`

**Response:**
```json
{
  "status": "success",
  "message": "Anomaly generation started",
  "data": {
    "enabled": true,
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"],
    "lastUpdated": "2024-02-06T10:30:00.000Z"
  }
}
```

### Stop Anomaly Generation

**POST** `/api/anomaly/stop`

Stop generating anomalies for specific sensors or all sensors.

**Request Body (optional):**
```json
{
  "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002"]
}
```

**Parameters:**
- `sensors` (optional): Array of sensor IDs to stop anomalies for. If omitted, stops all anomalies.

**Response:**
```json
{
  "status": "success",
  "message": "Anomaly generation stopped",
  "data": {
    "enabled": false,
    "anomalyRate": 0.1,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002"],
    "lastUpdated": "2024-02-06T10:35:00.000Z"
  }
}
```

### Get Anomaly Status

**GET** `/api/anomaly/status`

Get the current state of anomaly generation.

**Response:**
```json
{
  "status": "success",
  "data": {
    "enabled": true,
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"],
    "lastUpdated": "2024-02-06T10:30:00.000Z",
    "mqttConnected": true
  }
}
```

### Update Anomaly Rate

**PATCH** `/api/anomaly/rate`

Change the anomaly rate while anomaly generation is running (applies globally to all enabled sensors).

**Request Body:**
```json
{
  "anomalyRate": 0.5
}
```

**Parameters:**
- `anomalyRate` (required): New rate (0-10)

**Response:**
```json
{
  "status": "success",
  "message": "Anomaly rate updated",
  "data": {
    "enabled": true,
    "anomalyRate": 0.5,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"],
    "lastUpdated": "2024-02-06T10:40:00.000Z"
  }
}
```

### Reset Anomaly Increment

**POST** `/api/anomaly/reset`

Reset the anomaly increment back to 0 for specific sensors or all sensors.

**Request Body (optional):**
```json
{
  "sensors": ["TEMP_001_LINE_001"]
}
```

**Parameters:**
- `sensors` (optional): Array of sensor IDs to reset. If omitted, resets all sensors.

**Response:**
```json
{
  "status": "success",
  "message": "Anomaly increment reset to 0",
  "data": {
    "enabled": true,
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"],
    "lastUpdated": "2024-02-06T10:45:00.000Z"
  }
}
```

## MQTT Control Messages

The API publishes control messages to the MQTT topic `sensors/control/anomaly` with the following structure:

```json
{
  "command": "start_anomaly",
  "payload": {
    "enabled": true,
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"]
  },
  "timestamp": "2024-02-06T10:30:00.000Z"
}
```

### Supported Commands

- `start_anomaly`: Enable anomaly generation for specific sensors
  - Payload: `{ anomalyRate, sensors: [...] }`
- `stop_anomaly`: Disable anomaly generation
  - Payload: `{ sensors: [...] }` (optional, stops all if omitted)
- `update_rate`: Change anomaly rate globally
  - Payload: `{ anomalyRate }`
- `reset_anomaly`: Reset increment to 0
  - Payload: `{ sensors: [...] }` (optional, resets all if omitted)

## Example Usage

### Using curl

#### Simulator Control Examples

**Start specific production lines:**
```bash
curl -X POST http://localhost:3000/api/simulator/start \
  -H "Content-Type: application/json" \
  -d '{"production_lines": ["LINE_001", "LINE_002"]}'
```

**Stop specific production lines:**
```bash
curl -X POST http://localhost:3000/api/simulator/stop \
  -H "Content-Type: application/json" \
  -d '{"production_lines": ["LINE_001"]}'
```

**Check simulator status:**
```bash
curl http://localhost:3000/api/simulator/status
```

**Get simulator configuration:**
```bash
curl http://localhost:3000/api/simulator/config
```

Returns:
- Number of production lines
- All production line IDs
- Sensor counts per line (temperature, vibration, hygiene)
- Complete sensor list for each line

**Progressive line activation (demo scenario):**
```bash
# Start simulator idle (no lines active)
python sensor_simulator.py --production-lines 5

# Activate lines progressively
curl -X POST http://localhost:3000/api/simulator/start \
  -d '{"production_lines": ["LINE_001"]}'

# Add more lines
curl -X POST http://localhost:3000/api/simulator/start \
  -d '{"production_lines": ["LINE_002", "LINE_003"]}'

# Now 3 lines active: LINE_001, LINE_002, LINE_003
```

#### Anomaly Control Examples

**Start anomaly generation on specific sensors:**
```bash
# Target specific sensors across different production lines
curl -X POST http://localhost:3000/api/anomaly/start \
  -H "Content-Type: application/json" \
  -d '{
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002", "HYG_003_LINE_001"]
  }'
```

**Start anomalies on all temperature sensors of a production line:**
```bash
# Manually specify all temp sensors for LINE_001
curl -X POST http://localhost:3000/api/anomaly/start \
  -H "Content-Type: application/json" \
  -d '{
    "anomalyRate": 0.2,
    "sensors": ["TEMP_001_LINE_001", "TEMP_002_LINE_001", "TEMP_003_LINE_001"]
  }'
```

**Check status:**
```bash
curl http://localhost:3000/api/anomaly/status
```

**Update rate:**
```bash
curl -X PATCH http://localhost:3000/api/anomaly/rate \
  -H "Content-Type: application/json" \
  -d '{"anomalyRate": 0.5}'
```

**Stop anomaly for specific sensors:**
```bash
curl -X POST http://localhost:3000/api/anomaly/stop \
  -H "Content-Type: application/json" \
  -d '{"sensors": ["TEMP_001_LINE_001"]}'
```

**Stop all anomalies:**
```bash
curl -X POST http://localhost:3000/api/anomaly/stop
```

**Reset increment for specific sensors:**
```bash
curl -X POST http://localhost:3000/api/anomaly/reset \
  -H "Content-Type: application/json" \
  -d '{"sensors": ["VIB_007_LINE_002"]}'
```

**Reset all anomaly increments:**
```bash
curl -X POST http://localhost:3000/api/anomaly/reset
```

### Using JavaScript/Fetch

```javascript
// Start anomaly on specific sensors with custom rate
const response = await fetch('http://localhost:3000/api/anomaly/start', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    anomalyRate: 0.3,
    sensors: [
      'TEMP_001_LINE_001',
      'VIB_007_LINE_002',
      'HYG_003_LINE_001'
    ]
  })
});

const result = await response.json();
console.log(result);

// Stop anomalies for specific sensors
await fetch('http://localhost:3000/api/anomaly/stop', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    sensors: ['TEMP_001_LINE_001']
  })
});
```

## Project Structure

```
api/
├── src/
│   ├── config/
│   │   └── config.js           # Configuration management
│   ├── middleware/
│   │   ├── error.js            # Error handling
│   │   └── validation.js       # Request validation
│   ├── routes/
│   │   ├── anomaly.routes.js   # Anomaly control endpoints
│   │   └── health.routes.js    # Health check endpoint
│   ├── services/
│   │   └── mqtt.service.js     # MQTT client service
│   ├── utils/
│   │   └── logger.js           # Logging utility
│   └── server.js               # Main application
├── logs/                       # Log files
├── .env                        # Environment variables
├── .env.example                # Example environment file
├── package.json                # Dependencies
└── README.md                   # This file
```

## Error Handling

The API returns structured error responses:

```json
{
  "status": "error",
  "message": "Validation failed",
  "errors": [
    {
      "field": "anomalyRate",
      "message": "\"anomalyRate\" must be less than or equal to 10"
    }
  ]
}
```

## Logging

Logs are written to:
- Console (colored output)
- `logs/combined.log` (all logs)
- `logs/error.log` (errors only)

## Troubleshooting

### API can't connect to MQTT broker

1. Verify MQTT broker is running
2. Check `MQTT_BROKER_HOST` and `MQTT_BROKER_PORT` in `.env`
3. Check credentials if authentication is required
4. Review logs in `logs/combined.log`

### Sensor simulator not responding to commands

1. Ensure simulator is running
2. Verify simulator connects to the same MQTT broker
3. Check the control topic matches in both API and simulator
4. Look for control messages in simulator logs

### Health check shows MQTT disconnected

The API will retry connection automatically. Check:
- MQTT broker status
- Network connectivity
- Broker credentials

## License

MIT
