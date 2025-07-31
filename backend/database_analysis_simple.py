#!/usr/bin/env python3
"""
Simple Database Schema Analysis Script
Analyzes model definitions and code usage without requiring database connection.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_model_fields() -> Dict[str, Set[str]]:
    """Extract field names from all model files."""
    models_dir = Path("data/models")
    model_fields = {}
    
    for model_file in models_dir.glob("*.py"):
        if model_file.name == "__init__.py":
            continue
            
        table_name = model_file.stem
        fields = set()
        
        try:
            with open(model_file, 'r') as f:
                content = f.read()
                
            # Extract field names using regex
            # Look for patterns like: field_name: Type = Field(...)
            field_pattern = r'(\w+):\s*[^=]*=\s*Field'
            matches = re.findall(field_pattern, content)
            
            # Also look for fields without Field() but with type annotations
            type_pattern = r'(\w+):\s*[A-Za-z]'
            type_matches = re.findall(type_pattern, content)
            
            # Combine and filter out common non-field names
            all_fields = set(matches + type_matches)
            exclude_words = {'self', 'Optional', 'List', 'Dict', 'Any', 'UUID', 'datetime', 'str', 'bool', 'int', 'float', 'Enum'}
            fields = {f for f in all_fields if f not in exclude_words and not f.startswith('__')}
            
            model_fields[table_name] = fields
            
        except Exception as e:
            print(f"Error reading {model_file}: {e}")
    
    return model_fields

def search_code_for_field_usage(field_name: str) -> List[str]:
    """Search for field usage in the codebase."""
    backend_dir = Path(".")
    api_dir = Path("api")
    
    usage_locations = []
    
    # Search in backend directory
    for file_path in backend_dir.rglob("*.py"):
        if file_path.is_file() and not file_path.name.startswith('__'):
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    if field_name in content:
                        usage_locations.append(str(file_path))
            except Exception:
                continue
    
    # Search in API directory specifically
    if api_dir.exists():
        for file_path in api_dir.rglob("*.py"):
            if file_path.is_file() and not file_path.name.startswith('__'):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if field_name in content:
                            usage_locations.append(str(file_path))
                except Exception:
                    continue
    
    return usage_locations

def analyze_model_consistency() -> Dict[str, List[str]]:
    """Analyze consistency between model definitions."""
    models_dir = Path("data/models")
    model_files = {}
    
    for model_file in models_dir.glob("*.py"):
        if model_file.name == "__init__.py":
            continue
            
        table_name = model_file.stem
        model_files[table_name] = str(model_file)
    
    return model_files

def generate_comprehensive_report():
    """Generate comprehensive database analysis report."""
    print("=" * 80)
    print("DATABASE SCHEMA ANALYSIS REPORT")
    print("=" * 80)
    
    # Get model fields
    print("\n1. MODEL FIELD ANALYSIS")
    print("-" * 40)
    model_fields = get_model_fields()
    for table, fields in model_fields.items():
        print(f"\nTable: {table}")
        print(f"Fields: {sorted(fields)}")
    
    # Analyze field usage
    print("\n\n2. FIELD USAGE ANALYSIS")
    print("-" * 40)
    field_usage = {}
    total_usage = {}
    
    for table_name, fields in model_fields.items():
        field_usage[table_name] = {}
        for field in fields:
            usage = search_code_for_field_usage(field)
            if usage:
                field_usage[table_name][field] = usage
                total_usage[field] = len(usage)
    
    # Sort fields by usage
    sorted_fields = sorted(total_usage.items(), key=lambda x: x[1], reverse=True)
    
    print("\nMost Used Fields:")
    for field, count in sorted_fields[:10]:
        print(f"  - {field}: {count} references")
    
    print("\nField Usage by Table:")
    for table, fields in field_usage.items():
        if fields:
            print(f"\nTable: {table}")
            for field, usage in fields.items():
                print(f"  - {field}: {len(usage)} references")
                for location in usage[:2]:  # Show first 2 locations
                    print(f"    * {location}")
                if len(usage) > 2:
                    print(f"    * ... and {len(usage) - 2} more locations")
    
    # Analyze unused fields
    print("\n\n3. POTENTIALLY UNUSED FIELDS")
    print("-" * 40)
    unused_fields = {}
    
    for table_name, fields in model_fields.items():
        unused = []
        for field in fields:
            usage = search_code_for_field_usage(field)
            if not usage:
                unused.append(field)
        if unused:
            unused_fields[table_name] = unused
    
    if unused_fields:
        for table, fields in unused_fields.items():
            print(f"\nTable: {table}")
            for field in fields:
                print(f"  - {field}")
    else:
        print("No potentially unused fields found.")
    
    # Check for specific fields mentioned
    print("\n\n4. SPECIFIC FIELD ANALYSIS")
    print("-" * 40)
    specific_fields = ['mls_username', 'mls_password', 'license_number']
    for field in specific_fields:
        usage = search_code_for_field_usage(field)
        if usage:
            print(f"\n{field}: {len(usage)} references found")
            for location in usage:
                print(f"  - {location}")
        else:
            print(f"\n{field}: NO REFERENCES FOUND - SAFE TO REMOVE")
    
    # Generate recommendations
    print("\n\n5. RECOMMENDATIONS")
    print("-" * 40)
    
    if unused_fields:
        print("\nFIELDS TO CONSIDER REMOVING:")
        for table, fields in unused_fields.items():
            for field in fields:
                print(f"  - Remove {field} from {table} model")
    
    # Check for fields with very low usage
    low_usage_fields = {field: count for field, count in total_usage.items() if count <= 2}
    if low_usage_fields:
        print("\nFIELDS WITH LOW USAGE (≤2 references):")
        for field, count in low_usage_fields.items():
            print(f"  - {field}: {count} references")
    
    print("\n\n6. MODEL CONSISTENCY")
    print("-" * 40)
    model_files = analyze_model_consistency()
    for table, file_path in model_files.items():
        print(f"  - {table}: {file_path}")
    
    # Save detailed report to file
    report_data = {
        "model_fields": {k: list(v) for k, v in model_fields.items()},
        "field_usage": {k: {f: v for f, v in fields.items()} for k, fields in field_usage.items()},
        "unused_fields": unused_fields,
        "total_usage": total_usage,
        "specific_fields": {field: search_code_for_field_usage(field) for field in specific_fields}
    }
    
    with open("database_analysis_report.json", "w") as f:
        json.dump(report_data, f, indent=2)
    
    print(f"\nDetailed report saved to: database_analysis_report.json")
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    generate_comprehensive_report() 