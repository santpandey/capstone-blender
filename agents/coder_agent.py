"""
Coder Agent - Generates Python scripts from API mappings
Third agent in the multi-agent pipeline for 3D asset generation
"""

import asyncio
import time
import logging
import json
from typing import Dict, List, Optional, Any, Set
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent
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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.CODER,
            name="coder_agent",
            config=config or {}
        )
        
        # Code generation templates
        self.script_templates = {
            "header": self._get_script_header_template(),
            "imports": self._get_imports_template(),
            "setup": self._get_setup_template(),
            "cleanup": self._get_cleanup_template(),
            "error_handling": self._get_error_handling_template()
        }
        
        # API category to import mapping
        self.category_imports = {
            "mesh_operators": ["bpy.ops.mesh"],
            "object_operators": ["bpy.ops.object"],
            "geometry_nodes": ["bpy.ops.geometry", "bpy.data.node_groups"],
            "shader_nodes": ["bpy.ops.shader", "bpy.data.materials"],
            "material_operators": ["bpy.ops.material", "bpy.data.materials"],
            "animation_operators": ["bpy.ops.anim", "bpy.data.actions"],
            "scene_operators": ["bpy.ops.scene", "bpy.context.scene"]
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
import logging
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BlenderScriptExecutor:
    """Main executor class for the generated script"""
    
    def __init__(self):
        self.created_objects = []
        self.execution_context = {{}}
        self.errors = []
        
    def log_info(self, message: str):
        """Log information message"""
        logger.info(f"[BlenderScript] {{message}}")
        
    def log_error(self, message: str):
        """Log error message"""
        logger.error(f"[BlenderScript] {{message}}")
        self.errors.append(message)
        
    def add_created_object(self, obj_name: str, obj_type: str):
        """Track created objects"""
        self.created_objects.append({{"name": obj_name, "type": obj_type}})
        self.log_info(f"Created {{obj_type}}: {{obj_name}}")
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
        
        # Update scene
        bpy.context.view_layer.update()
        
        # Export if path provided
        if export_path:
            self.export_scene(export_path)
            
        self.log_info(f"Script execution completed. Created {{len(self.created_objects)}} objects.")
        
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
            self.log_info(f"Scene exported to: {{export_path}}")
            
        except Exception as e:
            self.log_error(f"Export failed: {{str(e)}}")
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
            code_analysis = self._analyze_code_requirements(input_data.api_mappings, input_data.plan)
            
            # Step 2: Generate script components
            script_components = await self._generate_script_components(
                input_data.api_mappings,
                input_data.plan,
                input_data.execution_context
            )
            
            # Step 3: Assemble complete script
            complete_script = self._assemble_complete_script(
                script_components,
                code_analysis,
                input_data
            )
            
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
            self.logger.error(f"Code generation failed: {e}")
            return CoderOutput(
                agent_type=AgentType.CODER,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Code generation failed: {str(e)}",
                errors=[str(e)]
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
                category = api_call["category"]
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
        
        # Generate header
        components["header"] = self.script_templates["header"].format(
            timestamp=datetime.now().isoformat(),
            original_prompt=plan.summary,
            plan_id=plan.plan_id
        )
        
        # Generate imports
        all_imports = set()
        for mapping in api_mappings:
            for api_call in mapping.api_calls:
                category = api_call["category"]
                if category in self.category_imports:
                    all_imports.update(self.category_imports[category])
        
        additional_imports = "\n".join(f"import {imp}" for imp in sorted(all_imports))
        components["imports"] = self.script_templates["imports"].format(
            additional_imports=additional_imports
        )
        
        # Generate setup
        components["setup"] = self.script_templates["setup"]
        
        # Generate main execution methods
        components["execution_methods"] = await self._generate_execution_methods(api_mappings, plan)
        
        # Generate cleanup
        components["cleanup"] = self.script_templates["cleanup"]
        
        # Generate error handling
        components["error_handling"] = self.script_templates["error_handling"]
        
        # Generate main execution function
        components["main_execution"] = self._generate_main_execution(api_mappings, plan)
        
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
            
            # Add API calls for this subtask
            for i, api_call in enumerate(mapping.api_calls):
                api_name = api_call["api_name"]
                parameters = api_call["parameters"]
                
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
                self.log_error("Failed to execute {api_name}")
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
        for mapping in api_mappings:
            method_name = f"execute_{mapping.subtask_id.replace('-', '_')}"
            main_code += f'''
        
        # Execute: {mapping.subtask_id}
        if not self.{method_name}():
            self.log_error("Failed to execute {mapping.subtask_id}")
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
        
        script_parts = [
            components["header"],
            components["imports"],
            components["setup"],
            components["error_handling"],
            components["execution_methods"],
            components["cleanup"],
            components["main_execution"]
        ]
        
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
