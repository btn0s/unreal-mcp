import json
import unreal

try:
    include_streaming = bool(MCP_PARAMS.get("include_streaming", True))

    world = unreal.EditorLevelLibrary.get_editor_world()
    if not world:
        print(json.dumps({"status": "error", "error": "Failed to get editor world"}))
    else:
        level = world.get_persistent_level()

        level_info = {
            "persistent_level_path": level.get_path_name(),
            "actor_count": len(unreal.EditorLevelLibrary.get_all_level_actors()),
            "is_dirty": bool(world.is_dirty()),
        }

        if include_streaming:
            streaming_levels = []
            for streaming_level in world.get_streaming_levels():
                if streaming_level:
                    streaming_levels.append(
                        {
                            "package": streaming_level.get_world_asset_package_name(),
                            "loaded": bool(streaming_level.is_level_loaded()),
                            "visible": bool(streaming_level.should_be_visible_in_editor()),
                        }
                    )
            level_info["streaming_levels"] = streaming_levels

        print(json.dumps({"status": "success", "result": level_info}))
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


