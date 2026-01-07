#!/usr/bin/env python
"""
Golden Path Example: Spawn or Update Actor (Research -> Execute -> Verify)

Demonstrates the complete Ask -> Research -> Execute -> Verify workflow:
1. RESEARCH: Check if an actor with a specific label exists
2. EXECUTE: Create the actor if missing, or update its transform if it exists
3. VERIFY: Confirm the final state

Usage:
    python golden_exec_spawn_or_update_actor.py
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def main():
    """Spawn or update an actor following the golden path workflow."""
    print("=" * 60)
    print("Golden Path: Spawn or Update Actor")
    print("=" * 60)
    print()
    
    actor_label = "GoldenPathTestActor"
    target_location = [500.0, 500.0, 200.0]
    
    print(f"Target Actor Label: {actor_label}")
    print(f"Target Location: {target_location}")
    print()
    
    # Complete workflow: Research → Execute → Verify
    workflow_code = f'''
import unreal
import json

actor_label = "{actor_label}"
target_location = unreal.Vector({target_location[0]}, {target_location[1]}, {target_location[2]})

try:
    # ===== RESEARCH PHASE =====
    print("RESEARCH: Checking current state...")
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    existing_actors = [a for a in all_actors if a.get_actor_label() == actor_label]
    
    actor_exists = len(existing_actors) > 0
    actor_count_before = len(all_actors)
    
    print(f"Found {{len(existing_actors)}} actor(s) with label '{{actor_label}}'")
    
    # ===== EXECUTE PHASE =====
    print("EXECUTE: Making changes in transaction...")
    with unreal.ScopedEditorTransaction(f"Ensure actor {{actor_label}} exists at target location"):
        if actor_exists:
            # Update existing actor
            actor = existing_actors[0]
            current_location = actor.get_actor_location()
            print(f"Updating existing actor from {{current_location}} to {{target_location}}")
            actor.set_actor_location(target_location, False, True)
            created = False
        else:
            # Create new actor
            print(f"Creating new actor '{{actor_label}}'")
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor, target_location
            )
            actor.set_actor_label(actor_label)
            created = True
        
        # Set a mesh so it's visible
        mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if mesh_comp:
            cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
            if cube_mesh:
                mesh_comp.set_static_mesh(cube_mesh)
    
    # ===== VERIFY PHASE =====
    print("VERIFY: Confirming final state...")
    all_actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
    actor_count_after = len(all_actors_after)
    
    # Re-query to verify
    verify_actors = [a for a in all_actors_after if a.get_actor_label() == actor_label]
    if verify_actors:
        final_actor = verify_actors[0]
        final_location = final_actor.get_actor_location()
        verified = True
    else:
        verified = False
        final_location = None
    
    # Return structured result
    result = {{
        "status": "success",
        "result": {{
            "actor_label": actor_label,
            "created": created,
            "verified": verified,
            "actors_before": actor_count_before,
            "actors_after": actor_count_after,
            "final_location": [
                final_location.x if final_location else None,
                final_location.y if final_location else None,
                final_location.z if final_location else None
            ],
            "target_location": [{target_location[0]}, {target_location[1]}, {target_location[2]}]
        }}
    }}
    print(json.dumps(result))
    
except Exception as e:
    result = {{
        "status": "error",
        "error": str(e)
    }}
    print(json.dumps(result))
'''
    
    print("Executing workflow: Research -> Execute -> Verify")
    print()
    
    response = send_command("exec_editor_python", {"code": workflow_code})
    
    if not response:
        print("[ERROR] Failed to connect to Unreal Engine")
        print("Make sure Unreal Editor is running with the UnrealMCP plugin loaded.")
        return False
    
    if response.get("status") != "success":
        print(f"[ERROR] Command failed: {response.get('error', 'Unknown error')}")
        return False
    
    result = response.get("result", {})
    if not result.get("success"):
        error_output = result.get("error_output", result.get("error", "Unknown error"))
        print(f"[ERROR] Python execution failed:")
        print(error_output)
        return False
    
    # Parse the JSON output from Python
    output = result.get("output", "")
    try:
        # Extract JSON from output
        lines = output.strip().split('\n')
        json_line = None
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_line = line
                break
        
        if json_line:
            workflow_result = json.loads(json_line)
            
            if workflow_result.get("status") == "success":
                data = workflow_result.get("result", {})
                
                print("[SUCCESS] Workflow Complete")
                print()
                print(f"Actor Label: {data.get('actor_label')}")
                print(f"Created: {data.get('created', False)}")
                print(f"Verified: {data.get('verified', False)}")
                print(f"Actors Before: {data.get('actors_before', 0)}")
                print(f"Actors After: {data.get('actors_after', 0)}")
                print()
                
                final_loc = data.get('final_location')
                target_loc = data.get('target_location')
                if final_loc and target_loc:
                    print(f"Final Location: [{final_loc[0]:.1f}, {final_loc[1]:.1f}, {final_loc[2]:.1f}]")
                    print(f"Target Location: [{target_loc[0]:.1f}, {target_loc[1]:.1f}, {target_loc[2]:.1f}]")
                    print()
                
                print("=" * 60)
                print("Golden path workflow complete!")
                print("=" * 60)
                return True
            else:
                print(f"[ERROR] Workflow failed: {workflow_result.get('error', 'Unknown error')}")
                return False
        else:
            print("[WARNING] Could not parse JSON from output")
            print("Raw output:")
            print(output)
            return False
            
    except json.JSONDecodeError as e:
        print(f"[ERROR] Failed to parse JSON result: {e}")
        print("Raw output:")
        print(output)
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

