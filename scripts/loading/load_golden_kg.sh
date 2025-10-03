#!/bin/bash

################################################################################
# Load goldenKG dataset to Neptune using bulk loader
#
# This script:
# 1. Uploads goldenKG nodes and edges to S3
# 2. Initiates Neptune bulk loading for nodes
# 3. Monitors node loading progress
# 4. Initiates Neptune bulk loading for edges
# 5. Monitors edge loading progress
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Parse command line arguments
SKIP_CONFIRM=false
if [ "$1" = "--yes" ] || [ "$1" = "-y" ]; then
    SKIP_CONFIRM=true
fi

# Configuration from neptune_config.env
NEPTUNE_ENDPOINT="midas-dev-2510021802.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com"
REGION="us-east-1"
S3_BUCKET="neptune-midas-dev-2510021802-989002774737"
IAM_ROLE_ARN="arn:aws:iam::989002774737:role/NeptuneS3LoadRole-midas-dev-2510021802"

# Data paths
NODES_FILE="data_output/kgs/goldenKG/goldenKG_nodes_fixed.csv"
EDGES_FILE="data_output/kgs/goldenKG/goldenKG_edges_fixed.csv"

# S3 paths
S3_PREFIX="goldenKG"
S3_NODES_PATH="s3://$S3_BUCKET/$S3_PREFIX/nodes.csv"
S3_EDGES_PATH="s3://$S3_BUCKET/$S3_PREFIX/edges.csv"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
log_info "Checking prerequisites..."

if ! command -v awscurl &> /dev/null; then
    log_error "awscurl is required but not installed. Install it with: pip install awscurl"
    exit 1
fi

if ! command -v jq &> /dev/null; then
    log_error "jq is required but not installed. Install it with: sudo apt-get install jq"
    exit 1
fi

if [ ! -f "$NODES_FILE" ]; then
    log_error "Nodes file not found: $NODES_FILE"
    exit 1
fi

if [ ! -f "$EDGES_FILE" ]; then
    log_error "Edges file not found: $EDGES_FILE"
    exit 1
fi

log_success "Prerequisites check passed"
echo ""

# Display summary
echo "================================================"
echo "Neptune Bulk Load Configuration"
echo "================================================"
echo "Cluster:     $NEPTUNE_ENDPOINT"
echo "Region:      $REGION"
echo "S3 Bucket:   $S3_BUCKET"
echo "IAM Role:    $IAM_ROLE_ARN"
echo ""
echo "Source Files:"
echo "  Nodes:     $NODES_FILE"
echo "  Edges:     $EDGES_FILE"
echo ""
echo "S3 Destinations:"
echo "  Nodes:     $S3_NODES_PATH"
echo "  Edges:     $S3_EDGES_PATH"
echo "================================================"
echo ""

# Count records
log_info "Counting records in source files..."
NODE_COUNT=$(wc -l < "$NODES_FILE")
EDGE_COUNT=$(wc -l < "$EDGES_FILE")
log_info "Nodes: $(($NODE_COUNT - 1)) (excluding header)"
log_info "Edges: $(($EDGE_COUNT - 1)) (excluding header)"
echo ""

# Confirm
if [ "$SKIP_CONFIRM" = false ]; then
    read -p "Do you want to proceed with the load? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        log_info "Operation cancelled."
        exit 0
    fi
fi

echo ""

# Step 1: Upload to S3
log_info "Step 1: Uploading files to S3..."
aws s3 cp "$NODES_FILE" "$S3_NODES_PATH" --region "$REGION"
aws s3 cp "$EDGES_FILE" "$S3_EDGES_PATH" --region "$REGION"
log_success "Files uploaded to S3"
echo ""

# Step 2: Load nodes
log_info "Step 2: Loading nodes..."
NODE_LOAD_RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
  -X POST "https://$NEPTUNE_ENDPOINT:8182/loader" \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"$S3_NODES_PATH\",
    \"format\": \"opencypher\",
    \"iamRoleArn\": \"$IAM_ROLE_ARN\",
    \"region\": \"$REGION\",
    \"failOnError\": \"FALSE\",
    \"parallelism\": \"HIGH\",
    \"updateSingleCardinalityProperties\": \"FALSE\",
    \"queueRequest\": \"TRUE\"
  }")

echo "Node load response: $NODE_LOAD_RESPONSE"
NODE_LOAD_ID=$(echo "$NODE_LOAD_RESPONSE" | jq -r '.payload.loadId // empty')

if [ -z "$NODE_LOAD_ID" ]; then
    log_error "Failed to start node load"
    log_error "Response: $NODE_LOAD_RESPONSE"
    exit 1
fi

log_success "Node load started with ID: $NODE_LOAD_ID"
log_info "Monitoring node load progress..."
echo ""

# Monitor node load
while true; do
    STATUS_RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
      -X GET "https://$NEPTUNE_ENDPOINT:8182/loader/$NODE_LOAD_ID")
    
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.status // empty')
    RECORDS_LOADED=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.totalRecords // 0')
    RECORDS_FAILED=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.totalRecordsFailed // 0')
    
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} Status: $STATUS | Loaded: $RECORDS_LOADED | Failed: $RECORDS_FAILED"
    
    if [ "$STATUS" = "LOAD_COMPLETED" ]; then
        log_success "Node loading completed!"
        log_success "Total records loaded: $RECORDS_LOADED"
        if [ "$RECORDS_FAILED" != "0" ]; then
            log_warning "Records failed: $RECORDS_FAILED"
        fi
        break
    elif [ "$STATUS" = "LOAD_FAILED" ]; then
        log_error "Node loading failed!"
        echo "Error details:"
        echo "$STATUS_RESPONSE" | jq '.payload.overallStatus'
        exit 1
    fi
    
    sleep 10
done

echo ""

# Step 3: Load edges
log_info "Step 3: Loading edges..."
EDGE_LOAD_RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
  -X POST "https://$NEPTUNE_ENDPOINT:8182/loader" \
  -H "Content-Type: application/json" \
  -d "{
    \"source\": \"$S3_EDGES_PATH\",
    \"format\": \"opencypher\",
    \"iamRoleArn\": \"$IAM_ROLE_ARN\",
    \"region\": \"$REGION\",
    \"failOnError\": \"FALSE\",
    \"parallelism\": \"HIGH\",
    \"updateSingleCardinalityProperties\": \"FALSE\",
    \"queueRequest\": \"TRUE\",
    \"userProvidedEdgeIds\": \"FALSE\"
  }")

echo "Edge load response: $EDGE_LOAD_RESPONSE"
EDGE_LOAD_ID=$(echo "$EDGE_LOAD_RESPONSE" | jq -r '.payload.loadId // empty')

if [ -z "$EDGE_LOAD_ID" ]; then
    log_error "Failed to start edge load"
    log_error "Response: $EDGE_LOAD_RESPONSE"
    exit 1
fi

log_success "Edge load started with ID: $EDGE_LOAD_ID"
log_info "Monitoring edge load progress..."
echo ""

# Monitor edge load
while true; do
    STATUS_RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
      -X GET "https://$NEPTUNE_ENDPOINT:8182/loader/$EDGE_LOAD_ID")
    
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.status // empty')
    RECORDS_LOADED=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.totalRecords // 0')
    RECORDS_FAILED=$(echo "$STATUS_RESPONSE" | jq -r '.payload.overallStatus.totalRecordsFailed // 0')
    
    echo -e "${BLUE}[$(date +%H:%M:%S)]${NC} Status: $STATUS | Loaded: $RECORDS_LOADED | Failed: $RECORDS_FAILED"
    
    if [ "$STATUS" = "LOAD_COMPLETED" ]; then
        log_success "Edge loading completed!"
        log_success "Total records loaded: $RECORDS_LOADED"
        if [ "$RECORDS_FAILED" != "0" ]; then
            log_warning "Records failed: $RECORDS_FAILED"
        fi
        break
    elif [ "$STATUS" = "LOAD_FAILED" ]; then
        log_error "Edge loading failed!"
        echo "Error details:"
        echo "$STATUS_RESPONSE" | jq '.payload.overallStatus'
        exit 1
    fi
    
    sleep 10
done

echo ""
echo "================================================"
log_success "goldenKG load completed successfully!"
echo "================================================"
echo ""
echo "Node Load ID: $NODE_LOAD_ID"
echo "Edge Load ID: $EDGE_LOAD_ID"
echo ""
echo "You can query your graph using:"
echo "  Cluster: $NEPTUNE_ENDPOINT"
echo "  Port: 8182"
echo "================================================"

