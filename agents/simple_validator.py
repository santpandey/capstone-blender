#!/usr/bin/env python3
"""
Simple API Validator - Focused on crash prevention
Removes dangerous parameters and provides basic type correction
"""

from typing import Dict, List, Any, Optional
import re
import json
from pathlib import Path

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
        # Registry-driven validation data
        self.registry_path = Path(__file__).parent.parent / "blender_api_registry.json"
        self.registry: Dict[str, Any] = {}
        self.valid_apis: List[str] = []
        self.param_schemas: Dict[str, Dict[str, Any]] = {}
        self._load_registry()
    
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
            # Do NOT silently default unknown APIs to a sphere. Leave as-is and mark invalid.
            corrections.append(
                f"Unknown API: {original_api}. Not auto-corrected to avoid unintended geometry."
            )
            return {
                "api_name": original_api,
                "parameters": parameters or {},
                "corrections": corrections,
                "valid": False,
            }
        
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
        
        # Step 3: Apply registry schema (required keys, types, simple ranges, defaults)
        schema = self.param_schemas.get(api_name, {})
        # Fill defaults for missing required params
        required = schema.get("required", []) if isinstance(schema.get("required", []), list) else []
        props = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
        for key in required:
            if key not in clean_params:
                default = props.get(key, {}).get("default") if isinstance(props.get(key, {}), dict) else None
                if default is not None:
                    clean_params[key] = default
                    corrections.append(f"Added default for required '{key}': {default}")
        # Coerce types and clamp by min/max if provided
        for key, meta in props.items():
            if key not in clean_params:
                continue
            expected_type = meta.get("type")
            clean_params[key], coerced = self._coerce_type(expected_type, clean_params[key])
            if coerced:
                corrections.append(f"Coerced '{key}' to {expected_type}: {clean_params[key]}")
            # Clamp ranges
            try:
                min_v = meta.get("minimum")
                max_v = meta.get("maximum")
                val = clean_params[key]
                if isinstance(val, (int, float)):
                    if min_v is not None and val < min_v:
                        clean_params[key] = min_v
                        corrections.append(f"Clamped '{key}' to minimum {min_v}")
                    if max_v is not None and val > max_v:
                        clean_params[key] = max_v
                        corrections.append(f"Clamped '{key}' to maximum {max_v}")
            except Exception:
                pass

        return {
            "api_name": api_name,
            "parameters": clean_params,
            "valid": True
        }

    def _clean_parameter_value(self, param_name: str, value: Any) -> Any:
        """Clean and convert parameter values to safe types"""
        # Vectors/arrays
        if param_name in ["location", "value", "scale", "rotation"]:
            if isinstance(value, str):
                try:
                    if value.startswith("[") and value.endswith("]"):
                        parsed = eval(value)
                        return list(parsed) if isinstance(parsed, (list, tuple)) else [0, 0, 0]
                    return [float(value), 0, 0]
                except Exception:
                    return [0, 0, 0]
            if isinstance(value, (list, tuple)):
                return list(value)
            return [0, 0, 0]

        # Numerics
        if param_name in ["radius", "size", "segments", "rings", "depth", "angle", "bevel_depth"]:
            try:
                if param_name in ["segments", "rings"]:
                    return int(float(value))
                return float(value)
            except Exception:
                return 1.0 if param_name in ["radius", "size", "depth", "angle", "bevel_depth"] else 16

        # Booleans
        if param_name in ["calc_uvs", "enter_editmode", "cap_end", "cap_start"]:
            if isinstance(value, str):
                return value.lower() in ("true", "1", "yes", "on")
            return bool(value)

        # Strings
        if param_name in ["text", "font", "name", "type"]:
            return str(value)

        # Default: pass-through
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

    def _load_registry(self) -> None:
        """Load API registry and extract parameter schemas for operators.
        The registry is expected to be a JSON mapping of api_name -> metadata with optional
        'parameters' schema compatible with JSON Schema-like fields (type/default/minimum/maximum/required).
        """
        try:
            if self.registry_path.exists():
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    self.registry = json.load(f)
                # Valid APIs are registry keys
                self.valid_apis = list(self.registry.keys())
                # Extract parameter schemas
                for name, meta in self.registry.items():
                    params_meta = meta.get("parameters") if isinstance(meta, dict) else None
                    # Normalize to a JSON-Schema-like dict with properties/required
                    if isinstance(params_meta, dict):
                        # Heuristics: if it already looks like JSON schema, keep; else wrap
                        if "properties" in params_meta or "required" in params_meta:
                            self.param_schemas[name] = params_meta
                        else:
                            self.param_schemas[name] = {"properties": params_meta, "required": []}
            else:
                # Keep basic fallbacks if file missing
                self.registry = {}
        except Exception:
            # If registry fails to load, keep previous minimal behavior
            self.registry = {}

    def _coerce_type(self, expected: Optional[str], value: Any) -> (Any, bool):
        """Coerce value to expected type if possible. Returns (value, coerced:boolean)."""
        if not expected:
            return value, False
        try:
            t = expected.lower()
            if t in ("number", "float"):
                return float(value), not isinstance(value, float)
            if t in ("integer", "int"):
                return int(float(value)), not isinstance(value, int)
            if t in ("boolean", "bool"):
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on"), True
                return bool(value), not isinstance(value, bool)
            if t in ("array", "vector", "vector3"):
                if isinstance(value, str) and value.startswith("[") and value.endswith("]"):
                    parsed = eval(value)
                    return list(parsed) if isinstance(parsed, (list, tuple)) else [0, 0, 0], True
                if isinstance(value, (list, tuple)):
                    return list(value), False
                # Scalar to vector
                try:
                    return [float(value), 0, 0], True
                except Exception:
                    return [0, 0, 0], True
            if t in ("string", "str"):
                return str(value), not isinstance(value, str)
        except Exception:
            return value, False
        return value, False
