"""
Simplified demo script for the Planner Agent
Tests prompt decomposition without heavy vector dependencies
"""

import asyncio
import json
import yaml
from pathlib import Path
from typing import Dict, Any

from agents import PlannerAgent
from agents.models import PlannerInput, TaskComplexity

def load_config() -> Dict[str, Any]:
    """Load agent configuration"""
    config_path = Path("config/agents_config.yaml")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config.get('planner_agent', {})
    return {}

def print_separator(title: str):
    """Print a formatted separator"""
    print("\n" + "="*80)
    print(f" {title} ".center(80, "="))
    print("="*80)

def print_subtask_details(subtask):
    """Print detailed subtask information"""
    print(f"\n📋 **{subtask.title}**")
    print(f"   ID: {subtask.task_id}")
    print(f"   Type: {subtask.type.value}")
    print(f"   Description: {subtask.description}")
    print(f"   Complexity: {subtask.complexity.value}")
    print(f"   Priority: {subtask.priority.value}")
    print(f"   Estimated Time: {subtask.estimated_time_minutes} minutes")
    print(f"   Object Count: {subtask.object_count}")
    
    if subtask.dependencies:
        print(f"   Dependencies: {', '.join(subtask.dependencies)}")
    
    if subtask.requirements:
        print(f"   Requirements: {', '.join(subtask.requirements)}")
    
    if subtask.blender_categories:
        print(f"   Blender Categories: {', '.join(subtask.blender_categories)}")
    
    if subtask.mesh_operations:
        print(f"   Mesh Operations: {', '.join(subtask.mesh_operations)}")
    
    if subtask.context:
        print(f"   Context: {json.dumps(subtask.context, indent=6)}")

def print_execution_plan(plan):
    """Print execution plan details"""
    print(f"\n🎯 **Execution Strategy**")
    print(f"   Execution Order: {' → '.join(plan.execution_order)}")
    print(f"   Total Estimated Time: {plan.total_estimated_time} minutes")
    print(f"   Overall Complexity: {plan.overall_complexity.value}")
    
    if plan.parallel_groups:
        print(f"\n   Parallel Execution Groups:")
        for i, group in enumerate(plan.parallel_groups, 1):
            if len(group) > 1:
                print(f"     Group {i}: {' + '.join(group)} (parallel)")
            else:
                print(f"     Group {i}: {group[0]} (sequential)")

async def test_planner_agent():
    """Test the Planner Agent with various prompts"""
    
    print_separator("PLANNER AGENT DEMO - SIMPLIFIED")
    print("Testing natural language prompt decomposition into structured subtasks")
    
    # Load configuration
    config = load_config()
    print(f"\n📁 Loaded configuration: {len(config)} settings")
    
    # Initialize Planner Agent
    planner = PlannerAgent(config)
    print(f"✅ Initialized {planner}")
    
    # Test cases with different complexity levels
    test_cases = [
        {
            "name": "Simple Character Scene",
            "prompt": "Create a simple person sitting on a chair",
            "complexity": TaskComplexity.SIMPLE
        },
        {
            "name": "Complex Character Scene (Original)",
            "prompt": "Draw an asset of an old person with grey hair, moustache, beard wearing light blue shirt and cream trouser sitting on a light brown chair and contemplating",
            "complexity": TaskComplexity.COMPLEX
        },
        {
            "name": "Multi-Character Environment",
            "prompt": "Create a realistic scene with two people talking in a modern office room with wooden furniture, large windows, and natural lighting",
            "complexity": TaskComplexity.EXPERT
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print_separator(f"TEST CASE {i}: {test_case['name']}")
        
        # Prepare input
        planner_input = PlannerInput(
            prompt=test_case["prompt"],
            target_complexity=test_case["complexity"],
            style_preferences={
                "realism": "high",
                "detail_level": "moderate"
            },
            constraints={
                "max_objects": 10,
                "performance_target": "real_time"
            }
        )
        
        print(f"📝 **Prompt**: {test_case['prompt']}")
        print(f"🎯 **Target Complexity**: {test_case['complexity'].value}")
        
        # Execute planning
        try:
            print(f"\n⚙️ **Processing...**")
            response = await planner.execute(planner_input)
            
            if response.success:
                plan = response.plan
                print(f"✅ **Planning Successful!**")
                print(f"   Execution Time: {response.execution_time_ms:.2f}ms")
                print(f"   Generated Subtasks: {len(plan.subtasks)}")
                
                # Print plan summary
                print(f"\n📊 **Plan Summary**")
                print(f"   Plan ID: {plan.plan_id}")
                print(f"   Summary: {plan.summary}")
                print(f"   Tags: {', '.join(plan.tags)}")
                
                # Print detailed subtasks
                print(f"\n📋 **Detailed Subtasks ({len(plan.subtasks)} total)**")
                for subtask in plan.subtasks:
                    print_subtask_details(subtask)
                
                # Print execution plan
                print_execution_plan(plan)
                
                # Print planning rationale
                if response.planning_rationale:
                    print(f"\n🧠 **Planning Rationale**")
                    print(f"   {response.planning_rationale}")
                
                # Print additional data
                if response.data:
                    print(f"\n📈 **Analysis Data**")
                    for key, value in response.data.items():
                        print(f"   {key}: {value}")
                
            else:
                print(f"❌ **Planning Failed**: {response.message}")
                if response.errors:
                    for error in response.errors:
                        print(f"   Error: {error}")
                        
        except Exception as e:
            print(f"💥 **Exception during planning**: {e}")
            import traceback
            traceback.print_exc()
        
        # Print agent health status
        health = planner.get_health_status()
        print(f"\n🏥 **Agent Health Status**")
        print(f"   Status: {health['status']}")
        print(f"   Executions: {health['execution_count']}")
        print(f"   Error Rate: {health['error_rate']:.2%}")
        print(f"   Avg Execution Time: {health['avg_execution_time_ms']:.2f}ms")
        
        print("\n" + "-"*80)
        await asyncio.sleep(1)  # Brief pause between tests
    
    # Final agent statistics
    print_separator("FINAL AGENT STATISTICS")
    final_health = planner.get_health_status()
    print(f"📊 **Overall Performance**")
    print(f"   Total Executions: {final_health['execution_count']}")
    print(f"   Total Errors: {final_health['error_count']}")
    print(f"   Success Rate: {(1 - final_health['error_rate']):.2%}")
    print(f"   Average Execution Time: {final_health['avg_execution_time_ms']:.2f}ms")
    
    # Test health check
    print(f"\n🏥 **Health Check**")
    is_healthy = await planner.health_check()
    print(f"   Agent Health: {'✅ Healthy' if is_healthy else '❌ Unhealthy'}")
    
    print_separator("DEMO COMPLETED")
    print("✅ Planner Agent successfully demonstrated prompt decomposition!")
    print("🚀 Ready for integration with Coordinator Agent")

if __name__ == "__main__":
    print("🚀 Starting Simplified Planner Agent Demo")
    
    # Run main demo
    asyncio.run(test_planner_agent())
    
    print("\n🎉 Demo completed successfully!")
    print("📝 The Planner Agent is ready for integration with the multi-agent pipeline!")
