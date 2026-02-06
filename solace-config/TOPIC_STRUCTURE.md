# MQTT Topic Structure & Permissions

Complete reference for all MQTT topics used in the OT-Sensors system.

## Topic Hierarchy

```
sensors/
├── reading/                    # Sensor data (published by simulator)
│   ├── {LINE_ID}/
│   │   ├── temperature/
│   │   │   └── {SENSOR_ID}     # e.g., sensors/reading/LINE_001/temperature/TEMP_001
│   │   ├── vibration/
│   │   │   └── {SENSOR_ID}     # e.g., sensors/reading/LINE_001/vibration/VIB_007
│   │   └── hygiene/
│   │       └── {SENSOR_ID}     # e.g., sensors/reading/LINE_001/hygiene/HYG_003
│
├── control/                    # Command topics (published by API)
│   ├── anomaly                 # Anomaly control commands
│   └── simulator               # Simulator start/stop commands
│
└── config/                     # Configuration topics
    └── simulator               # Simulator configuration (published by simulator)
```

## Topics by Component

### Sensor Simulator

**Publishes to:**
- `sensors/reading/{LINE_ID}/{TYPE}/{SENSOR_ID}` - Sensor readings
  - Example: `sensors/reading/LINE_001/temperature/TEMP_001`
- `sensors/config/simulator` - Simulator configuration

**Subscribes to:**
- `sensors/control/anomaly` - Anomaly control commands
- `sensors/control/simulator` - Simulator start/stop commands

### REST API (Node.js)

**Publishes to:**
- `sensors/control/anomaly` - Anomaly commands (start_anomaly, stop_anomaly, etc.)
- `sensors/control/simulator` - Simulator commands (start, stop, request_config)

**Subscribes to:**
- `sensors/config/simulator` - Receives simulator configuration

### MongoDB Consumer

**Publishes to:** (none)

**Subscribes to:**
- `sensors/reading/#` - All sensor readings

### Test Subscriber

**Publishes to:** (none)

**Subscribes to:**
- `sensors/#` - All topics (for monitoring)

## Message Formats

### Sensor Reading
**Topic:** `sensors/reading/{LINE_ID}/{TYPE}/{SENSOR_ID}`

```json
{
  "sensor_id": "TEMP_001",
  "sensor_type": "temperature",
  "value": 23.45,
  "unit": "°C",
  "status": "normal",
  "timestamp": "2024-02-06T16:30:00.000Z"
}
```

### Anomaly Control Command
**Topic:** `sensors/control/anomaly`

```json
{
  "command": "start_anomaly",
  "payload": {
    "anomalyRate": 0.3,
    "sensors": ["TEMP_001_LINE_001", "VIB_007_LINE_002"]
  },
  "timestamp": "2024-02-06T16:30:00.000Z"
}
```

Commands: `start_anomaly`, `stop_anomaly`, `update_rate`, `reset_anomaly`

### Simulator Control Command
**Topic:** `sensors/control/simulator`

```json
{
  "command": "start",
  "payload": {
    "production_lines": ["LINE_001", "LINE_002"]
  },
  "timestamp": "2024-02-06T16:30:00.000Z"
}
```

Commands: `start`, `stop`, `request_config`

### Simulator Configuration
**Topic:** `sensors/config/simulator` (retained)

```json
{
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
      "temperature": ["TEMP_001", "TEMP_002", ...],
      "vibration": ["VIB_001", "VIB_002", ...],
      "hygiene": ["HYG_001", "HYG_002", ...]
    }
  },
  "timestamp": "2024-02-06T16:30:00.000Z"
}
```

## QoS Levels

All messages use **QoS 1** (at least once delivery) for reliability.

## Retained Messages

These messages are published with `retain=true` so new subscribers get the last value:
- `sensors/control/anomaly` - Last anomaly command
- `sensors/control/simulator` - Last simulator command
- `sensors/config/simulator` - Current configuration

## Permission Matrix

| User | Publish sensors/reading/> | Publish sensors/control/> | Subscribe sensors/> | Subscribe sensors/control/> | Publish sensors/config/simulator |
|------|---------------------------|---------------------------|---------------------|----------------------------|----------------------------------|
| simulator | ✅ | ❌ | ❌ | ✅ | ✅ |
| appuser | ❌ | ✅ | ✅ (config only) | ❌ | ❌ |
| consumer | ❌ | ❌ | ✅ | ❌ | ❌ |

## Solace Wildcard Syntax

Solace uses different wildcards than MQTT:

- **`>`** - Multi-level wildcard (like MQTT `#`)
  - Must be last character in topic
  - `sensors/>` matches `sensors/reading/LINE_001/temperature/TEMP_001`

- **`*`** - Single-level wildcard (like MQTT `+`)
  - Matches exactly one level
  - `sensors/*/temperature` matches `sensors/LINE_001/temperature`

- **MQTT wildcards** (`#`, `+`) work for MQTT clients
- **Solace wildcards** (`>`, `*`) used in ACL configurations

## Testing

### Test Simulator Permissions

```bash
# Should succeed - publish to sensor reading topic
mosquitto_pub -h localhost -p 1883 -u simulator -P simulator \
  -t sensors/reading/LINE_001/temperature/TEMP_001 \
  -m '{"value": 25.0}'

# Should fail - publish to control topic
mosquitto_pub -h localhost -p 1883 -u simulator -P simulator \
  -t sensors/control/anomaly \
  -m '{"test": true}'
```

### Test API Permissions

```bash
# Should succeed - publish control command
mosquitto_pub -h localhost -p 1883 -u appuser -P MyUserPassword123! \
  -t sensors/control/simulator \
  -m '{"command": "test"}'

# Should fail - publish sensor data
mosquitto_pub -h localhost -p 1883 -u appuser -P MyUserPassword123! \
  -t sensors/reading/LINE_001/temperature/TEMP_001 \
  -m '{"value": 25.0}'
```

### Test Consumer Permissions

```bash
# Should succeed - subscribe to sensor data
mosquitto_sub -h localhost -p 1883 -u consumer -P consumer \
  -t 'sensors/reading/#' -v

# Should fail - publish anything
mosquitto_pub -h localhost -p 1883 -u consumer -P consumer \
  -t sensors/test \
  -m '{"test": true}'
```

## Modifying Configuration

### Add New Topic Permission

Example: Allow simulator to publish to a new topic

```bash
curl -X POST -u admin:admin \
  -H "Content-Type: application/json" \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/aclProfiles/sensor-simulator-acl/publishTopicExceptions" \
  -d '{
    "publishTopicException": "sensors/events/>",
    "publishTopicExceptionSyntax": "smf"
  }'
```

### Change Password

```bash
curl -X PATCH -u admin:admin \
  -H "Content-Type: application/json" \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/clientUsernames/simulator" \
  -d '{
    "password": "new_secure_password"
  }'
```

### Delete Client Username

```bash
curl -X DELETE -u admin:admin \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/clientUsernames/old_user"
```

## Production Considerations

1. **Change default passwords** - Use strong, unique passwords
2. **Use TLS** - Enable SSL/TLS on port 8883
3. **IP Whitelisting** - Restrict client IP addresses
4. **Monitor connections** - Use Solace monitoring tools
5. **Audit logs** - Enable and review authentication logs
6. **Backup config** - Export configuration regularly

## SEMP v2 API Reference

Base URL: `http://localhost:8080/SEMP/v2/config`

- Create ACL Profile: `POST /msgVpns/{vpn}/aclProfiles`
- Create Client Profile: `POST /msgVpns/{vpn}/clientProfiles`
- Create Client Username: `POST /msgVpns/{vpn}/clientUsernames`
- Add Publish Exception: `POST /msgVpns/{vpn}/aclProfiles/{profile}/publishTopicExceptions`
- Add Subscribe Exception: `POST /msgVpns/{vpn}/aclProfiles/{profile}/subscribeTopicExceptions`

Authentication: HTTP Basic Auth with admin credentials

## Support

For Solace-specific questions:
- [Solace Documentation](https://docs.solace.com/)
- [Solace Community](https://solace.community/)
- [SEMP API Reference](https://docs.solace.com/API-Developer-Online-Ref-Documentation/swagger-ui/config/index.html)
