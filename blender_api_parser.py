#!/usr/bin/env python3
"""
Blender Python API Parser
Extracts method signatures, parameters, and documentation from Blender HTML docs
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from bs4 import BeautifulSoup


@dataclass
class APIParameter:
    """Represents a single API parameter"""
    name: str
    type: str
    default: Optional[str] = None
    description: str = ""
    constraints: Optional[str] = None
    optional: bool = False
    enum_values: Optional[List[str]] = None


@dataclass
class APIMethod:
    """Represents a complete API method/operator"""
    full_name: str
    module: str
    name: str
    signature: str
    description: str
    parameters: List[APIParameter]
    category: str
    tags: List[str]
    examples: List[str]
    file_source: str


class BlenderAPIParser:
    """Parser for Blender Python API HTML documentation"""
    
    def __init__(self, docs_directory: str):
        self.docs_dir = Path(docs_directory)
        self.api_registry: Dict[str, APIMethod] = {}
        self.categories = {
            "mesh_operators": "bpy.ops.mesh",
            "object_operators": "bpy.ops.object", 
            "material_operators": "bpy.ops.material",
            "animation_operators": "bpy.ops.anim",
            "render_operators": "bpy.ops.render",
            "geometry_nodes": "bpy.types.GeometryNode",
            "shader_nodes": "bpy.types.ShaderNode",
            "compositor_nodes": "bpy.types.CompositorNode",
            "function_nodes": "bpy.types.FunctionNode",
            "modifiers": "bpy.types.*Modifier",
            "constraints": "bpy.types.*Constraint",
            "data_types": "bpy.types",
            "context": "bpy.context",
            "utilities": "bpy.utils"
        }
    
    def parse_all_apis(self) -> Dict[str, APIMethod]:
        """Parse all HTML files and extract API signatures"""
        print(f"Parsing Blender API docs from: {self.docs_dir}")
        
        html_files = list(self.docs_dir.glob("*.html"))
        print(f"Found {len(html_files)} HTML files")
        
        for html_file in html_files:
            if html_file.name.startswith("bpy."):
                try:
                    self.parse_module_file(html_file)
                except Exception as e:
                    print(f"Error parsing {html_file.name}: {e}")
        
        print(f"Extracted {len(self.api_registry)} API methods")
        return self.api_registry
    
    def parse_module_file(self, html_file: Path) -> None:
        """Extract all functions/methods from a single HTML file"""
        content = html_file.read_text(encoding='utf-8')
        soup = BeautifulSoup(content, 'html.parser')
        
        # Find all function definitions
        functions = soup.find_all('dl', class_='py function')
        
        for func in functions:
            try:
                api_info = self.extract_function_info(func, html_file.name)
                if api_info:
                    self.api_registry[api_info.full_name] = api_info
            except Exception as e:
                print(f"Error extracting function from {html_file.name}: {e}")
    
    def extract_function_info(self, func_element, file_name: str) -> Optional[APIMethod]:
        """Extract complete function information"""
        # Get function signature element
        sig_element = func_element.find('dt', class_='sig')
        if not sig_element:
            return None
        
        # Extract function name and module
        full_name = self.get_function_name(sig_element)
        if not full_name:
            return None
        
        module = self.get_module_name(full_name)
        name = full_name.split('.')[-1]
        
        # Extract signature
        signature = self.get_signature(sig_element)
        
        # Extract description
        description = self.get_description(func_element)
        
        # Extract parameters
        parameters = self.get_parameters(func_element)
        
        # Determine category
        category = self.determine_category(full_name)
        
        # Generate tags
        tags = self.generate_tags(full_name, description)
        
        # Extract examples (if any)
        examples = self.get_examples(func_element)
        
        return APIMethod(
            full_name=full_name,
            module=module,
            name=name,
            signature=signature,
            description=description,
            parameters=parameters,
            category=category,
            tags=tags,
            examples=examples,
            file_source=file_name
        )
    
    def get_function_name(self, sig_element) -> Optional[str]:
        """Extract the full function name"""
        id_attr = sig_element.get('id')
        if id_attr:
            return id_attr
        
        # Fallback: construct from class and name elements
        class_elem = sig_element.find('span', class_='sig-prename')
        name_elem = sig_element.find('span', class_='sig-name')
        
        if class_elem and name_elem:
            class_name = class_elem.get_text().strip()
            func_name = name_elem.get_text().strip()
            return f"{class_name}{func_name}"
        
        return None
    
    def get_module_name(self, full_name: str) -> str:
        """Extract module name from full function name"""
        parts = full_name.split('.')
        if len(parts) > 1:
            return '.'.join(parts[:-1])
        return ""
    
    def get_signature(self, sig_element) -> str:
        """Extract function signature"""
        # Get the text content and clean it up
        signature = sig_element.get_text()
        # Remove extra whitespace and normalize
        signature = re.sub(r'\s+', ' ', signature).strip()
        return signature
    
    def get_description(self, func_element) -> str:
        """Extract function description"""
        # Look for the description paragraph after the signature
        dd_element = func_element.find('dd')
        if dd_element:
            # Get the first paragraph that's not a parameter list
            for p in dd_element.find_all('p'):
                if p.get_text().strip():
                    return p.get_text().strip()
        return ""
    
    def get_parameters(self, func_element) -> List[APIParameter]:
        """Extract function parameters"""
        parameters = []
        
        # Find the parameters section
        dd_element = func_element.find('dd')
        if not dd_element:
            return parameters
        
        # Look for field list with parameters
        field_list = dd_element.find('dl', class_='field-list')
        if not field_list:
            return parameters
        
        # Find parameters field
        for dt in field_list.find_all('dt', class_='field-odd'):
            if 'Parameters' in dt.get_text():
                dd = dt.find_next_sibling('dd')
                if dd:
                    parameters = self.parse_parameter_list(dd)
                break
        
        return parameters
    
    def parse_parameter_list(self, dd_element) -> List[APIParameter]:
        """Parse the parameter list from the documentation"""
        parameters = []
        
        # Find all parameter list items
        for li in dd_element.find_all('li'):
            param = self.parse_single_parameter(li)
            if param:
                parameters.append(param)
        
        return parameters
    
    def parse_single_parameter(self, li_element) -> Optional[APIParameter]:
        """Parse a single parameter from list item"""
        text = li_element.get_text()
        
        # Extract parameter name (usually in bold)
        strong_elem = li_element.find('strong')
        if not strong_elem:
            return None
        
        name = strong_elem.get_text().strip()
        
        # Extract type information (usually in em tags)
        type_info = ""
        em_elems = li_element.find_all('em')
        if em_elems:
            type_info = em_elems[0].get_text().strip()
        
        # Parse type, constraints, and default
        param_type, constraints, default, optional = self.parse_type_info(type_info)
        
        # Extract description (text after the type info)
        description = self.extract_parameter_description(text, name, type_info)
        
        # Extract enum values if applicable
        enum_values = self.extract_enum_values(type_info)
        
        return APIParameter(
            name=name,
            type=param_type,
            default=default,
            description=description,
            constraints=constraints,
            optional=optional,
            enum_values=enum_values
        )
    
    def parse_type_info(self, type_info: str) -> tuple:
        """Parse type information string"""
        param_type = "unknown"
        constraints = None
        default = None
        optional = False
        
        if not type_info:
            return param_type, constraints, default, optional
        
        # Check if optional
        if "(optional)" in type_info:
            optional = True
            type_info = type_info.replace("(optional)", "").strip()
        
        # Extract basic type
        if "float" in type_info:
            param_type = "float"
        elif "int" in type_info:
            param_type = "int"
        elif "bool" in type_info:
            param_type = "boolean"
        elif "str" in type_info:
            param_type = "string"
        elif "enum" in type_info:
            param_type = "enum"
        elif "array" in type_info:
            param_type = "array"
        
        # Extract constraints (values in brackets)
        constraint_match = re.search(r'\[(.*?)\]', type_info)
        if constraint_match:
            constraints = constraint_match.group(1)
        
        return param_type, constraints, default, optional
    
    def extract_parameter_description(self, full_text: str, name: str, type_info: str) -> str:
        """Extract parameter description from full text"""
        # Remove the name and type info to get description
        text = full_text
        text = text.replace(name, "", 1)
        text = text.replace(type_info, "", 1)
        
        # Clean up and extract meaningful description
        text = re.sub(r'^[^\w]*', '', text)  # Remove leading non-word chars
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def extract_enum_values(self, type_info: str) -> Optional[List[str]]:
        """Extract enum values from type information"""
        if "enum" not in type_info:
            return None
        
        # Look for enum values in brackets
        enum_match = re.search(r"'([^']+)'(?:,\s*'([^']+)')*", type_info)
        if enum_match:
            # Extract all quoted values
            values = re.findall(r"'([^']+)'", type_info)
            return values
        
        return None
    
    def determine_category(self, full_name: str) -> str:
        """Determine API category based on full name"""
        for category, pattern in self.categories.items():
            if pattern.replace("*", "") in full_name:
                return category
        return "other"
    
    def generate_tags(self, full_name: str, description: str) -> List[str]:
        """Generate tags for the API method"""
        tags = []
        
        # Add module-based tags
        if "mesh" in full_name:
            tags.extend(["mesh", "modeling"])
        if "object" in full_name:
            tags.extend(["object", "transform"])
        if "material" in full_name:
            tags.extend(["material", "shading"])
        if "render" in full_name:
            tags.extend(["render", "output"])
        if "anim" in full_name:
            tags.extend(["animation", "keyframe"])
        
        # Add description-based tags
        desc_lower = description.lower()
        if any(word in desc_lower for word in ["create", "add", "new"]):
            tags.append("creation")
        if any(word in desc_lower for word in ["delete", "remove"]):
            tags.append("deletion")
        if any(word in desc_lower for word in ["select", "selection"]):
            tags.append("selection")
        if any(word in desc_lower for word in ["transform", "move", "rotate", "scale"]):
            tags.append("transform")
        
        return list(set(tags))  # Remove duplicates
    
    def get_examples(self, func_element) -> List[str]:
        """Extract code examples if present"""
        examples = []
        
        # Look for code blocks or examples
        for code_elem in func_element.find_all('code'):
            code_text = code_elem.get_text().strip()
            if code_text and len(code_text) > 10:  # Filter out short snippets
                examples.append(code_text)
        
        return examples
    
    def save_registry(self, output_file: str) -> None:
        """Save the API registry to JSON file"""
        # Convert to serializable format
        registry_data = {}
        for name, method in self.api_registry.items():
            registry_data[name] = asdict(method)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)
        
        print(f"API registry saved to: {output_file}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get parsing statistics"""
        stats = {
            "total_apis": len(self.api_registry),
            "categories": {},
            "modules": {},
            "parameter_types": {}
        }
        
        for method in self.api_registry.values():
            # Category stats
            stats["categories"][method.category] = stats["categories"].get(method.category, 0) + 1
            
            # Module stats
            stats["modules"][method.module] = stats["modules"].get(method.module, 0) + 1
            
            # Parameter type stats
            for param in method.parameters:
                stats["parameter_types"][param.type] = stats["parameter_types"].get(param.type, 0) + 1
        
        return stats


def main():
    """Main function to demonstrate the parser"""
    docs_dir = "d:/code/capstone/blender_python_reference_4_4"
    
    # Initialize parser
    parser = BlenderAPIParser(docs_dir)
    
    # Parse all APIs
    print("Starting Blender API parsing...")
    api_registry = parser.parse_all_apis()
    
    # Save results
    output_file = "d:/code/capstone/blender_api_registry.json"
    parser.save_registry(output_file)
    
    # Print statistics
    stats = parser.get_statistics()
    print("\n=== PARSING STATISTICS ===")
    print(f"Total APIs extracted: {stats['total_apis']}")
    print(f"\nTop categories:")
    for category, count in sorted(stats['categories'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {category}: {count}")
    
    print(f"\nTop modules:")
    for module, count in sorted(stats['modules'].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {module}: {count}")
    
    # Show sample APIs
    print(f"\n=== SAMPLE EXTRACTED APIS ===")
    sample_apis = list(api_registry.items())[:5]
    for name, method in sample_apis:
        print(f"\nAPI: {name}")
        print(f"Description: {method.description}")
        print(f"Parameters: {len(method.parameters)}")
        print(f"Category: {method.category}")
        print(f"Tags: {', '.join(method.tags)}")


if __name__ == "__main__":
    main()
