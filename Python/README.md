# Unreal MCP Python Server

Python MCP server for interacting with Unreal Engine 5.7 using the Model Context Protocol (MCP).

## Setup

1. Make sure Python 3.12+ is installed
2. Install `uv` (recommended) if you haven't already:
   - macOS/Linux:
     ```bash
     curl -LsSf https://astral.sh/uv/install.sh | sh
     ```
   - Windows (PowerShell):
     ```powershell
     irm https://astral.sh/uv/install.ps1 | iex
     ```
   - After install, close/reopen your terminal and verify:
     ```bash
     uv --version
     ```
3. Create and activate a virtual environment:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate     # On Windows
   ```
4. Install dependencies:
   ```bash
   uv pip install -e .
   ```

At this point, you can configure your MCP Client (Claude Desktop, Cursor, Windsurf) to use the Unreal MCP Server. See the [main README](../README.md#step-4-configure-your-mcp-client) for configuration details.

### No `uv`? (Fallback)

If you see `'uv' is not recognized...` you can use standard `venv` + `pip` instead:

```powershell
cd Python
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -U pip
pip install -e .
python -u unreal_mcp_server.py
```

## Testing Scripts

There are several example scripts in the [`scripts/`](./scripts) folder. These scripts connect directly to the Unreal Editor plugin via TCP (port 55557), so you don't need the MCP server running to test them.

Make sure you have installed dependencies and/or are running in the virtual environment for the scripts to work.

## Troubleshooting

- Make sure Unreal Engine editor is loaded and running before running the server
- Check logs in `unreal_mcp.log` (in the repository root) for detailed error information
- Ensure the UnrealMCP plugin is enabled in your Unreal project
- Verify PythonScriptPlugin is enabled (required dependency)

## Development

The server uses an **exec-first** architecture:
- The core tool is `exec_editor_python`, which executes Python code directly in Unreal Editor
- Foundation tools (like `focus_viewport`, `get_selected_actors`) are convenience wrappers that execute Python snippets
- To add new tools, create Python snippets in [`tools/snippets/`](./tools/snippets/) and register them in [`tools/snippets/_registry.py`](./tools/snippets/_registry.py)

See [`tools/snippets/README.md`](./tools/snippets/README.md) for snippet format guidelines.
