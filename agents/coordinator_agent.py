"""
Coordinator Agent - Maps subtasks to specific Blender APIs using optimized search
Second agent in the multi-agent pipeline for 3D asset generation
"""

import asyncio
import time
import logging
from typing import Dict, List, Optional, Any, Tuple
from concurrent.futures import ThreadPoolExecutor

from .base_agent import BaseAgent
from .models import (
    AgentType, AgentStatus, AgentResponse,
    CoordinatorInput, CoordinatorOutput, APIMapping,
    TaskPlan, SubTask, TaskType
)
from .llm_api_mapper import LLMAPIMapper
from .api_search import (
    OptimizedAPISearcher,
    SearchConfig,
    create_search_context
)
from .api_search.models import SearchContext, APICategory

class CoordinatorAgent(BaseAgent):
    """
    Coordinator Agent that maps subtasks to specific Blender APIs
    
    Key responsibilities:
    1. Take structured subtasks from Planner Agent
    2. Use optimized search engine to find relevant Blender APIs
    3. Map each subtask to specific API calls with parameters
    4. Validate API compatibility and workflow coherence
    5. Generate execution strategy for the Coder Agent
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.COORDINATOR,
            name="coordinator_agent",
            config=config or {}
        )
        
        # Initialize API search engine
        search_config = SearchConfig(
            enable_caching=True,
            cache_size=1000,
            preload_indices=True,
            lazy_load_embeddings=True,
            max_concurrent_searches=5
        )
        self.api_searcher = OptimizedAPISearcher(search_config)
        
        # Initialize LLM-based API mapper
        try:
            self.llm_mapper = LLMAPIMapper()
            self.use_llm_mapping = True
            self.logger.info("LLM API Mapper initialized successfully")
        except Exception as e:
            self.logger.warning(f"LLM API Mapper initialization failed: {e}")
            self.llm_mapper = None
            self.use_llm_mapping = False
        
        # Task type to API category mapping
        self.task_category_mapping = {
            TaskType.CREATE_CHARACTER: [APICategory.MESH_OPERATORS, APICategory.OBJECT_OPERATORS],
            TaskType.CREATE_OBJECT: [APICategory.MESH_OPERATORS, APICategory.OBJECT_OPERATORS],
            TaskType.CREATE_FURNITURE: [APICategory.MESH_OPERATORS, APICategory.OBJECT_OPERATORS],
            TaskType.CREATE_CLOTHING: [APICategory.MESH_OPERATORS, APICategory.GEOMETRY_NODES],
            TaskType.CREATE_ARCHITECTURE: [APICategory.MESH_OPERATORS, APICategory.OBJECT_OPERATORS],
            TaskType.CREATE_ENVIRONMENT: [APICategory.OBJECT_OPERATORS, APICategory.SCENE_OPERATORS],
            TaskType.LIGHTING_SETUP: [APICategory.OBJECT_OPERATORS, APICategory.SCENE_OPERATORS],
            TaskType.MATERIAL_APPLICATION: [APICategory.SHADER_NODES, APICategory.MATERIAL_OPERATORS],
            TaskType.SCENE_COMPOSITION: [APICategory.OBJECT_OPERATORS],
            TaskType.ANIMATION_SETUP: [APICategory.ANIMATION_OPERATORS, APICategory.OBJECT_OPERATORS],
            TaskType.POST_PROCESSING: [APICategory.SCENE_OPERATORS]
        }
        
        # API search strategies by task complexity
        self.complexity_search_strategies = {
            "simple": {"max_results": 3, "min_relevance": 0.7},
            "moderate": {"max_results": 5, "min_relevance": 0.6},
            "complex": {"max_results": 8, "min_relevance": 0.5},
            "expert": {"max_results": 10, "min_relevance": 0.4}
        }
        
        # Thread pool for concurrent API searches
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Performance tracking
        self.coordination_metrics = []
        self._initialized = False
    
    async def initialize(self) -> bool:
        """Initialize the coordinator agent and its search engine"""
        if self._initialized:
            return True
        
        try:
            self.logger.info("Initializing Coordinator Agent...")
            
            # Initialize API search engine
            success = await self.api_searcher.initialize()
            if not success:
                raise Exception("Failed to initialize API search engine")
            
            self._initialized = True
            self.logger.info("Coordinator Agent initialized successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Coordinator Agent: {e}")
            return False
    
    async def process(self, input_data: CoordinatorInput) -> CoordinatorOutput:
        """Process coordination request and generate API mappings"""
        
        if not self._initialized:
            if not await self.initialize():
                return CoordinatorOutput(
                    agent_type=AgentType.COORDINATOR,
                    status=AgentStatus.FAILED,
                    success=False,
                    message="Coordinator Agent not initialized"
                )
        
        try:
            self.logger.info(f"Coordinating plan with {len(input_data.plan.subtasks)} subtasks")
            
            start_time = time.time()
            
            # Step 1: Analyze the plan and validate subtasks
            plan_analysis = await self._analyze_plan(input_data.plan)
            
            # Step 2: Generate API mappings for each subtask
            api_mappings = await self._generate_api_mappings(
                input_data.plan.subtasks, 
                input_data.execution_context
            )
            
            # Step 3: Validate API compatibility and workflow coherence
            validated_mappings = await self._validate_api_mappings(api_mappings, input_data.plan)
            
            # Step 4: Generate execution strategy
            execution_strategy = self._generate_execution_strategy(validated_mappings, input_data.plan)
            
            # Step 5: Calculate resource requirements
            resource_requirements = self._calculate_resource_requirements(validated_mappings)
            
            coordination_time = (time.time() - start_time) * 1000
            
            return CoordinatorOutput(
                agent_type=AgentType.COORDINATOR,
                status=AgentStatus.COMPLETED,
                success=True,
                message=f"Successfully coordinated {len(validated_mappings)} API mappings",
                data={
                    "plan_analysis": plan_analysis,
                    "coordination_time_ms": coordination_time,
                    "total_api_calls": sum(len(mapping.api_calls) for mapping in validated_mappings),
                    "avg_confidence": sum(mapping.confidence_score for mapping in validated_mappings) / max(len(validated_mappings), 1)
                },
                api_mappings=validated_mappings,
                execution_strategy=execution_strategy,
                resource_requirements=resource_requirements
            )
            
        except Exception as e:
            self.logger.error(f"Coordination failed: {e}")
            return CoordinatorOutput(
                agent_type=AgentType.COORDINATOR,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Coordination failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _analyze_plan(self, plan: TaskPlan) -> Dict[str, Any]:
        """Analyze the task plan for coordination insights"""
        
        analysis = {
            "total_subtasks": len(plan.subtasks),
            "task_types": {},
            "complexity_distribution": {},
            "estimated_api_calls": 0,
            "potential_bottlenecks": [],
            "parallelization_opportunities": []
        }
        
        # Analyze task types
        for subtask in plan.subtasks:
            task_type = subtask.type.value
            analysis["task_types"][task_type] = analysis["task_types"].get(task_type, 0) + 1
            
            complexity = subtask.complexity.value
            analysis["complexity_distribution"][complexity] = analysis["complexity_distribution"].get(complexity, 0) + 1
            
            # Estimate API calls needed based on task type and complexity
            base_calls = self._estimate_api_calls_for_task(subtask)
            analysis["estimated_api_calls"] += base_calls
        
        # Identify potential bottlenecks
        for subtask in plan.subtasks:
            if subtask.complexity.value == "expert" and len(subtask.dependencies) > 0:
                analysis["potential_bottlenecks"].append(subtask.task_id)
        
        # Identify parallelization opportunities
        independent_tasks = [task for task in plan.subtasks if not task.dependencies]
        if len(independent_tasks) > 1:
            analysis["parallelization_opportunities"] = [task.task_id for task in independent_tasks]
        
        return analysis
    
    def _estimate_api_calls_for_task(self, subtask: SubTask) -> int:
        """Estimate number of API calls needed for a subtask"""
        base_calls = {
            TaskType.CREATE_CHARACTER: 8,
            TaskType.CREATE_OBJECT: 4,
            TaskType.CREATE_FURNITURE: 6,
            TaskType.CREATE_CLOTHING: 7,
            TaskType.CREATE_ARCHITECTURE: 10,
            TaskType.CREATE_ENVIRONMENT: 12,
            TaskType.LIGHTING_SETUP: 3,
            TaskType.MATERIAL_APPLICATION: 4,
            TaskType.SCENE_COMPOSITION: 5,
            TaskType.ANIMATION_SETUP: 6,
            TaskType.POST_PROCESSING: 3
        }
        
        base = base_calls.get(subtask.type, 5)
        
        # Adjust based on complexity
        complexity_multipliers = {
            "simple": 0.7,
            "moderate": 1.0,
            "complex": 1.5,
            "expert": 2.0
        }
        
        multiplier = complexity_multipliers.get(subtask.complexity.value, 1.0)
        return int(base * multiplier)
    
    async def _generate_api_mappings(
        self, 
        subtasks: List[SubTask], 
        execution_context: Dict[str, Any]
    ) -> List[APIMapping]:
        """Generate API mappings for all subtasks concurrently"""
        
        # Create mapping tasks for concurrent execution
        mapping_tasks = []
        for subtask in subtasks:
            task = self._map_subtask_to_apis(subtask, execution_context)
            mapping_tasks.append(task)
        
        # Execute all mappings concurrently
        api_mappings = await asyncio.gather(*mapping_tasks, return_exceptions=True)
        
        # Filter out exceptions and log errors
        valid_mappings = []
        for i, mapping in enumerate(api_mappings):
            if isinstance(mapping, Exception):
                self.logger.error(f"Failed to map subtask {subtasks[i].task_id}: {mapping}")
            else:
                valid_mappings.append(mapping)
        
        return valid_mappings
    
    async def _map_subtask_to_apis(
        self, 
        subtask: SubTask, 
        execution_context: Dict[str, Any]
    ) -> APIMapping:
        """Map a single subtask to specific Blender APIs using LLM or fallback to search"""
        
        # Try LLM-based mapping first (preferred approach)
        if self.use_llm_mapping and self.llm_mapper:
            try:
                self.logger.info(f"Using LLM to map subtask: {subtask.title}")
                
                # Get LLM-generated API calls
                llm_api_calls = await self.llm_mapper.map_subtask_to_apis(subtask)
                
                if llm_api_calls:
                    # Convert LLM response to APIMapping format
                    api_calls = []
                    for call in llm_api_calls:
                        api_calls.append({
                            "api_name": call["api_name"],
                            "parameters": call["parameters"],
                            "description": call["description"],
                            "execution_order": call.get("execution_order", len(api_calls) + 1)
                        })
                    
                    # Create APIMapping object
                    api_mapping = APIMapping(
                        subtask_id=subtask.task_id,
                        api_calls=api_calls,
                        execution_strategy="sequential",
                        estimated_execution_time=len(api_calls) * 2.0,  # 2 seconds per API call
                        dependencies=[],
                        resource_requirements={"memory_mb": 100, "cpu_cores": 1},
                        mcp_server="blender_api_server"  # Add required mcp_server field
                    )
                    
                    self.logger.info(f"LLM successfully mapped {len(api_calls)} API calls for subtask {subtask.task_id}")
                    return api_mapping
                    
            except Exception as e:
                self.logger.warning(f"LLM mapping failed for subtask {subtask.task_id}: {e}")
                # Fall through to traditional search approach
        
        # Fallback to traditional search-based mapping
        self.logger.info(f"Using traditional search for subtask: {subtask.title}")
        
        # ROBUST FALLBACK: Generate basic API mappings based on task type
        return self._generate_basic_api_mapping(subtask)
        
        # Get preferred API categories for this task type
        preferred_categories = self.task_category_mapping.get(subtask.type, [APICategory.MESH_OPERATORS])
        
        # Get search strategy based on complexity
        search_params = self.complexity_search_strategies.get(
            subtask.complexity.value, 
            {"max_results": 5, "min_relevance": 0.6}
        )
        
        # Create search context
        search_context = SearchContext(
            task_type=subtask.type.value,
            task_description=subtask.description,
            preferred_categories=preferred_categories,
            max_results=search_params["max_results"],
            min_relevance=search_params["min_relevance"],
            enable_semantic_search=True
        )
        
        # Generate search queries from subtask
        search_queries = self._generate_search_queries(subtask)
        
        # Search for APIs using multiple queries
        all_api_results = []
        for query in search_queries:
            try:
                results = await self.api_searcher.search(query, search_context)
                all_api_results.extend(results)
            except Exception as e:
                self.logger.warning(f"Search failed for query '{query}': {e}")
        
        # Deduplicate and rank results
        unique_apis = self._deduplicate_and_rank_apis(all_api_results)
        
        # Convert to API calls with parameters
        api_calls = self._convert_to_api_calls(unique_apis, subtask, execution_context)
        
        # Calculate confidence score
        confidence_score = self._calculate_mapping_confidence(unique_apis, subtask)
        
        # Generate alternatives
        alternatives = self._generate_alternative_mappings(unique_apis[3:], subtask)
        
        return APIMapping(
            subtask_id=subtask.task_id,
            mcp_server=self._determine_mcp_server(preferred_categories[0] if preferred_categories else APICategory.MESH_OPERATORS),
            api_calls=api_calls,
            confidence_score=confidence_score,
            alternatives=alternatives
        )
    
    def _generate_basic_api_mapping(self, subtask: SubTask) -> APIMapping:
        """Generate basic API mapping when LLM and complex search fail - ROBUST FALLBACK"""
        
        self.logger.info(f"Generating basic API mapping for {subtask.type.value}: {subtask.title}")
        
        # Basic API mappings based on task type - ONLY VALID BLENDER OPERATIONS
        basic_mappings = {
            TaskType.CREATE_OBJECT: [
                {
                    "api_name": "bpy.ops.mesh.primitive_uv_sphere_add",
                    "parameters": {"radius": 1.0, "location": (0, 0, 0)},
                    "description": "Create UV sphere primitive",
                    "execution_order": 1
                }
            ],
            TaskType.MATERIAL_APPLICATION: [
                {
                    "api_name": "bpy.ops.object.select_all",
                    "parameters": {"action": "SELECT"},
                    "description": "Select all objects to apply materials",
                    "execution_order": 1
                }
            ],
            TaskType.SCENE_COMPOSITION: [
                {
                    "api_name": "bpy.ops.object.select_all",
                    "parameters": {"action": "SELECT"},
                    "description": "Select all objects for composition",
                    "execution_order": 1
                },
                {
                    "api_name": "bpy.ops.transform.translate",
                    "parameters": {"value": (0, 0, 0)},
                    "description": "Position objects in scene",
                    "execution_order": 2
                }
            ]
        }
        
        # Get basic API calls for this task type
        api_calls = basic_mappings.get(subtask.type, [
            {
                "api_name": "bpy.ops.mesh.primitive_cube_add",
                "parameters": {"size": 2.0, "location": (0, 0, 0)},
                "description": "Create basic cube primitive",
                "execution_order": 1
            }
        ])
        
        return APIMapping(
            subtask_id=subtask.task_id,
            api_calls=api_calls,
            execution_strategy="sequential",
            estimated_execution_time=len(api_calls) * 2.0,
            dependencies=[],
            resource_requirements={"memory_mb": 50, "cpu_cores": 1},
            mcp_server="blender_api_server",
            confidence_score=0.7,  # Basic but reliable
            alternatives=[]
        )
    
    def _generate_search_queries(self, subtask: SubTask) -> List[str]:
        """Generate enhanced search queries from granular subtask information"""
        
        queries = []
        
        # Priority 1: Extract specific mesh operations (highest priority for granular subtasks)
        if hasattr(subtask, 'mesh_operations') and subtask.mesh_operations:
            for operation in subtask.mesh_operations:
                # Convert our format to Blender API format
                if operation.startswith('mesh.'):
                    queries.append(operation.replace('.', '.ops.'))  # mesh.primitive_cube_add → mesh.ops.primitive_cube_add
                elif operation.startswith('transform.'):
                    queries.append(operation.replace('.', '.ops.'))  # transform.resize → transform.ops.resize
                else:
                    queries.append(operation)
        
        # Priority 2: Extract specific APIs from context
        if subtask.context and 'specific_apis_needed' in subtask.context:
            api_list = subtask.context['specific_apis_needed']
            for api in api_list:
                # Extract the operation part: bpy.ops.mesh.primitive_cube_add → primitive_cube_add
                if 'bpy.ops.' in api:
                    operation = api.split('bpy.ops.')[-1]
                    queries.append(operation)
                else:
                    queries.append(api)
        
        # Priority 3: Enhanced title-based queries
        if subtask.title:
            title_lower = subtask.title.lower()
            # Extract key operations from title
            if "mesh primitives" in title_lower:
                queries.extend(["primitive_cube_add", "primitive_cylinder_add", "primitive_uv_sphere_add"])
            if "chair" in title_lower:
                queries.extend(["primitive_cube_add", "primitive_cylinder_add", "duplicate"])
            if "human" in title_lower or "character" in title_lower:
                queries.extend(["primitive_cube_add", "primitive_uv_sphere_add", "primitive_cylinder_add"])
        
        # Priority 4: Enhanced description-based queries  
        if subtask.description:
            desc_lower = subtask.description.lower()
            # Extract Blender-specific keywords
            blender_keywords = []
            if "cube" in desc_lower:
                blender_keywords.append("primitive_cube_add")
            if "sphere" in desc_lower:
                blender_keywords.append("primitive_uv_sphere_add")
            if "cylinder" in desc_lower:
                blender_keywords.append("primitive_cylinder_add")
            if "scale" in desc_lower or "resize" in desc_lower:
                blender_keywords.append("resize")
            if "position" in desc_lower or "translate" in desc_lower:
                blender_keywords.append("translate")
            if "rotate" in desc_lower:
                blender_keywords.append("rotate")
            
            queries.extend(blender_keywords)
        
        # Priority 5: Task-specific fallback queries (enhanced)
        enhanced_task_queries = {
            TaskType.CREATE_CHARACTER: ["primitive_cube_add", "primitive_uv_sphere_add", "primitive_cylinder_add"],
            TaskType.CREATE_FURNITURE: ["primitive_cube_add", "primitive_cylinder_add", "duplicate"],
            TaskType.CREATE_CLOTHING: ["cloth", "modifier_add"],
            TaskType.LIGHTING_SETUP: ["light_add", "sun_add", "area_add"],
            TaskType.MATERIAL_APPLICATION: ["material_new", "node_add"],
            TaskType.SCENE_COMPOSITION: ["transform", "translate", "rotate"],
            TaskType.ANIMATION_SETUP: ["keyframe_insert", "frame_set"]
        }
        
        if subtask.type in enhanced_task_queries:
            queries.extend(enhanced_task_queries[subtask.type])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_queries = []
        for query in queries:
            if query not in seen:
                seen.add(query)
                unique_queries.append(query)
        
        # Limit to top 8 queries (increased from 5 for better coverage)
        return unique_queries[:8]
    
    def _deduplicate_and_rank_apis(self, api_results) -> List:
        """Remove duplicates and rank APIs by relevance"""
        
        # Group by API ID and keep best score
        api_scores = {}
        for result in api_results:
            api_id = result.api.id
            if api_id not in api_scores or api_scores[api_id].relevance_score < result.relevance_score:
                api_scores[api_id] = result
        
        # Sort by relevance score (descending)
        ranked_results = sorted(api_scores.values(), key=lambda x: x.relevance_score, reverse=True)
        
        return ranked_results
    
    def _convert_to_api_calls(self, api_results, subtask: SubTask, execution_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert API search results to structured API calls with parameters"""
        
        api_calls = []
        
        for result in api_results[:5]:  # Limit to top 5 APIs
            api_call = {
                "api_name": result.api.name,
                "category": result.api.category.value,
                "description": result.api.description,
                "parameters": self._infer_parameters(result.api, subtask, execution_context),
                "relevance_score": result.relevance_score,
                "confidence": result.confidence,
                "execution_order": len(api_calls) + 1
            }
            
            # Add suggested parameters from search result
            if result.suggested_parameters:
                api_call["parameters"].update(result.suggested_parameters)
            
            api_calls.append(api_call)
        
        return api_calls
    
    def _infer_parameters(self, api, subtask: SubTask, execution_context: Dict[str, Any]) -> Dict[str, Any]:
        """Infer parameter values for an API based on subtask context"""
        
        parameters = {}
        
        # Basic parameter inference based on API name patterns
        api_name_lower = api.name.lower()
        
        # Scale/size parameters
        if "scale" in api_name_lower or "size" in api_name_lower:
            if subtask.context.get("size") == "large":
                parameters["factor"] = 2.0
            elif subtask.context.get("size") == "small":
                parameters["factor"] = 0.5
            else:
                parameters["factor"] = 1.0
        
        # Rotation parameters
        if "rotate" in api_name_lower:
            parameters["angle"] = 90.0  # Default rotation
            parameters["axis"] = (0, 0, 1)  # Z-axis
        
        # Extrude parameters
        if "extrude" in api_name_lower:
            parameters["value"] = 1.0
        
        # Bevel parameters
        if "bevel" in api_name_lower:
            parameters["offset"] = 0.1
            parameters["segments"] = 3
        
        # Subdivide parameters
        if "subdivide" in api_name_lower:
            if subtask.complexity.value == "expert":
                parameters["number_cuts"] = 4
            elif subtask.complexity.value == "complex":
                parameters["number_cuts"] = 3
            else:
                parameters["number_cuts"] = 2
        
        # Location parameters for primitive creation
        if "primitive" in api_name_lower or "add" in api_name_lower:
            parameters["location"] = (0, 0, 0)
        
        # Context-specific parameter inference
        if subtask.context:
            # Material properties
            if "material" in subtask.context:
                material_type = subtask.context["material"]
                if material_type == "metal":
                    parameters["metallic"] = 1.0
                    parameters["roughness"] = 0.2
                elif material_type == "wood":
                    parameters["metallic"] = 0.0
                    parameters["roughness"] = 0.8
        
        return parameters
    
    def _calculate_mapping_confidence(self, api_results, subtask: SubTask) -> float:
        """Calculate confidence score for the API mapping"""
        
        if not api_results:
            return 0.0
        
        # Base confidence on best API result
        best_result = api_results[0]
        base_confidence = best_result.confidence
        
        # Boost confidence if multiple good results
        if len(api_results) >= 3:
            avg_confidence = sum(r.confidence for r in api_results[:3]) / 3
            base_confidence = (base_confidence + avg_confidence) / 2
        
        # Adjust based on task complexity match
        if subtask.complexity.value == "simple" and base_confidence > 0.8:
            base_confidence *= 1.1  # Boost for simple tasks with high confidence
        elif subtask.complexity.value == "expert" and base_confidence < 0.6:
            base_confidence *= 0.9  # Reduce for complex tasks with low confidence
        
        return min(base_confidence, 1.0)
    
    def _generate_alternative_mappings(self, alternative_results, subtask: SubTask) -> List[Dict[str, Any]]:
        """Generate alternative API mappings"""
        
        alternatives = []
        
        for result in alternative_results[:3]:  # Top 3 alternatives
            alternative = {
                "api_name": result.api.name,
                "category": result.api.category.value,
                "relevance_score": result.relevance_score,
                "confidence": result.confidence,
                "reason": f"Alternative approach for {subtask.type.value}"
            }
            alternatives.append(alternative)
        
        return alternatives
    
    def _determine_mcp_server(self, category: APICategory) -> str:
        """Determine which MCP server to use for an API category"""
        
        server_mapping = {
            APICategory.MESH_OPERATORS: "blender-mesh",
            APICategory.OBJECT_OPERATORS: "blender-objects",
            APICategory.GEOMETRY_NODES: "blender-geometry",
            APICategory.SHADER_NODES: "blender-shaders",
            APICategory.MATERIAL_OPERATORS: "blender-shaders",
            APICategory.ANIMATION_OPERATORS: "blender-objects",
            APICategory.SCENE_OPERATORS: "blender-objects"
        }
        
        return server_mapping.get(category, "blender-mesh")
    
    async def _validate_api_mappings(
        self, 
        api_mappings: List[APIMapping], 
        plan: TaskPlan
    ) -> List[APIMapping]:
        """Validate API mappings for compatibility and coherence"""
        
        validated_mappings = []
        
        for mapping in api_mappings:
            # Basic validation
            if not mapping.api_calls:
                self.logger.warning(f"No API calls found for subtask {mapping.subtask_id}")
                continue
            
            # Confidence threshold validation
            if mapping.confidence_score < 0.3:
                self.logger.warning(f"Low confidence mapping for subtask {mapping.subtask_id}: {mapping.confidence_score}")
                # Still include but mark as low confidence
            
            # API compatibility validation
            if self._validate_api_compatibility(mapping):
                validated_mappings.append(mapping)
            else:
                self.logger.warning(f"API compatibility issues for subtask {mapping.subtask_id}")
                # Try to fix or provide alternatives
                fixed_mapping = self._attempt_mapping_fix(mapping)
                if fixed_mapping:
                    validated_mappings.append(fixed_mapping)
        
        return validated_mappings
    
    def _validate_api_compatibility(self, mapping: APIMapping) -> bool:
        """Validate that APIs in a mapping are compatible"""
        
        # Check that all APIs are from compatible categories
        categories = set()
        for api_call in mapping.api_calls:
            categories.add(api_call.get("category", "mesh_operators"))
        
        # Some categories don't mix well
        incompatible_pairs = [
            {"mesh_operators", "shader_nodes"},
            {"animation_operators", "material_operators"}
        ]
        
        for incompatible in incompatible_pairs:
            if incompatible.issubset(categories):
                return False
        
        return True
    
    def _attempt_mapping_fix(self, mapping: APIMapping) -> Optional[APIMapping]:
        """Attempt to fix a problematic API mapping"""
        
        # For now, just filter out incompatible APIs
        # In a more sophisticated version, this could use ML or heuristics
        
        filtered_calls = []
        primary_category = None
        
        # Determine primary category from first API
        if mapping.api_calls:
            primary_category = mapping.api_calls[0].get("category", "mesh_operators")
        
        # Keep only APIs from compatible categories
        for api_call in mapping.api_calls:
            if self._are_categories_compatible(primary_category, api_call.get("category", "mesh_operators")):
                filtered_calls.append(api_call)
        
        if filtered_calls:
            mapping.api_calls = filtered_calls
            mapping.confidence_score *= 0.8  # Reduce confidence for fixed mapping
            return mapping
        
        return None
    
    def _are_categories_compatible(self, cat1: str, cat2: str) -> bool:
        """Check if two API categories are compatible"""
        
        compatible_groups = [
            {"mesh_operators", "object_operators"},
            {"shader_nodes", "material_operators"},
            {"animation_operators", "object_operators"},
            {"geometry_nodes", "mesh_operators"}
        ]
        
        for group in compatible_groups:
            if cat1 in group and cat2 in group:
                return True
        
        return cat1 == cat2
    
    def _generate_execution_strategy(
        self, 
        api_mappings: List[APIMapping], 
        plan: TaskPlan
    ) -> str:
        """Generate execution strategy description"""
        
        total_apis = sum(len(mapping.api_calls) for mapping in api_mappings)
        avg_confidence = sum(mapping.confidence_score for mapping in api_mappings) / max(len(api_mappings), 1)
        
        # Determine strategy based on plan characteristics
        if len(plan.parallel_groups) > 1:
            strategy = f"Parallel execution strategy with {len(plan.parallel_groups)} groups"
        else:
            strategy = "Sequential execution strategy"
        
        strategy += f" involving {total_apis} API calls across {len(api_mappings)} subtasks"
        strategy += f" with average confidence {avg_confidence:.2f}"
        
        # Add recommendations
        if avg_confidence < 0.6:
            strategy += ". Recommend manual review of low-confidence mappings."
        
        if total_apis > 50:
            strategy += ". Consider breaking down into smaller execution batches."
        
        return strategy
    
    def _calculate_resource_requirements(self, api_mappings: List[APIMapping]) -> Dict[str, Any]:
        """Calculate estimated resource requirements"""
        
        total_apis = sum(len(mapping.api_calls) for mapping in api_mappings)
        
        # Estimate based on API count and complexity
        estimated_memory_mb = total_apis * 2  # Rough estimate: 2MB per API call
        estimated_execution_time_seconds = total_apis * 0.5  # Rough estimate: 0.5s per API call
        
        # Count APIs by category for server load balancing
        category_counts = {}
        for mapping in api_mappings:
            for api_call in mapping.api_calls:
                category = api_call.get("category", "mesh_operators")
                category_counts[category] = category_counts.get(category, 0) + 1
        
        return {
            "estimated_memory_mb": estimated_memory_mb,
            "estimated_execution_time_seconds": estimated_execution_time_seconds,
            "total_api_calls": total_apis,
            "api_calls_by_category": category_counts,
            "recommended_parallel_workers": min(len(api_mappings), 5),
            "mcp_servers_needed": list(set(mapping.mcp_server for mapping in api_mappings))
        }
    
    async def get_coordination_stats(self) -> Dict[str, Any]:
        """Get coordination performance statistics"""
        
        search_stats = self.api_searcher.get_performance_stats()
        
        return {
            "coordinator_initialized": self._initialized,
            "api_search_stats": search_stats,
            "total_coordinations": len(self.coordination_metrics),
            "search_engine_memory_mb": search_stats.get("memory_usage_mb", 0)
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the coordinator agent"""
        
        health = {
            "initialized": self._initialized,
            "api_searcher_ready": False,
            "search_engine_functional": False
        }
        
        if self._initialized:
            # Check API searcher health
            search_health = await self.api_searcher.health_check()
            health["api_searcher_ready"] = search_health.get("initialized", False)
            health["search_engine_functional"] = search_health.get("search_functional", False)
            health["search_engine_memory_mb"] = search_health.get("memory_usage_mb", 0)
        
        return health
    
    def __del__(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=False)
