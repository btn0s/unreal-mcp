<div align="center">

# Model Context Protocol for Unreal Engine
<span style="color: #555555">unreal-mcp</span>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.7-orange)](https://www.unrealengine.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-Experimental-red)](https://github.com/chongdashu/unreal-mcp)

</div>

Control Unreal Engine through natural language using AI assistants (Cursor, Claude Desktop, Windsurf). Execute Python directly in Unreal Editor via the Model Context Protocol.

**Architecture:** AI Client ↔ Python MCP Server ↔ C++ Plugin ↔ Unreal Editor Python API

> [!WARNING]
> **SECURITY NOTICE: This tool executes arbitrary Python code with full Unreal Editor privileges.**
> 
> - 🚫 **Local development only** - Never expose to untrusted networks
> - 🔒 **No sandboxing** - Complete access to your project and file system  
> - ⚠️ **Experimental software** - Use at your own risk
> - 👁️ **Review AI-generated code** when possible
>
> Only use with trusted AI assistants in controlled development environments.

---

## 🚀 Quick Start

### Prerequisites

- Unreal Engine 5.6+ (tested on 5.7)
- Python 3.10+ with pip
- MCP Client (Cursor, Claude Desktop, or Windsurf)
- Visual Studio (for plugin builds)

### Installation

**1. Clone and setup plugin:**

```bash
git clone https://github.com/chongdashu/unreal-mcp.git
cd unreal-mcp
npm install
npm run build-plugin
npm run install-plugin  # Interactive - select your .uproject
```

Or use the included sample project: Open `MCPGameProject/MCPGameProject.uproject`

**2. Start Python MCP server:**

```bash
pip install -e Python/
python Python/unreal_mcp_server.py
```

**3. Configure your AI client:**

```bash
npm run mcp-deeplink  # Generates config for your system
```

Copy the generated config to your MCP client's settings file:
- **Cursor**: `.cursor/mcp.json` (project root)
- **Claude Desktop**: `~/.config/claude-desktop/mcp.json` (Mac/Linux) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- **Windsurf**: `~/.config/windsurf/mcp.json` (Mac/Linux) or `%USERPROFILE%\.config\windsurf\mcp.json` (Windows)

**4. Verify:**

In your AI chat, try: *"Get the current level info"* or *"List all actors in the scene"*

---

## 💡 Usage

Control Unreal through natural language. The AI automatically generates and executes Python code:

```
You: "Spawn a cube at (100, 200, 50)"
AI:  Uses exec_editor_python to create StaticMeshActor

You: "Focus the viewport on the actor named 'PlayerStart'"
AI:  Uses focus_viewport tool

You: "Create a blueprint with a static mesh component"
AI:  Generates Python code using Unreal's Blueprint API
```

**Available Foundation Tools:**
- `get_selected_actors` - Query editor selection
- `set_selected_actors` - Set selection by actor names
- `clear_selection` - Clear selection
- `focus_viewport` - Focus camera on actor/location
- `take_screenshot` - Capture viewport
- `get_current_level_info` - Query level details

**Core Tool:**
- `exec_editor_python` - Execute arbitrary Python with full Unreal API access

**Pro tip:** Be specific. "Move the actor named 'Cube' to (0, 0, 100)" works better than "move the actor."

---

## 🔧 Troubleshooting

**Python server won't connect:**
- Verify Unreal Editor is running
- Check UnrealMCP plugin is enabled (Edit > Plugins > search "UnrealMCP")
- Look for "UnrealMCP plugin started TCP server on port 55557" in Output Log

**MCP client not detecting tools:**
- Use absolute paths in `mcp.json` configuration
- Restart MCP client after config changes
- Verify: `pip list | grep mcp` shows installed packages

**Plugin build fails:**
- Close Unreal Editor before building
- Disable Live Coding: `Ctrl+Alt+F11` (Windows) / `Cmd+Alt+F11` (Mac)
- Clean build: Delete `Binaries/` and `Intermediate/` folders, regenerate project files

**Check logs:**
- MCP Server: `unreal_mcp.log` (repository root)
- Unreal Editor: Window > Developer Tools > Output Log

---

## 📖 Background & Architecture

### About This Fork

This is a **complete architectural reimagining** of the original Unreal MCP concept. The implementation philosophy and codebase have completely diverged:

**Original:** Command-based architecture with discrete tool endpoints  
**This Repo:** Exec-first approach with `exec_editor_python` as the primary interface

The commit history has been rewritten (11 clean commits) to reflect the current architecture. The original fork remains for historical reference.

### Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────────┐
│   MCP Client    │  stdio  │  Python Server   │   TCP   │   Unreal Editor     │
│                 │◄───────►│                  │◄───────►│                     │
│ (Cursor/Claude) │         │ unreal_mcp_server│ :55557  │  UnrealMCP Plugin   │
│                 │         │                  │         │  (C++ + Python API) │
└─────────────────┘         └──────────────────┘         └─────────────────────┘
```

**Exec-First Philosophy:**
- Single powerful `exec_editor_python` tool provides full API access
- Foundation tools are lightweight Python snippets (no C++ recompilation)
- Maximum flexibility - anything possible in Unreal's Python API is available
- Rapid iteration - new capabilities are Python code, not compiled plugins

**Core Components:**
- **C++ Plugin** (`MCPGameProject/Plugins/UnrealMCP/`): TCP server + Python execution bridge
- **Python MCP Server** (`Python/unreal_mcp_server.py`): MCP protocol handler
- **Foundation Tools** (`Python/tools/snippets/`): Common operation wrappers
- **Example Scripts** (`Python/scripts/editor/`): Demonstrations and templates

### Security Considerations

⚠️ **This tool executes arbitrary Python code with full Unreal Editor privileges.**

- **Local use only** - Never expose to untrusted networks
- **No sandboxing** - Complete access to project and file system
- **Development only** - Not for production environments
- **Review AI code** - Inspect generated code when possible

**This is experimental software. Use at your own risk with trusted AI assistants in controlled environments.**

### Repository Structure

```
unreal-mcp/
├── MCPGameProject/              # Sample Unreal 5.7 project
│   └── Plugins/UnrealMCP/       # C++ plugin source
│       ├── Source/              # TCP server + Python bridge
│       └── UnrealMCP.uplugin    # Plugin manifest
├── Python/
│   ├── unreal_mcp_server.py     # MCP server (run this)
│   ├── tools/snippets/          # Foundation tool implementations
│   └── scripts/editor/          # Example scripts & demos
├── scripts/                     # Build automation (TypeScript)
└── package.json                 # npm scripts
```

**Key Files:**
- Plugin: `MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/`
- MCP Server: `Python/unreal_mcp_server.py`
- Foundation Tools: `Python/tools/snippets/*.py`

---

## 📚 Additional Resources

**Unreal Python API:** [docs.unrealengine.com/PythonAPI](https://docs.unrealengine.com/5.7/en-US/PythonAPI/)

**Example Scripts:**
- `Python/scripts/editor/build_castle.py` - Scene building demo
- `Python/scripts/editor/golden_exec_*.py` - Workflow examples
- `Python/scripts/editor/test_exec_editor_python.py` - Core testing

**MCP Protocol:** [modelcontextprotocol.io](https://modelcontextprotocol.io)

---

## License

MIT

## Questions

Reach out on X/Twitter: [@btn0s](https://www.x.com/btn0s)
