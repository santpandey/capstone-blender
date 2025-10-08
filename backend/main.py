"""
FastAPI Backend for 3D Asset Generation
Integrates with the existing multi-agent pipeline
"""

import asyncio
import os
import uuid
import tempfile
import subprocess
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional
import shutil

# --- START OF SETUP BLOCK ---

# 1. Add project root and backend directory to the Python path
# This ensures that all local modules can be found
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / 'backend'))

# 2. Load environment variables from the .env file in the project root
from dotenv import load_dotenv
dotenv_path = project_root / '.env'
load_dotenv(dotenv_path=dotenv_path)

# 3. Configure logging to see output from all agents
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

# --- END OF SETUP BLOCK ---

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import uvicorn

from .monitoring import monitor

# Import existing pipeline components
from agents import (
    PlannerAgent, CoordinatorAgent, CoderAgent, QAAgent,
    PlannerInput, CoordinatorInput, CoderInput, QAInput,
    AgentStatus
)

app = FastAPI(
    title="3D Asset Generator API",
    description="AI-powered 3D asset generation using Blender automation",
    version="1.0.0"
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response models
class GenerateRequest(BaseModel):
    prompt: str
    style_preferences: Optional[Dict[str, Any]] = None

class GenerateResponse(BaseModel):
    success: bool
    job_id: Optional[str] = None
    message: str
    model_url: Optional[str] = None
    status: str = "pending"

class StatusResponse(BaseModel):
    status: str  # pending, processing, completed, failed
    message: str
    model_url: Optional[str] = None
    progress: Optional[int] = None

# Global storage for job status
job_status: Dict[str, Dict[str, Any]] = {}

# Directories
MODELS_DIR = Path("generated_models")
SCRIPTS_DIR = Path("generated_scripts")
MODELS_DIR.mkdir(exist_ok=True)
SCRIPTS_DIR.mkdir(exist_ok=True)

@app.get("/")
async def root():
    return {"message": "3D Asset Generator API", "status": "running"}

@app.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    return monitor.get_health_status()

@app.get("/metrics")
async def get_metrics():
    """Get system and application metrics"""
    return {
        "system": monitor.get_system_metrics(),
        "application": monitor.get_application_metrics()
    }

@app.post("/generate", response_model=GenerateResponse)
async def generate_asset(
    request: GenerateRequest,
    background_tasks: BackgroundTasks
):
    """Generate 3D asset from text prompt"""
    
    if not request.prompt.strip():
        raise HTTPException(status_code=400, detail="Prompt cannot be empty")
    
    # Generate unique job ID
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    job_status[job_id] = {
        "status": "pending",
        "message": "Job created",
        "progress": 0,
        "model_url": None,
        "error": None
    }
    
    # Start background task
    background_tasks.add_task(
        process_generation_request,
        job_id,
        request.prompt,
        request.style_preferences or {}
    )
    
    return GenerateResponse(
        success=True,
        job_id=job_id,
        message="Generation started",
        status="pending"
    )

@app.get("/status/{job_id}", response_model=StatusResponse)
async def get_status(job_id: str):
    """Get generation status"""
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    
    return StatusResponse(
        status=status["status"],
        message=status["message"],
        model_url=status["model_url"],
        progress=status.get("progress", 0)
    )

@app.get("/download/{job_id}")
async def download_model(job_id: str):
    """Download generated GLB file"""
    
    if job_id not in job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    status = job_status[job_id]
    
    if status["status"] != "completed" or not status["model_url"]:
        raise HTTPException(status_code=400, detail="Model not ready")
    
    model_path = MODELS_DIR / f"{job_id}.glb"
    
    if not model_path.exists():
        raise HTTPException(status_code=404, detail="Model file not found")
    
    return FileResponse(
        path=model_path,
        media_type="application/octet-stream",
        filename=f"generated_model_{job_id}.glb"
    )

async def process_generation_request(
    job_id: str,
    prompt: str,
    style_preferences: Dict[str, Any]
):
    """Background task to process generation request"""
    
    try:
        # Update status
        job_status[job_id].update({
            "status": "processing",
            "message": "Initializing agents...",
            "progress": 10
        })
        
        # Initialize agents
        planner = PlannerAgent()
        # Calculate the absolute path to the registry file
        registry_path = Path(__file__).parent.parent / 'blender_api_registry.json'
        coordinator = CoordinatorAgent(api_registry_path=str(registry_path))
        coder = CoderAgent()
        qa = QAAgent()
        
        # Initialize coordinator
        coord_init = await coordinator.initialize()
        if not coord_init:
            raise Exception("Failed to initialize coordinator agent")
        
        # Step 1: Planner Agent
        job_status[job_id].update({
            "message": "Planning subtasks...",
            "progress": 20
        })
        
        planner_input = PlannerInput(
            prompt=prompt,
            style_preferences=style_preferences,
            constraints={}
        )
        
        planner_result = await planner.process(planner_input)
        
        if not planner_result.success:
            raise Exception(f"Planner failed: {planner_result.message}")
        
        plan = planner_result.plan
        
        # Step 2: Coordinator Agent
        job_status[job_id].update({
            "message": "Mapping to Blender APIs...",
            "progress": 40
        })
        
        coordinator_input = CoordinatorInput(
            plan=plan,
            available_servers=["blender-mesh", "blender-objects", "blender-geometry", "blender-shaders"],
            execution_context={
                "scene_name": "generated_scene",
                "target_format": "gltf",
                "quality": "high",
                "original_prompt": prompt  # Pass original prompt for context
            }
        )
        
        coordinator_result = await coordinator.process(coordinator_input)
        
        if not coordinator_result.success:
            raise Exception(f"Coordinator failed: {coordinator_result.message}")
        
        api_mappings = coordinator_result.api_mappings
        
        # Step 3: Coder Agent
        job_status[job_id].update({
            "message": "Generating Python script...",
            "progress": 60
        })
        
        coder_input = CoderInput(
            plan=plan,
            api_mappings=api_mappings,
            execution_context=coordinator_input.execution_context
        )
        
        coder_result = await coder.process(coder_input)
        
        if not coder_result.success:
            raise Exception(f"Coder failed: {coder_result.message}")
        
        generated_script = coder_result.generated_script
        
        # Step 4: QA Agent
        job_status[job_id].update({
            "message": "Validating script quality...",
            "progress": 70
        })
        
        qa_input = QAInput(
            generated_script=generated_script,
            original_plan=plan,
            execution_context=coordinator_input.execution_context
        )
        
        qa_result = await qa.process(qa_input)
        
        if not qa_result.success:
            raise Exception(f"QA failed: {qa_result.message}")
        
        validation = qa_result.validation_result
        
        if not validation.is_valid:
            raise Exception("Generated script failed validation")
        
        # Step 5: Execute Blender script (or save for local mode)
        execution_mode = os.getenv("EXECUTION_MODE", "docker").lower()

        if execution_mode == "local":
            # In local mode, execute the script directly using BlenderExecutor
            from blender_executor import execute_script_for_job
            
            logger = logging.getLogger(__name__)
            
            job_status[job_id].update({
                "message": "Saving script and starting Blender...",
                "progress": 80
            })
            
            script_path = SCRIPTS_DIR / f"{job_id}.py"
            script_path.write_text(generated_script.python_code, encoding='utf-8')
            
            logger.info("="*80)
            logger.info(f"[LOCAL MODE] STEP 1: Script saved to {script_path}")
            logger.info(f"[LOCAL MODE] Script size: {len(generated_script.python_code)} bytes")
            logger.info(f"[LOCAL MODE] STEP 2: Starting Blender in headless mode...")
            logger.info("="*80)
            
            job_status[job_id].update({
                "message": "Executing in Blender (headless)...",
                "progress": 85
            })
            
            # Execute the script in Blender
            logger.info(f"[LOCAL MODE] STEP 3: Calling BlenderExecutor...")
            success, message, glb_path = execute_script_for_job(job_id, timeout=120)
            
            logger.info("="*80)
            logger.info(f"[LOCAL MODE] STEP 4: Blender execution completed")
            logger.info(f"[LOCAL MODE] Success: {success}")
            logger.info(f"[LOCAL MODE] Message: {message}")
            
            if success:
                # Verify GLB file exists and get its size
                if glb_path and glb_path.exists():
                    file_size = glb_path.stat().st_size
                    logger.info(f"[LOCAL MODE] STEP 5: GLB file verified")
                    logger.info(f"[LOCAL MODE] GLB Path: {glb_path}")
                    logger.info(f"[LOCAL MODE] GLB Size: {file_size:,} bytes")
                    logger.info(f"[LOCAL MODE] Download URL: /download/{job_id}")
                else:
                    logger.error(f"[LOCAL MODE] ❌ GLB file not found at: {glb_path}")
                    raise Exception(f"GLB file was not created at expected path: {glb_path}")
                
                job_status[job_id].update({
                    "status": "completed",
                    "message": "3D asset generated successfully!",
                    "progress": 100,
                    "model_url": f"/download/{job_id}"
                })
                
                logger.info(f"[LOCAL MODE] ✅ COMPLETE! Asset ready for download")
                logger.info("="*80)
                monitor.record_generation(success=True)
            else:
                logger.error(f"[LOCAL MODE] ❌ Blender execution failed: {message}")
                logger.info("="*80)
                raise Exception(f"Blender execution failed: {message}")
            
            return # End of processing for local mode

        # --- This part only runs in 'docker' mode ---
        job_status[job_id].update({
            "message": "Executing Blender script...",
            "progress": 80
        })
        
        model_path = await execute_blender_script(job_id, generated_script.python_code)
        
        # Step 6: Complete
        job_status[job_id].update({
            "status": "completed",
            "message": "3D asset generated successfully!",
            "progress": 100,
            "model_url": f"/download/{job_id}"
        })
        
        # Record successful generation
        monitor.record_generation(success=True)
        
    except Exception as e:
        logging.getLogger(__name__).error(f"[Job: {job_id}] Generation failed with unhandled exception: {e}", exc_info=True)
        job_status[job_id].update({
            "status": "failed",
            "message": f"Generation failed: {str(e)}",
            "error": str(e)
        })
        
        # Record failed generation
        monitor.record_generation(success=False)

async def execute_blender_script(job_id: str, python_code: str) -> Path:
    """Execute Blender script and return path to generated GLB file"""
    
    # Save script to file
    script_path = SCRIPTS_DIR / f"{job_id}.py"
    script_path.write_text(python_code, encoding='utf-8')
    
    # Output GLB path
    glb_path = MODELS_DIR / f"{job_id}.glb"
    
    # Check if running in Docker (headless Blender)
    if os.getenv('BLENDER_DOCKER', 'false').lower() == 'true':
        # Docker environment - use headless Blender
        blender_cmd = [
            'blender',
            '--background',
            '--python', str(script_path),
            '--',
            str(glb_path)
        ]
    else:
        # Local development - try to find Blender installation
        blender_executable = find_blender_executable()
        if not blender_executable:
            raise Exception("Blender not found. Please install Blender or run in Docker environment.")
        
        blender_cmd = [
            blender_executable,
            '--background',
            '--python', str(script_path),
            '--',
            str(glb_path)
        ]
    
    # Execute Blender
    try:
        logger = logging.getLogger(__name__)
        cmd_pretty = ' '.join(['"{}"'.format(c) if ' ' in str(c) else str(c) for c in blender_cmd])
        logger.info("Executing Blender command: %s", cmd_pretty)
        result = subprocess.run(
            blender_cmd,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            raise Exception(
                "Blender execution failed.\n" 
                f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            )
        
        if not glb_path.exists():
            raise Exception("GLB file was not generated")
        
        return glb_path
        
    except subprocess.TimeoutExpired:
        raise Exception("Blender execution timed out")
    except Exception as e:
        raise Exception(f"Failed to execute Blender: {str(e)}")

def find_blender_executable() -> Optional[str]:
    """Find Blender executable on the system"""
    
    # 1) Allow explicit override
    env_path = os.getenv("BLENDER_PATH")
    if env_path and Path(env_path).exists():
        return env_path

    # 2) Check PATH
    via_path = shutil.which("blender")
    if via_path:
        return via_path

    # 3) Check common Windows and Unix install locations using os.path.exists
    common_paths = [
        r"C:\\Program Files\\Blender Foundation\\Blender 4.2\\blender.exe",
        r"C:\\Program Files\\Blender Foundation\\Blender 4.1\\blender.exe",
        r"C:\\Program Files\\Blender Foundation\\Blender 4.0\\blender.exe",
        r"C:\\Program Files\\Blender Foundation\\Blender 3.6\\blender.exe",
        r"C:\\Program Files (x86)\\Blender Foundation\\Blender\\blender.exe",
        "/usr/bin/blender",
        "/usr/local/bin/blender",
        "/Applications/Blender.app/Contents/MacOS/Blender",
    ]
    for p in common_paths:
        if Path(p).exists():
            return p

    return None

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
