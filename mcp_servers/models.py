"""
Pydantic models for Blender API MCP servers
Type-safe input/output models following EAG-V17 patterns
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum

# ================= Base Models =================

class APIParameter(BaseModel):
    """Represents a single API parameter"""
    name: str
    type: str
    default: Optional[str] = None
    description: str = ""
    constraints: Optional[str] = None
    optional: bool = False
    enum_values: Optional[List[str]] = None

class APIInfo(BaseModel):
    """Complete API information"""
    id: str
    full_name: str
    description: str
    category: str
    module: str
    signature: str
    parameters: List[APIParameter]
    tags: List[str]
    examples: List[str]
    score: Optional[float] = None

# ================= Discovery Models =================

class DiscoverAPIsInput(BaseModel):
    """Input for API discovery"""
    intent: str = Field(..., description="Natural language description of what you want to do")
    category_filter: Optional[List[str]] = Field(None, description="Filter by specific categories")
    top_k: int = Field(5, description="Maximum number of APIs to return")
    include_examples: bool = Field(True, description="Include usage examples in results")

class DiscoverAPIsOutput(BaseModel):
    """Output for API discovery"""
    apis: List[APIInfo]
    total_found: int
    search_time_ms: float
    backend_used: str
    suggestions: List[str] = Field(default_factory=list, description="Alternative search suggestions")

# ================= Parameter Validation Models =================

class ValidateParametersInput(BaseModel):
    """Input for parameter validation"""
    api_name: str = Field(..., description="Full API name (e.g., bpy.ops.mesh.bevel)")
    parameters: Dict[str, Any] = Field(..., description="Parameters to validate")

class ParameterValidationResult(BaseModel):
    """Single parameter validation result"""
    name: str
    valid: bool
    error_message: Optional[str] = None
    suggested_value: Optional[Any] = None
    type_info: str

class ValidateParametersOutput(BaseModel):
    """Output for parameter validation"""
    api_name: str
    valid: bool
    parameter_results: List[ParameterValidationResult]
    corrected_parameters: Dict[str, Any]
    validation_errors: List[str]

# ================= Code Generation Models =================

class GenerateCodeInput(BaseModel):
    """Input for Blender Python code generation"""
    apis: List[str] = Field(..., description="List of API names to use")
    parameters: Dict[str, Dict[str, Any]] = Field(..., description="Parameters for each API")
    context: str = Field("", description="Additional context for code generation")
    include_error_handling: bool = Field(True, description="Include try-catch blocks")
    include_comments: bool = Field(True, description="Include explanatory comments")

class GenerateCodeOutput(BaseModel):
    """Output for code generation"""
    code: str
    imports: List[str]
    warnings: List[str] = Field(default_factory=list)
    estimated_execution_time: Optional[float] = None

# ================= Execution Models =================

class ExecuteCodeInput(BaseModel):
    """Input for code execution on headless Blender"""
    code: str = Field(..., description="Python code to execute in Blender")
    timeout: int = Field(30, description="Execution timeout in seconds")
    capture_output: bool = Field(True, description="Capture stdout/stderr")
    export_gltf: bool = Field(False, description="Export result as GLTF")
    export_path: Optional[str] = Field(None, description="Path for GLTF export")

class ExecutionResult(BaseModel):
    """Result of code execution"""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float
    gltf_path: Optional[str] = None
    screenshot_path: Optional[str] = None

class ExecuteCodeOutput(BaseModel):
    """Output for code execution"""
    result: ExecutionResult
    blender_version: str
    warnings: List[str] = Field(default_factory=list)

# ================= Health Check Models =================

class HealthCheckOutput(BaseModel):
    """Health check output"""
    status: str  # healthy, degraded, unhealthy
    server_name: str
    api_count: int
    vector_store_status: str
    blender_connection_status: str
    last_updated: float
    performance_metrics: Dict[str, Any]

# ================= Search Filter Models =================

class SearchFilters(BaseModel):
    """Search filters for API discovery"""
    categories: Optional[List[str]] = None
    modules: Optional[List[str]] = None
    has_parameters: Optional[bool] = None
    complexity_level: Optional[str] = None  # basic, intermediate, advanced
    tags: Optional[List[str]] = None

# ================= Mesh-Specific Models =================

class MeshOperationType(str, Enum):
    """Types of mesh operations"""
    MODELING = "modeling"
    SUBDIVISION = "subdivision"
    DEFORMATION = "deformation"
    CLEANUP = "cleanup"
    GENERATION = "generation"
    ANALYSIS = "analysis"

class DiscoverMeshAPIsInput(DiscoverAPIsInput):
    """Mesh-specific API discovery input"""
    operation_type: Optional[MeshOperationType] = None
    affects_geometry: Optional[bool] = None
    requires_selection: Optional[bool] = None

# ================= Object-Specific Models =================

class ObjectOperationType(str, Enum):
    """Types of object operations"""
    TRANSFORM = "transform"
    DUPLICATION = "duplication"
    HIERARCHY = "hierarchy"
    PROPERTIES = "properties"
    ANIMATION = "animation"
    CONSTRAINTS = "constraints"

class DiscoverObjectAPIsInput(DiscoverAPIsInput):
    """Object-specific API discovery input"""
    operation_type: Optional[ObjectOperationType] = None
    affects_transform: Optional[bool] = None
    works_with_multiple: Optional[bool] = None

# ================= Geometry Nodes Models =================

class GeometryNodeCategory(str, Enum):
    """Geometry node categories"""
    INPUT = "input"
    OUTPUT = "output"
    GEOMETRY = "geometry"
    MESH = "mesh"
    CURVE = "curve"
    INSTANCES = "instances"
    MATERIAL = "material"
    TEXTURE = "texture"
    UTILITIES = "utilities"

class DiscoverGeometryAPIsInput(DiscoverAPIsInput):
    """Geometry nodes specific API discovery input"""
    node_category: Optional[GeometryNodeCategory] = None
    input_type: Optional[str] = None
    output_type: Optional[str] = None

# ================= Shader Nodes Models =================

class ShaderNodeCategory(str, Enum):
    """Shader node categories"""
    INPUT = "input"
    OUTPUT = "output"
    SHADER = "shader"
    TEXTURE = "texture"
    COLOR = "color"
    VECTOR = "vector"
    CONVERTER = "converter"
    SCRIPT = "script"

class DiscoverShaderAPIsInput(DiscoverAPIsInput):
    """Shader nodes specific API discovery input"""
    node_category: Optional[ShaderNodeCategory] = None
    material_type: Optional[str] = None  # principled, emission, etc.
    render_engine: Optional[str] = None  # cycles, eevee

# ================= Error Models =================

class APIError(BaseModel):
    """API error information"""
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None
    suggestions: List[str] = Field(default_factory=list)

class ErrorResponse(BaseModel):
    """Standard error response"""
    error: APIError
    request_id: Optional[str] = None
    timestamp: float
