#!/usr/bin/env python3
"""
Blender API Validation System
Validates and auto-corrects LLM-generated API calls against actual Blender specs
"""

import json
import re
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

@dataclass
class ValidationResult:
    """Result of API validation"""
    valid: bool
    api_name: str
    corrected_parameters: Dict[str, Any]
    errors: List[str]
    warnings: List[str]
    auto_corrections: List[str]

class ValidationLevel(Enum):
    """Validation strictness levels"""
    STRICT = "strict"      # Reject any invalid parameters
    CORRECTIVE = "corrective"  # Auto-correct invalid parameters
    PERMISSIVE = "permissive"  # Allow with warnings

class BlenderAPIValidator:
    """
    Validates LLM-generated API calls against actual Blender API registry
    Provides auto-correction for common mistakes
    """
    
    def __init__(self, registry_path: str = "d:/code/capstone/blender_api_registry.json"):
        self.registry_path = Path(registry_path)
        self.api_registry: Dict[str, Dict[str, Any]] = {}
        self.parameter_types: Dict[str, Dict[str, str]] = {}
        self.common_corrections: Dict[str, str] = {}
        
        # Load API registry
        self._load_api_registry()
        self._build_parameter_index()
        self._initialize_corrections()
    
    def _load_api_registry(self) -> None:
        """Load the Blender API registry from JSON"""
        try:
            if self.registry_path.exists():
                with open(self.registry_path, 'r', encoding='utf-8') as f:
                    self.api_registry = json.load(f)
                print(f"✅ Loaded {len(self.api_registry)} APIs from registry")
            else:
                print(f"⚠️ API registry not found at {self.registry_path}")
                # Create minimal fallback registry
                self._create_fallback_registry()
        except Exception as e:
            print(f"❌ Error loading API registry: {e}")
            self._create_fallback_registry()
    
    def _create_fallback_registry(self) -> None:
        """Create minimal fallback registry for common APIs"""
        self.api_registry = {
            "bpy.ops.mesh.primitive_uv_sphere_add": {
                "full_name": "bpy.ops.mesh.primitive_uv_sphere_add",
                "parameters": [
                    {"name": "radius", "type": "float", "default": "1.0", "optional": True},
                    {"name": "location", "type": "array", "default": "[0, 0, 0]", "optional": True},
                    {"name": "segments", "type": "int", "default": "32", "optional": True},
                    {"name": "rings", "type": "int", "default": "16", "optional": True}
                ]
            },
            "bpy.ops.mesh.primitive_cube_add": {
                "full_name": "bpy.ops.mesh.primitive_cube_add",
                "parameters": [
                    {"name": "size", "type": "float", "default": "2.0", "optional": True},
                    {"name": "location", "type": "array", "default": "[0, 0, 0]", "optional": True}
                ]
            },
            "bpy.ops.transform.translate": {
                "full_name": "bpy.ops.transform.translate",
                "parameters": [
                    {"name": "value", "type": "array", "default": "[0, 0, 0]", "optional": True},
                    {"name": "constraint_axis", "type": "array", "default": "[False, False, False]", "optional": True}
                ]
            },
            "bpy.ops.transform.resize": {
                "full_name": "bpy.ops.transform.resize",
                "parameters": [
                    {"name": "value", "type": "array", "default": "[1, 1, 1]", "optional": True}
                ]
            }
        }
    
    def _build_parameter_index(self) -> None:
        """Build fast lookup index for parameter types"""
        for api_name, api_info in self.api_registry.items():
            self.parameter_types[api_name] = {}
            for param in api_info.get("parameters", []):
                param_name = param.get("name", "")
                param_type = param.get("type", "unknown")
                self.parameter_types[api_name][param_name] = param_type
    
    def _initialize_corrections(self) -> None:
        """Initialize common API name corrections"""
        self.common_corrections = {
            # Common LLM mistakes -> Correct API names
            "bpy.ops.mesh.add_sphere": "bpy.ops.mesh.primitive_uv_sphere_add",
            "bpy.ops.mesh.add_cube": "bpy.ops.mesh.primitive_cube_add",
            "bpy.ops.mesh.add_cylinder": "bpy.ops.mesh.primitive_cylinder_add",
            "bpy.ops.object.move": "bpy.ops.transform.translate",
            "bpy.ops.object.scale": "bpy.ops.transform.resize",
            "bpy.ops.object.rotate": "bpy.ops.transform.rotate",
            "bpy.ops.mesh.sphere_add": "bpy.ops.mesh.primitive_uv_sphere_add",
            "bpy.ops.mesh.cube_add": "bpy.ops.mesh.primitive_cube_add",
        }
    
    def validate_api_call(self, api_name: str, parameters: Dict[str, Any], 
                         validation_level: ValidationLevel = ValidationLevel.CORRECTIVE) -> ValidationResult:
        """
        Validate a single API call against the registry
        
        Args:
            api_name: The Blender API name (e.g., "bpy.ops.mesh.primitive_uv_sphere_add")
            parameters: Dictionary of parameters to validate
            validation_level: How strict to be with validation
            
        Returns:
            ValidationResult with validation status and corrections
        """
        errors = []
        warnings = []
        auto_corrections = []
        corrected_parameters = parameters.copy()
        
        # Step 1: Validate API name exists
        original_api_name = api_name
        if api_name not in self.api_registry:
            # Try to find correction
            corrected_name = self._correct_api_name(api_name)
            if corrected_name:
                api_name = corrected_name
                auto_corrections.append(f"Corrected API name: {original_api_name} → {api_name}")
            else:
                errors.append(f"Unknown API: {api_name}")
                return ValidationResult(
                    valid=False,
                    api_name=original_api_name,
                    corrected_parameters=corrected_parameters,
                    errors=errors,
                    warnings=warnings,
                    auto_corrections=auto_corrections
                )
        
        # Step 2: Get API specification
        api_spec = self.api_registry[api_name]
        valid_params = {p["name"]: p for p in api_spec.get("parameters", [])}
        
        # Step 3: Validate each parameter
        cleaned_parameters = {}
        
        for param_name, param_value in parameters.items():
            # Skip invalid operator parameters that cause crashes
            if self._is_invalid_operator_param(param_name):
                auto_corrections.append(f"Removed invalid operator parameter: {param_name}")
                continue
            
            # Check if parameter exists for this API
            if param_name not in valid_params:
                # Try to find similar parameter name
                corrected_name = self._correct_parameter_name(param_name, list(valid_params.keys()))
                if corrected_name:
                    param_spec = valid_params[corrected_name]
                    corrected_value = self._validate_parameter_value(
                        corrected_name, param_value, param_spec, validation_level
                    )
                    cleaned_parameters[corrected_name] = corrected_value
                    auto_corrections.append(f"Corrected parameter: {param_name} → {corrected_name}")
                    if corrected_value != param_value:
                        auto_corrections.append(f"Corrected {corrected_name}: {param_value} → {corrected_value}")
                else:
                    if validation_level == ValidationLevel.STRICT:
                        errors.append(f"Invalid parameter '{param_name}' for API {api_name}")
                    else:
                        warnings.append(f"Unknown parameter '{param_name}' removed")
                continue
            
            # Validate parameter type and value
            param_spec = valid_params[param_name]
            corrected_value = self._validate_parameter_value(
                param_name, param_value, param_spec, validation_level
            )
            
            if corrected_value != param_value:
                auto_corrections.append(f"Corrected {param_name}: {param_value} → {corrected_value}")
            
            cleaned_parameters[param_name] = corrected_value
        
        # Step 4: Add missing required parameters with defaults (skip this for now to avoid clutter)
        # This was adding too many unnecessary parameters
        pass
        
        corrected_parameters = cleaned_parameters
        is_valid = len(errors) == 0
        
        return ValidationResult(
            valid=is_valid,
            api_name=api_name,
            corrected_parameters=corrected_parameters,
            errors=errors,
            warnings=warnings,
            auto_corrections=auto_corrections
        )
    
    def validate_api_batch(self, api_calls: List[Dict[str, Any]], 
                          validation_level: ValidationLevel = ValidationLevel.CORRECTIVE) -> List[ValidationResult]:
        """Validate a batch of API calls"""
        results = []
        
        for call in api_calls:
            api_name = call.get("api_name", "")
            parameters = call.get("parameters", {})
            
            result = self.validate_api_call(api_name, parameters, validation_level)
            results.append(result)
        
        return results
    
    def _correct_api_name(self, api_name: str) -> Optional[str]:
        """Try to correct invalid API names"""
        # Direct lookup in corrections
        if api_name in self.common_corrections:
            return self.common_corrections[api_name]
        
        # Fuzzy matching for similar names
        for valid_name in self.api_registry.keys():
            if self._similarity_score(api_name, valid_name) > 0.8:
                return valid_name
        
        return None
    
    def _correct_parameter_name(self, param_name: str, valid_names: List[str]) -> Optional[str]:
        """Try to correct invalid parameter names"""
        # Exact match (case insensitive)
        for valid_name in valid_names:
            if param_name.lower() == valid_name.lower():
                return valid_name
        
        # Fuzzy matching
        best_match = None
        best_score = 0.7  # Minimum similarity threshold
        
        for valid_name in valid_names:
            score = self._similarity_score(param_name, valid_name)
            if score > best_score:
                best_score = score
                best_match = valid_name
        
        return best_match
    
    def _validate_parameter_value(self, param_name: str, value: Any, 
                                 param_spec: Dict[str, Any], validation_level: ValidationLevel) -> Any:
        """Validate and correct parameter value"""
        expected_type = param_spec.get("type", "unknown")
        
        # Type conversion and validation
        try:
            if expected_type == "float":
                return float(value) if value is not None else 1.0
            elif expected_type == "int":
                return int(float(value)) if value is not None else 1
            elif expected_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)
            elif expected_type == "array":
                if isinstance(value, (list, tuple)):
                    return list(value)
                elif isinstance(value, str):
                    # Try to parse string representation of array
                    try:
                        if value.startswith('[') and value.endswith(']'):
                            parsed = eval(value)
                            return list(parsed) if isinstance(parsed, (list, tuple)) else [0, 0, 0]
                        else:
                            # Single value, convert to float and make single-element list
                            return [float(value)]
                    except:
                        return [0, 0, 0]  # Default 3D vector
                return [0, 0, 0]
            elif expected_type == "string":
                return str(value)
            else:
                return value
        except (ValueError, TypeError):
            # Return safe default for the type
            return self._get_default_value(param_spec)
    
    def _get_default_value(self, param_spec: Dict[str, Any]) -> Any:
        """Get safe default value for parameter"""
        default = param_spec.get("default")
        param_type = param_spec.get("type", "unknown")
        
        if default is not None:
            try:
                if param_type == "array" and isinstance(default, str):
                    return eval(default)
                elif param_type == "float":
                    return float(default)
                elif param_type == "int":
                    return int(float(default))
                elif param_type == "boolean":
                    return bool(default)
                return default
            except:
                pass
        
        # Type-based defaults
        type_defaults = {
            "float": 1.0,
            "int": 1,
            "boolean": True,
            "array": [0, 0, 0],
            "string": "",
            "unknown": None
        }
        
        return type_defaults.get(param_type, None)
    
    def _is_invalid_operator_param(self, param_name: str) -> bool:
        """Check if parameter name is an invalid operator combination"""
        invalid_patterns = [
            "OBJECT_OT_", "TRANSFORM_OT_", "MESH_OT_", "EDIT_OT_",
            "VIEW3D_OT_", "SCREEN_OT_", "WM_OT_"
        ]
        return any(pattern in param_name for pattern in invalid_patterns)
    
    def _similarity_score(self, str1: str, str2: str) -> float:
        """Calculate similarity score between two strings"""
        # Simple Levenshtein-based similarity
        if not str1 or not str2:
            return 0.0
        
        # Normalize strings
        s1, s2 = str1.lower(), str2.lower()
        
        # Calculate edit distance
        if len(s1) < len(s2):
            s1, s2 = s2, s1
        
        if len(s2) == 0:
            return 0.0
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        edit_distance = previous_row[-1]
        max_len = max(len(s1), len(s2))
        
        return 1.0 - (edit_distance / max_len)
    
    def get_api_suggestions(self, partial_name: str, limit: int = 5) -> List[str]:
        """Get API suggestions for partial names"""
        suggestions = []
        partial_lower = partial_name.lower()
        
        for api_name in self.api_registry.keys():
            if partial_lower in api_name.lower():
                suggestions.append(api_name)
        
        # Sort by similarity and return top matches
        suggestions.sort(key=lambda x: self._similarity_score(partial_name, x), reverse=True)
        return suggestions[:limit]
    
    def get_parameter_info(self, api_name: str) -> Dict[str, Any]:
        """Get detailed parameter information for an API"""
        if api_name not in self.api_registry:
            return {}
        
        api_spec = self.api_registry[api_name]
        return {
            "api_name": api_name,
            "description": api_spec.get("description", ""),
            "parameters": api_spec.get("parameters", []),
            "category": api_spec.get("category", "unknown"),
            "examples": api_spec.get("examples", [])
        }
    
    def generate_validation_report(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        total_calls = len(results)
        valid_calls = sum(1 for r in results if r.valid)
        total_corrections = sum(len(r.auto_corrections) for r in results)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        return {
            "summary": {
                "total_api_calls": total_calls,
                "valid_calls": valid_calls,
                "invalid_calls": total_calls - valid_calls,
                "success_rate": (valid_calls / total_calls * 100) if total_calls > 0 else 0,
                "total_corrections": total_corrections,
                "total_errors": total_errors,
                "total_warnings": total_warnings
            },
            "details": [
                {
                    "api_name": r.api_name,
                    "valid": r.valid,
                    "corrections": r.auto_corrections,
                    "errors": r.errors,
                    "warnings": r.warnings
                } for r in results
            ]
        }

# Factory function
def create_api_validator(registry_path: str = None) -> BlenderAPIValidator:
    """Create API validator instance"""
    if registry_path is None:
        registry_path = "d:/code/capstone/blender_api_registry.json"
    
    return BlenderAPIValidator(registry_path)
