# 🚀 Local Mode - New Approach (Headless Blender Execution)

## ✅ Architecture Change

### Old Approach (Connector-based) ❌
- Required running a connector script **inside** Blender
- Connector watched for new scripts every 1 second
- Required manual setup in Blender Scripting workspace
- Blender had to stay open and running

### New Approach (Direct Execution) ✅
- Backend **directly starts Blender** in headless mode
- Passes script as command-line argument
- Blender executes script and exits
- **No manual Blender setup required!**
- **Automatically kills existing Blender instances**

## 🎯 How It Works

### Workflow:
```
User submits prompt
    ↓
Backend generates Python script
    ↓
Backend saves script to generated_scripts/
    ↓
Backend calls BlenderExecutor
    ↓
BlenderExecutor kills any running Blender instances
    ↓
BlenderExecutor starts Blender headless:
    blender.exe --background --python script.py -- output.glb
    ↓
Blender executes script in clean environment
    ↓
Script creates 3D objects
    ↓
Script exports GLB to specified path
    ↓
Blender exits
    ↓
Backend returns success + GLB path
    ↓
Frontend downloads and displays GLB
```

## 🔧 Components

### 1. BlenderExecutor (`blender_executor.py`)

**Key Features**:
- ✅ **Process Management**: Kills existing Blender instances before execution
- ✅ **Headless Execution**: Runs Blender with `--background` flag
- ✅ **Script Injection**: Passes script via `--python` argument
- ✅ **Output Path**: Passes GLB output path via `--` separator
- ✅ **Timeout Handling**: Kills Blender if execution takes too long
- ✅ **Detailed Logging**: Every step logged with timestamps and PIDs
- ✅ **Error Handling**: Captures stdout/stderr from Blender

**Command Format**:
```bash
blender.exe \
  --background \              # Headless mode (no GUI)
  --python script.py \        # Execute this Python script
  -- \                        # Separator for script arguments
  output.glb                  # Arguments passed to the script
```

### 2. Updated Script Generation (`coder_agent.py`)

**Changes**:
- Scripts now accept output path from `sys.argv`
- Parse arguments after `--` separator
- Export GLB to specified path
- Exit with proper status code (0 = success, 1 = error)

**Script Structure**:
```python
if __name__ == "__main__":
    # Get output path from command-line
    if '--' in sys.argv:
        args = sys.argv[sys.argv.index('--') + 1:]
        output_path = args[0]
    
    # Execute plan
    executor.execute_plan()
    
    # Export to GLB
    executor.finalize_and_export(output_path)
    
    # Exit successfully
    sys.exit(0)
```

### 3. Backend Integration (`backend/main.py`)

**Local Mode Execution**:
```python
from blender_executor import execute_script_for_job

# Save script
script_path.write_text(generated_script.python_code)

# Execute in Blender
success, message, glb_path = execute_script_for_job(job_id, timeout=120)

if success:
    # GLB is ready for download
    return {"status": "completed", "model_url": f"/download/{job_id}"}
```

## 🎉 Benefits

### For Users:
- ✅ **Zero Manual Setup**: No need to run connector in Blender
- ✅ **Faster Execution**: No 1-second polling delay
- ✅ **Clean Environment**: Each script gets fresh Blender instance
- ✅ **Automatic Cleanup**: Old Blender instances automatically killed
- ✅ **Better Error Handling**: Clear error messages from Blender

### For Developers:
- ✅ **Simpler Architecture**: No complex connector script
- ✅ **Better Logging**: Full Blender stdout/stderr captured
- ✅ **Easier Debugging**: Can test scripts directly with Blender CLI
- ✅ **More Reliable**: No dependency on persistent Blender process
- ✅ **Process Isolation**: Each execution is independent

## 📋 Setup (3 Steps)

### Step 1: Configure Environment
```powershell
# Create or edit .env file
echo "EXECUTION_MODE=local" > .env
echo "GEMINI_API_KEY=your_key_here" >> .env
```

### Step 2: Verify Blender Path
Edit `blender_executor.py` if your Blender is in a different location:
```python
BLENDER_EXECUTABLE = r"C:\Program Files\Blender Foundation\Blender 4.2\blender.exe"
```

### Step 3: Start Backend
```powershell
cd d:\code\capstone
.\capstone_venc\Scripts\Activate.ps1
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**That's it!** No Blender setup required!

## 🧪 Testing

### Test BlenderExecutor Directly:
```powershell
python blender_executor.py
```

This will:
1. Look for scripts in `generated_scripts/`
2. Execute the first one found
3. Export GLB to `generated_models/`
4. Show detailed logs

### Test Complete Pipeline:
1. Open `front_end/index.html`
2. Enter prompt: "Create a red cube"
3. Click "Generate 3D Asset"
4. Watch backend terminal for:
   ```
   [LOCAL MODE] Starting Blender in headless mode...
   [BlenderExecutor] 🚀 STARTING BLENDER EXECUTION
   [BlenderExecutor] Checking for existing Blender instances...
   [BlenderExecutor] Executing Blender command:
   ... (Blender output) ...
   [BlenderExecutor] ✅ SUCCESS!
   [LOCAL MODE] ✅ Execution successful!
   ```

## 📊 Logging Output

### When Execution Starts:
```
================================================================================
[BlenderExecutor] 🚀 STARTING BLENDER EXECUTION
================================================================================
[BlenderExecutor] Script: 59517473-a0b6-405f-801e-c04f6af1a23d.py
[BlenderExecutor] Output: 59517473-a0b6-405f-801e-c04f6af1a23d.glb
[BlenderExecutor] Timeout: 120 seconds
[BlenderExecutor] Time: 2025-10-07 16:03:50
================================================================================

[BlenderExecutor] Checking for existing Blender instances...
[BlenderExecutor] Found Blender process (PID: 6696)
[BlenderExecutor] Terminating process...
[BlenderExecutor] ✅ Gracefully terminated PID 6696
[BlenderExecutor] Killed 1 Blender instance(s)

[BlenderExecutor] Executing Blender command:
[BlenderExecutor] C:\...\blender.exe --background --python script.py -- output.glb
--------------------------------------------------------------------------------
```

### Blender Output (Captured):
```
Blender 4.2.0
[BlenderScript] Output path from CLI: d:\code\capstone\generated_models\59...glb
[BlenderScript] Final output path: d:\code\capstone\generated_models\59...glb
[BlenderScript] Setting up scene...
[BlenderScript] Scene cleared.
[BlenderScript] Creating materials...
[BlenderScript] Created material: Red
[BlenderScript] Executing task: Create red cube
[BlenderScript] Executing: bpy.ops.mesh.primitive_cube_add with {'location': (0, 0, 0)}
[BlenderScript] Tracked object: Cube (MESH)
[BlenderScript] Finalizing and exporting asset...
[BlenderScript] Asset exported to d:\code\capstone\generated_models\59...glb
[BlenderScript] ✅ Script execution completed successfully!
```

### When Execution Completes:
```
================================================================================
[BlenderExecutor] ✅ SUCCESS!
[BlenderExecutor] Execution Time: 8.42 seconds
[BlenderExecutor] GLB File: 59517473-a0b6-405f-801e-c04f6af1a23d.glb
[BlenderExecutor] File Size: 98,234 bytes
[BlenderExecutor] Full Path: d:\code\capstone\generated_models\59...glb
================================================================================
```

## 🔍 Process Management

### Automatic Cleanup:
The executor automatically finds and kills Blender processes by:
1. Scanning all running processes
2. Identifying processes with "blender" in name
3. Attempting graceful termination (5 second timeout)
4. Force killing if termination fails
5. Waiting 2 seconds for cleanup

### Why Kill Existing Instances?
- ✅ Prevents resource conflicts
- ✅ Ensures clean execution environment
- ✅ Avoids file locking issues
- ✅ Prevents memory leaks from long-running Blender

### Safety:
- Only kills processes named "blender"
- Logs every PID before killing
- Handles access denied errors gracefully
- Reports how many instances were killed

## 🚨 Error Handling

### Timeout:
```
[BlenderExecutor] ⏱️ TIMEOUT: Execution timed out after 120 seconds
[BlenderExecutor] Killing any remaining Blender processes...
```

### Script Error:
```
[BlenderExecutor] ❌ FAILED: Blender exited with code 1
[BlenderExecutor] Blender Errors/Warnings:
Traceback (most recent call last):
  ... (Python error from script) ...
```

### Missing GLB:
```
[BlenderExecutor] ⚠️ WARNING: Script executed but GLB file was not created
```

## 🎯 Comparison: Old vs New

| Feature | Old (Connector) | New (Direct) |
|---------|----------------|--------------|
| **Setup** | Manual (run script in Blender) | Automatic (zero config) |
| **Speed** | 1-2 seconds delay (polling) | Immediate execution |
| **Reliability** | Depends on persistent process | Fresh instance every time |
| **Blender GUI** | Must stay open | Runs headless |
| **Process Management** | Manual cleanup | Automatic cleanup |
| **Logging** | Limited visibility | Full Blender output |
| **Error Handling** | Silent failures possible | Clear error messages |
| **Resource Usage** | Blender always running | Blender only when needed |

## 🔧 Troubleshooting

### Issue: "Blender not found"
**Solution**: Update `BLENDER_EXECUTABLE` path in `blender_executor.py`

### Issue: "Access Denied" killing Blender
**Solution**: Close Blender manually and try again, or run as administrator

### Issue: Timeout (>120 seconds)
**Solution**: 
- Check if script has infinite loops
- Increase timeout in backend: `execute_script_for_job(job_id, timeout=300)`

### Issue: GLB not created
**Solution**:
- Check Blender output for errors
- Verify script has `finalize_and_export()` call
- Check if objects were created

## 📝 Configuration

### Blender Executable Path:
Edit `blender_executor.py`:
```python
BLENDER_EXECUTABLE = r"C:\Your\Custom\Path\blender.exe"
```

### Timeout Settings:
Edit `backend/main.py`:
```python
success, message, glb_path = execute_script_for_job(job_id, timeout=180)
```

### Output Directories:
Edit `blender_executor.py`:
```python
SCRIPT_DIR = Path(r"d:\code\capstone\generated_scripts")
MODEL_DIR = Path(r"d:\code\capstone\generated_models")
```

## 🎉 Summary

The new approach is:
- ✅ **Simpler**: No manual Blender setup
- ✅ **Faster**: No polling delays
- ✅ **More Reliable**: Fresh Blender per execution
- ✅ **Better Logging**: Full visibility into execution
- ✅ **Automatic**: Handles process management
- ✅ **User-Friendly**: Just start backend and go!

**You can now generate 3D assets without ever opening Blender manually!** 🚀

---

**Ready to use!** Just start the backend and access the frontend. The system will automatically execute scripts in headless Blender with full logging and error handling.
