# Deprecated Tool Modules

These tool modules are deprecated in favor of the exec-first workflow.

All functionality should now be implemented using `exec_editor_python` with Python snippets in `Python/tools/snippets/`.

These files are kept for reference only and are not imported or registered by the MCP server.

## Deprecated Modules

- `blueprint_tools.py` - Blueprint creation and manipulation tools
- `node_tools.py` - Blueprint graph node manipulation tools  
- `project_tools.py` - Project-level configuration tools
- `umg_tools.py` - UMG widget creation tools

## Migration Path

Instead of adding new tools to these modules:

1. Create a Python snippet in `Python/tools/snippets/` that implements the functionality
2. Add a wrapper tool in `Python/tools/editor_tools.py` that loads and executes the snippet
3. See `Python/tools/snippets/README.md` for snippet format guidelines

