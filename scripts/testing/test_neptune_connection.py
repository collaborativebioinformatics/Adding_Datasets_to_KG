#!/usr/bin/env python3
"""
Test Neptune connection and basic queries
"""

import json
import subprocess

def test_neptune_connection():
    """Test basic Neptune connection and queries"""
    
    NEPTUNE_ENDPOINT = "https://midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com:8182"
    REGION = "us-east-1"
    
    def execute_query(query):
        """Execute a query on Neptune"""
        cmd = [
            'awscurl',
            '--service', 'neptune-db',
            '--region', REGION,
            f"{NEPTUNE_ENDPOINT}/openCypher",
            '-X', 'POST',
            '-H', 'Content-Type: application/json',
            '-d', json.dumps({"query": query})
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return result.returncode == 0, result.stdout, result.stderr
    
    print("Testing Neptune connection...")
    
    # Test 1: Count nodes
    print("\n1. Testing node count...")
    success, stdout, stderr = execute_query("MATCH (n) RETURN count(n) as node_count")
    if success:
        print(f"✅ Node count query successful: {stdout}")
    else:
        print(f"❌ Node count query failed: {stderr}")
        return False
    
    # Test 2: Count edges
    print("\n2. Testing edge count...")
    success, stdout, stderr = execute_query("MATCH ()-[r]->() RETURN count(r) as edge_count")
    if success:
        print(f"✅ Edge count query successful: {stdout}")
    else:
        print(f"❌ Edge count query failed: {stderr}")
        return False
    
    # Test 3: Sample nodes
    print("\n3. Testing sample nodes...")
    success, stdout, stderr = execute_query("MATCH (n) RETURN n LIMIT 3")
    if success:
        print(f"✅ Sample nodes query successful: {stdout}")
    else:
        print(f"❌ Sample nodes query failed: {stderr}")
        return False
    
    # Test 4: Look for Huntington disease
    print("\n4. Testing Huntington disease search...")
    success, stdout, stderr = execute_query("MATCH (n) WHERE toLower(n.name) CONTAINS 'huntington' RETURN n LIMIT 5")
    if success:
        print(f"✅ Huntington disease search successful: {stdout}")
    else:
        print(f"❌ Huntington disease search failed: {stderr}")
        return False
    
    print("\n🎉 All tests passed! Neptune connection is working.")
    return True

if __name__ == "__main__":
    test_neptune_connection()

