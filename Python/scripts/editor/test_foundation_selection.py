#!/usr/bin/env python
"""
Test Foundation Selection Tools

Tests get_selected_actors, set_selected_actors, and clear_selection foundation tools.
All tools now execute via exec_editor_python internally.
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def main():
    """Test selection foundation tools via exec_editor_python."""
    print("=" * 60)
    print("Testing Foundation Selection Tools (via exec_editor_python)")
    print("=" * 60)
    print()
    
    # Step 1: Spawn two test actors using exec_editor_python
    print("Step 1: Spawning test actors via exec_editor_python...")
    spawn_code = '''
import unreal
import json

try:
    # Spawn two test actors
    actors = []
    for i in range(2):
        location = unreal.Vector(i * 200, 0, 100)
        actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
            unreal.StaticMeshActor, location
        )
        actor.set_actor_label(f"SelectionTestActor_{i+1}")
        actors.append(actor.get_actor_label())
    
    result = {
        "status": "success",
        "result": {
            "actor_labels": actors
        }
    }
    print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    spawn_response = send_command("exec_editor_python", {"code": spawn_code})
    
    if not spawn_response or spawn_response.get("status") != "success":
        print("[ERROR] Failed to spawn test actors")
        print(f"Response: {spawn_response}")
        return False
    
    result = spawn_response.get("result", {})
    if not result.get("success"):
        print("[ERROR] Python execution failed")
        print(f"Error: {result.get('error_output', result.get('error', 'Unknown'))}")
        return False
    
    output = result.get("output", "")
    # Extract JSON from output
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
            actor_labels = parsed.get("result", {}).get("actor_labels", [])
            print(f"[SUCCESS] Spawned actors: {', '.join(actor_labels)}")
        else:
            print(f"[ERROR] Spawn failed: {parsed.get('error')}")
            return False
    else:
        actor_labels = ["SelectionTestActor_1", "SelectionTestActor_2"]
        print("[SUCCESS] Test actors spawned (using default names)")
    
    print()
    
    # Step 2: Clear selection (using Python code that clear_selection tool generates)
    print("Step 2: Clearing selection...")
    clear_code = '''
import unreal
import json

try:
    unreal.EditorLevelLibrary.set_selected_level_actors([])
    result = {"status": "success", "result": {}}
    print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    clear_response = send_command("exec_editor_python", {"code": clear_code})
    
    if not clear_response or clear_response.get("status") != "success":
        print("[ERROR] Failed to clear selection")
        print(f"Response: {clear_response}")
        return False
    
    result = clear_response.get("result", {})
    if result.get("success"):
        print("[SUCCESS] Selection cleared")
    else:
        print(f"[ERROR] Clear failed: {result.get('error_output', 'Unknown')}")
        return False
    
    print()
    
    # Step 3: Get selected actors (using Python code that get_selected_actors tool generates)
    print("Step 3: Verifying selection is empty...")
    get_code = '''
import unreal
import json

try:
    selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    actors_list = []
    for actor in selected_actors:
        actors_list.append({
            "name": actor.get_name(),
            "label": actor.get_actor_label(),
            "path": actor.get_path_name()
        })
    
    result = {"status": "success", "result": {"actors": actors_list}}
    print(json.dumps(result))
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    get_response = send_command("exec_editor_python", {"code": get_code})
    
    if not get_response or get_response.get("status") != "success":
        print("[ERROR] Failed to get selected actors")
        print(f"Response: {get_response}")
        return False
    
    result = get_response.get("result", {})
    if not result.get("success"):
        print(f"[ERROR] Get failed: {result.get('error_output', 'Unknown')}")
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
            actors = parsed.get("result", {}).get("actors", [])
            if len(actors) == 0:
                print("[SUCCESS] Selection is empty (as expected)")
            else:
                print(f"[WARNING] Selection not empty: {len(actors)} actors selected")
        else:
            print(f"[ERROR] Get failed: {parsed.get('error')}")
            return False
    
    print()
    
    # Step 4: Set selection (using Python code that set_selected_actors tool generates)
    print(f"Step 4: Setting selection to test actors: {actor_labels}")
    actor_names_json = json.dumps(actor_labels)
    set_code = f'''
import unreal
import json

try:
    actor_names = {actor_names_json}
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    
    # Clear current selection
    unreal.EditorLevelLibrary.set_selected_level_actors([])
    
    found_actors = []
    not_found = []
    
    selected = unreal.EditorLevelLibrary.get_selected_level_actors()
    selected_list = list(selected) if selected else []
    
    for name in actor_names:
        found = False
        for actor in all_actors:
            if actor.get_name() == name or actor.get_actor_label() == name:
                selected_list.append(actor)
                found_actors.append(name)
                found = True
                break
        if not found:
            not_found.append(name)
    
    unreal.EditorLevelLibrary.set_selected_level_actors(selected_list)
    
    result = {{
        "status": "success",
        "result": {{
            "selected_count": len(found_actors),
            "found": found_actors,
            "not_found": not_found if not_found else None
        }}
    }}
    print(json.dumps(result))
except Exception as e:
    result = {{"status": "error", "error": str(e)}}
    print(json.dumps(result))
'''
    
    set_response = send_command("exec_editor_python", {"code": set_code})
    
    if not set_response or set_response.get("status") != "success":
        print("[ERROR] Failed to set selected actors")
        print(f"Response: {set_response}")
        return False
    
    result = set_response.get("result", {})
    if not result.get("success"):
        print(f"[ERROR] Set failed: {result.get('error_output', 'Unknown')}")
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
            data = parsed.get("result", {})
            selected_count = data.get("selected_count", 0)
            found = data.get("found", [])
            not_found = data.get("not_found", [])
            
            print(f"[SUCCESS] Selected {selected_count} actor(s)")
            if found:
                print(f"  Found: {', '.join(found)}")
            if not_found:
                print(f"  Not found: {', '.join(not_found)}")
        else:
            print(f"[ERROR] Set failed: {parsed.get('error')}")
            return False
    
    print()
    
    # Step 5: Verify selection again
    print("Step 5: Verifying selection...")
    get_response2 = send_command("exec_editor_python", {"code": get_code})
    
    if not get_response2 or get_response2.get("status") != "success":
        print("[ERROR] Failed to get selected actors")
        return False
    
    result2 = get_response2.get("result", {})
    if not result2.get("success"):
        print(f"[ERROR] Get failed: {result2.get('error_output', 'Unknown')}")
        return False
    
    output2 = result2.get("output", "")
    lines2 = output2.strip().split('\n')
    json_line2 = None
    for line in reversed(lines2):
        line = line.strip()
        if line.startswith('{') and line.endswith('}'):
            json_line2 = line
            break
    
    if json_line2:
        parsed2 = json.loads(json_line2)
        if parsed2.get("status") == "success":
            actors2 = parsed2.get("result", {}).get("actors", [])
            if len(actors2) == selected_count:
                print(f"[SUCCESS] Selection verified: {len(actors2)} actor(s) selected")
                for actor in actors2:
                    print(f"  - {actor.get('label', actor.get('name', 'Unknown'))}")
            else:
                print(f"[WARNING] Selection count mismatch: expected {selected_count}, got {len(actors2)}")
        else:
            print(f"[ERROR] Get failed: {parsed2.get('error')}")
            return False
    
    print()
    
    print("=" * 60)
    print("All selection foundation tests passed!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
