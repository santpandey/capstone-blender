"""
Coder Agent - Generates Python scripts from API mappings
Third agent in the multi-agent pipeline for 3D asset generation
"""

import asyncio
import time
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .base_agent import BaseAgent
from .simple_validator import SimpleAPIValidator
from .models import (
    AgentType, AgentStatus, AgentResponse,
    CoderInput, CoderOutput, GeneratedScript,
    APIMapping, TaskPlan, SubTask, TaskType
)

class CoderAgent(BaseAgent):
    """
    Coder Agent that generates executable Python scripts from API mappings
    
    Key responsibilities:
    1. Transform API mappings into valid Python code
    2. Handle dependencies and execution order
    3. Add error handling and validation
    4. Generate imports and setup code
    5. Create modular, maintainable scripts
    6. Add logging and debugging support
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODER,
            name="Coder Agent"
        )
        
        # Initialize API validator for crash prevention
        self.api_validator = SimpleAPIValidator()
        
        # Code generation templates
        self.script_templates = {
            "header": self._get_script_header_template(),
            "imports": self._get_imports_template(),
            "setup": self._get_setup_template(),
            "cleanup": self._get_cleanup_template(),
            "error_handling": self._get_error_handling_template()
        }
        
        # API category to import mapping
        # Note: bpy.ops.* are not importable modules, they are accessed via bpy.ops
        # Only import the base modules that are actually importable
        self.category_imports = {
            "mesh_operators": [],  # bpy.ops.mesh is accessed via bpy (already imported)
            "object_operators": [],  # bpy.ops.object is accessed via bpy (already imported)
            "geometry_nodes": [],  # bpy.ops.geometry is accessed via bpy (already imported)
            "shader_nodes": [],  # bpy.ops.shader is accessed via bpy (already imported)
            "material_operators": [],  # bpy.ops.material is accessed via bpy (already imported)
            "animation_operators": [],  # bpy.ops.anim is accessed via bpy (already imported)
            "scene_operators": []  # bpy.ops.scene is accessed via bpy (already imported)
        }
        
        # Code generation metrics
        self.generation_metrics = []
        self._initialized = True
    
    def _get_script_header_template(self) -> str:
        """Get the script header template"""
        return '''"""
Generated Blender Python Script
Created by Coder Agent - Dynamic 3D Asset Generation Pipeline
Generated at: {timestamp}
Original prompt: {original_prompt}
Plan ID: {plan_id}
"""

import bpy
import bmesh
import mathutils
from mathutils import Vector, Euler, Matrix
import sys
import os
from typing import Dict, List, Any, Optional

class BlenderScriptExecutor:
    """Main executor class for the generated script"""
    
    def __init__(self):
        self.created_objects = []
        self.execution_context = {{}}
        self.errors = []
        
    def log_info(self, message: str):
        """Log information message"""
        print(f"[BlenderScript] {{message}}")
        
    def log_error(self, message: str):
        """Log error message"""
        print(f"[BlenderScript ERROR] {{message}}")
        self.errors.append(message)
        
    def add_created_object(self, obj_name: str, obj_type: str):
        """Track created objects"""
        self.created_objects.append({{"name": obj_name, "type": obj_type}})
        print(f"[BlenderScript] Created {{obj_type}}: {{obj_name}}")
    
    def create_material_safely(self, material_name: str, color: tuple):
        """Create material safely with error handling"""
        try:
            material = bpy.data.materials.new(name=material_name)
            material.diffuse_color = color  # RGBA tuple
            print(f"[BlenderScript] Created material: {{material_name}}")
            return material
        except Exception as e:
            print(f"[BlenderScript ERROR] Material creation failed for {{material_name}}: {{str(e)}}")
            return None
    
    def apply_material_safely(self, obj_name: str, material):
        """Apply material to object safely"""
        try:
            if obj_name in bpy.data.objects and material:
                obj = bpy.data.objects[obj_name]
                # Simple material assignment
                if len(obj.data.materials) == 0:
                    obj.data.materials.append(material)
                else:
                    obj.data.materials[0] = material
                print(f"[BlenderScript] Applied material to {{obj_name}}")
                return True
        except Exception as e:
            print(f"[BlenderScript ERROR] Material application failed for {{obj_name}}: {{str(e)}}")
        return False
    
    def setup_text_alignment(self, text_obj, align_center=True):
        """Setup text alignment properties safely"""
        try:
            if align_center:
                # Center align the text (both horizontal and vertical)
                if hasattr(text_obj.data, 'align_x'):
                    text_obj.data.align_x = 'CENTER'
                if hasattr(text_obj.data, 'align_y'):
                    text_obj.data.align_y = 'CENTER'
                print("[BlenderScript] Applied center alignment to text object")
        except Exception as e:
            print(f"[BlenderScript ERROR] Text alignment setup failed: {{str(e)}}")
'''
    
    def _get_imports_template(self) -> str:
        """Get additional imports template"""
        return '''
# Additional imports based on API categories used
{additional_imports}

# Ensure we're in the correct context
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')
'''
    
    def _get_setup_template(self) -> str:
        """Get scene setup template"""
        return '''
    def setup_scene(self):
        """Initialize scene for asset generation"""
        self.log_info("Setting up scene...")
        
        # Clear existing mesh objects (optional - can be configured)
        bpy.ops.object.select_all(action='SELECT')
        bpy.ops.object.delete(use_global=False, confirm=False)
        
        # Reset cursor to origin
        bpy.context.scene.cursor.location = (0.0, 0.0, 0.0)
        
        # Set units and scale
        bpy.context.scene.unit_settings.system = 'METRIC'
        bpy.context.scene.unit_settings.scale_length = 1.0
        
        self.log_info("Scene setup completed")
'''
    
    def _get_cleanup_template(self) -> str:
        """Get cleanup template"""
        return '''
    def cleanup_and_export(self, export_path: str = None):
        """Clean up scene and export if requested"""
        self.log_info("Performing cleanup...")
        
        # Deselect all objects
        bpy.ops.object.select_all(action='DESELECT')
        
        # Update scene (SAFE: only updates object data, no UI manipulation)
        bpy.context.view_layer.update()
        
        # Log final asset summary with material verification
        self.log_info(f"Asset creation completed. Created {len(self.created_objects)} objects:")
        for obj in self.created_objects:
            self.log_info(f"  - {obj['name']} ({obj['type']})")
        
        # Verify materials are applied
        for obj_info in self.created_objects:
            obj_name = obj_info['name']
            if obj_name in bpy.data.objects:
                obj = bpy.data.objects[obj_name]
                if obj.data.materials:
                    mat_name = obj.data.materials[0].name if obj.data.materials[0] else "None"
                    self.log_info(f"  - {obj_name} has material: {mat_name}")
                else:
                    self.log_info(f"  - {obj_name} has NO material")
        
        # SAFETY NOTE: This script only creates 3D assets. 
        # To see materials/colors, manually switch Blender viewport to Material Preview mode.
        # Scripts should NEVER manipulate viewport, UI, or Blender native settings.
        
        # Export if path provided
        if export_path:
            self.export_scene(export_path)
            
        self.log_info(f"Script execution completed. Created {len(self.created_objects)} objects.")
        
    def export_scene(self, export_path: str):
        """Export scene to GLTF format"""
        try:
            # Select all created objects for export
            for obj_info in self.created_objects:
                obj = bpy.data.objects.get(obj_info["name"])
                if obj:
                    obj.select_set(True)
            
            # Export to GLTF
            bpy.ops.export_scene.gltf(
                filepath=export_path,
                use_selection=True,
                export_format='GLTF_SEPARATE'
            )
            self.log_info(f"Scene exported to: {export_path}")
            
        except Exception as e:
            self.log_error(f"Export failed: {str(e)}")
'''
    
    def _get_error_handling_template(self) -> str:
        """Get error handling template"""
        return '''
    def safe_execute_api(self, api_name: str, parameters: Dict[str, Any]) -> bool:
        """Safely execute a Blender API call with error handling"""
        try:
            self.log_info(f"Executing: {{api_name}} with params: {{parameters}}")
            
            # Get the API function
            api_parts = api_name.split('.')
            api_func = bpy
            for part in api_parts[1:]:  # Skip 'bpy'
                api_func = getattr(api_func, part)
            
            # Execute with parameters
            result = api_func(**parameters)
            
            # Log success
            self.log_info(f"Successfully executed: {{api_name}}")
            return True
            
        except AttributeError as e:
            self.log_error(f"API not found: {{api_name}} - {{str(e)}}")
            return False
        except TypeError as e:
            self.log_error(f"Invalid parameters for {{api_name}}: {{str(e)}}")
            return False
        except Exception as e:
            self.log_error(f"Execution failed for {{api_name}}: {{str(e)}}")
            return False
'''
    
    async def process(self, input_data: CoderInput) -> CoderOutput:
        """Process coding request and generate Python script"""
        
        try:
            self.logger.info(f"Generating script for {len(input_data.api_mappings)} API mappings")
            
            start_time = time.time()
            
            # Step 1: Analyze API mappings and plan code structure
            self.logger.info("Step 1: Analyzing code requirements...")
            code_analysis = self._analyze_code_requirements(input_data.api_mappings, input_data.plan)
            self.logger.info(f"Code analysis completed: {code_analysis}")
            
            # Step 2: Generate script components
            self.logger.info("Step 2: Generating script components...")
            script_components = await self._generate_script_components(
                input_data.api_mappings,
                input_data.plan,
                input_data.execution_context
            )
            self.logger.info(f"Script components generated: {list(script_components.keys())}")
            
            # Step 3: Assemble complete script
            self.logger.info("Step 3: Assembling complete script...")
            complete_script = self._assemble_complete_script(
                script_components,
                code_analysis,
                input_data
            )
            self.logger.info(f"Complete script assembled, length: {len(complete_script)} chars")
            
            # Step 4: Validate generated code
            validation_results = self._validate_generated_code(complete_script)
            
            # Step 5: Generate execution metadata
            execution_metadata = self._generate_execution_metadata(
                input_data.api_mappings,
                code_analysis
            )
            
            generation_time = (time.time() - start_time) * 1000
            
            # Create generated script object
            generated_script = GeneratedScript(
                script_id=f"script_{int(time.time())}",
                plan_id=input_data.plan.plan_id,
                python_code=complete_script,
                api_calls_count=sum(len(mapping.api_calls) for mapping in input_data.api_mappings),
                estimated_execution_time_seconds=execution_metadata["estimated_execution_time"],
                dependencies=execution_metadata["dependencies"],
                created_objects_estimate=execution_metadata["created_objects_estimate"],
                export_formats=["gltf"],
                validation_passed=validation_results["passed"],
                validation_warnings=validation_results["warnings"]
            )
            
            return CoderOutput(
                agent_type=AgentType.CODER,
                status=AgentStatus.COMPLETED,
                success=True,
                message=f"Successfully generated script with {generated_script.api_calls_count} API calls",
                data={
                    "generation_time_ms": generation_time,
                    "code_analysis": code_analysis,
                    "validation_results": validation_results,
                    "lines_of_code": len(complete_script.split('\n'))
                },
                generated_script=generated_script
            )
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            self.logger.error(f"Code generation failed: {e}")
            self.logger.error(f"Full traceback: {error_details}")
            
            # Log additional debugging info
            self.logger.error(f"Number of API mappings: {len(input_data.api_mappings)}")
            for i, mapping in enumerate(input_data.api_mappings):
                self.logger.error(f"Mapping {i}: subtask_id={mapping.subtask_id}, api_calls={len(mapping.api_calls)}")
                for j, api_call in enumerate(mapping.api_calls):
                    self.logger.error(f"  API Call {j}: {api_call}")
            
            return CoderOutput(
                agent_type=AgentType.CODER,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Code generation failed: {str(e)}",
                errors=[str(e), error_details]
            )
    
    def _analyze_code_requirements(self, api_mappings: List[APIMapping], plan: TaskPlan) -> Dict[str, Any]:
        """Analyze code requirements from API mappings"""
        
        analysis = {
            "total_api_calls": sum(len(mapping.api_calls) for mapping in api_mappings),
            "categories_used": set(),
            "imports_needed": set(),
            "execution_groups": [],
            "dependency_chain": [],
            "complexity_score": 0.0,
            "estimated_objects": 0
        }
        
        # Analyze each mapping
        for mapping in api_mappings:
            for api_call in mapping.api_calls:
                # Handle missing category field with fallback
                category = api_call.get("category", "mesh_operators")
                analysis["categories_used"].add(category)
                
                # Add required imports
                if category in self.category_imports:
                    analysis["imports_needed"].update(self.category_imports[category])
                
                # Estimate complexity
                if "complex" in api_call["api_name"].lower():
                    analysis["complexity_score"] += 2.0
                elif "advanced" in api_call["api_name"].lower():
                    analysis["complexity_score"] += 1.5
                else:
                    analysis["complexity_score"] += 1.0
        
        # Group by execution order (respecting dependencies)
        analysis["execution_groups"] = self._plan_execution_groups(api_mappings, plan)
        
        # Estimate created objects
        for mapping in api_mappings:
            subtask = next((st for st in plan.subtasks if st.task_id == mapping.subtask_id), None)
            if subtask:
                if subtask.type in [TaskType.CREATE_CHARACTER, TaskType.CREATE_OBJECT, TaskType.CREATE_FURNITURE]:
                    analysis["estimated_objects"] += 1
                elif subtask.type == TaskType.CREATE_ENVIRONMENT:
                    analysis["estimated_objects"] += 3
        
        return analysis
    
    def _plan_execution_groups(self, api_mappings: List[APIMapping], plan: TaskPlan) -> List[List[str]]:
        """Plan execution groups based on dependencies"""
        
        # Create dependency graph
        subtask_deps = {}
        for subtask in plan.subtasks:
            subtask_deps[subtask.task_id] = subtask.dependencies
        
        # Group subtasks by execution level
        execution_groups = []
        remaining_tasks = set(mapping.subtask_id for mapping in api_mappings)
        
        while remaining_tasks:
            # Find tasks with no remaining dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                deps = subtask_deps.get(task_id, [])
                if not any(dep in remaining_tasks for dep in deps):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # Circular dependency or error - add remaining tasks
                ready_tasks = list(remaining_tasks)
            
            execution_groups.append(ready_tasks)
            remaining_tasks -= set(ready_tasks)
        
        return execution_groups
    
    async def _generate_script_components(
        self, 
        api_mappings: List[APIMapping], 
        plan: TaskPlan,
        execution_context: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate individual script components"""
        
        components = {}
        
        try:
            # Generate header
            self.logger.info("Generating header component...")
            
            # DEBUG: Log the actual plan object fields
            self.logger.info(f"🔍 DEBUG: Received plan object:")
            self.logger.info(f"  - plan.summary = '{plan.summary}'")
            self.logger.info(f"  - plan.plan_id = '{plan.plan_id}'")
            self.logger.info(f"  - plan.original_prompt = '{plan.original_prompt}'")
            self.logger.info(f"  - type(plan.summary) = {type(plan.summary)}")
            
            # Add null checks and fallbacks for template variables
            timestamp = datetime.now().isoformat()
            original_prompt = plan.summary if plan.summary else "No prompt provided"
            plan_id = plan.plan_id if plan.plan_id else "unknown_plan"
            
            self.logger.info(f"Header template variables: timestamp={timestamp}, original_prompt='{original_prompt}', plan_id='{plan_id}'")
            
            components["header"] = self.script_templates["header"].format(
                timestamp=timestamp,
                original_prompt=original_prompt,
                plan_id=plan_id
            )
            self.logger.info("Header component generated successfully")
        except Exception as e:
            self.logger.error(f"Header generation failed: {e}")
            raise
        
        try:
            # Generate imports
            self.logger.info("Generating imports component...")
            all_imports = set()
            for mapping in api_mappings:
                for api_call in mapping.api_calls:
                    # Handle missing category field with fallback
                    category = api_call.get("category", "mesh_operators")  # Default fallback
                    if category in self.category_imports:
                        all_imports.update(self.category_imports[category])
                    else:
                        # If category not found, add default mesh operations import
                        all_imports.update(self.category_imports.get("mesh_operators", ["bpy.ops.mesh"]))
            
            additional_imports = "\n".join(f"import {imp}" for imp in sorted(all_imports))
            components["imports"] = self.script_templates["imports"].format(
                additional_imports=additional_imports
            )
            self.logger.info("Imports component generated successfully")
        except Exception as e:
            self.logger.error(f"Imports generation failed: {e}")
            raise
        
        try:
            # Generate setup
            self.logger.info("Generating setup component...")
            components["setup"] = self.script_templates["setup"]
            self.logger.info("Setup component generated successfully")
        except Exception as e:
            self.logger.error(f"Setup generation failed: {e}")
            raise
        
        try:
            # Generate main execution methods
            self.logger.info("Generating execution methods component...")
            components["execution_methods"] = await self._generate_execution_methods(api_mappings, plan)
            self.logger.info("Execution methods component generated successfully")
        except Exception as e:
            self.logger.error(f"Execution methods generation failed: {e}")
            raise
        
        try:
            # Generate cleanup
            self.logger.info("Generating cleanup component...")
            components["cleanup"] = self.script_templates["cleanup"]
            self.logger.info("Cleanup component generated successfully")
        except Exception as e:
            self.logger.error(f"Cleanup generation failed: {e}")
            raise
        
        try:
            # Generate error handling
            self.logger.info("Generating error handling component...")
            components["error_handling"] = self.script_templates["error_handling"]
            self.logger.info("Error handling component generated successfully")
        except Exception as e:
            self.logger.error(f"Error handling generation failed: {e}")
            raise
        
        try:
            # Generate main execution function
            self.logger.info("Generating main execution component...")
            components["main_execution"] = self._generate_main_execution(api_mappings, plan)
            self.logger.info("Main execution component generated successfully")
        except Exception as e:
            self.logger.error(f"Main execution generation failed: {e}")
            raise
        
        return components
    
    async def _generate_execution_methods(self, api_mappings: List[APIMapping], plan: TaskPlan) -> str:
        """Generate execution methods for each subtask"""
        
        methods = []
        
        for mapping in api_mappings:
            # Find corresponding subtask
            subtask = next((st for st in plan.subtasks if st.task_id == mapping.subtask_id), None)
            if not subtask:
                continue
            
            method_name = f"execute_{mapping.subtask_id.replace('-', '_')}"
            method_code = f'''
    def {method_name}(self):
        """Execute subtask: {subtask.title}"""
        self.log_info("Starting subtask: {subtask.title}")
        
        try:'''
            
            # Check if this is a material application subtask
            is_material_subtask = (subtask.type == TaskType.MATERIAL_APPLICATION or 
                                 "material" in subtask.title.lower() or 
                                 "color" in subtask.title.lower())
            
            if is_material_subtask:
                # Generate proper material creation workflow instead of raw API calls
                color_info = self._extract_color_from_text(subtask.title + " " + subtask.description)
                object_type = self._extract_object_type_from_text(subtask.title + " " + subtask.description)
                method_code += f'''
            
            # Create object and apply material with color for {subtask.title}
            # First ensure we have an object to apply material to
            if not bpy.context.active_object:
                # Create a basic object if none exists
                bpy.ops.mesh.{object_type}()
                self.log_info(f"Created {{'{object_type}'}} object for material application")
            
            if bpy.context.active_object:
                material_name = "Material_{subtask.task_id.replace('-', '_')}"
                material = self.create_material_safely(material_name, {color_info})
                if material:
                    success = self.apply_material_safely(bpy.context.active_object.name, material)
                    if success:
                        self.log_info(f"Applied {{material_name}} with color {color_info} to {{bpy.context.active_object.name}}")
                        # Track the created object
                        self.add_created_object(bpy.context.active_object.name, "material_object")
                    else:
                        self.log_error(f"Failed to apply material {{material_name}}")
                        return False
                else:
                    self.log_error(f"Failed to create material {{material_name}}")
                    return False
            else:
                self.log_error("No active object available for material application")
                return False'''
            else:
                # Add regular API calls for non-material subtasks
                # But ensure we always create visible objects
                has_object_creation = any("primitive" in api_call.get("api_name", "") for api_call in mapping.api_calls)
                
                if not has_object_creation:
                    # If no object creation APIs, add a default visible object
                    object_type = self._extract_object_type_from_text(subtask.title + " " + subtask.description)
                    method_code += f'''
            
            # Create visible object for {subtask.title}
            success = self.safe_execute_api(
                "bpy.ops.mesh.{object_type}",
                {{"radius": 2.0, "location": [0, 0, 0]}}
            )
            
            if not success:
                self.log_error(f"Failed to create object")
                return False
            
            # Track the created object
            if bpy.context.active_object:
                self.add_created_object(bpy.context.active_object.name, "generated_object")'''
                
                for i, api_call in enumerate(mapping.api_calls):
                    api_name = api_call["api_name"]
                    parameters = api_call["parameters"]
                    
                    # Ensure size parameters are reasonable for visibility
                    if "radius" in parameters and isinstance(parameters["radius"], (int, float)):
                        if parameters["radius"] < 1.0:
                            parameters["radius"] = 2.0  # Make objects visible
                    
                    # Clean parameters for code generation
                    clean_params = self._clean_parameters_for_code(parameters)
                    
                    method_code += f'''
            
            # API Call {i+1}: {api_name}
            # Description: {api_call.get("description", "No description")}
            success = self.safe_execute_api(
                "{api_name}",
                {clean_params}
            )
            
            if not success:
                self.log_error(f"Failed to execute {api_name}")
                return False'''
            

            
            # Add object tracking if this creates objects
            if subtask.type in [TaskType.CREATE_CHARACTER, TaskType.CREATE_OBJECT, TaskType.CREATE_FURNITURE]:
                method_code += f'''
            
            # Track created object
            if bpy.context.active_object:
                self.add_created_object(
                    bpy.context.active_object.name,
                    "{subtask.type.value}"
                )'''
            
            method_code += f'''
            
            self.log_info("Completed subtask: {subtask.title}")
            return True
            
        except Exception as e:
            self.log_error(f"Subtask {subtask.title} failed: {{str(e)}}")
            return False
'''
            
            methods.append(method_code)
        
        return "\n".join(methods)
    
    def _extract_color_from_text(self, text: str) -> tuple:
        """Extract color information from text description"""
        text_lower = text.lower()
        
        # Common color mappings to RGB values
        color_map = {
            'red': (1.0, 0.0, 0.0, 1.0),
            'green': (0.0, 1.0, 0.0, 1.0),
            'blue': (0.0, 0.0, 1.0, 1.0),
            'yellow': (1.0, 1.0, 0.0, 1.0),
            'orange': (1.0, 0.5, 0.0, 1.0),
            'purple': (0.5, 0.0, 1.0, 1.0),
            'pink': (1.0, 0.0, 0.5, 1.0),
            'brown': (0.6, 0.3, 0.1, 1.0),
            'black': (0.0, 0.0, 0.0, 1.0),
            'white': (1.0, 1.0, 1.0, 1.0),
            'gray': (0.5, 0.5, 0.5, 1.0),
            'grey': (0.5, 0.5, 0.5, 1.0)
        }
        
        # Search for color keywords in text
        for color_name, rgb_value in color_map.items():
            if color_name in text_lower:
                return rgb_value
        
        # Default to red if no color found (for cricket ball)
        return (1.0, 0.0, 0.0, 1.0)
    
    def _extract_object_type_from_text(self, text: str) -> str:
        """Extract object type from text description for mesh creation"""
        text_lower = text.lower()
        
        # Object type mappings to Blender mesh primitives
        object_map = {
            'ball': 'primitive_uv_sphere_add',
            'sphere': 'primitive_uv_sphere_add',
            'cube': 'primitive_cube_add',
            'box': 'primitive_cube_add',
            'cylinder': 'primitive_cylinder_add',
            'cone': 'primitive_cone_add',
            'mug': 'primitive_cylinder_add',
            'cup': 'primitive_cylinder_add',
            'chair': 'primitive_cube_add',
            'table': 'primitive_cube_add'
        }
        
        # Search for object keywords in text
        for object_name, mesh_type in object_map.items():
            if object_name in text_lower:
                return mesh_type
        
        # Default to sphere for round objects like cricket ball
        return 'primitive_uv_sphere_add'
    
    def _clean_parameters_for_code(self, parameters: Dict[str, Any]) -> str:
        """Clean parameters for code generation"""
        
        clean_params = {}
        
        for key, value in parameters.items():
            if isinstance(value, str):
                clean_params[key] = f'"{value}"'
            elif isinstance(value, (list, tuple)):
                clean_params[key] = str(tuple(value))
            elif isinstance(value, dict):
                clean_params[key] = str(value)
            else:
                clean_params[key] = value
        
        # Format as Python dict
        param_items = [f'"{k}": {v}' for k, v in clean_params.items()]
        return "{" + ", ".join(param_items) + "}"
    
    def _generate_main_execution(self, api_mappings: List[APIMapping], plan: TaskPlan) -> str:
        """Generate main execution function"""
        
        main_code = '''
    def execute_plan(self, export_path: str = None):
        """Execute the complete plan"""
        self.log_info("Starting plan execution...")
        
        # Setup scene
        self.setup_scene()
        
        # Execute subtasks in dependency order'''
        
        # Add execution calls for each subtask
        if api_mappings:
            for mapping in api_mappings:
                method_name = f"execute_{mapping.subtask_id.replace('-', '_')}"
                main_code += f'''
        
        # Execute: {mapping.subtask_id}
        if not self.{method_name}():
            self.log_error("Failed to execute {mapping.subtask_id}")
            return False'''
        else:
            # Handle case when no API mappings are available
            main_code += '''
        
        # No API mappings available - this should not happen with proper fallback
        self.log_error("No API mappings found. Coordinator Agent fallback mechanism failed.")
        self.log_error("This indicates a critical issue with the API search fallback.")
        return False'''
        
        main_code += '''
        
        # Cleanup and export
        self.cleanup_and_export(export_path)
        
        self.log_info("Plan execution completed successfully!")
        return True

# Main execution
if __name__ == "__main__":
    executor = BlenderScriptExecutor()
    
    # Get export path from command line arguments or use default
    export_path = sys.argv[-1] if len(sys.argv) > 1 and sys.argv[-1].endswith('.gltf') else None
    
    # Execute the plan
    success = executor.execute_plan(export_path)
    
    if success:
        print("✅ Script execution completed successfully!")
    else:
        print("❌ Script execution failed!")
        sys.exit(1)
'''
        
        return main_code
    
    def _assemble_complete_script(
        self, 
        components: Dict[str, str], 
        analysis: Dict[str, Any],
        input_data: CoderInput
    ) -> str:
        """Assemble all components into complete script"""
        
        # Simple assembly - just join all components in order
        # The main_execution component already contains both the execute_plan method AND the main execution block
        # No need for complex splitting that breaks indentation
        
        # Split main_execution to separate class method from script-level execution
        main_execution = components["main_execution"]
        if "# Main execution" in main_execution:
            execute_plan_method = main_execution.split("# Main execution")[0]
            main_script_block = "# Main execution" + main_execution.split("# Main execution")[1]
        else:
            execute_plan_method = main_execution
            main_script_block = ""
        
        # Assemble all CLASS components first (everything that should be inside BlenderScriptExecutor class)
        class_components = [
            components["header"],           # Class definition and initial methods
            components["setup"],            # Setup functions (setup_scene method)
            components["error_handling"],   # Error handling functions
            components["cleanup"],          # Cleanup functions  
            components["execution_methods"], # Individual subtask methods
            execute_plan_method            # execute_plan method only
        ]
        
        # Assemble SCRIPT-LEVEL components (everything outside the class)
        script_components = [
            components["imports"],          # Additional imports
            main_script_block              # Main execution block
        ]
        
        # Join class components
        class_content = "\n".join(class_components)
        
        # Join script components (filter out empty ones)
        script_content = "\n".join([comp for comp in script_components if comp.strip()])
        
        # Combine with proper structure
        script_parts = [class_content]
        if script_content:
            script_parts.append(script_content)
        
        return "\n".join(script_parts)
    
    def _validate_generated_code(self, script_code: str) -> Dict[str, Any]:
        """Validate the generated Python code"""
        
        validation = {
            "passed": True,
            "warnings": [],
            "errors": [],
            "metrics": {}
        }
        
        try:
            # Basic syntax check
            compile(script_code, '<generated_script>', 'exec')
            validation["metrics"]["syntax_valid"] = True
            
        except SyntaxError as e:
            validation["passed"] = False
            validation["errors"].append(f"Syntax error: {str(e)}")
            validation["metrics"]["syntax_valid"] = False
        
        # SAFETY CHECK: Detect dangerous Blender operations that can cause crashes
        # These patterns are VERY SPECIFIC to avoid blocking legitimate asset creation operations
        dangerous_patterns = [
            # UI/Viewport manipulation (CRITICAL - causes crashes)
            "bpy.ops.view3d.view_selected",  # Viewport navigation - CRASHES BLENDER
            "bpy.ops.view3d.view_all",       # Viewport navigation - CRASHES BLENDER
            "bpy.ops.view3d.view_center_cursor", # Viewport navigation - CRASHES BLENDER
            "bpy.ops.view3d.view_camera",    # Viewport navigation - CRASHES BLENDER
            "bpy.context.screen.areas",      # UI screen area access
            "space.shading.type =",          # Viewport shading assignment
            "area.type == 'VIEW_3D'",        # UI area detection
            "space.type == 'VIEW_3D'",       # UI space detection  
            "bpy.context.window",            # Window management
            "bpy.context.area.spaces",       # UI area space access
            ".shading.type = 'MATERIAL_PREVIEW'",  # Specific viewport shading change
            ".shading.type = 'RENDERED'",    # Specific viewport shading change
            "for area in bpy.context.screen", # Screen area iteration
            # Additional dangerous viewport operations
            "bpy.ops.screen.",               # Screen operations
            "bpy.ops.wm.window",             # Window manager operations
            "bpy.context.area.type",         # Area type manipulation
            "bpy.context.space_data"         # Space data manipulation
        ]
        
        for pattern in dangerous_patterns:
            if pattern in script_code:
                validation["passed"] = False
                validation["errors"].append(f"FORBIDDEN OPERATION: Script contains dangerous Blender UI manipulation: '{pattern}'. Scripts must ONLY create 3D assets, not manipulate viewport/UI settings.")
        
        # Check for required components
        required_components = [
            "import bpy",
            "class BlenderScriptExecutor",
            "def execute_plan",
            "if __name__ == \"__main__\""
        ]
        
        for component in required_components:
            if component not in script_code:
                validation["warnings"].append(f"Missing component: {component}")
        
        # Calculate metrics
        lines = script_code.split('\n')
        validation["metrics"]["total_lines"] = len(lines)
        validation["metrics"]["code_lines"] = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        validation["metrics"]["comment_lines"] = len([l for l in lines if l.strip().startswith('#')])
        
        return validation
    
    def _generate_execution_metadata(self, api_mappings: List[APIMapping], analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate execution metadata"""
        
        # Estimate execution time (rough approximation)
        base_time_per_api = 0.5  # seconds
        complexity_multiplier = min(analysis["complexity_score"] / 10, 2.0)
        estimated_time = analysis["total_api_calls"] * base_time_per_api * complexity_multiplier
        
        # Collect dependencies
        dependencies = ["bpy", "bmesh", "mathutils"]
        dependencies.extend(analysis["imports_needed"])
        
        return {
            "estimated_execution_time": estimated_time,
            "dependencies": list(set(dependencies)),
            "created_objects_estimate": analysis["estimated_objects"]
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the coder agent"""
        
        return {
            "initialized": self._initialized,
            "templates_loaded": len(self.script_templates),
            "category_mappings": len(self.category_imports),
            "generation_count": len(self.generation_metrics)
        }
