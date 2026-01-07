"""
Snippet Registry

Maps tool names to their snippet filenames and optional metadata.
This is the single source of truth for which snippets exist.
"""

# Registry: tool_name -> (snippet_filename, description, param_schema)
SNIPPET_REGISTRY = {
    "focus_viewport": (
        "focus_viewport.py",
        "Focus the viewport on an actor or location",
        {
            "target": "str (optional) - Actor name/label",
            "location": "List[float] (optional) - [X, Y, Z] coordinates",
            "distance": "float (default: 1000.0) - Distance from target",
            "orientation": "List[float] (optional) - [Pitch, Yaw, Roll]"
        }
    ),
    "take_screenshot": (
        "take_screenshot.py",
        "Capture a screenshot of the active viewport",
        {
            "filepath": "str (required) - Path where screenshot will be saved"
        }
    ),
    "get_selected_actors": (
        "get_selected_actors.py",
        "Get currently selected actors in the editor",
        {}
    ),
    "set_selected_actors": (
        "set_selected_actors.py",
        "Set editor selection to specified actors",
        {
            "actor_names": "List[str] (required) - List of actor names/labels to select"
        }
    ),
    "clear_selection": (
        "clear_selection.py",
        "Clear the current editor selection",
        {}
    ),
    "get_current_level_info": (
        "get_current_level_info.py",
        "Get information about the current level",
        {
            "include_streaming": "bool (default: True) - Include streaming levels info"
        }
    ),
    "search_unreal_docs": (
        "search_unreal_docs.py",
        "Search Unreal Engine Python API documentation",
        {
            "query": "str (required) - Search term (module, class, or function name)"
        }
    ),
}


def get_snippet_filename(tool_name: str) -> str:
    """Get the snippet filename for a tool name."""
    if tool_name not in SNIPPET_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return SNIPPET_REGISTRY[tool_name][0]


def get_snippet_info(tool_name: str) -> tuple:
    """Get full snippet info (filename, description, param_schema) for a tool."""
    if tool_name not in SNIPPET_REGISTRY:
        raise ValueError(f"Unknown tool: {tool_name}")
    return SNIPPET_REGISTRY[tool_name]


def list_all_snippets() -> dict:
    """List all registered snippets with their metadata."""
    return {
        name: {
            "filename": info[0],
            "description": info[1],
            "params": info[2]
        }
        for name, info in SNIPPET_REGISTRY.items()
    }

