"""
Blender Mesh Operations MCP Server
Specialized server for mesh modeling APIs (234 APIs)
"""

import asyncio
from typing import List, Dict, Any
from .base_server import BlenderMCPServer
from .models import (
    DiscoverMeshAPIsInput, DiscoverAPIsOutput, MeshOperationType,
    APIInfo, APIParameter
)

class BlenderMeshServer(BlenderMCPServer):
    """
    MCP Server specialized for Blender mesh operations
    Handles 234+ mesh-related APIs including modeling, subdivision, deformation, etc.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(
            server_name="blender-mesh",
            category="mesh_operators",
            config=config
        )
        
        # Mesh-specific operation mappings
        self.operation_keywords = {
            MeshOperationType.MODELING: [
                'extrude', 'inset', 'bevel', 'loop_cut', 'knife', 'bisect',
                'bridge', 'fill', 'grid_fill', 'beautify_fill'
            ],
            MeshOperationType.SUBDIVISION: [
                'subdivide', 'unsubdivide', 'smooth', 'catmull_clark',
                'edge_split', 'triangulate', 'quads_convert_to_tris'
            ],
            MeshOperationType.DEFORMATION: [
                'smooth', 'relax', 'push_pull', 'shrink_fatten',
                'noise', 'randomize', 'sort_elements'
            ],
            MeshOperationType.CLEANUP: [
                'remove_doubles', 'merge', 'dissolve', 'delete',
                'separate', 'split', 'cleanup'
            ],
            MeshOperationType.GENERATION: [
                'primitive', 'add', 'create', 'duplicate',
                'spin', 'screw', 'solidify'
            ],
            MeshOperationType.ANALYSIS: [
                'select', 'shortest_path', 'similar', 'linked',
                'face_select', 'edge_select', 'vertex_select'
            ]
        }
    
    async def _register_category_tools(self):
        """Register mesh-specific MCP tools"""
        
        @self.mcp.tool()
        def discover_mesh_apis(input: DiscoverMeshAPIsInput) -> DiscoverAPIsOutput:
            """Discover mesh-specific Blender APIs with advanced filtering"""
            return asyncio.run(self._discover_mesh_apis_impl(input))
        
        @self.mcp.tool()
        def get_modeling_workflow(intent: str) -> Dict[str, Any]:
            """Get a complete modeling workflow for a specific intent"""
            return asyncio.run(self._get_modeling_workflow_impl(intent))
        
        @self.mcp.tool()
        def suggest_mesh_operations(current_selection: str, goal: str) -> Dict[str, Any]:
            """Suggest next mesh operations based on current selection and goal"""
            return asyncio.run(self._suggest_mesh_operations_impl(current_selection, goal))
        
        @self.mcp.tool()
        def validate_mesh_workflow(operations: List[str]) -> Dict[str, Any]:
            """Validate a sequence of mesh operations for potential issues"""
            return asyncio.run(self._validate_mesh_workflow_impl(operations))
    
    async def _discover_mesh_apis_impl(self, input: DiscoverMeshAPIsInput) -> DiscoverAPIsOutput:
        """Enhanced mesh API discovery with operation type filtering"""
        try:
            # Build enhanced search query
            enhanced_query = input.intent
            
            # Add operation type keywords if specified
            if input.operation_type:
                operation_keywords = self.operation_keywords.get(input.operation_type, [])
                enhanced_query += " " + " ".join(operation_keywords[:3])
            
            # Build filters
            filters = {'category': ['mesh_operators']}
            if input.category_filter:
                filters['category'].extend(input.category_filter)
            
            # Add mesh-specific filters
            if input.affects_geometry is not None:
                # This would require metadata in the API registry
                # For now, we'll use tag-based filtering
                if input.affects_geometry:
                    enhanced_query += " geometry modify transform"
                else:
                    enhanced_query += " select query analyze"
            
            if input.requires_selection is not None:
                if input.requires_selection:
                    enhanced_query += " selected elements"
                else:
                    enhanced_query += " all mesh global"
            
            # Perform enhanced search
            search_results = await self.vector_manager.hybrid_search(
                query=enhanced_query,
                top_k=input.top_k,
                filters=filters
            )
            
            # Post-process results for mesh-specific ranking
            ranked_results = self._rank_mesh_results(search_results, input)
            
            # Convert to APIInfo objects
            apis = []
            for result in ranked_results:
                parameters = []
                for param in result.parameters:
                    if isinstance(param, dict):
                        api_param = APIParameter(
                            name=param.get('name', ''),
                            type=param.get('type', 'unknown'),
                            default=param.get('default'),
                            description=param.get('description', ''),
                            optional=param.get('optional', False),
                            enum_values=param.get('enum_values')
                        )
                        parameters.append(api_param)
                
                api_info = APIInfo(
                    id=result.id,
                    full_name=result.api_name,
                    description=result.content,
                    category=result.category,
                    module=result.metadata.get('module', ''),
                    signature=result.metadata.get('signature', ''),
                    parameters=parameters,
                    tags=result.metadata.get('tags', []),
                    examples=result.metadata.get('examples', []) if input.include_examples else [],
                    score=result.score
                )
                apis.append(api_info)
            
            # Generate mesh-specific suggestions
            suggestions = self._generate_mesh_suggestions(input.intent, input.operation_type, apis)
            
            return DiscoverAPIsOutput(
                apis=apis,
                total_found=len(apis),
                search_time_ms=0,  # Would be calculated in real implementation
                backend_used=self.vector_manager.active_backend.value,
                suggestions=suggestions
            )
            
        except Exception as e:
            print(f"❌ Mesh API discovery failed: {e}")
            return DiscoverAPIsOutput(
                apis=[],
                total_found=0,
                search_time_ms=0,
                backend_used="error",
                suggestions=[f"Error: {str(e)}"]
            )
    
    def _rank_mesh_results(self, results, input: DiscoverMeshAPIsInput):
        """Apply mesh-specific ranking to search results"""
        if not input.operation_type:
            return results
        
        operation_keywords = self.operation_keywords.get(input.operation_type, [])
        
        # Boost results that match operation type keywords
        for result in results:
            boost_score = 0
            api_name_lower = result.api_name.lower()
            description_lower = result.content.lower()
            tags_lower = [tag.lower() for tag in result.metadata.get('tags', [])]
            
            for keyword in operation_keywords:
                if keyword in api_name_lower:
                    boost_score += 0.3
                if keyword in description_lower:
                    boost_score += 0.2
                if keyword in ' '.join(tags_lower):
                    boost_score += 0.1
            
            result.score = min(1.0, result.score + boost_score)
        
        # Re-sort by updated scores
        results.sort(key=lambda x: x.score, reverse=True)
        return results
    
    async def _get_modeling_workflow_impl(self, intent: str) -> Dict[str, Any]:
        """Generate a complete modeling workflow"""
        try:
            # This would use LLM + API knowledge to create workflows
            # For now, provide a simplified implementation
            
            workflows = {
                'create_character': [
                    'bpy.ops.mesh.primitive_cube_add',
                    'bpy.ops.mesh.subdivide',
                    'bpy.ops.mesh.loopcut_slide',
                    'bpy.ops.mesh.extrude_region_move',
                    'bpy.ops.mesh.bevel'
                ],
                'create_building': [
                    'bpy.ops.mesh.primitive_cube_add',
                    'bpy.ops.mesh.extrude_region_move',
                    'bpy.ops.mesh.inset_faces',
                    'bpy.ops.mesh.subdivide',
                    'bpy.ops.mesh.bevel'
                ],
                'organic_modeling': [
                    'bpy.ops.mesh.primitive_uv_sphere_add',
                    'bpy.ops.mesh.subdivide',
                    'bpy.ops.mesh.vertices_smooth',
                    'bpy.ops.mesh.noise',
                    'bpy.ops.mesh.smooth'
                ]
            }
            
            # Find best matching workflow
            intent_lower = intent.lower()
            best_workflow = []
            best_match = ""
            
            for workflow_name, operations in workflows.items():
                if any(word in intent_lower for word in workflow_name.split('_')):
                    best_workflow = operations
                    best_match = workflow_name
                    break
            
            if not best_workflow:
                # Generate generic workflow
                search_results = await self.vector_manager.hybrid_search(intent, top_k=5)
                best_workflow = [result.api_name for result in search_results]
                best_match = "custom_workflow"
            
            return {
                'workflow_name': best_match,
                'operations': best_workflow,
                'description': f"Modeling workflow for: {intent}",
                'estimated_time': len(best_workflow) * 2,  # minutes
                'difficulty': 'intermediate',
                'prerequisites': ['Basic mesh selection', 'Transform tools knowledge']
            }
            
        except Exception as e:
            return {
                'error': f"Failed to generate workflow: {str(e)}",
                'workflow_name': 'error',
                'operations': []
            }
    
    async def _suggest_mesh_operations_impl(self, current_selection: str, goal: str) -> Dict[str, Any]:
        """Suggest next operations based on current state"""
        try:
            # Build context-aware query
            query = f"{current_selection} {goal} next operation"
            
            results = await self.vector_manager.hybrid_search(query, top_k=3)
            
            suggestions = []
            for result in results:
                suggestion = {
                    'operation': result.api_name,
                    'description': result.content,
                    'confidence': result.score,
                    'parameters': self._suggest_parameters(result, current_selection, goal)
                }
                suggestions.append(suggestion)
            
            return {
                'suggestions': suggestions,
                'context': f"Current: {current_selection}, Goal: {goal}",
                'reasoning': "Based on common modeling patterns and API compatibility"
            }
            
        except Exception as e:
            return {
                'error': f"Failed to suggest operations: {str(e)}",
                'suggestions': []
            }
    
    async def _validate_mesh_workflow_impl(self, operations: List[str]) -> Dict[str, Any]:
        """Validate a sequence of mesh operations"""
        try:
            issues = []
            warnings = []
            suggestions = []
            
            # Check for common issues
            for i, operation in enumerate(operations):
                # Check if operation exists
                if operation not in self.api_registry:
                    issues.append(f"Unknown operation: {operation}")
                    continue
                
                # Check for destructive operations without backup
                if 'delete' in operation.lower() or 'dissolve' in operation.lower():
                    if i == 0 or 'duplicate' not in operations[i-1].lower():
                        warnings.append(f"Destructive operation '{operation}' without backup")
                
                # Check for selection requirements
                if 'selected' in self.api_registry[operation].get('description', '').lower():
                    if i == 0:
                        suggestions.append(f"Consider adding selection operation before '{operation}'")
            
            # Check workflow coherence
            if len(operations) > 1:
                # Check for logical flow
                modeling_ops = sum(1 for op in operations if any(kw in op.lower() for kw in ['extrude', 'bevel', 'inset']))
                if modeling_ops == 0:
                    warnings.append("No major modeling operations detected")
            
            validation_score = max(0, 100 - len(issues) * 30 - len(warnings) * 10)
            
            return {
                'valid': len(issues) == 0,
                'score': validation_score,
                'issues': issues,
                'warnings': warnings,
                'suggestions': suggestions,
                'estimated_complexity': self._estimate_workflow_complexity(operations)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f"Validation failed: {str(e)}",
                'issues': [str(e)]
            }
    
    def _suggest_parameters(self, result, current_selection: str, goal: str) -> Dict[str, Any]:
        """Suggest parameters for an operation based on context"""
        # This would be more sophisticated in a full implementation
        suggested_params = {}
        
        # Get parameter definitions
        api_info = self.api_registry.get(result.api_name, {})
        parameters = api_info.get('parameters', [])
        
        for param in parameters:
            param_name = param.get('name', '')
            param_type = param.get('type', '')
            
            # Suggest common values based on context
            if param_name == 'offset' and 'bevel' in result.api_name:
                suggested_params[param_name] = 0.1
            elif param_name == 'number_cuts' and 'loop' in result.api_name:
                suggested_params[param_name] = 2
            elif param_type == 'bool' and 'use_' in param_name:
                suggested_params[param_name] = True
        
        return suggested_params
    
    def _estimate_workflow_complexity(self, operations: List[str]) -> str:
        """Estimate workflow complexity"""
        if len(operations) <= 3:
            return "beginner"
        elif len(operations) <= 7:
            return "intermediate"
        else:
            return "advanced"
    
    def _generate_mesh_suggestions(self, query: str, operation_type, results: List[APIInfo]) -> List[str]:
        """Generate mesh-specific search suggestions"""
        suggestions = []
        
        if not results:
            suggestions.extend([
                "Try 'extrude', 'bevel', or 'subdivide' for basic modeling",
                "Use 'select' operations to specify target elements",
                "Consider 'primitive' operations to start with basic shapes"
            ])
        
        # Operation type specific suggestions
        if operation_type == MeshOperationType.MODELING:
            suggestions.append("Try combining with 'loop cut' or 'edge split'")
        elif operation_type == MeshOperationType.CLEANUP:
            suggestions.append("Consider 'remove doubles' or 'merge' operations")
        
        return suggestions[:3]
    
    def _get_category_suggestions(self, query: str) -> List[str]:
        """Get mesh-specific search suggestions"""
        return [
            "Try mesh modeling terms like 'extrude', 'bevel', 'subdivide'",
            "Use selection terms like 'faces', 'edges', 'vertices'",
            "Consider workflow terms like 'modeling', 'cleanup', 'deformation'"
        ]

# Factory function for easy server creation
def create_mesh_server(config: Dict[str, Any] = None) -> BlenderMeshServer:
    """Create a configured mesh MCP server"""
    if config is None:
        config = {
            'vector_store': {
                'faiss': {'index_path': 'mesh_faiss_index'},
                'qdrant': {'collection_name': 'mesh_apis'}
            }
        }
    
    return BlenderMeshServer(config)
