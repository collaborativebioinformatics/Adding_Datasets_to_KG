#!/bin/bash

# Load full dataset using Neptune bulk loader
# This script loads all nodes and edges using the fast bulk loading approach

set -e

# Configuration
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION="us-east-1"
CLUSTER_ENDPOINT="midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com"
ROLE_NAME="NeptuneLoadRole"
BUCKET_NAME="251001-midas-test"

echo "=== Neptune Bulk Loading Script ==="
echo "Account ID: $ACCOUNT_ID"
echo "Region: $REGION"
echo "Cluster: $CLUSTER_ENDPOINT"
echo ""

# Step 1: Convert full dataset
echo "Step 1: Converting full dataset to Neptune format..."
python3 scripts/preprocessing/convert_for_neptune_bulk.py --input data/nodes.temp_csv --output data/nodes_full.csv --type nodes
python3 scripts/preprocessing/convert_for_neptune_bulk.py --input data/edges.temp_csv --output data/edges_full.csv --type edges

echo "Conversion complete!"
echo ""

# Step 2: Upload to S3
echo "Step 2: Uploading files to S3..."
aws s3 cp data/nodes_full.csv s3://$BUCKET_NAME/neptune-full/nodes.csv
aws s3 cp data/edges_full.csv s3://$BUCKET_NAME/neptune-full/edges.csv

echo "Upload complete!"
echo ""

# Step 3: Load nodes
echo "Step 3: Loading nodes..."
NODE_LOAD_RESPONSE=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/loader" \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"s3://$BUCKET_NAME/neptune-full/nodes.csv\",
    \"format\": \"opencypher\",
    \"iamRoleArn\": \"arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME\",
    \"region\": \"$REGION\",
    \"failOnError\": \"FALSE\",
    \"parallelism\": \"HIGH\",
    \"updateSingleCardinalityProperties\": \"FALSE\",
    \"queueRequest\": \"TRUE\"
  }")

echo "Node load response: $NODE_LOAD_RESPONSE"

NODE_LOAD_ID=$(echo $NODE_LOAD_RESPONSE | jq -r '.payload.loadId // empty')

if [ -n "$NODE_LOAD_ID" ]; then
    echo "Node load started with ID: $NODE_LOAD_ID"
    echo "Monitoring node load progress..."
    
    # Monitor node load progress
    while true; do
        STATUS_RESPONSE=$(awscurl --service neptune-db --region $REGION \
          -X GET "https://$CLUSTER_ENDPOINT:8182/loader/$NODE_LOAD_ID")
        
        STATUS=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.status // empty')
        RECORDS_LOADED=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.totalRecords // 0')
        RECORDS_FAILED=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.totalRecordsFailed // 0')
        
        echo "Node load status: $STATUS, Records loaded: $RECORDS_LOADED, Failed: $RECORDS_FAILED"
        
        if [ "$STATUS" = "LOAD_COMPLETED" ]; then
            echo "Node loading completed successfully!"
            break
        elif [ "$STATUS" = "LOAD_FAILED" ]; then
            echo "Node loading failed!"
            echo "Error details: $STATUS_RESPONSE"
            exit 1
        fi
        
        sleep 10
    done
else
    echo "Failed to start node load. Response: $NODE_LOAD_RESPONSE"
    exit 1
fi

echo ""

# Step 4: Load edges
echo "Step 4: Loading edges..."
EDGE_LOAD_RESPONSE=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/loader" \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"s3://$BUCKET_NAME/neptune-full/edges.csv\",
    \"format\": \"opencypher\",
    \"iamRoleArn\": \"arn:aws:iam::$ACCOUNT_ID:role/$ROLE_NAME\",
    \"region\": \"$REGION\",
    \"failOnError\": \"FALSE\",
    \"parallelism\": \"HIGH\",
    \"updateSingleCardinalityProperties\": \"FALSE\",
    \"queueRequest\": \"TRUE\",
    \"userProvidedEdgeIds\": \"FALSE\"
  }")

echo "Edge load response: $EDGE_LOAD_RESPONSE"

EDGE_LOAD_ID=$(echo $EDGE_LOAD_RESPONSE | jq -r '.payload.loadId // empty')

if [ -n "$EDGE_LOAD_ID" ]; then
    echo "Edge load started with ID: $EDGE_LOAD_ID"
    echo "Monitoring edge load progress..."
    
    # Monitor edge load progress
    while true; do
        STATUS_RESPONSE=$(awscurl --service neptune-db --region $REGION \
          -X GET "https://$CLUSTER_ENDPOINT:8182/loader/$EDGE_LOAD_ID")
        
        STATUS=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.status // empty')
        RECORDS_LOADED=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.totalRecords // 0')
        RECORDS_FAILED=$(echo $STATUS_RESPONSE | jq -r '.payload.overallStatus.totalRecordsFailed // 0')
        
        echo "Edge load status: $STATUS, Records loaded: $RECORDS_LOADED, Failed: $RECORDS_FAILED"
        
        if [ "$STATUS" = "LOAD_COMPLETED" ]; then
            echo "Edge loading completed successfully!"
            break
        elif [ "$STATUS" = "LOAD_FAILED" ]; then
            echo "Edge loading failed!"
            echo "Error details: $STATUS_RESPONSE"
            exit 1
        fi
        
        sleep 10
    done
else
    echo "Failed to start edge load. Response: $EDGE_LOAD_RESPONSE"
    exit 1
fi

echo ""
echo "=== Data Loading Complete ==="
echo "Verifying counts..."

# Verify final counts
NODE_COUNT=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as count"}' | jq -r '.results[0].count')

EDGE_COUNT=$(awscurl --service neptune-db --region $REGION \
  -X POST "https://$CLUSTER_ENDPOINT:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH ()-[r]->() RETURN count(r) as count"}' | jq -r '.results[0].count')

echo "Total nodes loaded: $NODE_COUNT"
echo "Total edges loaded: $EDGE_COUNT"

