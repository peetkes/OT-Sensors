#!/bin/bash
# Apply Solace Broker Configuration via SEMP v2 API
# This script creates ACL profiles, client profiles, and client usernames

set -e

# Configuration
SOLACE_SEMP_URL="http://localhost:8080/SEMP/v2/config"
SOLACE_ADMIN_USER="admin"
SOLACE_ADMIN_PASS="admin"
MSG_VPN="default"

# Color output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo "=========================================="
echo "Solace Broker Configuration Setup"
echo "=========================================="
echo ""
echo "SEMP URL: $SOLACE_SEMP_URL"
echo "Message VPN: $MSG_VPN"
echo ""

# Function to make SEMP request
semp_request() {
    local method=$1
    local endpoint=$2
    local data=$3

    curl -s -w "\n%{http_code}" -X "$method" \
        -u "$SOLACE_ADMIN_USER:$SOLACE_ADMIN_PASS" \
        -H "Content-Type: application/json" \
        "$SOLACE_SEMP_URL/$endpoint" \
        ${data:+-d "$data"}
}

# Parse response
parse_response() {
    local response=$1
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    echo "$http_code|$body"
}

echo "Step 1: Creating ACL Profiles"
echo "==============================="

# Create sensor-simulator-acl
echo -n "ACL Profile: sensor-simulator-acl ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/aclProfiles" '{"aclProfileName":"sensor-simulator-acl","clientConnectDefaultAction":"allow","publishTopicDefaultAction":"disallow","subscribeTopicDefaultAction":"disallow"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)
body=$(echo "$result" | cut -d'|' -f2-)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"

    # Add publish exceptions
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/sensor-simulator-acl/publishTopicExceptions" '{"publishTopicException":"sensors/reading/>","publishTopicExceptionSyntax":"smf"}' > /dev/null
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/sensor-simulator-acl/publishTopicExceptions" '{"publishTopicException":"sensors/config/simulator","publishTopicExceptionSyntax":"smf"}' > /dev/null

    # Add subscribe exceptions
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/sensor-simulator-acl/subscribeTopicExceptions" '{"subscribeTopicException":"sensors/control/anomaly","subscribeTopicExceptionSyntax":"smf"}' > /dev/null
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/sensor-simulator-acl/subscribeTopicExceptions" '{"subscribeTopicException":"sensors/control/simulator","subscribeTopicExceptionSyntax":"smf"}' > /dev/null
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗ (HTTP $http_code)${NC}"
    echo "$body" | jq -r '.meta.error.description' 2>/dev/null || echo "$body"
fi

# Create api-controller-acl
echo -n "ACL Profile: api-controller-acl ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/aclProfiles" '{"aclProfileName":"api-controller-acl","clientConnectDefaultAction":"allow","publishTopicDefaultAction":"disallow","subscribeTopicDefaultAction":"disallow"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/api-controller-acl/publishTopicExceptions" '{"publishTopicException":"sensors/control/>","publishTopicExceptionSyntax":"smf"}' > /dev/null
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/api-controller-acl/subscribeTopicExceptions" '{"subscribeTopicException":"sensors/config/simulator","subscribeTopicExceptionSyntax":"smf"}' > /dev/null
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Create consumer-acl
echo -n "ACL Profile: consumer-acl ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/aclProfiles" '{"aclProfileName":"consumer-acl","clientConnectDefaultAction":"allow","publishTopicDefaultAction":"disallow","subscribeTopicDefaultAction":"disallow"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
    semp_request POST "msgVpns/$MSG_VPN/aclProfiles/consumer-acl/subscribeTopicExceptions" '{"subscribeTopicException":"sensors/>","subscribeTopicExceptionSyntax":"smf"}' > /dev/null
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "Step 2: Creating Client Profiles"
echo "=================================="

# sensor-simulator-profile
echo -n "Client Profile: sensor-simulator-profile ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientProfiles" '{"clientProfileName":"sensor-simulator-profile","allowGuaranteedMsgSendEnabled":true,"allowGuaranteedMsgReceiveEnabled":true,"allowGuaranteedEndpointCreateEnabled":true,"allowGuaranteedEndpointCreateDurability":"non-durable","maxConnectionCountPerClientUsername":10,"maxSubscriptionCount":500}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# api-controller-profile
echo -n "Client Profile: api-controller-profile ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientProfiles" '{"clientProfileName":"api-controller-profile","allowGuaranteedMsgSendEnabled":true,"allowGuaranteedMsgReceiveEnabled":true,"allowGuaranteedEndpointCreateEnabled":true,"allowGuaranteedEndpointCreateDurability":"non-durable","maxConnectionCountPerClientUsername":5,"maxSubscriptionCount":50}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# consumer-profile
echo -n "Client Profile: consumer-profile ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientProfiles" '{"clientProfileName":"consumer-profile","allowGuaranteedMsgSendEnabled":false,"allowGuaranteedMsgReceiveEnabled":true,"allowGuaranteedEndpointCreateEnabled":true,"allowGuaranteedEndpointCreateDurability":"non-durable","maxConnectionCountPerClientUsername":10,"maxSubscriptionCount":1000}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "Step 3: Creating Client Usernames"
echo "==================================="

# simulator user
echo -n "Client Username: simulator ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientUsernames" '{"clientUsername":"simulator","enabled":true,"password":"simulator","aclProfileName":"sensor-simulator-acl","clientProfileName":"sensor-simulator-profile"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# appuser
echo -n "Client Username: appuser ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientUsernames" '{"clientUsername":"appuser","enabled":true,"password":"MyUserPassword123!","aclProfileName":"api-controller-acl","clientProfileName":"api-controller-profile"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# consumer user
echo -n "Client Username: consumer ... "
response=$(semp_request POST "msgVpns/$MSG_VPN/clientUsernames" '{"clientUsername":"consumer","enabled":true,"password":"consumer","aclProfileName":"consumer-acl","clientProfileName":"consumer-profile"}')
result=$(parse_response "$response")
http_code=$(echo "$result" | cut -d'|' -f1)

if [ "$http_code" = "200" ]; then
    echo -e "${GREEN}✓${NC}"
elif echo "$body" | grep -q "already exists"; then
    echo -e "${YELLOW}Already exists${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}Configuration Complete!${NC}"
echo "=========================================="
echo ""
echo "Client Usernames:"
echo "  - simulator / simulator (Sensor Simulator)"
echo "  - appuser / MyUserPassword123! (API Controller)"
echo "  - consumer / consumer (Data Consumers)"
echo ""
echo "Topic Permissions:"
echo "  simulator: Publish sensors/reading/>, sensors/config/simulator"
echo "  appuser:   Publish sensors/control/>"
echo "  consumer:  Subscribe sensors/>"
echo ""
