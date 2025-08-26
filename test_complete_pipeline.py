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

def get_user_prompt():
    """Get user prompt interactively"""
    print("🎨 **Dynamic 3D Asset Generation Pipeline**")
    print("="*80)
    print("Enter your 3D asset description below:")
    print("Examples:")
    print("  • Create a white coffee mug with 'Coffee' text in brown")
    print("  • Design a wooden chair with red cushions")
    print("  • Make a blue car with chrome wheels")
    print("  • Build a house with a red roof and white walls")
    print("-"*80)
    
    while True:
        user_prompt = input("\n🎯 Your prompt: ").strip()
        
        if not user_prompt:
            print("❌ Please enter a valid prompt!")
            continue
            
        if user_prompt.lower() in ['quit', 'exit', 'q']:
            print("👋 Goodbye!")
            return None
            
        # Confirm prompt
        print(f"\n📝 You entered: '{user_prompt}'")
        confirm = input("✅ Proceed with this prompt? (y/n/edit): ").strip().lower()
        
        if confirm in ['y', 'yes']:
            return user_prompt
        elif confirm in ['n', 'no']:
            print("🔄 Let's try again...")
            continue
        elif confirm in ['e', 'edit']:
            continue
        else:
            print("❌ Please enter 'y', 'n', or 'edit'")

async def test_complete_pipeline():
    """Interactive multi-agent pipeline for 3D asset generation"""
    # Get user prompt interactively
    user_prompt = get_user_prompt()
    
    if not user_prompt:
        return  # User chose to quit
    
    print(f"\n🚀 Starting Pipeline for: '{user_prompt}'")
    print("="*80)
    
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
        print("\n🧠 **Step 2: Planner Agent - Decomposing Prompt**")
        planner_input = PlannerInput(
            prompt=user_prompt,
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
                "scene_name": "generated_scene",
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
        
        if len(api_mappings) > 0:
            avg_confidence = sum(mapping.confidence_score for mapping in api_mappings) / len(api_mappings)
            print(f"   ✅ Mapped {len(api_mappings)} subtasks to {total_apis} API calls")
            print(f"   Average confidence: {avg_confidence:.3f}")
        else:
            print(f"   ⚠️ No API mappings generated")
            avg_confidence = 0.0
        
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
    
    all_healthy = True
    
    for name, agent in agents.items():
        try:
            health = await agent.health_check()
            print(f"\n🔍 **{name} Agent Health**:")
            
            if isinstance(health, bool):
                status = "✅" if health else "❌"
                print(f"   {status} healthy: {health}")
                if not health:
                    all_healthy = False
            elif isinstance(health, dict):
                for key, value in health.items():
                    status = "✅" if value else "❌" if isinstance(value, bool) else "📊"
                    print(f"   {status} {key}: {value}")
                    if isinstance(value, bool) and not value:
                        all_healthy = False
            else:
                print(f"   📊 health_status: {health}")
                
        except Exception as e:
            print(f"   ❌ Health check failed: {e}")
            all_healthy = False
    
    return all_healthy

async def main():
    """Main function to run interactive pipeline"""
    print("🎨 **Interactive 3D Asset Generation Pipeline**")
    print("="*80)
    print("Welcome to the Dynamic Multi-Agent 3D Asset Generator!")
    print("This pipeline uses AI agents to create Blender Python scripts from your descriptions.")
    print()
    
    # Test health checks first
    print("🔧 Checking agent health...")
    health_ok = await test_agent_health_checks()
    
    if not health_ok:
        print("❌ Agent health check failed. Please fix issues before continuing.")
        return False
    
    print("✅ All agents are healthy!")
    print()
    
    # Interactive loop
    while True:
        print("\n" + "="*80)
        success = await test_complete_pipeline()
        
        if success is None:  # User chose to quit
            break
            
        # Ask if user wants to continue
        print("\n" + "="*80)
        try:
            continue_choice = input("🔄 Generate another asset? (y/n): ").strip().lower()
            
            if continue_choice not in ['y', 'yes']:
                print("👋 Thank you for using the 3D Asset Generation Pipeline!")
                break
        except (EOFError, KeyboardInterrupt):
            print("\n👋 Pipeline execution completed!")
            break
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
