import json
import unreal

try:
    target = MCP_PARAMS.get("target", None)
    location = MCP_PARAMS.get("location", None)
    distance = float(MCP_PARAMS.get("distance", 1000.0))
    orientation = MCP_PARAMS.get("orientation", None)

    # Resolve focus location
    focus_location = None
    if isinstance(target, str) and target.strip():
        all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
        for actor in all_actors:
            if actor.get_name() == target or actor.get_actor_label() == target:
                focus_location = actor.get_actor_location()
                break
        if focus_location is None:
            print(json.dumps({"status": "error", "error": f"Actor '{target}' not found"}))
            raise SystemExit(0)
    elif isinstance(location, list) and len(location) == 3:
        # Create Vector and set properties explicitly for safety
        focus_location = unreal.Vector()
        focus_location.x = float(location[0])
        focus_location.y = float(location[1])
        focus_location.z = float(location[2])
    else:
        print(json.dumps({"status": "error", "error": "Either 'target' or 'location' must be provided"}))
        raise SystemExit(0)

    editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
    if not editor_subsystem:
        print(json.dumps({"status": "error", "error": "Failed to get UnrealEditorSubsystem"}))
        raise SystemExit(0)

    viewport_client = editor_subsystem.get_level_viewport_client()
    if not viewport_client:
        print(json.dumps({"status": "error", "error": "Failed to get level viewport client"}))
        raise SystemExit(0)

    # Basic framing: offset along +X
    offset = unreal.Vector()
    offset.x = distance
    offset.y = 0.0
    offset.z = 0.0
    view_location = focus_location + offset
    viewport_client.set_view_location(view_location)

    if isinstance(orientation, list) and len(orientation) == 3:
        # Create Rotator and set properties explicitly to avoid scrambled values
        rot = unreal.Rotator()
        rot.pitch = float(orientation[0])
        rot.yaw = float(orientation[1])
        rot.roll = float(orientation[2])
        viewport_client.set_view_rotation(rot)

    print(
        json.dumps(
            {
                "status": "success",
                "result": {
                    "focused_on": target if target else "location",
                    "location": [focus_location.x, focus_location.y, focus_location.z],
                },
            }
        )
    )
except SystemExit:
    pass
except Exception as e:
    print(json.dumps({"status": "error", "error": str(e)}))


