#!/usr/bin/env python
"""
Test script for exec_editor_python command.

This script demonstrates the Python execution capability:
- Execute simple Python code
- Use Unreal Python API to manipulate actors
- Verify output and error handling
"""

import sys
import os
import time
import socket
import json
import logging
from typing import Dict, Any, Optional

# Add the parent directory to the path so we can import the server module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("TestExecEditorPython")

def send_command(command: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send a command to the Unreal MCP server and get the response."""
    try:
        # Create new socket connection
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(("127.0.0.1", 55557))
        
        try:
            # Create command object
            command_obj = {
                "type": command,
                "params": params
            }
            
            # Convert to JSON and send
            command_json = json.dumps(command_obj)
            logger.info(f"Sending command: {command_json}")
            sock.sendall(command_json.encode('utf-8'))
            
            # Receive response
            chunks = []
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                
                # Try parsing to see if we have a complete response
                try:
                    data = b''.join(chunks)
                    json.loads(data.decode('utf-8'))
                    # If we can parse it, we have the complete response
                    break
                except json.JSONDecodeError:
                    # Not a complete JSON object yet, continue receiving
                    continue
            
            # Parse response
            data = b''.join(chunks)
            response = json.loads(data.decode('utf-8'))
            logger.info(f"Received response: {response}")
            return response
            
        finally:
            # Always close the socket
            sock.close()
            
    except Exception as e:
        logger.error(f"Error sending command: {e}")
        return None

def test_simple_python():
    """Test executing simple Python code."""
    logger.info("Testing simple Python execution...")
    
    python_code = """
print("Hello from Unreal Editor Python!")
result = 2 + 2
print(f"2 + 2 = {result}")
"""
    
    response = send_command("exec_editor_python", {"code": python_code})
    
    if not response:
        logger.error("No response received")
        return False
    
    if response.get("status") != "success":
        logger.error(f"Command failed: {response.get('error', 'Unknown error')}")
        return False
    
    result = response.get("result", {})
    if result.get("success"):
        output = result.get("output", "")
        logger.info(f"Python output: {output}")
        if "Hello from Unreal Editor Python!" in output and "2 + 2 = 4" in output:
            logger.info("✓ Simple Python execution test passed")
            return True
        else:
            logger.warning("Python executed but output doesn't match expected")
            return False
    else:
        logger.error(f"Python execution failed: {result.get('error', 'Unknown error')}")
        return False

def test_unreal_api():
    """Test using Unreal Python API to create an actor."""
    logger.info("Testing Unreal Python API...")
    
    python_code = """
import unreal

# Get all actors before
actors_before = unreal.EditorLevelLibrary.get_all_level_actors()
count_before = len(actors_before)

# Create a test actor using Python API
actor_class = unreal.StaticMeshActor
location = unreal.Vector(500.0, 500.0, 200.0)
rotation = unreal.Rotator(0.0, 45.0, 0.0)
new_actor = unreal.EditorLevelLibrary.spawn_actor_from_class(actor_class, location, rotation)
new_actor.set_actor_label("PythonTestActor")

# Get all actors after
actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
count_after = len(actors_after)

print(f"Actors before: {count_before}, after: {count_after}")
print(f"Created actor: {new_actor.get_actor_label()}")
"""
    
    response = send_command("exec_editor_python", {"code": python_code})
    
    if not response:
        logger.error("No response received")
        return False
    
    if response.get("status") != "success":
        logger.error(f"Command failed: {response.get('error', 'Unknown error')}")
        return False
    
    result = response.get("result", {})
    if result.get("success"):
        output = result.get("output", "")
        logger.info(f"Python output: {output}")
        if "Created actor: PythonTestActor" in output:
            logger.info("✓ Unreal API test passed")
            return True
        else:
            logger.warning("Python executed but actor creation may have failed")
            logger.warning(f"Output: {output}")
            return False
    else:
        error_output = result.get("error", "")
        logger.error(f"Python execution failed: {error_output}")
        return False

def test_error_handling():
    """Test error handling for invalid Python code."""
    logger.info("Testing error handling...")
    
    python_code = """
# This will cause a syntax error
print("Missing quote)
"""
    
    response = send_command("exec_editor_python", {"code": python_code})
    
    if not response:
        logger.error("No response received")
        return False
    
    result = response.get("result", {})
    # Error handling should return success=false
    if not result.get("success"):
        error_output = result.get("error", "")
        logger.info(f"✓ Error correctly caught: {error_output}")
        return True
    else:
        logger.warning("Error was not properly caught")
        return False

def main():
    """Main function to run all tests."""
    logger.info("Starting exec_editor_python tests...")
    
    try:
        # Test 1: Simple Python execution
        if not test_simple_python():
            logger.error("Simple Python test failed")
            return False
        
        # Test 2: Unreal API usage
        if not test_unreal_api():
            logger.error("Unreal API test failed")
            return False
        
        # Test 3: Error handling
        if not test_error_handling():
            logger.error("Error handling test failed")
            return False
        
        logger.info("All tests passed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

