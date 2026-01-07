"""
Unreal Engine MCP Server

A simple MCP server for interacting with Unreal Engine.
"""

import logging
import socket
import sys
import json
from contextlib import asynccontextmanager
from typing import AsyncIterator, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP

# Configure logging with more detailed format
logging.basicConfig(
    level=logging.DEBUG,  # Change to DEBUG level for more details
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.FileHandler('unreal_mcp.log'),
        # logging.StreamHandler(sys.stdout) # Remove this handler to unexpected non-whitespace characters in JSON
    ]
)
logger = logging.getLogger("UnrealMCP")

# Configuration
UNREAL_HOST = "127.0.0.1"
UNREAL_PORT = 55557
# Unreal Editor operations (asset loads, blueprint compilation/spawn, screenshots) can easily take
# longer than a few seconds. The MCP server must wait long enough for Unreal to respond.
UNREAL_SOCKET_TIMEOUT_SECONDS = 30

class UnrealConnection:
    """Connection to an Unreal Engine instance."""
    
    def __init__(self):
        """Initialize the connection."""
        self.socket = None
        self.connected = False
    
    def connect(self) -> bool:
        """Connect to the Unreal Engine instance."""
        try:
            # Close any existing socket
            if self.socket:
                try:
                    self.socket.close()
                except:
                    pass
                self.socket = None
            
            logger.info(f"Connecting to Unreal at {UNREAL_HOST}:{UNREAL_PORT}...")
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(UNREAL_SOCKET_TIMEOUT_SECONDS)
            
            # Set socket options for better stability
            self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            
            # Set larger buffer sizes
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
            
            self.socket.connect((UNREAL_HOST, UNREAL_PORT))
            self.connected = True
            logger.info("Connected to Unreal Engine")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to Unreal: {e}")
            self.connected = False
            return False
    
    def disconnect(self):
        """Disconnect from the Unreal Engine instance."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
        self.socket = None
        self.connected = False

    def receive_full_response(self, sock, buffer_size=4096) -> bytes:
        """Receive a complete response from Unreal, handling chunked data."""
        chunks = []
        sock.settimeout(UNREAL_SOCKET_TIMEOUT_SECONDS)
        try:
            while True:
                chunk = sock.recv(buffer_size)
                if not chunk:
                    if not chunks:
                        raise Exception("Connection closed before receiving data")
                    break
                chunks.append(chunk)
                
                # Process the data received so far
                data = b''.join(chunks)
                decoded_data = data.decode('utf-8')
                
                # Try to parse as JSON to check if complete
                try:
                    json.loads(decoded_data)
                    logger.info(f"Received complete response ({len(data)} bytes)")
                    return data
                except json.JSONDecodeError:
                    # Not complete JSON yet, continue reading
                    logger.debug(f"Received partial response, waiting for more data...")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing response chunk: {str(e)}")
                    continue
        except socket.timeout:
            logger.warning("Socket timeout during receive")
            if chunks:
                # If we have some data already, try to use it
                data = b''.join(chunks)
                try:
                    json.loads(data.decode('utf-8'))
                    logger.info(f"Using partial response after timeout ({len(data)} bytes)")
                    return data
                except:
                    pass
            raise Exception("Timeout receiving Unreal response")
        except Exception as e:
            logger.error(f"Error during receive: {str(e)}")
            raise
    
    def send_command(self, command: str, params: Dict[str, Any] = None) -> Optional[Dict[str, Any]]:
        """Send a command to Unreal Engine and get the response."""
        # Always reconnect for each command, since Unreal closes the connection after each command
        # This is different from Unity which keeps connections alive
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
        
        if not self.connect():
            logger.error("Failed to connect to Unreal Engine for command")
            return None
        
        try:
            # Match Unity's command format exactly
            command_obj = {
                "type": command,  # Use "type" instead of "command"
                "params": params or {}  # Use Unity's params or {} pattern
            }
            
            # Send without newline, exactly like Unity
            command_json = json.dumps(command_obj)
            logger.info(f"Sending command: {command_json}")
            self.socket.sendall(command_json.encode('utf-8'))
            
            # Read response using improved handler
            response_data = self.receive_full_response(self.socket)
            response = json.loads(response_data.decode('utf-8'))
            
            # Log complete response for debugging
            logger.info(f"Complete response from Unreal: {response}")
            
            # Normalize to canonical response schema: {status: "success"|"error", result?: {...}, error?: "..."}
            canonical_response: Dict[str, Any] = {}
            
            if response.get("status") == "error":
                # Already in canonical error format
                canonical_response = {
                    "status": "error",
                    "error": response.get("error") or response.get("message", "Unknown Unreal error")
                }
                if "details" in response:
                    canonical_response["details"] = response["details"]
                logger.error(f"Unreal error: {canonical_response['error']}")
            elif response.get("status") == "success":
                # Already in canonical success format
                canonical_response = {
                    "status": "success",
                    "result": response.get("result", {})
                }
            elif response.get("success") is False:
                # Legacy format: convert to canonical error format
                error_message = response.get("error") or response.get("message", "Unknown Unreal error")
                canonical_response = {
                    "status": "error",
                    "error": error_message
                }
                logger.error(f"Unreal error (legacy format): {error_message}")
            else:
                # Assume success if no status/success field (legacy behavior)
                canonical_response = {
                    "status": "success",
                    "result": response
                }
            
            # Always close the connection after command is complete
            # since Unreal will close it on its side anyway
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            self.connected = False
            
            return canonical_response
            
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            # Always reset connection state on any error
            self.connected = False
            try:
                self.socket.close()
            except:
                pass
            self.socket = None
            return {
                "status": "error",
                "error": str(e)
            }

# Global connection state
_unreal_connection: UnrealConnection = None

def get_unreal_connection() -> Optional[UnrealConnection]:
    """Get the connection to Unreal Engine."""
    global _unreal_connection
    try:
        if _unreal_connection is None:
            _unreal_connection = UnrealConnection()
            if not _unreal_connection.connect():
                logger.warning("Could not connect to Unreal Engine")
                _unreal_connection = None
        else:
            # Verify connection is still valid with a real ping command
            try:
                ping_response = _unreal_connection.send_command("ping", {})
                if ping_response and ping_response.get("status") == "success":
                    logger.debug("Connection verified with ping command")
                else:
                    raise Exception("Ping command failed or returned error")
            except Exception as e:
                logger.warning(f"Existing connection failed: {e}")
                _unreal_connection.disconnect()
                _unreal_connection = None
                # Try to reconnect
                _unreal_connection = UnrealConnection()
                if not _unreal_connection.connect():
                    logger.warning("Could not reconnect to Unreal Engine")
                    _unreal_connection = None
                else:
                    logger.info("Successfully reconnected to Unreal Engine")
        
        return _unreal_connection
    except Exception as e:
        logger.error(f"Error getting Unreal connection: {e}")
        return None

@asynccontextmanager
async def server_lifespan(server: FastMCP) -> AsyncIterator[Dict[str, Any]]:
    """Handle server startup and shutdown."""
    global _unreal_connection
    logger.info("UnrealMCP server starting up")
    try:
        _unreal_connection = get_unreal_connection()
        if _unreal_connection:
            logger.info("Connected to Unreal Engine on startup")
        else:
            logger.warning("Could not connect to Unreal Engine on startup")
    except Exception as e:
        logger.error(f"Error connecting to Unreal Engine on startup: {e}")
        _unreal_connection = None
    
    try:
        yield {}
    finally:
        if _unreal_connection:
            _unreal_connection.disconnect()
            _unreal_connection = None
        logger.info("Unreal MCP server shut down")

# Initialize server
mcp = FastMCP(
    "UnrealMCP",
    instructions="Unreal Engine integration via Model Context Protocol",
    lifespan=server_lifespan
)

# Import and register tools (foundation set only - exec-first workflow)
from tools.editor_tools import register_editor_tools

# Register foundation tools only
# Note: Blueprint/UMG/node/project tools are deprecated in favor of exec_editor_python
register_editor_tools(mcp)  

@mcp.prompt()
def info():
    """Information about available Unreal MCP tools and best practices."""
    return """
    # Unreal MCP Server - Exec-First Workflow
    
    ## ⚠️ SECURITY WARNING
    
    **CRITICAL:** The `exec_editor_python` tool executes arbitrary Python code with **full editor privileges**. Only use with trusted MCP clients. The Python code has complete access to your Unreal project and can modify or delete assets.
    
    ## Recommended Workflow: Ask → Research → Execute → Verify
    
    The Unreal MCP server follows an **exec-first** philosophy. For maximum flexibility and power, use `exec_editor_python` as your primary tool, following this loop:
    
    1. **Ask**: Understand what the user wants to accomplish
    2. **Research**: Use read-only Python queries to inspect the current state (actors, assets, selection, level info)
    3. **Execute**: Perform edits wrapped in transactions, with idempotent operations where possible
    4. **Verify**: Re-query state and optionally capture screenshots to confirm results
    
    ## Primary Tool: exec_editor_python
    
    **Use this tool for 95% of Unreal operations.** It provides direct access to the full Unreal Python API (`unreal.EditorLevelLibrary`, `unreal.EditorAssetLibrary`, etc.).
    
    ### Exec Tool Contract
    
    When using `exec_editor_python`, follow these conventions:
    
    - **Transactions**: Wrap all edits in `unreal.ScopedEditorTransaction("description")` for undo/redo support
    - **Idempotency**: Design operations to be safe when run multiple times (check existence before creating)
    - **Asset Path Validation**: Always validate asset paths before operations (use `/Game/` prefix for project assets)
    - **Structured Output**: Always end your Python code by printing a final JSON object:
      ```python
      import json
      result = {"status": "success", "result": {...}}  # or {"status": "error", "error": "message"}
      print(json.dumps(result))
      ```
    
    ### Example Workflow
    
    ```python
    import unreal
    import json
    
    # RESEARCH: Check current state
    actors = unreal.EditorLevelLibrary.get_all_level_actors()
    actor_count = len(actors)
    
    # EXECUTE: Make changes in a transaction
    with unreal.ScopedEditorTransaction("Add test actor"):
        if actor_count < 10:  # Idempotent check
            location = unreal.Vector(0, 0, 100)
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor, location
            )
            actor.set_actor_label("TestActor")
    
    # VERIFY: Confirm results
    new_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    result = {
        "status": "success",
        "result": {
            "actors_before": actor_count,
            "actors_after": len(new_actors),
            "created": actor_count < 10
        }
    }
    print(json.dumps(result))
    ```
    
    ## Specialized Tools (Use When Needed)
    
    These tools provide convenience wrappers for common operations. Use them when:
    - You need guaranteed parameter validation
    - You want explicit tool schemas for better client-side autocomplete
    - The operation is frequently repeated and benefits from a dedicated wrapper
    
    ### Editor Tools
    - `get_actors_in_level()` - List all actors in current level
    - `find_actors_by_name(pattern)` - Find actors by name pattern
    - `spawn_actor(name, type, location=[0,0,0], rotation=[0,0,0])` - Create actors
    - `delete_actor(name)` - Remove actors
    - `set_actor_transform(name, location, rotation, scale)` - Modify actor transform
    - `get_actor_properties(name)` - Get actor properties
    - `create_level(level_name, folder, template_level, open_after_create)` - Create new level
    - `open_level(level, save_dirty)` - Open a level
    - `save_current_level()` - Save current level
    - `get_current_level_info(include_streaming)` - Get level information
    
    ### Blueprint Tools
    - `create_blueprint(name, parent_class)` - Create new Blueprint classes
    - `add_component_to_blueprint(blueprint_name, component_type, component_name, ...)` - Add components
    - `compile_blueprint(blueprint_name)` - Compile Blueprint changes
    - `spawn_blueprint_actor(blueprint_name, actor_name, location, rotation)` - Spawn Blueprint actors
    
    ### UMG Widget Tools
    - `create_umg_widget_blueprint(widget_name, parent_class, path)` - Create Widget Blueprint
    - `add_text_block_to_widget(widget_name, text_block_name, ...)` - Add Text Block
    - `add_button_to_widget(widget_name, button_name, ...)` - Add Button
    - `bind_widget_event(widget_name, widget_component_name, event_name, function_name)` - Bind events
    
    ## Best Practices
    
    ### Research Phase
    - Always query current state before making changes
    - Use `unreal.EditorLevelLibrary.get_selected_level_actors()` to check selection
    - Use `unreal.EditorAssetLibrary.does_asset_exist(path)` before asset operations
    - Use `unreal.EditorLevelLibrary.get_all_level_actors()` to enumerate actors
    
    ### Execute Phase
    - Wrap all edits in `unreal.ScopedEditorTransaction("description")`
    - Make operations idempotent (check before create, validate before modify)
    - Use descriptive transaction names for undo/redo clarity
    - Validate asset paths (project assets use `/Game/` prefix)
    
    ### Verify Phase
    - Re-query state after operations to confirm changes
    - Print structured JSON results for client parsing
    - Consider taking screenshots for visual verification (if `take_screenshot` tool available)
    
    ### Error Handling
    - Use try/except blocks in Python code
    - Always return structured JSON even on errors: `{"status": "error", "error": "message"}`
    - Validate inputs before operations (actor existence, asset paths, etc.)
    
    ## Documentation
    
    For detailed examples and snippet format guidelines, see:
    - Python/tools/snippets/README.md
    - Python/tools/editor_tools.py
    """

# Run the server
if __name__ == "__main__":
    logger.info("Starting MCP server with stdio transport")
    mcp.run(transport='stdio') 