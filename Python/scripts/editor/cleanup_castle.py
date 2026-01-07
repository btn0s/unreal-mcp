#!/usr/bin/env python
"""
Cleanup script to delete castle actors.
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

cleanup_code = '''
import unreal

# Find all actors starting with "Castle"
actors = unreal.EditorLevelLibrary.get_all_level_actors()
to_delete = [a for a in actors if a.get_actor_label().startswith("Castle")]

for actor in to_delete:
    print(f"Deleting {actor.get_actor_label()}...")
    unreal.EditorLevelLibrary.destroy_actor(actor)

print(f"Deleted {len(to_delete)} castle actors.")
'''

if __name__ == "__main__":
    print("Deleting castle...")
    response = send_command('exec_editor_python', {'code': cleanup_code})
    if response.get('status') == 'success':
        print(response.get('result', {}).get('output', ''))
    else:
        print(f"Error: {response.get('error')}")

