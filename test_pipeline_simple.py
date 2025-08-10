"""
Simplified Multi-Agent Pipeline Test
Tests the core workflow without problematic health checks
"""

import asyncio
import time
from pathlib import Path

from agents import (
    PlannerAgent, CoordinatorAgent, CoderAgent, QAAgent,
    PlannerInput, CoordinatorInput, CoderInput, QAInput,
    AgentStatus
)

async def test_simplified_pipeline():
    """Test the simplified multi-agent pipeline"""
    print("🚀 Simplified Multi-Agent Pipeline Test")
    print("="*60)
    
    # Test prompt
    test_prompt = "Create an old man sitting on a wooden chair in his room with lighting at 30 degrees from his head"
    
    try:
        # Initialize agents
        print("\n📋 **Initializing Agents**")
        planner = PlannerAgent()
        coordinator = CoordinatorAgent()
        coder = CoderAgent()
        qa = QAAgent()
        
        # Initialize coordinator
        coord_init = await coordinator.initialize()
        print(f"   All agents initialized: {'✅' if coord_init else '❌'}")
        
        # Step 1: Planner
        print(f"\n🧠 **Step 1: Planning**")
        planner_input = PlannerInput(
            prompt=test_prompt,
            style_preferences={"quality": "high", "style": "realistic"}
        )
        
        planner_result = await planner.process(planner_input)
        print(f"   Status: {planner_result.status.value}")
        
        if not planner_result.success:
            print(f"   ❌ Failed: {planner_result.message}")
            return False
        
        plan = planner_result.plan
        print(f"   ✅ Generated {len(plan.subtasks)} subtasks")
        
        # Step 2: Coordinator
        print(f"\n🎯 **Step 2: Coordination**")
        coordinator_input = CoordinatorInput(
            plan=plan,
            available_servers=["blender-mesh", "blender-objects", "blender-geometry", "blender-shaders"],
            execution_context={"scene_name": "test_scene", "quality": "high"}
        )
        
        coordinator_result = await coordinator.process(coordinator_input)
        print(f"   Status: {coordinator_result.status.value}")
        
        if not coordinator_result.success:
            print(f"   ❌ Failed: {coordinator_result.message}")
            return False
        
        api_mappings = coordinator_result.api_mappings
        total_apis = sum(len(mapping.api_calls) for mapping in api_mappings)
        print(f"   ✅ Mapped to {total_apis} API calls")
        
        # Step 3: Coder
        print(f"\n💻 **Step 3: Code Generation**")
        coder_input = CoderInput(
            plan=plan,
            api_mappings=api_mappings,
            execution_context=coordinator_input.execution_context
        )
        
        coder_result = await coder.process(coder_input)
        print(f"   Status: {coder_result.status.value}")
        
        if not coder_result.success:
            print(f"   ❌ Failed: {coder_result.message}")
            return False
        
        generated_script = coder_result.generated_script
        script_lines = len(generated_script.python_code.split('\n'))
        print(f"   ✅ Generated {script_lines} lines of code")
        
        # Step 4: QA
        print(f"\n🔍 **Step 4: Quality Assurance**")
        qa_input = QAInput(
            generated_script=generated_script,
            original_plan=plan,
            execution_context=coordinator_input.execution_context
        )
        
        qa_result = await qa.process(qa_input)
        print(f"   Status: {qa_result.status.value}")
        
        if not qa_result.success:
            print(f"   ❌ Failed: {qa_result.message}")
            return False
        
        validation = qa_result.validation_result
        print(f"   ✅ Validation score: {validation.confidence_score:.3f}")
        
        # Save generated script
        script_path = Path("generated_blender_script.py")
        script_path.write_text(generated_script.python_code, encoding='utf-8')
        print(f"\n💾 **Script saved to**: {script_path.absolute()}")
        
        # Show summary
        print(f"\n📊 **Pipeline Summary**")
        print(f"   ├─ Subtasks planned: {len(plan.subtasks)}")
        print(f"   ├─ API calls mapped: {total_apis}")
        print(f"   ├─ Script lines: {script_lines}")
        print(f"   ├─ Validation score: {validation.confidence_score:.3f}")
        print(f"   └─ Overall success: {'✅ YES' if validation.is_valid else '❌ NO'}")
        
        return validation.is_valid
        
    except Exception as e:
        print(f"💥 Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run simplified pipeline test"""
    success = await test_simplified_pipeline()
    
    print("\n" + "="*60)
    if success:
        print("🎉 **SUCCESS**: Multi-Agent Pipeline is Working!")
        print("🚀 **Ready for Production!**")
        print("\n📋 **What We Built**:")
        print("   ✅ Planner Agent - Decomposes prompts into subtasks")
        print("   ✅ Coordinator Agent - Maps subtasks to Blender APIs")
        print("   ✅ Coder Agent - Generates executable Python scripts")
        print("   ✅ QA Agent - Validates script quality and compliance")
        print("\n🎯 **Complete Pipeline**: Prompt → Plan → APIs → Code → Validation")
    else:
        print("❌ **FAILED**: Pipeline needs debugging")

if __name__ == "__main__":
    asyncio.run(main())
