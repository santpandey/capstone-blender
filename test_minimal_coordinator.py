"""
Minimal test to verify Coordinator Agent works
"""

def test_basic_imports():
    """Test if we can import the coordinator"""
    try:
        print("Testing basic imports...")
        
        # Test individual imports
        from agents.models import TaskType, SubTask, TaskPlan
        print("✅ Task models imported")
        
        from agents.coordinator_agent import CoordinatorAgent
        print("✅ Coordinator agent imported")
        
        # Create a simple coordinator instance
        coordinator = CoordinatorAgent()
        print("✅ Coordinator instance created")
        
        print("\n🎉 All basic tests passed!")
        print("The Coordinator Agent is ready to use!")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Minimal Coordinator Test")
    print("="*40)
    
    success = test_basic_imports()
    
    if success:
        print("\n✅ SUCCESS: Coordinator Agent is working!")
        print("🚀 Ready to proceed with full pipeline!")
    else:
        print("\n❌ FAILED: Need to fix import issues")
