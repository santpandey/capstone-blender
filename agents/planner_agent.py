"""
Planner Agent - Decomposes natural language prompts into structured subtasks
First agent in the multi-agent pipeline for 3D asset generation
"""

import re
import uuid
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .base_agent import BaseAgent
from .models import (
    AgentType, AgentStatus, AgentResponse,
    PlannerInput, PlannerOutput, TaskPlan, SubTask,
    TaskType, TaskComplexity, TaskPriority
)

class PlannerAgent(BaseAgent):
    """
    Planner Agent that decomposes natural language prompts into structured subtasks
    
    Key responsibilities:
    1. Parse natural language prompts for 3D modeling intent
    2. Identify objects, characters, environments, and relationships
    3. Break down complex requests into manageable subtasks
    4. Determine task dependencies and execution order
    5. Estimate complexity and time requirements
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            agent_type=AgentType.PLANNER,
            name="planner_agent",
            config=config or {}
        )
        
        # Initialize planning knowledge base
        self._init_planning_knowledge()
        
    def _init_planning_knowledge(self):
        """Initialize planning knowledge and semantic understanding"""
        
        # Semantic categories for intelligent task classification
        self.semantic_categories = {
            TaskType.CREATE_CHARACTER: {
                "keywords": ["person", "man", "woman", "child", "character", "human", "figure", "people", 
                           "animal", "dog", "cat", "bird", "creature", "monster", "dragon", "being", "entity"],
                "descriptors": ["living", "organic", "animated", "facial", "body", "limbs", "head", "torso"],
                "actions": ["walking", "running", "sitting", "standing", "moving", "breathing"],
                "context_clues": ["age", "gender", "species", "personality", "emotion"]
            },
            TaskType.CREATE_FURNITURE: {
                "keywords": ["chair", "table", "desk", "bed", "sofa", "couch", "furniture", "cabinet", 
                           "shelf", "drawer", "bench", "stool", "wardrobe", "bookshelf"],
                "descriptors": ["wooden", "metal", "comfortable", "ergonomic", "functional", "decorative"],
                "actions": ["sitting", "lying", "resting", "storing", "supporting"],
                "context_clues": ["room", "indoor", "home", "office", "comfort"]
            },
            TaskType.CREATE_OBJECT: {
                "keywords": ["object", "item", "thing", "tool", "device", "gadget", "artifact", "prop",
                           "box", "sphere", "cube", "cylinder", "cone", "pyramid"],
                "descriptors": ["geometric", "mechanical", "electronic", "simple", "complex", "functional"],
                "actions": ["create", "make", "build", "construct", "design", "model"],
                "context_clues": ["shape", "form", "structure", "utility", "purpose"]
            },
            TaskType.CREATE_CLOTHING: {
                "keywords": ["shirt", "pants", "dress", "clothing", "clothes", "hat", "shoes", "jacket",
                           "garment", "outfit", "uniform", "costume", "fabric", "textile"],
                "descriptors": ["wearable", "fashionable", "comfortable", "stylish", "protective"],
                "actions": ["wearing", "dressing", "covering", "protecting"],
                "context_clues": ["fashion", "style", "material", "fit", "size"]
            },
            TaskType.CREATE_ARCHITECTURE: {
                "keywords": ["room", "house", "building", "wall", "floor", "ceiling", "door", "window",
                           "structure", "architecture", "construction", "facility", "space"],
                "descriptors": ["architectural", "structural", "spatial", "interior", "exterior"],
                "actions": ["building", "constructing", "designing", "planning"],
                "context_clues": ["indoor", "outdoor", "residential", "commercial", "public"]
            },
            TaskType.CREATE_ENVIRONMENT: {
                "keywords": ["environment", "scene", "landscape", "background", "setting", "world",
                           "terrain", "nature", "forest", "city", "ocean", "mountain"],
                "descriptors": ["environmental", "atmospheric", "scenic", "natural", "urban"],
                "actions": ["exploring", "inhabiting", "surrounding", "encompassing"],
                "context_clues": ["location", "place", "area", "region", "atmosphere"]
            },
            TaskType.LIGHTING_SETUP: {
                "keywords": ["light", "lighting", "illumination", "lamp", "brightness", "shadow",
                           "glow", "shine", "beam", "ray", "sun", "moon", "fire"],
                "descriptors": ["bright", "dim", "warm", "cool", "harsh", "soft", "dramatic"],
                "actions": ["illuminating", "shining", "glowing", "casting", "reflecting"],
                "context_clues": ["visibility", "mood", "atmosphere", "time", "weather"]
            },
            TaskType.MATERIAL_APPLICATION: {
                "keywords": ["material", "texture", "color", "surface", "fabric", "wood", "metal", "glass",
                           "plastic", "stone", "leather", "rubber", "paint", "finish"],
                "descriptors": ["smooth", "rough", "shiny", "matte", "transparent", "opaque"],
                "actions": ["applying", "coating", "covering", "finishing", "texturing"],
                "context_clues": ["appearance", "feel", "quality", "aesthetic", "realistic"]
            },
            TaskType.SCENE_COMPOSITION: {
                "keywords": ["pose", "position", "posture", "arrangement", "composition", "layout",
                           "placement", "orientation", "angle", "perspective"],
                "descriptors": ["positioned", "arranged", "composed", "balanced", "centered"],
                "actions": ["sitting", "standing", "lying", "leaning", "positioning", "arranging"],
                "context_clues": ["spatial", "relationship", "interaction", "proximity", "relative"]
            },
            TaskType.ANIMATION_SETUP: {
                "keywords": ["animation", "movement", "motion", "animate", "sequence", "timeline",
                           "keyframe", "transition", "dynamic", "kinetic"],
                "descriptors": ["moving", "animated", "dynamic", "fluid", "smooth", "realistic"],
                "actions": ["moving", "animating", "transitioning", "flowing", "changing"],
                "context_clues": ["time", "sequence", "progression", "change", "evolution"]
            }
        }
        
        # Intent detection patterns for fallback
        self.intent_patterns = {
            "create": [TaskType.CREATE_OBJECT, TaskType.CREATE_CHARACTER],
            "make": [TaskType.CREATE_OBJECT, TaskType.CREATE_FURNITURE],
            "design": [TaskType.CREATE_ARCHITECTURE, TaskType.CREATE_ENVIRONMENT],
            "build": [TaskType.CREATE_ARCHITECTURE, TaskType.CREATE_OBJECT],
            "model": [TaskType.CREATE_CHARACTER, TaskType.CREATE_OBJECT],
            "draw": [TaskType.CREATE_CHARACTER, TaskType.CREATE_OBJECT],
            "render": [TaskType.LIGHTING_SETUP, TaskType.MATERIAL_APPLICATION],
            "animate": [TaskType.ANIMATION_SETUP, TaskType.SCENE_COMPOSITION]
        }
        
        # Complexity indicators
        self.complexity_indicators = {
            TaskComplexity.SIMPLE: [
                'simple', 'basic', 'primitive', 'cube', 'sphere', 'cylinder',
                'single', 'one', 'minimal'
            ],
            TaskComplexity.MODERATE: [
                'detailed', 'realistic', 'textured', 'multiple', 'several',
                'character', 'furniture', 'room'
            ],
            TaskComplexity.COMPLEX: [
                'intricate', 'complex', 'advanced', 'professional', 'detailed scene',
                'multiple characters', 'full environment', 'architectural'
            ],
            TaskComplexity.EXPERT: [
                'photorealistic', 'cinematic', 'production-ready', 'highly detailed',
                'studio quality', 'professional grade', 'film quality'
            ]
        }
        
        # Time estimation base (in minutes)
        self.base_time_estimates = {
            TaskType.CREATE_CHARACTER: 45,
            TaskType.CREATE_OBJECT: 15,
            TaskType.CREATE_FURNITURE: 25,
            TaskType.CREATE_CLOTHING: 30,
            TaskType.CREATE_ARCHITECTURE: 60,
            TaskType.CREATE_ENVIRONMENT: 90,
            TaskType.SCENE_COMPOSITION: 20,
            TaskType.LIGHTING_SETUP: 15,
            TaskType.MATERIAL_APPLICATION: 10,
            TaskType.ANIMATION_SETUP: 40,
            TaskType.POST_PROCESSING: 10
        }
        
        # Complexity multipliers for time estimation
        self.complexity_multipliers = {
            TaskComplexity.SIMPLE: 0.5,
            TaskComplexity.MODERATE: 1.0,
            TaskComplexity.COMPLEX: 2.0,
            TaskComplexity.EXPERT: 4.0
        }
    
    async def process(self, input_data: PlannerInput) -> PlannerOutput:
        """Process the planning request and generate structured subtasks"""
        
        try:
            self.logger.info(f"Planning for prompt: {input_data.prompt[:100]}...")
            
            # Step 1: Analyze the prompt
            prompt_analysis = self._analyze_prompt(input_data.prompt)
            
            # Step 2: Extract entities and relationships
            entities = self._extract_entities(input_data.prompt)
            
            # Step 3: Generate subtasks
            subtasks = self._generate_subtasks(
                prompt_analysis, entities, input_data
            )
            
            # Step 4: Determine dependencies and execution order
            execution_plan = self._plan_execution_order(subtasks)
            
            # Step 5: Create the complete task plan
            task_plan = self._create_task_plan(
                input_data.prompt, subtasks, execution_plan, prompt_analysis
            )
            
            # Step 6: Generate alternative plans if requested
            alternative_plans = []
            if self.config.get('generate_alternatives', False):
                alternative_plans = self._generate_alternative_plans(task_plan)
            
            return PlannerOutput(
                agent_type=AgentType.PLANNER,
                status=AgentStatus.COMPLETED,
                success=True,
                message=f"Successfully generated plan with {len(subtasks)} subtasks",
                data={
                    "prompt_analysis": prompt_analysis,
                    "entities_found": len(entities),
                    "total_subtasks": len(subtasks)
                },
                plan=task_plan,
                alternative_plans=alternative_plans,
                planning_rationale=self._generate_rationale(prompt_analysis, subtasks)
            )
            
        except Exception as e:
            self.logger.error(f"Planning failed: {e}")
            return PlannerOutput(
                agent_type=AgentType.PLANNER,
                status=AgentStatus.FAILED,
                success=False,
                message=f"Planning failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _analyze_prompt(self, prompt: str) -> Dict[str, Any]:
        """Analyze the prompt to understand intent and requirements"""
        
        prompt_lower = prompt.lower()
        
        analysis = {
            "original_prompt": prompt,
            "word_count": len(prompt.split()),
            "entities": [],
            "actions": [],
            "descriptors": [],
            "spatial_relationships": [],
            "estimated_complexity": TaskComplexity.MODERATE,
            "primary_intent": "create_3d_asset"
        }
        
        # Extract descriptive words (adjectives, colors, materials)
        descriptors = re.findall(r'\b(old|young|large|small|big|tiny|red|blue|green|yellow|wooden|metal|glass|leather|fabric|smooth|rough|shiny|matte)\b', prompt_lower)
        analysis["descriptors"] = list(set(descriptors))
        
        # Extract actions and poses
        actions = re.findall(r'\b(sitting|standing|walking|running|holding|wearing|looking|contemplating|thinking|resting)\b', prompt_lower)
        analysis["actions"] = list(set(actions))
        
        # Extract spatial relationships
        spatial_words = re.findall(r'\b(on|in|under|above|below|beside|next to|behind|in front of|near|far from)\b', prompt_lower)
        analysis["spatial_relationships"] = list(set(spatial_words))
        
        # Determine complexity based on indicators
        complexity_scores = {}
        for complexity, indicators in self.complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in prompt_lower)
            complexity_scores[complexity] = score
        
        # Choose complexity with highest score
        if complexity_scores:
            analysis["estimated_complexity"] = max(complexity_scores, key=complexity_scores.get)
        
        return analysis
    
    def _extract_entities(self, prompt: str) -> List[Dict[str, Any]]:
        """Extract entities using intelligent semantic analysis"""
        
        entities = []
        prompt_lower = prompt.lower()
        words = prompt_lower.split()
        
        # Score each task type based on semantic relevance
        task_scores = {}
        for task_type, categories in self.semantic_categories.items():
            score = 0
            matched_terms = []
            
            # Check keywords (highest weight)
            for keyword in categories["keywords"]:
                if keyword in prompt_lower:
                    score += 3
                    matched_terms.append(("keyword", keyword))
            
            # Check descriptors (medium weight)
            for descriptor in categories["descriptors"]:
                if descriptor in prompt_lower:
                    score += 2
                    matched_terms.append(("descriptor", descriptor))
            
            # Check actions (medium weight)
            for action in categories["actions"]:
                if action in prompt_lower:
                    score += 2
                    matched_terms.append(("action", action))
            
            # Check context clues (lower weight)
            for clue in categories["context_clues"]:
                if clue in prompt_lower:
                    score += 1
                    matched_terms.append(("context", clue))
            
            if score > 0:
                task_scores[task_type] = {
                    "score": score,
                    "matched_terms": matched_terms,
                    "confidence": min(score / 10.0, 1.0)  # Normalize to 0-1
                }
        
        # Convert high-scoring task types to entities
        for task_type, data in task_scores.items():
            if data["confidence"] >= 0.3:  # Minimum confidence threshold
                # Find the most relevant matched term for positioning
                primary_term = data["matched_terms"][0][1] if data["matched_terms"] else ""
                start_pos = prompt_lower.find(primary_term) if primary_term else 0
                
                entity = {
                    "text": primary_term,
                    "start": start_pos,
                    "end": start_pos + len(primary_term),
                    "task_type": task_type,
                    "confidence": data["confidence"],
                    "matched_terms": data["matched_terms"],
                    "context": prompt[max(0, start_pos-20):start_pos+len(primary_term)+20]
                }
                entities.append(entity)
        
        # Fallback: Use intent patterns if no entities found
        if not entities:
            entities = self._extract_entities_by_intent(prompt_lower)
        
        # Fallback: Create generic object task if still no entities
        if not entities:
            entities = self._create_generic_entity(prompt)
        
        # Sort by confidence and position
        entities.sort(key=lambda x: (-x.get("confidence", 0), x.get("start", 0)))
        
        return entities
    
    def _extract_entities_by_intent(self, prompt_lower: str) -> List[Dict[str, Any]]:
        """Extract entities based on intent verbs when semantic analysis fails"""
        
        entities = []
        
        for intent_verb, possible_tasks in self.intent_patterns.items():
            if intent_verb in prompt_lower:
                # Choose the most likely task type based on context
                task_type = possible_tasks[0]  # Default to first option
                
                # Try to refine based on additional context
                if len(possible_tasks) > 1:
                    for possible_task in possible_tasks:
                        # Check if there are any weak indicators for this task
                        categories = self.semantic_categories[possible_task]
                        for keyword in categories["keywords"][:3]:  # Check top 3 keywords
                            if keyword in prompt_lower:
                                task_type = possible_task
                                break
                
                start_pos = prompt_lower.find(intent_verb)
                entity = {
                    "text": intent_verb,
                    "start": start_pos,
                    "end": start_pos + len(intent_verb),
                    "task_type": task_type,
                    "confidence": 0.5,  # Medium confidence for intent-based detection
                    "matched_terms": [("intent", intent_verb)],
                    "context": prompt_lower[max(0, start_pos-20):start_pos+len(intent_verb)+20]
                }
                entities.append(entity)
        
        return entities
    
    def _create_generic_entity(self, prompt: str) -> List[Dict[str, Any]]:
        """Create a generic entity when no specific entities are detected"""
        
        # Analyze prompt length and complexity to determine likely task type
        word_count = len(prompt.split())
        
        if word_count <= 3:
            # Very short prompts likely want simple objects
            task_type = TaskType.CREATE_OBJECT
        elif "scene" in prompt.lower() or word_count > 15:
            # Long prompts or scene mentions likely want environments
            task_type = TaskType.CREATE_ENVIRONMENT
        else:
            # Medium prompts default to object creation
            task_type = TaskType.CREATE_OBJECT
        
        return [{
            "text": "generic_3d_asset",
            "start": 0,
            "end": len(prompt),
            "task_type": task_type,
            "confidence": 0.3,  # Low confidence for generic detection
            "matched_terms": [("generic", "fallback")],
            "context": prompt[:50] + "..." if len(prompt) > 50 else prompt
        }]
    
    def _generate_subtasks(
        self, 
        prompt_analysis: Dict[str, Any], 
        entities: List[Dict[str, Any]], 
        input_data: PlannerInput
    ) -> List[SubTask]:
        """Generate subtasks based on prompt analysis and entities"""
        
        subtasks = []
        task_counter = 1
        
        # Group entities by task type
        entities_by_type = {}
        for entity in entities:
            task_type = entity["task_type"]
            if task_type not in entities_by_type:
                entities_by_type[task_type] = []
            entities_by_type[task_type].append(entity)
        
        # Generate subtasks for each entity type
        for task_type, entity_list in entities_by_type.items():
            
            if task_type == TaskType.CREATE_CHARACTER:
                subtask = self._create_character_subtask(
                    task_counter, entity_list, prompt_analysis
                )
                subtasks.append(subtask)
                task_counter += 1
                
            elif task_type == TaskType.CREATE_FURNITURE:
                for entity in entity_list:
                    subtask = self._create_furniture_subtask(
                        task_counter, entity, prompt_analysis
                    )
                    subtasks.append(subtask)
                    task_counter += 1
                    
            elif task_type == TaskType.CREATE_CLOTHING:
                subtask = self._create_clothing_subtask(
                    task_counter, entity_list, prompt_analysis
                )
                subtasks.append(subtask)
                task_counter += 1
                
            elif task_type == TaskType.LIGHTING_SETUP:
                subtask = self._create_lighting_subtask(
                    task_counter, entity_list, prompt_analysis
                )
                subtasks.append(subtask)
                task_counter += 1
        
        # Add scene composition if multiple objects
        if len(subtasks) > 1 or prompt_analysis.get("spatial_relationships"):
            composition_subtask = self._create_composition_subtask(
                task_counter, prompt_analysis, subtasks
            )
            subtasks.append(composition_subtask)
            task_counter += 1
        
        # Add material application if descriptors found
        if prompt_analysis.get("descriptors"):
            material_subtask = self._create_material_subtask(
                task_counter, prompt_analysis
            )
            subtasks.append(material_subtask)
            task_counter += 1
        
        return subtasks
    
    def _create_character_subtask(
        self,
        task_id: int, 
        entities: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> SubTask:
        """Create granular subtask for character creation with specific Blender operations"""
        
        entity_texts = [entity["text"] for entity in entities]
        descriptors = analysis.get("descriptors", [])
        actions = analysis.get("actions", [])
        
        # Determine if character is sitting (affects mesh operations)
        is_sitting = any(action in ["sitting"] for action in actions)
        
        # Create granular, Blender-specific requirements
        granular_requirements = [
            "add_cube_primitive_for_torso",
            "scale_torso_to_human_proportions", 
            "add_sphere_primitive_for_head",
            "position_head_above_torso",
            "add_cylinder_primitives_for_arms",
            "add_cylinder_primitives_for_legs",
        ]
        
        if is_sitting:
            granular_requirements.extend([
                "rotate_legs_90_degrees_for_sitting",
                "position_legs_for_chair_sitting",
                "adjust_torso_angle_for_sitting_posture"
            ])
        
        # Specific mesh operations that Coordinator can map to APIs
        specific_mesh_operations = [
            "mesh.primitive_cube_add",      # For torso
            "mesh.primitive_uv_sphere_add", # For head  
            "mesh.primitive_cylinder_add",  # For limbs
            "transform.resize",             # For scaling
            "transform.translate",          # For positioning
            "transform.rotate"              # For posing
        ]
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.CREATE_CHARACTER,
            title="Add Basic Human Mesh Primitives",
            description=f"Create basic human figure using Blender primitives: cube for torso, sphere for head, cylinders for limbs. {'Configure for sitting pose.' if is_sitting else 'Configure for standing pose.'}",
            requirements=granular_requirements,
            estimated_time_minutes=self._estimate_time(
                TaskType.CREATE_CHARACTER, analysis["estimated_complexity"]
            ),
            complexity=analysis["estimated_complexity"],
            priority=TaskPriority.HIGH,
            blender_categories=["mesh_operators", "object_operators"],
            mesh_operations=specific_mesh_operations,
            object_count=4,  # torso, head, 2 arms, 2 legs = 6, but simplified to 4 main parts
            context={
                "character_type": entity_texts[0] if entity_texts else "person",
                "descriptors": descriptors,
                "actions": actions,
                "pose_type": "sitting" if is_sitting else "standing",
                "primitive_approach": True,
                "specific_apis_needed": [
                    "bpy.ops.mesh.primitive_cube_add",
                    "bpy.ops.mesh.primitive_uv_sphere_add", 
                    "bpy.ops.mesh.primitive_cylinder_add",
                    "bpy.ops.transform.resize",
                    "bpy.ops.transform.translate",
                    "bpy.ops.transform.rotate"
                ]
            }
        )
    
    def _create_furniture_subtask(
        self, 
        task_id: int, 
        entity: Dict[str, Any], 
        analysis: Dict[str, Any]
    ) -> SubTask:
        """Create granular subtask for furniture creation with specific Blender operations"""
        
        furniture_type = entity["text"]
        descriptors = analysis.get("descriptors", [])
        
        # Create granular, Blender-specific requirements for chair
        if "chair" in furniture_type.lower():
            granular_requirements = [
                "add_cube_primitive_for_seat",
                "scale_seat_to_chair_proportions",
                "add_cube_primitive_for_backrest", 
                "position_backrest_behind_seat",
                "add_cylinder_primitives_for_legs",
                "position_four_legs_under_seat"
            ]
            specific_mesh_operations = [
                "mesh.primitive_cube_add",      # For seat and backrest
                "mesh.primitive_cylinder_add",  # For legs
                "transform.resize",             # For scaling parts
                "transform.translate",          # For positioning
                "object.duplicate"              # For creating multiple legs
            ]
        else:
            # Generic furniture approach
            granular_requirements = [
                "add_cube_primitive_for_base",
                "scale_base_to_furniture_proportions",
                "add_additional_structural_elements"
            ]
            specific_mesh_operations = [
                "mesh.primitive_cube_add",
                "transform.resize", 
                "transform.translate"
            ]
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.CREATE_FURNITURE,
            title=f"Add {furniture_type.title()} Using Mesh Primitives",
            description=f"Create {furniture_type} using Blender mesh primitives. {'Add seat, backrest, and 4 legs using cubes and cylinders.' if 'chair' in furniture_type.lower() else f'Create {furniture_type} structure using basic shapes.'}",
            requirements=granular_requirements,
            estimated_time_minutes=self._estimate_time(
                TaskType.CREATE_FURNITURE, analysis["estimated_complexity"]
            ),
            complexity=analysis["estimated_complexity"],
            priority=TaskPriority.MEDIUM,
            blender_categories=["mesh_operators", "object_operators"],
            mesh_operations=specific_mesh_operations,
            object_count=5 if "chair" in furniture_type.lower() else 1,  # seat + backrest + 4 legs = 6, simplified to 5
            context={
                "furniture_type": furniture_type,
                "descriptors": descriptors,
                "style": "realistic",
                "primitive_approach": True,
                "specific_apis_needed": [
                    "bpy.ops.mesh.primitive_cube_add",
                    "bpy.ops.mesh.primitive_cylinder_add",
                    "bpy.ops.transform.resize",
                    "bpy.ops.transform.translate",
                    "bpy.ops.object.duplicate"
                ]
            }
        )
    
    def _create_clothing_subtask(
        self, 
        task_id: int, 
        entities: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> SubTask:
        """Create subtask for clothing creation"""
        
        clothing_items = [e["text"] for e in entities]
        descriptors = analysis.get("descriptors", [])
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.CREATE_CLOTHING,
            title=f"Create Clothing: {', '.join(clothing_items)}",
            description=f"Create clothing items with properties: {', '.join(descriptors)}",
            requirements=[
                "character_base_mesh",
                "clothing_topology",
                "fabric_simulation"
            ],
            dependencies=["task_001"],  # Depends on character creation
            estimated_time_minutes=self._estimate_time(
                TaskType.CREATE_CLOTHING, analysis["estimated_complexity"]
            ),
            complexity=analysis["estimated_complexity"],
            priority=TaskPriority.MEDIUM,
            blender_categories=["mesh_operators", "geometry_nodes"],
            mesh_operations=["duplicate", "separate", "solidify", "cloth_simulation"],
            object_count=len(clothing_items),
            context={
                "clothing_items": clothing_items,
                "descriptors": descriptors,
                "fit_type": "realistic"
            }
        )
    
    def _create_lighting_subtask(
        self, 
        task_id: int, 
        entities: List[Dict[str, Any]], 
        analysis: Dict[str, Any]
    ) -> SubTask:
        """Create subtask for lighting setup"""
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.LIGHTING_SETUP,
            title="Setup Scene Lighting",
            description="Configure lighting for the scene with appropriate mood and visibility",
            requirements=[
                "scene_objects",
                "lighting_setup",
                "shadow_configuration"
            ],
            estimated_time_minutes=self._estimate_time(
                TaskType.LIGHTING_SETUP, analysis["estimated_complexity"]
            ),
            complexity=TaskComplexity.MODERATE,
            priority=TaskPriority.MEDIUM,
            blender_categories=["object_operators"],
            mesh_operations=["light_add", "sun_add", "area_light_add"],
            object_count=3,
            context={
                "lighting_type": "three_point",
                "mood": "natural",
                "shadows": True
            }
        )
    
    def _create_composition_subtask(
        self, 
        task_id: int, 
        analysis: Dict[str, Any], 
        existing_subtasks: List[SubTask]
    ) -> SubTask:
        """Create subtask for scene composition"""
        
        dependencies = [task.task_id for task in existing_subtasks]
        spatial_relationships = analysis.get("spatial_relationships", [])
        actions = analysis.get("actions", [])
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.SCENE_COMPOSITION,
            title="Compose Scene",
            description=f"Arrange objects and characters with relationships: {', '.join(spatial_relationships + actions)}",
            requirements=[
                "all_objects_created",
                "spatial_positioning",
                "pose_setup"
            ],
            dependencies=dependencies,
            estimated_time_minutes=self._estimate_time(
                TaskType.SCENE_COMPOSITION, analysis["estimated_complexity"]
            ),
            complexity=analysis["estimated_complexity"],
            priority=TaskPriority.HIGH,
            blender_categories=["object_operators"],
            mesh_operations=["transform", "rotate", "scale", "constraint_add"],
            object_count=0,  # Modifies existing objects
            context={
                "spatial_relationships": spatial_relationships,
                "actions": actions,
                "composition_style": "realistic"
            }
        )
    
    def _create_material_subtask(
        self, 
        task_id: int, 
        analysis: Dict[str, Any]
    ) -> SubTask:
        """Create subtask for material application"""
        
        descriptors = analysis.get("descriptors", [])
        
        return SubTask(
            task_id=f"task_{task_id:03d}",
            type=TaskType.MATERIAL_APPLICATION,
            title="Apply Materials and Textures",
            description=f"Apply materials with properties: {', '.join(descriptors)}",
            requirements=[
                "all_objects_created",
                "material_setup",
                "texture_application"
            ],
            estimated_time_minutes=self._estimate_time(
                TaskType.MATERIAL_APPLICATION, analysis["estimated_complexity"]
            ),
            complexity=analysis["estimated_complexity"],
            priority=TaskPriority.LOW,
            blender_categories=["shader_nodes"],
            mesh_operations=["material_new", "texture_add", "node_setup"],
            object_count=0,  # Applies to existing objects
            context={
                "material_types": descriptors,
                "style": "realistic",
                "pbr_workflow": True
            }
        )
    
    def _estimate_time(self, task_type: TaskType, complexity: TaskComplexity) -> int:
        """Estimate time for a subtask based on type and complexity"""
        
        base_time = self.base_time_estimates.get(task_type, 20)
        multiplier = self.complexity_multipliers.get(complexity, 1.0)
        
        return int(base_time * multiplier)
    
    def _plan_execution_order(self, subtasks: List[SubTask]) -> Dict[str, Any]:
        """Determine optimal execution order and parallel groups"""
        
        # Build dependency graph
        dependency_graph = {}
        for task in subtasks:
            dependency_graph[task.task_id] = task.dependencies
        
        # Topological sort for execution order
        execution_order = []
        remaining_tasks = set(task.task_id for task in subtasks)
        
        while remaining_tasks:
            # Find tasks with no remaining dependencies
            ready_tasks = []
            for task_id in remaining_tasks:
                deps = dependency_graph[task_id]
                if all(dep not in remaining_tasks for dep in deps):
                    ready_tasks.append(task_id)
            
            if not ready_tasks:
                # Circular dependency - break it
                ready_tasks = [list(remaining_tasks)[0]]
            
            # Add ready tasks to execution order
            execution_order.extend(ready_tasks)
            remaining_tasks -= set(ready_tasks)
        
        # Identify parallel groups (tasks that can run simultaneously)
        parallel_groups = []
        current_group = []
        
        for task_id in execution_order:
            task = next(t for t in subtasks if t.task_id == task_id)
            
            # Check if this task can run in parallel with current group
            can_parallel = True
            for group_task_id in current_group:
                group_task = next(t for t in subtasks if t.task_id == group_task_id)
                
                # Can't parallel if there's a dependency
                if (task_id in group_task.dependencies or 
                    group_task_id in task.dependencies):
                    can_parallel = False
                    break
                
                # Can't parallel if both modify the same object type
                if (task.type == group_task.type and 
                    task.type in [TaskType.CREATE_CHARACTER, TaskType.CREATE_FURNITURE]):
                    can_parallel = False
                    break
            
            if can_parallel and len(current_group) < 3:  # Max 3 parallel tasks
                current_group.append(task_id)
            else:
                if current_group:
                    parallel_groups.append(current_group)
                current_group = [task_id]
        
        if current_group:
            parallel_groups.append(current_group)
        
        return {
            "execution_order": execution_order,
            "parallel_groups": parallel_groups,
            "dependency_graph": dependency_graph
        }
    
    def _create_task_plan(
        self, 
        prompt: str, 
        subtasks: List[SubTask], 
        execution_plan: Dict[str, Any],
        analysis: Dict[str, Any]
    ) -> TaskPlan:
        """Create the complete task plan"""
        
        total_time = sum(task.estimated_time_minutes for task in subtasks)
        
        # Generate summary
        task_types = list(set(task.type for task in subtasks))
        summary = f"3D asset generation with {len(subtasks)} subtasks: {', '.join([t.value for t in task_types])}"
        
        # Generate tags
        tags = []
        tags.extend(analysis.get("descriptors", []))
        tags.extend([t.value for t in task_types])
        tags = list(set(tags))
        
        return TaskPlan(
            plan_id=str(uuid.uuid4()),
            original_prompt=prompt,
            summary=summary,
            subtasks=subtasks,
            total_estimated_time=total_time,
            overall_complexity=analysis["estimated_complexity"],
            tags=tags,
            execution_order=execution_plan["execution_order"],
            parallel_groups=execution_plan["parallel_groups"]
        )
    
    def _generate_alternative_plans(self, main_plan: TaskPlan) -> List[TaskPlan]:
        """Generate alternative plans with different approaches"""
        # For now, return empty list - can be enhanced later
        return []
    
    def _generate_rationale(
        self, 
        analysis: Dict[str, Any], 
        subtasks: List[SubTask]
    ) -> str:
        """Generate explanation of planning decisions"""
        
        rationale_parts = []
        
        # Complexity rationale
        complexity = analysis["estimated_complexity"]
        rationale_parts.append(
            f"Estimated complexity as {complexity.value} based on prompt analysis."
        )
        
        # Task breakdown rationale
        task_types = list(set(task.type for task in subtasks))
        rationale_parts.append(
            f"Identified {len(task_types)} main task categories: {', '.join([t.value for t in task_types])}."
        )
        
        # Dependencies rationale
        dependent_tasks = [t for t in subtasks if t.dependencies]
        if dependent_tasks:
            rationale_parts.append(
                f"Established dependencies for {len(dependent_tasks)} tasks to ensure proper execution order."
            )
        
        # Time estimation rationale
        total_time = sum(task.estimated_time_minutes for task in subtasks)
        rationale_parts.append(
            f"Total estimated time: {total_time} minutes based on task complexity and type."
        )
        
        return " ".join(rationale_parts)
