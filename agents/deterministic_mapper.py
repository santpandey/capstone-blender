"""
Deterministic API Mapper - Rule-based mapping for common Blender operations.
Provides reliable, predictable API calls for frequent task patterns.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from .models import SubTask, TaskType

class DeterministicMapper:
    """
    Maps common subtask patterns to known-good Blender API sequences.
    Handles primitives, transformations, materials, and text creation reliably.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Primitive shape keywords and their APIs
        self.primitive_mapping = {
            'cube': 'bpy.ops.mesh.primitive_cube_add',
            'box': 'bpy.ops.mesh.primitive_cube_add',
            'sphere': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'ball': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'balloon': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'globe': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'orb': 'bpy.ops.mesh.primitive_uv_sphere_add',
            'cylinder': 'bpy.ops.mesh.primitive_cylinder_add',
            'tube': 'bpy.ops.mesh.primitive_cylinder_add',
            'cone': 'bpy.ops.mesh.primitive_cone_add',
            'torus': 'bpy.ops.mesh.primitive_torus_add',
            'ring': 'bpy.ops.mesh.primitive_torus_add',
            'donut': 'bpy.ops.mesh.primitive_torus_add',
            'plane': 'bpy.ops.mesh.primitive_plane_add',
            'circle': 'bpy.ops.mesh.primitive_circle_add',
            'disc': 'bpy.ops.mesh.primitive_circle_add',
            'ico_sphere': 'bpy.ops.mesh.primitive_ico_sphere_add',
            'monkey': 'bpy.ops.mesh.primitive_monkey_add',
        }
        
        # Shape keyword aliases for better matching
        self.shape_keywords = {
            'balloon': 'sphere',
            'ball': 'sphere',
            'globe': 'sphere',
            'orb': 'sphere',
            'egg': 'sphere',
            'box': 'cube',
            'block': 'cube',
            'tube': 'cylinder',
            'pipe': 'cylinder',
            'ring': 'torus',
            'donut': 'torus',
            'disc': 'circle',
            'disk': 'circle',
        }
        
        # Material/color operations
        self.material_patterns = {
            'create_material': 'bpy.data.materials.new',
            'apply_material': 'bpy.ops.object.material_slot_add',
        }
        
        # Transformation operations
        self.transform_patterns = {
            'scale': 'bpy.ops.transform.resize',
            'move': 'bpy.ops.transform.translate',
            'rotate': 'bpy.ops.transform.rotate',
        }
        
    def can_handle(self, subtask: SubTask) -> bool:
        """Check if this subtask can be handled deterministically."""
        text = f"{subtask.title} {subtask.description}".lower()
        
        # Check for handle creation (special complex primitive)
        if 'handle' in text and any(word in text for word in ['mug', 'cup', 'jug', 'pitcher', 'basket']):
            return True
        
        # Check for primitive creation
        if any(prim in text for prim in self.primitive_mapping.keys()):
            return True
        
        # Check for text creation
        if 'text' in text and ('add' in text or 'create' in text):
            return True
        
        # Check for material/color application
        if any(word in text for word in ['material', 'color', 'colour', 'shader']):
            return True
        
        # Check for transformations
        if any(word in text for word in ['scale', 'resize', 'move', 'position', 'rotate']):
            return True
        
        return False
    
    def map(self, subtask: SubTask, context: Dict[str, Any] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Map subtask to API calls deterministically.
        Returns None if it cannot handle the subtask.
        """
        text = f"{subtask.title} {subtask.description}".lower()
        
        # Add original prompt context for better color/attribute extraction
        if context and 'original_prompt' in context:
            text = f"{text} {context['original_prompt']}".lower()
        
        api_calls = []
        
        # 1. Handle primitive creation
        primitive_calls = self._handle_primitives(text, subtask)
        if primitive_calls:
            api_calls.extend(primitive_calls)
        
        # 2. Handle text creation
        if 'text' in text and ('add' in text or 'create' in text or 'label' in text):
            text_calls = self._handle_text_creation(text, subtask)
            if text_calls:
                api_calls.extend(text_calls)
        
        # 3. Handle material/color
        if any(word in text for word in ['material', 'color', 'colour', 'paint', 'shader']):
            material_calls = self._handle_materials(text, subtask)
            if material_calls:
                api_calls.extend(material_calls)
        
        # 4. Handle transformations
        transform_calls = self._handle_transformations(text, subtask)
        if transform_calls:
            api_calls.extend(transform_calls)
        
        if api_calls:
            self.logger.info(f"Deterministically mapped subtask '{subtask.title}' to {len(api_calls)} API calls")
            return api_calls
        
        return None
    
    def _handle_primitives(self, text: str, subtask: SubTask) -> List[Dict[str, Any]]:
        """Handle primitive shape creation."""
        api_calls = []
        
        # Extract color for material application
        color = self._extract_color(text)
        
        # Special case: handle creation (common for mugs, cups, bags)
        if 'handle' in text and any(word in text for word in ['mug', 'cup', 'jug', 'pitcher', 'basket']):
            # Calculate handle size proportional to mug (cylinder radius is 4.5)
            cylinder_radius = 4.5
            handle_major_radius = cylinder_radius * 0.27  # ~1.2
            handle_minor_radius = cylinder_radius * 0.056  # ~0.25
            handle_x_position = cylinder_radius + handle_major_radius  # ~5.7
            
            api_calls.append({
                'api_name': 'bpy.ops.mesh.primitive_torus_add',
                'parameters': {
                    'major_radius': handle_major_radius,
                    'minor_radius': handle_minor_radius,
                    'location': (handle_x_position, 0, cylinder_radius * 0.4),  # ~1.8
                    'rotation': (1.5708, 0, 0),  # 90 degrees on X axis for perpendicular handle
                    '_color_hint': color if color else ''
                },
                'description': f'Create torus for handle: {subtask.title}'
            })
            # Add a scale to flatten it slightly for realistic handle shape
            api_calls.append({
                'api_name': 'bpy.ops.transform.resize',
                'parameters': {
                    'value': (1.0, 0.6, 1.2),  # Flatten and elongate
                    'orient_type': 'GLOBAL'
                },
                'description': 'Scale handle to realistic proportions'
            })
            return api_calls
        
        # Standard primitive handling
        for shape_name, api_name in self.primitive_mapping.items():
            if shape_name in text:
                # Extract size/scale if mentioned
                size = self._extract_size(text)
                location = self._extract_location(text, subtask)
                
                # Different primitives use different parameters
                params = {}
                
                if 'cylinder' in shape_name:
                    # Cylinder for coffee mug body - use larger sizes for visibility
                    params = {
                        'radius': size or 4.5,  # Increased from 0.5 to 1.5
                        'depth': (size or 4.5) * 2.4,  # Height = 2.4x radius for mug proportions
                        'location': location or (0, 0, 1.8),  # Adjusted for new size
                        '_color_hint': color if color else ''
                    }
                elif 'sphere' in shape_name or 'ball' in shape_name or 'balloon' in shape_name or 'globe' in shape_name or 'orb' in shape_name:
                    params = {
                        'radius': size or 8.0,  # Increased from 1.0 to 2.0 for better visibility
                        'location': location or (0, 0, (size or 8.0)),  # Lift sphere off ground by its radius
                        '_color_hint': color if color else ''
                    }
                    # Balloon-specific: add slight vertical scale for elongated shape
                    if 'balloon' in text:
                        params['_balloon_shape'] = True  # Coder will add scale operation
                elif 'cube' in shape_name or 'box' in shape_name:
                    params = {
                        'size': size or 9.0,  # Increased from 2.0 to 3.0
                        'location': location or (0, 0, 1.5),  # Center at half the size
                        '_color_hint': color if color else ''
                    }
                elif 'cone' in shape_name:
                    params = {
                        'radius1': size or 8.0,  # Increased from 1.0 to 2.0
                        'radius2': 0,
                        'depth': (size or 8.0) * 2,
                        'location': location or (0, 0, (size or 8.0)),
                        '_color_hint': color if color else ''
                    }
                else:
                    # Generic fallback
                    params = {'size': size or 8.0}
                    if location:
                        params['location'] = location
                    if color:
                        params['_color_hint'] = color
                
                api_calls.append({
                    'api_name': api_name,
                    'parameters': params,
                    'description': f'Create {shape_name} primitive for: {subtask.title}'
                })
                break  # Only use first match
        
        return api_calls
    
    def _handle_text_creation(self, text: str, subtask: SubTask) -> List[Dict[str, Any]]:
        """Handle text object creation with proper positioning and sizing."""
        # Extract quoted text
        quoted_text = self._extract_quoted_text(text)
        
        # Default text color - check for "text in X" or "X text" patterns
        color = None
        valid_colors = ['red', 'blue', 'green', 'yellow', 'white', 'black', 'brown', 
                       'orange', 'purple', 'pink', 'gray', 'grey', 'cyan', 'magenta']
        
        # Simple word-by-word check for colors near "text" keyword
        words = text.lower().split()
        for i, word in enumerate(words):
            if word in ['text', 'label', 'writing']:
                # Check word before
                if i > 0 and words[i-1] in valid_colors:
                    color = words[i-1]
                    break
                # Check word after
                if i < len(words) - 1 and words[i+1] in valid_colors:
                    color = words[i+1]
                    break
                # Check 2 words after (for "text in brown")
                if i < len(words) - 2 and words[i+2] in valid_colors:
                    color = words[i+2]
                    break
        
        # Position text CLOSER to mug surface for shrinkwrap to work
        # Cylinder radius is 4.5, position text slightly inside so shrinkwrap pushes it out
        cylinder_radius = 4.5
        text_location = (0, -(cylinder_radius - 0.5), cylinder_radius * 0.6)  # Slightly inside, will wrap out
        
        api_calls = [{
            'api_name': 'bpy.ops.object.text_add',
            'parameters': {
                'location': text_location,
                'enter_editmode': False,
                '_note': f'Set text body to: {quoted_text if quoted_text else "Text"}',
                '_text_size': 1.5,  # Size hint for coder
                '_text_color': color if color else None
            },
            'description': f'Create text object for: {subtask.title}'
        }]
        
        return api_calls
    
    def _handle_materials(self, text: str, subtask: SubTask) -> List[Dict[str, Any]]:
        """Handle material and color application."""
        api_calls = []
        
        # Extract color if present
        color = self._extract_color(text)
        
        # Strategy: Create material + assign it
        material_name = f"{color or 'Material'}_mat"
        
        api_calls.append({
            'api_name': 'bpy.ops.object.material_slot_add',
            'parameters': {},
            'description': f'Add material slot for {subtask.title}'
        })
        
        # Note about color if found
        if color:
            api_calls[0]['parameters']['_color_hint'] = color
        
        return api_calls
    
    def _handle_transformations(self, text: str, subtask: SubTask) -> List[Dict[str, Any]]:
        """Handle scale, rotation, translation."""
        api_calls = []
        
        # Scale operations
        if any(word in text for word in ['scale', 'size', 'resize']):
            scale_value = self._extract_scale(text)
            # If no specific scale value, use reasonable default (1.5x)
            if not scale_value:
                scale_value = (1.5, 1.5, 1.5)
            api_calls.append({
                'api_name': 'bpy.ops.transform.resize',
                'parameters': {
                    'value': scale_value,
                    'orient_type': 'GLOBAL'
                },
                'description': f'Scale object for: {subtask.title}'
            })
        
        # Rotation operations
        if 'rotate' in text:
            angle = self._extract_angle(text)
            api_calls.append({
                'api_name': 'bpy.ops.transform.rotate',
                'parameters': {
                    'value': angle or 1.5708,  # 90 degrees default
                    'orient_axis': 'Z',
                    'orient_type': 'GLOBAL'
                },
                'description': f'Rotate object for: {subtask.title}'
            })
        
        return api_calls
    
    # Helper methods for extraction
    
    def _extract_size(self, text: str) -> Optional[float]:
        """Extract size/radius from text."""
        # Look for patterns like "size 2", "radius 1.5", etc.
        size_match = re.search(r'(?:size|radius|diameter)\s*[:=]?\s*(\d+\.?\d*)', text)
        if size_match:
            return float(size_match.group(1))
        return None
    
    def _extract_location(self, text: str, subtask: SubTask) -> Optional[tuple]:
        """Extract location coordinates."""
        # Check context for location hints
        if 'origin' in text or 'center' in text:
            return (0, 0, 0)
        return None
    
    def _extract_quoted_text(self, text: str) -> Optional[str]:
        """Extract text within quotes."""
        quote_match = re.search(r'["\']([^"\']+)["\']', text)
        if quote_match:
            return quote_match.group(1)
        return None
    
    def _extract_color(self, text: str) -> Optional[str]:
        """Extract color name from text."""
        colors = ['red', 'blue', 'green', 'yellow', 'white', 'black', 'brown', 
                  'orange', 'purple', 'pink', 'gray', 'grey', 'cyan', 'magenta']
        for color in colors:
            if color in text:
                return color
        return None
    
    def _extract_scale(self, text: str) -> Optional[tuple]:
        """Extract scale values."""
        scale_match = re.search(r'scale\s*[:=]?\s*(\d+\.?\d*)', text)
        if scale_match:
            val = float(scale_match.group(1))
            return (val, val, val)
        return None
    
    def _extract_angle(self, text: str) -> Optional[float]:
        """Extract rotation angle in radians."""
        angle_match = re.search(r'(\d+)\s*(?:degrees?|deg)', text)
        if angle_match:
            degrees = float(angle_match.group(1))
            return degrees * 3.14159 / 180.0
        return None
