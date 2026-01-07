<div align="center">

# Model Context Protocol for Unreal Engine
<span style="color: #555555">unreal-mcp</span>

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Unreal Engine](https://img.shields.io/badge/Unreal%20Engine-5.7-orange)](https://www.unrealengine.com)
[![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)](https://www.python.org)
[![Status](https://img.shields.io/badge/Status-Experimental-red)](https://github.com/chongdashu/unreal-mcp)

</div>

Control Unreal Engine through natural language using AI assistants (Cursor, Claude Desktop, Windsurf). This implementation uses the Model Context Protocol (MCP) to bridge AI clients with Unreal Editor.

**How it works:** MCP Client ↔ Python Server ↔ TCP (port 55557) ↔ C++ Plugin ↔ Unreal Editor Python API

## ⚠️ Experimental Status

This project is currently **EXPERIMENTAL**. Breaking changes may occur without notice. Production use is not recommended.

## 📜 About This Fork

This repository is a **complete architectural reimagining** of the original Unreal MCP concept. While it began as a fork, the implementation philosophy and codebase have **completely diverged**:

### Key Differences

**Original Approach:**
- Command-based architecture with discrete tool endpoints
- Separate handlers for each operation type
- Tightly coupled to specific Unreal operations

**This Implementation (Exec-First):**
- Single powerful `exec_editor_python` tool as the primary interface
- Direct access to Unreal's entire Python API
- Foundation tools built as lightweight Python snippets
- Maximum flexibility and rapid iteration

### Commit History

The commit history has been **completely rewritten** to reflect the current architecture:
- 8 logical commits telling a clear story of the implementation
- Clean separation of concerns (C++ plugin → Python server → Tools → Documentation)
- All outdated command-based code and deprecated tools removed

The original fork remains available for **historical reference**, but this repository represents a fundamentally different approach to MCP integration with Unreal Engine.

## 🚀 Quick Start (15 minutes)

### Prerequisites

- **Unreal Engine** 5.6+ (tested on 5.7)
- **Python** 3.10+ with pip
- **Node.js** 16+ (optional, for build scripts)
- **MCP Client** - One of:
  - Cursor (recommended for development)
  - Claude Desktop
  - Windsurf
- **Visual Studio** or compatible C++ compiler (for plugin builds)

### Overview

You'll set up three components:
1. **C++ Plugin** in Unreal Editor (handles Python execution)
2. **Python MCP Server** (bridges MCP client and Unreal)
3. **MCP Client Configuration** (connects your AI assistant)

---

### Step 1: Clone this Repository

```bash
git clone https://github.com/chongdashu/unreal-mcp.git
cd unreal-mcp
```

### Step 2: Choose Your Unreal Project

**Option A: Use the included sample project (easiest)**
- Open `MCPGameProject/MCPGameProject.uproject` in Unreal Engine
- The plugin is already configured here
- Skip to Step 3

**Option B: Use your existing Unreal project**
- Continue to Step 3 to install the plugin into your project

### Step 3: Install the UnrealMCP Plugin

**Option 3A: Automated Installation (recommended)**

From the `unreal-mcp` repository root:

```bash
# Install Node dependencies (first time only)
npm install

# Build the plugin
npm run build-plugin

# Install to your project (interactive prompt)
npm run install-plugin
```

The installer will scan for `.uproject` files and let you choose where to install.

**Option 3B: Manual Installation**

1. Copy `MCPGameProject/Plugins/UnrealMCP/` to your project's `Plugins/UnrealMCP/` folder
2. Right-click your `.uproject` file → "Generate Visual Studio project files"
3. Open the generated `.sln` file in Visual Studio
4. Build the solution (Development Editor configuration)
5. Launch Unreal Editor from Visual Studio or open your `.uproject`
6. Enable the plugin: Edit > Plugins > search "UnrealMCP" > Enable > Restart

**Important:** If Unreal Editor is already running during build, close it or disable Live Coding (`Ctrl+Alt+F11` on Windows/Linux, `Cmd+Alt+F11` on Mac).

### Step 4: Start the Python MCP Server

The Python server runs separately and connects to the Unreal plugin via TCP.

```bash
# From the repository root, install Python dependencies
pip install mcp fastmcp

# OR install as editable package with all dependencies:
pip install -e Python/

# OR using uv (faster dependency management):
uv pip install -e Python/

# Start the server
python Python/unreal_mcp_server.py
```

**Expected output:**
```
INFO: Started MCP server on stdio
Connecting to Unreal Editor on localhost:55557...
Connected to Unreal Editor
```

**Troubleshooting Step 4:**
- **"Connection refused"** → Ensure Unreal Editor is running with the UnrealMCP plugin enabled
- **"ModuleNotFoundError"** → Install dependencies: `pip install mcp fastmcp`
- Check `unreal_mcp.log` in the repository root for details

### Step 5: Configure Your MCP Client

Configure your AI assistant to connect to the MCP server:

#### Configuration File Locations

| MCP Client | Configuration File |
|------------|-------------------|
| **Cursor** | `.cursor/mcp.json` (in your project root) |
| **Claude Desktop** | Mac/Linux: `~/.config/claude-desktop/mcp.json`<br>Windows: `%APPDATA%\Claude\claude_desktop_config.json` |
| **Windsurf** | Mac/Linux: `~/.config/windsurf/mcp.json`<br>Windows: `%USERPROFILE%\.config\windsurf\mcp.json` |

#### Setup Methods

Run the configuration generator script (auto-detects paths and Python executable):

```bash
npm run mcp-deeplink
```

The script will output configuration for your system. Then choose one of these options:

**Option A: One-click install (Cursor only)**
- Click the generated deeplink URL to auto-configure Cursor

**Option B: Manual install (all clients)**
- Copy the JSON snippet from the script output
- Paste it into your MCP client's configuration file (see locations above)
- Restart your MCP client

### Step 6: Verify the Setup

**In Cursor:**
- Open the chat panel
- Type: "Get the current level info"
- The AI should use the `get_current_level_info` tool and return details about your open Unreal level

**In Claude Desktop:**
- Start a conversation
- Ask: "What version of Unreal Engine am I running?"
- Claude should use `exec_editor_python` to query the engine version

**Manual verification:**
1. In your MCP client, verify the `unrealMCP` server appears in the available MCP tools
2. Try executing Python code:
   ```
   Execute this Python in Unreal: 
   import unreal
   print(unreal.SystemLibrary.get_engine_version())
   ```
3. Check that actors can be selected:
   ```
   Get the currently selected actors in Unreal
   ```

If something isn't working, see [Troubleshooting](#-troubleshooting).

---

## 🎯 How to Use After Setup

Once configured, you interact with Unreal through your MCP client (Cursor/Claude) using natural language:

**Example Commands:**

- *"Get the currently selected actors in Unreal"* → Uses `get_selected_actors` tool
- *"Focus the viewport on the actor named 'PlayerStart'"* → Uses `focus_viewport` tool
- *"Spawn a cube at location (100, 200, 50)"* → Uses `exec_editor_python` to create actor
- *"Create a blueprint class with a static mesh component"* → Uses `exec_editor_python` with blueprint API
- *"List all actors in the current level"* → Uses `exec_editor_python` with level query

The AI assistant will automatically choose the appropriate tool (`exec_editor_python` or a foundation tool) and generate the necessary Python code.

**Pro tip:** Be specific about what you want. Instead of "move the actor," say "move the actor named 'Cube' to location (0, 0, 100)."

---

## 💡 Architecture

### System Overview

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────────┐
│   MCP Client    │  stdio  │  Python Server   │   TCP   │   Unreal Editor     │
│                 │◄───────►│                  │◄───────►│                     │
│ (Cursor/Claude) │         │ unreal_mcp_server│ :55557  │  UnrealMCP Plugin   │
│                 │         │                  │         │  (C++ + Python API) │
└─────────────────┘         └──────────────────┘         └─────────────────────┘
```

**Communication Flow:**
1. AI client sends MCP tool requests (stdio/JSON-RPC)
2. Python server translates requests to Python code
3. C++ plugin executes Python in Unreal Editor's Python environment
4. Results flow back through the chain

### Exec-First Design Philosophy

The architecture centers on **`exec_editor_python`** - a single, powerful tool that executes arbitrary Python code in Unreal Editor. This provides:

- **Full API Access:** Anything possible in Unreal's Python API is available
- **Flexibility:** No need to add C++ handlers for every operation
- **Rapid Iteration:** New capabilities are Python snippets, not compiled code
- **Transparency:** See exactly what code is running in the editor

**Core Capabilities via Unreal Python API:**
- Create/modify actors, blueprints, materials, and assets
- Control viewport camera and editor selection
- Query project structure and editor state
- Run editor commands and utilities
- Manipulate levels, layers, and world composition

### Foundation Tools (Convenience Layer)

Built on top of `exec_editor_python`, these tools provide common operations:

| Tool | Purpose |
|------|---------|
| `get_selected_actors` | Get actors selected in editor |
| `set_selected_actors` | Set editor selection by actor names |
| `clear_selection` | Clear editor selection |
| `focus_viewport` | Focus viewport on actor or location |
| `take_screenshot` | Capture viewport screenshot |
| `get_current_level_info` | Query current level details |

All foundation tools are Python snippets in [`Python/tools/snippets/`](Python/tools/snippets/). See the [snippets README](Python/tools/snippets/README.md) for implementation details.

### Security Considerations

⚠️ **`exec_editor_python` executes arbitrary code with full editor privileges.** 

- Only use with trusted MCP clients and code
- Review AI-generated code before execution when possible
- Consider this experimental software for development use only
- No sandboxing or permission system is currently implemented

## 📖 Usage Examples

### Using Foundation Tools (Recommended for Common Tasks)

Foundation tools are convenience wrappers for common operations. Use these when available:

```python
# Get selected actors
get_selected_actors()

# Focus viewport on an actor
focus_viewport(target="MyActor")

# Take a screenshot
take_screenshot(filepath="C:/temp/screenshot.png")

# Get level information
get_current_level_info()
```

### Using exec_editor_python (For Custom Operations)

For operations without a foundation tool, execute Python directly:

**Query selection:**
```python
exec_editor_python("""
import unreal
selected = unreal.EditorLevelLibrary.get_selected_level_actors()
for actor in selected:
    print(f"{actor.get_actor_label()}: {actor.get_actor_location()}")
""")
```

**Spawn an actor:**
```python
exec_editor_python("""
import unreal
actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.StaticMeshActor,
    unreal.Vector(0, 0, 100)
)
actor.set_actor_label("MyNewActor")
print(f"Created: {actor.get_actor_label()}")
""")
```

**Modify materials:**
```python
exec_editor_python("""
import unreal
selected = unreal.EditorLevelLibrary.get_selected_level_actors()
for actor in selected:
    static_mesh_comp = actor.get_component_by_class(unreal.StaticMeshComponent)
    if static_mesh_comp:
        material = unreal.EditorAssetLibrary.load_asset('/Game/Materials/MyMaterial')
        static_mesh_comp.set_material(0, material)
""")
```

**More Examples:**
- [`Python/scripts/editor/`](Python/scripts/editor/) - Editor automation
- [`Python/scripts/actors/`](Python/scripts/actors/) - Actor manipulation
- [`Python/scripts/blueprints/`](Python/scripts/blueprints/) - Blueprint creation

**Unreal Python API Reference:** [Unreal Engine Python API Documentation](https://docs.unrealengine.com/5.7/en-US/PythonAPI/)

## 🔧 Troubleshooting

### Python Server Can't Connect to Unreal

**Error:** "Connection refused" or "Failed to connect to localhost:55557"

**Solutions:**
1. Verify Unreal Editor is running
2. Check that the UnrealMCP plugin is enabled:
   - Edit > Plugins > search "UnrealMCP"
   - Must be checked and editor restarted if just enabled
3. Verify plugin loaded successfully:
   - Check Output Log (Window > Developer Tools > Output Log)
   - Look for "UnrealMCP plugin started TCP server on port 55557"
4. Check firewall isn't blocking port 55557
5. Review `unreal_mcp.log` in the repository root

### Unreal Python Not Available

**Error:** Python commands fail or PythonScriptPlugin missing

**Solutions:**
1. Enable **Python Editor Script Plugin** (required dependency):
   - Edit > Plugins > search "Python"
   - Enable "Python Editor Script Plugin"
   - Restart the editor
2. Verify Python is enabled in project settings:
   - Edit > Project Settings > Plugins > Python
   - Ensure Python is enabled for your platform

### Plugin Build Fails

**Error:** Build errors or "cannot open file for writing"

**Solutions:**
1. Close Unreal Editor completely before building
2. Disable Live Coding if editor must stay open:
   - Press `Ctrl+Alt+F11` (Windows/Linux) or `Cmd+Alt+F11` (Mac)
3. Clean build:
   - Delete `MCPGameProject/Intermediate/` and `MCPGameProject/Binaries/`
   - Delete `MCPGameProject/Plugins/UnrealMCP/Intermediate/` and `.../Binaries/`
   - Regenerate project files (right-click `.uproject`)
   - Rebuild in Visual Studio

### MCP Client Not Detecting Tools

**Error:** "unrealMCP" server not found or no tools available

**Solutions:**
1. Verify the config path is correct in `mcp.json`
2. Use absolute paths (relative paths may not resolve correctly)
3. Restart your MCP client after editing config
4. Check Python dependencies are installed: `pip list | grep mcp`
5. For Cursor: ensure `.cursor/mcp.json` is in your project root
6. Test the server standalone: `python Python/unreal_mcp_server.py` should not error

### Logs and Debugging

- **MCP Server logs:** `unreal_mcp.log` in the repository root
- **Unreal Editor logs:** Window > Developer Tools > Output Log
- **Python execution errors:** Check both logs above
- Include relevant log excerpts when reporting issues on GitHub

## 📂 Repository Structure

```
unreal-mcp/
├── MCPGameProject/                    # Sample Unreal 5.7 project
│   ├── MCPGameProject.uproject        # Unreal project file
│   └── Plugins/
│       └── UnrealMCP/                 # C++ Plugin source
│           ├── Source/
│           │   └── UnrealMCP/
│           │       ├── Private/       # C++ implementation
│           │       │   ├── UnrealMCPModule.cpp
│           │       │   ├── MCPServerRunnable.cpp  # TCP server
│           │       │   └── UnrealMCPBridge.cpp    # Python executor
│           │       └── Public/        # C++ headers
│           └── UnrealMCP.uplugin      # Plugin manifest
│
├── Python/
│   ├── unreal_mcp_server.py           # MCP server entrypoint (run this)
│   ├── pyproject.toml                 # Python dependencies
│   ├── tools/
│   │   ├── snippets/                  # Foundation tool implementations
│   │   │   ├── get_selected_actors.py
│   │   │   ├── focus_viewport.py
│   │   │   └── ...                    # Other snippets
│   │   └── editor_tools.py            # Helper utilities
│   └── scripts/                       # Example scripts & demos
│       ├── editor/                    # Editor automation examples
│       ├── actors/                    # Actor manipulation examples
│       └── blueprints/                # Blueprint creation examples
│
├── scripts/
│   ├── build-plugin.ts                # Automated plugin builder
│   ├── install-plugin.ts              # Interactive plugin installer
│   └── generate-mcp-deeplink.ts       # Cursor config generator
│
├── package.json                       # npm scripts and Node dependencies
└── unreal_mcp.log                     # Runtime log (auto-generated)
```

**Key Files:**
- **Plugin Entry:** `MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPModule.cpp`
- **TCP Server:** `MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/MCPServerRunnable.cpp`
- **Python Execution:** `MCPGameProject/Plugins/UnrealMCP/Source/UnrealMCP/Private/UnrealMCPBridge.cpp`
- **MCP Server:** `Python/unreal_mcp_server.py`
- **Tool Definitions:** `Python/tools/snippets/` (each tool is a standalone Python file)

## License

MIT

## Questions

For questions, reach out on X/Twitter: [@btn0s](https://www.x.com/btn0s)
