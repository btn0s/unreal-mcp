#!/usr/bin/env python
"""
Test script for level CRUD operations in Unreal Engine via MCP.

This script demonstrates the level management capabilities:
- Creating a new level from a template
- Opening a level
- Getting level information
- Saving levels
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
logger = logging.getLogger("TestLevels")

def send_command(command: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Send a command to the Unreal MCP server and get the response.
    
    Args:
        command: The command type to send
        params: Dictionary of parameters for the command
        
    Returns:
        Optional[Dict[str, Any]]: The response from the server, or None if there was an error
    """
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

def create_level(
    level_name: str,
    folder: Optional[str] = None,
    template_level: Optional[str] = None,
    open_after_create: bool = True
) -> Optional[Dict[str, Any]]:
    """Create a new level from a template.
    
    Args:
        level_name: Name of the new level
        folder: Optional folder path (defaults to /Game/Maps)
        template_level: Optional template level path
        open_after_create: Whether to open after creation
        
    Returns:
        Optional[Dict[str, Any]]: The response from create command, or None if failed
    """
    params = {
        "level_name": level_name,
        "open_after_create": open_after_create
    }
    
    if folder is not None:
        params["folder"] = folder
    if template_level is not None:
        params["template_level"] = template_level
    
    response = send_command("create_level", params)
    if not response or response.get("status") == "error":
        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"Failed to create level: {error_msg}")
        return None
        
    logger.info(f"Created level '{level_name}' successfully")
    return response

def open_level(level: str, save_dirty: bool = True) -> Optional[Dict[str, Any]]:
    """Open a level in the editor.
    
    Args:
        level: Level name or path
        save_dirty: Whether to save dirty levels first
        
    Returns:
        Optional[Dict[str, Any]]: The response from open command, or None if failed
    """
    params = {
        "level": level,
        "save_dirty": save_dirty
    }
    
    response = send_command("open_level", params)
    if not response or response.get("status") == "error":
        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"Failed to open level: {error_msg}")
        return None
        
    logger.info(f"Opened level '{level}' successfully")
    return response

def get_current_level_info(include_streaming: bool = True) -> Optional[Dict[str, Any]]:
    """Get information about the current level.
    
    Args:
        include_streaming: Whether to include streaming levels info
        
    Returns:
        Optional[Dict[str, Any]]: The level info, or None if failed
    """
    params = {
        "include_streaming": include_streaming
    }
    
    response = send_command("get_current_level_info", params)
    if not response or response.get("status") == "error":
        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"Failed to get level info: {error_msg}")
        return None
        
    logger.info("Got current level info successfully")
    return response

def save_current_level() -> Optional[Dict[str, Any]]:
    """Save the current level.
    
    Returns:
        Optional[Dict[str, Any]]: The response from save command, or None if failed
    """
    response = send_command("save_current_level", {})
    if not response or response.get("status") == "error":
        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"Failed to save current level: {error_msg}")
        return None
        
    logger.info("Saved current level successfully")
    return response

def save_all_levels() -> Optional[Dict[str, Any]]:
    """Save all dirty levels.
    
    Returns:
        Optional[Dict[str, Any]]: The response from save command, or None if failed
    """
    response = send_command("save_all_levels", {})
    if not response or response.get("status") == "error":
        error_msg = response.get("error", "Unknown error") if response else "No response"
        logger.error(f"Failed to save all levels: {error_msg}")
        return None
        
    logger.info("Saved all levels successfully")
    return response

def main():
    """Main function to test level operations."""
    try:
        # Get current level info first
        logger.info("=== Getting current level info ===")
        current_info = get_current_level_info()
        if current_info:
            result = current_info.get("result", {})
            logger.info(f"Current level: {result.get('persistent_level_path', 'Unknown')}")
            logger.info(f"Actor count: {result.get('actor_count', 0)}")
            logger.info(f"Is dirty: {result.get('is_dirty', False)}")
        
        # Create a new test level
        logger.info("\n=== Creating new test level ===")
        test_level_name = "MCP_TestLevel"
        created = create_level(test_level_name, open_after_create=True)
        if not created:
            logger.error("Failed to create test level")
            return
        
        # Wait a moment for level to open
        time.sleep(1)
        
        # Get info about the newly created level
        logger.info("\n=== Getting info about new level ===")
        new_info = get_current_level_info()
        if new_info:
            result = new_info.get("result", {})
            logger.info(f"Current level: {result.get('persistent_level_path', 'Unknown')}")
            logger.info(f"Actor count: {result.get('actor_count', 0)}")
            
            streaming_levels = result.get("streaming_levels", [])
            logger.info(f"Streaming levels: {len(streaming_levels)}")
            for sl in streaming_levels:
                logger.info(f"  - {sl.get('package', 'Unknown')} (loaded: {sl.get('loaded', False)}, visible: {sl.get('visible', False)})")
        
        # Save the current level
        logger.info("\n=== Saving current level ===")
        save_result = save_current_level()
        if not save_result:
            logger.error("Failed to save current level")
            return
        
        # Test opening the level again (should already be open, but test the command)
        logger.info("\n=== Testing open_level command ===")
        open_result = open_level(test_level_name, save_dirty=False)
        if not open_result:
            logger.error("Failed to open level")
            return
        
        logger.info("\n=== All level operations completed successfully! ===")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

