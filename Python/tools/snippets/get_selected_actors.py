import json
import unreal

try:
    selected_actors = unreal.EditorLevelLibrary.get_selected_level_actors()
    actors_list = []
    for actor in selected_actors:
        actors_list.append(
            {
                "name": actor.get_name(),
                "label": actor.get_actor_label(),
                "path": actor.get_path_name(),
            }
        )

    result = {"status": "success", "result": {"actors": actors_list}}
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


