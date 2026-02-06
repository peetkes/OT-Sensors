// MongoDB User Setup Script
// Creates a user for the sensor data consumer with read/write permissions
//
// Usage:
//   mongosh -u root -p < setup_mongodb_user.js
//   OR
//   mongosh -u root -p
//   > load('setup_mongodb_user.js')

// Switch to admin database to create the user
use admin

// Create the sensor_subscriber user
db.createUser({
  user: "sensor_subscriber",
  pwd: "sensor_subscriber",  // Change this password in production!
  roles: [
    {
      role: "readWrite",
      db: "iot_sensors"  // Database name (matches mongodb_consumer.py)
    },
    {
      role: "dbAdmin",
      db: "iot_sensors"  // Allows creating indexes
    }
  ]
})

print("✓ User 'sensor_subscriber' created successfully")
print("")
print("User details:")
db.getUser("sensor_subscriber")

print("")
print("Connection string to use:")
print("mongodb://sensor_subscriber:sensor_subscriber@localhost:27017/?authSource=admin")
print("")
print("⚠️  IMPORTANT: Change the default password in production!")
