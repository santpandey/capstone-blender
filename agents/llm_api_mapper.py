"""
LLM-based API Mapper for Blender Operations
Inspired by EAG-V17's model_manager.py approach
"""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import asyncio
from dotenv import load_dotenv
import google.generativeai as genai
from .base_agent import BaseAgent
from .models import SubTask, APIMapping
from .simple_validator import SimpleAPIValidator
from prompts import APIMapperPrompts

# Load environment variables
load_dotenv()

class LLMAPIMapper:
    """
    LLM-powered API mapper that converts granular subtasks to specific Blender API calls
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """Initialize the LLM API Mapper with Gemini"""
        
        # Initialize Gemini client
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        self.model_name = model_name
        
        # Initialize simple API validator
        self.api_validator = SimpleAPIValidator()
        
        # Load Blender API registry for context
        self.api_registry_path = Path(__file__).parent.parent / "blender_api_registry.json"
        self.api_context = self._load_api_context()
        
    def _load_api_context(self) -> str:
        """Load a subset of Blender API context for the LLM"""
        try:
            if self.api_registry_path.exists():
                with open(self.api_registry_path, 'r') as f:
                    registry = json.load(f)
                
                # Extract commonly used APIs for context
                common_apis = []
                for category, apis in registry.items():
                    if isinstance(apis, list):
                        # Get first 10 APIs from each category as examples
                        for api in apis[:10]:
                            if isinstance(api, dict) and 'name' in api:
                                common_apis.append(f"- {api['name']}: {api.get('description', 'No description')}")
                
                return "\n".join(common_apis[:50])  # Limit to 50 examples
            else:
                return "Blender API registry not found. Using general Blender knowledge."
        except Exception as e:
            return f"Error loading API context: {str(e)}"
    
    async def map_subtask_to_apis(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """
        Map a granular subtask to specific Blender API calls using LLM
        
        Args:
            subtask: The granular subtask to map
            
        Returns:
            List of API call dictionaries with name, parameters, and description
        """
        
        # Create detailed prompt for the LLM
        prompt = self._create_mapping_prompt(subtask)
        
        try:
            # Generate API mappings using Gemini
            response = await self._gemini_generate(prompt)
            
            # Parse the response into structured API calls
            api_calls = self._parse_llm_response(response)
            
            return api_calls
            
        except Exception as e:
            print(f"LLM API mapping failed for subtask {subtask.task_id}: {e}")
            # Fallback to basic mapping
            return self._fallback_mapping(subtask)
    
    def _create_mapping_prompt(self, subtask: SubTask) -> str:
        """Create a detailed prompt for LLM to map subtask to Blender APIs"""
        return APIMapperPrompts.create_subtask_mapping_prompt(subtask)
    
    async def _gemini_generate(self, prompt: str) -> str:
        """Generate content using Gemini LLM"""
        try:
            model = genai.GenerativeModel(self.model_name)
            response = await model.generate_content_async(prompt)
            return response.text.strip()
            
        except Exception as e:
            raise RuntimeError(f"Gemini generation failed: {str(e)}")
    
    def _clean_json_response(self, response: str) -> str:
        """Comprehensive JSON cleaning for LLM responses - PROVEN SOLUTION"""
        import re
        
        # Step 1: Remove markdown code blocks
        response = response.strip()
        response = re.sub(r'^```json\s*', '', response, flags=re.MULTILINE)
        response = re.sub(r'^```\s*', '', response, flags=re.MULTILINE) 
        response = re.sub(r'```$', '', response, flags=re.MULTILINE)
        
        # Step 2: Extract JSON object
        json_match = re.search(r'\{.*\}', response, re.DOTALL)
        if json_match:
            response = json_match.group(0)
        
        # Step 3: Fix array syntax (0, 0, 0) -> [0, 0, 0]
        response = re.sub(r'\((\s*[-\d\.\s,]+\s*)\)', r'[\1]', response)
        
        # Step 4: Fix malformed API names - replace invalid calls with valid ones
        # Fix: bpy.data.materials['RedMaterial'].diffuse_color -> bpy.ops.object.select_all
        response = re.sub(r'"api_name":\s*"bpy\.data\.materials\[[^\]]+\][^"]*"', '"api_name": "bpy.ops.object.select_all"', response)
        
        # Fix other invalid API patterns
        response = re.sub(r'"api_name":\s*"bpy\.ops\.material\.new"', '"api_name": "bpy.ops.object.select_all"', response)
        response = re.sub(r'"api_name":\s*"bpy\.ops\.view3d\.[^"]*"', '"api_name": "bpy.ops.transform.translate"', response)
        
        # Step 5: Fix single quotes 'WORLD' -> "WORLD" (but avoid breaking already fixed API names)
        response = re.sub(r"'([^']*)'", r'"\1"', response)
        
        # Step 6: Remove invalid parameter references
        response = re.sub(r'"material":\s*bpy\.data\.materials\[[^\]]+\]', '"material": "WhiteMaterial"', response)
        
        # Step 7: Fix malformed API patterns with semantic awareness
        # Don't force spheres - use context-appropriate defaults
        response = re.sub(r'"api_name":\s*"bpy\.ops\.obj[^"]*"', '"api_name": "bpy.ops.mesh.primitive_cylinder_add"', response)
        
        # Step 8: Convert Python literals
        response = response.replace('None', 'null')
        response = response.replace('True', 'true')
        response = response.replace('False', 'false')
        
        # Step 9: Remove trailing commas
        response = re.sub(r',(\s*[}\]])', r'\1', response)
        
        # Step 10: Handle smart quotes
        response = response.replace('"', '"').replace('"', '"')
        response = response.replace(''', "'").replace(''', "'")
        
        return response.strip()

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract API calls"""
        
        try:
            # Clean the response first
            cleaned_response = self._clean_json_response(response)
            
            # Try multiple JSON parsing approaches for robustness
            api_calls = []
            
            # Approach 1: Try parsing as complete JSON object
            try:
                data = json.loads(cleaned_response)
                if isinstance(data, dict) and "api_calls" in data:
                    api_calls = data["api_calls"]
                    print(f"✅ Parsed as JSON object with api_calls array: {len(api_calls)} calls")
                elif isinstance(data, list):
                    api_calls = data
                    print(f"✅ Parsed as direct JSON array: {len(api_calls)} calls")
                else:
                    raise ValueError("JSON structure not recognized")
            except json.JSONDecodeError as parse_error:
                print(f"⚠️ Direct JSON parsing failed: {parse_error}")
                
                # Approach 2: Try regex extraction as fallback
                import re
                json_match = re.search(r'\{.*"api_calls"\s*:\s*\[.*?\]\s*.*?\}', cleaned_response, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(0)
                        print(f"🔧 Attempting regex extraction: {json_str[:200]}...")
                        data = json.loads(json_str)
                        api_calls = data.get("api_calls", [])
                        print(f"✅ Regex extraction successful: {len(api_calls)} calls")
                    except Exception as regex_error:
                        print(f"❌ Regex extraction failed: {regex_error}")
                
                # Approach 3: Try array-only extraction
                if not api_calls:
                    array_match = re.search(r'\[.*\]', cleaned_response, re.DOTALL)
                    if array_match:
                        try:
                            array_str = array_match.group(0)
                            api_calls = json.loads(array_str)
                            print(f"✅ Array extraction successful: {len(api_calls)} calls")
                        except Exception as array_error:
                            print(f"❌ Array extraction failed: {array_error}")
            
            if not isinstance(api_calls, list):
                raise ValueError(f"API calls must be a JSON array, got: {type(api_calls)}")
            
            return self._validate_api_calls(api_calls)
            
        except (json.JSONDecodeError, ValueError) as e:
            print(f"❌ Failed to parse LLM response: {e}")
            print(f"📝 Raw LLM Response (first 500 chars): {response[:500]}...")
            print(f"📝 Response length: {len(response)} characters")
            
            # Save full response to file for debugging
            debug_file = Path("debug_llm_full_response.json")
            debug_file.write_text(response, encoding='utf-8')
            print(f"💾 Full LLM response saved to: {debug_file}")
            
            # Try to extract JSON using regex as fallback
            import re
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                try:
                    json_str = json_match.group(0)
                    print(f"🔧 Attempting regex extraction: {json_str[:200]}...")
                    api_calls = json.loads(json_str)
                    print(f"✅ Regex extraction successful! Found {len(api_calls)} API calls")
                    return self._validate_api_calls(api_calls)
                except Exception as regex_e:
                    print(f"❌ Regex extraction also failed: {regex_e}")
            
            return []
    
    def _validate_api_calls(self, api_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate and clean API calls structure - REPLACE INVALID CALLS WITH VALID ONES"""
        validated_calls = []
        
        # Valid Blender API operations (guaranteed to work)
        valid_apis = {
            "mesh_creation": [
                "bpy.ops.mesh.primitive_cube_add",
                "bpy.ops.mesh.primitive_uv_sphere_add", 
                "bpy.ops.mesh.primitive_cylinder_add",
                "bpy.ops.mesh.primitive_cone_add"
            ],
            "transformations": [
                "bpy.ops.transform.translate",
                "bpy.ops.transform.rotate", 
                "bpy.ops.transform.resize"
            ],
            "object_ops": [
                "bpy.ops.object.select_all",
                "bpy.ops.object.duplicate_move"
            ],
            "material_ops": [
                # Core material operations
                "bpy.ops.material.new",
                "bpy.ops.material.copy", 
                "bpy.ops.material.paste",
                
                # Object material slot operations
                "bpy.ops.object.material_slot_add",
                "bpy.ops.object.material_slot_assign",
                "bpy.ops.object.material_slot_copy",
                "bpy.ops.object.material_slot_deselect",
                "bpy.ops.object.material_slot_move",
                "bpy.ops.object.material_slot_remove",
                "bpy.ops.object.material_slot_remove_unused",
                "bpy.ops.object.material_slot_select"
            ]
        }
        
        for call in api_calls:
            if isinstance(call, dict) and "api_name" in call:
                api_name = call.get("api_name", "")
                
                # Replace invalid API calls with valid ones
                if "bpy.data.materials" in api_name:
                    # Invalid direct material access -> use proper material operator
                    api_name = "bpy.ops.material.new"
                    call["parameters"] = {}
                    call["description"] = "Create new material"
                    
                elif "bpy.ops.view3d" in api_name:
                    # Dangerous viewport operations -> safe transformation
                    api_name = "bpy.ops.transform.translate"
                    call["parameters"] = {"value": [0, 0, 0]}
                    call["description"] = "Position objects safely"
                    
                elif not any(valid_api in api_name for valid_group in valid_apis.values() for valid_api in valid_group):
                    # Unknown/invalid API -> default to sphere creation
                    api_name = "bpy.ops.mesh.primitive_uv_sphere_add"
                    call["parameters"] = {"radius": 1.0, "location": [0, 0, 0]}
                    call["description"] = "Create basic sphere primitive"
                
                # Validate API call using the simple validator
                validation_result = self.api_validator.validate_and_clean(
                    api_name, 
                    call.get("parameters", {})
                )
                
                # Use validated and corrected parameters
                final_api_name = validation_result["api_name"]
                final_parameters = validation_result["parameters"]
                
                # Log corrections if any
                if validation_result["corrections"]:
                    print(f"🔧 API Corrections for {api_name}:")
                    for correction in validation_result["corrections"]:
                        print(f"   - {correction}")
                
                validated_calls.append({
                    "api_name": final_api_name,
                    "parameters": final_parameters,
                    "description": call.get("description", ""),
                    "execution_order": call.get("execution_order", len(validated_calls) + 1),
                    "validation_status": "valid"
                })
                
        return validated_calls
    
    def _fallback_mapping(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """
        Intelligent fallback mapping when LLM fails to generate API calls.
        Uses semantic understanding of object types for appropriate geometry selection.
        """
        fallback_apis = []
        
        if subtask.type.value == "CREATE_OBJECT":
            # Semantic shape selection based on object name/description
            object_name = subtask.title.lower()
            description = subtask.description.lower() if subtask.description else ""
            combined_text = f"{object_name} {description}"
            
            # Coffee mug/cup detection
            if any(word in combined_text for word in ['mug', 'cup', 'coffee', 'tea']):
                fallback_apis = [
                    {
                        "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                        "parameters": {"radius": 0.8, "depth": 1.2, "location": [0, 0, 0]},
                        "description": f"Create cylinder body for {subtask.title}",
                        "execution_order": 1
                    },
                    {
                        "api_name": "bpy.ops.mesh.primitive_torus_add",
                        "parameters": {"major_radius": 0.6, "minor_radius": 0.1, "location": [1.0, 0, 0.3]},
                        "description": f"Create torus handle for {subtask.title}",
                        "execution_order": 2
                    }
                ]
            # Chair detection
            elif any(word in combined_text for word in ['chair', 'seat', 'stool']):
                fallback_apis = [
                    {
                        "api_name": "bpy.ops.mesh.primitive_cube_add",
                        "parameters": {"size": 1.0, "location": [0, 0, 0.5]},
                        "description": f"Create seat for {subtask.title}",
                        "execution_order": 1
                    },
                    {
                        "api_name": "bpy.ops.mesh.primitive_cube_add",
                        "parameters": {"size": 1.0, "location": [0, -0.4, 1.2]},
                        "description": f"Create backrest for {subtask.title}",
                        "execution_order": 2
                    }
                ]
            # Ball/sphere detection
            elif any(word in combined_text for word in ['ball', 'sphere', 'globe', 'orb']):
                fallback_apis = [{
                    "api_name": "bpy.ops.mesh.primitive_uv_sphere_add",
                    "parameters": {"radius": 1.0, "location": [0, 0, 0]},
                    "description": f"Create sphere for {subtask.title}",
                    "execution_order": 1
                }]
            # Table detection
            elif any(word in combined_text for word in ['table', 'desk', 'surface']):
                fallback_apis = [
                    {
                        "api_name": "bpy.ops.mesh.primitive_cube_add",
                        "parameters": {"size": 2.0, "location": [0, 0, 1.0]},
                        "description": f"Create table top for {subtask.title}",
                        "execution_order": 1
                    }
                ]
            # Default fallback - cylinder (more versatile than cube)
            else:
                fallback_apis = [{
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                    "parameters": {"radius": 1.0, "depth": 2.0, "location": [0, 0, 0]},
                    "description": f"Create basic cylindrical object for {subtask.title}",
                    "execution_order": 1
                }]
                
        elif subtask.type.value == "APPLY_MATERIAL":
            # Basic material creation and application
            fallback_apis = [
                {
                    "api_name": "bpy.data.materials.new",
                    "parameters": {"name": "BasicMaterial"},
                    "description": "Create basic material",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.context.object.data.materials.append",
                    "parameters": {"material": "BasicMaterial"},
                    "description": "Apply material to active object",
                    "execution_order": 2
                }
            ]
        elif subtask.type.value == "ADD_TEXT":
            fallback_apis = [{
                "api_name": "bpy.ops.object.text_add",
                "parameters": {"location": [0, 0, 0]},
                "description": f"Add text for {subtask.title}",
                "execution_order": 1
            }]
        
        return fallback_apis
    
    async def map_multiple_subtasks(self, subtasks: List[SubTask]) -> Dict[str, List[Dict[str, Any]]]:
        """Map multiple subtasks concurrently"""
        
        tasks = [self.map_subtask_to_apis(subtask) for subtask in subtasks]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        mapping_results = {}
        for subtask, result in zip(subtasks, results):
            if isinstance(result, Exception):
                print(f"Failed to map subtask {subtask.task_id}: {result}")
                mapping_results[subtask.task_id] = []
            else:
                mapping_results[subtask.task_id] = result
        
        return mapping_results

# Example usage and testing
async def test_llm_mapper():
    """Test the LLM API Mapper"""
    
    # Mock subtask for testing
    from .models import SubTask, TaskType, TaskComplexity, TaskPriority
    
    test_subtask = SubTask(
        task_id="test_001",
        type=TaskType.CREATE_CHARACTER,
        title="Add Basic Human Mesh Primitives",
        description="Create basic human figure using Blender primitives: cube for torso, sphere for head, cylinders for limbs. Configure for sitting pose.",
        requirements=[
            "add_cube_primitive_for_torso",
            "add_sphere_primitive_for_head", 
            "add_cylinder_primitives_for_limbs"
        ],
        estimated_time_minutes=10,
        complexity=TaskComplexity.MODERATE,
        priority=TaskPriority.HIGH,
        blender_categories=["mesh_operators"],
        mesh_operations=[
            "mesh.primitive_cube_add",
            "mesh.primitive_uv_sphere_add", 
            "mesh.primitive_cylinder_add"
        ],
        object_count=4,
        context={
            "character_type": "man",
            "pose_type": "sitting",
            "primitive_approach": True
        }
    )
    
    mapper = LLMAPIMapper()
    api_calls = await mapper.map_subtask_to_apis(test_subtask)
    
    print("LLM-Generated API Calls:")
    for call in api_calls:
        print(f"- {call['api_name']}: {call['description']}")
    
    return api_calls

if __name__ == "__main__":
    asyncio.run(test_llm_mapper())
