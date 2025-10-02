#!/bin/bash

################################################################################
# Check Neptune Access and Network Configuration
################################################################################

CLUSTER_ENDPOINT="${1}"
REGION="${2:-us-east-1}"

if [ -z "$CLUSTER_ENDPOINT" ]; then
    echo "Usage: $0 <cluster-endpoint> [region]"
    echo "Example: $0 midas-dev-2510021802.cluster-xxxxx.us-east-1.neptune.amazonaws.com"
    exit 1
fi

echo "================================================"
echo "Neptune Access Check"
echo "================================================"
echo "Cluster Endpoint: $CLUSTER_ENDPOINT"
echo "Region: $REGION"
echo ""

# Check if running on EC2
echo "1. Checking if running on EC2..."
if curl -s -m 2 http://169.254.169.254/latest/meta-data/instance-id &>/dev/null; then
    INSTANCE_ID=$(curl -s http://169.254.169.254/latest/meta-data/instance-id)
    EC2_VPC=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/vpc-id)
    EC2_SG=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/security-group-ids | tr '\n' ',')
    EC2_SUBNET=$(curl -s http://169.254.169.254/latest/meta-data/network/interfaces/macs/$(curl -s http://169.254.169.254/latest/meta-data/mac)/subnet-id)
    
    echo "✅ Running on EC2"
    echo "   Instance ID: $INSTANCE_ID"
    echo "   VPC: $EC2_VPC"
    echo "   Subnet: $EC2_SUBNET"
    echo "   Security Groups: $EC2_SG"
else
    echo "❌ Not running on EC2 or can't access metadata"
    echo "   You must access Neptune from within the VPC (EC2, Lambda, etc.)"
    exit 1
fi

echo ""
echo "2. Checking DNS resolution..."
if nslookup "$CLUSTER_ENDPOINT" &>/dev/null; then
    echo "✅ DNS resolves"
    nslookup "$CLUSTER_ENDPOINT" | grep -A2 "Name:" | tail -2
else
    echo "❌ DNS does not resolve"
    echo "   This could mean:"
    echo "   - Cluster not fully created yet"
    echo "   - Not in the same VPC as Neptune"
    echo "   - VPC DNS resolution disabled"
fi

echo ""
echo "3. Checking network connectivity..."
if timeout 5 bash -c "cat < /dev/null > /dev/tcp/$CLUSTER_ENDPOINT/8182" 2>/dev/null; then
    echo "✅ Can reach Neptune port 8182"
else
    echo "❌ Cannot reach Neptune port 8182"
    echo "   This could mean:"
    echo "   - Security group doesn't allow access from this instance"
    echo "   - Instance not in allowed subnets"
    echo "   - Network ACLs blocking traffic"
fi

echo ""
echo "4. Testing OpenCypher endpoint..."
if command -v awscurl &>/dev/null; then
    RESPONSE=$(awscurl --service neptune-db --region "$REGION" \
        -X POST "https://${CLUSTER_ENDPOINT}:8182/openCypher" \
        -H "Content-Type: application/json" \
        -d '{"query": "MATCH (n) RETURN count(n) as count LIMIT 1"}' 2>&1)
    
    if echo "$RESPONSE" | grep -q "results"; then
        echo "✅ Neptune is accessible and responding!"
        echo "$RESPONSE" | jq '.' 2>/dev/null || echo "$RESPONSE"
    else
        echo "❌ Neptune not accessible"
        echo "Response: $RESPONSE"
    fi
else
    echo "⚠️  awscurl not installed, skipping query test"
    echo "   Install with: pip install awscurl"
fi

echo ""
echo "================================================"
echo "Troubleshooting Tips"
echo "================================================"
echo ""
echo "If Neptune is not accessible:"
echo ""
echo "1. Ensure EC2 instance is in the SAME VPC as Neptune"
echo "   Neptune VPC: (check CloudFormation outputs)"
echo "   This EC2 VPC: $EC2_VPC"
echo ""
echo "2. Update Neptune security group to allow access from EC2:"
echo "   aws ec2 authorize-security-group-ingress \\"
echo "     --group-id <neptune-sg-id> \\"
echo "     --protocol tcp \\"
echo "     --port 8182 \\"
echo "     --source-group <ec2-sg-id>"
echo ""
echo "3. Or add EC2 security group to Neptune cluster"
echo ""
echo "4. Verify VPC has DNS resolution and hostnames enabled"
echo ""

