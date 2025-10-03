#!/usr/bin/env python3
"""
Fix goldenKG CSV format for Neptune bulk loading.

Neptune openCypher CSV format requirements:
- Node ID column: :ID or id:ID
- Node labels: :LABEL (not category:LABEL)
- Edge start: :START_ID or subject:START_ID
- Edge end: :END_ID or object:END_ID
- Edge type: :TYPE or predicate:TYPE
- Properties: name:type (e.g., name:string, count:int)
"""

import csv
import sys

def fix_nodes_file(input_file, output_file):
    """Fix nodes CSV format."""
    print(f"Processing nodes file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile)
            
            # Map old headers to new headers
            # Note: Neptune openCypher doesn't support string[] notation
            # Use string with semicolon delimiters instead
            fieldnames = [
                ':ID',                              # id:ID -> :ID
                'name:string',                      # name:string (keep)
                ':LABEL',                           # category:LABEL -> :LABEL
                'equivalent_identifiers:string',    # string[] -> string (semicolon-delimited)
                'information_content:float',        # information_content:float
                'description:string',               # description:string
                'hgvs:string',                      # string[] -> string (semicolon-delimited)
                'robokop_variant_id:string'         # robokop_variant_id:string
            ]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for row in reader:
                writer.writerow({
                    ':ID': row.get('id:ID', ''),
                    'name:string': row.get('name:string', ''),
                    ':LABEL': row.get('category:LABEL', ''),  # Fix: category:LABEL -> :LABEL
                    'equivalent_identifiers:string': row.get('equivalent_identifiers:string[]', ''),  # string[] -> string
                    'information_content:float': row.get('information_content:float', ''),
                    'description:string': row.get('description:string', ''),
                    'hgvs:string': row.get('hgvs:string[]', ''),  # string[] -> string
                    'robokop_variant_id:string': row.get('robokop_variant_id:string', '')
                })
                count += 1
                if count % 100 == 0:
                    print(f"  Processed {count} nodes...")
            
            print(f"  Total nodes: {count}")

def fix_edges_file(input_file, output_file):
    """Fix edges CSV format."""
    print(f"Processing edges file: {input_file}")
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile)
            
            # Map old headers to new headers
            fieldnames = [
                ':START_ID',                        # subject:START_ID -> :START_ID
                ':TYPE',                            # predicate:TYPE -> :TYPE
                ':END_ID',                          # object:END_ID -> :END_ID
                'primary_knowledge_source:string',  # primary_knowledge_source:string
                'original_subject:string',          # original_subject:string
                'original_object:string'            # original_object:string
            ]
            
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            count = 0
            for row in reader:
                writer.writerow({
                    ':START_ID': row.get('subject:START_ID', ''),  # Fix
                    ':TYPE': row.get('predicate:TYPE', ''),        # Fix
                    ':END_ID': row.get('object:END_ID', ''),       # Fix
                    'primary_knowledge_source:string': row.get('primary_knowledge_source:string', ''),
                    'original_subject:string': row.get('original_subject:string', ''),
                    'original_object:string': row.get('original_object:string', '')
                })
                count += 1
                if count % 1000 == 0:
                    print(f"  Processed {count} edges...")
            
            print(f"  Total edges: {count}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Fix goldenKG CSV format for Neptune')
    parser.add_argument('--nodes-in', default='data_output/kgs/goldenKG/goldenKG_nodes.csv',
                       help='Input nodes file')
    parser.add_argument('--edges-in', default='data_output/kgs/goldenKG/goldenKG_edges.csv',
                       help='Input edges file')
    parser.add_argument('--nodes-out', default='data_output/kgs/goldenKG/goldenKG_nodes_fixed.csv',
                       help='Output nodes file')
    parser.add_argument('--edges-out', default='data_output/kgs/goldenKG/goldenKG_edges_fixed.csv',
                       help='Output edges file')
    
    args = parser.parse_args()
    
    print("=" * 50)
    print("Fixing goldenKG CSV format for Neptune")
    print("=" * 50)
    print()
    
    fix_nodes_file(args.nodes_in, args.nodes_out)
    print()
    fix_edges_file(args.edges_in, args.edges_out)
    
    print()
    print("=" * 50)
    print("Conversion complete!")
    print("=" * 50)
    print(f"Nodes: {args.nodes_out}")
    print(f"Edges: {args.edges_out}")

