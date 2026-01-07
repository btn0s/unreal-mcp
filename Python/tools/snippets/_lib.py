"""
Shared helper functions for Unreal MCP snippets.

This module provides common utilities that snippets can use.
Import this in snippets via: `from snippets._lib import ...`
"""

import unreal
import json


def find_actor_by_name_or_label(name_or_label: str):
    """
    Find an actor by its name or label.
    
    Args:
        name_or_label: Actor name or label to search for
        
    Returns:
        Actor object if found, None otherwise
    """
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    for actor in all_actors:
        if actor.get_name() == name_or_label or actor.get_actor_label() == name_or_label:
            return actor
    return None


def print_json_result(status: str, result: dict = None, error: str = None):
    """
    Print a standardized JSON result to stdout.
    
    Args:
        status: "success" or "error"
        result: Result dictionary (for success)
        error: Error message (for error)
    """
    if status == "success":
        output = {"status": "success", "result": result or {}}
    else:
        output = {"status": "error", "error": error or "Unknown error"}
    print(json.dumps(output))


def safe_get_mcp_param(key: str, default=None):
    """
    Safely get a parameter from MCP_PARAMS with a default value.
    
    Args:
        key: Parameter key
        default: Default value if key not found
        
    Returns:
        Parameter value or default
    """
    try:
        return MCP_PARAMS.get(key, default)
    except NameError:
        return default

