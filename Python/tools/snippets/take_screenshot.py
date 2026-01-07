import json
import unreal

try:
    filepath = MCP_PARAMS.get("filepath", "")
    if not isinstance(filepath, str) or not filepath.strip():
        print(json.dumps({"status": "error", "error": "filepath is required"}))
    else:
        if not filepath.lower().endswith(".png"):
            filepath += ".png"

        world = unreal.EditorLevelLibrary.get_editor_world()
        if not world:
            print(json.dumps({"status": "error", "error": "Failed to get editor world"}))
        else:
            # HighResShot writes to disk; directory must exist.
            unreal.SystemLibrary.execute_console_command(world, f"HighResShot {filepath}")
            print(json.dumps({"status": "success", "result": {"filepath": filepath}}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


