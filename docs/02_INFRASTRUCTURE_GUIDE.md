# Neptune CloudFormation Infrastructure

Infrastructure as Code (IaC) approach using AWS CloudFormation for Neptune database management.

## Why CloudFormation?

✅ **Single source of truth** - One YAML file defines all resources  
✅ **Automatic rollback** - Failed deployments roll back automatically  
✅ **Easy cleanup** - Delete entire stack with one command  
✅ **Dependency management** - CloudFormation handles resource dependencies  
✅ **No hanging scripts** - Built-in wait logic and error handling  
✅ **Reproducible** - Create identical environments easily  

## Files

- **`neptune-stack.yaml`** - CloudFormation template defining all resources
- **`deploy_stack.sh`** - Helper script for common operations

## Quick Start

### 1. Create Infrastructure

```bash
cd scripts/database

# Create new Neptune stack
./deploy_stack.sh create \
  --vpc-id vpc-xxxxxxxxx \
  --subnet-ids subnet-xxx,subnet-yyy \
  --security-groups sg-xxxxxxxxx
```

### 2. Check Status

```bash
# View stack status
./deploy_stack.sh status neptune-midas-dev

# Watch events in real-time
./deploy_stack.sh events neptune-midas-dev
```

### 3. Get Endpoints

```bash
# Show all outputs (endpoints, bucket, etc.)
./deploy_stack.sh outputs neptune-midas-dev

# This also creates neptune_config.env
source neptune_config.env
```

### 4. Delete Everything

```bash
# Delete entire stack (with confirmation)
./deploy_stack.sh delete neptune-midas-dev

# Everything gets cleaned up automatically:
# - Neptune cluster and instances
# - S3 bucket (requires manual emptying first)
# - IAM roles and policies
# - Subnet groups
```

## What Gets Created

The CloudFormation stack creates:

1. **Neptune Serverless Cluster**
   - Auto-scaling from 1-128 NCUs
   - Encrypted storage
   - Automated backups

2. **Neptune Instance**
   - db.serverless type
   - Automatic failover support

3. **S3 Bucket** (optional)
   - Versioning enabled
   - Server-side encryption
   - Named: `neptune-{cluster-name}-{account-id}`

4. **IAM Role**
   - S3 read access for Neptune
   - Automatically associated with cluster

5. **Subnet Group**
   - Uses your provided subnets
   - Multi-AZ support

## Advanced Usage

### Custom Parameters

```bash
./deploy_stack.sh create \
  --stack-name my-custom-stack \
  --cluster-name my-neptune \
  --vpc-id vpc-xxx \
  --subnet-ids subnet-a,subnet-b \
  --security-groups sg-xxx \
  --min-capacity 2.5 \
  --max-capacity 256 \
  --region us-west-2
```

### Update Existing Stack

```bash
# Update scaling configuration
./deploy_stack.sh update \
  --stack-name neptune-midas-dev \
  --min-capacity 2.5 \
  --max-capacity 64
```

### List All Stacks

```bash
./deploy_stack.sh list
```

### Use Existing S3 Bucket

```bash
./deploy_stack.sh create \
  --vpc-id vpc-xxx \
  --subnet-ids subnet-a,subnet-b \
  --security-groups sg-xxx \
  --no-bucket
```

## Template Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| ClusterName | midas-dev | Neptune cluster identifier |
| VpcId | (required) | VPC ID |
| SubnetIds | (required) | List of subnet IDs |
| SecurityGroupIds | (required) | List of security group IDs |
| MinCapacity | 1.0 | Minimum NCUs |
| MaxCapacity | 128.0 | Maximum NCUs |
| EngineVersion | 1.4.6.1 | Neptune engine version |
| BackupRetentionDays | 1 | Backup retention period |
| CreateS3Bucket | true | Whether to create S3 bucket |

## Stack Outputs

After creation, the stack provides:

- **ClusterEndpoint** - Writer endpoint for queries
- **ClusterReadEndpoint** - Reader endpoint for read-only queries
- **ClusterPort** - Port number (8182)
- **S3BucketName** - Created S3 bucket name
- **S3BucketUrl** - Console link to bucket
- **IAMRoleArn** - IAM role ARN for bulk loading
- **ConnectionString** - WebSocket connection string
- **OpenCypherEndpoint** - OpenCypher query endpoint

## Workflow Examples

### Development Environment

```bash
# Create dev stack
./deploy_stack.sh create \
  --stack-name neptune-dev \
  --cluster-name midas-dev \
  --vpc-id vpc-xxx \
  --subnet-ids subnet-a,subnet-b \
  --security-groups sg-xxx \
  --min-capacity 1.0 \
  --max-capacity 32

# Get config
./deploy_stack.sh outputs neptune-dev
source neptune_config.env

# Use it...
# (load data, run queries, etc.)

# Delete when done
./deploy_stack.sh delete neptune-dev
```

### Production Environment

```bash
# Create prod stack with higher capacity
./deploy_stack.sh create \
  --stack-name neptune-prod \
  --cluster-name midas-prod \
  --vpc-id vpc-xxx \
  --subnet-ids subnet-a,subnet-b \
  --security-groups sg-xxx \
  --min-capacity 2.5 \
  --max-capacity 256 \
  --region us-east-1

# Monitor
./deploy_stack.sh status neptune-prod
./deploy_stack.sh events neptune-prod
```

## Monitoring Stack Creation

CloudFormation provides detailed progress:

```bash
# Watch status
watch -n 10 './deploy_stack.sh status neptune-midas-dev'

# View events (most recent first)
./deploy_stack.sh events neptune-midas-dev

# Check from AWS Console
# CloudFormation → Stacks → neptune-midas-dev
```

## Troubleshooting

### Stack Creation Failed

```bash
# Check events for error
./deploy_stack.sh events neptune-midas-dev

# Common issues:
# - Invalid subnet IDs (check they're in the VPC)
# - Security group not found
# - Insufficient IAM permissions
# - Subnet availability zones (need at least 2)
```

### Stack Stuck in DELETE_FAILED

```bash
# Some resources may need manual cleanup (e.g., non-empty S3 bucket)

# Empty S3 bucket first
aws s3 rm s3://neptune-midas-dev-123456789012 --recursive

# Then delete stack again
./deploy_stack.sh delete neptune-midas-dev
```

### Update Stack Fails

```bash
# Some properties can't be updated (like cluster ID)
# Solution: Create new stack with new name

# Or check what properties can be updated:
# https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-neptune-dbcluster.html
```

## Cost Optimization

```bash
# Scale down for development
./deploy_stack.sh update \
  --stack-name neptune-dev \
  --min-capacity 1.0 \
  --max-capacity 4

# Delete when not in use
./deploy_stack.sh delete neptune-dev

# Create again when needed (data is lost)
./deploy_stack.sh create ...
```

## Comparison: Bash Scripts vs CloudFormation

| Aspect | Bash Scripts | CloudFormation |
|--------|-------------|----------------|
| **Deployment** | Manual steps, can hang | Automatic, reliable |
| **Cleanup** | Manual deletion | One command deletes all |
| **Rollback** | Manual recovery | Automatic rollback |
| **Status** | Custom wait logic | Built-in status tracking |
| **Reproducibility** | Script + parameters | Single template file |
| **Error Handling** | Custom logic needed | Built-in |
| **Dependencies** | Manual ordering | Automatic |
| **Best For** | Quick hacks | Production infrastructure |

## Migration from Bash Scripts

If you have existing infrastructure from bash scripts:

```bash
# 1. Get current config
VPC_ID=$(aws neptune describe-db-clusters --db-cluster-identifier midas-test --query 'DBClusters[0].DBSubnetGroup.VpcId' --output text)
SUBNET_IDS=$(aws rds describe-db-subnet-groups --db-subnet-group-name neptune-subnet-group --query 'DBSubnetGroups[0].Subnets[*].SubnetIdentifier' --output text | tr '\t' ',')
SG_IDS=$(aws neptune describe-db-clusters --db-cluster-identifier midas-test --query 'DBClusters[0].VpcSecurityGroups[0].VpcSecurityGroupId' --output text)

# 2. Create new stack
./deploy_stack.sh create \
  --stack-name neptune-midas-cf \
  --cluster-name midas-cf \
  --vpc-id $VPC_ID \
  --subnet-ids $SUBNET_IDS \
  --security-groups $SG_IDS

# 3. Migrate data (if needed)
# ... data migration steps ...

# 4. Delete old infrastructure
./cleanup_old_cluster.sh midas-test
```

## Next Steps

After stack is created:
1. Load your data using the S3 bucket
2. Query using the endpoints
3. Use `./manage_neptune.sh` for operations
4. Delete stack when done: `./deploy_stack.sh delete`

## Resources

- [AWS Neptune CloudFormation Reference](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_Neptune.html)
- [Neptune Serverless](https://docs.aws.amazon.com/neptune/latest/userguide/neptune-serverless.html)
- [CloudFormation Best Practices](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html)

