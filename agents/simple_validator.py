#!/usr/bin/env python3
"""
Simple API Validator - Focused on crash prevention
Removes dangerous parameters and provides basic type correction
"""

from typing import Dict, List, Any, Optional
import re

class SimpleAPIValidator:
    """Lightweight validator focused on preventing Blender crashes"""
    
    def __init__(self):
        # Common API name corrections
        self.api_corrections = {
            "bpy.ops.mesh.add_sphere": "bpy.ops.mesh.primitive_uv_sphere_add",
            "bpy.ops.mesh.add_cube": "bpy.ops.mesh.primitive_cube_add",
            "bpy.ops.mesh.add_cylinder": "bpy.ops.mesh.primitive_cylinder_add",
            "bpy.ops.object.move": "bpy.ops.transform.translate",
            "bpy.ops.object.scale": "bpy.ops.transform.resize",
            "bpy.ops.object.rotate": "bpy.ops.transform.rotate",
        }
        
        # Valid API patterns
        self.valid_apis = [
            "bpy.ops.mesh.primitive_uv_sphere_add",
            "bpy.ops.mesh.primitive_cube_add",
            "bpy.ops.mesh.primitive_cylinder_add",
            "bpy.ops.mesh.primitive_plane_add",
            "bpy.ops.transform.translate",
            "bpy.ops.transform.resize",
            "bpy.ops.transform.rotate",
            "bpy.ops.object.select_all",
            "bpy.ops.material.new"
        ]
    
    def validate_and_clean(self, api_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and clean API call to prevent crashes
        
        Returns:
            Dict with 'api_name', 'parameters', 'corrections' keys
        """
        corrections = []
        
        # Step 1: Correct API name
        original_api = api_name
        if api_name in self.api_corrections:
            api_name = self.api_corrections[api_name]
            corrections.append(f"Corrected API: {original_api} → {api_name}")
        elif api_name not in self.valid_apis:
            # Default to sphere creation for unknown APIs
            api_name = "bpy.ops.mesh.primitive_uv_sphere_add"
            corrections.append(f"Unknown API {original_api} → using sphere creation")
        
        # Step 2: Clean dangerous parameters
        clean_params = {}
        dangerous_patterns = ["OBJECT_OT_", "TRANSFORM_OT_", "MESH_OT_", "VIEW3D_OT_"]
        
        for key, value in parameters.items():
            # Remove dangerous operator parameters
            if any(pattern in key for pattern in dangerous_patterns):
                corrections.append(f"Removed dangerous parameter: {key}")
                continue
            
            # Clean and validate parameter values
            clean_value = self._clean_parameter_value(key, value)
            if clean_value != value:
                corrections.append(f"Corrected {key}: {value} → {clean_value}")
            
            clean_params[key] = clean_value
        
        # Step 3: Add safe defaults for common parameters
        if api_name == "bpy.ops.mesh.primitive_uv_sphere_add":
            if "radius" not in clean_params:
                clean_params["radius"] = 1.0
            if "location" not in clean_params:
                clean_params["location"] = [0, 0, 0]
        elif api_name == "bpy.ops.mesh.primitive_cube_add":
            if "size" not in clean_params:
                clean_params["size"] = 2.0
            if "location" not in clean_params:
                clean_params["location"] = [0, 0, 0]
        elif api_name == "bpy.ops.transform.translate":
            if "value" not in clean_params:
                clean_params["value"] = [0, 0, 0]
        
        return {
            "api_name": api_name,
            "parameters": clean_params,
            "corrections": corrections,
            "valid": True
        }
    
    def _clean_parameter_value(self, param_name: str, value: Any) -> Any:
        """Clean and convert parameter values to safe types"""
        
        # Handle location, value, scale parameters (should be arrays)
        if param_name in ["location", "value", "scale", "rotation"]:
            if isinstance(value, str):
                try:
                    if value.startswith('[') and value.endswith(']'):
                        # Parse string array like "[1, 2, 3]"
                        parsed = eval(value)
                        return list(parsed) if isinstance(parsed, (list, tuple)) else [0, 0, 0]
                    else:
                        # Single value, convert to float and make 3D vector
                        return [float(value), 0, 0]
                except:
                    return [0, 0, 0]
            elif isinstance(value, (list, tuple)):
                return list(value)
            else:
                return [0, 0, 0]
        
        # Handle numeric parameters
        elif param_name in ["radius", "size", "segments", "rings"]:
            try:
                if param_name in ["segments", "rings"]:
                    return int(float(value))  # Integer parameters
                else:
                    return float(value)  # Float parameters
            except:
                return 1.0 if param_name in ["radius", "size"] else 16
        
        # Handle boolean parameters
        elif param_name in ["calc_uvs", "enter_editmode"]:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)
        
        # Default: return as-is for unknown parameters
        return value
    
    def validate_batch(self, api_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate a batch of API calls"""
        results = []
        
        for call in api_calls:
            api_name = call.get("api_name", "")
            parameters = call.get("parameters", {})
            
            result = self.validate_and_clean(api_name, parameters)
            
            # Preserve other fields from original call
            result.update({
                "description": call.get("description", ""),
                "execution_order": call.get("execution_order", len(results) + 1)
            })
            
            results.append(result)
        
        return results
