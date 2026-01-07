"""
Foundation Editor Tools for Unreal MCP (Exec-First Workflow).

All tools are convenience wrappers around exec_editor_python.

To keep tool logic maintainable, wrappers load Python snippet files from
`Python/tools/snippets/` instead of embedding large code strings.
"""

import logging
import json
from pathlib import Path
from typing import Dict, List, Any
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

_SNIPPETS_DIR = Path(__file__).resolve().parent / "snippets"

# Import registry (will be available after snippets are loaded)
try:
    import sys
    sys.path.insert(0, str(_SNIPPETS_DIR))
    from snippets._registry import get_snippet_filename, get_snippet_info
    sys.path.pop(0)
except ImportError:
    # Fallback if registry not available
    def get_snippet_filename(tool_name: str) -> str:
        return f"{tool_name}.py"


def _load_snippet(snippet_filename: str) -> str:
    """Load a snippet file from the snippets directory."""
    snippet_path = _SNIPPETS_DIR / snippet_filename
    if not snippet_path.exists():
        raise FileNotFoundError(f"Snippet file not found: {snippet_filename}")
    return snippet_path.read_text(encoding="utf-8")


def _extract_last_json_line(output: str) -> Dict[str, Any]:
    """
    Extract the last JSON object printed from stdout.
    
    Handles cases where snippets print debug logs before the final JSON result.
    """
    if not output:
        return {}
    
    lines = [ln.strip() for ln in output.strip().split("\n") if ln.strip()]
    
    # Try to find JSON starting from the end
    for line in reversed(lines):
        # Look for lines that look like JSON objects
        if line.startswith("{") and line.endswith("}"):
            try:
                parsed = json.loads(line)
                # Validate it's a result object
                if isinstance(parsed, dict) and "status" in parsed:
                    return parsed
            except (json.JSONDecodeError, ValueError):
                continue
    
    # If no valid JSON found, return empty dict (caller will handle error)
    return {}


def _exec_snippet(unreal_conn, snippet_filename: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute a snippet inside Unreal with MCP_PARAMS injected, and return the parsed JSON result.
    
    Args:
        unreal_conn: UnrealConnection instance
        snippet_filename: Name of snippet file (e.g., "focus_viewport.py")
        params: Parameters to inject as MCP_PARAMS
        
    Returns:
        Parsed JSON result from snippet, or error dict
    """
    try:
        snippet = _load_snippet(snippet_filename)
    except FileNotFoundError as e:
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"Error loading snippet {snippet_filename}: {e}")
        return {"status": "error", "error": f"Failed to load snippet: {e}"}
    
    params_json = json.dumps(params or {}, ensure_ascii=False)

    # Inject MCP_PARAMS then execute snippet.
    # Snippet must print a final json.dumps({...}) line.
    code = (
        "import json\n"
        "import sys\n"
        # Add snippets directory to path so snippets can import _lib
        f"sys.path.insert(0, r'''{_SNIPPETS_DIR}''')\n"
        f"MCP_PARAMS = json.loads(r'''{params_json}''')\n"
        "\n"
        f"{snippet}\n"
    )

    response = unreal_conn.send_command("exec_editor_python", {"code": code})
    canonical = _canonical_response(response)
    if canonical.get("status") != "success":
        return canonical

    result = canonical.get("result", {})
    if not isinstance(result, dict) or not result.get("success"):
        # exec failed; return error with details from error_output
        error_output = result.get("error_output", "")
        error_msg = result.get("error", "Python execution failed")
        if error_output:
            error_msg = f"{error_msg}\n{error_output}"
        return {"status": "error", "error": error_msg}

    parsed = _extract_last_json_line(result.get("output", ""))
    if parsed and parsed.get("status"):
        return parsed

    # If no valid JSON found, return error with output for debugging
    output = result.get("output", "")
    return {
        "status": "error",
        "error": "Snippet did not print a parseable JSON result",
        "details": {"output_preview": output[:500] if output else "No output"}
    }

def register_editor_tools(mcp: FastMCP):
    """Register foundation editor tools with the MCP server.
    
    All tools are convenience wrappers that generate Python code and execute it via exec_editor_python.
    """
    
    @mcp.tool()
    def exec_editor_python(ctx: Context, code: str) -> Dict[str, Any]:
        """
        Execute Python code in the Unreal Editor using PythonScriptPlugin.
        
        ⚠️ PRIMARY TOOL - This is the only direct C++ command. All other tools wrap this.
        See Python/tools/snippets/README.md for snippet format guidelines.
        
        WARNING: This tool allows execution of arbitrary Python code with full editor privileges.
        Only use with trusted MCP clients.
        
        Args:
            ctx: The MCP context
            code: Python code to execute (as a string)
            
        Returns:
            Dict with status="success"|"error", result.output containing stdout, 
            result.error_output containing stderr (if any), or error message on failure.
        """
        from unreal_mcp_server import get_unreal_connection
        
        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")
            
            if not code or not code.strip():
                return _canonical_response(None, "Python code cannot be empty")
            
            response = unreal.send_command("exec_editor_python", {
                "code": code
            })
            return _canonical_response(response)
            
        except Exception as e:
            logger.error(f"Error executing Python code: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def focus_viewport(
        ctx: Context,
        target: str = None,
        location: List[float] = None,
        distance: float = 1000.0,
        orientation: List[float] = None
    ) -> Dict[str, Any]:
        """
        Focus the viewport on a specific actor or location.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            target: Name or label of the actor to focus on (if provided, location is ignored)
            location: [X, Y, Z] coordinates to focus on (used if target is None)
            distance: Distance from the target/location (default: 1000.0)
            orientation: Optional [Pitch, Yaw, Roll] for the viewport camera
            
        Returns:
            Dict with status="success" or status="error"
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            if not target and not location:
                return _canonical_response(None, "Either 'target' or 'location' must be provided")

            snippet_filename = get_snippet_filename("focus_viewport")
            return _exec_snippet(
                unreal,
                snippet_filename,
                {
                    "target": target,
                    "location": location,
                    "distance": distance,
                    "orientation": orientation,
                },
            )
        except Exception as e:
            logger.error(f"Error focusing viewport: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def take_screenshot(
        ctx: Context,
        filepath: str
    ) -> Dict[str, Any]:
        """
        Capture a screenshot of the active viewport.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            filepath: Path where the screenshot will be saved (will add .png extension if missing)
            
        Returns:
            Dict with status="success" and result.filepath containing the saved file path
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            snippet_filename = get_snippet_filename("take_screenshot")
            return _exec_snippet(unreal, snippet_filename, {"filepath": filepath})
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def get_selected_actors(ctx: Context) -> Dict[str, Any]:
        """
        Get the currently selected actors in the editor.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            
        Returns:
            Dict with status="success" and result.actors containing list of actor objects
            with name, label, and path fields
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            snippet_filename = get_snippet_filename("get_selected_actors")
            return _exec_snippet(unreal, snippet_filename, {})
        except Exception as e:
            logger.error(f"Error getting selected actors: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def set_selected_actors(
        ctx: Context,
        actor_names: List[str]
    ) -> Dict[str, Any]:
        """
        Set the editor selection to the specified actors by name.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            actor_names: List of actor names or labels to select
            
        Returns:
            Dict with status="success" and result containing:
            - selected_count: Number of actors successfully selected
            - found: List of actor names that were found and selected
            - not_found: List of actor names that were not found (if any)
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            if not actor_names or not isinstance(actor_names, list):
                return _canonical_response(None, "actor_names must be a non-empty list")

            snippet_filename = get_snippet_filename("set_selected_actors")
            return _exec_snippet(unreal, snippet_filename, {"actor_names": actor_names})
        except Exception as e:
            logger.error(f"Error setting selected actors: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def clear_selection(ctx: Context) -> Dict[str, Any]:
        """
        Clear the current editor selection.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            
        Returns:
            Dict with status="success"
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            snippet_filename = get_snippet_filename("clear_selection")
            return _exec_snippet(unreal, snippet_filename, {})
        except Exception as e:
            logger.error(f"Error clearing selection: {e}")
            return _canonical_response(None, str(e))

    @mcp.tool()
    def get_current_level_info(
        ctx: Context,
        include_streaming: bool = True
    ) -> Dict[str, Any]:
        """
        Get information about the current level.
        
        This is a convenience wrapper that generates Python code using unreal.EditorLevelLibrary.
        
        Args:
            ctx: The MCP context
            include_streaming: Whether to include streaming levels info (default: True)
            
        Returns:
            Dict containing level path, actor count, dirty state, and streaming levels
        """
        from unreal_mcp_server import get_unreal_connection

        try:
            unreal = get_unreal_connection()
            if not unreal:
                return _canonical_response(None, "Failed to connect to Unreal Engine")

            snippet_filename = get_snippet_filename("get_current_level_info")
            return _exec_snippet(
                unreal, snippet_filename, {"include_streaming": include_streaming}
            )
        except Exception as e:
            logger.error(f"Error getting current level info: {e}")
            return _canonical_response(None, str(e))

    logger.info("Foundation editor tools registered successfully (snippets via exec_editor_python)")
