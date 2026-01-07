import json
import unreal

try:
    actor_names = MCP_PARAMS.get("actor_names", [])
    if not isinstance(actor_names, list) or not actor_names:
        print(json.dumps({"status": "error", "error": "actor_names must be a non-empty list"}))
    else:
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()

        found_actors = []
        not_found = []
        selected_list = []

        for name in actor_names:
            found = False
            for actor in all_actors:
                if actor.get_name() == name or actor.get_actor_label() == name:
                    selected_list.append(actor)
                    found_actors.append(name)
                    found = True
                    break
            if not found:
                not_found.append(name)

        unreal.EditorLevelLibrary.set_selected_level_actors(selected_list)

        result = {
            "status": "success",
            "result": {
                "selected_count": len(found_actors),
                "found": found_actors,
            },
        }
        if not_found:
            result["result"]["not_found"] = not_found

        print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


