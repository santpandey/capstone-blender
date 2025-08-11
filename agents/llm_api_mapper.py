"""
LLM-based API Mapper for Blender Operations
Inspired by EAG-V17's model_manager.py approach
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from dotenv import load_dotenv

from .models import SubTask, APIMapping
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
            api_calls = self._parse_api_response(response)
            
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
        
        # Step 4: Fix single quotes 'WORLD' -> "WORLD"
        response = re.sub(r"'([^']*)'", r'"\1"', response)
        
        # Step 5: Remove invalid parameter references
        response = re.sub(r'"material":\s*bpy\.data\.materials\[[^\]]+\]', '"material": "WhiteMaterial"', response)
        
        # Step 6: Convert Python literals
        response = response.replace('None', 'null')
        response = response.replace('True', 'true')
        response = response.replace('False', 'false')
        
        # Step 7: Remove trailing commas
        response = re.sub(r',(\s*[}\]])', r'\1', response)
        
        # Step 8: Handle smart quotes
        response = response.replace('"', '"').replace('"', '"')
        response = response.replace(''', "'").replace(''', "'")
        
        return response.strip()

    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response and extract API calls"""
        
        try:
            # Clean the response first
            cleaned_response = self._clean_json_response(response)
            
            # Try to parse as JSON
            if cleaned_response.startswith('{') and '"api_calls"' in cleaned_response:
                # Response is wrapped in an object
                data = json.loads(cleaned_response)
                api_calls = data.get("api_calls", [])
            elif cleaned_response.startswith('['):
                # Response is a direct array
                api_calls = json.loads(cleaned_response)
            else:
                raise ValueError("Response doesn't start with { or [")
            
            if not isinstance(api_calls, list):
                raise ValueError("API calls must be a JSON array")
            
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
        """Validate and clean API calls structure"""
        validated_calls = []
        for call in api_calls:
            if isinstance(call, dict) and "api_name" in call:
                validated_calls.append({
                    "api_name": call.get("api_name", ""),
                    "parameters": call.get("parameters", {}),
                    "description": call.get("description", ""),
                    "execution_order": call.get("execution_order", len(validated_calls) + 1)
                })
        return validated_calls
    
    def _fallback_mapping(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """Fallback mapping when LLM fails"""
        
        fallback_apis = []
        
        # Basic fallback based on subtask type and operations
        if subtask.type.value == "CREATE_CHARACTER":
            fallback_apis = [
                {
                    "api_name": "bpy.ops.mesh.primitive_cube_add",
                    "parameters": {"size": 2.0, "location": [0, 0, 1]},
                    "description": "Add cube for torso",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_uv_sphere_add",
                    "parameters": {"radius": 0.5, "location": [0, 0, 2.5]},
                    "description": "Add sphere for head",
                    "execution_order": 2
                }
            ]
        elif subtask.type.value == "CREATE_FURNITURE":
            fallback_apis = [
                {
                    "api_name": "bpy.ops.mesh.primitive_cube_add",
                    "parameters": {"size": 1.0, "location": [0, 0, 0.5]},
                    "description": "Add cube for furniture base",
                    "execution_order": 1
                }
            ]
        
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
