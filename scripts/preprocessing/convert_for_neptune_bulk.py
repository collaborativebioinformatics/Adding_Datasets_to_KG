#!/usr/bin/env python3
"""
Conversion script for Neptune bulk loading with proper multi-value handling.
Splits concatenated labels and identifiers into proper semicolon-delimited format.
"""

import csv
import re

def split_labels(label_string):
    """Split concatenated biolink labels."""
    if not label_string:
        return "Node"
    
    # Split on 'biolink:' and rejoin with semicolons
    labels = re.findall(r'biolink:[A-Za-z]+', label_string)
    return ';'.join(labels) if labels else "Node"

def split_identifiers(id_string):
    """Split concatenated identifiers."""
    if not id_string:
        return ""
    
    # Split on common identifier prefixes (handles formats like "PREFIX:value")
    identifiers = re.findall(r'[A-Z][A-Z\.\-\_]*:[^\s]+?(?=[A-Z][A-Z\.\-\_]*:|$)', id_string)
    return ';'.join(identifiers) if identifiers else id_string

def split_publications(pub_string):
    """Split concatenated PMID publications."""
    if not pub_string:
        return ""
    
    # Split on 'PMID:' and rejoin with semicolons
    pubs = re.findall(r'PMID:\d+', pub_string)
    return ';'.join(pubs) if pubs else pub_string

def convert_for_neptune_bulk(input_file, output_file, file_type):
    """Convert files for Neptune bulk loading with proper multi-value handling."""
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile, delimiter='\t')
            
            if file_type == 'nodes':
                # Use String with semicolon delimiters (String[] not supported in openCypher format)
                fieldnames = [':ID', 'name:String', ':LABEL', 'equivalent_identifiers:String', 
                             'NCBITaxon:String', 'information_content:Double', 'description:String']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                for row in reader:
                    # Split concatenated labels
                    labels = split_labels(row.get('category:LABEL', ''))
                    
                    # Split concatenated identifiers
                    identifiers = split_identifiers(row.get('equivalent_identifiers:string[]', ''))
                    
                    writer.writerow({
                        ':ID': row.get('id:ID', ''),
                        'name:String': row.get('name:string', ''),
                        ':LABEL': labels,
                        'equivalent_identifiers:String': identifiers,
                        'NCBITaxon:String': row.get('NCBITaxon:string', ''),
                        'information_content:Double': row.get('information_content:float', ''),
                        'description:String': row.get('description:string', '')
                    })
                    
            elif file_type == 'edges':
                # Include ALL edge properties
                fieldnames = [
                    ':START_ID', ':END_ID', ':TYPE', 
                    'primary_knowledge_source:String', 
                    'knowledge_level:String', 
                    'agent_type:String',
                    'original_subject:String',
                    'original_object:String',
                    'description:String',
                    'NCBITaxon:String',
                    'publications:String',
                    'object_aspect_qualifier:String',
                    'object_direction_qualifier:String',
                    'qualified_predicate:String'
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                for row in reader:
                    # Split concatenated publications
                    publications = split_publications(row.get('publications:string[]', ''))
                    
                    writer.writerow({
                        ':START_ID': row.get('subject:START_ID', ''),
                        ':END_ID': row.get('object:END_ID', ''),
                        ':TYPE': row.get('predicate:TYPE', 'RELATED_TO'),
                        'primary_knowledge_source:String': row.get('primary_knowledge_source:string', ''),
                        'knowledge_level:String': row.get('knowledge_level:string', ''),
                        'agent_type:String': row.get('agent_type:string', ''),
                        'original_subject:String': row.get('original_subject:string', ''),
                        'original_object:String': row.get('original_object:string', ''),
                        'description:String': row.get('description:string', ''),
                        'NCBITaxon:String': row.get('NCBITaxon:string', ''),
                        'publications:String': publications,
                        'object_aspect_qualifier:String': row.get('object_aspect_qualifier:string', ''),
                        'object_direction_qualifier:String': row.get('object_direction_qualifier:string', ''),
                        'qualified_predicate:String': row.get('qualified_predicate:string', '')
                    })

def create_test_files(input_file, output_file, file_type, limit=100):
    """Create test files with limited records."""
    
    with open(input_file, 'r', encoding='utf-8') as infile:
        with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
            reader = csv.DictReader(infile, delimiter='\t')
            
            if file_type == 'nodes':
                fieldnames = [':ID', 'name:String', ':LABEL', 'equivalent_identifiers:String', 
                             'NCBITaxon:String', 'information_content:Double', 'description:String']
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                count = 0
                for row in reader:
                    if count >= limit:
                        break
                    
                    labels = split_labels(row.get('category:LABEL', ''))
                    identifiers = split_identifiers(row.get('equivalent_identifiers:string[]', ''))
                        
                    writer.writerow({
                        ':ID': row.get('id:ID', ''),
                        'name:String': row.get('name:string', ''),
                        ':LABEL': labels,
                        'equivalent_identifiers:String': identifiers,
                        'NCBITaxon:String': row.get('NCBITaxon:string', ''),
                        'information_content:Double': row.get('information_content:float', ''),
                        'description:String': row.get('description:string', '')
                    })
                    count += 1
                    
            elif file_type == 'edges':
                fieldnames = [
                    ':START_ID', ':END_ID', ':TYPE', 
                    'primary_knowledge_source:String', 
                    'knowledge_level:String', 
                    'agent_type:String',
                    'original_subject:String',
                    'original_object:String',
                    'description:String',
                    'NCBITaxon:String',
                    'publications:String',
                    'object_aspect_qualifier:String',
                    'object_direction_qualifier:String',
                    'qualified_predicate:String'
                ]
                writer = csv.DictWriter(outfile, fieldnames=fieldnames, delimiter=',')
                writer.writeheader()
                
                count = 0
                for row in reader:
                    if count >= limit:
                        break
                    
                    publications = split_publications(row.get('publications:string[]', ''))
                        
                    writer.writerow({
                        ':START_ID': row.get('subject:START_ID', ''),
                        ':END_ID': row.get('object:END_ID', ''),
                        ':TYPE': row.get('predicate:TYPE', 'RELATED_TO'),
                        'primary_knowledge_source:String': row.get('primary_knowledge_source:string', ''),
                        'knowledge_level:String': row.get('knowledge_level:string', ''),
                        'agent_type:String': row.get('agent_type:string', ''),
                        'original_subject:String': row.get('original_subject:string', ''),
                        'original_object:String': row.get('original_object:string', ''),
                        'description:String': row.get('description:string', ''),
                        'NCBITaxon:String': row.get('NCBITaxon:string', ''),
                        'publications:String': publications,
                        'object_aspect_qualifier:String': row.get('object_aspect_qualifier:string', ''),
                        'object_direction_qualifier:String': row.get('object_direction_qualifier:string', ''),
                        'qualified_predicate:String': row.get('qualified_predicate:string', '')
                    })
                    count += 1

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Convert files for Neptune bulk loading')
    parser.add_argument('--input', required=True, help='Input file path')
    parser.add_argument('--output', required=True, help='Output file path')
    parser.add_argument('--type', choices=['nodes', 'edges'], required=True, help='File type')
    parser.add_argument('--test', type=int, help='Create test file with limited records')
    
    args = parser.parse_args()
    
    if args.test:
        print(f"Creating test file with {args.test} records...")
        create_test_files(args.input, args.output, args.type, args.test)
    else:
        print("Converting full file...")
        convert_for_neptune_bulk(args.input, args.output, args.type)
    
    print(f"Conversion complete: {args.output}")

