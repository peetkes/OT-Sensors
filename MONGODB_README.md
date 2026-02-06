# MongoDB Sensor Data Consumer

A Python-based MQTT consumer that subscribes to all sensor data topics and stores the readings in MongoDB for historical analysis and querying.

## Features

- **Automatic Data Storage**: Subscribes to all sensor topics (`sensors/#`) and stores data in MongoDB
- **Hierarchical Topic Parsing**: Extracts production line information from topic structure
- **Optimized Indexing**: Creates indexes for efficient querying by line, type, status, and timestamp
- **Connection Resilience**: Handles MQTT and MongoDB reconnections
- **Statistics Tracking**: Shows consumption and storage statistics
- **Graceful Shutdown**: Properly closes connections and displays summary on exit

## Prerequisites

- Python 3.7+
- MongoDB (local installation or MongoDB Atlas cloud)
- MQTT broker (same as sensor simulator)
- Required Python packages (see [requirements.txt](requirements.txt))

## Installation

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- `paho-mqtt` - MQTT client
- `pymongo` - MongoDB Python driver

### 2. Setup MongoDB

**Option A: Local MongoDB with Docker**
```bash
docker run -d \
  --name mongodb \
  -p 27017:27017 \
  -v mongodb_data:/data/db \
  mongo:latest
```

**Option B: MongoDB Atlas (Cloud)**
1. Create free account at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string (format: `mongodb+srv://username:password@cluster.mongodb.net/`)
4. Whitelist your IP address

**Option C: Local MongoDB Installation**
- macOS: `brew install mongodb-community`
- Ubuntu: `sudo apt-get install mongodb`
- Windows: Download from [mongodb.com](https://www.mongodb.com/try/download/community)

### 3. Configure the Consumer

```bash
# Copy configuration example
cp mongodb_config_example.py mongodb_config.py

# Edit configuration
nano mongodb_config.py
```

Update these settings:
```python
MQTT_BROKER_HOST = "localhost"  # Your MQTT broker
MONGODB_URI = "mongodb://localhost:27017/"  # Your MongoDB URI
DATABASE_NAME = "iot_sensors"
COLLECTION_NAME = "sensor_readings"
```

## Usage

### Start the Consumer

```bash
python mongodb_consumer.py
```

You should see:
```
2026-02-06 10:30:00 - __main__ - INFO - Connecting to MongoDB at mongodb://localhost:27017/
2026-02-06 10:30:00 - __main__ - INFO - MongoDB connection successful
2026-02-06 10:30:00 - __main__ - INFO - MongoDB indexes created successfully
2026-02-06 10:30:00 - __main__ - INFO - Connected to MQTT broker at localhost:1883
2026-02-06 10:30:00 - __main__ - INFO - Subscribed to sensors/# topic
2026-02-06 10:30:00 - __main__ - INFO - Starting MongoDB sensor consumer...
```

### Stop the Consumer

Press `Ctrl+C` to gracefully shutdown and see statistics:
```
============================================================
MONGODB CONSUMER STATISTICS
============================================================
Total messages received: 150
Successfully inserted: 150
Errors: 0

Total documents in database: 150

Documents per production line:
  LINE_001: 50
  LINE_002: 50
  LINE_003: 50

Documents per sensor type:
  hygiene: 45
  temperature: 60
  vibration: 45
============================================================
```

## Data Schema

Each sensor reading is stored as a MongoDB document:

```json
{
  "_id": ObjectId("..."),
  "line_id": "LINE_001",
  "sensor_id": "TEMP_001",
  "sensor_type": "temperature",
  "value": 23.45,
  "unit": "°C",
  "status": "normal",
  "timestamp": "2024-02-06T10:30:00.000Z",
  "created_at": ISODate("2024-02-06T10:30:01.234Z")
}
```

**Fields:**
- `line_id`: Production line identifier (e.g., "LINE_001")
- `sensor_id`: Sensor identifier without line prefix (e.g., "TEMP_001")
- `sensor_type`: Type of sensor ("temperature", "vibration", "hygiene")
- `value`: Numeric sensor reading
- `unit`: Unit of measurement ("°C", "mm/s", "%")
- `status`: Sensor status ("normal", "warning")
- `timestamp`: Reading timestamp from sensor (ISO 8601 format)
- `created_at`: MongoDB insertion time (for tracking data lag)

## Querying Data

### Using MongoDB Shell

```bash
# Connect to MongoDB
mongosh  # or: mongo

# Use the database
use iot_sensors

# Count total documents
db.sensor_readings.countDocuments()

# Find latest 10 readings
db.sensor_readings.find().sort({timestamp: -1}).limit(10)

# Find all readings from a specific line
db.sensor_readings.find({line_id: "LINE_001"})

# Find temperature sensor readings
db.sensor_readings.find({sensor_type: "temperature"})

# Find anomalies (warnings)
db.sensor_readings.find({status: "warning"})

# Find readings in a time range
db.sensor_readings.find({
  timestamp: {
    $gte: "2024-02-06T00:00:00.000Z",
    $lt: "2024-02-07T00:00:00.000Z"
  }
})

# Aggregate average temperature per line
db.sensor_readings.aggregate([
  {$match: {sensor_type: "temperature"}},
  {$group: {
    _id: "$line_id",
    avgTemp: {$avg: "$value"},
    count: {$sum: 1}
  }},
  {$sort: {_id: 1}}
])
```

### Using Python

```python
from pymongo import MongoClient
from datetime import datetime, timedelta

# Connect
client = MongoClient("mongodb://localhost:27017/")
db = client.iot_sensors
collection = db.sensor_readings

# Get total count
total = collection.count_documents({})
print(f"Total documents: {total}")

# Get latest reading
latest = collection.find_one(sort=[("timestamp", -1)])
print(f"Latest: {latest}")

# Query by production line
line_data = collection.find({"line_id": "LINE_001"}).limit(10)
for doc in line_data:
    print(doc)

# Find anomalies
anomalies = collection.find({"status": "warning"})
print(f"Anomalies found: {anomalies.count()}")

# Time-range query (last hour)
one_hour_ago = datetime.utcnow() - timedelta(hours=1)
recent = collection.find({
    "created_at": {"$gte": one_hour_ago}
})

# Aggregation: Average value per sensor type
pipeline = [
    {"$group": {
        "_id": "$sensor_type",
        "avg_value": {"$avg": "$value"},
        "min_value": {"$min": "$value"},
        "max_value": {"$max": "$value"},
        "count": {"$sum": 1}
    }},
    {"$sort": {"_id": 1}}
]
stats = list(collection.aggregate(pipeline))
for stat in stats:
    print(f"{stat['_id']}: avg={stat['avg_value']:.2f}, "
          f"min={stat['min_value']:.2f}, max={stat['max_value']:.2f}, "
          f"count={stat['count']}")
```

## Indexes

The consumer automatically creates the following indexes for query performance:

| Index | Purpose |
|-------|---------|
| `line_id + timestamp` | Query readings by production line over time |
| `sensor_type + timestamp` | Query by sensor type over time |
| `status + timestamp` | Find anomalies over time |
| `timestamp` | General time-range queries |

## Data Retention

To automatically delete old data after a certain period, enable the TTL (Time To Live) index:

1. Edit `mongodb_consumer.py`
2. Uncomment this line in the `_create_indexes()` method:
   ```python
   self.collection.create_index("created_at", expireAfterSeconds=2592000)
   ```
3. Adjust `expireAfterSeconds` as needed:
   - 30 days: `2592000`
   - 7 days: `604800`
   - 1 day: `86400`

MongoDB will automatically delete documents older than the specified time.

## Troubleshooting

### Consumer can't connect to MongoDB

**Error:** `ServerSelectionTimeoutError`

**Solutions:**
1. Verify MongoDB is running:
   ```bash
   docker ps  # Check if container is running
   # or
   systemctl status mongod  # Check service status
   ```

2. Check connection string in `mongodb_config.py`
3. For MongoDB Atlas: Verify IP whitelist and credentials

### Consumer can't connect to MQTT broker

**Error:** MQTT connection failed

**Solutions:**
1. Verify sensor simulator or MQTT broker is running
2. Check `MQTT_BROKER_HOST` and `MQTT_BROKER_PORT` settings
3. Test MQTT connection:
   ```bash
   python subscriber.py  # Should receive sensor data
   ```

### No data being stored

**Check:**
1. Is the sensor simulator publishing data?
   ```bash
   python subscriber.py  # Verify data flow
   ```

2. Check consumer logs for errors
3. Verify topic format matches `sensors/{line}/{type}/{id}`

### Slow queries

**Solutions:**
1. Verify indexes are created (check logs on startup)
2. Use compound indexes for common query patterns
3. Add projection to return only needed fields:
   ```python
   collection.find({"line_id": "LINE_001"}, {"_id": 0, "value": 1, "timestamp": 1})
   ```

## Architecture

```
┌─────────────────┐          MQTT Topics           ┌──────────────────┐
│     Sensor      │  sensors/{line}/{type}/{id}    │    MongoDB       │
│    Simulator    │ ─────────────────────────────> │    Consumer      │
│    (Python)     │                                 │    (Python)      │
└─────────────────┘                                 └──────────────────┘
         │                                                   │
         │                                                   │
         └──────────> MQTT Broker <─────────────────────────┘
                   (Solace/Mosquitto)                       │
                                                             ▼
                                                   ┌──────────────────┐
                                                   │     MongoDB      │
                                                   │     Database     │
                                                   │  iot_sensors.    │
                                                   │ sensor_readings  │
                                                   └──────────────────┘
```

## Performance Considerations

- **Bulk Inserts**: For high-throughput scenarios, modify the consumer to batch insert documents
- **Write Concern**: Adjust MongoDB write concern based on durability requirements
- **Connection Pooling**: MongoClient handles connection pooling automatically
- **Sharding**: For very large datasets, consider MongoDB sharding

## Security Best Practices

1. **MongoDB Authentication**: Always use authentication in production
   ```python
   MONGODB_URI = "mongodb://username:password@host:port/"
   ```

2. **Network Security**: Use TLS/SSL for MongoDB connections
   ```python
   MONGODB_URI = "mongodb://host:port/?tls=true"
   ```

3. **Access Control**: Create a dedicated MongoDB user with limited permissions
   ```javascript
   db.createUser({
     user: "sensor_consumer",
     pwd: "strong_password",
     roles: [{role: "readWrite", db: "iot_sensors"}]
   })
   ```

4. **MQTT Security**: Use MQTT over TLS and authentication

## License

MIT
