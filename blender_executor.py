"""
Blender Executor - Local Mode
================================
Executes generated Python scripts by starting Blender in headless mode.
Automatically kills existing Blender instances before execution.
"""

import subprocess
import psutil
import os
import time
import platform
from pathlib import Path
from typing import Optional, Tuple

# ============================================================================
# CROSS-PLATFORM CONFIGURATION
# ============================================================================
# Automatically detects environment (Windows/Linux/Docker) and sets paths

# Detect environment
IS_DOCKER = os.getenv("BLENDER_DOCKER", "false").lower() == "true"
IS_LINUX = platform.system() == "Linux"
IS_WINDOWS = platform.system() == "Windows"
IS_AWS = os.getenv("AWS_EXECUTION_ENV") is not None

print(f"[Environment Detection]")
print(f"  Platform: {platform.system()}")
print(f"  Docker: {IS_DOCKER}")
print(f"  AWS: {IS_AWS}")

# Blender executable path - environment-based
if IS_DOCKER:
    # Docker container
    BLENDER_EXECUTABLE = "/opt/blender/blender"
    print(f"  Mode: Docker Container")
elif IS_LINUX:
    # Linux (AWS EC2 or local)
    BLENDER_EXECUTABLE = os.getenv("BLENDER_PATH", "/usr/local/bin/blender")
    print(f"  Mode: Linux")
elif IS_WINDOWS:
    # Windows development
    BLENDER_EXECUTABLE = os.getenv("BLENDER_PATH", r"D:\blender.exe")
    print(f"  Mode: Windows Development")
else:
    raise RuntimeError(f"Unsupported platform: {platform.system()}")

print(f"  Blender Path: {BLENDER_EXECUTABLE}")

# Working directories - cross-platform
if IS_DOCKER or IS_AWS:
    # Production: Docker or AWS
    BASE_DIR = Path("/app")
else:
    # Development: Local machine
    BASE_DIR = Path(__file__).parent.resolve()

SCRIPT_DIR = BASE_DIR / "generated_scripts"
MODEL_DIR = BASE_DIR / "generated_models"

print(f"  Base Directory: {BASE_DIR}")
print(f"  Scripts: {SCRIPT_DIR}")
print(f"  Models: {MODEL_DIR}")

# Ensure directories exist
SCRIPT_DIR.mkdir(parents=True, exist_ok=True)
MODEL_DIR.mkdir(parents=True, exist_ok=True)


class BlenderExecutor:
    """Executes Blender scripts in headless mode"""
    
    def __init__(self, blender_path: str = BLENDER_EXECUTABLE):
        self.blender_path = blender_path
        
        # Verify Blender exists
        if not Path(blender_path).exists():
            raise FileNotFoundError(f"Blender not found at: {blender_path}")
        
        print(f"[BlenderExecutor] Initialized with Blender: {blender_path}")
    
    def kill_existing_blender_instances(self) -> int:
        """Kill all running Blender processes"""
        killed_count = 0
        
        print("[BlenderExecutor] Checking for existing Blender instances...")
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] and 'blender' in proc.info['name'].lower():
                    pid = proc.info['pid']
                    print(f"[BlenderExecutor] Found Blender process (PID: {pid})")
                    print(f"[BlenderExecutor] Terminating process...")
                    
                    # Try graceful termination first
                    try:
                        proc.terminate()
                        proc.wait(timeout=5)
                        print(f"[BlenderExecutor] ✅ Gracefully terminated PID {pid}")
                    except psutil.TimeoutExpired:
                        # Force kill if graceful termination fails
                        proc.kill()
                        print(f"[BlenderExecutor] ✅ Force killed PID {pid}")
                    
                    killed_count += 1
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        if killed_count > 0:
            print(f"[BlenderExecutor] Killed {killed_count} Blender instance(s)")
            time.sleep(2)  # Wait for processes to fully terminate
        else:
            print("[BlenderExecutor] No existing Blender instances found")
        
        return killed_count
    
    def execute_script(self, script_path: Path, output_glb: Path, timeout: int = 120) -> Tuple[bool, str]:
        """
        Execute a Blender Python script and export GLB
        
        Args:
            script_path: Path to the Python script to execute
            output_glb: Path where GLB should be exported
            timeout: Maximum execution time in seconds
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        print("\n" + "="*80)
        print(f"[BlenderExecutor] 🚀 STARTING BLENDER EXECUTION")
        print("="*80)
        print(f"[BlenderExecutor] Script: {script_path.name}")
        print(f"[BlenderExecutor] Output: {output_glb.name}")
        print(f"[BlenderExecutor] Timeout: {timeout} seconds")
        print(f"[BlenderExecutor] Time: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Verify script exists
        if not script_path.exists():
            error_msg = f"Script not found: {script_path}"
            print(f"[BlenderExecutor] ❌ {error_msg}")
            return False, error_msg
        
        # Kill existing instances
        print()
        self.kill_existing_blender_instances()
        
        # Prepare Blender command
        # Use --background for headless mode and --python to execute script
        command = [
            str(self.blender_path),
            "--background",  # Headless mode
            "--python", str(script_path),  # Execute Python script
            "--",  # Separator for script arguments
            str(output_glb)  # Pass output path as argument to script
        ]
        
        print()
        print("[BlenderExecutor] Executing Blender command:")
        print(f"[BlenderExecutor] {' '.join(command)}")
        print()
        print("[BlenderExecutor] " + "-"*80)
        
        try:
            # Execute Blender with the script
            start_time = time.time()
            
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(script_path.parent)
            )
            
            execution_time = time.time() - start_time
            
            print("[BlenderExecutor] " + "-"*80)
            print()
            
            # Print Blender output
            if result.stdout:
                print("[BlenderExecutor] Blender Output:")
                print(result.stdout)
            
            if result.stderr:
                print("[BlenderExecutor] Blender Errors/Warnings:")
                print(result.stderr)
            
            # Check if execution was successful
            if result.returncode == 0:
                # Verify GLB was created
                if output_glb.exists():
                    file_size = output_glb.stat().st_size
                    print()
                    print("="*80)
                    print(f"[BlenderExecutor] ✅ SUCCESS!")
                    print(f"[BlenderExecutor] Execution Time: {execution_time:.2f} seconds")
                    print(f"[BlenderExecutor] GLB File: {output_glb.name}")
                    print(f"[BlenderExecutor] File Size: {file_size:,} bytes")
                    print(f"[BlenderExecutor] Full Path: {output_glb}")
                    print("="*80 + "\n")
                    return True, "Script executed successfully"
                else:
                    error_msg = "Script executed but GLB file was not created"
                    print()
                    print("="*80)
                    print(f"[BlenderExecutor] ⚠️ WARNING: {error_msg}")
                    print("="*80 + "\n")
                    return False, error_msg
            else:
                error_msg = f"Blender exited with code {result.returncode}"
                print()
                print("="*80)
                print(f"[BlenderExecutor] ❌ FAILED: {error_msg}")
                print("="*80 + "\n")
                return False, error_msg
        
        except subprocess.TimeoutExpired:
            error_msg = f"Execution timed out after {timeout} seconds"
            print()
            print("="*80)
            print(f"[BlenderExecutor] ⏱️ TIMEOUT: {error_msg}")
            print("="*80 + "\n")
            
            # Try to kill any remaining Blender processes
            self.kill_existing_blender_instances()
            
            return False, error_msg
        
        except Exception as e:
            error_msg = f"Execution error: {str(e)}"
            print()
            print("="*80)
            print(f"[BlenderExecutor] ❌ ERROR: {error_msg}")
            print("="*80 + "\n")
            
            import traceback
            traceback.print_exc()
            
            return False, error_msg


def execute_script_for_job(job_id: str, timeout: int = 120) -> Tuple[bool, str, Optional[Path]]:
    """
    Execute a script for a given job ID
    
    Args:
        job_id: The job ID (filename without extension)
        timeout: Maximum execution time
        
    Returns:
        Tuple of (success, message, glb_path)
    """
    script_path = SCRIPT_DIR / f"{job_id}.py"
    output_glb = MODEL_DIR / f"{job_id}.glb"
    
    executor = BlenderExecutor()
    success, message = executor.execute_script(script_path, output_glb, timeout)
    
    return success, message, output_glb if success else None


if __name__ == "__main__":
    # Test execution
    print("="*80)
    print("  BLENDER EXECUTOR - TEST MODE")
    print("="*80)
    print()
    
    # Find a test script
    test_scripts = list(SCRIPT_DIR.glob("*.py"))
    
    if test_scripts:
        test_script = test_scripts[0]
        job_id = test_script.stem
        
        print(f"Testing with script: {test_script.name}")
        print()
        
        success, message, glb_path = execute_script_for_job(job_id, timeout=60)
        
        if success:
            print(f"\n✅ Test successful!")
            print(f"GLB created at: {glb_path}")
        else:
            print(f"\n❌ Test failed: {message}")
    else:
        print("No test scripts found in generated_scripts/")
