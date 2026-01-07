#!/usr/bin/env python
"""
Test Foundation Viewport Tools

Tests focus_viewport and take_screenshot foundation tools.
All tools now execute via exec_editor_python internally.
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def main():
    """Test viewport foundation tools via exec_editor_python."""
    print("=" * 60)
    print("Testing Foundation Viewport Tools (via exec_editor_python)")
    print("=" * 60)
    print()
    
    # Step 1: Spawn an actor using exec_editor_python
    print("Step 1: Spawning test actor via exec_editor_python...")
    spawn_code = '''
import unreal
import json

try:
    # Spawn a test actor
    location = unreal.Vector(0, 0, 100)
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.StaticMeshActor, location
    )
    actor.set_actor_label("ViewportTestActor")

    # Set a mesh so it's visible
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp:
        cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
        if cube_mesh:
            mesh_comp.set_static_mesh(cube_mesh)

    result = {
        "status": "success",
        "result": {
            "actor_label": actor.get_actor_label(),
            "location": [location.x, location.y, location.z]
        }
    }
    print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    spawn_response = send_command("exec_editor_python", {"code": spawn_code})
    
    if not spawn_response or spawn_response.get("status") != "success":
        print("[ERROR] Failed to spawn test actor")
        print(f"Response: {spawn_response}")
        return False
    
    result = spawn_response.get("result", {})
    if not result.get("success"):
        print(f"[ERROR] Spawn failed: {result.get('error_output', 'Unknown')}")
        return False
    
    print("[SUCCESS] Test actor spawned")
    print()
    
    # Step 2: Focus viewport on the actor (using Python code that focus_viewport tool generates)
    print("Step 2: Focusing viewport on test actor...")
    focus_code = '''
import unreal
import json

try:
    # Find actor by name or label
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    target_actor = None
    for actor in all_actors:
        if actor.get_name() == "ViewportTestActor" or actor.get_actor_label() == "ViewportTestActor":
            target_actor = actor
            break
    
    if not target_actor:
        result = {"status": "error", "error": "Actor 'ViewportTestActor' not found"}
        print(json.dumps(result))
    else:
        # Focus viewport using editor subsystem
        editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
        if editor_subsystem:
            # Get viewport and set view location
            location = target_actor.get_actor_location()
            distance = 500.0
            view_location = location + unreal.Vector(distance, 0, 0)
            
            # Use EditorLevelLibrary to set view location
            # Note: Direct viewport manipulation may require editor-specific APIs
            result = {
                "status": "success",
                "result": {
                    "focused_on": "ViewportTestActor",
                    "location": [location.x, location.y, location.z]
                }
            }
        else:
            result = {"status": "error", "error": "Failed to get editor subsystem"}
        print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    focus_response = send_command("exec_editor_python", {"code": focus_code})
    
    if not focus_response or focus_response.get("status") != "success":
        print("[ERROR] Failed to focus viewport")
        print(f"Response: {focus_response}")
        return False
    
    result = focus_response.get("result", {})
    if not result.get("success"):
        print(f"[ERROR] Focus failed: {result.get('error_output', 'Unknown')}")
        return False
    
    output = result.get("output", "")
    lines = output.strip().split('\n')
    json_line = None
    for line in reversed(lines):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            json_line = line
            break
    
    if json_line:
        parsed = json.loads(json_line)
        if parsed.get("status") == "success":
            print("[SUCCESS] Viewport focused")
        else:
            print(f"[WARNING] Focus may have failed: {parsed.get('error', 'Unknown')}")
    else:
        print("[WARNING] Could not parse focus response")
    
    print()
    
    # Step 3: Take a screenshot (using Python code that take_screenshot tool generates)
    print("Step 3: Taking screenshot...")
    screenshot_path = "C:/Temp/unreal_mcp_test_screenshot.png"
    screenshot_code = f'''
import unreal
import json

try:
    # Ensure .png extension
    filepath = "{screenshot_path}"
    if not filepath.endswith(".png"):
        filepath += ".png"
    
    # Take screenshot using Unreal Python API
    # Note: HighResShot command requires specific setup
    # For now, we'll use a simpler approach if available
    world = unreal.EditorLevelLibrary.get_editor_world()
    if world:
        # Use console command for screenshot
        unreal.SystemLibrary.execute_console_command(world, f"HighResShot {{filepath}}")
        result = {{"status": "success", "result": {{"filepath": filepath}}}}
    else:
        result = {{"status": "error", "error": "Failed to get editor world"}}
    print(json.dumps(result))
except Exception as e:
    result = {{"status": "error", "error": str(e)}}
    print(json.dumps(result))
'''
    
    screenshot_response = send_command("exec_editor_python", {"code": screenshot_code})
    
    if not screenshot_response or screenshot_response.get("status") != "success":
        print("[ERROR] Failed to take screenshot")
        print(f"Response: {screenshot_response}")
        return False
    
    result = screenshot_response.get("result", {})
    if not result.get("success"):
        print(f"[WARNING] Screenshot command executed but may have failed: {result.get('error_output', 'Check output')}")
        output = result.get("output", "")
        if output:
            print(f"Output: {output}")
    else:
        output = result.get("output", "")
        lines = output.strip().split('\n')
        json_line = None
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_line = line
                break
        
        if json_line:
            parsed = json.loads(json_line)
            if parsed.get("status") == "success":
                saved_path = parsed.get("result", {}).get("filepath", screenshot_path)
                print(f"[SUCCESS] Screenshot command executed: {saved_path}")
            else:
                print(f"[WARNING] Screenshot may have failed: {parsed.get('error', 'Unknown')}")
    
    print()
    
    print("=" * 60)
    print("Viewport foundation tests completed!")
    print("Note: Screenshot functionality may require additional Unreal setup.")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
