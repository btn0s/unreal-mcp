#!/usr/bin/env python
"""
Build a castle in Unreal Engine using exec_editor_python.
"""

import sys
import os
import socket
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def send_command(command, params):
    """Send a command to Unreal Engine."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 55557))
    try:
        cmd = {'type': command, 'params': params}
        sock.sendall(json.dumps(cmd).encode('utf-8'))
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            try:
                data = b''.join(chunks)
                json.loads(data.decode('utf-8'))
                break
            except json.JSONDecodeError:
                continue
        return json.loads(b''.join(chunks).decode('utf-8'))
    finally:
        sock.close()

castle_code = '''
import unreal

# Castle building script
print("Building a castle...")

# Get editor level library
editor_level = unreal.EditorLevelLibrary()

# Base size for the castle
base_size = 800.0
wall_height = 400.0
tower_height = 600.0
wall_thickness = 100.0

# Materials
cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")

# Function to spawn a cube actor
def spawn_cube(name, location, scale):
    actor = editor_level.spawn_actor_from_class(unreal.StaticMeshActor, location)
    actor.set_actor_label(name)
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp:
        mesh_comp.set_static_mesh(cube_mesh)
        mesh_comp.set_world_scale3d(scale)
    return actor

# Function to spawn a cylinder actor (for towers)
def spawn_cylinder(name, location, scale):
    actor = editor_level.spawn_actor_from_class(unreal.StaticMeshActor, location)
    actor.set_actor_label(name)
    mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if mesh_comp:
        mesh_comp.set_static_mesh(cylinder_mesh)
        mesh_comp.set_world_scale3d(scale)
    return actor

# Center position
center = unreal.Vector(0, 0, 0)

# Build four corner towers
tower_positions = [
    unreal.Vector(-base_size/2, -base_size/2, tower_height/2),
    unreal.Vector(base_size/2, -base_size/2, tower_height/2),
    unreal.Vector(base_size/2, base_size/2, tower_height/2),
    unreal.Vector(-base_size/2, base_size/2, tower_height/2)
]

print("Building corner towers...")
for i, pos in enumerate(tower_positions):
    spawn_cylinder(f"CastleTower_{i+1}", pos, unreal.Vector(1.5, 1.5, tower_height/100))

# Build walls between towers
print("Building walls...")
wall_positions = [
    unreal.Vector(0, -base_size/2, wall_height/2),  # South wall
    unreal.Vector(base_size/2, 0, wall_height/2),    # East wall
    unreal.Vector(0, base_size/2, wall_height/2),   # North wall
    unreal.Vector(-base_size/2, 0, wall_height/2),  # West wall
]

wall_scales = [
    unreal.Vector(base_size/100, wall_thickness/100, wall_height/100),  # South
    unreal.Vector(wall_thickness/100, base_size/100, wall_height/100),  # East
    unreal.Vector(base_size/100, wall_thickness/100, wall_height/100),  # North
    unreal.Vector(wall_thickness/100, base_size/100, wall_height/100),  # West
]

for i, (pos, scale) in enumerate(zip(wall_positions, wall_scales)):
    spawn_cube(f"CastleWall_{i+1}", pos, scale)

# Build a keep in the center
print("Building central keep...")
keep_height = 500.0
keep_size = 300.0
spawn_cube("CastleKeep", unreal.Vector(0, 0, keep_height/2), unreal.Vector(keep_size/100, keep_size/100, keep_height/100))

# Add a gate (opening in south wall)
gate_width = 200.0
gate_height = 300.0
gate_pos = unreal.Vector(0, -base_size/2, gate_height/2)
spawn_cube("CastleGate", gate_pos, unreal.Vector(gate_width/100, wall_thickness/100, gate_height/100))

# Add some decorative elements - flags on towers
print("Adding decorative elements...")
flag_positions = [
    unreal.Vector(-base_size/2, -base_size/2, tower_height + 50),
    unreal.Vector(base_size/2, -base_size/2, tower_height + 50),
]

for i, pos in enumerate(flag_positions):
    spawn_cube(f"CastleFlag_{i+1}", pos, unreal.Vector(0.5, 2.0, 0.1))

print("Castle construction complete!")
print(f"Created castle with towers, walls, keep, gate, and flags")
'''

if __name__ == "__main__":
    print("Building a castle in Unreal Engine...")
    response = send_command('exec_editor_python', {'code': castle_code})
    
    if response.get('status') == 'success':
        result = response.get('result', {})
        if result.get('success'):
            print("\n[SUCCESS] Castle built successfully!")
            print("\nOutput:")
            print(result.get('output', ''))
        else:
            print("\n[FAILED] Castle build failed:")
            print(result.get('error', 'Unknown error'))
    else:
        print("\n[FAILED] Command failed:")
        print(response.get('error', 'Unknown error'))
        print("\nFull response:")
        print(json.dumps(response, indent=2))

