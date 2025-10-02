#!/bin/bash

################################################################################
# Neptune Management Script
#
# This script provides management operations for Neptune infrastructure:
# - Start/Stop instances
# - Check status
# - Get connection information
# - Modify instance sizes
#
# Usage:
#   ./manage_neptune.sh [command] [options]
#
# Commands:
#   status              Show cluster and instance status
#   start               Start Neptune instance
#   stop                Stop Neptune instance
#   restart             Restart Neptune instance
#   info                Display connection information
#   modify              Modify instance class
#   list-loads          List bulk load jobs
#   check-load          Check status of a specific load job
#
# Options:
#   --cluster-name      Neptune cluster identifier (default: midas-dev)
#   --instance-name     Neptune instance identifier (default: midas-dev-instance-1)
#   --region            AWS region (default: us-east-1)
#   --instance-class    New instance class for modify command
#   --load-id           Load job ID for check-load command
#   --help              Show this help message
#
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# Default values
CLUSTER_NAME="midas-dev"
INSTANCE_NAME="midas-dev-instance-1"
REGION="us-east-1"

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

show_help() {
    sed -n '/^# Usage:/,/^####/p' "$0" | sed 's/^# //g' | head -n -1
}

# Parse command
if [ $# -eq 0 ]; then
    log_error "No command specified"
    show_help
    exit 1
fi

COMMAND=$1
shift

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --instance-name)
            INSTANCE_NAME="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --instance-class)
            NEW_INSTANCE_CLASS="$2"
            shift 2
            ;;
        --load-id)
            LOAD_ID="$2"
            shift 2
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to get cluster status
get_cluster_status() {
    aws neptune describe-db-clusters \
        --db-cluster-identifier "$CLUSTER_NAME" \
        --region "$REGION" \
        --output json 2>/dev/null || echo "{}"
}

# Function to get instance status
get_instance_status() {
    aws neptune describe-db-instances \
        --db-instance-identifier "$INSTANCE_NAME" \
        --region "$REGION" \
        --output json 2>/dev/null || echo "{}"
}

# Function to get Neptune endpoint
get_endpoint() {
    CLUSTER_DATA=$(get_cluster_status)
    echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].Endpoint // "N/A"'
}

# Function to get Neptune reader endpoint
get_reader_endpoint() {
    CLUSTER_DATA=$(get_cluster_status)
    echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].ReaderEndpoint // "N/A"'
}

# Command: status
cmd_status() {
    log_info "Fetching Neptune cluster and instance status..."
    echo ""
    
    CLUSTER_DATA=$(get_cluster_status)
    INSTANCE_DATA=$(get_instance_status)
    
    # Parse cluster info
    CLUSTER_STATUS=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].Status // "not-found"')
    CLUSTER_ENGINE=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].EngineVersion // "N/A"')
    CLUSTER_ENDPOINT=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].Endpoint // "N/A"')
    CLUSTER_READER=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].ReaderEndpoint // "N/A"')
    
    # Parse instance info
    INSTANCE_STATUS=$(echo "$INSTANCE_DATA" | jq -r '.DBInstances[0].DBInstanceStatus // "not-found"')
    INSTANCE_CLASS=$(echo "$INSTANCE_DATA" | jq -r '.DBInstances[0].DBInstanceClass // "N/A"')
    INSTANCE_AZ=$(echo "$INSTANCE_DATA" | jq -r '.DBInstances[0].AvailabilityZone // "N/A"')
    
    # Display cluster status
    echo "================================================"
    echo "Neptune Cluster Status"
    echo "================================================"
    echo "Cluster ID:        $CLUSTER_NAME"
    echo "Status:            $CLUSTER_STATUS"
    echo "Engine Version:    $CLUSTER_ENGINE"
    echo "Writer Endpoint:   $CLUSTER_ENDPOINT"
    echo "Reader Endpoint:   $CLUSTER_READER"
    echo ""
    
    # Display instance status
    echo "================================================"
    echo "Neptune Instance Status"
    echo "================================================"
    echo "Instance ID:       $INSTANCE_NAME"
    echo "Status:            $INSTANCE_STATUS"
    echo "Instance Class:    $INSTANCE_CLASS"
    echo "Availability Zone: $INSTANCE_AZ"
    echo "================================================"
    echo ""
    
    # Count nodes and edges if available
    if [ "$CLUSTER_STATUS" = "available" ] && [ "$INSTANCE_STATUS" = "available" ]; then
        log_info "Querying database statistics..."
        
        if command -v awscurl &> /dev/null; then
            NODE_COUNT=$(awscurl --service neptune-db --region "$REGION" \
                -X POST "https://${CLUSTER_ENDPOINT}:8182/openCypher" \
                -H "Content-Type: application/json" \
                -d '{"query": "MATCH (n) RETURN count(n) as count"}' 2>/dev/null | jq -r '.results[0].count // "N/A"')
            
            EDGE_COUNT=$(awscurl --service neptune-db --region "$REGION" \
                -X POST "https://${CLUSTER_ENDPOINT}:8182/openCypher" \
                -H "Content-Type: application/json" \
                -d '{"query": "MATCH ()-[r]->() RETURN count(r) as count"}' 2>/dev/null | jq -r '.results[0].count // "N/A"')
            
            echo "Database Statistics:"
            echo "  Nodes: $NODE_COUNT"
            echo "  Edges: $EDGE_COUNT"
            echo ""
        else
            log_warning "awscurl not found. Install it to query database statistics."
        fi
    fi
}

# Command: start
cmd_start() {
    log_info "Starting Neptune instance: $INSTANCE_NAME"
    
    CURRENT_STATUS=$(get_instance_status | jq -r '.DBInstances[0].DBInstanceStatus // "not-found"')
    
    if [ "$CURRENT_STATUS" = "available" ]; then
        log_warning "Instance is already running"
        return 0
    fi
    
    if [ "$CURRENT_STATUS" = "stopped" ]; then
        aws neptune start-db-cluster \
            --db-cluster-identifier "$CLUSTER_NAME" \
            --region "$REGION" &>/dev/null
        
        log_success "Start command sent. Waiting for instance to be available..."
        aws neptune wait db-instance-available \
            --db-instance-identifier "$INSTANCE_NAME" \
            --region "$REGION"
        
        log_success "Instance is now available"
    else
        log_error "Cannot start instance in state: $CURRENT_STATUS"
        exit 1
    fi
}

# Command: stop
cmd_stop() {
    log_info "Stopping Neptune cluster: $CLUSTER_NAME"
    
    CURRENT_STATUS=$(get_cluster_status | jq -r '.DBClusters[0].Status // "not-found"')
    
    if [ "$CURRENT_STATUS" = "stopped" ]; then
        log_warning "Cluster is already stopped"
        return 0
    fi
    
    if [ "$CURRENT_STATUS" = "available" ]; then
        aws neptune stop-db-cluster \
            --db-cluster-identifier "$CLUSTER_NAME" \
            --region "$REGION" &>/dev/null
        
        log_success "Stop command sent"
        log_info "Note: It may take several minutes for the cluster to fully stop"
    else
        log_error "Cannot stop cluster in state: $CURRENT_STATUS"
        exit 1
    fi
}

# Command: restart
cmd_restart() {
    log_info "Restarting Neptune instance: $INSTANCE_NAME"
    
    aws neptune reboot-db-instance \
        --db-instance-identifier "$INSTANCE_NAME" \
        --region "$REGION" &>/dev/null
    
    log_success "Restart command sent. Waiting for instance to be available..."
    aws neptune wait db-instance-available \
        --db-instance-identifier "$INSTANCE_NAME" \
        --region "$REGION"
    
    log_success "Instance restarted successfully"
}

# Command: info
cmd_info() {
    log_info "Retrieving Neptune connection information..."
    echo ""
    
    CLUSTER_DATA=$(get_cluster_status)
    INSTANCE_DATA=$(get_instance_status)
    
    ENDPOINT=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].Endpoint // "N/A"')
    READER_ENDPOINT=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].ReaderEndpoint // "N/A"')
    PORT=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].Port // "8182"')
    IAM_ROLES=$(echo "$CLUSTER_DATA" | jq -r '.DBClusters[0].AssociatedRoles[].RoleArn // "N/A"')
    
    echo "================================================"
    echo "Neptune Connection Information"
    echo "================================================"
    echo "Writer Endpoint: $ENDPOINT"
    echo "Reader Endpoint: $READER_ENDPOINT"
    echo "Port:           $PORT"
    echo "Region:         $REGION"
    echo ""
    echo "OpenCypher URL:"
    echo "  https://${ENDPOINT}:${PORT}/openCypher"
    echo ""
    echo "Gremlin WebSocket URL:"
    echo "  wss://${ENDPOINT}:${PORT}/gremlin"
    echo ""
    echo "SPARQL URL:"
    echo "  https://${ENDPOINT}:${PORT}/sparql"
    echo ""
    echo "IAM Roles:"
    echo "$IAM_ROLES" | while read -r role; do
        echo "  - $role"
    done
    echo "================================================"
    echo ""
    
    # Generate sample connection code
    echo "Sample Python Connection Code:"
    echo "================================================"
    cat << EOF
from gremlin_python.driver import client, serializer

neptune_endpoint = '${ENDPOINT}'
neptune_port = ${PORT}

gremlin_client = client.Client(
    f'wss://{neptune_endpoint}:{neptune_port}/gremlin',
    'g',
    message_serializer=serializer.GraphSONSerializersV2d0()
)

# Execute query
result = gremlin_client.submit('g.V().limit(5)').all().result()
print(result)
EOF
    echo "================================================"
}

# Command: modify
cmd_modify() {
    if [ -z "$NEW_INSTANCE_CLASS" ]; then
        log_error "New instance class not specified. Use --instance-class option."
        exit 1
    fi
    
    log_info "Modifying instance class to: $NEW_INSTANCE_CLASS"
    
    aws neptune modify-db-instance \
        --db-instance-identifier "$INSTANCE_NAME" \
        --db-instance-class "$NEW_INSTANCE_CLASS" \
        --apply-immediately \
        --region "$REGION" &>/dev/null
    
    log_success "Modification initiated. Waiting for instance to be available..."
    aws neptune wait db-instance-available \
        --db-instance-identifier "$INSTANCE_NAME" \
        --region "$REGION"
    
    log_success "Instance modified successfully"
}

# Command: list-loads
cmd_list_loads() {
    log_info "Fetching bulk load jobs..."
    
    ENDPOINT=$(get_endpoint)
    
    if ! command -v awscurl &> /dev/null; then
        log_error "awscurl is required for this command. Install it with: pip install awscurl"
        exit 1
    fi
    
    RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
        -X GET "https://${ENDPOINT}:8182/loader" 2>/dev/null)
    
    echo ""
    echo "================================================"
    echo "Bulk Load Jobs"
    echo "================================================"
    echo "$RESPONSE" | jq -r '.payload.loadIds[]? // "No load jobs found"' | while read -r load_id; do
        echo "Load ID: $load_id"
    done
    echo "================================================"
    echo ""
    echo "Use --load-id <ID> with check-load command to see details"
}

# Command: check-load
cmd_check_load() {
    if [ -z "$LOAD_ID" ]; then
        log_error "Load ID not specified. Use --load-id option."
        exit 1
    fi
    
    log_info "Checking load job status: $LOAD_ID"
    
    ENDPOINT=$(get_endpoint)
    
    if ! command -v awscurl &> /dev/null; then
        log_error "awscurl is required for this command. Install it with: pip install awscurl"
        exit 1
    fi
    
    RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
        -X GET "https://${ENDPOINT}:8182/loader/${LOAD_ID}" 2>/dev/null)
    
    echo ""
    echo "================================================"
    echo "Load Job Status"
    echo "================================================"
    echo "$RESPONSE" | jq '.'
    echo "================================================"
}

# Execute command
case $COMMAND in
    status)
        cmd_status
        ;;
    start)
        cmd_start
        ;;
    stop)
        cmd_stop
        ;;
    restart)
        cmd_restart
        ;;
    info)
        cmd_info
        ;;
    modify)
        cmd_modify
        ;;
    list-loads)
        cmd_list_loads
        ;;
    check-load)
        cmd_check_load
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

