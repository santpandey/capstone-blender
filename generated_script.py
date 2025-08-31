"""
Generated Blender Python Script
Created by Coder Agent - Dynamic 3D Asset Generation Pipeline
Generated at: 2025-08-31T12:47:44.486889
Original prompt: 3D asset generation with 3 subtasks: create_object, material_application
Plan ID: 54382d93-2eae-4379-95a5-dc22f5de3b7f
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
        self.execution_context = {}
        self.errors = []
        
    def log_info(self, message: str):
        """Log information message"""
        print(f"[BlenderScript] {message}")
        
    def log_error(self, message: str):
        """Log error message"""
        print(f"[BlenderScript ERROR] {message}")
        self.errors.append(message)
        
    def add_created_object(self, obj_name: str, obj_type: str):
        """Track created objects"""
        self.created_objects.append({"name": obj_name, "type": obj_type})
        print(f"[BlenderScript] Created {obj_type}: {obj_name}")
    
    def create_material_safely(self, material_name: str, color: tuple):
        """Create material safely with error handling"""
        try:
            material = bpy.data.materials.new(name=material_name)
            material.diffuse_color = color  # RGBA tuple
            print(f"[BlenderScript] Created material: {material_name}")
            return material
        except Exception as e:
            print(f"[BlenderScript ERROR] Material creation failed for {material_name}: {str(e)}")
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
                print(f"[BlenderScript] Applied material to {obj_name}")
                return True
        except Exception as e:
            print(f"[BlenderScript ERROR] Material application failed for {obj_name}: {str(e)}")
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
            print(f"[BlenderScript ERROR] Text alignment setup failed: {str(e)}")


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


    def execute_task_001(self):
        """Execute subtask: Create Coffee Mug"""
        self.log_info("Starting subtask: Create Coffee Mug")
        
        try:
            
            # API Call 1: bpy.ops.mesh.primitive_cylinder_add
            # Description: Create a cylinder for the coffee mug body
            success = self.safe_execute_api(
                "bpy.ops.mesh.primitive_cylinder_add",
                {"radius": 2.0, "depth": 2.0, "location": (0, 0, 0), "rotation": (0, 0, 0)}
            )
            
            if not success:
                self.log_error(f"Failed to execute bpy.ops.mesh.primitive_cylinder_add")
                return False
            
            # API Call 2: bpy.ops.mesh.primitive_uv_sphere_add
            # Description: Create basic sphere primitive
            success = self.safe_execute_api(
                "bpy.ops.mesh.primitive_uv_sphere_add",
                {"radius": 1.0, "location": (0, 0, 0)}
            )
            
            if not success:
                self.log_error(f"Failed to execute bpy.ops.mesh.primitive_uv_sphere_add")
                return False
            
            # Track created object
            if bpy.context.active_object:
                self.add_created_object(
                    bpy.context.active_object.name,
                    "create_object"
                )
            
            self.log_info("Completed subtask: Create Coffee Mug")
            return True
            
        except Exception as e:
            self.log_error(f"Subtask Create Coffee Mug failed: {str(e)}")
            return False


    def execute_task_002(self):
        """Execute subtask: Apply Materials and Colors"""
        self.log_info("Starting subtask: Apply Materials and Colors")
        
        try:
            
            # Create object and apply material with color for Apply Materials and Colors
            # First ensure we have an object to apply material to
            if not bpy.context.active_object:
                # Create a basic object if none exists
                bpy.ops.mesh.primitive_uv_sphere_add()
                self.log_info(f"Created {'primitive_uv_sphere_add'} object for material application")
            
            if bpy.context.active_object:
                material_name = "Material_task_002"
                material = self.create_material_safely(material_name, (0.6, 0.3, 0.1, 1.0))
                if material:
                    success = self.apply_material_safely(bpy.context.active_object.name, material)
                    if success:
                        self.log_info(f"Applied {material_name} with color (0.6, 0.3, 0.1, 1.0) to {bpy.context.active_object.name}")
                        # Track the created object
                        self.add_created_object(bpy.context.active_object.name, "material_object")
                    else:
                        self.log_error(f"Failed to apply material {material_name}")
                        return False
                else:
                    self.log_error(f"Failed to create material {material_name}")
                    return False
            else:
                self.log_error("No active object available for material application")
                return False
            
            self.log_info("Completed subtask: Apply Materials and Colors")
            return True
            
        except Exception as e:
            self.log_error(f"Subtask Apply Materials and Colors failed: {str(e)}")
            return False


    def execute_task_003(self):
        """Execute subtask: Add Text Elements"""
        self.log_info("Starting subtask: Add Text Elements")
        
        try:
            
            # Create object and apply material with color for Add Text Elements
            # First ensure we have an object to apply material to
            if not bpy.context.active_object:
                # Create a basic object if none exists
                bpy.ops.mesh.primitive_uv_sphere_add()
                self.log_info(f"Created {'primitive_uv_sphere_add'} object for material application")
            
            if bpy.context.active_object:
                material_name = "Material_task_003"
                material = self.create_material_safely(material_name, (1.0, 0.0, 0.0, 1.0))
                if material:
                    success = self.apply_material_safely(bpy.context.active_object.name, material)
                    if success:
                        self.log_info(f"Applied {material_name} with color (1.0, 0.0, 0.0, 1.0) to {bpy.context.active_object.name}")
                        # Track the created object
                        self.add_created_object(bpy.context.active_object.name, "material_object")
                    else:
                        self.log_error(f"Failed to apply material {material_name}")
                        return False
                else:
                    self.log_error(f"Failed to create material {material_name}")
                    return False
            else:
                self.log_error("No active object available for material application")
                return False
            
            self.log_info("Completed subtask: Add Text Elements")
            return True
            
        except Exception as e:
            self.log_error(f"Subtask Add Text Elements failed: {str(e)}")
            return False


    def execute_plan(self, export_path: str = None):
        """Execute the complete plan"""
        self.log_info("Starting plan execution...")
        
        # Setup scene
        self.setup_scene()
        
        # Execute subtasks in dependency order
        
        # Execute: task_001
        if not self.execute_task_001():
            self.log_error("Failed to execute task_001")
            return False
        
        # Execute: task_002
        if not self.execute_task_002():
            self.log_error("Failed to execute task_002")
            return False
        
        # Execute: task_003
        if not self.execute_task_003():
            self.log_error("Failed to execute task_003")
            return False
        
        # Cleanup and export
        self.cleanup_and_export(export_path)
        
        self.log_info("Plan execution completed successfully!")
        return True



# Additional imports based on API categories used


# Ensure we're in the correct context
if bpy.context.mode != 'OBJECT':
    bpy.ops.object.mode_set(mode='OBJECT')

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
