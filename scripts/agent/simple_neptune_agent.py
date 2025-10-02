#!/usr/bin/env python3
"""
Simple Neptune Agent - A straightforward agent for querying Neptune database
"""

import json
import subprocess
from typing import Dict, Any

class NeptuneAgent:
    def __init__(self, endpoint: str, region: str = "us-east-1"):
        self.endpoint = endpoint
        self.region = region
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a query on the Neptune database"""
        try:
            cmd = [
                'awscurl',
                '--service', 'neptune-db',
                '--region', self.region,
                f"{self.endpoint}/openCypher",
                '-X', 'POST',
                '-H', 'Content-Type: application/json',
                '-d', json.dumps({"query": query})
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                return {"success": True, "data": json.loads(result.stdout)}
            else:
                return {"success": False, "error": result.stderr}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_schema(self) -> str:
        """Get the database schema"""
        queries = [
            "CALL db.labels()",
            "CALL db.relationshipTypes()",
            "CALL db.propertyKeys()"
        ]
        
        schema_info = {}
        for query in queries:
            result = self.execute_query(query)
            if result["success"]:
                schema_info[query] = result["data"]
            else:
                schema_info[query] = {"error": result["error"]}
        
        return json.dumps(schema_info, indent=2)
    
    def find_drugs_for_disease(self, disease_name: str) -> Dict[str, Any]:
        """Find drugs associated with a specific disease"""
        # Find drugs related to the disease
        drug_query = f"""
        MATCH (d)-[r]-(drug)
        WHERE toLower(d.name) CONTAINS '{disease_name.lower()}'
        AND d:biolink:Disease
        AND drug:biolink:SmallMolecule
        RETURN d.name as disease, drug.name as drug, type(r) as relationship_type
        LIMIT 20
        """
        
        return self.execute_query(drug_query)
    
    def get_disease_info(self, disease_name: str) -> Dict[str, Any]:
        """Get detailed information about a disease"""
        query = f"""
        MATCH (d)
        WHERE toLower(d.name) CONTAINS '{disease_name.lower()}'
        AND d:biolink:Disease
        RETURN d.name as name, d.description as description, d.equivalent_identifiers as identifiers
        LIMIT 5
        """
        
        return self.execute_query(query)
    
    def get_drug_info(self, drug_name: str) -> Dict[str, Any]:
        """Get detailed information about a drug"""
        query = f"""
        MATCH (drug)
        WHERE toLower(drug.name) CONTAINS '{drug_name.lower()}'
        AND drug:biolink:SmallMolecule
        RETURN drug.name as name, drug.description as description, drug.equivalent_identifiers as identifiers
        LIMIT 5
        """
        
        return self.execute_query(query)

def main():
    """Main function to demonstrate the agent"""
    # Initialize the agent
    agent = NeptuneAgent("https://midas-test.cluster-c7j2zglv4rfb.us-east-1.neptune.amazonaws.com:8182")
    
    print("🔍 Neptune Knowledge Graph Agent")
    print("=" * 50)
    
    # Test 1: Get basic stats
    print("\n1. Database Statistics:")
    stats_query = "MATCH (n) RETURN count(n) as total_nodes"
    stats_result = agent.execute_query(stats_query)
    if stats_result["success"]:
        print(f"   Total nodes: {stats_result['data']['results'][0]['total_nodes']}")
    
    edge_stats = agent.execute_query("MATCH ()-[r]->() RETURN count(r) as total_edges")
    if edge_stats["success"]:
        print(f"   Total edges: {edge_stats['data']['results'][0]['total_edges']}")
    
    # Test 2: Find Huntington disease
    print("\n2. Searching for Huntington disease:")
    disease_info = agent.get_disease_info("huntington")
    if disease_info["success"] and "results" in disease_info["data"]:
        diseases = disease_info["data"]["results"]
        for disease in diseases[:3]:  # Show first 3
            print(f"   - {disease['name']}")
            if disease.get('description'):
                print(f"     Description: {disease['description'][:100]}...")
    else:
        print(f"   Error: {disease_info.get('error', 'Unknown error')}")
        print(f"   Debug info: {disease_info}")
    
    # Test 3: Find drugs for Huntington disease
    print("\n3. Finding drugs associated with Huntington disease:")
    drugs_result = agent.find_drugs_for_disease("huntington")
    if drugs_result["success"] and "results" in drugs_result["data"]:
        drugs = drugs_result["data"]["results"]
        if drugs:
            print(f"   Found {len(drugs)} drug-disease relationships:")
            for drug in drugs[:5]:  # Show first 5
                print(f"   - {drug['drug']} -> {drug['disease']} ({drug['relationship_type']})")
        else:
            print("   No direct drug-disease relationships found")
    else:
        print(f"   Error: {drugs_result.get('error', 'Unknown error')}")
    
    # Test 4: Get schema information
    print("\n4. Database Schema:")
    schema = agent.get_schema()
    print("   Schema information retrieved (see full schema in output)")
    
    print("\n✅ Agent demonstration complete!")

if __name__ == "__main__":
    main()
