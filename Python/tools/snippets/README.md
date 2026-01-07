# Editor Tool Snippets (Exec-First)

These snippets are executed inside Unreal Editor via the `exec_editor_python` command.

## Contract

- Each snippet receives parameters through a global `MCP_PARAMS` dict injected by the Python MCP server.
- Each snippet must `print(json.dumps({...}))` as its final output.
- The tool wrapper will parse the last JSON object printed and return it as the tool result.
- Use structured error responses: `{"status": "error", "error": "message"}`

## Snippet Registry

All snippets must be registered in `Python/tools/snippets/_registry.py`:

```python
SNIPPET_REGISTRY = {
    "my_tool": (
        "my_tool.py",  # Filename
        "Description of what the tool does",  # Description
        {"param1": "str (required) - Description"}  # Parameter schema
    ),
}
```

## Shared Helpers

Snippets can import shared utilities from `snippets._lib`:

```python
from snippets._lib import find_actor_by_name_or_label, print_json_result, safe_get_mcp_param

# Find an actor
actor = find_actor_by_name_or_label("MyActor")
if not actor:
    print_json_result("error", error="Actor not found")
    exit()

# Get MCP parameter with default
distance = safe_get_mcp_param("distance", 1000.0)

# Print result
print_json_result("success", result={"actor": actor.get_name()})
```

## Example

```python
import json
import unreal
from snippets._lib import find_actor_by_name_or_label, print_json_result, safe_get_mcp_param

try:
    target = safe_get_mcp_param("target", "")
    if not target:
        print_json_result("error", error="'target' parameter is required")
    else:
        actor = find_actor_by_name_or_label(target)
        if actor:
            print_json_result("success", result={"found": actor.get_name()})
        else:
            print_json_result("error", error=f"Actor '{target}' not found")
except Exception as e:
    print_json_result("error", error=str(e))
```


