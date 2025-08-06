#!/usr/bin/env python3
"""Quick script to check the generated JSON file"""

import json
import sys

def check_json_file():
    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin-1']:
            try:
                with open('blender_api_registry.json', 'r', encoding=encoding) as f:
                    data = json.load(f)
                print(f"✓ Successfully loaded JSON with {encoding} encoding")
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception("Could not decode JSON file with any encoding")
        
        print("=== JSON FILE VALIDATION ===")
        print(f"✓ JSON file is valid")
        print(f"✓ Available keys: {list(data.keys())}")
        
        # Check if 'apis' key exists, otherwise check the actual structure
        if 'apis' in data:
            print(f"✓ Total APIs extracted: {len(data['apis'])}")
        elif isinstance(data, list):
            print(f"✓ Total APIs extracted: {len(data)}")
            data = {'apis': {f'api_{i}': api for i, api in enumerate(data)}}
        else:
            print(f"✓ Data structure: {type(data)}")
            return True
        
        print("\n=== TOP CATEGORIES ===")
        categories = data['statistics']['categories']
        sorted_categories = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:10]
        for category, count in sorted_categories:
            print(f"  {category}: {count} APIs")
        
        print("\n=== SAMPLE API ===")
        sample_api = next(iter(data['apis'].values()))
        print(f"  Name: {sample_api['full_name']}")
        print(f"  Module: {sample_api['module']}")
        print(f"  Category: {sample_api['category']}")
        print(f"  Parameters: {len(sample_api['parameters'])}")
        print(f"  Tags: {', '.join(sample_api['tags'][:5])}")
        print(f"  Description: {sample_api['description'][:100]}...")
        
        if sample_api['parameters']:
            print(f"\n  Sample Parameter:")
            param = sample_api['parameters'][0]
            print(f"    Name: {param['name']}")
            print(f"    Type: {param['type']}")
            print(f"    Optional: {param['optional']}")
            if param['description']:
                print(f"    Description: {param['description'][:80]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking JSON file: {e}")
        return False

if __name__ == "__main__":
    success = check_json_file()
    sys.exit(0 if success else 1)
