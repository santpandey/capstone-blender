"""
Test just the models to ensure they're working correctly
"""

def test_models():
    """Test model creation and validation"""
    print("🧪 Testing Models Only")
    print("="*40)
    
    try:
        # Test imports
        print("📦 Testing imports...")
        from agents.models import (
            GeneratedScript, ValidationResult, 
            PlannerInput, CoordinatorInput, CoderInput, QAInput,
            TaskPlan, SubTask, TaskType, TaskComplexity, TaskPriority
        )
        print("   ✅ All models imported successfully")
        
        # Test GeneratedScript creation
        print("\n🔧 Testing GeneratedScript creation...")
        script = GeneratedScript(
            script_id="test_script_123",
            plan_id="test_plan_456", 
            python_code="print('Hello Blender')",
            api_calls_count=5,
            estimated_execution_time_seconds=10.0,
            dependencies=["bpy", "bmesh"],
            created_objects_estimate=2,
            export_formats=["gltf"],
            validation_passed=True,
            validation_warnings=[]
        )
        print(f"   ✅ GeneratedScript created: {script.script_id}")
        print(f"   Code length: {len(script.python_code)} chars")
        
        # Test ValidationResult creation
        print("\n✅ Testing ValidationResult creation...")
        validation = ValidationResult(
            is_valid=True,
            confidence_score=0.85,
            issues_found=["Minor style issue"],
            suggestions=["Add more comments"],
            quality_metrics={"overall": 0.85, "syntax": 0.95}
        )
        print(f"   ✅ ValidationResult created: valid={validation.is_valid}")
        
        # Test SubTask creation
        print("\n📋 Testing SubTask creation...")
        subtask = SubTask(
            task_id="test_task_001",
            type=TaskType.CREATE_OBJECT,
            title="Create a cube",
            description="Add a basic cube to the scene",
            requirements=["Basic mesh operations"],
            dependencies=[],
            estimated_time_minutes=5,
            complexity=TaskComplexity.SIMPLE,
            priority=TaskPriority.HIGH,
            mesh_operations=["add_cube"],
            object_count=1,
            context={"size": "medium"}
        )
        print(f"   ✅ SubTask created: {subtask.title}")
        
        # Test TaskPlan creation
        print("\n📊 Testing TaskPlan creation...")
        plan = TaskPlan(
            plan_id="test_plan_789",
            original_prompt="Create a simple cube",
            summary="Simple cube creation plan",
            subtasks=[subtask],
            total_estimated_time=5,
            overall_complexity=TaskComplexity.SIMPLE,
            execution_order=["test_task_001"],
            parallel_groups=[["test_task_001"]]
        )
        print(f"   ✅ TaskPlan created: {plan.plan_id}")
        
        print("\n🎉 **ALL MODEL TESTS PASSED!**")
        print("✅ Models are working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Model test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_models()
    if success:
        print("\n🚀 Models are ready for pipeline testing!")
    else:
        print("\n🔧 Models need fixing before pipeline can work")
