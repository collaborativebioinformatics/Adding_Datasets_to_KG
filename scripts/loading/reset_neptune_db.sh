#!/bin/bash

# Reset Neptune database using the system endpoint
# This is the FAST method that actually works for large datasets
# WARNING: This will delete ALL data from the database!

set -e

# Configuration
REGION="us-east-1"
CLUSTER_ENDPOINT="midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com"

echo "=== Neptune Database Reset Script ==="
echo "Cluster: $CLUSTER_ENDPOINT"
echo ""
echo "WARNING: This will delete ALL data from the Neptune database!"
echo "This operation uses the system endpoint for fast database reset."
read -p "Are you sure you want to continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Step 1: Initiating database reset..."

# Initiate database reset and get token
RESPONSE=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/system" \
  -H 'Content-Type: application/json' \
  -d '{"action": "initiateDatabaseReset"}')

echo "Response: $RESPONSE"

# Extract token from response using jq
TOKEN=$(echo "$RESPONSE" | jq -r '.payload.token')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
    echo "ERROR: Failed to get reset token from response"
    echo "Response was: $RESPONSE"
    exit 1
fi

echo "Reset token received: ${TOKEN:0:20}..."
echo ""
echo "Step 2: Performing database reset with token..."

# Perform the actual reset
RESET_RESPONSE=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/system" \
  -H 'Content-Type: application/json' \
  -d "{\"action\": \"performDatabaseReset\", \"token\": \"$TOKEN\"}")

echo "Reset response: $RESET_RESPONSE"
echo ""

# Wait for reset to complete
echo "Waiting for reset to complete..."
sleep 10

# Verify the database is empty
echo "Verifying database is empty..."

NODE_COUNT=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as count"}' | jq -r '.results[0].count')

EDGE_COUNT=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH ()-[r]->() RETURN count(r) as count"}' | jq -r '.results[0].count')

echo "Current nodes: $NODE_COUNT"
echo "Current edges: $EDGE_COUNT"

if [ "$NODE_COUNT" = "0" ] && [ "$EDGE_COUNT" = "0" ]; then
    echo ""
    echo "=== Database Successfully Reset ==="
    echo ""
    echo "The database is now empty and ready for data loading."
    echo "To load data, run: bash scripts/loading/load_full_dataset_bulk.sh"
else
    echo ""
    echo "WARNING: Database may not be completely cleared!"
    echo "Nodes remaining: $NODE_COUNT"
    echo "Edges remaining: $EDGE_COUNT"
    exit 1
fi


