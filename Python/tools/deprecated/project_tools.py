"""
Project Tools for Unreal MCP.

This module provides tools for managing project-wide settings and configuration.
"""

import logging
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP, Context

# Get logger
logger = logging.getLogger("UnrealMCP")

def _canonical_response(response: Dict[str, Any] = None, error_msg: str = None) -> Dict[str, Any]:
    """Normalize response to canonical format: {status: "success"|"error", result?: {...}, error?: "..."}"""
    if error_msg:
        return {"status": "error", "error": error_msg}
    if not response:
        return {"status": "error", "error": "No response from Unreal Engine"}
    if response.get("status") == "error":
        return response
    if response.get("status") == "success":
        return response
    # Legacy format: wrap in canonical format
    return {"status": "success", "result": response}

def register_project_tools(mcp: FastMCP):
    """Register project tools with the MCP server."""
    
    @mcp.tool()
    def create_input_mapping(
        ctx: Context,
        action_name: str,
        key: str,
        input_type: str = "Action"
    ) -> Dict[str, Any]:
        """
        Create an input mapping for the project.
        
        Args:
            action_name: Name of the input action
            key: Key to bind (SpaceBar, LeftMouseButton, etc.)
            input_type: Type of input mapping (Action or Axis)
            
        Returns:
            Response indicating success or failure
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")
            
            params = {
                "action_name": action_name,
                "key": key,
                "input_type": input_type
            }
            
            logger.info(f"Creating input mapping '{action_name}' with key '{key}'")
            response = unreal.send_command("create_input_mapping", params)
            return _canonical_response(response)
            
        except Exception as e:
            logger.error(f"Error creating input mapping: {e}")
            return _canonical_response(None, str(e))
    
    logger.info("Project tools registered successfully") 