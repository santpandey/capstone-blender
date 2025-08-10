"""
Mock LLM-based API Mapper for testing the concept
This simulates what the real Gemini LLM would do for Blender API mapping
"""

import asyncio
from typing import List, Dict, Any
from .models import SubTask, TaskType

class MockLLMAPIMapper:
    """
    Mock LLM-powered API mapper that simulates intelligent mapping
    of granular subtasks to specific Blender API calls
    """
    
    def __init__(self):
        """Initialize the mock LLM API Mapper"""
        self.api_knowledge_base = self._create_api_knowledge_base()
        
    def _create_api_knowledge_base(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create a knowledge base of common Blender API patterns"""
        return {
            # Character creation patterns
            "human_mesh_primitives": [
                {
                    "api_name": "bpy.ops.mesh.primitive_cube_add",
                    "parameters": {"size": 2.0, "location": [0, 0, 1]},
                    "description": "Add cube primitive for torso",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_uv_sphere_add", 
                    "parameters": {"radius": 0.5, "location": [0, 0, 2.5]},
                    "description": "Add sphere primitive for head",
                    "execution_order": 2
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                    "parameters": {"radius": 0.2, "depth": 1.5, "location": [-0.8, 0, 1]},
                    "description": "Add cylinder primitive for left arm",
                    "execution_order": 3
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                    "parameters": {"radius": 0.2, "depth": 1.5, "location": [0.8, 0, 1]},
                    "description": "Add cylinder primitive for right arm", 
                    "execution_order": 4
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                    "parameters": {"radius": 0.25, "depth": 1.8, "location": [-0.4, 0, -0.5]},
                    "description": "Add cylinder primitive for left leg",
                    "execution_order": 5
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add", 
                    "parameters": {"radius": 0.25, "depth": 1.8, "location": [0.4, 0, -0.5]},
                    "description": "Add cylinder primitive for right leg",
                    "execution_order": 6
                }
            ],
            
            # Chair creation patterns
            "chair_mesh_primitives": [
                {
                    "api_name": "bpy.ops.mesh.primitive_cube_add",
                    "parameters": {"size": 1.0, "location": [0, 0, 0.5]},
                    "description": "Add cube primitive for chair seat",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.transform.resize",
                    "parameters": {"value": [1.2, 1.0, 0.1]},
                    "description": "Scale seat to proper proportions",
                    "execution_order": 2
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cube_add",
                    "parameters": {"size": 1.0, "location": [0, -0.45, 1.2]},
                    "description": "Add cube primitive for chair backrest",
                    "execution_order": 3
                },
                {
                    "api_name": "bpy.ops.transform.resize",
                    "parameters": {"value": [1.2, 0.1, 1.4]},
                    "description": "Scale backrest to proper proportions",
                    "execution_order": 4
                },
                {
                    "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                    "parameters": {"radius": 0.05, "depth": 0.5, "location": [0.5, 0.4, 0.25]},
                    "description": "Add cylinder primitive for front-right leg",
                    "execution_order": 5
                },
                {
                    "api_name": "bpy.ops.object.duplicate",
                    "parameters": {"linked": False},
                    "description": "Duplicate leg for other positions",
                    "execution_order": 6
                }
            ],
            
            # Lighting setup patterns
            "scene_lighting": [
                {
                    "api_name": "bpy.ops.object.light_add",
                    "parameters": {"type": "SUN", "location": [2, 2, 4]},
                    "description": "Add sun light for main illumination",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.transform.rotate",
                    "parameters": {"value": 0.52, "orient_axis": "X"},
                    "description": "Rotate light to 30 degrees from head",
                    "execution_order": 2
                }
            ],
            
            # Material application patterns
            "material_application": [
                {
                    "api_name": "bpy.ops.material.new",
                    "parameters": {},
                    "description": "Create new material",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.object.material_slot_add",
                    "parameters": {},
                    "description": "Add material slot to object",
                    "execution_order": 2
                }
            ],
            
            # Scene composition patterns
            "scene_composition": [
                {
                    "api_name": "bpy.ops.transform.translate",
                    "parameters": {"value": [0, 0, 0.5]},
                    "description": "Position character on chair",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.transform.rotate",
                    "parameters": {"value": 1.57, "orient_axis": "Z"},
                    "description": "Rotate for proper sitting orientation",
                    "execution_order": 2
                }
            ]
        }
    
    async def map_subtask_to_apis(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """
        Mock intelligent mapping of granular subtask to specific Blender API calls
        
        Args:
            subtask: The granular subtask to map
            
        Returns:
            List of API call dictionaries with name, parameters, and description
        """
        
        # Simulate LLM processing time
        await asyncio.sleep(0.1)
        
        # Intelligent pattern matching based on subtask content
        title_lower = subtask.title.lower()
        description_lower = subtask.description.lower()
        
        # Pattern matching logic (simulating what LLM would do)
        if "human" in title_lower or "character" in title_lower:
            if "mesh primitives" in title_lower:
                return self.api_knowledge_base["human_mesh_primitives"]
        
        elif "chair" in title_lower:
            if "mesh primitives" in title_lower:
                return self.api_knowledge_base["chair_mesh_primitives"]
        
        elif "lighting" in title_lower or subtask.type == TaskType.LIGHTING_SETUP:
            return self.api_knowledge_base["scene_lighting"]
        
        elif "material" in title_lower or subtask.type == TaskType.MATERIAL_APPLICATION:
            return self.api_knowledge_base["material_application"]
        
        elif "compose" in title_lower or subtask.type == TaskType.SCENE_COMPOSITION:
            return self.api_knowledge_base["scene_composition"]
        
        # Fallback: analyze mesh operations from subtask
        if hasattr(subtask, 'mesh_operations') and subtask.mesh_operations:
            fallback_apis = []
            for i, operation in enumerate(subtask.mesh_operations[:3], 1):  # Limit to 3 operations
                if "cube" in operation:
                    fallback_apis.append({
                        "api_name": "bpy.ops.mesh.primitive_cube_add",
                        "parameters": {"size": 1.0},
                        "description": f"Add cube primitive from mesh operation: {operation}",
                        "execution_order": i
                    })
                elif "sphere" in operation:
                    fallback_apis.append({
                        "api_name": "bpy.ops.mesh.primitive_uv_sphere_add", 
                        "parameters": {"radius": 0.5},
                        "description": f"Add sphere primitive from mesh operation: {operation}",
                        "execution_order": i
                    })
                elif "cylinder" in operation:
                    fallback_apis.append({
                        "api_name": "bpy.ops.mesh.primitive_cylinder_add",
                        "parameters": {"radius": 0.3, "depth": 1.0},
                        "description": f"Add cylinder primitive from mesh operation: {operation}",
                        "execution_order": i
                    })
                elif "resize" in operation or "scale" in operation:
                    fallback_apis.append({
                        "api_name": "bpy.ops.transform.resize",
                        "parameters": {"value": [1.0, 1.0, 1.0]},
                        "description": f"Scale object from mesh operation: {operation}",
                        "execution_order": i
                    })
                elif "translate" in operation or "position" in operation:
                    fallback_apis.append({
                        "api_name": "bpy.ops.transform.translate",
                        "parameters": {"value": [0, 0, 0]},
                        "description": f"Position object from mesh operation: {operation}",
                        "execution_order": i
                    })
            
            if fallback_apis:
                return fallback_apis
        
        # Final fallback: generic object creation
        return [
            {
                "api_name": "bpy.ops.mesh.primitive_cube_add",
                "parameters": {"size": 1.0},
                "description": f"Generic object creation for: {subtask.title}",
                "execution_order": 1
            }
        ]

# Example usage and testing
async def test_mock_llm_mapper():
    """Test the Mock LLM API Mapper"""
    
    from .models import SubTask, TaskType, TaskComplexity, TaskPriority
    
    # Test character creation
    character_subtask = SubTask(
        task_id="test_001",
        type=TaskType.CREATE_CHARACTER,
        title="Add Basic Human Mesh Primitives",
        description="Create basic human figure using Blender primitives: cube for torso, sphere for head, cylinders for limbs. Configure for sitting pose.",
        requirements=[
            "add_cube_primitive_for_torso",
            "add_sphere_primitive_for_head"
        ],
        estimated_time_minutes=10,
        complexity=TaskComplexity.MODERATE,
        priority=TaskPriority.HIGH,
        blender_categories=["mesh_operators"],
        mesh_operations=[
            "mesh.primitive_cube_add",
            "mesh.primitive_uv_sphere_add"
        ],
        object_count=4,
        context={"character_type": "man", "pose_type": "sitting"}
    )
    
    mapper = MockLLMAPIMapper()
    api_calls = await mapper.map_subtask_to_apis(character_subtask)
    
    print("Mock LLM-Generated API Calls:")
    for call in api_calls:
        print(f"- {call['api_name']}: {call['description']}")
    
    return api_calls

if __name__ == "__main__":
    asyncio.run(test_mock_llm_mapper())
