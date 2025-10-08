"""
Coder Agent - Generates Python scripts from API mappings
Third agent in the multi-agent pipeline for 3D asset generation
"""

import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import traceback

from .base_agent import BaseAgent
from .models import (
    AgentType, AgentStatus,
    CoderInput, CoderOutput, GeneratedScript,
    APIMapping, TaskPlan
)

class CoderAgent(BaseAgent):
    """
    Coder Agent that generates executable Python scripts from API mappings.
    This version uses a robust, template-based approach to create well-structured scripts.
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.CODER,
            name="Coder Agent"
        )
        self._initialized = True
        self.logger.info("CoderAgent initialized with new robust templating system.")

    async def process(self, input_data: CoderInput) -> CoderOutput:
        """Process coding request and generate a well-structured Python script."""
        try:
            self.logger.info(f"Generating script for plan '{input_data.plan.plan_id}' with {len(input_data.api_mappings)} mappings.")
            start_time = time.time()

            complete_script = self._generate_complete_script(input_data.api_mappings, input_data.plan)

            generation_time = (time.time() - start_time) * 1000
            self.logger.info(f"Script generated in {generation_time:.2f}ms.")

            generated_script = GeneratedScript(
                script_id=f"script_{int(time.time())}",
                plan_id=input_data.plan.plan_id,
                python_code=complete_script,
                api_calls_count=sum(len(m.api_calls) for m in input_data.api_mappings),
                estimated_execution_time_seconds=30,
                dependencies=[],
                export_formats=["glb"],
            )

            return CoderOutput(
                agent_type=AgentType.CODER,
                status=AgentStatus.COMPLETED,
                success=True,
                message="Successfully generated script.",
                generated_script=generated_script,
            )

        except Exception as e:
            self.logger.error(f"Code generation failed: {e}", exc_info=True)
            return CoderOutput(
                agent_type=AgentType.CODER,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Code generation failed: {str(e)}",
                errors=[str(e), traceback.format_exc()],
            )
    def _generate_complete_script(self, api_mappings: List[APIMapping], plan: TaskPlan) -> str:
        """Generates the full Blender script from all components."""
        header = self._generate_header_section(plan)
        materials_section = self._generate_materials_section(plan)
        task_execution_section = self._generate_task_execution_section(api_mappings)
        main_plan_executor_section = self._generate_main_plan_executor_section(api_mappings)

        # Build the class via a list of lines to avoid nested f-string/brace issues
        cls: List[str] = []
        cls.append("class BlenderScriptExecutor:")
        cls.append("    def __init__(self):")
        cls.append("        self.created_objects = []")
        cls.append("        self.materials = {}")
        cls.append("        self.errors = []")
        cls.append("")
        cls.append("    def log_info(self, message: str):")
        cls.append("        print(f\"[BlenderScript] {message}\")")
        cls.append("")
        cls.append("    def log_error(self, message: str):")
        cls.append("        print(f\"[BlenderScript ERROR] {message}\")")
        cls.append("        self.errors.append(message)")
        cls.append("")
        cls.append("    def track_object(self, obj):")
        cls.append("        if obj and obj.name not in [o['name'] for o in self.created_objects]:")
        cls.append("            self.created_objects.append({'name': obj.name, 'type': obj.type})")
        cls.append("            self.log_info(f\"Tracked object: {obj.name} ({obj.type})\")")
        cls.append("")
        cls.append("    def safe_execute(self, api_func_str, **kwargs):")
        cls.append("        try:")
        cls.append("            # Remove custom parameters that aren't valid Blender API parameters")
        cls.append("            custom_params = ['_color_hint', '_note', '_balloon_shape', '_text_size', '_text_color', '_hollow_mug']")
        cls.append("            blender_kwargs = {k: v for k, v in kwargs.items() if k not in custom_params}")
        cls.append("            ")
        cls.append("            api_func = eval(api_func_str)")
        cls.append("            self.log_info(f\"Executing: {api_func_str} with {blender_kwargs}\")")
        cls.append("            if 'mesh' in getattr(api_func, '__module__', '') and bpy.context.mode != 'OBJECT':")
        cls.append("                bpy.ops.object.mode_set(mode='OBJECT')")
        cls.append("            result = api_func(**blender_kwargs)")
        cls.append("            try:")
        cls.append("                bpy.context.view_layer.update()")
        cls.append("            except Exception:")
        cls.append("                pass")
        cls.append("        except Exception as e:")
        cls.append("            self.log_error(f\"Execution failed for {api_func_str}: {str(e)}\")")
        cls.append("            return None")
        cls.append("")
        cls.append("    # --- Scene Setup ---")
        cls.append("    def setup_scene(self):")
        cls.append("        self.log_info(\"Setting up scene...\")")
        cls.append("        bpy.ops.object.select_all(action='SELECT')")
        cls.append("        bpy.ops.object.delete(use_global=False)")
        cls.append("        try:")
        cls.append("            bpy.context.view_layer.update()")
        cls.append("        except Exception:")
        cls.append("            pass")
        cls.append("        self.log_info(\"Scene cleared.\")")
        cls.append("        ")
        cls.append("        # Reset camera for better visibility")
        cls.append("        if 'Camera' in bpy.data.objects:")
        cls.append("            camera = bpy.data.objects['Camera']")
        cls.append("            camera.location = (10, -10, 8)")
        cls.append("            camera.rotation_euler = (1.1, 0, 0.785)")
        cls.append("        self.log_info(\"Camera positioned for optimal view.\")")
        cls.append("        ")
        cls.append("        # CRITICAL: Set viewport to Material Preview mode to show colors")
        cls.append("        try:")
        cls.append("            for area in bpy.context.screen.areas:")
        cls.append("                if area.type == 'VIEW_3D':")
        cls.append("                    for space in area.spaces:")
        cls.append("                        if space.type == 'VIEW_3D':")
        cls.append("                            space.shading.type = 'MATERIAL'  # Material Preview mode")
        cls.append("                            self.log_info(\"✅ Viewport set to Material Preview - colors will be visible!\")")
        cls.append("                            break")
        cls.append("        except Exception as e:")
        cls.append("            self.log_info(f\"⚠️ Could not auto-set viewport shading: {e}\")")
        cls.append("            self.log_info(\"📌 MANUALLY press 'Z' key and select 'Material Preview' to see colors!\")")
        cls.append(materials_section)  # INSERT MATERIALS SECTION!
        cls.append(task_execution_section)
        cls.append(main_plan_executor_section)
        cls.append("")
        cls.append("    # Compatibility alias expected by QAAgent")
        cls.append("    def safe_execute_api(self, api_func_str, **kwargs):")
        cls.append("        return self.safe_execute(api_func_str, **kwargs)")
        cls.append("")
        cls.append("    # --- Cleanup and Export ---")
        cls.append("    def finalize_and_export(self, export_path: str):")
        cls.append("        self.log_info(\"Finalizing and exporting asset...\")")
        cls.append("        ")
        cls.append("        # Select all created objects and frame them in view")
        cls.append("        bpy.ops.object.select_all(action='DESELECT')")
        cls.append("        for obj_info in self.created_objects:")
        cls.append("            obj = bpy.data.objects.get(obj_info['name'])")
        cls.append("            if obj:")
        cls.append("                obj.select_set(True)")
        cls.append("        ")
        cls.append("        # Frame selected objects in viewport for visibility")
        cls.append("        if len(bpy.context.selected_objects) > 0:")
        cls.append("            try:")
        cls.append("                # This helps zoom to fit objects in viewport")
        cls.append("                bpy.ops.view3d.view_selected()")
        cls.append("                self.log_info(\"Viewport framed to show all objects.\")")
        cls.append("            except Exception:")
        cls.append("                pass")
        cls.append("        ")
        cls.append("        # Set viewport shading to Material Preview to show colors")
        cls.append("        try:")
        cls.append("            for area in bpy.context.screen.areas:")
        cls.append("                if area.type == 'VIEW_3D':")
        cls.append("                    for space in area.spaces:")
        cls.append("                        if space.type == 'VIEW_3D':")
        cls.append("                            space.shading.type = 'MATERIAL'  # Material Preview mode")
        cls.append("                            self.log_info(\"Viewport set to Material Preview mode for color visibility.\")")
        cls.append("                            break")
        cls.append("        except Exception as e:")
        cls.append("            self.log_info(f\"Could not set viewport shading: {e}\")")
        cls.append("        if export_path and any(obj.select_get() for obj in bpy.data.objects):")
        cls.append("            try:")
        cls.append("                bpy.ops.export_scene.gltf(")
        cls.append("                    filepath=export_path,")
        cls.append("                    use_selection=True,")
        cls.append("                    export_format='GLB'")
        cls.append("                )")
        cls.append("                self.log_info(f\"Asset exported to {export_path}\")")
        cls.append("            except Exception as e:")
        cls.append("                self.log_error(f\"Export to GLB failed: {e}\")")
        cls.append("        else:")
        cls.append("            self.log_info(\"Export skipped: No objects were selected or no export path was provided.\")")

        class_definition = "\n".join(cls)

        main_block_lines = [
            "# --- Main Execution Block ---",
            "if __name__ == \"__main__\":",
            "    executor = BlenderScriptExecutor()",
            "    try:",
            "        # Get output path from command-line arguments",
            "        # Blender passes arguments after '--' to the script",
            "        output_path = \"generated_asset.glb\"  # Default fallback",
            "        ",
            "        # Check for command-line argument (passed via Blender --python script.py -- output.glb)",
            "        if '--' in sys.argv:",
            "            args_after_separator = sys.argv[sys.argv.index('--') + 1:]",
            "            if args_after_separator:",
            "                output_path = args_after_separator[0]",
            "                print(f\"[BlenderScript] Output path from CLI: {output_path}\")",
            "        else:",
            "            # Fallback: use current directory or blend file location",
            "            if 'bpy' in locals() and hasattr(bpy.data, 'filepath') and bpy.data.filepath:",
            "                output_path = os.path.join(os.path.dirname(bpy.data.filepath), output_path)",
            "        ",
            "        print(f\"[BlenderScript] Final output path: {output_path}\")",
            "        ",
            "        executor.execute_plan()",
            "        executor.finalize_and_export(output_path)",
            "        ",
            "        print(f\"[BlenderScript] ✅ Script execution completed successfully!\")",
            "    except Exception as e:",
            "        print(f\"[BlenderScript CRITICAL] A top-level error occurred: {e}\")",
            "        import traceback",
            "        traceback.print_exc()",
            "        sys.exit(1)  # Exit with error code",
        ]
        main_execution_block = "\n".join(main_block_lines)

        full_script = "\n\n".join([header, class_definition, main_execution_block])
        return full_script

    def _generate_header_section(self, plan: TaskPlan) -> str:
        timestamp = datetime.now().isoformat()
        return f'''"""
Generated Blender Python Script
Created by Coder Agent - Dynamic 3D Asset Generation Pipeline
Generated at: {timestamp}
Original prompt: {plan.original_prompt}
Plan ID: {plan.plan_id}
"""
import bpy
import bmesh
import mathutils
import os
import sys'''

    def _get_color_map(self) -> Dict[str, tuple]:
        return {
            'red': (1.0, 0.0, 0.0, 1.0), 'green': (0.0, 1.0, 0.0, 1.0),
            'blue': (0.0, 0.0, 1.0, 1.0), 'yellow': (1.0, 1.0, 0.0, 1.0),
            'orange': (1.0, 0.5, 0.0, 1.0), 'purple': (0.5, 0.0, 1.0, 1.0),
            'pink': (1.0, 0.0, 0.5, 1.0), 'brown': (0.6, 0.3, 0.1, 1.0),
            'black': (0.0, 0.0, 0.0, 1.0), 'white': (1.0, 1.0, 1.0, 1.0),
            'gray': (0.5, 0.5, 0.5, 1.0), 'grey': (0.5, 0.5, 0.5, 1.0)
        }

    def _generate_materials_section(self, plan: TaskPlan) -> str:
        colors = set()
        full_text = plan.original_prompt + " " + " ".join(st.description for st in plan.subtasks)
        color_map = self._get_color_map()
        for color_name in color_map:
            if color_name in full_text.lower():
                colors.add(color_name)

        if not colors:
            return """    def create_materials(self):
        self.log_info('No materials specified in the plan.')
        pass"""

        material_creation_code = ["    def create_materials(self):", "        self.log_info('Creating materials...')"]
        for color in colors:
            rgba = color_map[color]
            material_creation_code.extend([
                f"        mat = bpy.data.materials.new(name='{color.capitalize()}')",
                "        mat.use_nodes = True",
                "        bsdf = mat.node_tree.nodes.get('Principled BSDF')",
                "        if bsdf:",
                f"            bsdf.inputs['Base Color'].default_value = {rgba}",
                f"        self.materials['{color}'] = mat",
                f"        self.log_info(f'Created material: {color.capitalize()}')"
            ])
        return "\n".join(material_creation_code)

    def _generate_task_execution_section(self, api_mappings: List[APIMapping]) -> str:
        task_methods = []
        object_counter = {'cylinder': 0, 'sphere': 0, 'cube': 0, 'torus': 0, 'text': 0}
        
        for i, mapping in enumerate(api_mappings):
            method_name = f"execute_task_{i+1:03d}"
            method_body = [f"    def {method_name}(self):", f"        self.log_info(f'Executing task: {mapping.subtask_id}')"]
            
            for api_call in mapping.api_calls:
                api_func_str = api_call['api_name']
                raw_params = api_call['parameters']  # Keep raw dict for checking
                params_str = self._clean_parameters_for_code(raw_params)  # String for code gen
                
                # Detect object type from API name
                obj_type = None
                obj_name = None
                if 'cylinder' in api_func_str:
                    obj_type = 'cylinder'
                    object_counter['cylinder'] += 1
                    obj_name = f"Cylinder_{object_counter['cylinder']:03d}"
                    # Mark cylinder as needing hollow-out for mug
                    raw_params['_hollow_mug'] = True
                elif 'sphere' in api_func_str:
                    obj_type = 'sphere'
                    object_counter['sphere'] += 1
                    obj_name = f"Sphere_{object_counter['sphere']:03d}"
                elif 'cube' in api_func_str:
                    obj_type = 'cube'
                    object_counter['cube'] += 1
                    obj_name = f"Cube_{object_counter['cube']:03d}"
                elif 'torus' in api_func_str:
                    obj_type = 'torus'
                    object_counter['torus'] += 1
                    obj_name = f"Torus_{object_counter['torus']:03d}"
                elif 'text_add' in api_func_str:
                    obj_type = 'text'
                    object_counter['text'] += 1
                    obj_name = f"Text_{object_counter['text']:03d}"
                
                # Execute the API call
                method_body.append(f"        self.safe_execute('{api_func_str}', **{params_str})")
                
                # If it's an object creation, name it and track it
                if obj_name:
                    method_body.append("        obj = bpy.context.active_object")
                    method_body.append(f"        if obj:")
                    method_body.append(f"            obj.name = '{obj_name}'")
                    method_body.append("            self.track_object(obj)")
                    
                    # Handle text object - extract text from _note parameter
                    if obj_type == 'text' and '_note' in raw_params:
                        note_text = raw_params.get('_note', '')
                        if 'Set text body to:' in note_text:
                            text_content = note_text.split('Set text body to:')[1].strip()
                            method_body.append(f"            obj.data.body = '{text_content}'")
                            # Set text size if provided
                            text_size = raw_params.get('_text_size', 1.5)
                            method_body.append(f"            obj.data.size = {text_size}")
                            # Rotate text to lie flat on cylinder surface (90 degrees on X-axis)
                            method_body.append("            obj.rotation_euler[0] = 1.5708  # 90 degrees to lay flat")
                            method_body.append("            obj.rotation_euler[2] = 1.5708  # Also rotate 90 deg on Z for proper orientation")
                            # Add shrinkwrap modifier to follow curved surface
                            method_body.append("            # Add shrinkwrap to conform text to cylinder curvature")
                            method_body.append("            shrink = obj.modifiers.new(name='Shrinkwrap', type='SHRINKWRAP')")
                            method_body.append("            # Find cylinder object to wrap to")
                            method_body.append("            for cyl_obj in bpy.data.objects:")
                            method_body.append("                if 'Cylinder' in cyl_obj.name:")
                            method_body.append("                    shrink.target = cyl_obj")
                            method_body.append("                    shrink.wrap_method = 'NEAREST_SURFACEPOINT'")
                            method_body.append("                    shrink.offset = 0.05  # Small offset from surface")
                            method_body.append("                    # Apply the modifier to see the effect")
                            method_body.append("                    bpy.context.view_layer.update()")
                            method_body.append("                    break")
                            # Apply text color if provided
                            text_color = raw_params.get('_text_color')
                            if text_color:
                                method_body.append(f"            # Apply {text_color} material to text")
                                method_body.append(f"            if '{text_color}' in self.materials:")
                                method_body.append(f"                if len(obj.data.materials) == 0:")
                                method_body.append(f"                    obj.data.materials.append(self.materials['{text_color}'])")
                                method_body.append(f"                else:")
                                method_body.append(f"                    obj.data.materials[0] = self.materials['{text_color}']")
                    
                    # Handle balloon shape (elongated sphere)
                    if raw_params.get('_balloon_shape'):
                        method_body.append("            # Scale for balloon shape (slightly elongated)")
                        method_body.append("            obj.scale = (1.0, 1.0, 1.2)")
                    
                    # Hollow out cylinder for mug (open top)
                    if raw_params.get('_hollow_mug') and obj_type == 'cylinder':
                        method_body.append("            # Hollow out cylinder to create open mug")
                        method_body.append("            # Use solidify modifier with negative thickness")
                        method_body.append("            mod = obj.modifiers.new(name='Solidify', type='SOLIDIFY')")
                        method_body.append("            mod.thickness = -0.1  # Negative = inward")
                        method_body.append("            mod.offset = 0  # Centered")
                        method_body.append("            # Delete top face to open the mug")
                        method_body.append("            bpy.ops.object.mode_set(mode='EDIT')")
                        method_body.append("            bpy.ops.mesh.select_all(action='DESELECT')")
                        method_body.append("            bpy.ops.object.mode_set(mode='OBJECT')")
                        method_body.append("            # Select top face and delete it")
                        method_body.append("            for face in obj.data.polygons:")
                        method_body.append("                if face.normal.z > 0.9:  # Top face pointing up")
                        method_body.append("                    face.select = True")
                        method_body.append("            bpy.ops.object.mode_set(mode='EDIT')")
                        method_body.append("            bpy.ops.mesh.delete(type='FACE')")
                        method_body.append("            bpy.ops.object.mode_set(mode='OBJECT')")
                    
                    # Apply material if color hint exists
                    color_hint = raw_params.get('_color_hint', '').lower()
                    if color_hint and color_hint in ['red', 'green', 'blue', 'yellow', 'orange', 'purple', 'pink', 'brown', 'black', 'white', 'gray', 'grey']:
                        method_body.append(f"            # Apply {color_hint} material")
                        method_body.append(f"            if '{color_hint}' in self.materials:")
                        method_body.append(f"                if len(obj.data.materials) == 0:")
                        method_body.append(f"                    obj.data.materials.append(self.materials['{color_hint}'])")
                        method_body.append(f"                else:")
                        method_body.append(f"                    obj.data.materials[0] = self.materials['{color_hint}']")
                
                # Handle material_slot_add separately
                elif 'material_slot_add' in api_func_str:
                    # This is handled inline with object creation now, skip standalone calls
                    method_body.append("        # Material slot handled inline with object creation")

            task_methods.append("\n".join(method_body))
        return "\n\n".join(task_methods)

    def _generate_main_plan_executor_section(self, api_mappings: List[APIMapping]) -> str:
        executor_body = ["    def execute_plan(self):", "        self.log_info('Starting plan execution...')"]
        executor_body.append("        self.setup_scene()")
        executor_body.append("        self.create_materials()")
        for i in range(len(api_mappings)):
            executor_body.append(f"        self.execute_task_{i+1:03d}()")
        executor_body.append("        self.log_info('Plan execution completed.')")
        return "\n".join(executor_body)

    def _clean_parameters_for_code(self, parameters: Dict[str, Any]) -> str:
        return repr(parameters)