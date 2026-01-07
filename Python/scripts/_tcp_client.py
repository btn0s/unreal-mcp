"""
Shared TCP client helper for connecting to Unreal Engine MCP server.

This module provides a simple interface for sending commands to Unreal Engine
via the TCP connection (port 55557). Used by test scripts and golden-path examples.
"""

import socket
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("TCPClient")

# Default connection settings
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 55557
DEFAULT_TIMEOUT = 30.0


def send_command(
    command: str,
    params: Dict[str, Any] = None,
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT
) -> Optional[Dict[str, Any]]:
    """
    Send a command to the Unreal Engine MCP server and get the response.
    
    Args:
        command: Command type (e.g., "exec_editor_python", "spawn_actor")
        params: Command parameters dictionary
        host: Server hostname (default: 127.0.0.1)
        port: Server port (default: 55557)
        timeout: Socket timeout in seconds (default: 30.0)
    
    Returns:
        Response dictionary with status and result/error, or None on connection failure
    """
    sock = None
    try:
        # Create socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        sock.connect((host, port))
        
        # Create command object
        command_obj = {
            "type": command,
            "params": params or {}
        }
        
        # Send command
        command_json = json.dumps(command_obj)
        logger.debug(f"Sending command: {command_json}")
        sock.sendall(command_json.encode('utf-8'))
        
        # Receive response (handle chunked data)
        chunks = []
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                if not chunks:
                    raise Exception("Connection closed before receiving data")
                break
            chunks.append(chunk)
            
            # Try parsing to check if we have complete JSON
            try:
                data = b''.join(chunks)
                decoded = data.decode('utf-8')
                json.loads(decoded)
                # Complete JSON received
                break
            except json.JSONDecodeError:
                # Not complete yet, continue receiving
                continue
        
        # Parse response
        data = b''.join(chunks)
        response = json.loads(data.decode('utf-8'))
        logger.debug(f"Received response: {response}")
        return response
        
    except socket.timeout:
        logger.error(f"Timeout connecting to {host}:{port}")
        return None
    except ConnectionRefusedError:
        logger.error(f"Connection refused to {host}:{port}. Is Unreal Editor running with the plugin loaded?")
        return None
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return None
    finally:
        if sock:
            try:
                sock.close()
            except:
                pass

