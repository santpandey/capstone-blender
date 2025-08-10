"""
Complete Multi-Agent Pipeline Test
Tests the full workflow: Planner → Coordinator → Coder → QA
"""

import asyncio
import time
import json
from pathlib import Path

from agents import (
    PlannerAgent, CoordinatorAgent, CoderAgent, QAAgent,
    PlannerInput, CoordinatorInput, CoderInput, QAInput,
    AgentStatus
)

async def test_complete_pipeline():
    """Test the complete multi-agent pipeline end-to-end"""
    print("🚀 Starting Complete Multi-Agent Pipeline Test")
    print("="*80)
    
    # Test prompt
    test_prompt = "Create an old man sitting on a wooden chair in his room with lighting at 30 degrees from his head"
    
    try:
        # Step 1: Initialize all agents
        print("\n📋 **Step 1: Initializing Agents**")
        
        planner = PlannerAgent()
        coordinator = CoordinatorAgent()
        coder = CoderAgent()
        qa = QAAgent()
        
        # Initialize coordinator (others don't need async init)
        coord_init = await coordinator.initialize()
        print(f"   Planner: ✅ Ready")
        print(f"   Coordinator: {'✅ Ready' if coord_init else '❌ Failed'}")
        print(f"   Coder: ✅ Ready")
        print(f"   QA: ✅ Ready")
        
        if not coord_init:
            print("❌ Pipeline initialization failed")
            return False
        
        # Step 2: Planner Agent - Decompose prompt
        print(f"\n🧠 **Step 2: Planner Agent - Decomposing Prompt**")
        print(f"   Input: '{test_prompt}'")
        
        planner_input = PlannerInput(
            prompt=test_prompt,
            style_preferences={"quality": "high", "style": "realistic"}
        )
        
        start_time = time.time()
        planner_result = await planner.process(planner_input)
        planner_time = (time.time() - start_time) * 1000
        
        print(f"   Status: {planner_result.status.value}")
        print(f"   Time: {planner_time:.2f}ms")
        
        if not planner_result.success:
            print(f"   ❌ Planner failed: {planner_result.message}")
            return False
        
        plan = planner_result.plan
        print(f"   ✅ Generated {len(plan.subtasks)} subtasks")
        for i, subtask in enumerate(plan.subtasks[:3]):  # Show first 3
            print(f"      {i+1}. {subtask.title} ({subtask.type.value})")
        
        # Step 3: Coordinator Agent - Map to APIs
        print(f"\n🎯 **Step 3: Coordinator Agent - Mapping to APIs**")
        
        coordinator_input = CoordinatorInput(
            plan=plan,
            available_servers=["blender-mesh", "blender-objects", "blender-geometry", "blender-shaders"],
            execution_context={
                "scene_name": "old_man_scene",
                "target_format": "gltf",
                "quality": "high"
            }
        )
        
        start_time = time.time()
        coordinator_result = await coordinator.process(coordinator_input)
        coordinator_time = (time.time() - start_time) * 1000
        
        print(f"   Status: {coordinator_result.status.value}")
        print(f"   Time: {coordinator_time:.2f}ms")
        
        if not coordinator_result.success:
            print(f"   ❌ Coordinator failed: {coordinator_result.message}")
            return False
        
        api_mappings = coordinator_result.api_mappings
        total_apis = sum(len(mapping.api_calls) for mapping in api_mappings)
        avg_confidence = sum(mapping.confidence_score for mapping in api_mappings) / len(api_mappings)
        
        print(f"   ✅ Mapped {len(api_mappings)} subtasks to {total_apis} API calls")
        print(f"   Average confidence: {avg_confidence:.3f}")
        print(f"   Execution strategy: {coordinator_result.execution_strategy}")
        
        # Step 4: Coder Agent - Generate Python script
        print(f"\n💻 **Step 4: Coder Agent - Generating Python Script**")
        
        coder_input = CoderInput(
            plan=plan,
            api_mappings=api_mappings,
            execution_context=coordinator_input.execution_context
        )
        
        start_time = time.time()
        coder_result = await coder.process(coder_input)
        coder_time = (time.time() - start_time) * 1000
        
        print(f"   Status: {coder_result.status.value}")
        print(f"   Time: {coder_time:.2f}ms")
        
        if not coder_result.success:
            print(f"   ❌ Coder failed: {coder_result.message}")
            return False
        
        generated_script = coder_result.generated_script
        script_lines = len(generated_script.python_code.split('\n'))
        
        print(f"   ✅ Generated script with {generated_script.api_calls_count} API calls")
        print(f"   Script length: {script_lines} lines")
        print(f"   Estimated execution time: {generated_script.estimated_execution_time_seconds:.1f}s")
        print(f"   Validation passed: {generated_script.validation_passed}")
        
        # Step 5: QA Agent - Validate script and quality
        print(f"\n🔍 **Step 5: QA Agent - Validating Script Quality**")
        
        qa_input = QAInput(
            generated_script=generated_script,
            original_plan=plan,
            execution_context=coordinator_input.execution_context
        )
        
        start_time = time.time()
        qa_result = await qa.process(qa_input)
        qa_time = (time.time() - start_time) * 1000
        
        print(f"   Status: {qa_result.status.value}")
        print(f"   Time: {qa_time:.2f}ms")
        
        if not qa_result.success:
            print(f"   ❌ QA failed: {qa_result.message}")
            return False
        
        validation = qa_result.validation_result
        print(f"   ✅ Validation completed")
        print(f"   Overall score: {validation.confidence_score:.3f}")
        print(f"   Quality level: {validation.quality_metrics.get('quality_level', 'unknown')}")
        print(f"   Issues found: {len(validation.issues_found)}")
        print(f"   Suggestions: {len(validation.suggestions)}")
        
        # Step 6: Pipeline Summary
        print(f"\n📊 **Pipeline Summary**")
        
        total_time = planner_time + coordinator_time + coder_time + qa_time
        
        print(f"   Total execution time: {total_time:.2f}ms")
        print(f"   ├─ Planner: {planner_time:.2f}ms ({planner_time/total_time*100:.1f}%)")
        print(f"   ├─ Coordinator: {coordinator_time:.2f}ms ({coordinator_time/total_time*100:.1f}%)")
        print(f"   ├─ Coder: {coder_time:.2f}ms ({coder_time/total_time*100:.1f}%)")
        print(f"   └─ QA: {qa_time:.2f}ms ({qa_time/total_time*100:.1f}%)")
        
        print(f"\n   📈 **Results**:")
        print(f"   ├─ Subtasks planned: {len(plan.subtasks)}")
        print(f"   ├─ API calls mapped: {total_apis}")
        print(f"   ├─ Script lines generated: {script_lines}")
        print(f"   ├─ Validation score: {validation.confidence_score:.3f}")
        print(f"   └─ Overall success: {'✅ YES' if validation.is_valid else '❌ NO'}")
        
        # Save generated script for inspection
        script_path = Path("generated_script.py")
        script_path.write_text(generated_script.python_code, encoding='utf-8')
        print(f"\n   💾 Generated script saved to: {script_path.absolute()}")
        
        # Show sample of generated code
        print(f"\n   📝 **Sample Generated Code**:")
        code_lines = generated_script.python_code.split('\n')
        for i, line in enumerate(code_lines[10:20]):  # Show lines 10-20
            print(f"   {i+10:2d}: {line}")
        print("   ... (truncated)")
        
        return validation.is_valid
        
    except Exception as e:
        print(f"💥 Pipeline test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_agent_health_checks():
    """Test health checks for all agents"""
    print("\n" + "="*80)
    print("🏥 **Agent Health Checks**")
    print("="*80)
    
    agents = {
        "Planner": PlannerAgent(),
        "Coordinator": CoordinatorAgent(),
        "Coder": CoderAgent(),
        "QA": QAAgent()
    }
    
    # Initialize coordinator
    await agents["Coordinator"].initialize()
    
    for name, agent in agents.items():
        try:
            health = await agent.health_check()
            print(f"\n🔍 **{name} Agent Health**:")
            for key, value in health.items():
                status = "✅" if value else "❌" if isinstance(value, bool) else "📊"
                print(f"   {status} {key}: {value}")
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")

async def main():
    """Run complete pipeline tests"""
    
    # Test 1: Complete pipeline
    pipeline_success = await test_complete_pipeline()
    
    # Test 2: Health checks
    await test_agent_health_checks()
    
    # Final results
    print("\n" + "="*80)
    print("🎉 **FINAL RESULTS**")
    print("="*80)
    
    if pipeline_success:
        print("✅ **SUCCESS**: Complete multi-agent pipeline is working!")
        print("🚀 **Ready for production deployment!**")
        print("\n📋 **Next Steps**:")
        print("   1. Deploy MCP servers for Blender API categories")
        print("   2. Set up headless Blender execution environment")
        print("   3. Implement frontend with Three.js for asset rendering")
        print("   4. Add multimodal QA validation with computer vision")
    else:
        print("❌ **FAILED**: Pipeline has issues that need to be addressed")
        print("🔧 **Check the validation results above for improvement suggestions**")

if __name__ == "__main__":
    asyncio.run(main())
