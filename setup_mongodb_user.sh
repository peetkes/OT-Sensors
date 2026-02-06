#!/bin/bash
# MongoDB User Setup Script
# Creates a sensor_subscriber user with read/write permissions for iot_sensors database

set -e  # Exit on error

echo "=========================================="
echo "MongoDB User Setup"
echo "=========================================="
echo ""
echo "This script will create a MongoDB user:"
echo "  Username: sensor_subscriber"
echo "  Password: sensor_subscriber"
echo "  Database: iot_sensors"
echo "  Permissions: readWrite + dbAdmin"
echo ""
echo "⚠️  Change the default password in production!"
echo ""

# Check if mongosh is available
if ! command -v mongosh &> /dev/null; then
    echo "Error: mongosh command not found"
    echo "Please install MongoDB Shell: https://www.mongodb.com/try/download/shell"
    exit 1
fi

# Prompt for root/admin credentials
echo "Enter MongoDB root/admin username (default: root):"
read -r MONGO_ROOT_USER
MONGO_ROOT_USER=${MONGO_ROOT_USER:-root}

echo "Enter MongoDB root/admin password:"
read -s MONGO_ROOT_PASS
echo ""

# Create the user using mongosh
echo "Creating user..."
mongosh -u "$MONGO_ROOT_USER" -p "$MONGO_ROOT_PASS" --authenticationDatabase admin --quiet --eval '
use admin

// Check if user already exists
const existingUser = db.getUser("sensor_subscriber");
if (existingUser) {
    print("⚠️  User sensor_subscriber already exists. Updating roles...");
    db.updateUser("sensor_subscriber", {
        roles: [
            { role: "readWrite", db: "iot_sensors" },
            { role: "dbAdmin", db: "iot_sensors" }
        ]
    });
    print("✓ User roles updated successfully");
} else {
    // Create new user
    db.createUser({
        user: "sensor_subscriber",
        pwd: "sensor_subscriber",
        roles: [
            { role: "readWrite", db: "iot_sensors" },
            { role: "dbAdmin", db: "iot_sensors" }
        ]
    });
    print("✓ User sensor_subscriber created successfully");
}

print("");
print("User permissions:");
db.getUser("sensor_subscriber").roles.forEach(role => {
    print(`  - ${role.role} on ${role.db}`);
});
'

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ Setup Complete!"
    echo "=========================================="
    echo ""
    echo "MongoDB Connection String:"
    echo "mongodb://sensor_subscriber:sensor_subscriber@localhost:27017/?authSource=admin"
    echo ""
    echo "Update mongodb_consumer.py with:"
    echo "  MONGODB_USERNAME = \"sensor_subscriber\""
    echo "  MONGODB_PASSWORD = \"sensor_subscriber\""
    echo "  MONGODB_URI = \"mongodb://sensor_subscriber:sensor_subscriber@localhost:27017/?authSource=admin\""
    echo ""
    echo "⚠️  IMPORTANT: Change the default password in production!"
    echo ""
else
    echo ""
    echo "❌ Setup failed. Please check the error messages above."
    exit 1
fi
