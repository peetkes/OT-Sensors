# Solace Broker Configuration (SEMP v2)

This directory contains configuration files for setting up proper authentication and authorization on your Solace PubSub+ broker.

## Overview

The configuration creates three types of users with different permissions:

| Username | Password | Role | Publish Topics | Subscribe Topics |
|----------|----------|------|----------------|------------------|
| `simulator` | `simulator` | Sensor Simulator | `sensors/reading/>`, `sensors/config/simulator` | `sensors/control/anomaly`, `sensors/control/simulator` |
| `appuser` | `MyUserPassword123!` | API Controller | `sensors/control/>` | `sensors/config/simulator` |
| `consumer` | `consumer` | Data Consumers | (none) | `sensors/>` (all sensor topics) |

## Quick Start

### 1. Ensure Solace Broker is Running

```bash
docker ps | grep solace
# or
docker-compose up -d
```

### 2. Apply Configuration

```bash
cd solace-config
./apply-config.sh
```

This will:
- Create 3 ACL profiles
- Create 3 client profiles
- Create 3 client usernames
- Display results for each step

### 3. Update Application Credentials

After applying the configuration, update your applications:

**sensor_simulator.py:**
```python
BROKER_HOST = "localhost"
USERNAME = "simulator"
PASSWORD = "simulator"
```

**api/.env:**
```env
MQTT_USERNAME=appuser
MQTT_PASSWORD=MyUserPassword123!
```

**mongodb_consumer.py:**
```python
MQTT_USERNAME = "consumer"
MQTT_PASSWORD = "consumer"
```

## Configuration Files

### 1. ACL Profiles ([acl-profiles.json](acl-profiles.json))

Defines publish/subscribe permissions for topics.

#### sensor-simulator-acl
- **Publish**: `sensors/reading/>` (all sensor readings), `sensors/config/simulator` (configuration)
- **Subscribe**: `sensors/control/anomaly`, `sensors/control/simulator` (command topics)

#### api-controller-acl
- **Publish**: `sensors/control/>` (all control commands)
- **Subscribe**: `sensors/config/simulator` (simulator configuration)

#### consumer-acl
- **Publish**: (none - read-only)
- **Subscribe**: `sensors/>` (all sensor data)

### 2. Client Profiles ([client-profiles.json](client-profiles.json))

Defines connection limits and messaging capabilities.

#### sensor-simulator-profile
- Max connections: 10 (supports multiple simulator instances)
- Guaranteed messaging: Enabled (QoS 1)
- Max subscriptions: 500

#### api-controller-profile
- Max connections: 5
- Guaranteed messaging: Enabled
- Max subscriptions: 50

#### consumer-profile
- Max connections: 10 (supports multiple consumers)
- Guaranteed messaging: Receive only
- Max subscriptions: 1000 (for wildcards)

### 3. Client Usernames ([client-usernames.json](client-usernames.json))

Links usernames to profiles.

Each username is assigned:
- An ACL profile (topic permissions)
- A client profile (connection limits)
- A password

## Manual Configuration via Solace Manager

If you prefer to configure via the web UI:

1. Open Solace Manager: http://localhost:8080
2. Login with: `admin` / `admin`
3. Navigate to your Message VPN (usually `default`)

### Create ACL Profiles

1. Go to **Access Control** → **ACL Profiles**
2. Click **+ ACL Profile**
3. For each profile:
   - Name: `sensor-simulator-acl`, `api-controller-acl`, `consumer-acl`
   - Add **Publish Topic Exceptions** (allowlist)
   - Add **Subscribe Topic Exceptions** (allowlist)

### Create Client Profiles

1. Go to **Access Control** → **Client Profiles**
2. Click **+ Client Profile**
3. Configure limits per the JSON files

### Create Client Usernames

1. Go to **Access Control** → **Client Usernames**
2. Click **+ Client Username**
3. For each user:
   - Username and password
   - Select ACL profile
   - Select client profile
   - Enable the user

## Topic Permissions Explained

### Solace Topic Syntax

- `>` - Multi-level wildcard (matches everything after)
  - `sensors/>` matches `sensors/reading/LINE_001/temperature/TEMP_001`
- `/` - Topic level separator
- No single-level wildcard in Solace SMF (use `>` for flexibility)

### Why These Permissions?

**Simulator needs**:
- Publish sensor data: `sensors/reading/>` covers all lines/types/sensors
- Publish config: `sensors/config/simulator`
- Receive commands: Subscribe to control topics

**API needs**:
- Send commands: `sensors/control/>` covers anomaly and simulator controls
- Receive config: Subscribe to `sensors/config/simulator`

**Consumers need**:
- Receive all data: `sensors/>` covers readings, config, everything

## Troubleshooting

### "Already exists" errors

The script will show "Already exists" if resources are already configured. This is normal on re-runs.

### Authentication failed

Check:
1. Credentials in client-usernames.json match your app configurations
2. Users are **enabled** (`"enabled": true`)
3. Message VPN name matches (default is `default`)

### Permission denied errors

Check ACL profiles:
- Publish exceptions allow the topics you're publishing to
- Subscribe exceptions allow the topics you're subscribing to
- Use `>` wildcard appropriately

### Testing Permissions

Use `mqtt-spy` or command-line tools:

```bash
# Test simulator user
mosquitto_pub -h localhost -p 1883 \
  -u simulator -P simulator \
  -t sensors/reading/LINE_001/test \
  -m '{"test": true}'

# Test API user
mosquitto_pub -h localhost -p 1883 \
  -u appuser -P MyUserPassword123! \
  -t sensors/control/simulator \
  -m '{"command": "test"}'

# Test consumer user
mosquitto_sub -h localhost -p 1883 \
  -u consumer -P consumer \
  -t 'sensors/#' -v
```

## Security Best Practices

1. **Change default passwords** before production deployment
2. **Use TLS/SSL** for MQTT connections (port 8883)
3. **Restrict IP access** using Solace firewall rules
4. **Regular audit** of client usernames and permissions
5. **Principle of least privilege**: Only grant necessary permissions

## Advanced Configuration

### Enable TLS

Update client profiles to require TLS:
```json
{
  "tlsEnabled": true
}
```

### Add Publish/Subscribe Exception

Via SEMP v2:
```bash
# Add subscribe exception to existing ACL profile
curl -X POST -u admin:admin \
  -H "Content-Type: application/json" \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/aclProfiles/consumer-acl/subscribeTopicExceptions" \
  -d '{
    "subscribeTopicException": "sensors/alerts/>",
    "subscribeTopicExceptionSyntax": "smf"
  }'
```

### View Current Configuration

```bash
# List all client usernames
curl -u admin:admin \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/clientUsernames"

# Get specific ACL profile
curl -u admin:admin \
  "http://localhost:8080/SEMP/v2/config/msgVpns/default/aclProfiles/sensor-simulator-acl"
```

## Files

- `acl-profiles.json` - Topic access control lists
- `client-profiles.json` - Connection and messaging limits
- `client-usernames.json` - User credentials and profile assignments
- `apply-config.sh` - Automated setup script
- `README.md` - This file

## References

- [Solace SEMP v2 Documentation](https://docs.solace.com/Admin/SEMP/Using-SEMP.htm)
- [ACL Profile Configuration](https://docs.solace.com/Security/Configuring-ACLs.htm)
- [Client Authentication](https://docs.solace.com/Security/Client-Authentication.htm)
