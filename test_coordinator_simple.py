"""
Simple test for Coordinator Agent to isolate import issues
"""

import asyncio
import sys
import traceback

def test_imports():
    """Test imports step by step"""
    print("🔍 Testing imports step by step...")
    
    try:
        print("   1. Testing basic imports...")
        from pydantic import BaseModel
        print("   ✅ Pydantic import successful")
        
        print("   2. Testing agents.models...")
        from agents.models import TaskType, TaskComplexity, TaskPriority
        print("   ✅ Basic models import successful")
        
        print("   3. Testing SubTask...")
        from agents.models import SubTask, TaskPlan
        print("   ✅ Task models import successful")
        
        print("   4. Testing agent models...")
        from agents.models import CoordinatorInput, CoordinatorOutput
        print("   ✅ Agent models import successful")
        
        print("   5. Testing base agent...")
        from agents.base_agent import BaseAgent
        print("   ✅ Base agent import successful")
        
        print("   6. Testing coordinator agent...")
        from agents.coordinator_agent import CoordinatorAgent
        print("   ✅ Coordinator agent import successful")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Import failed: {e}")
        traceback.print_exc()
        return False

async def test_basic_initialization():
    """Test basic coordinator initialization"""
    print("\n🚀 Testing basic initialization...")
    
    try:
        from agents.coordinator_agent import CoordinatorAgent
        
        coordinator = CoordinatorAgent()
        print("   ✅ Coordinator instance created")
        
        # Test initialization
        success = await coordinator.initialize()
        print(f"   Initialization result: {success}")
        
        if success:
            # Test health check
            health = await coordinator.health_check()
            print(f"   Health check: {health}")
        
        return success
        
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        traceback.print_exc()
        return False

async def main():
    """Run simple tests"""
    print("🧪 Simple Coordinator Agent Test")
    print("="*50)
    
    # Test imports first
    if not test_imports():
        print("❌ Import test failed - aborting")
        return
    
    print("✅ All imports successful!")
    
    # Test basic initialization
    success = await test_basic_initialization()
    
    if success:
        print("\n✅ Simple coordinator test passed!")
        print("🚀 Ready for full testing!")
    else:
        print("\n❌ Simple coordinator test failed")

if __name__ == "__main__":
    asyncio.run(main())
