"""
LLM-based API Mapper for Blender Operations
Uses Gemini's Tool Calling feature for robust, structured output.
"""

import asyncio
import json
import logging
import os
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from .utils.rate_limiter import AsyncRateLimiter
import os
from collections import deque  # if not already present

from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.types import FunctionDeclaration, Tool, HarmCategory, HarmBlockThreshold
from google.api_core.exceptions import GoogleAPICallError
from grpc import aio as grpc_aio

from .models import SubTask
from .api_search import SearchContext, APICategory, OptimizedAPISearcher
from .simple_validator import SimpleAPIValidator
from .deterministic_mapper import DeterministicMapper
from prompts import APIMapperPrompts
from jinja2 import Template

# Load environment variables
load_dotenv()

class LLMAPIMapper:
    """
    LLM-powered API mapper that converts granular subtasks to specific Blender API calls
    using Gemini's Tool Calling feature for robust, structured output.
    """

    def __init__(self, model_name: str = "gemini-2.5-flash"):
        """Initialize the LLM API Mapper with Gemini and define the API tool."""
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
        
        genai.configure(api_key=api_key)
        
        self.blender_api_tool = Tool(
            function_declarations=[
                FunctionDeclaration(
                    name="generate_blender_api_calls",
                    description="Generates a list of Blender API calls for a given subtask.",
                    parameters={
                        "type": "object",
                        "properties": {
                            "api_calls": {
                                "type": "array",
                                "description": "A list of Blender API calls to execute.",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "api_name": {"type": "string", "description": "The full name of the Blender API function (e.g., 'bpy.ops.mesh.primitive_cube_add')."},
                                        "parameters": {"type": "object", "description": "A dictionary of parameters for the API call."},
                                        "description": {"type": "string", "description": "A brief explanation of what this API call does."}
                                    },
                                    "required": ["api_name", "parameters", "description"]
                                }
                            }
                        },
                        "required": ["api_calls"]
                    }
                )
            ]
        )
        
        self.model = genai.GenerativeModel(
            model_name=model_name,
            tools=[self.blender_api_tool]
        )
        
        self.logger = logging.getLogger(__name__)
        self.api_validator = SimpleAPIValidator()
        self.search_engine = OptimizedAPISearcher()
        self.deterministic_mapper = DeterministicMapper()
        # Metrics
        self.gemini_calls_made = 0
        self.deterministic_hits = 0
        self.llm_hits = 0
        rpm = int(os.getenv("GEMINI_RPM", "10"))
        window = float(os.getenv("GEMINI_RPM_WINDOW_SEC", "60"))
        self._rate_limiter = AsyncRateLimiter(max_calls=rpm, per_seconds=window)
        
        self.api_registry_path = Path(__file__).parent.parent / "blender_api_registry.json"
        self.valid_api_names = set()
        self._load_api_registry()
        # Curated allowlist for material/shader data APIs loaded from config
        self.curated_material_apis = self._load_curated_allowlist()

    def _load_api_registry(self):
        """Load the full API registry for validation."""
        self.logger.info(f"Attempting to load API registry from: {self.api_registry_path.resolve()}")
        try:
            if self.api_registry_path.exists():
                with open(self.api_registry_path, 'r', encoding='utf-8') as f:
                    registry = json.load(f)
                for api_name in registry.keys():
                    self.valid_api_names.add(api_name)
                self.logger.info(f"Successfully loaded {len(self.valid_api_names)} valid API names for validation.")
            else:
                self.logger.error("API registry file not found. API call validation will be skipped.")
        except Exception as e:
            self.logger.error(f"Error loading API registry: {e}", exc_info=True)

    def _load_curated_allowlist(self) -> set:
        """Load curated allowlist entries from config/curated_allowlist.json.
        Returns a set of strings. Falls back to a safe default if file is missing or invalid.
        """
        try:
            cfg_path = Path(__file__).parent.parent / "config" / "curated_allowlist.json"
            if cfg_path.exists():
                with open(cfg_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                materials = set(data.get("materials", []))
                if materials:
                    self.logger.info(f"Loaded {len(materials)} curated material allowlist entries from {cfg_path}.")
                    return materials
        except Exception as e:
            self.logger.warning(f"Failed to load curated allowlist: {e}")
        # Fallback defaults
        self.logger.info("Using built-in curated material allowlist defaults.")
        return {
            "bpy.data.materials.new",
            "<material>.use_nodes",
            "<material>.node_tree.nodes['Principled BSDF']",
            "<node>.inputs['Base Color'].default_value",
            "<node>.inputs['Roughness'].default_value",
            "<node>.inputs['Specular'].default_value",
            "<object>.data.materials.append",
            "<object>.data.materials[0]",
        }

    async def map_subtask_to_apis(self, subtask: SubTask, max_retries: int = 1, retry_mode: str = "feedback", allowed_apis: Optional[List[Dict[str, Any]]] = None, context: Dict[str, Any] = None) -> Optional[List[Dict[str, Any]]]:
        """
        Map a granular subtask to specific Blender API calls.
        Uses deterministic mapping first, then falls back to LLM with self-correction.
        """
        # TIER 1: Try deterministic mapping first
        if self.deterministic_mapper.can_handle(subtask):
            deterministic_result = self.deterministic_mapper.map(subtask, context=context)
            if deterministic_result:
                self.deterministic_hits += 1
                self.logger.info(f"✓ Deterministic mapping succeeded for '{subtask.title}' ({self.deterministic_hits} total hits)")
                return deterministic_result
        
        # TIER 2: Fall back to LLM mapping
        self.logger.info(f"→ Using LLM mapping for '{subtask.title}'")
        self.llm_hits += 1
        
        error_feedback = None
        # Retrieve an allowed API shortlist for grounding
        if allowed_apis is None:
            allowed_apis = await self._get_allowed_apis(subtask)
        # Determine attempts based on retry mode
        attempts_total = 0 if retry_mode == "none" else max_retries
        # Track repeated failure mode to early abort
        consecutive_empty_tool_outputs = 0
        consecutive_missing_tool_calls = 0
        for attempt in range(attempts_total + 1):
            prompt = self._create_mapping_prompt(subtask, error_feedback, allowed_apis=allowed_apis)

            try:
                self.logger.info(
                    f"Generating API calls for subtask: '{subtask.title}' (Attempt {attempt + 1}/{max_retries + 1})"
                )

                # Add timeout to avoid hanging on API calls
                _t0 = time.perf_counter()
                # Tighten tool calling if previous attempt failed to call tool or returned empty api_calls
                tool_cfg = {'function_calling_config': 'ANY'}
                if consecutive_missing_tool_calls > 0 or consecutive_empty_tool_outputs > 0:
                    # Strongly require the specific tool on subsequent attempts
                    tool_cfg = {'function_calling_config': 'REQUIRED'}

                # Respect free-tier Gemini rate limit
                await self._rate_limiter.acquire()
                response = await asyncio.wait_for(
                    self.model.generate_content_async(
                        prompt,
                        tool_config=tool_cfg,
                        safety_settings={
                            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                        }
                    ),
                    timeout=90
                )
                _dt = time.perf_counter() - _t0
                self.gemini_calls_made += 1
                self.logger.info(f"Gemini call #{self.gemini_calls_made} completed in {_dt:.2f}s")

                function_call = self._safe_extract_function_call(response)
                if not function_call:
                    self.logger.warning("LLM did not produce a valid tool function_call.")
                    error_feedback = (
                        "Your response did not include a valid 'generate_blender_api_calls' tool call. You MUST call this tool and return a non-empty 'api_calls' array."
                    )
                    consecutive_missing_tool_calls += 1
                    if consecutive_missing_tool_calls >= 2 or retry_mode == "none":
                        break
                    continue

                if function_call.name != 'generate_blender_api_calls':
                    self.logger.warning(f"LLM used unexpected tool: {function_call.name}")
                    error_feedback = "You used the wrong tool. You MUST call 'generate_blender_api_calls'."
                    consecutive_missing_tool_calls += 1
                    if consecutive_missing_tool_calls >= 2 or retry_mode == "none":
                        break
                    continue

                api_calls = function_call.args.get('api_calls') if hasattr(function_call, 'args') else None
                if not api_calls or not isinstance(api_calls, list):
                    self.logger.warning("Tool was called, but no API calls were generated.")
                    # Extra debug logging to inspect raw candidate content for diagnosis
                    try:
                        cand0 = response.candidates[0] if getattr(response, "candidates", None) else None
                        self.logger.debug(f"LLM raw first candidate content: {getattr(cand0, 'content', None)}")
                    except Exception:
                        pass
                    error_feedback = (
                        "You used the tool but did not provide a non-empty 'api_calls' array. You MUST return at least one valid API call with realistic parameters."
                    )
                    consecutive_empty_tool_outputs += 1
                    if consecutive_empty_tool_outputs >= 2 or retry_mode == "none":
                        break
                    continue

                self.logger.info(f"Received {len(api_calls)} API calls from LLM tool.")

                validated_calls, validation_errors = self._validate_api_calls(api_calls, allowed_apis=allowed_apis)
                if validation_errors:
                    self.logger.warning(f"Validation failed with {len(validation_errors)} errors.")
                    error_feedback = (
                        "Your previous attempt failed validation. Correct these errors:\n" + "\n".join(validation_errors)
                    )
                    # Do not loop endlessly on same validation errors
                    if retry_mode == "none":
                        break
                    continue

                # success
                self.logger.info(f"Total Gemini calls so far: {self.gemini_calls_made}")
                return validated_calls

            except asyncio.TimeoutError:
                _dt = time.perf_counter() - _t0 if '_t0' in locals() else 0.0
                self.gemini_calls_made += 1
                self.logger.error(f"Gemini call timed out after {_dt:.2f}s (call #{self.gemini_calls_made}).")
                error_feedback = (
                    "Your previous attempt timed out. Respond quickly with a valid 'generate_blender_api_calls' tool call."
                )
                if retry_mode == "none":
                    break
            except asyncio.CancelledError:
                _dt = time.perf_counter() - _t0 if '_t0' in locals() else 0.0
                self.gemini_calls_made += 1
                self.logger.error(f"Gemini call was cancelled after {_dt:.2f}s (call #{self.gemini_calls_made}).")
                error_feedback = (
                    "Your previous attempt was cancelled. Try again with a concise, valid tool call."
                )
                if retry_mode == "none":
                    break
            except (GoogleAPICallError, grpc_aio.AioRpcError) as e:
                _dt = time.perf_counter() - _t0 if '_t0' in locals() else 0.0
                self.gemini_calls_made += 1
                self.logger.error(f"Gemini API transport error after {_dt:.2f}s (call #{self.gemini_calls_made}): {e}", exc_info=True)
                error_feedback = (
                    "Transport error occurred. Try again with a valid 'generate_blender_api_calls' tool call."
                )
                if retry_mode == "none":
                    break
            except Exception as e:
                _dt = time.perf_counter() - _t0 if '_t0' in locals() else 0.0
                self.gemini_calls_made += 1
                self.logger.error(
                    f"Unexpected error in API mapping attempt {attempt + 1} after {_dt:.2f}s (call #{self.gemini_calls_made}): {e}",
                    exc_info=True
                )
                error_feedback = (
                    f"Unexpected error: {e}. Return only the required tool call with a valid 'api_calls' array."
                )
                if retry_mode == "none":
                    break

        self.logger.error(
            f"Failed to generate valid API calls for subtask '{subtask.title}' after {max_retries + 1} attempts. Falling back."
        )
        self.logger.info(f"Total Gemini calls so far: {self.gemini_calls_made}")
        return await self._fallback_mapping(subtask)

    def _safe_extract_function_call(self, response):
        """
        Safely extract function_call from Gemini response; returns None if missing.
        """
        try:
            if not response or not getattr(response, "candidates", None):
                return None
            first = response.candidates[0]
            if not getattr(first, "content", None) or not getattr(first.content, "parts", None):
                return None
            part0 = first.content.parts[0]
            return getattr(part0, "function_call", None)
        except Exception:
            return None

    def _create_mapping_prompt(self, subtask: SubTask, error_feedback: Optional[str] = None, allowed_apis: Optional[List[Dict[str, Any]]] = None) -> str:
        """Create a detailed prompt for LLM to map subtask to Blender APIs."""
        base_template_str = APIMapperPrompts.get_base_prompt_template()
        template = Template(base_template_str)
        context = {
            "subtask_title": subtask.title,
            "subtask_description": subtask.description,
            "task_type": subtask.type.value,
            "mesh_operations": subtask.context.get('mesh_operations', 'N/A'),
            "context": str(subtask.context),
            "error_feedback": error_feedback or "",
            "allowed_apis": allowed_apis or []
        }
        return template.render(context)

    async def _fallback_mapping(self, subtask: SubTask) -> List[Dict[str, Any]]:
        """Intelligent fallback using search if LLM mapping fails."""
        self.logger.warning(f"Executing intelligent fallback for subtask: {subtask.title}")
        search_query = subtask.title
        
        search_context = SearchContext(
            task_type="object_creation",
            max_results=5,
            preferred_categories=[APICategory.MESH_OPERATORS]
        )
        search_results = await self.search_engine.search(search_query, context=search_context)
        
        # No hardcoded fallback - let search results determine the best API
        best_api = None
        if search_results:
            for result in search_results:
                if 'primitive' in result.api.name and 'add' in result.api.name:
                    best_api = result.api.name
                    self.logger.info(f"Fallback search found a better primitive: {best_api}")
                    break
        
        # Only return if we found a valid API from search
        if best_api:
            return [{
                "api_name": best_api,
                "parameters": {"size": 1, "location": (0, 0, 0)},
                "description": f"[SEARCH FALLBACK] for: {subtask.title}"
            }]
        
        # No valid API found - return None to let deterministic mapper handle it
        self.logger.warning(f"Fallback search found no suitable API for: {subtask.title}")
        return None

    def _validate_api_calls(self, api_calls: List[Dict[str, Any]], allowed_apis: Optional[List[Dict[str, Any]]] = None) -> Tuple[List[Dict[str, Any]], List[str]]:
        """Validate every API call, returning validated calls and a list of error strings."""
        validated_calls = []
        validation_errors = []
        if not self.valid_api_names:
            self.logger.error("API registry not loaded. Cannot validate API calls.")
            return api_calls, ["API registry is not available for validation."]

        allowed_names = set(a.get("name") for a in (allowed_apis or []) if isinstance(a, dict) and a.get("name"))
        for call in api_calls:
            if not isinstance(call, dict) or "api_name" not in call:
                error_msg = f"Malformed API call object: `{str(call)}`. Each call must be a dictionary with an 'api_name' key."
                self.logger.error(error_msg)
                validation_errors.append(error_msg)
                continue

            api_name = call.get("api_name", "")

            if api_name not in self.valid_api_names:
                # Allow curated material data APIs only if they are concrete callable names
                # e.g., 'bpy.data.materials.new'. Reject placeholder patterns like '<material>....'
                if not (api_name in self.curated_material_apis and api_name.startswith("bpy.data.")):
                    error_msg = f"Hallucinated API detected: '{api_name}'. This API does not exist in the Blender registry. Please choose a valid API."
                    self.logger.error(error_msg)
                    validation_errors.append(error_msg)
                    continue
            # If we provided an allowed shortlist, enforce closed-world choice
            if allowed_names and api_name not in allowed_names:
                error_msg = f"API '{api_name}' is not in the allowed list for this subtask. Choose only from: {sorted(list(allowed_names))}"
                self.logger.error(error_msg)
                validation_errors.append(error_msg)
                continue
            
            validation_result = self.api_validator.validate_and_clean(
                call['api_name'], 
                call.get("parameters", {})
            )

            validated_calls.append({
                "api_name": validation_result["api_name"],
                "parameters": validation_result.get("parameters", {}),
                "description": call.get("description", ""),
                "execution_order": len(validated_calls) + 1,
            })
                
        return validated_calls, validation_errors

    async def _get_allowed_apis(self, subtask: SubTask, top_k: int = 8) -> List[Dict[str, Any]]:
        """Retrieve a shortlist of allowed bpy.ops.* APIs for the given subtask using the search engine.
        Returns a list of dicts: {"name": str, "description": str}.
        """
        try:
            query = f"{subtask.title or ''} | {subtask.description or ''}"
            is_material = self._is_material_related(subtask)
            # Broaden categories for material-related tasks
            categories = [APICategory.MESH_OPERATORS]
            if is_material:
                categories.extend([APICategory.SHADER_NODES, APICategory.MATERIAL_OPERATORS])

            search_ctx = SearchContext(
                task_type="object_creation",
                max_results=top_k,
                preferred_categories=categories
            )
            results = await self.search_engine.search(query, context=search_ctx)
            shortlist: List[Dict[str, Any]] = []
            seen = set()
            for r in results or []:
                name = getattr(r.api, "name", None)
                if not name or name in seen:
                    continue
                # For non-material tasks, we keep bpy.ops.* only.
                if (not is_material) and (not name.startswith("bpy.ops.")):
                    continue
                desc = getattr(r.api, "description", "")
                shortlist.append({"name": name, "description": desc})
                seen.add(name)
                if len(shortlist) >= top_k:
                    break
            # Inject curated material APIs as guidance if material-related
            if is_material:
                for cname in sorted(self.curated_material_apis):
                    if cname.startswith("bpy.data.") and cname not in seen:
                        shortlist.append({"name": cname, "description": "Core material creation or assignment API."})
                        seen.add(cname)
            return shortlist
        except Exception as e:
            self.logger.warning(f"Allowed API retrieval failed: {e}")
            return []

    def _is_material_related(self, subtask: SubTask) -> bool:
        text = f"{subtask.title} {subtask.description}".lower()
        keywords = ["material", "shader", "color", "colour", "bsdf", "texture"]
        return any(k in text for k in keywords)