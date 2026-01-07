#include "Commands/UnrealMCPEditorCommands.h"
#include "Commands/UnrealMCPCommonUtils.h"
#include "Editor.h"
#include "EditorViewportClient.h"
#include "LevelEditorViewport.h"
#include "ImageUtils.h"
#include "HighResScreenshot.h"
#include "Engine/GameViewportClient.h"
#include "Misc/FileHelper.h"
#include "GameFramework/Actor.h"
#include "Engine/Selection.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DirectionalLight.h"
#include "Engine/PointLight.h"
#include "Engine/SpotLight.h"
#include "Camera/CameraActor.h"
#include "Components/StaticMeshComponent.h"
#include "EditorSubsystem.h"
#include "Subsystems/EditorActorSubsystem.h"
#include "Engine/Blueprint.h"
#include "Engine/BlueprintGeneratedClass.h"
#include "EditorAssetLibrary.h"
#include "Editor/EditorEngine.h"
#include "FileHelpers.h"
#include "Engine/World.h"
#include "Engine/LevelStreaming.h"
#include "Engine/LevelStreamingDynamic.h"
#include "Misc/PackageName.h"
#include "AssetRegistry/AssetRegistryModule.h"
#include "IPythonScriptPlugin.h"
#include "PythonScriptTypes.h"

FUnrealMCPEditorCommands::FUnrealMCPEditorCommands()
{
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleCommand(const FString& CommandType, const TSharedPtr<FJsonObject>& Params)
{
    // Actor manipulation commands
    if (CommandType == TEXT("get_actors_in_level"))
    {
        return HandleGetActorsInLevel(Params);
    }
    else if (CommandType == TEXT("find_actors_by_name"))
    {
        return HandleFindActorsByName(Params);
    }
    else if (CommandType == TEXT("spawn_actor") || CommandType == TEXT("create_actor"))
    {
        if (CommandType == TEXT("create_actor"))
        {
            UE_LOG(LogTemp, Warning, TEXT("'create_actor' command is deprecated and will be removed in a future version. Please use 'spawn_actor' instead."));
        }
        return HandleSpawnActor(Params);
    }
    else if (CommandType == TEXT("delete_actor"))
    {
        return HandleDeleteActor(Params);
    }
    else if (CommandType == TEXT("set_actor_transform"))
    {
        return HandleSetActorTransform(Params);
    }
    else if (CommandType == TEXT("get_actor_properties"))
    {
        return HandleGetActorProperties(Params);
    }
    else if (CommandType == TEXT("set_actor_property"))
    {
        return HandleSetActorProperty(Params);
    }
    else if (CommandType == TEXT("set_actor_static_mesh"))
    {
        return HandleSetActorStaticMesh(Params);
    }
    // Blueprint actor spawning
    else if (CommandType == TEXT("spawn_blueprint_actor"))
    {
        return HandleSpawnBlueprintActor(Params);
    }
    // Editor viewport commands
    else if (CommandType == TEXT("focus_viewport"))
    {
        return HandleFocusViewport(Params);
    }
    else if (CommandType == TEXT("take_screenshot"))
    {
        return HandleTakeScreenshot(Params);
    }
    // Level management commands
    else if (CommandType == TEXT("create_level"))
    {
        return HandleCreateLevel(Params);
    }
    else if (CommandType == TEXT("open_level"))
    {
        return HandleOpenLevel(Params);
    }
    else if (CommandType == TEXT("save_current_level"))
    {
        return HandleSaveCurrentLevel(Params);
    }
    else if (CommandType == TEXT("save_all_levels"))
    {
        return HandleSaveAllLevels(Params);
    }
    else if (CommandType == TEXT("get_current_level_info"))
    {
        return HandleGetCurrentLevelInfo(Params);
    }
    // Python execution command
    else if (CommandType == TEXT("exec_editor_python"))
    {
        return HandleExecEditorPython(Params);
    }
    
    return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown editor command: %s"), *CommandType));
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleGetActorsInLevel(const TSharedPtr<FJsonObject>& Params)
{
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> ActorArray;
    for (AActor* Actor : AllActors)
    {
        if (Actor)
        {
            ActorArray.Add(FUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), ActorArray);
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleFindActorsByName(const TSharedPtr<FJsonObject>& Params)
{
    FString Pattern;
    if (!Params->TryGetStringField(TEXT("pattern"), Pattern))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'pattern' parameter"));
    }
    
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    TArray<TSharedPtr<FJsonValue>> MatchingActors;
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName().Contains(Pattern))
        {
            MatchingActors.Add(FUnrealMCPCommonUtils::ActorToJson(Actor));
        }
    }
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetArrayField(TEXT("actors"), MatchingActors);
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSpawnActor(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString ActorType;
    if (!Params->TryGetStringField(TEXT("type"), ActorType))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'type' parameter"));
    }

    // Get actor name (required parameter)
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Get optional transform parameters
    FVector Location(0.0f, 0.0f, 0.0f);
    FRotator Rotation(0.0f, 0.0f, 0.0f);
    FVector Scale(1.0f, 1.0f, 1.0f);

    if (Params->HasField(TEXT("location")))
    {
        Location = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        Rotation = FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"));
    }
    if (Params->HasField(TEXT("scale")))
    {
        Scale = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale"));
    }

    // Create the actor based on type
    AActor* NewActor = nullptr;
    UWorld* World = GEditor->GetEditorWorldContext().World();

    if (!World)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    // Check if an actor with this name already exists
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(World, AActor::StaticClass(), AllActors);
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor with name '%s' already exists"), *ActorName));
        }
    }

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = *ActorName;

    if (ActorType == TEXT("StaticMeshActor"))
    {
        NewActor = World->SpawnActor<AStaticMeshActor>(AStaticMeshActor::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("PointLight"))
    {
        NewActor = World->SpawnActor<APointLight>(APointLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("SpotLight"))
    {
        NewActor = World->SpawnActor<ASpotLight>(ASpotLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("DirectionalLight"))
    {
        NewActor = World->SpawnActor<ADirectionalLight>(ADirectionalLight::StaticClass(), Location, Rotation, SpawnParams);
    }
    else if (ActorType == TEXT("CameraActor"))
    {
        NewActor = World->SpawnActor<ACameraActor>(ACameraActor::StaticClass(), Location, Rotation, SpawnParams);
    }
    else
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Unknown actor type: %s"), *ActorType));
    }

    if (NewActor)
    {
        // Set scale (since SpawnActor only takes location and rotation)
        FTransform Transform = NewActor->GetTransform();
        Transform.SetScale3D(Scale);
        NewActor->SetActorTransform(Transform);

        // Return the created actor's details
        return FUnrealMCPCommonUtils::ActorToJsonObject(NewActor, true);
    }

    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to create actor"));
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleDeleteActor(const TSharedPtr<FJsonObject>& Params)
{
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            // Store actor info before deletion for the response
            TSharedPtr<FJsonObject> ActorInfo = FUnrealMCPCommonUtils::ActorToJsonObject(Actor);
            
            // Delete the actor
            Actor->Destroy();
            
            TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
            ResultObj->SetObjectField(TEXT("deleted_actor"), ActorInfo);
            return ResultObj;
        }
    }
    
    return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSetActorTransform(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Get transform parameters
    FTransform NewTransform = TargetActor->GetTransform();

    if (Params->HasField(TEXT("location")))
    {
        NewTransform.SetLocation(FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location")));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        NewTransform.SetRotation(FQuat(FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"))));
    }
    if (Params->HasField(TEXT("scale")))
    {
        NewTransform.SetScale3D(FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale")));
    }

    // Set the new transform
    TargetActor->SetActorTransform(NewTransform);

    // Return updated actor info
    return FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleGetActorProperties(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Always return detailed properties for this command
    return FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true);
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSetActorProperty(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Get property name
    FString PropertyName;
    if (!Params->TryGetStringField(TEXT("property_name"), PropertyName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'property_name' parameter"));
    }

    // Get property value
    if (!Params->HasField(TEXT("property_value")))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'property_value' parameter"));
    }
    
    TSharedPtr<FJsonValue> PropertyValue = Params->Values.FindRef(TEXT("property_value"));
    
    // Set the property using our utility function
    FString ErrorMessage;
    if (FUnrealMCPCommonUtils::SetObjectProperty(TargetActor, PropertyName, PropertyValue, ErrorMessage))
    {
        // Property set successfully
        TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
        ResultObj->SetStringField(TEXT("actor"), ActorName);
        ResultObj->SetStringField(TEXT("property"), PropertyName);
        ResultObj->SetBoolField(TEXT("success"), true);
        
        // Also include the full actor details
        ResultObj->SetObjectField(TEXT("actor_details"), FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true));
        return ResultObj;
    }
    else
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(ErrorMessage);
    }
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSetActorStaticMesh(const TSharedPtr<FJsonObject>& Params)
{
    // Get actor name
    FString ActorName;
    if (!Params->TryGetStringField(TEXT("name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'name' parameter"));
    }

    // Get static mesh path
    FString MeshPath;
    if (!Params->TryGetStringField(TEXT("static_mesh"), MeshPath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'static_mesh' parameter"));
    }

    // Get optional component name
    FString ComponentName;
    Params->TryGetStringField(TEXT("component_name"), ComponentName);

    // Find the actor
    AActor* TargetActor = nullptr;
    TArray<AActor*> AllActors;
    UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
    
    for (AActor* Actor : AllActors)
    {
        if (Actor && Actor->GetName() == ActorName)
        {
            TargetActor = Actor;
            break;
        }
    }

    if (!TargetActor)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *ActorName));
    }

    // Find the StaticMeshComponent
    UStaticMeshComponent* MeshComponent = nullptr;

    // Special handling for AStaticMeshActor
    AStaticMeshActor* StaticMeshActor = Cast<AStaticMeshActor>(TargetActor);
    if (StaticMeshActor)
    {
        MeshComponent = StaticMeshActor->GetStaticMeshComponent();
        if (MeshComponent && !ComponentName.IsEmpty())
        {
            // If component name specified, check if it matches
            if (!MeshComponent->GetName().Equals(ComponentName, ESearchCase::IgnoreCase))
            {
                MeshComponent = nullptr; // Name doesn't match, will search all components below
            }
        }
    }

    // If not found yet, search all components
    if (!MeshComponent)
    {
        TArray<UActorComponent*> Components;
        TargetActor->GetComponents(UStaticMeshComponent::StaticClass(), Components);
        
        if (ComponentName.IsEmpty())
        {
            // No component name specified, use first StaticMeshComponent found
            if (Components.Num() > 0)
            {
                MeshComponent = Cast<UStaticMeshComponent>(Components[0]);
            }
        }
        else
        {
            // Search for component with matching name (case-insensitive)
            for (UActorComponent* Comp : Components)
            {
                UStaticMeshComponent* StaticMeshComp = Cast<UStaticMeshComponent>(Comp);
                if (StaticMeshComp && StaticMeshComp->GetName().Equals(ComponentName, ESearchCase::IgnoreCase))
                {
                    MeshComponent = StaticMeshComp;
                    break;
                }
            }
        }
    }

    if (!MeshComponent)
    {
        if (ComponentName.IsEmpty())
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor '%s' has no StaticMeshComponent"), *ActorName));
        }
        else
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("StaticMeshComponent '%s' not found on actor '%s'"), *ComponentName, *ActorName));
        }
    }

    // Load the static mesh asset
    UStaticMesh* Mesh = Cast<UStaticMesh>(UEditorAssetLibrary::LoadAsset(MeshPath));
    if (!Mesh)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to load static mesh from path: %s"), *MeshPath));
    }

    // Set the mesh with proper editor transaction handling
    MeshComponent->Modify();
    TargetActor->Modify();
    
    MeshComponent->SetStaticMesh(Mesh);
    
    // Notify the component that it has been modified
    MeshComponent->PostEditChange();
    
    // Mark the actor's package as dirty
    TargetActor->MarkPackageDirty();

    // Return success response
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("success"), true);
    ResultObj->SetStringField(TEXT("actor"), ActorName);
    ResultObj->SetStringField(TEXT("component"), MeshComponent->GetName());
    ResultObj->SetStringField(TEXT("static_mesh"), MeshPath);
    ResultObj->SetObjectField(TEXT("actor_details"), FUnrealMCPCommonUtils::ActorToJsonObject(TargetActor, true));
    
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSpawnBlueprintActor(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString BlueprintName;
    if (!Params->TryGetStringField(TEXT("blueprint_name"), BlueprintName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'blueprint_name' parameter"));
    }

    FString ActorName;
    if (!Params->TryGetStringField(TEXT("actor_name"), ActorName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'actor_name' parameter"));
    }

    // Find the blueprint
    if (BlueprintName.IsEmpty())
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Blueprint name is empty"));
    }

    FString Root      = TEXT("/Game/Blueprints/");
    FString AssetPath = Root + BlueprintName;

    if (!FPackageName::DoesPackageExist(AssetPath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint '%s' not found – it must reside under /Game/Blueprints"), *BlueprintName));
    }

    UBlueprint* Blueprint = LoadObject<UBlueprint>(nullptr, *AssetPath);
    if (!Blueprint)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Blueprint not found: %s"), *BlueprintName));
    }

    // Get transform parameters
    FVector Location(0.0f, 0.0f, 0.0f);
    FRotator Rotation(0.0f, 0.0f, 0.0f);
    FVector Scale(1.0f, 1.0f, 1.0f);

    if (Params->HasField(TEXT("location")))
    {
        Location = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
    }
    if (Params->HasField(TEXT("rotation")))
    {
        Rotation = FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("rotation"));
    }
    if (Params->HasField(TEXT("scale")))
    {
        Scale = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("scale"));
    }

    // Spawn the actor
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    FTransform SpawnTransform;
    SpawnTransform.SetLocation(Location);
    SpawnTransform.SetRotation(FQuat(Rotation));
    SpawnTransform.SetScale3D(Scale);

    FActorSpawnParameters SpawnParams;
    SpawnParams.Name = *ActorName;

    AActor* NewActor = World->SpawnActor<AActor>(Blueprint->GeneratedClass, SpawnTransform, SpawnParams);
    if (NewActor)
    {
        return FUnrealMCPCommonUtils::ActorToJsonObject(NewActor, true);
    }

    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to spawn blueprint actor"));
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleFocusViewport(const TSharedPtr<FJsonObject>& Params)
{
    // Get target actor name if provided
    FString TargetActorName;
    bool HasTargetActor = Params->TryGetStringField(TEXT("target"), TargetActorName);

    // Get location if provided
    FVector Location(0.0f, 0.0f, 0.0f);
    bool HasLocation = false;
    if (Params->HasField(TEXT("location")))
    {
        Location = FUnrealMCPCommonUtils::GetVectorFromJson(Params, TEXT("location"));
        HasLocation = true;
    }

    // Get distance
    float Distance = 1000.0f;
    if (Params->HasField(TEXT("distance")))
    {
        Distance = Params->GetNumberField(TEXT("distance"));
    }

    // Get orientation if provided
    FRotator Orientation(0.0f, 0.0f, 0.0f);
    bool HasOrientation = false;
    if (Params->HasField(TEXT("orientation")))
    {
        Orientation = FUnrealMCPCommonUtils::GetRotatorFromJson(Params, TEXT("orientation"));
        HasOrientation = true;
    }

    // Get the active viewport
    FLevelEditorViewportClient* ViewportClient = (FLevelEditorViewportClient*)GEditor->GetActiveViewport()->GetClient();
    if (!ViewportClient)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get active viewport"));
    }

    // If we have a target actor, focus on it
    if (HasTargetActor)
    {
        // Find the actor
        AActor* TargetActor = nullptr;
        TArray<AActor*> AllActors;
        UGameplayStatics::GetAllActorsOfClass(GWorld, AActor::StaticClass(), AllActors);
        
        for (AActor* Actor : AllActors)
        {
            if (Actor && Actor->GetName() == TargetActorName)
            {
                TargetActor = Actor;
                break;
            }
        }

        if (!TargetActor)
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Actor not found: %s"), *TargetActorName));
        }

        // Focus on the actor
        ViewportClient->SetViewLocation(TargetActor->GetActorLocation() - FVector(Distance, 0.0f, 0.0f));
    }
    // Otherwise use the provided location
    else if (HasLocation)
    {
        ViewportClient->SetViewLocation(Location - FVector(Distance, 0.0f, 0.0f));
    }
    else
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Either 'target' or 'location' must be provided"));
    }

    // Set orientation if provided
    if (HasOrientation)
    {
        ViewportClient->SetViewRotation(Orientation);
    }

    // Force viewport to redraw
    ViewportClient->Invalidate();

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("success"), true);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleTakeScreenshot(const TSharedPtr<FJsonObject>& Params)
{
    // Get file path parameter
    FString FilePath;
    if (!Params->TryGetStringField(TEXT("filepath"), FilePath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'filepath' parameter"));
    }
    
    // Ensure the file path has a proper extension
    if (!FilePath.EndsWith(TEXT(".png")))
    {
        FilePath += TEXT(".png");
    }

    // Get the active viewport
    if (GEditor && GEditor->GetActiveViewport())
    {
        FViewport* Viewport = GEditor->GetActiveViewport();
        TArray<FColor> Bitmap;
        FIntRect ViewportRect(0, 0, Viewport->GetSizeXY().X, Viewport->GetSizeXY().Y);
        
        if (Viewport->ReadPixels(Bitmap, FReadSurfaceDataFlags(), ViewportRect))
        {
            TArray<uint8> CompressedBitmap;
            FImageUtils::CompressImageArray(Viewport->GetSizeXY().X, Viewport->GetSizeXY().Y, Bitmap, CompressedBitmap);
            
            if (FFileHelper::SaveArrayToFile(CompressedBitmap, *FilePath))
            {
                TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
                ResultObj->SetStringField(TEXT("filepath"), FilePath);
                return ResultObj;
            }
        }
    }
    
    return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to take screenshot"));
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleCreateLevel(const TSharedPtr<FJsonObject>& Params)
{
    // Get required parameters
    FString LevelName;
    if (!Params->TryGetStringField(TEXT("level_name"), LevelName))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'level_name' parameter"));
    }

    // Get optional folder parameter
    FString Folder = TEXT("/Game/Maps");
    if (Params->HasField(TEXT("folder")))
    {
        Params->TryGetStringField(TEXT("folder"), Folder);
    }

    // Get optional template_level parameter
    FString TemplateLevel = TEXT("/Engine/Maps/Templates/Minimal_Default");
    if (Params->HasField(TEXT("template_level")))
    {
        Params->TryGetStringField(TEXT("template_level"), TemplateLevel);
    }

    // Get optional open_after_create parameter
    bool bOpenAfterCreate = true;
    if (Params->HasField(TEXT("open_after_create")))
    {
        bOpenAfterCreate = Params->GetBoolField(TEXT("open_after_create"));
    }

    // Normalize destination path
    FString DestPath = Folder + TEXT("/") + LevelName;

    // Check if asset already exists
    if (UEditorAssetLibrary::DoesAssetExist(DestPath))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Level already exists: %s"), *DestPath));
    }

    // Check if template exists
    if (!UEditorAssetLibrary::DoesAssetExist(TemplateLevel))
    {
        // Try fallback template
        TemplateLevel = TEXT("/Engine/Maps/Templates/Template_Default");
        if (!UEditorAssetLibrary::DoesAssetExist(TemplateLevel))
        {
            return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Template level not found: %s"), *TemplateLevel));
        }
    }

    // Duplicate the template map asset
    UObject* DuplicatedAsset = UEditorAssetLibrary::DuplicateAsset(TemplateLevel, DestPath);
    if (!DuplicatedAsset)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to duplicate template level from %s to %s"), *TemplateLevel, *DestPath));
    }

    // Get the package path from the duplicated asset
    FString NewAssetPath = DuplicatedAsset->GetOutermost()->GetName();

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("level_path"), NewAssetPath);
    ResultObj->SetStringField(TEXT("level_name"), LevelName);

    // Open the level if requested
    if (bOpenAfterCreate)
    {
        // Normalize to package path for loading
        FString PackagePath = NewAssetPath;
        if (!PackagePath.StartsWith(TEXT("/")))
        {
            PackagePath = TEXT("/") + PackagePath;
        }

        // Load the map
        FEditorFileUtils::LoadMap(PackagePath);
        ResultObj->SetBoolField(TEXT("opened"), true);
    }
    else
    {
        ResultObj->SetBoolField(TEXT("opened"), false);
    }

    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleOpenLevel(const TSharedPtr<FJsonObject>& Params)
{
    // Get required level parameter
    FString Level;
    if (!Params->TryGetStringField(TEXT("level"), Level))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'level' parameter"));
    }

    // Get optional save_dirty parameter
    bool bSaveDirty = true;
    if (Params->HasField(TEXT("save_dirty")))
    {
        bSaveDirty = Params->GetBoolField(TEXT("save_dirty"));
    }

    // Normalize level path
    FString LevelPackage = Level;
    if (!LevelPackage.StartsWith(TEXT("/Game/")))
    {
        // Assume it's a short name, prepend /Game/Maps/
        LevelPackage = TEXT("/Game/Maps/") + Level;
    }

    // Ensure it doesn't have .umap extension
    LevelPackage.ReplaceInline(TEXT(".umap"), TEXT(""));

    // Check if level exists
    if (!UEditorAssetLibrary::DoesAssetExist(LevelPackage))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Level not found: %s"), *LevelPackage));
    }

    // Save dirty levels if requested
    if (bSaveDirty)
    {
        FEditorFileUtils::SaveDirtyPackages(false, true, true, false, false, false, nullptr);
    }

    // Load the map
    bool bLoaded = FEditorFileUtils::LoadMap(LevelPackage);
    if (!bLoaded)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to load level: %s"), *LevelPackage));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("level_path"), LevelPackage);
    ResultObj->SetBoolField(TEXT("success"), true);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSaveCurrentLevel(const TSharedPtr<FJsonObject>& Params)
{
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    ULevel* PersistentLevel = World->PersistentLevel;
    if (!PersistentLevel)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get persistent level"));
    }

    // Get the package name
    FString PackageName = PersistentLevel->GetOutermost()->GetName();
    
    // Save the level
    bool bSaved = FEditorFileUtils::SaveLevel(PersistentLevel);
    if (!bSaved)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(FString::Printf(TEXT("Failed to save level: %s"), *PackageName));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetStringField(TEXT("level_path"), PackageName);
    ResultObj->SetBoolField(TEXT("success"), true);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleSaveAllLevels(const TSharedPtr<FJsonObject>& Params)
{
    // Save all dirty packages (including levels)
    bool bSaved = FEditorFileUtils::SaveDirtyPackages(false, true, true, false, false, false, nullptr);
    
    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    ResultObj->SetBoolField(TEXT("success"), bSaved);
    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleGetCurrentLevelInfo(const TSharedPtr<FJsonObject>& Params)
{
    UWorld* World = GEditor->GetEditorWorldContext().World();
    if (!World)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Failed to get editor world"));
    }

    // Get optional include_streaming parameter
    bool bIncludeStreaming = true;
    if (Params->HasField(TEXT("include_streaming")))
    {
        bIncludeStreaming = Params->GetBoolField(TEXT("include_streaming"));
    }

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();

    // Get persistent level info
    ULevel* PersistentLevel = World->PersistentLevel;
    if (PersistentLevel)
    {
        FString PackageName = PersistentLevel->GetOutermost()->GetName();
        ResultObj->SetStringField(TEXT("persistent_level_path"), PackageName);
        
        // Get actor count
        int32 ActorCount = PersistentLevel->Actors.Num();
        ResultObj->SetNumberField(TEXT("actor_count"), ActorCount);

        // Try to get dirty state (best effort)
        UPackage* LevelPackage = PersistentLevel->GetOutermost();
        bool bIsDirty = LevelPackage->IsDirty();
        ResultObj->SetBoolField(TEXT("is_dirty"), bIsDirty);
    }

    // Get streaming levels info if requested
    if (bIncludeStreaming)
    {
        TArray<TSharedPtr<FJsonValue>> StreamingLevelsArray;
        
        for (ULevelStreaming* StreamingLevel : World->GetStreamingLevels())
        {
            if (StreamingLevel)
            {
                TSharedPtr<FJsonObject> StreamingLevelObj = MakeShared<FJsonObject>();
                
                FString PackageName = StreamingLevel->GetWorldAssetPackageName();
                StreamingLevelObj->SetStringField(TEXT("package"), PackageName);
                
                bool bIsLoaded = StreamingLevel->IsLevelLoaded();
                StreamingLevelObj->SetBoolField(TEXT("loaded"), bIsLoaded);
                
                bool bShouldBeVisible = StreamingLevel->ShouldBeVisible();
                StreamingLevelObj->SetBoolField(TEXT("visible"), bShouldBeVisible);
                
                StreamingLevelsArray.Add(MakeShared<FJsonValueObject>(StreamingLevelObj));
            }
        }
        
        ResultObj->SetArrayField(TEXT("streaming_levels"), StreamingLevelsArray);
    }

    return ResultObj;
}

TSharedPtr<FJsonObject> FUnrealMCPEditorCommands::HandleExecEditorPython(const TSharedPtr<FJsonObject>& Params)
{
    FString PythonCode;
    if (!Params->TryGetStringField(TEXT("code"), PythonCode))
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Missing 'code' parameter"));
    }

    if (PythonCode.IsEmpty())
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("Python code cannot be empty"));
    }

    // Check if PythonScriptPlugin is available
    IPythonScriptPlugin* PythonPlugin = IPythonScriptPlugin::Get();
    if (!PythonPlugin)
    {
        return FUnrealMCPCommonUtils::CreateErrorResponse(TEXT("PythonScriptPlugin is not available. Please enable it in the Editor."));
    }

    // Execute Python code using ExecPythonCommandEx to capture output
    FPythonCommandEx PythonCommand;
    PythonCommand.Command = PythonCode;
    PythonCommand.ExecutionMode = EPythonCommandExecutionMode::ExecuteFile;
    PythonCommand.FileExecutionScope = EPythonFileExecutionScope::Public;
    
    bool bSuccess = PythonPlugin->ExecPythonCommandEx(PythonCommand);

    TSharedPtr<FJsonObject> ResultObj = MakeShared<FJsonObject>();
    
    // Build output string from log entries
    FString Output;
    FString ErrorOutput;
    
    for (const FPythonLogOutputEntry& LogEntry : PythonCommand.LogOutput)
    {
        FString LogLine = LogEntry.Output;
        if (LogEntry.Type == EPythonLogOutputType::Error)
        {
            if (!ErrorOutput.IsEmpty())
            {
                ErrorOutput += TEXT("\n");
            }
            ErrorOutput += LogLine;
        }
        else
        {
            if (!Output.IsEmpty())
            {
                Output += TEXT("\n");
            }
            Output += LogLine;
        }
    }
    
    // If CommandResult has content, include it (especially for EvaluateStatement mode)
    if (!PythonCommand.CommandResult.IsEmpty())
    {
        if (!Output.IsEmpty())
        {
            Output += TEXT("\n");
        }
        Output += PythonCommand.CommandResult;
    }
    
    if (bSuccess)
    {
        ResultObj->SetBoolField(TEXT("success"), true);
        ResultObj->SetStringField(TEXT("output"), Output);
        if (!ErrorOutput.IsEmpty())
        {
            ResultObj->SetStringField(TEXT("error_output"), ErrorOutput);
        }
    }
    else
    {
        ResultObj->SetBoolField(TEXT("success"), false);
        // Use CommandResult if available (contains error trace), otherwise use ErrorOutput
        FString ErrorMessage = !PythonCommand.CommandResult.IsEmpty() ? PythonCommand.CommandResult : 
                               (!ErrorOutput.IsEmpty() ? ErrorOutput : TEXT("Python execution failed"));
        ResultObj->SetStringField(TEXT("error"), ErrorMessage);
        if (!Output.IsEmpty())
        {
            ResultObj->SetStringField(TEXT("output"), Output);
        }
    }

    return ResultObj;
} 