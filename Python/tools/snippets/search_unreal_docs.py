import json

try:
    query = MCP_PARAMS.get("query", "").strip()
    
    if not query:
        print(json.dumps({
            "status": "error",
            "error": "Query parameter is required"
        }))
        raise SystemExit(0)
    
    # Base documentation URL
    base_url = "https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api"
    
    # Common module mappings
    common_modules = {
        "editor": f"{base_url}/unreal-editor-subsystem",
        "level": f"{base_url}/unreal-editor-level-library",
        "asset": f"{base_url}/unreal-editor-asset-library", 
        "actor": f"{base_url}/unreal-editor-level-library",
        "blueprint": f"{base_url}/unreal-blueprint-library",
        "static_mesh": f"{base_url}/unreal-static-mesh",
        "material": f"{base_url}/unreal-material",
        "vector": f"{base_url}/unreal-vector",
        "rotator": f"{base_url}/unreal-rotator",
        "transform": f"{base_url}/unreal-transform",
    }
    
    # Check if query matches a known module
    query_lower = query.lower()
    matched_url = None
    matched_module = None
    
    for module, url in common_modules.items():
        if module in query_lower or query_lower in module:
            matched_url = url
            matched_module = module
            break
    
    result = {
        "query": query,
        "base_documentation": base_url,
    }
    
    if matched_url:
        result["matched_module"] = matched_module
        result["direct_link"] = matched_url
        result["suggestion"] = f"Found direct link for '{matched_module}' module"
    else:
        # Construct search URL (if Epic supports it) or provide base URL
        result["suggestion"] = f"Search for '{query}' in the Unreal Python API documentation"
        result["search_tips"] = [
            f"Visit {base_url} and use browser search (Ctrl+F / Cmd+F)",
            "Common modules: EditorLevelLibrary, EditorAssetLibrary, UnrealEditorSubsystem",
            "Try searching for class names like 'StaticMeshActor', 'BlueprintLibrary', etc."
        ]
    
    print(json.dumps({
        "status": "success",
        "result": result
    }))

except SystemExit:
    pass
except Exception as e:
    print(json.dumps({
        "status": "error",
        "error": str(e)
    }))

