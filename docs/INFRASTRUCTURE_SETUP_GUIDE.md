# Neptune Infrastructure Setup Guide

This guide provides step-by-step instructions to recreate the Neptune infrastructure with proper bulk loading capabilities for fast data ingestion.

## Prerequisites

- AWS CLI configured with appropriate permissions
- Python 3.x installed
- awscurl installed (`pip install awscurl`)

## Step 1: Create IAM Role for Neptune S3 Access

```bash
# Create the Neptune S3 Load Role
aws iam create-role \
  --role-name NeptuneS3LoadRole \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Principal": {
          "Service": "rds.amazonaws.com"
        },
        "Action": "sts:AssumeRole"
      }
    ]
  }'

# Attach S3 read permissions
aws iam attach-role-policy \
  --role-name NeptuneS3LoadRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

# Create custom policy for specific S3 bucket access
aws iam put-role-policy \
  --role-name NeptuneS3LoadRole \
  --policy-name S3BucketAccess \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": [
          "s3:GetObject",
          "s3:ListBucket"
        ],
        "Resource": [
          "arn:aws:s3:::YOUR-BUCKET-NAME",
          "arn:aws:s3:::YOUR-BUCKET-NAME/*"
        ]
      }
    ]
  }'
```

## Step 2: Create Neptune Cluster

```bash
# Create DB subnet group (if not exists)
aws rds create-db-subnet-group \
  --db-subnet-group-name neptune-subnet-group \
  --db-subnet-group-description "Neptune subnet group" \
  --subnet-ids subnet-12345678 subnet-87654321

# Create Neptune cluster
aws neptune create-db-cluster \
  --db-cluster-identifier midas-neptune-cluster \
  --engine neptune \
  --engine-version 1.4.0.0 \
  --db-cluster-parameter-group-name default.neptune1.4 \
  --vpc-security-group-ids sg-12345678 \
  --db-subnet-group-name neptune-subnet-group \
  --backup-retention-period 7 \
  --preferred-backup-window "07:00-09:00" \
  --preferred-maintenance-window "sun:09:00-sun:11:00" \
  --storage-encrypted \
  --region us-east-1

# Create Neptune instance
aws neptune create-db-instance \
  --db-instance-identifier midas-neptune-instance \
  --db-instance-class db.r5.large \
  --engine neptune \
  --db-cluster-identifier midas-neptune-cluster \
  --region us-east-1
```

## Step 3: Associate IAM Role with Neptune Cluster

```bash
# Add the IAM role to the Neptune cluster
aws neptune add-role-to-db-cluster \
  --db-cluster-identifier midas-neptune-cluster \
  --role-arn arn:aws:iam::YOUR-ACCOUNT-ID:role/NeptuneS3LoadRole \
  --region us-east-1
```

## Step 4: Prepare Data Files for Bulk Loading

### Convert Data to Proper Neptune Format

```bash
# Create data conversion script
cat > convert_data.py << 'EOF'
import csv
import json

def convert_nodes(input_file, output_file):
    """Convert nodes to Neptune openCypher format."""
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile, delimiter='\t')
            
            # Neptune openCypher format headers
            fieldnames = [':ID', 'name:String', ':LABEL', 'description:String', 'NCBITaxon:String', 'information_content:Double']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            
            for row in reader:
                # Extract primary label
                labels = row.get(':LABEL', '').split('biolink:')
                primary_label = labels[1] if len(labels) > 1 else 'Node'
                primary_label = primary_label.split('_')[0] if '_' in primary_label else primary_label
                
                writer.writerow({
                    ':ID': row.get(':ID', ''),
                    'name:String': row.get('name:string', ''),
                    ':LABEL': primary_label,
                    'description:String': row.get('description:string', '')[:500],
                    'NCBITaxon:String': row.get('NCBITaxon:string', ''),
                    'information_content:Double': row.get('information_content:float', '')
                })

def convert_edges(input_file, output_file):
    """Convert edges to Neptune openCypher format."""
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile, delimiter='\t')
            
            # Neptune openCypher format headers (no :ID for edges)
            fieldnames = [':START_ID', ':END_ID', ':TYPE', 'primary_knowledge_source:String', 'knowledge_level:String']
            writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
            writer.writeheader()
            
            for row in reader:
                rel_type = row.get(':TYPE', 'RELATED_TO').replace(':', '_').replace('biolink:', '')
                
                writer.writerow({
                    ':START_ID': row.get(':START_ID', ''),
                    ':END_ID': row.get(':END_ID', ''),
                    ':TYPE': rel_type,
                    'primary_knowledge_source:String': row.get('primary_knowledge_source:string', ''),
                    'knowledge_level:String': row.get('knowledge_level:string', '')
                })

# Convert the files
convert_nodes('data/nodes.temp_csv', 'data/nodes_neptune.csv')
convert_edges('data/edges.temp_csv', 'data/edges_neptune.csv')
print("Data conversion complete!")
EOF

# Run the conversion
python3 convert_data.py
```

## Step 5: Upload Data to S3

```bash
# Create S3 bucket (if not exists)
aws s3 mb s3://your-neptune-data-bucket

# Upload data files
aws s3 cp data/nodes_neptune.csv s3://your-neptune-data-bucket/nodes.csv
aws s3 cp data/edges_neptune.csv s3://your-neptune-data-bucket/edges.csv

# Verify upload
aws s3 ls s3://your-neptune-data-bucket/
```

## Step 6: Bulk Load Data to Neptune

### Load Nodes First

```bash
# Load nodes using bulk loader
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/loader" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://your-neptune-data-bucket/nodes.csv",
    "format": "opencypher",
    "iamRoleArn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/NeptuneS3LoadRole",
    "region": "us-east-1",
    "failOnError": "FALSE",
    "parallelism": "HIGH",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "TRUE"
  }'
```

### Monitor Node Loading Progress

```bash
# Check loader status
awscurl --service neptune-db --region us-east-1 \
  -X GET "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/loader/LOAD_ID"

# Check node count
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as node_count"}'
```

### Load Edges After Nodes Complete

```bash
# Load edges using bulk loader
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/loader" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://your-neptune-data-bucket/edges.csv",
    "format": "opencypher",
    "iamRoleArn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/NeptuneS3LoadRole",
    "region": "us-east-1",
    "failOnError": "FALSE",
    "parallelism": "HIGH",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "TRUE",
    "userProvidedEdgeIds": "FALSE"
  }'
```

## Step 7: Verify Data Loading

```bash
# Check total counts
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN count(n) as node_count"}'

awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH ()-[r]->() RETURN count(r) as edge_count"}'

# Sample query
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/openCypher" \
  -H "Content-Type: application/json" \
  -d '{"query": "MATCH (n) RETURN n LIMIT 5"}'
```

## Step 8: Performance Optimization

### For Large Datasets, Split Files

```bash
# Split large files for parallel loading
split -l 50000 data/nodes_neptune.csv data/nodes_part_
split -l 100000 data/edges_neptune.csv data/edges_part_

# Upload parts to S3
aws s3 cp data/nodes_part_* s3://your-neptune-data-bucket/nodes/
aws s3 cp data/edges_part_* s3://your-neptune-data-bucket/edges/

# Load multiple node files in parallel
awscurl --service neptune-db --region us-east-1 \
  -X POST "https://midas-neptune-cluster.cluster-xxxxx.us-east-1.neptune.amazonaws.com:8182/loader" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "s3://your-neptune-data-bucket/nodes/",
    "format": "opencypher",
    "iamRoleArn": "arn:aws:iam::YOUR-ACCOUNT-ID:role/NeptuneS3LoadRole",
    "region": "us-east-1",
    "failOnError": "FALSE",
    "parallelism": "HIGH",
    "updateSingleCardinalityProperties": "FALSE",
    "queueRequest": "TRUE"
  }'
```

## Troubleshooting

### Common Issues

1. **VPC Endpoint for S3**: Ensure your Neptune cluster has access to S3
   ```bash
   # Create VPC endpoint for S3
   aws ec2 create-vpc-endpoint \
     --vpc-id vpc-12345678 \
     --service-name com.amazonaws.us-east-1.s3 \
     --route-table-ids rtb-12345678
   ```

2. **Security Group**: Ensure security group allows outbound HTTPS (443) to S3
   ```bash
   # Add outbound rule for HTTPS
   aws ec2 authorize-security-group-egress \
     --group-id sg-12345678 \
     --protocol tcp \
     --port 443 \
     --cidr 0.0.0.0/0
   ```

3. **IAM Role Trust Policy**: Ensure the role can be assumed by Neptune
   ```bash
   # Update trust policy
   aws iam update-assume-role-policy \
     --role-name NeptuneS3LoadRole \
     --policy-document '{
       "Version": "2012-10-17",
       "Statement": [
         {
           "Effect": "Allow",
           "Principal": {
             "Service": "rds.amazonaws.com"
           },
           "Action": "sts:AssumeRole"
         }
       ]
     }'
   ```

## Expected Performance

- **Bulk Loading**: ~50,000-100,000 records per minute
- **Direct Loading**: ~100-500 records per minute
- **Total Time for 258K nodes + 1M edges**: ~15-30 minutes with bulk loading vs 8+ hours with direct loading

## Cleanup

```bash
# Delete Neptune cluster
aws neptune delete-db-cluster \
  --db-cluster-identifier midas-neptune-cluster \
  --skip-final-snapshot \
  --region us-east-1

# Delete IAM role
aws iam delete-role-policy \
  --role-name NeptuneS3LoadRole \
  --policy-name S3BucketAccess

aws iam detach-role-policy \
  --role-name NeptuneS3LoadRole \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3ReadOnlyAccess

aws iam delete-role \
  --role-name NeptuneS3LoadRole
```

## Notes

- Replace `YOUR-ACCOUNT-ID` with your actual AWS account ID
- Replace `YOUR-BUCKET-NAME` with your actual S3 bucket name
- Replace subnet and security group IDs with your actual values
- The bulk loader is significantly faster than direct loading
- Always load nodes before edges to maintain referential integrity
- Monitor the loading progress and check for errors
