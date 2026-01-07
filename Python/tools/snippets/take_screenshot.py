import json
import unreal
import os

try:
    filepath = MCP_PARAMS.get("filepath", "")
    if not isinstance(filepath, str) or not filepath.strip():
        print(json.dumps({"status": "error", "error": "filepath is required"}))
        raise SystemExit(0)
    
    # Ensure .png extension
    if not filepath.lower().endswith(".png"):
        filepath += ".png"
    
    # Convert to absolute path and ensure directory exists
    filepath = os.path.abspath(filepath)
    directory = os.path.dirname(filepath)
    
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, exist_ok=True)
        except Exception as e:
            print(json.dumps({"status": "error", "error": f"Failed to create directory {directory}: {str(e)}"}))
            raise SystemExit(0)
    
    # Try using AutomationLibrary first (more reliable)
    try:
        automation_lib = unreal.AutomationLibrary()
        automation_lib.take_high_res_screenshot(1920, 1080, filepath)
        
        # Verify file was created
        if os.path.exists(filepath):
            print(json.dumps({
                "status": "success", 
                "result": {
                    "filepath": filepath,
                    "method": "AutomationLibrary.take_high_res_screenshot"
                }
            }))
        else:
            # File not created, fall back to console command
            raise Exception("Screenshot file not created by AutomationLibrary")
            
    except Exception as automation_error:
        # Fallback to HighResShot console command
        world = unreal.EditorLevelLibrary.get_editor_world()
        if not world:
            print(json.dumps({"status": "error", "error": "Failed to get editor world"}))
            raise SystemExit(0)
        
        # Use HighResShot with specific resolution
        unreal.SystemLibrary.execute_console_command(world, f"HighResShot 1920x1080 filename={filepath}")
        
        # Note: HighResShot may not immediately write the file
        print(json.dumps({
            "status": "success",
            "result": {
                "filepath": filepath,
                "method": "HighResShot console command",
                "note": "Screenshot may take a moment to save"
            }
        }))

except SystemExit:
    pass
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


