"""
Base MCP Server for Blender APIs
Provides common functionality for all specialized Blender API servers
"""

import asyncio
import time
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from abc import ABC, abstractmethod

try:
    from mcp.server.fastmcp import FastMCP
    from mcp.types import TextContent
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("⚠️ FastMCP not available. Install with: uv add fastmcp")

from vector_store import HybridVectorManager
from .models import (
    DiscoverAPIsInput, DiscoverAPIsOutput, APIInfo, APIParameter,
    ValidateParametersInput, ValidateParametersOutput, ParameterValidationResult,
    GenerateCodeInput, GenerateCodeOutput,
    ExecuteCodeInput, ExecuteCodeOutput, ExecutionResult,
    HealthCheckOutput, APIError, ErrorResponse
)

class BlenderMCPServer(ABC):
    """
    Abstract base class for Blender API MCP servers
    Provides common functionality like vector search, parameter validation, etc.
    """
    
    def __init__(self, server_name: str, category: str, config: Dict[str, Any]):
        if not MCP_AVAILABLE:
            raise ImportError("FastMCP not available. Install with: uv add fastmcp")
        
        self.server_name = server_name
        self.category = category
        self.config = config
        
        # Initialize FastMCP server
        self.mcp = FastMCP(server_name)
        
        # Initialize vector store manager
        vector_config = config.get('vector_store', {})
        self.vector_manager = HybridVectorManager(vector_config)
        
        # API registry cache
        self.api_registry = {}
        self.last_registry_update = 0
        
        # Performance metrics
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'avg_response_time': 0.0,
            'last_request_time': 0
        }
        
        # Register common tools
        self._register_common_tools()
    
    def _register_common_tools(self):
        """Register common MCP tools available to all servers"""
        
        @self.mcp.tool()
        def discover_apis(input: DiscoverAPIsInput) -> DiscoverAPIsOutput:
            """Discover relevant Blender APIs based on natural language intent"""
            return asyncio.run(self._discover_apis_impl(input))
        
        @self.mcp.tool()
        def validate_parameters(input: ValidateParametersInput) -> ValidateParametersOutput:
            """Validate parameters for a specific Blender API"""
            return asyncio.run(self._validate_parameters_impl(input))
        
        @self.mcp.tool()
        def generate_code(input: GenerateCodeInput) -> GenerateCodeOutput:
            """Generate Python code for Blender API calls"""
            return asyncio.run(self._generate_code_impl(input))
        
        @self.mcp.tool()
        def execute_code(input: ExecuteCodeInput) -> ExecuteCodeOutput:
            """Execute Python code in headless Blender"""
            return asyncio.run(self._execute_code_impl(input))
        
        @self.mcp.tool()
        def health_check() -> HealthCheckOutput:
            """Check server health and status"""
            return asyncio.run(self._health_check_impl())
    
    async def initialize(self) -> bool:
        """Initialize the MCP server"""
        try:
            # Initialize vector store
            vector_success = await self.vector_manager.initialize()
            if not vector_success:
                print(f"❌ Failed to initialize vector store for {self.server_name}")
                return False
            
            # Load API registry for this category
            await self._load_api_registry()
            
            # Register category-specific tools
            await self._register_category_tools()
            
            print(f"✅ {self.server_name} MCP server initialized successfully")
            return True
            
        except Exception as e:
            print(f"❌ Failed to initialize {self.server_name}: {e}")
            return False
    
    async def _load_api_registry(self):
        """Load and filter API registry for this server's category"""
        try:
            registry_path = Path("blender_api_registry.json")
            if not registry_path.exists():
                print(f"⚠️ API registry not found for {self.server_name}")
                return
            
            # Load full registry
            with open(registry_path, 'r', encoding='utf-8') as f:
                try:
                    full_registry = json.load(f)
                except UnicodeDecodeError:
                    # Handle encoding issues
                    f.seek(0)
                    content = f.read().encode('utf-8').decode('utf-8', errors='ignore')
                    full_registry = json.loads(content)
            
            # Filter APIs for this category
            category_apis = []
            
            if isinstance(full_registry, dict):
                api_data = full_registry.get('apis', full_registry)
                
                for api_id, api_info in api_data.items():
                    if isinstance(api_info, dict):
                        api_category = api_info.get('category', '').lower()
                        if self.category.lower() in api_category or api_category in self.category.lower():
                            # Convert to our format
                            doc = {
                                'id': api_id,
                                'full_name': api_info.get('full_name', api_id),
                                'description': api_info.get('description', ''),
                                'category': api_info.get('category', 'unknown'),
                                'module': api_info.get('module', ''),
                                'signature': api_info.get('signature', ''),
                                'parameters': api_info.get('parameters', []),
                                'tags': api_info.get('tags', []),
                                'examples': api_info.get('examples', [])
                            }
                            category_apis.append(doc)
                            self.api_registry[api_id] = api_info
            
            # Add to vector store
            if category_apis:
                await self.vector_manager.add_documents(category_apis)
                print(f"✅ Loaded {len(category_apis)} APIs for {self.server_name}")
            else:
                print(f"⚠️ No APIs found for category '{self.category}' in {self.server_name}")
            
            self.last_registry_update = time.time()
            
        except Exception as e:
            print(f"❌ Failed to load API registry for {self.server_name}: {e}")
    
    async def _discover_apis_impl(self, input: DiscoverAPIsInput) -> DiscoverAPIsOutput:
        """Implementation of API discovery"""
        start_time = time.time()
        
        try:
            # Build search filters
            filters = {}
            if input.category_filter:
                filters['category'] = input.category_filter
            
            # Perform hybrid search
            search_results = await self.vector_manager.hybrid_search(
                query=input.intent,
                top_k=input.top_k,
                filters=filters
            )
            
            # Convert to APIInfo objects
            apis = []
            for result in search_results:
                # Convert parameters
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
            
            # Generate suggestions
            suggestions = self._generate_search_suggestions(input.intent, apis)
            
            search_time = (time.time() - start_time) * 1000
            
            # Update metrics
            self._update_metrics(search_time, True)
            
            return DiscoverAPIsOutput(
                apis=apis,
                total_found=len(apis),
                search_time_ms=search_time,
                backend_used=self.vector_manager.active_backend.value,
                suggestions=suggestions
            )
            
        except Exception as e:
            self._update_metrics((time.time() - start_time) * 1000, False)
            print(f"❌ API discovery failed: {e}")
            return DiscoverAPIsOutput(
                apis=[],
                total_found=0,
                search_time_ms=(time.time() - start_time) * 1000,
                backend_used="error",
                suggestions=[f"Error occurred: {str(e)}"]
            )
    
    async def _validate_parameters_impl(self, input: ValidateParametersInput) -> ValidateParametersOutput:
        """Implementation of parameter validation"""
        try:
            # Get API info
            api_info = self.api_registry.get(input.api_name)
            if not api_info:
                return ValidateParametersOutput(
                    api_name=input.api_name,
                    valid=False,
                    parameter_results=[],
                    corrected_parameters={},
                    validation_errors=[f"API '{input.api_name}' not found in registry"]
                )
            
            # Validate each parameter
            parameter_results = []
            corrected_parameters = {}
            validation_errors = []
            
            api_params = {p.get('name'): p for p in api_info.get('parameters', [])}
            
            for param_name, param_value in input.parameters.items():
                if param_name not in api_params:
                    result = ParameterValidationResult(
                        name=param_name,
                        valid=False,
                        error_message=f"Parameter '{param_name}' not found in API definition",
                        type_info="unknown"
                    )
                    validation_errors.append(result.error_message)
                else:
                    param_def = api_params[param_name]
                    result = self._validate_single_parameter(param_name, param_value, param_def)
                    
                    if result.valid:
                        corrected_parameters[param_name] = param_value
                    elif result.suggested_value is not None:
                        corrected_parameters[param_name] = result.suggested_value
                    else:
                        validation_errors.append(result.error_message)
                
                parameter_results.append(result)
            
            # Check for required parameters
            for param_name, param_def in api_params.items():
                if not param_def.get('optional', True) and param_name not in input.parameters:
                    error_msg = f"Required parameter '{param_name}' is missing"
                    validation_errors.append(error_msg)
                    parameter_results.append(ParameterValidationResult(
                        name=param_name,
                        valid=False,
                        error_message=error_msg,
                        type_info=param_def.get('type', 'unknown')
                    ))
            
            return ValidateParametersOutput(
                api_name=input.api_name,
                valid=len(validation_errors) == 0,
                parameter_results=parameter_results,
                corrected_parameters=corrected_parameters,
                validation_errors=validation_errors
            )
            
        except Exception as e:
            return ValidateParametersOutput(
                api_name=input.api_name,
                valid=False,
                parameter_results=[],
                corrected_parameters={},
                validation_errors=[f"Validation error: {str(e)}"]
            )
    
    def _validate_single_parameter(self, name: str, value: Any, param_def: Dict[str, Any]) -> ParameterValidationResult:
        """Validate a single parameter"""
        param_type = param_def.get('type', 'unknown').lower()
        
        try:
            # Type validation
            if param_type == 'float':
                float(value)
            elif param_type == 'int':
                int(value)
            elif param_type == 'bool':
                if not isinstance(value, bool):
                    # Try to convert string to bool
                    if isinstance(value, str):
                        if value.lower() in ['true', '1', 'yes']:
                            return ParameterValidationResult(
                                name=name,
                                valid=True,
                                suggested_value=True,
                                type_info=param_type
                            )
                        elif value.lower() in ['false', '0', 'no']:
                            return ParameterValidationResult(
                                name=name,
                                valid=True,
                                suggested_value=False,
                                type_info=param_type
                            )
            elif param_type == 'str':
                str(value)
            
            # Enum validation
            enum_values = param_def.get('enum_values')
            if enum_values and value not in enum_values:
                return ParameterValidationResult(
                    name=name,
                    valid=False,
                    error_message=f"Value '{value}' not in allowed values: {enum_values}",
                    suggested_value=enum_values[0] if enum_values else None,
                    type_info=param_type
                )
            
            return ParameterValidationResult(
                name=name,
                valid=True,
                type_info=param_type
            )
            
        except (ValueError, TypeError) as e:
            return ParameterValidationResult(
                name=name,
                valid=False,
                error_message=f"Type validation failed: {str(e)}",
                type_info=param_type
            )
    
    async def _generate_code_impl(self, input: GenerateCodeInput) -> GenerateCodeOutput:
        """Implementation of code generation"""
        try:
            # This is a simplified implementation
            # In a full system, this would use an LLM for intelligent code generation
            
            code_lines = []
            imports = set(['import bpy'])
            warnings = []
            
            if input.include_comments:
                code_lines.append("# Generated Blender Python code")
                code_lines.append("")
            
            if input.include_error_handling:
                code_lines.append("try:")
                indent = "    "
            else:
                indent = ""
            
            # Generate code for each API
            for api_name in input.apis:
                if api_name in input.parameters:
                    params = input.parameters[api_name]
                    param_str = ", ".join([f"{k}={repr(v)}" for k, v in params.items()])
                    code_lines.append(f"{indent}{api_name}({param_str})")
                else:
                    code_lines.append(f"{indent}{api_name}()")
                
                if input.include_comments:
                    api_info = self.api_registry.get(api_name)
                    if api_info:
                        code_lines.append(f"{indent}# {api_info.get('description', '')}")
            
            if input.include_error_handling:
                code_lines.extend([
                    "except Exception as e:",
                    "    print(f'Error executing Blender code: {e}')",
                    "    raise"
                ])
            
            code = "\n".join(code_lines)
            
            return GenerateCodeOutput(
                code=code,
                imports=list(imports),
                warnings=warnings,
                estimated_execution_time=len(input.apis) * 0.1  # Rough estimate
            )
            
        except Exception as e:
            return GenerateCodeOutput(
                code="# Code generation failed",
                imports=[],
                warnings=[f"Code generation error: {str(e)}"]
            )
    
    async def _execute_code_impl(self, input: ExecuteCodeInput) -> ExecuteCodeOutput:
        """Implementation of code execution (placeholder)"""
        # This would connect to headless Blender in a full implementation
        return ExecuteCodeOutput(
            result=ExecutionResult(
                success=False,
                output="Code execution not implemented yet",
                execution_time=0.0
            ),
            blender_version="N/A",
            warnings=["Code execution requires headless Blender integration"]
        )
    
    async def _health_check_impl(self) -> HealthCheckOutput:
        """Implementation of health check"""
        try:
            # Check vector store health
            vector_health = await self.vector_manager.health_check()
            vector_status = vector_health.get('status', 'unknown')
            
            # Determine overall status
            if vector_status == 'healthy':
                status = 'healthy'
            elif vector_status == 'degraded':
                status = 'degraded'
            else:
                status = 'unhealthy'
            
            return HealthCheckOutput(
                status=status,
                server_name=self.server_name,
                api_count=len(self.api_registry),
                vector_store_status=vector_status,
                blender_connection_status="not_implemented",
                last_updated=self.last_registry_update,
                performance_metrics=self.metrics
            )
            
        except Exception as e:
            return HealthCheckOutput(
                status="error",
                server_name=self.server_name,
                api_count=0,
                vector_store_status="error",
                blender_connection_status="error",
                last_updated=0,
                performance_metrics={"error": str(e)}
            )
    
    def _generate_search_suggestions(self, query: str, results: List[APIInfo]) -> List[str]:
        """Generate search suggestions based on query and results"""
        suggestions = []
        
        if not results:
            suggestions.extend([
                "Try using more specific terms",
                "Check spelling and try synonyms",
                f"Search in other categories besides '{self.category}'"
            ])
        elif len(results) < 3:
            suggestions.extend([
                "Try broader search terms",
                "Remove specific constraints",
                "Consider related operations"
            ])
        
        # Add category-specific suggestions
        suggestions.extend(self._get_category_suggestions(query))
        
        return suggestions[:3]  # Limit to 3 suggestions
    
    def _update_metrics(self, response_time_ms: float, success: bool):
        """Update performance metrics"""
        self.metrics['total_requests'] += 1
        if success:
            self.metrics['successful_requests'] += 1
        
        # Update average response time
        total = self.metrics['total_requests']
        current_avg = self.metrics['avg_response_time']
        self.metrics['avg_response_time'] = (current_avg * (total - 1) + response_time_ms) / total
        self.metrics['last_request_time'] = time.time()
    
    @abstractmethod
    async def _register_category_tools(self):
        """Register category-specific MCP tools"""
        pass
    
    @abstractmethod
    def _get_category_suggestions(self, query: str) -> List[str]:
        """Get category-specific search suggestions"""
        pass
    
    def run(self, host: str = "localhost", port: int = 8000):
        """Run the MCP server"""
        if not MCP_AVAILABLE:
            print("❌ Cannot run server - FastMCP not available")
            return
        
        print(f"🚀 Starting {self.server_name} MCP server on {host}:{port}")
        self.mcp.run(host=host, port=port)
