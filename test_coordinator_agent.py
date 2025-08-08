"""
Comprehensive test suite for the Coordinator Agent
Tests API mapping, search integration, and coordination logic
"""

import asyncio
import json
import time
from pathlib import Path

from agents import (
    CoordinatorAgent, CoordinatorInput, CoordinatorOutput,
    TaskPlan, SubTask, TaskType, TaskComplexity, TaskPriority,
    AgentStatus
)

async def test_coordinator_initialization():
    """Test coordinator agent initialization"""
    print("🚀 Testing Coordinator Agent initialization...")
    
    coordinator = CoordinatorAgent()
    
    # Test initialization
    start_time = time.time()
    success = await coordinator.initialize()
    init_time = (time.time() - start_time) * 1000
    
    if success:
        print(f"✅ Initialization successful in {init_time:.2f}ms")
    else:
        print("❌ Initialization failed")
        return None
    
    # Test health check
    health = await coordinator.health_check()
    print("🏥 **Health Check**:")
    for key, value in health.items():
        print(f"   {key}: {value}")
    
    return coordinator

async def test_simple_coordination(coordinator):
    """Test coordination with a simple task plan"""
    print("\n" + "="*80)
    print("======================== SIMPLE COORDINATION TEST ===========================")
    print("="*80)
    
    # Create a simple task plan
    subtasks = [
        SubTask(
            task_id="task_1",
            title="Create a simple cube",
            description="Add a basic cube primitive to the scene",
            type=TaskType.CREATE_OBJECT,
            complexity=TaskComplexity.SIMPLE,
            priority=TaskPriority.HIGH,
            estimated_time_minutes=2,
            dependencies=[],
            context={"object_type": "cube", "size": "medium"}
        )
    ]
    
    plan = TaskPlan(
        plan_id="simple_plan",
        description="Create a simple cube object",
        subtasks=subtasks,
        estimated_total_time_minutes=2,
        parallel_groups=[[subtasks[0].task_id]]
    )
    
    # Create coordination input
    coord_input = CoordinatorInput(
        plan=plan,
        execution_context={
            "scene_name": "test_scene",
            "target_format": "gltf",
            "quality": "medium"
        }
    )
    
    # Test coordination
    print(f"🎯 Coordinating simple plan with {len(subtasks)} subtask...")
    start_time = time.time()
    
    result = await coordinator.process(coord_input)
    
    coordination_time = (time.time() - start_time) * 1000
    
    # Display results
    print(f"   Coordination time: {coordination_time:.2f}ms")
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    
    if result.success and result.api_mappings:
        mapping = result.api_mappings[0]
        print(f"   ✅ Generated {len(mapping.api_calls)} API calls")
        print(f"   Confidence: {mapping.confidence_score:.3f}")
        print(f"   MCP Server: {mapping.mcp_server}")
        
        # Show top API calls
        for i, api_call in enumerate(mapping.api_calls[:3]):
            print(f"   API {i+1}: {api_call['api_name']} (relevance: {api_call['relevance_score']:.3f})")
    
    return result

async def test_complex_coordination(coordinator):
    """Test coordination with a complex multi-task plan"""
    print("\n" + "="*80)
    print("======================= COMPLEX COORDINATION TEST ========================")
    print("="*80)
    
    # Create a complex task plan
    subtasks = [
        SubTask(
            task_id="task_1",
            title="Create character base mesh",
            description="Create a human character using basic mesh operations and sculpting",
            type=TaskType.CREATE_CHARACTER,
            complexity=TaskComplexity.COMPLEX,
            priority=TaskPriority.HIGH,
            estimated_time_minutes=15,
            dependencies=[],
            context={"character_type": "human", "age": "adult", "gender": "male"}
        ),
        SubTask(
            task_id="task_2", 
            title="Create chair furniture",
            description="Model a wooden chair with armrests and cushioning",
            type=TaskType.CREATE_FURNITURE,
            complexity=TaskComplexity.MODERATE,
            priority=TaskPriority.MEDIUM,
            estimated_time_minutes=10,
            dependencies=[],
            context={"furniture_type": "chair", "material": "wood", "style": "modern"}
        ),
        SubTask(
            task_id="task_3",
            title="Setup scene lighting",
            description="Add three-point lighting setup with 30-degree angle from head",
            type=TaskType.LIGHTING_SETUP,
            complexity=TaskComplexity.MODERATE,
            priority=TaskPriority.MEDIUM,
            estimated_time_minutes=8,
            dependencies=["task_1"],
            context={"lighting_type": "three_point", "angle": 30, "intensity": "medium"}
        ),
        SubTask(
            task_id="task_4",
            title="Apply materials and textures",
            description="Apply realistic skin material to character and wood texture to chair",
            type=TaskType.MATERIAL_APPLICATION,
            complexity=TaskComplexity.MODERATE,
            priority=TaskPriority.LOW,
            estimated_time_minutes=12,
            dependencies=["task_1", "task_2"],
            context={"materials": ["skin", "wood"], "quality": "high"}
        )
    ]
    
    plan = TaskPlan(
        plan_id="complex_plan",
        description="Create a scene with an old man sitting on a chair with proper lighting",
        subtasks=subtasks,
        estimated_total_time_minutes=45,
        parallel_groups=[
            ["task_1", "task_2"],  # Character and chair can be created in parallel
            ["task_3"],            # Lighting depends on character
            ["task_4"]             # Materials depend on both character and chair
        ]
    )
    
    # Create coordination input
    coord_input = CoordinatorInput(
        plan=plan,
        execution_context={
            "scene_name": "old_man_scene",
            "target_format": "gltf",
            "quality": "high",
            "render_engine": "cycles"
        }
    )
    
    # Test coordination
    print(f"🎯 Coordinating complex plan with {len(subtasks)} subtasks...")
    start_time = time.time()
    
    result = await coordinator.process(coord_input)
    
    coordination_time = (time.time() - start_time) * 1000
    
    # Display results
    print(f"   Coordination time: {coordination_time:.2f}ms")
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.success}")
    print(f"   Message: {result.message}")
    
    if result.success and result.api_mappings:
        print(f"   ✅ Generated mappings for {len(result.api_mappings)} subtasks")
        
        total_api_calls = sum(len(mapping.api_calls) for mapping in result.api_mappings)
        avg_confidence = sum(mapping.confidence_score for mapping in result.api_mappings) / len(result.api_mappings)
        
        print(f"   Total API calls: {total_api_calls}")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Execution strategy: {result.execution_strategy}")
        
        # Show mapping details
        for i, mapping in enumerate(result.api_mappings):
            subtask = next(st for st in subtasks if st.task_id == mapping.subtask_id)
            print(f"\n   📋 **Subtask {i+1}**: {subtask.title}")
            print(f"      Type: {subtask.type.value}")
            print(f"      Complexity: {subtask.complexity.value}")
            print(f"      API calls: {len(mapping.api_calls)}")
            print(f"      Confidence: {mapping.confidence_score:.3f}")
            print(f"      MCP Server: {mapping.mcp_server}")
            
            # Show top 3 API calls
            for j, api_call in enumerate(mapping.api_calls[:3]):
                print(f"         {j+1}. {api_call['api_name']} (relevance: {api_call['relevance_score']:.3f})")
        
        # Show resource requirements
        if result.resource_requirements:
            print(f"\n   📊 **Resource Requirements**:")
            for key, value in result.resource_requirements.items():
                print(f"      {key}: {value}")
    
    return result

async def test_edge_cases(coordinator):
    """Test coordinator with edge cases and error scenarios"""
    print("\n" + "="*80)
    print("=========================== EDGE CASES TEST ==============================")
    print("="*80)
    
    # Test 1: Empty plan
    print("🧪 Testing edge case: Empty plan")
    empty_plan = TaskPlan(
        plan_id="empty_plan",
        description="Empty plan with no subtasks",
        subtasks=[],
        estimated_total_time_minutes=0,
        parallel_groups=[]
    )
    
    coord_input = CoordinatorInput(
        plan=empty_plan,
        execution_context={}
    )
    
    result = await coordinator.process(coord_input)
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.success}")
    print(f"   API mappings: {len(result.api_mappings) if result.api_mappings else 0}")
    
    # Test 2: Vague/ambiguous task
    print("\n🧪 Testing edge case: Vague task description")
    vague_subtask = SubTask(
        task_id="vague_task",
        title="Make something",
        description="Create some kind of object or thing",
        type=TaskType.CREATE_OBJECT,
        complexity=TaskComplexity.SIMPLE,
        priority=TaskPriority.LOW,
        estimated_time_minutes=5,
        dependencies=[],
        context={}
    )
    
    vague_plan = TaskPlan(
        plan_id="vague_plan",
        description="Vague plan",
        subtasks=[vague_subtask],
        estimated_total_time_minutes=5,
        parallel_groups=[[vague_subtask.task_id]]
    )
    
    coord_input = CoordinatorInput(
        plan=vague_plan,
        execution_context={}
    )
    
    result = await coordinator.process(coord_input)
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.success}")
    if result.api_mappings:
        mapping = result.api_mappings[0]
        print(f"   Confidence: {mapping.confidence_score:.3f}")
        print(f"   API calls found: {len(mapping.api_calls)}")
    
    # Test 3: Expert-level complex task
    print("\n🧪 Testing edge case: Expert-level complex task")
    expert_subtask = SubTask(
        task_id="expert_task",
        title="Advanced procedural character generation",
        description="Create a highly detailed character using advanced geometry nodes, procedural texturing, and complex rigging systems",
        type=TaskType.CREATE_CHARACTER,
        complexity=TaskComplexity.EXPERT,
        priority=TaskPriority.HIGH,
        estimated_time_minutes=60,
        dependencies=[],
        context={
            "detail_level": "ultra_high",
            "procedural": True,
            "rigging": "advanced",
            "texturing": "procedural"
        }
    )
    
    expert_plan = TaskPlan(
        plan_id="expert_plan",
        description="Expert-level character creation",
        subtasks=[expert_subtask],
        estimated_total_time_minutes=60,
        parallel_groups=[[expert_subtask.task_id]]
    )
    
    coord_input = CoordinatorInput(
        plan=expert_plan,
        execution_context={"quality": "ultra_high"}
    )
    
    result = await coordinator.process(coord_input)
    print(f"   Status: {result.status.value}")
    print(f"   Success: {result.success}")
    if result.api_mappings:
        mapping = result.api_mappings[0]
        print(f"   Confidence: {mapping.confidence_score:.3f}")
        print(f"   API calls found: {len(mapping.api_calls)}")
        print(f"   Alternatives: {len(mapping.alternatives)}")

async def test_performance_benchmarks(coordinator):
    """Test coordinator performance with various loads"""
    print("\n" + "="*80)
    print("======================== PERFORMANCE BENCHMARK TEST =======================")
    print("="*80)
    
    print("🚀 Running performance benchmarks...")
    
    # Test different plan sizes
    plan_sizes = [1, 3, 5, 10]
    
    for size in plan_sizes:
        # Generate plan with specified number of subtasks
        subtasks = []
        for i in range(size):
            subtask = SubTask(
                task_id=f"perf_task_{i}",
                title=f"Performance test task {i}",
                description=f"Test task {i} for performance benchmarking",
                type=TaskType.CREATE_OBJECT,
                complexity=TaskComplexity.MODERATE,
                priority=TaskPriority.MEDIUM,
                estimated_time_minutes=5,
                dependencies=[],
                context={"test": True, "index": i}
            )
            subtasks.append(subtask)
        
        plan = TaskPlan(
            plan_id=f"perf_plan_{size}",
            description=f"Performance test plan with {size} subtasks",
            subtasks=subtasks,
            estimated_total_time_minutes=size * 5,
            parallel_groups=[[st.task_id for st in subtasks]]
        )
        
        coord_input = CoordinatorInput(
            plan=plan,
            execution_context={"performance_test": True}
        )
        
        # Measure coordination time
        start_time = time.time()
        result = await coordinator.process(coord_input)
        coordination_time = (time.time() - start_time) * 1000
        
        print(f"   Plan size {size}: {coordination_time:.2f}ms")
        
        if result.success:
            total_apis = sum(len(mapping.api_calls) for mapping in result.api_mappings)
            avg_confidence = sum(mapping.confidence_score for mapping in result.api_mappings) / len(result.api_mappings)
            print(f"      Total APIs: {total_apis}, Avg confidence: {avg_confidence:.3f}")

async def test_coordination_stats(coordinator):
    """Test coordination statistics and monitoring"""
    print("\n" + "="*80)
    print("======================== COORDINATION STATS TEST ==========================")
    print("="*80)
    
    # Get coordination stats
    stats = await coordinator.get_coordination_stats()
    
    print("📊 **Coordination Statistics**:")
    for key, value in stats.items():
        if isinstance(value, dict):
            print(f"   {key}:")
            for sub_key, sub_value in value.items():
                print(f"      {sub_key}: {sub_value}")
        else:
            print(f"   {key}: {value}")

async def main():
    """Run all coordinator agent tests"""
    print("🚀 Starting Comprehensive Coordinator Agent Tests")
    print("="*80)
    
    try:
        # Initialize coordinator
        coordinator = await test_coordinator_initialization()
        if not coordinator:
            print("❌ Failed to initialize coordinator - aborting tests")
            return
        
        # Run test suite
        await test_simple_coordination(coordinator)
        await test_complex_coordination(coordinator)
        await test_edge_cases(coordinator)
        await test_performance_benchmarks(coordinator)
        await test_coordination_stats(coordinator)
        
        print("\n" + "="*80)
        print("========================= ALL TESTS COMPLETED =========================")
        print("="*80)
        print("✅ Coordinator Agent testing completed successfully!")
        print("🚀 Ready for integration with Coder Agent!")
        
    except Exception as e:
        print(f"💥 Test suite failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
