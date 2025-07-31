#!/usr/bin/env python3
"""
Database Schema Analysis Script
Compares actual database schema with model definitions and code usage.
"""

import os
import sys
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple
import subprocess

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
            exclude_words = {'self', 'Optional', 'List', 'Dict', 'Any', 'UUID', 'datetime', 'str', 'bool', 'int', 'float'}
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
        if file_path.is_file():
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
            if file_path.is_file():
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                        if field_name in content:
                            usage_locations.append(str(file_path))
                except Exception:
                    continue
    
    return usage_locations

def get_database_schema() -> Dict[str, Set[str]]:
    """Get actual database schema using psql."""
    schema = {}
    
    # Try to get DATABASE_URL from environment
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not found in environment")
        return {}
    
    # Extract database name from URL
    # Format: postgresql://user:pass@host:port/dbname
    db_match = re.search(r'/([^/?]+)(?:\?|$)', database_url)
    if not db_match:
        print("Could not extract database name from DATABASE_URL")
        return {}
    
    db_name = db_match.group(1)
    
    try:
        # Get list of tables
        result = subprocess.run([
            'psql', database_url, 
            '-c', "SELECT tablename FROM pg_tables WHERE schemaname = 'public';",
            '-t', '-A'
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"Error getting tables: {result.stderr}")
            return {}
        
        tables = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
        
        # Get columns for each table
        for table in tables:
            result = subprocess.run([
                'psql', database_url,
                '-c', f"SELECT column_name FROM information_schema.columns WHERE table_name = '{table}' AND table_schema = 'public';",
                '-t', '-A'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                columns = [line.strip() for line in result.stdout.strip().split('\n') if line.strip()]
                schema[table] = set(columns)
            else:
                print(f"Error getting columns for table {table}: {result.stderr}")
                
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return {}
    
    return schema

def analyze_missing_fields() -> Dict[str, List[str]]:
    """Analyze fields that exist in models but not in database."""
    model_fields = get_model_fields()
    db_schema = get_database_schema()
    
    missing_fields = {}
    
    for table_name, fields in model_fields.items():
        db_columns = db_schema.get(table_name, set())
        missing = fields - db_columns
        if missing:
            missing_fields[table_name] = list(missing)
    
    return missing_fields

def analyze_unused_fields() -> Dict[str, List[str]]:
    """Analyze fields that exist in database but not in models."""
    model_fields = get_model_fields()
    db_schema = get_database_schema()
    
    unused_fields = {}
    
    for table_name, db_columns in db_schema.items():
        model_columns = model_fields.get(table_name, set())
        unused = db_columns - model_columns
        if unused:
            unused_fields[table_name] = list(unused)
    
    return unused_fields

def analyze_field_usage() -> Dict[str, Dict[str, List[str]]]:
    """Analyze usage of all fields in the codebase."""
    model_fields = get_model_fields()
    field_usage = {}
    
    for table_name, fields in model_fields.items():
        field_usage[table_name] = {}
        for field in fields:
            usage = search_code_for_field_usage(field)
            if usage:
                field_usage[table_name][field] = usage
    
    return field_usage

def generate_report():
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
    
    # Get database schema
    print("\n\n2. DATABASE SCHEMA ANALYSIS")
    print("-" * 40)
    db_schema = get_database_schema()
    for table, columns in db_schema.items():
        print(f"\nTable: {table}")
        print(f"Columns: {sorted(columns)}")
    
    # Analyze missing fields
    print("\n\n3. MISSING FIELDS (In Models but Not in Database)")
    print("-" * 40)
    missing_fields = analyze_missing_fields()
    if missing_fields:
        for table, fields in missing_fields.items():
            print(f"\nTable: {table}")
            for field in fields:
                print(f"  - {field}")
    else:
        print("No missing fields found.")
    
    # Analyze unused fields
    print("\n\n4. UNUSED FIELDS (In Database but Not in Models)")
    print("-" * 40)
    unused_fields = analyze_unused_fields()
    if unused_fields:
        for table, fields in unused_fields.items():
            print(f"\nTable: {table}")
            for field in fields:
                print(f"  - {field}")
    else:
        print("No unused fields found.")
    
    # Analyze field usage
    print("\n\n5. FIELD USAGE ANALYSIS")
    print("-" * 40)
    field_usage = analyze_field_usage()
    for table, fields in field_usage.items():
        if fields:
            print(f"\nTable: {table}")
            for field, usage in fields.items():
                print(f"  - {field}: {len(usage)} references")
                for location in usage[:3]:  # Show first 3 locations
                    print(f"    * {location}")
                if len(usage) > 3:
                    print(f"    * ... and {len(usage) - 3} more locations")
    
    # Generate recommendations
    print("\n\n6. RECOMMENDATIONS")
    print("-" * 40)
    
    if missing_fields:
        print("\nFIELDS TO ADD TO DATABASE:")
        for table, fields in missing_fields.items():
            for field in fields:
                print(f"  - Add {field} to {table} table")
    
    if unused_fields:
        print("\nFIELDS TO REMOVE FROM DATABASE:")
        for table, fields in unused_fields.items():
            for field in fields:
                print(f"  - Remove {field} from {table} table")
    
    # Check for specific fields mentioned
    print("\n\n7. SPECIFIC FIELD ANALYSIS")
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
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    generate_report() 