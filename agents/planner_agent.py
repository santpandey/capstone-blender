"""
Planner Agent - Decomposes natural language prompts into structured subtasks
First agent in the multi-agent pipeline for 3D asset generation
"""

import re
import uuid
import asyncio
import json
import os
from typing import Dict, Any, List
from dotenv import load_dotenv
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from .utils.rate_limiter import AsyncRateLimiter
import os

from .base_agent import BaseAgent
from .models import (
    AgentType, AgentStatus, PlannerInput, PlannerOutput, TaskPlan, SubTask,
    TaskType, TaskComplexity, TaskPriority
)

class PlannerAgent(BaseAgent):
    """
    Planner Agent that decomposes natural language prompts into a structured TaskPlan.
    This agent uses a powerful LLM with a 'Chain of Thought' prompt to ensure
    detailed and accurate planning.
    """
    
    def __init__(self):
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="Planner Agent"
        )
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.llm_available = True
            rpm = int(os.getenv("GEMINI_RPM", "10"))
            window = float(os.getenv("GEMINI_RPM_WINDOW_SEC", "60"))
            self._rate_limiter = AsyncRateLimiter(max_calls=rpm, per_seconds=window)
        else:
            self.llm_available = False
            self.logger.warning("GEMINI_API_KEY not found. Planning will fail.")

    async def plan(self, prompt: str) -> TaskPlan:
        """Simple interface to generate a plan from a prompt string."""
        input_data = PlannerInput(prompt=prompt)
        result = await self.process(input_data)
        if result.success and result.plan:
            return result.plan
        else:
            raise Exception(f"Planning failed: {result.message}")

    async def process(self, input_data: PlannerInput) -> PlannerOutput:
        """Processes the planning request by generating a structured TaskPlan using an LLM."""
        try:
            self.logger.info(f"Generating plan for prompt: '{input_data.prompt[:100]}...'" )
            if not self.llm_available:
                raise Exception("LLM is not available. Cannot generate a plan.")

            # STAGE 1: Generate a high-level plan in text from the LLM.
            text_plan = await self._generate_text_plan_with_llm(input_data.prompt)

            # STAGE 2: Convert the text-based plan into a structured JSON TaskPlan.
            if text_plan.startswith("FALLBACK:"):
                self.logger.warning("Generating fallback plan due to failure in text generation stage.")
                task_plan = self._create_fallback_plan(input_data.prompt)
            else:
                task_plan = await self._convert_text_to_structured_plan(text_plan, input_data.prompt)
                # Post-process: expand material steps into finer-grained subtasks
                task_plan = self._expand_material_subtasks(task_plan)

            return PlannerOutput(
                agent_type=self.agent_type,
                status=AgentStatus.COMPLETED,
                success=True,
                message=f"Successfully generated plan with {len(task_plan.subtasks)} subtasks.",
                plan=task_plan,
                planning_rationale=text_plan
            )
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return PlannerOutput(
                agent_type=self.agent_type,
                status=AgentStatus.FAILED,
                success=False,
                message=str(e),
                errors=[str(e)]
            )

    async def _generate_text_plan_with_llm(self, prompt: str) -> str:
        """Generates a high-level text plan using the LLM, with robust error handling."""
        planning_prompt = self._create_planning_prompt(prompt)
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            await self._rate_limiter.acquire()
            response = await model.generate_content_async(planning_prompt)
            self.logger.info("Successfully generated text plan from LLM.")
            return response.text.strip()
        except google_exceptions.GoogleAPICallError as e:
            self.logger.error(f"Gemini API call failed during text plan generation: {e.message}", exc_info=True)
            return f"FALLBACK: {e.message}"
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during text plan generation: {e}", exc_info=True)
            return f"FALLBACK: {str(e)}"

    def _create_fallback_plan(self, prompt: str) -> TaskPlan:
        """Creates a single, generic subtask when the LLM fails."""
        self.logger.warning(f"Creating a generic fallback plan for prompt: {prompt}")
        fallback_subtask = SubTask(
            task_id="task_001",
            title="Generic Asset Creation",
            description=f"Create a generic 3D asset based on the prompt: '{prompt}'.",
            type=TaskType.CREATE_OBJECT,
            complexity=TaskComplexity.MODERATE,
            priority=TaskPriority.HIGH,
            estimated_time_minutes=15,
            dependencies=[]
        )
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            original_prompt=prompt,
            summary="Generic fallback plan",
            subtasks=[fallback_subtask],
            total_estimated_time=15,
            overall_complexity=TaskComplexity.MODERATE,
            tags=["fallback"]
        )

    def _create_planning_prompt(self, prompt: str) -> str:
        return f"""You are a master 3D artist and project planner. Your task is to decompose a user's request into a detailed, step-by-step plan. Output only the plan as a numbered list. Do not generate JSON.

**Chain of Thought Instructions:**
1.  **Deconstruct**: Break the user's request into its core components (e.g., a 'house' has 'walls' and a 'roof').
2.  **Sequence**: Determine the logical order of creation. You must build the base before adding details.
3.  **Specify Actions**: For each step, specify the action, like 'Create', 'Apply Material', 'Add Text'.
4.  **Describe Details**: Include all details from the prompt, like colors, textures, and text content.
5.  **ONE TEXT OBJECT**: If the prompt includes text, create ONLY ONE subtask for text. Include creation, positioning, rotation, and color in that SINGLE subtask. Never create multiple text subtasks.

**IMPORTANT - Choose Correct Shapes:**
- Coffee mug / Cup → Use CYLINDER for the body
- Ball / Balloon / Sphere → Use SPHERE
- Box / Container / Crate → Use CUBE
- Handle / Ring → Use TORUS
- Table leg / Pipe → Use CYLINDER
- Cone / Pyramid tip → Use CONE

**CRITICAL - Text Positioning on Cylindrical Objects (Mugs, Cups, etc.):**
When adding text to a cylindrical object like a mug:
1. Position the text OUTSIDE the cylinder, not at the center
2. Calculate position: cylinder_radius + text_offset (e.g., radius + 0.1)
3. Rotate the text to face outward (90 degrees from cylinder axis)
4. The text should appear like a sticker/decal on the outer surface
5. For a vertical cylinder (mug), position text at mid-height and offset from center along X or Y axis

**Example positioning for text on mug:**
- Mug radius: 0.5
- Text position: (0.6, 0, 0.5) ← Outside the mug, on the outer surface
- Text rotation: Facing outward toward viewer

**Example 1:**

*   **User Prompt**: 'A wooden table with a book on it'
*   **Your Output**:
    1.  Create a flat, wide cube for the tabletop.
    2.  Create four long, thin cylinders for the table legs and position them under the tabletop.
    3.  Create a small, flat cube for the main body of the book.
    4.  Place the book object on top of the table object.
    5.  Apply a dark wood texture to the tabletop and legs.

**Example 2:**

*   **User Prompt**: 'A white coffee mug with "Coffee" text in brown'
*   **Your Output**:
    1.  Create a CYLINDER for the mug body (coffee mugs are cylindrical!).
    2.  Create a TORUS for the handle and position it on the side of the cylinder.
    3.  Apply white color to both the mug body and handle.
    4.  Create ONE text object with content "Coffee", positioned OUTSIDE the cylinder at (radius + 0.1), rotated to face outward, and colored brown.

**CRITICAL: For text on objects, create ONLY ONE subtask that includes creation, positioning, rotation, AND color. Do NOT create separate subtasks for each step.**

**Example 3:**

*   **User Prompt**: 'A green cube'
*   **Your Output**:
    1.  Create a CUBE.
    2.  Apply green color to the cube.

**Example 4:**

*   **User Prompt**: 'A white cloud'
*   **Your Output**:
    1.  Create multiple SPHERES of different sizes grouped together to form cloud shape.
    2.  Apply white color to all spheres.
    3.  Position spheres overlapping to create fluffy cloud appearance.

**Your Task:**

Now, generate a step-by-step text plan for the following user prompt. Remember to use the correct shape primitives!

**Prompt**: "{prompt}"""

    async def _convert_text_to_structured_plan(self, text_plan: str, original_prompt: str) -> TaskPlan:
        """Converts a text-based plan from the LLM into a structured TaskPlan JSON object."""
        
        # Dynamically generate the list of valid TaskType enum values.
        valid_task_types = " | ".join([t.value for t in TaskType])

        conversion_prompt = f"""You are a JSON formatting expert. Convert the following step-by-step text plan into a valid JSON `TaskPlan` object. Assign a `task_id`, `title`, `description`, and `type` for each step. The `type` must be one of the following values: [{valid_task_types}]. Infer dependencies correctly.

**Text Plan:**
{text_plan}

**JSON Output Format:**
```json
{{
    "plan_id": "...",
    "prompt": "{original_prompt}",
    "subtasks": [
        {{
            "task_id": "task_001",
            "title": "...",
            "description": "...",
            "type": "{valid_task_types}",
            "dependencies": []
        }}
    ]
}}
```
"""
        try:
            model = genai.GenerativeModel('gemini-2.5-flash')
            response = await model.generate_content_async(conversion_prompt)
            response_text = response.text.strip()

            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                raise ValueError("No valid JSON object found in the LLM response during conversion.")
            json_str = response_text[json_start:json_end]
            
            plan_data = json.loads(json_str)

            # CRITICAL FIX: Convert the 'type' field to lowercase to match the Pydantic enum.
            subtask_data = plan_data.get('subtasks', [])
            for st in subtask_data:
                if 'type' in st and isinstance(st['type'], str):
                    st['type'] = st['type'].lower()

            subtasks = [SubTask(**st) for st in subtask_data]
            return TaskPlan(
                plan_id=plan_data.get('plan_id', str(uuid.uuid4())),
                original_prompt=original_prompt,
                summary=f"Plan for '{original_prompt}' with {len(subtasks)} steps.",
                subtasks=subtasks,
                total_estimated_time=15 * len(subtasks), # Simple estimation
                overall_complexity=TaskComplexity.MODERATE,
                tags=[]
            )
        except google_exceptions.GoogleAPICallError as e:
            self.logger.error(f"Gemini API call failed during JSON conversion: {e.message}", exc_info=True)
            return self._create_fallback_plan(original_prompt)
        except Exception as e:
            self.logger.error(f"Failed to convert text plan to JSON: {e}", exc_info=True)
            return self._create_fallback_plan(original_prompt)

    def _expand_material_subtasks(self, plan: TaskPlan) -> TaskPlan:
        """Split any 'Apply material' subtask into finer-grained steps to improve API mapping.
        Rules:
        - Detect subtasks whose title/description references material/shader/color/colour
        - Replace each such subtask with 4 micro-steps:
          1) Ensure target object selected/active
          2) Create or reuse material and enable nodes
          3) Configure Principled BSDF base color/roughness/specular
          4) Assign material to object's material slots
        Dependencies are chained sequentially and respect original dependencies.
        """
        try:
            from .models import SubTask, TaskType, TaskComplexity, TaskPriority
            new_subtasks = []
            id_counter = 1
            for st in plan.subtasks:
                text = f"{st.title} {st.description}".lower()
                if any(k in text for k in ["apply material", "material", "shader", "colour", "color"]):
                    base_prefix = st.task_id.rsplit("_", 1)[0] if "_" in st.task_id else st.task_id
                    # Derive object name hint, if present
                    obj_hint = "object"
                    if "cone" in text:
                        obj_hint = "cone"
                    elif "mug" in text:
                        obj_hint = "mug"

                    s1 = SubTask(
                        task_id=f"{base_prefix}_mat_{id_counter:03d}",
                        title=f"Select and activate {obj_hint} object",
                        description=f"Deselect all, select the {obj_hint} by name, and set it active for material assignment.",
                        type=TaskType.MATERIAL_APPLICATION,
                        complexity=st.complexity,
                        priority=TaskPriority.HIGH,
                        estimated_time_minutes=1,
                        dependencies=st.dependencies,
                    ); id_counter += 1
                    s2 = SubTask(
                        task_id=f"{base_prefix}_mat_{id_counter:03d}",
                        title=f"Create/reuse material and enable nodes",
                        description=f"Create a material named based on the {obj_hint} (e.g., '{obj_hint.capitalize()}Mat') and set use_nodes=True.",
                        type=TaskType.MATERIAL_APPLICATION,
                        complexity=st.complexity,
                        priority=TaskPriority.HIGH,
                        estimated_time_minutes=1,
                        dependencies=[s1.task_id],
                    ); id_counter += 1
                    s3 = SubTask(
                        task_id=f"{base_prefix}_mat_{id_counter:03d}",
                        title=f"Configure Principled BSDF parameters",
                        description=f"Set Base Color, Roughness, and Specular on the Principled BSDF node to match the prompt.",
                        type=TaskType.MATERIAL_APPLICATION,
                        complexity=st.complexity,
                        priority=TaskPriority.HIGH,
                        estimated_time_minutes=1,
                        dependencies=[s2.task_id],
                    ); id_counter += 1
                    s4 = SubTask(
                        task_id=f"{base_prefix}_mat_{id_counter:03d}",
                        title=f"Assign material to {obj_hint}",
                        description=f"Assign the material to the object's material slots (append or replace index 0).",
                        type=TaskType.MATERIAL_APPLICATION,
                        complexity=st.complexity,
                        priority=TaskPriority.HIGH,
                        estimated_time_minutes=1,
                        dependencies=[s3.task_id],
                    ); id_counter += 1
                    new_subtasks.extend([s1, s2, s3, s4])
                else:
                    new_subtasks.append(st)
            plan.subtasks = new_subtasks
            return plan
        except Exception:
            # If anything goes wrong, return the original plan unchanged
            return plan
