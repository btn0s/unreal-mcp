"""
Test script for set_actor_static_mesh command.

This script tests setting a static mesh on a level actor.
Requires Unreal Editor to be running with the MCP plugin loaded.
"""

import sys
import os

# Add parent directory to path to import unreal_mcp_server
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from unreal_mcp_server import UnrealConnection

def test_set_actor_static_mesh():
    """Test setting a static mesh on an actor."""
    print("=" * 60)
    print("Testing set_actor_static_mesh command")
    print("=" * 60)
    
    # Create connection
    unreal = UnrealConnection()
    if not unreal.connect():
        print("ERROR: Failed to connect to Unreal Engine")
        print("Make sure Unreal Editor is running with the MCP plugin loaded")
        print("The plugin should automatically start a TCP server on port 55557")
        return False
    
    print("[OK] Connected to Unreal Engine")
    
    try:
        # Step 0: Delete actor if it already exists
        print("\n0. Cleaning up any existing 'TestMeshActor'...")
        delete_response = unreal.send_command("delete_actor", {
            "name": "TestMeshActor"
        })
        if delete_response.get("status") != "error":
            print(f"[OK] Cleaned up existing actor")
        
        # Step 1: Spawn a StaticMeshActor
        print("\n1. Spawning a StaticMeshActor named 'TestMeshActor'...")
        spawn_response = unreal.send_command("spawn_actor", {
            "name": "TestMeshActor",
            "type": "StaticMeshActor",
            "location": [0.0, 0.0, 100.0],
            "rotation": [0.0, 0.0, 0.0]
        })
        
        if spawn_response.get("status") == "error":
            print(f"ERROR: Failed to spawn actor: {spawn_response.get('error')}")
            return False
        
        print(f"[OK] Actor spawned successfully")
        if "result" in spawn_response:
            actor_info = spawn_response["result"]
            print(f"  Actor name: {actor_info.get('name')}")
            print(f"  Actor class: {actor_info.get('class')}")
        
        # Step 2: Set the static mesh to a cube
        print("\n2. Setting static mesh to '/Engine/BasicShapes/Cube.Cube'...")
        set_mesh_response = unreal.send_command("set_actor_static_mesh", {
            "name": "TestMeshActor",
            "static_mesh": "/Engine/BasicShapes/Cube.Cube"
        })
        
        if set_mesh_response.get("status") == "error":
            print(f"ERROR: Failed to set static mesh: {set_mesh_response.get('error')}")
            return False
        
        print(f"[OK] Static mesh set successfully")
        if "result" in set_mesh_response:
            result = set_mesh_response["result"]
            print(f"  Component used: {result.get('component')}")
            print(f"  Mesh path: {result.get('static_mesh')}")
            print(f"  Success: {result.get('success')}")
        
        # Step 3: Verify by getting actor properties
        print("\n3. Verifying actor properties...")
        get_props_response = unreal.send_command("get_actor_properties", {
            "name": "TestMeshActor"
        })
        
        if get_props_response.get("status") == "error":
            print(f"ERROR: Failed to get actor properties: {get_props_response.get('error')}")
            return False
        
        print(f"[OK] Actor properties retrieved")
        if "result" in get_props_response:
            actor_props = get_props_response["result"]
            print(f"  Actor name: {actor_props.get('name')}")
            print(f"  Actor class: {actor_props.get('class')}")
            location = actor_props.get('location', [])
            print(f"  Location: [{location[0]:.2f}, {location[1]:.2f}, {location[2]:.2f}]")
        
        # Step 4: Test with a different mesh (sphere)
        print("\n4. Changing mesh to '/Engine/BasicShapes/Sphere.Sphere'...")
        set_mesh_response2 = unreal.send_command("set_actor_static_mesh", {
            "name": "TestMeshActor",
            "static_mesh": "/Engine/BasicShapes/Sphere.Sphere"
        })
        
        if set_mesh_response2.get("status") == "error":
            print(f"ERROR: Failed to set static mesh: {set_mesh_response2.get('error')}")
            return False
        
        print(f"[OK] Static mesh changed successfully")
        if "result" in set_mesh_response2:
            result = set_mesh_response2["result"]
            print(f"  Component used: {result.get('component')}")
            print(f"  Mesh path: {result.get('static_mesh')}")
        
        print("\n" + "=" * 60)
        print("All tests passed!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\nERROR: Exception occurred: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        unreal.disconnect()

if __name__ == "__main__":
    success = test_set_actor_static_mesh()
    sys.exit(0 if success else 1)

