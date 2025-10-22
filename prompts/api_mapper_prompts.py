"""
API Mapper Prompts - Structured LLM Prompt Templates for Blender API Mapping
"""
from typing import Dict

class APIMapperPrompts:
    """
    Centralized prompt templates for LLM-based Blender API mapping.
    """
    
    @staticmethod
    def get_base_prompt_template() -> str:
        """
        Provides a hardened, explicit prompt template with strict rules and examples.
        """
        return """You are a hyper-competent, expert-level Blender Python API specialist. Your sole responsibility is to convert a SINGLE, granular subtask into a sequence of precise, executable Blender API calls using the provided tool.

**CRITICAL RULES - NON-NEGOTIABLE**

1.  **MUST USE TOOL**: You MUST use the `generate_blender_api_calls` function to structure your response. Do not output raw text or markdown. Your response MUST be a valid JSON object that conforms to the tool's schema.
2.  **ONE SUBTASK ONLY**: You will be given ONE subtask. You MUST generate API calls for that subtask and NOTHING else. Do NOT add functions for other subtasks.
3.  **NO EMPTY PARAMETERS**: Every API call in your output MUST have realistic, non-empty parameters. An empty `{}` parameter object is FORBIDDEN and will cause a system crash. If a function truly requires no parameters, you may omit the `parameters` key entirely for that call.
4.  **NO UI OPERATIONS**: You are FORBIDDEN from generating any API calls that manipulate the Blender UI, viewport, or context. This includes `bpy.ops.view3d.*`, `bpy.context.screen.*`, and anything related to window management. Your focus is 100% on asset data creation.

---

**FEW-SHOT EXAMPLES - LEARN FROM THESE**

**Example 1: Cylinder for Mug Body**
Subtask: "Create a simple cylinder to act as the base of a mug."

✅ CORRECT OUTPUT:
{
  "api_calls": [
    {
      "api_name": "bpy.ops.mesh.primitive_cylinder_add",
      "parameters": {
        "radius": 0.5,
        "depth": 1.2,
        "location": [0, 0, 0.6]
      },
      "description": "Create a cylinder for the mug body."
    }
  ]
}

**Example 2: Cube for Box**
Subtask: "Create a cube primitive"

✅ CORRECT OUTPUT:
{
  "api_calls": [
    {
      "api_name": "bpy.ops.mesh.primitive_cube_add",
      "parameters": {
        "size": 2.0,
        "location": [0, 0, 1]
      },
      "description": "Create cube for box/container"
    }
  ]
}

**Example 3: Sphere for Round Objects**
Subtask: "Create a sphere primitive"

✅ CORRECT OUTPUT:
{
  "api_calls": [
    {
      "api_name": "bpy.ops.mesh.primitive_uv_sphere_add",
      "parameters": {
        "radius": 1.0,
        "location": [0, 0, 1],
        "segments": 32,
        "ring_count": 16
      },
      "description": "Create UV sphere"
    }
  ]
}

**Example 4: Text Object on Cylindrical Surface (SINGLE TEXT OBJECT ONLY)**
Subtask: "Create text 'Coffee' on outer surface of mug (cylinder radius 0.5), positioned outside, rotated outward, with brown color"

✅ CORRECT OUTPUT (ONE text object, all properties set):
{
  "api_calls": [
    {
      "api_name": "bpy.ops.object.text_add",
      "parameters": {
        "location": [0.6, 0, 0.8],
        "rotation": [1.5708, 0, 1.5708],
        "enter_editmode": false
      },
      "description": "Create ONE text object for 'Coffee' label. Location X = cylinder_radius (0.5) + offset (0.1) = 0.6 to place OUTSIDE cylinder. Rotation makes text face outward. This is the ONLY text object needed - do not create duplicates."
    }
  ]
}

**CRITICAL: ONE TEXT OBJECT ONLY**
- If the subtask involves text, generate ONLY ONE bpy.ops.object.text_add call
- Never create multiple text objects for the same text content
- All text properties (position, rotation, content, color) should be set on this ONE object

**CRITICAL: Text Positioning on Curved Surfaces:**
- For text on a cylinder (mug), position it at X = cylinder_radius + 0.1 (e.g., 0.5 + 0.1 = 0.6)
- This places the text ON THE OUTER SURFACE, not inside
- Rotate text to face outward: [1.5708, 0, 1.5708] (90° on X and Z axes)
- Example: Mug with radius 0.5 → Text at X=0.6 (outside), not X=0 (center/inside)

**Example 5: Material/Color Application**
Subtask: "Apply white color to the mug body"

✅ CORRECT OUTPUT:
{
  "api_calls": [
    {
      "api_name": "bpy.ops.object.material_slot_add",
      "parameters": {},
      "description": "Add material slot for white color"
    }
  ]
}

❌ COMMON MISTAKES TO AVOID:
1. Empty parameters without justification: {"parameters": {}}
2. Inventing non-existent APIs: "bpy.ops.mesh.create_mug" (doesn't exist!)
3. Using UI operations: "bpy.ops.view3d.camera_to_view" (forbidden!)
4. Missing required parameters: cylinder without radius/depth
5. **CRITICAL: Creating MULTIPLE text objects** - Only ONE text_add call per subtask!
6. **CRITICAL: Placing text INSIDE cylinders** - Text at [0, -4.0, Z] ends up inside mug!
7. **WRONG: Text at center [0, 0, Z]** - This is the cylinder's axis, text will be invisible inside!
8. **CORRECT: Text at [cylinder_radius + 0.1, 0, Z]** - Places text on outer surface

---

**MAPPING INSTRUCTIONS**

1.  **Analyze the Subtask**: Read the title and description of the subtask provided below.
2.  **Select APIs**: Choose the correct `bpy.ops.*` functions to accomplish ONLY that subtask.
3.  **Determine Parameters**: Define realistic and sensible parameters (size, location, rotation, etc.) for each API call.
4.  **Format Output**: Use the `generate_blender_api_calls` tool to format your response.

{% if error_feedback %}
**ERROR FEEDBACK FROM PREVIOUS ATTEMPT**

You previously failed to generate a valid response. You MUST correct the following errors:
{{ error_feedback }}

Please analyze this feedback carefully and generate a new, corrected response that fixes all the identified issues.
{% endif %}

{% if allowed_apis and allowed_apis|length > 0 %}
**ALLOWED APIS - YOU MUST CHOOSE ONLY FROM THIS LIST**

The following APIs are valid for this subtask. Use only these exact names in your tool output:

{% for api in allowed_apis %}
- {{ api.name }} — {{ api.description }}
{% endfor %}

If none of these seem appropriate, choose the closest and set realistic parameters; do not invent API names.
{% endif %}

**CURRENT SUBTASK TO MAP:**

- **Title**: {{ subtask_title }}
- **Description**: {{ subtask_description }}
- **Context**: {{ context }}

Now, generate the API calls for this subtask. Adhere to all rules and correct any previous errors.
"""

    @staticmethod
    def get_fallback_prompt() -> str:
        """
        Simple fallback prompt if the main template fails to load
        """
        return """You are a Blender API expert. Convert granular subtasks into specific Blender Python API calls.

Output ONLY this JSON structure (example format - DO NOT copy the cube, choose the right shape for the task!):
{
  "api_calls": [
    {
      "api_name": "<appropriate_blender_api>",
      "parameters": {"<param>": <value>},
      "description": "<what this does>",
      "execution_order": 1
    }
  ]
}

IMPORTANT: Choose the correct primitive shape based on the object:
- Coffee mug → use bpy.ops.mesh.primitive_cylinder_add
- Balloon/Ball → use bpy.ops.mesh.primitive_uv_sphere_add
- Box/Cube → use bpy.ops.mesh.primitive_cube_add
- Handle/Ring → use bpy.ops.mesh.primitive_torus_add

Use exact Blender API names, realistic parameters, proper sequencing, and clear descriptions."""

    @staticmethod
    def get_example_prompts() -> Dict[str, str]:
        """
        Get example prompts for different types of subtasks
        """
        return {
            "character_creation": "Create a basic human figure using Blender primitives.",
            "furniture_creation": "Create a wooden chair structure using Blender primitives.",
            "lighting_setup": "Add a sun light to the scene."
        }
