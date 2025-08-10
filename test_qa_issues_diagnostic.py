"""
Diagnostic script to analyze QA Agent issues in detail
"""
import asyncio
from pathlib import Path

async def analyze_qa_issues():
    """Analyze what specific issues the QA Agent is detecting"""
    print("🔍 QA Agent Issues Diagnostic")
    print("="*50)
    
    try:
        # Import required modules
        from agents.planner_agent import PlannerAgent
        from agents.coordinator_agent import CoordinatorAgent
        from agents.coder_agent import CoderAgent
        from agents.qa_agent import QAAgent
        from agents.models import (
            PlannerInput, CoordinatorInput, CoderInput, QAInput
        )
        
        # Initialize agents
        print("📋 Initializing agents...")
        planner = PlannerAgent()
        coordinator = CoordinatorAgent()
        coder = CoderAgent()
        qa = QAAgent()
        
        # Test prompt
        test_prompt = "Create an old man sitting on a wooden chair in his room with lighting at 30 degrees from his head"
        
        # Step 1: Planning
        print(f"\n🧠 Step 1: Planning")
        planner_input = PlannerInput(prompt=test_prompt)
        plan_result = await planner.process(planner_input)
        plan = plan_result.plan
        
        # Step 2: Coordination
        print(f"\n🎯 Step 2: Coordination")
        coordinator_input = CoordinatorInput(
            plan=plan,
            available_servers=["mesh_operators", "object_operators", "material_operators"]
        )
        coord_result = await coordinator.process(coordinator_input)
        
        # Step 3: Code Generation
        print(f"\n💻 Step 3: Code Generation")
        coder_input = CoderInput(
            plan=plan,
            api_mappings=coord_result.api_mappings
        )
        coder_result = await coder.process(coder_input)
        generated_script = coder_result.generated_script
        
        # Step 4: QA Analysis with detailed issue tracking
        print(f"\n🔍 Step 4: Detailed QA Analysis")
        qa_input = QAInput(
            generated_script=generated_script,
            original_plan=plan,
            execution_context={}
        )
        
        # Manually call QA validation methods to get detailed breakdown
        print("\n📊 **Detailed Issue Analysis:**")
        
        # 1. Script validation
        script_validation = await qa._validate_generated_script(generated_script, plan)
        print(f"\n1️⃣ **Script Structure Issues:**")
        script_issues = script_validation.get("issues", [])
        if script_issues:
            for i, issue in enumerate(script_issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ No script structure issues")
        
        # 2. Requirement analysis
        requirement_analysis = await qa._analyze_requirement_compliance(generated_script, plan, {})
        print(f"\n2️⃣ **Requirement Compliance Issues:**")
        req_issues = requirement_analysis.get("missing_requirements", [])
        if req_issues:
            for i, issue in enumerate(req_issues, 1):
                print(f"   {i}. Missing: {issue}")
        else:
            print("   ✅ No requirement compliance issues")
        
        # 3. Code quality
        code_quality = await qa._assess_code_quality(generated_script)
        print(f"\n3️⃣ **Code Quality Issues:**")
        quality_issues = code_quality.get("issues", [])
        if quality_issues:
            for i, issue in enumerate(quality_issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("   ✅ No code quality issues")
        
        # 4. API validation
        api_validation = await qa._validate_api_usage(generated_script)
        print(f"\n4️⃣ **API Usage Issues:**")
        deprecated_apis = api_validation.get("deprecated_apis", [])
        risky_operations = api_validation.get("risky_operations", [])
        
        if deprecated_apis:
            print(f"   📛 Deprecated APIs ({len(deprecated_apis)}):")
            for i, api in enumerate(deprecated_apis, 1):
                print(f"      {i}. {api}")
        
        if risky_operations:
            print(f"   ⚠️ Risky Operations ({len(risky_operations)}):")
            for i, op in enumerate(risky_operations, 1):
                print(f"      {i}. {op}")
        
        if not deprecated_apis and not risky_operations:
            print("   ✅ No API usage issues")
        
        # Calculate total issues
        all_issues = []
        all_issues.extend(script_issues)
        all_issues.extend(req_issues)
        all_issues.extend(quality_issues)
        all_issues.extend([f"Deprecated API: {api}" for api in deprecated_apis])
        all_issues.extend([f"Risky operation: {op}" for op in risky_operations])
        
        print(f"\n📈 **Issue Summary:**")
        print(f"   Total Issues Found: {len(all_issues)}")
        print(f"   Current Threshold: < 5 issues")
        print(f"   Validation Status: {'✅ PASS' if len(all_issues) < 5 else '❌ FAIL'}")
        
        print(f"\n📋 **All Issues List:**")
        if all_issues:
            for i, issue in enumerate(all_issues, 1):
                print(f"   {i:2d}. {issue}")
        else:
            print("   ✅ No issues found!")
        
        # Show scores
        print(f"\n📊 **Validation Scores:**")
        print(f"   Script Structure: {script_validation.get('score', 0):.3f}")
        print(f"   Requirement Match: {requirement_analysis.get('requirement_match_score', 0):.3f}")
        print(f"   Code Quality (Maintainability): {code_quality.get('maintainability_score', 0):.3f}")
        print(f"   API Correctness: {api_validation.get('score', 0):.3f}")
        
        # Recommendation
        print(f"\n💡 **Recommendation:**")
        if len(all_issues) < 5:
            print("   ✅ Current threshold (< 5) is appropriate")
        elif len(all_issues) < 10:
            print("   🔧 Consider increasing threshold to < 10 (issues seem minor)")
        else:
            print("   ⚠️ Many issues found - review script generation logic")
        
        return len(all_issues), all_issues
        
    except Exception as e:
        print(f"❌ Diagnostic failed: {e}")
        import traceback
        traceback.print_exc()
        return None, []

if __name__ == "__main__":
    asyncio.run(analyze_qa_issues())
