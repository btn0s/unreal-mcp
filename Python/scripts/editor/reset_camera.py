#!/usr/bin/env python
"""Reset camera to mansion view."""
import socket
import json

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

reset_code = """
import unreal
loc = unreal.Vector(2000, -2000, 1000)
rot = unreal.Rotator(-20, 135, 0)
unreal.EditorLevelLibrary.set_level_viewport_camera_info(loc, rot)
print("Camera reset to mansion view")
"""

response = send_command('exec_editor_python', {'code': reset_code})
print(response.get('result', {}).get('output', ''))
