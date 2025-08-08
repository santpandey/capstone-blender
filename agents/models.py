"""
Pydantic models for the multi-agent pipeline
Defines structured data formats for agent communication
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Union
from enum import Enum
import time

# ================= Task Models =================

class TaskType(str, Enum):
    """Types of 3D modeling tasks"""
    CREATE_CHARACTER = "create_character"
    CREATE_OBJECT = "create_object"
    CREATE_ENVIRONMENT = "create_environment"
    CREATE_CLOTHING = "create_clothing"
    CREATE_FURNITURE = "create_furniture"
    CREATE_ARCHITECTURE = "create_architecture"
    SCENE_COMPOSITION = "scene_composition"
    LIGHTING_SETUP = "lighting_setup"
    MATERIAL_APPLICATION = "material_application"
    ANIMATION_SETUP = "animation_setup"
    POST_PROCESSING = "post_processing"

class TaskComplexity(str, Enum):
    """Task complexity levels"""
    SIMPLE = "simple"          # Single primitive operations
    MODERATE = "moderate"      # Multiple operations, basic workflows
    COMPLEX = "complex"        # Advanced workflows, multiple objects
    EXPERT = "expert"          # Professional-level, intricate details

class TaskPriority(str, Enum):
    """Task execution priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class SubTask(BaseModel):
    """Individual subtask within a larger plan"""
    task_id: str = Field(..., description="Unique identifier for the subtask")
    type: TaskType = Field(..., description="Type of modeling task")
    title: str = Field(..., description="Brief title for the subtask")
    description: str = Field(..., description="Detailed description of what needs to be done")
    requirements: List[str] = Field(default_factory=list, description="Prerequisites and requirements")
    dependencies: List[str] = Field(default_factory=list, description="IDs of subtasks that must complete first")
    estimated_time_minutes: int = Field(5, description="Estimated time to complete in minutes")
    complexity: TaskComplexity = Field(TaskComplexity.MODERATE, description="Complexity level")
    priority: TaskPriority = Field(TaskPriority.MEDIUM, description="Execution priority")
    
    # Blender-specific metadata
    blender_categories: List[str] = Field(default_factory=list, description="Relevant Blender API categories")
    mesh_operations: List[str] = Field(default_factory=list, description="Expected mesh operations")
    object_count: int = Field(1, description="Number of objects this task will create/modify")
    
    # Context for other agents
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context for downstream agents")

class TaskPlan(BaseModel):
    """Complete plan for 3D asset generation"""
    plan_id: str = Field(..., description="Unique identifier for the plan")
    original_prompt: str = Field(..., description="Original user prompt")
    summary: str = Field(..., description="Brief summary of the plan")
    subtasks: List[SubTask] = Field(..., description="List of subtasks to execute")
    total_estimated_time: int = Field(0, description="Total estimated time in minutes")
    overall_complexity: TaskComplexity = Field(TaskComplexity.MODERATE, description="Overall plan complexity")
    
    # Metadata
    created_at: float = Field(default_factory=time.time, description="Plan creation timestamp")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    
    # Execution tracking
    execution_order: List[str] = Field(default_factory=list, description="Optimal execution order of subtask IDs")
    parallel_groups: List[List[str]] = Field(default_factory=list, description="Groups of subtasks that can run in parallel")

# ================= Agent Communication Models =================

class AgentType(str, Enum):
    """Types of agents in the pipeline"""
    PLANNER = "planner"
    COORDINATOR = "coordinator"
    CODER = "coder"
    QA = "qa"

class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING = "waiting"

class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    agent_type: AgentType = Field(..., description="Type of agent that generated this response")
    status: AgentStatus = Field(..., description="Execution status")
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field("", description="Human-readable status message")
    
    # Response data (varies by agent type)
    data: Dict[str, Any] = Field(default_factory=dict, description="Agent-specific response data")
    
    # Metadata
    execution_time_ms: float = Field(0, description="Time taken to execute in milliseconds")
    timestamp: float = Field(default_factory=time.time, description="Response timestamp")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings generated")

# ================= Planner Agent Models =================

class PlannerInput(BaseModel):
    """Input for the Planner Agent"""
    prompt: str = Field(..., description="Natural language prompt for 3D asset generation")
    style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Style and aesthetic preferences")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Technical constraints and limitations")
    target_complexity: Optional[TaskComplexity] = Field(None, description="Desired complexity level")
    max_execution_time: Optional[int] = Field(None, description="Maximum execution time in minutes")

class PlannerOutput(AgentResponse):
    """Output from the Planner Agent"""
    plan: Optional[TaskPlan] = Field(None, description="Generated task plan")
    alternative_plans: List[TaskPlan] = Field(default_factory=list, description="Alternative plan options")
    planning_rationale: str = Field("", description="Explanation of planning decisions")

# ================= Coordinator Agent Models =================

class APIMapping(BaseModel):
    """Mapping of subtask to specific Blender APIs"""
    subtask_id: str = Field(..., description="ID of the subtask")
    mcp_server: str = Field(..., description="Target MCP server (e.g., blender-mesh)")
    api_calls: List[Dict[str, Any]] = Field(..., description="Specific API calls with parameters")
    confidence_score: float = Field(0.0, description="Confidence in API selection (0-1)")
    alternatives: List[Dict[str, Any]] = Field(default_factory=list, description="Alternative API approaches")

class CoordinatorInput(BaseModel):
    """Input for the Coordinator Agent"""
    plan: TaskPlan = Field(..., description="Task plan to coordinate")
    available_servers: List[str] = Field(..., description="Available MCP servers")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Current execution context")

class CoordinatorOutput(AgentResponse):
    """Output from the Coordinator Agent"""
    api_mappings: List[APIMapping] = Field(default_factory=list, description="API mappings for each subtask")
    execution_strategy: str = Field("", description="Recommended execution strategy")
    resource_requirements: Dict[str, Any] = Field(default_factory=dict, description="Required resources")

# ================= Coder Agent Models =================

class GeneratedScript(BaseModel):
    """Generated Python script for Blender"""
    subtask_id: str = Field(..., description="ID of the subtask this script addresses")
    script_content: str = Field(..., description="Python script content")
    imports: List[str] = Field(default_factory=list, description="Required imports")
    dependencies: List[str] = Field(default_factory=list, description="Script dependencies")
    estimated_execution_time: float = Field(0.0, description="Estimated execution time in seconds")
    validation_status: str = Field("not_validated", description="Script validation status")

class CoderInput(BaseModel):
    """Input for the Coder Agent"""
    api_mappings: List[APIMapping] = Field(..., description="API mappings from Coordinator")
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    code_style_preferences: Dict[str, Any] = Field(default_factory=dict, description="Code generation preferences")

class CoderOutput(AgentResponse):
    """Output from the Coder Agent"""
    scripts: List[GeneratedScript] = Field(default_factory=list, description="Generated scripts")
    execution_order: List[str] = Field(default_factory=list, description="Recommended script execution order")
    integration_notes: str = Field("", description="Notes on script integration")

# ================= QA Agent Models =================

class ValidationIssue(BaseModel):
    """Issue found during QA validation"""
    issue_id: str = Field(..., description="Unique identifier for the issue")
    severity: str = Field(..., description="Issue severity: low, medium, high, critical")
    category: str = Field(..., description="Issue category: geometry, material, lighting, etc.")
    description: str = Field(..., description="Description of the issue")
    suggested_fix: str = Field("", description="Suggested fix or correction")
    affected_objects: List[str] = Field(default_factory=list, description="Objects affected by this issue")
    confidence: float = Field(0.0, description="Confidence in issue detection (0-1)")

class QAInput(BaseModel):
    """Input for the QA Agent"""
    generated_assets: List[str] = Field(..., description="Paths to generated 3D assets")
    original_prompt: str = Field(..., description="Original user prompt for comparison")
    execution_logs: List[str] = Field(default_factory=list, description="Execution logs from script running")
    screenshots: List[str] = Field(default_factory=list, description="Screenshot paths for visual validation")

class QAOutput(AgentResponse):
    """Output from the QA Agent"""
    validation_score: float = Field(0.0, description="Overall validation score (0-1)")
    issues: List[ValidationIssue] = Field(default_factory=list, description="Issues found during validation")
    recommendations: List[str] = Field(default_factory=list, description="Recommendations for improvement")
    approved_for_delivery: bool = Field(False, description="Whether asset is approved for delivery")

# ================= Pipeline Models =================

class PipelineStatus(str, Enum):
    """Overall pipeline execution status"""
    INITIALIZING = "initializing"
    PLANNING = "planning"
    COORDINATING = "coordinating"
    CODING = "coding"
    EXECUTING = "executing"
    VALIDATING = "validating"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class PipelineExecution(BaseModel):
    """Complete pipeline execution tracking"""
    execution_id: str = Field(..., description="Unique execution identifier")
    original_prompt: str = Field(..., description="Original user prompt")
    status: PipelineStatus = Field(PipelineStatus.INITIALIZING, description="Current pipeline status")
    
    # Agent responses
    planner_response: Optional[PlannerOutput] = None
    coordinator_response: Optional[CoordinatorOutput] = None
    coder_response: Optional[CoderOutput] = None
    qa_response: Optional[QAOutput] = None
    
    # Execution metadata
    started_at: float = Field(default_factory=time.time, description="Execution start time")
    completed_at: Optional[float] = None
    total_execution_time: Optional[float] = None
    
    # Results
    final_assets: List[str] = Field(default_factory=list, description="Paths to final generated assets")
    execution_logs: List[str] = Field(default_factory=list, description="Complete execution logs")
    
    def mark_completed(self):
        """Mark execution as completed"""
        self.completed_at = time.time()
        self.total_execution_time = self.completed_at - self.started_at
        self.status = PipelineStatus.COMPLETED
