#!/usr/bin/env python
"""
Build a stealth game coastal mansion level in Unreal Engine.
"""

import socket
import json
import os
import sys

def send_command(command, params):
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

mansion_code = '''
import unreal

# --- Setup ---
print("Building Stealth Coastal Mansion...")
editor_actor_subs = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

# Meshes
cube_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cube")
sphere_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Sphere")
cylinder_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cylinder")
cone_mesh = unreal.EditorAssetLibrary.load_asset("/Engine/BasicShapes/Cone")

def spawn(name, location, scale=[1, 1, 1], rotation=[0, 0, 0], mesh=cube_mesh):
    actor = editor_actor_subs.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(rotation[0], rotation[1], rotation[2]))
    actor.set_actor_label(name)
    comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if comp:
        comp.set_static_mesh(mesh)
        comp.set_world_scale3d(unreal.Vector(scale[0], scale[1], scale[2]))
    return actor

# --- 1. The Environment ---
# Sea (Far below)
spawn("Ocean", unreal.Vector(0, 0, -500), [200, 200, 0.1])

# Cliff-side Platform
spawn("MansionCliff", unreal.Vector(0, 0, 0), [50, 50, 1])

# --- 2. The Mansion ---
# Main Building (First Floor)
spawn("Mansion_Base", unreal.Vector(0, 0, 250), [15, 10, 5])

# Second Floor
spawn("Mansion_Upper", unreal.Vector(0, 0, 750), [10, 8, 5])

# Balcony
spawn("Mansion_Balcony", unreal.Vector(1000, 0, 600), [5, 6, 0.5])

# Large Windows (Glass Effect via scale/pos)
spawn("Mansion_Window_Front", unreal.Vector(750, 0, 350), [0.1, 4, 3])

# --- 3. Garden & Stealth Elements ---
# Tall Grass / Hiding Spots
import random
for i in range(20):
    x = random.uniform(-2000, 2000)
    y = random.uniform(-2000, -500)
    spawn(f"Garden_Bush_{i}", unreal.Vector(x, y, 100), [1.5, 1.5, 1.5], mesh=sphere_mesh)

# Crates for Cover
spawn("Cover_Crate_1", unreal.Vector(500, -800, 150), [1.5, 1.5, 1.5])
spawn("Cover_Crate_2", unreal.Vector(650, -800, 150), [1.5, 1.5, 1.5])

# --- 4. Guard Patrols ---
# Represented by Red Cones
guard_path = [
    unreal.Vector(1500, -1500, 100),
    unreal.Vector(1500, 1500, 100),
    unreal.Vector(-1500, 1500, 100),
    unreal.Vector(-1500, -1500, 100)
]

for i, pos in enumerate(guard_path):
    spawn(f"Guard_Node_{i}", pos, [1, 1, 2], mesh=cone_mesh)

# --- 5. Lighting / Points of Interest ---
# Front Gate Pillars
spawn("Gate_Pillar_L", unreal.Vector(-1500, -2000, 250), [1, 1, 5], mesh=cylinder_mesh)
spawn("Gate_Pillar_R", unreal.Vector(1500, -2000, 250), [1, 1, 5], mesh=cylinder_mesh)

print("Stealth Level Construction Complete!")
'''

if __name__ == "__main__":
    print("Building Stealth Coastal Mansion Level...")
    response = send_command('exec_editor_python', {'code': mansion_code})
    if response.get('status') == 'success':
        print(response.get('result', {}).get('output', ''))
    else:
        print(f"Error: {response.get('error')}")

