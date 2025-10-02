#!/bin/bash

################################################################################
# Deploy Neptune Infrastructure using CloudFormation
#
# Usage:
#   ./deploy_stack.sh create [options]
#   ./deploy_stack.sh delete [stack-name]
#   ./deploy_stack.sh status [stack-name]
#   ./deploy_stack.sh outputs [stack-name]
################################################################################

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Default values
TIMESTAMP=$(date +%y%m%d%H%M)
STACK_NAME="neptune-midas-dev-${TIMESTAMP}"
CLUSTER_NAME="midas-dev-${TIMESTAMP}"
REGION="us-east-1"
TEMPLATE_FILE="neptune-stack.yaml"

show_help() {
    cat << EOF
Neptune CloudFormation Deployment Tool

Usage:
  $0 create [options]          Create new Neptune stack
  $0 update [options]          Update existing stack
  $0 delete <stack-name>       Delete stack
  $0 status <stack-name>       Show stack status
  $0 outputs <stack-name>      Show stack outputs
  $0 events <stack-name>       Show stack events
  $0 list                      List all Neptune stacks

Create/Update Options:
  --stack-name <name>          CloudFormation stack name (default: neptune-midas-dev-YYMMDDHHMM)
  --cluster-name <name>        Neptune cluster name (default: midas-dev-YYMMDDHHMM)
  --vpc-id <id>                VPC ID (required)
  --subnet-ids <ids>           Comma-separated subnet IDs (required)
  --security-groups <ids>      Comma-separated security group IDs (required)
  --region <region>            AWS region (default: us-east-1)
  --min-capacity <num>         Min NCUs (default: 1.0)
  --max-capacity <num>         Max NCUs (default: 128.0)
  --no-bucket                  Don't create S3 bucket
  --help                       Show this help

Examples:
  # Create new stack
  $0 create --vpc-id vpc-xxx --subnet-ids subnet-a,subnet-b --security-groups sg-xxx

  # Check status
  $0 status neptune-midas-dev

  # Get outputs (endpoints, bucket)
  $0 outputs neptune-midas-dev

  # Delete stack
  $0 delete neptune-midas-dev

EOF
}

# Command functions
cmd_create() {
    log_info "Creating CloudFormation stack: $STACK_NAME"
    
    # Validate required parameters
    if [ -z "$VPC_ID" ] || [ -z "$SUBNET_IDS" ] || [ -z "$SECURITY_GROUP_IDS" ]; then
        log_error "Missing required parameters. Use --help for usage."
        exit 1
    fi
    
    # Build parameters (use provided cluster name or the timestamped default)
    PARAMS="ParameterKey=ClusterName,ParameterValue=${CLUSTER_NAME}"
    PARAMS="$PARAMS ParameterKey=VpcId,ParameterValue=$VPC_ID"
    PARAMS="$PARAMS ParameterKey=SubnetIds,ParameterValue=\"$SUBNET_IDS\""
    PARAMS="$PARAMS ParameterKey=SecurityGroupIds,ParameterValue=\"$SECURITY_GROUP_IDS\""
    PARAMS="$PARAMS ParameterKey=MinCapacity,ParameterValue=${MIN_CAPACITY:-1.0}"
    PARAMS="$PARAMS ParameterKey=MaxCapacity,ParameterValue=${MAX_CAPACITY:-128.0}"
    PARAMS="$PARAMS ParameterKey=CreateS3Bucket,ParameterValue=${CREATE_BUCKET:-true}"
    
    log_info "Creating stack with parameters:"
    echo "  Stack Name: $STACK_NAME"
    echo "  Cluster Name: $CLUSTER_NAME"
    echo "  VPC: $VPC_ID"
    echo "  Subnets: $SUBNET_IDS"
    echo "  Security Groups: $SECURITY_GROUP_IDS"
    echo "  Min Capacity: ${MIN_CAPACITY:-1.0} NCUs"
    echo "  Max Capacity: ${MAX_CAPACITY:-128.0} NCUs"
    echo "  Create S3 Bucket: ${CREATE_BUCKET:-true}"
    echo ""
    
    aws cloudformation create-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters $PARAMS \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" \
        --tags Key=ManagedBy,Value=CloudFormation Key=Purpose,Value=Neptune
    
    log_success "Stack creation initiated!"
    log_info "Monitor progress with: $0 status $STACK_NAME"
    log_info "This will take 10-15 minutes..."
    
    # Wait for stack creation
    log_info "Waiting for stack creation to complete..."
    aws cloudformation wait stack-create-complete \
        --stack-name "$STACK_NAME" \
        --region "$REGION" && {
        echo ""
        log_success "Stack created successfully!"
        echo ""
        cmd_outputs "$STACK_NAME"
    } || {
        log_error "Stack creation failed. Check events with: $0 events $STACK_NAME"
        exit 1
    }
}

cmd_update() {
    log_info "Updating CloudFormation stack: $STACK_NAME"
    
    # Build parameters
    PARAMS="ParameterKey=ClusterName,UsePreviousValue=true"
    PARAMS="$PARAMS ParameterKey=VpcId,UsePreviousValue=true"
    PARAMS="$PARAMS ParameterKey=SubnetIds,UsePreviousValue=true"
    PARAMS="$PARAMS ParameterKey=SecurityGroupIds,UsePreviousValue=true"
    
    [ -n "$MIN_CAPACITY" ] && PARAMS="$PARAMS ParameterKey=MinCapacity,ParameterValue=$MIN_CAPACITY" || PARAMS="$PARAMS ParameterKey=MinCapacity,UsePreviousValue=true"
    [ -n "$MAX_CAPACITY" ] && PARAMS="$PARAMS ParameterKey=MaxCapacity,ParameterValue=$MAX_CAPACITY" || PARAMS="$PARAMS ParameterKey=MaxCapacity,UsePreviousValue=true"
    
    aws cloudformation update-stack \
        --stack-name "$STACK_NAME" \
        --template-body "file://$TEMPLATE_FILE" \
        --parameters $PARAMS \
        --capabilities CAPABILITY_NAMED_IAM \
        --region "$REGION" 2>&1 | tee /tmp/update_result.txt
    
    if grep -q "No updates are to be performed" /tmp/update_result.txt; then
        log_warning "No changes to apply"
    else
        log_success "Stack update initiated!"
        log_info "Monitor progress with: $0 status $STACK_NAME"
    fi
}

cmd_delete() {
    local stack_name="${1:-$STACK_NAME}"
    
    log_warning "This will delete the Neptune cluster and all data!"
    echo -n "Are you sure? Type 'yes' to confirm: "
    read -r confirmation
    
    if [ "$confirmation" != "yes" ]; then
        log_info "Deletion cancelled"
        exit 0
    fi
    
    log_info "Deleting stack: $stack_name"
    
    aws cloudformation delete-stack \
        --stack-name "$stack_name" \
        --region "$REGION"
    
    log_success "Stack deletion initiated!"
    log_info "Monitor progress with: $0 status $stack_name"
    
    # Wait for deletion
    log_info "Waiting for stack deletion to complete..."
    aws cloudformation wait stack-delete-complete \
        --stack-name "$stack_name" \
        --region "$REGION" 2>/dev/null && {
        log_success "Stack deleted successfully!"
    } || {
        log_warning "Stack may have already been deleted or check status manually"
    }
}

cmd_status() {
    local stack_name="${1:-$STACK_NAME}"
    
    log_info "Checking status of stack: $stack_name"
    echo ""
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].[StackName,StackStatus,CreationTime]' \
        --output table 2>/dev/null || {
        log_error "Stack not found: $stack_name"
        exit 1
    }
}

cmd_outputs() {
    local stack_name="${1:-$STACK_NAME}"
    
    log_info "Stack outputs for: $stack_name"
    echo ""
    
    aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs' \
        --output table 2>/dev/null || {
        log_error "Stack not found or no outputs available"
        exit 1
    }
    
    # Also save to env file
    log_info "Saving outputs to neptune_config.env..."
    
    ENDPOINT=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`ClusterEndpoint`].OutputValue' \
        --output text 2>/dev/null)
    
    BUCKET=$(aws cloudformation describe-stacks \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --query 'Stacks[0].Outputs[?OutputKey==`S3BucketName`].OutputValue' \
        --output text 2>/dev/null)
    
    cat > neptune_config.env << EOF
# Neptune Configuration (from CloudFormation stack: $stack_name)
# Generated on $(date)

export NEPTUNE_ENDPOINT="$ENDPOINT"
export NEPTUNE_REGION="$REGION"
export S3_BUCKET="$BUCKET"
export STACK_NAME="$stack_name"
EOF
    
    log_success "Configuration saved to neptune_config.env"
    echo "  Source it with: source neptune_config.env"
}

cmd_events() {
    local stack_name="${1:-$STACK_NAME}"
    
    log_info "Recent events for stack: $stack_name"
    echo ""
    
    aws cloudformation describe-stack-events \
        --stack-name "$stack_name" \
        --region "$REGION" \
        --max-items 20 \
        --query 'StackEvents[*].[Timestamp,ResourceStatus,ResourceType,LogicalResourceId,ResourceStatusReason]' \
        --output table
}

cmd_list() {
    log_info "Neptune CloudFormation stacks in region: $REGION"
    echo ""
    
    aws cloudformation list-stacks \
        --region "$REGION" \
        --query 'StackSummaries[?starts_with(StackName, `neptune`) && StackStatus != `DELETE_COMPLETE`].[StackName,StackStatus,CreationTime]' \
        --output table
}

# Main script
COMMAND="${1:-help}"
shift || true

# Parse options
while [[ $# -gt 0 ]]; do
    case $1 in
        --stack-name)
            STACK_NAME="$2"
            shift 2
            ;;
        --cluster-name)
            CLUSTER_NAME="$2"
            shift 2
            ;;
        --vpc-id)
            VPC_ID="$2"
            shift 2
            ;;
        --subnet-ids)
            SUBNET_IDS="$2"
            shift 2
            ;;
        --security-groups)
            SECURITY_GROUP_IDS="$2"
            shift 2
            ;;
        --region)
            REGION="$2"
            shift 2
            ;;
        --min-capacity)
            MIN_CAPACITY="$2"
            shift 2
            ;;
        --max-capacity)
            MAX_CAPACITY="$2"
            shift 2
            ;;
        --no-bucket)
            CREATE_BUCKET="false"
            shift
            ;;
        --help)
            show_help
            exit 0
            ;;
        *)
            # Positional argument (stack name for delete/status/outputs)
            if [ "$COMMAND" = "delete" ] || [ "$COMMAND" = "status" ] || [ "$COMMAND" = "outputs" ] || [ "$COMMAND" = "events" ]; then
                STACK_NAME="$1"
            fi
            shift
            ;;
    esac
done

# Execute command
case $COMMAND in
    create)
        cmd_create
        ;;
    update)
        cmd_update
        ;;
    delete)
        cmd_delete "$STACK_NAME"
        ;;
    status)
        cmd_status "$STACK_NAME"
        ;;
    outputs)
        cmd_outputs "$STACK_NAME"
        ;;
    events)
        cmd_events "$STACK_NAME"
        ;;
    list)
        cmd_list
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        log_error "Unknown command: $COMMAND"
        show_help
        exit 1
        ;;
esac

