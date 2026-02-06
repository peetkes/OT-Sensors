# MongoDB User Setup Guide

This guide helps you create a MongoDB user for the sensor data consumer.

## Quick Setup (Automated)

### Option 1: Run the Setup Script

```bash
./setup_mongodb_user.sh
```

This script will:
- Create user `sensor_subscriber` with password `sensor_subscriber`
- Grant `readWrite` and `dbAdmin` roles on `iot_sensors` database
- Display the connection string to use

## Manual Setup

### Option 2: Using mongosh Command Line

```bash
mongosh -u root -p
```

Then run these commands in the MongoDB shell:

```javascript
// Switch to admin database
use admin

// Create the user
db.createUser({
  user: "sensor_subscriber",
  pwd: "sensor_subscriber",
  roles: [
    { role: "readWrite", db: "iot_sensors" },
    { role: "dbAdmin", db: "iot_sensors" }
  ]
})

// Verify the user was created
db.getUser("sensor_subscriber")

// Exit
exit
```

### Option 3: Using JavaScript File

```bash
mongosh -u root -p < setup_mongodb_user.js
```

## Update MongoDB Consumer

After creating the user, update [mongodb_consumer.py](mongodb_consumer.py):

```python
MONGODB_USERNAME = "sensor_subscriber"
MONGODB_PASSWORD = "sensor_subscriber"
MONGODB_URI = f"mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@localhost:27017/?authSource=admin"
```

Or directly:
```python
MONGODB_URI = "mongodb://sensor_subscriber:sensor_subscriber@localhost:27017/?authSource=admin"
```

## Verify Connection

Test the connection:

```bash
mongosh "mongodb://sensor_subscriber:sensor_subscriber@localhost:27017/?authSource=admin"
```

If successful, you'll see:
```
Current Mongosh Log ID: ...
Connecting to: mongodb://sensor_subscriber@localhost:27017/?authSource=admin
Using MongoDB: 7.x.x
```

## Troubleshooting

### Error: "Authentication failed"

**Cause:** Wrong password or authSource

**Fix:**
```bash
# Check where user was created
mongosh -u root -p
> use admin
> db.getUser("sensor_subscriber")
```

Look for the `db` field in the user object - use that database name in `authSource`.

### Error: "not authorized on iot_sensors"

**Cause:** Missing permissions

**Fix:** Grant additional roles
```bash
mongosh -u root -p
> use admin
> db.grantRolesToUser("sensor_subscriber", [
    { role: "readWrite", db: "iot_sensors" },
    { role: "dbAdmin", db: "iot_sensors" }
  ])
```

### User Already Exists

If you get "User already exists", update the existing user:

```javascript
use admin
db.updateUser("sensor_subscriber", {
  pwd: "sensor_subscriber",
  roles: [
    { role: "readWrite", db: "iot_sensors" },
    { role: "dbAdmin", db: "iot_sensors" }
  ]
})
```

Or drop and recreate:
```javascript
use admin
db.dropUser("sensor_subscriber")
// Then run createUser again
```

## Roles Explained

- **`readWrite`**: Allows reading and writing documents (insert, update, delete, find)
- **`dbAdmin`**: Allows database admin tasks (creating indexes, managing collections)

These are the minimum required roles for the MongoDB consumer to function properly.

## Security Best Practices

1. **Change the default password** in production environments
2. Use strong passwords (16+ characters, mixed case, numbers, symbols)
3. Consider using environment variables instead of hardcoding credentials
4. Use TLS/SSL for MongoDB connections in production
5. Restrict MongoDB network access with firewall rules

## Production Password Example

```javascript
db.updateUser("sensor_subscriber", {
  pwd: "Tr0ng!P@ssw0rd#2026_Sens0r$"
})
```

Then update your connection string accordingly.
