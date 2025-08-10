"""
QA Agent - Validates generated 3D assets and provides feedback
Fourth agent in the multi-agent pipeline for 3D asset generation
"""

import asyncio
import time
import logging
import json
import base64
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from datetime import datetime

from .base_agent import BaseAgent
from .models import (
    AgentType, AgentStatus, AgentResponse,
    QAInput, QAOutput, ValidationResult,
    GeneratedScript, TaskPlan, SubTask, TaskType
)

class QAAgent(BaseAgent):
    """
    QA Agent that validates generated 3D assets and provides feedback
    
    Key responsibilities:
    1. Validate generated Python scripts for correctness
    2. Analyze rendered 3D assets for quality
    3. Compare results against original requirements
    4. Identify issues and suggest corrections
    5. Provide confidence scores for validation
    6. Generate improvement recommendations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.QA,
            name="qa_agent",
            config=config or {}
        )
        
        # Validation criteria weights
        self.validation_weights = {
            "script_syntax": 0.2,
            "api_correctness": 0.25,
            "requirement_match": 0.25,
            "asset_quality": 0.15,
            "performance": 0.1,
            "maintainability": 0.05
        }
        
        # Quality thresholds
        self.quality_thresholds = {
            "excellent": 0.9,
            "good": 0.75,
            "acceptable": 0.6,
            "poor": 0.4
        }
        
        # Common issues and their severity
        self.issue_severity = {
            "syntax_error": "critical",
            "missing_api": "high",
            "parameter_mismatch": "medium",
            "performance_issue": "low",
            "style_violation": "low"
        }
        
        # Asset quality metrics
        self.quality_metrics = [
            "geometry_completeness",
            "topology_quality", 
            "material_application",
            "lighting_setup",
            "scene_composition",
            "export_compatibility"
        ]
        
        # Validation metrics
        self.validation_metrics = []
        self._initialized = True
    
    async def process(self, input_data: QAInput) -> QAOutput:
        """Process QA request and validate generated assets"""
        
        try:
            self.logger.info(f"Starting QA validation for script: {input_data.generated_script.script_id}")
            
            start_time = time.time()
            
            # Step 1: Validate generated script
            script_validation = await self._validate_generated_script(
                input_data.generated_script,
                input_data.original_plan
            )
            
            # Step 2: Analyze requirement compliance
            requirement_analysis = await self._analyze_requirement_compliance(
                input_data.generated_script,
                input_data.original_plan,
                input_data.execution_context
            )
            
            # Step 3: Assess code quality and maintainability
            code_quality = await self._assess_code_quality(input_data.generated_script)
            
            # Step 4: Validate API usage patterns
            api_validation = await self._validate_api_usage(input_data.generated_script)
            
            # Step 5: Generate overall validation result
            overall_validation = self._generate_overall_validation(
                script_validation,
                requirement_analysis,
                code_quality,
                api_validation
            )
            
            # Step 6: Generate improvement suggestions
            improvement_suggestions = self._generate_improvement_suggestions(
                script_validation,
                requirement_analysis,
                code_quality,
                api_validation
            )
            
            validation_time = (time.time() - start_time) * 1000
            
            return QAOutput(
                agent_type=AgentType.QA,
                status=AgentStatus.COMPLETED,
                success=True,
                message=f"QA validation completed with {overall_validation.confidence_score:.2f} confidence",
                data={
                    "validation_time_ms": validation_time,
                    "script_validation": script_validation,
                    "requirement_analysis": requirement_analysis,
                    "code_quality": code_quality,
                    "api_validation": api_validation
                },
                validation_result=overall_validation,
                improvement_suggestions=improvement_suggestions,
                confidence_score=overall_validation.confidence_score
            )
            
        except Exception as e:
            self.logger.error(f"QA validation failed: {e}")
            return QAOutput(
                agent_type=AgentType.QA,
                status=AgentStatus.FAILED,
                success=False,
                message=f"QA validation failed: {str(e)}",
                errors=[str(e)]
            )
    
    async def _validate_generated_script(
        self, 
        script: GeneratedScript, 
        plan: TaskPlan
    ) -> Dict[str, Any]:
        """Validate the generated Python script"""
        
        validation = {
            "syntax_valid": False,
            "imports_complete": False,
            "structure_valid": False,
            "error_handling_present": False,
            "logging_implemented": False,
            "issues": [],
            "score": 0.0
        }
        
        script_code = script.python_code
        
        # 1. Syntax validation
        try:
            compile(script_code, '<generated_script>', 'exec')
            validation["syntax_valid"] = True
            validation["score"] += 0.3
        except SyntaxError as e:
            validation["issues"].append(f"Syntax error: {str(e)}")
        
        # 2. Import completeness
        required_imports = ["import bpy", "import bmesh", "import mathutils"]
        imports_found = sum(1 for imp in required_imports if imp in script_code)
        validation["imports_complete"] = imports_found == len(required_imports)
        validation["score"] += (imports_found / len(required_imports)) * 0.2
        
        # 3. Structure validation
        required_structures = [
            "class BlenderScriptExecutor",
            "def execute_plan",
            "def setup_scene",
            "def safe_execute_api"
        ]
        structures_found = sum(1 for struct in required_structures if struct in script_code)
        validation["structure_valid"] = structures_found >= 3
        validation["score"] += (structures_found / len(required_structures)) * 0.2
        
        # 4. Error handling
        error_patterns = ["try:", "except", "self.log_error"]
        error_handling_count = sum(1 for pattern in error_patterns if pattern in script_code)
        validation["error_handling_present"] = error_handling_count >= 2
        validation["score"] += min(error_handling_count / 5, 0.15)
        
        # 5. Logging implementation
        logging_patterns = ["self.log_info", "logger.info", "logging."]
        logging_count = sum(1 for pattern in logging_patterns if pattern in script_code)
        validation["logging_implemented"] = logging_count >= 3
        validation["score"] += min(logging_count / 10, 0.15)
        
        # Check for common issues
        if "bpy.ops.object.delete(use_global=False)" not in script_code:
            validation["issues"].append("Missing safe object deletion")
        
        if "bpy.context.view_layer.update()" not in script_code:
            validation["issues"].append("Missing scene update calls")
        
        return validation
    
    async def _analyze_requirement_compliance(
        self,
        script: GeneratedScript,
        plan: TaskPlan,
        execution_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how well the script meets original requirements"""
        
        analysis = {
            "subtasks_covered": 0,
            "total_subtasks": len(plan.subtasks),
            "requirement_match_score": 0.0,
            "missing_requirements": [],
            "extra_features": [],
            "complexity_appropriate": False
        }
        
        script_code = script.python_code
        
        # Check subtask coverage
        for subtask in plan.subtasks:
            method_name = f"execute_{subtask.task_id.replace('-', '_')}"
            if method_name in script_code:
                analysis["subtasks_covered"] += 1
            else:
                analysis["missing_requirements"].append(f"Missing implementation for: {subtask.title}")
        
        # Calculate requirement match score
        coverage_ratio = analysis["subtasks_covered"] / max(analysis["total_subtasks"], 1)
        analysis["requirement_match_score"] = coverage_ratio
        
        # Check task type specific requirements
        task_types = set(subtask.type for subtask in plan.subtasks)
        
        for task_type in task_types:
            if task_type == TaskType.CREATE_CHARACTER:
                if "character" not in script_code.lower() and "human" not in script_code.lower():
                    analysis["missing_requirements"].append("Character creation not explicitly handled")
            
            elif task_type == TaskType.LIGHTING_SETUP:
                if "light" not in script_code.lower() and "lamp" not in script_code.lower():
                    analysis["missing_requirements"].append("Lighting setup not found in script")
            
            elif task_type == TaskType.MATERIAL_APPLICATION:
                if "material" not in script_code.lower() and "shader" not in script_code.lower():
                    analysis["missing_requirements"].append("Material application not found in script")
        
        # Check complexity appropriateness
        estimated_complexity = sum(1 for subtask in plan.subtasks if subtask.complexity.value in ["complex", "expert"])
        script_complexity_indicators = script_code.count("def ") + script_code.count("class ")
        analysis["complexity_appropriate"] = script_complexity_indicators >= estimated_complexity
        
        return analysis
    
    async def _assess_code_quality(self, script: GeneratedScript) -> Dict[str, Any]:
        """Assess code quality and maintainability"""
        
        quality = {
            "readability_score": 0.0,
            "maintainability_score": 0.0,
            "performance_score": 0.0,
            "documentation_score": 0.0,
            "best_practices_score": 0.0,
            "issues": []
        }
        
        script_code = script.python_code
        lines = script_code.split('\n')
        
        # 1. Readability assessment
        comment_lines = len([l for l in lines if l.strip().startswith('#') or '"""' in l])
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
        
        if code_lines > 0:
            comment_ratio = comment_lines / code_lines
            quality["readability_score"] = min(comment_ratio * 2, 1.0)
        
        # 2. Maintainability
        function_count = script_code.count('def ')
        class_count = script_code.count('class ')
        
        # Good modularization indicates maintainability
        if function_count >= 5 and class_count >= 1:
            quality["maintainability_score"] = 0.8
        elif function_count >= 3:
            quality["maintainability_score"] = 0.6
        else:
            quality["maintainability_score"] = 0.3
        
        # 3. Performance considerations
        performance_indicators = [
            "bpy.context.view_layer.update()",
            "bpy.ops.object.select_all(action='DESELECT')",
            "use_selection=True"
        ]
        performance_count = sum(1 for indicator in performance_indicators if indicator in script_code)
        quality["performance_score"] = min(performance_count / len(performance_indicators), 1.0)
        
        # 4. Documentation
        docstring_count = script_code.count('"""')
        method_count = script_code.count('def ')
        if method_count > 0:
            quality["documentation_score"] = min(docstring_count / (method_count * 2), 1.0)
        
        # 5. Best practices
        best_practices = [
            "try:" in script_code,  # Error handling
            "logging" in script_code,  # Logging
            "if __name__ == \"__main__\":" in script_code,  # Main guard
            "self." in script_code  # Object-oriented approach
        ]
        quality["best_practices_score"] = sum(best_practices) / len(best_practices)
        
        # Identify issues
        if quality["readability_score"] < 0.3:
            quality["issues"].append("Insufficient comments and documentation")
        
        if quality["performance_score"] < 0.5:
            quality["issues"].append("Missing performance optimizations")
        
        if "global " in script_code:
            quality["issues"].append("Use of global variables detected")
        
        return quality
    
    async def _validate_api_usage(self, script: GeneratedScript) -> Dict[str, Any]:
        """Validate Blender API usage patterns"""
        
        validation = {
            "api_calls_valid": True,
            "parameter_usage_correct": True,
            "context_handling_proper": True,
            "deprecated_apis": [],
            "risky_operations": [],
            "score": 0.0
        }
        
        script_code = script.python_code
        
        # Check for deprecated or risky API usage
        deprecated_patterns = [
            "bpy.ops.object.delete()",  # Should use use_global=False
            "bpy.ops.mesh.select_all()",  # Should specify action
            "bpy.context.scene.objects.active"  # Deprecated in 2.8+
        ]
        
        for pattern in deprecated_patterns:
            if pattern in script_code:
                validation["deprecated_apis"].append(pattern)
                validation["api_calls_valid"] = False
        
        # Check for risky operations
        risky_patterns = [
            "bpy.ops.wm.quit_blender()",
            "bpy.ops.wm.save_mainfile()",
            "import os; os.system"
        ]
        
        for pattern in risky_patterns:
            if pattern in script_code:
                validation["risky_operations"].append(pattern)
        
        # Check context handling
        context_checks = [
            "bpy.context.mode" in script_code,
            "bpy.context.active_object" in script_code,
            "bpy.context.selected_objects" in script_code
        ]
        validation["context_handling_proper"] = any(context_checks)
        
        # Calculate score
        score = 1.0
        score -= len(validation["deprecated_apis"]) * 0.2
        score -= len(validation["risky_operations"]) * 0.3
        if not validation["context_handling_proper"]:
            score -= 0.1
        
        validation["score"] = max(score, 0.0)
        
        return validation
    
    def _generate_overall_validation(
        self,
        script_validation: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        code_quality: Dict[str, Any],
        api_validation: Dict[str, Any]
    ) -> ValidationResult:
        """Generate overall validation result"""
        
        # Calculate weighted score
        weighted_score = (
            script_validation["score"] * self.validation_weights["script_syntax"] +
            requirement_analysis["requirement_match_score"] * self.validation_weights["requirement_match"] +
            api_validation["score"] * self.validation_weights["api_correctness"] +
            code_quality["maintainability_score"] * self.validation_weights["maintainability"] +
            code_quality["performance_score"] * self.validation_weights["performance"]
        )
        
        # Collect all issues
        all_issues = []
        all_issues.extend(script_validation.get("issues", []))
        all_issues.extend(requirement_analysis.get("missing_requirements", []))
        all_issues.extend(code_quality.get("issues", []))
        all_issues.extend([f"Deprecated API: {api}" for api in api_validation.get("deprecated_apis", [])])
        all_issues.extend([f"Risky operation: {op}" for op in api_validation.get("risky_operations", [])])
        

        
        # Generate suggestions
        suggestions = []
        
        if script_validation["score"] < 0.7:
            suggestions.append("Improve script structure and error handling")
        
        if requirement_analysis["requirement_match_score"] < 0.8:
            suggestions.append("Ensure all subtasks are properly implemented")
        
        if code_quality["documentation_score"] < 0.5:
            suggestions.append("Add more comprehensive documentation and comments")
        
        if api_validation["score"] < 0.8:
            suggestions.append("Review and update API usage patterns")
        
        # Determine quality level (convert to numeric score)
        quality_level_score = 0.0
        for level, threshold in sorted(self.quality_thresholds.items(), key=lambda x: x[1], reverse=True):
            if weighted_score >= threshold:
                quality_level_score = threshold
                break
        
        # Determine if validation passes
        is_valid = weighted_score >= self.quality_thresholds["acceptable"] and len(all_issues) < 5
        
        # Calculate quality metrics (all numeric values)
        quality_metrics = {
            "overall_score": weighted_score,
            "quality_level_score": quality_level_score,
            "script_completeness": requirement_analysis["requirement_match_score"],
            "code_maintainability": code_quality["maintainability_score"],
            "api_correctness": api_validation["score"],
            "documentation_quality": code_quality["documentation_score"]
        }
        
        return ValidationResult(
            is_valid=is_valid,
            confidence_score=weighted_score,
            issues_found=all_issues,
            suggestions=suggestions,
            quality_metrics=quality_metrics
        )
    
    def _generate_improvement_suggestions(
        self,
        script_validation: Dict[str, Any],
        requirement_analysis: Dict[str, Any],
        code_quality: Dict[str, Any],
        api_validation: Dict[str, Any]
    ) -> List[str]:
        """Generate specific improvement suggestions"""
        
        suggestions = []
        
        # Script-level improvements
        if not script_validation["syntax_valid"]:
            suggestions.append("Fix syntax errors in the generated script")
        
        if not script_validation["error_handling_present"]:
            suggestions.append("Add comprehensive error handling with try-catch blocks")
        
        if not script_validation["logging_implemented"]:
            suggestions.append("Implement proper logging for debugging and monitoring")
        
        # Requirement compliance improvements
        if requirement_analysis["requirement_match_score"] < 0.9:
            missing_count = len(requirement_analysis["missing_requirements"])
            suggestions.append(f"Implement {missing_count} missing requirement(s)")
        
        # Code quality improvements
        if code_quality["readability_score"] < 0.5:
            suggestions.append("Add more comments and documentation for better readability")
        
        if code_quality["maintainability_score"] < 0.6:
            suggestions.append("Refactor code into smaller, more modular functions")
        
        if code_quality["performance_score"] < 0.5:
            suggestions.append("Add performance optimizations like scene updates and object selection management")
        
        # API usage improvements
        if api_validation["deprecated_apis"]:
            suggestions.append("Replace deprecated API calls with modern alternatives")
        
        if api_validation["risky_operations"]:
            suggestions.append("Remove or secure risky operations that could affect system stability")
        
        if not api_validation["context_handling_proper"]:
            suggestions.append("Add proper Blender context checking and handling")
        
        # Priority-based suggestions
        high_priority = [s for s in suggestions if any(word in s.lower() for word in ["syntax", "error", "missing"])]
        medium_priority = [s for s in suggestions if s not in high_priority and any(word in s.lower() for word in ["deprecated", "performance"])]
        low_priority = [s for s in suggestions if s not in high_priority and s not in medium_priority]
        
        # Return prioritized suggestions
        return high_priority + medium_priority + low_priority
    
    async def validate_asset_quality(self, asset_path: str, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate 3D asset quality (placeholder for future multimodal validation)"""
        
        # This would be expanded to use computer vision/3D analysis
        # For now, return basic file-based validation
        
        validation = {
            "file_exists": Path(asset_path).exists() if asset_path else False,
            "format_valid": asset_path.endswith('.gltf') if asset_path else False,
            "size_reasonable": True,  # Would check file size
            "geometry_valid": True,   # Would analyze mesh quality
            "materials_applied": True, # Would check material presence
            "score": 0.8  # Placeholder score
        }
        
        return validation
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check of the QA agent"""
        
        return {
            "initialized": self._initialized,
            "validation_weights_configured": len(self.validation_weights) == 6,
            "quality_thresholds_set": len(self.quality_thresholds) == 4,
            "validation_count": len(self.validation_metrics)
        }
