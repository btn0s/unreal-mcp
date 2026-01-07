import json
import unreal

try:
    unreal.EditorLevelLibrary.set_selected_level_actors([])
    print(json.dumps({"status": "success", "result": {}}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


