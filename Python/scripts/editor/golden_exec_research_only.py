#!/usr/bin/env python
"""
Golden Path Example: Research Only (No Edits)

Demonstrates the RESEARCH phase of the Ask -> Research -> Execute -> Verify workflow.
This script performs read-only queries to inspect the current Unreal Editor state
without making any changes.

Usage:
    python golden_exec_research_only.py
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def main():
    """Research current Unreal Editor state."""
    print("=" * 60)
    print("Golden Path: Research Only (No Edits)")
    print("=" * 60)
    print()
    
    # RESEARCH: Query current state using exec_editor_python
    research_code = '''
import unreal
import json

# Get all actors in the level
all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
actor_count = len(all_actors)

# Get selected actors
selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
selected_count = len(selected_actors)

# Get level information
level = unreal.EditorLevelLibrary.get_editor_world()
level_path = level.get_path_name() if level else "Unknown"

# Filter actors by type
static_mesh_actors = [a for a in all_actors if isinstance(a, unreal.StaticMeshActor)]
light_actors = [a for a in all_actors if isinstance(a, (unreal.PointLight, unreal.DirectionalLight, unreal.SpotLight))]

# Get actor labels (first 10)
actor_labels = [a.get_actor_label() for a in all_actors[:10]]

# Check for common test actors
test_actors = [a for a in all_actors if "Test" in a.get_actor_label() or "test" in a.get_actor_label()]

# Compile results
result = {
    "status": "success",
    "result": {
        "level_path": level_path,
        "total_actors": actor_count,
        "selected_actors": selected_count,
        "static_mesh_actors": len(static_mesh_actors),
        "light_actors": len(light_actors),
        "test_actors": len(test_actors),
        "sample_actor_labels": actor_labels,
        "test_actor_labels": [a.get_actor_label() for a in test_actors]
    }
}
print(json.dumps(result))
'''
    
    print("Researching current Unreal Editor state...")
    print()
    
    response = send_command("exec_editor_python", {"code": research_code})
    
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
        # Extract JSON from output (may have other print statements)
        lines = output.strip().split('\n')
        json_line = None
        for line in reversed(lines):
            line = line.strip()
            if line.startswith('{') and line.endswith('}'):
                json_line = line
                break
        
        if json_line:
            research_result = json.loads(json_line)
            if research_result.get("status") == "success":
                data = research_result.get("result", {})
                
                print("[SUCCESS] Research Complete")
                print()
                print(f"Level: {data.get('level_path', 'Unknown')}")
                print(f"Total Actors: {data.get('total_actors', 0)}")
                print(f"Selected Actors: {data.get('selected_actors', 0)}")
                print(f"Static Mesh Actors: {data.get('static_mesh_actors', 0)}")
                print(f"Light Actors: {data.get('light_actors', 0)}")
                print(f"Test Actors: {data.get('test_actors', 0)}")
                print()
                
                if data.get('sample_actor_labels'):
                    print("Sample Actor Labels:")
                    for label in data['sample_actor_labels']:
                        print(f"  - {label}")
                    print()
                
                if data.get('test_actor_labels'):
                    print("Test Actor Labels:")
                    for label in data['test_actor_labels']:
                        print(f"  - {label}")
                    print()
                
                print("=" * 60)
                print("Research phase complete. No edits were made.")
                print("=" * 60)
                return True
            else:
                print(f"[ERROR] Research failed: {research_result.get('error', 'Unknown error')}")
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

