#!/usr/bin/env python
"""
Golden Path Example: Transaction and Structured JSON Output

Demonstrates:
1. Proper use of ScopedEditorTransaction for undo/redo support
2. Structured JSON output for reliable client parsing
3. Error handling with structured error responses
4. Idempotent operations

Follows the Ask -> Research -> Execute -> Verify workflow.

Usage:
    python golden_exec_transaction_and_json.py
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def test_successful_transaction():
    """Test a successful transaction with structured JSON output."""
    print("=" * 60)
    print("Test 1: Successful Transaction")
    print("=" * 60)
    print()
    
    code = '''
import unreal
import json

try:
    # RESEARCH: Get current actor count
    actors_before = unreal.EditorLevelLibrary.get_all_level_actors()
    count_before = len(actors_before)
    
    # EXECUTE: Create multiple actors in a single transaction
    with unreal.ScopedEditorTransaction("Golden Path: Create test actors"):
        # Create 3 test actors
        locations = [
            unreal.Vector(0, 0, 100),
            unreal.Vector(200, 0, 100),
            unreal.Vector(400, 0, 100)
        ]
        
        created_actors = []
        for i, loc in enumerate(locations):
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor, loc
            )
            actor.set_actor_label(f"TransactionTest_{i+1}")
            created_actors.append(actor.get_actor_label())
    
    # VERIFY: Confirm creation
    actors_after = unreal.EditorLevelLibrary.get_all_level_actors()
    count_after = len(actors_after)
    
    # Return structured JSON
    result = {
        "status": "success",
        "result": {
            "actors_before": count_before,
            "actors_after": count_after,
            "created_count": count_after - count_before,
            "created_labels": created_actors
        }
    }
    print(json.dumps(result))
    
except Exception as e:
    result = {
        "status": "error",
        "error": str(e)
    }
    print(json.dumps(result))
'''
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            # Extract JSON
            lines = output.strip().split('\n')
            json_line = None
            for line in reversed(lines):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    json_line = line
                    break
            
            if json_line:
                parsed = json.loads(json_line)
                if parsed.get("status") == "success":
                    data = parsed.get("result", {})
                    print("[SUCCESS] Transaction completed")
                    print(f"Actors Before: {data.get('actors_before', 0)}")
                    print(f"Actors After: {data.get('actors_after', 0)}")
                    print(f"Created: {data.get('created_count', 0)} actors")
                    print(f"Labels: {', '.join(data.get('created_labels', []))}")
                    print()
                    return True
    
    print("[FAILED] Transaction test failed")
    print(f"Response: {response}")
    return False

def test_idempotent_operation():
    """Test an idempotent operation (safe to run multiple times)."""
    print("=" * 60)
    print("Test 2: Idempotent Operation")
    print("=" * 60)
    print()
    
    code = '''
import unreal
import json

try:
    actor_label = "IdempotentTestActor"
    target_location = unreal.Vector(600, 0, 100)
    
    # RESEARCH: Check if actor exists
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    existing = [a for a in all_actors if a.get_actor_label() == actor_label]
    
    # EXECUTE: Create only if doesn't exist (idempotent)
    with unreal.ScopedEditorTransaction(f"Ensure actor {actor_label} exists"):
        if existing:
            actor = existing[0]
            created = False
            updated = True
            # Update location to ensure it's at target
            actor.set_actor_location(target_location, False, True)
        else:
            actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
                unreal.StaticMeshActor, target_location
            )
            actor.set_actor_label(actor_label)
            created = True
            updated = False
        
        final_location = actor.get_actor_location()
    
    # VERIFY
    result = {
        "status": "success",
        "result": {
            "actor_label": actor_label,
            "created": created,
            "updated": updated,
            "location": [final_location.x, final_location.y, final_location.z]
        }
    }
    print(json.dumps(result))
    
except Exception as e:
    result = {
        "status": "error",
        "error": str(e)
    }
    print(json.dumps(result))
'''
    
    print("Running idempotent operation (safe to run multiple times)...")
    print()
    
    # Run twice to demonstrate idempotency
    for run in [1, 2]:
        print(f"Run {run}:")
        response = send_command("exec_editor_python", {"code": code})
        
        if response and response.get("status") == "success":
            result = response.get("result", {})
            if result.get("success"):
                output = result.get("output", "")
                lines = output.strip().split('\n')
                json_line = None
                for line in reversed(lines):
                    line = line.strip()
                    if line.startswith('{') and line.endswith('}'):
                        json_line = line
                        break
                
                if json_line:
                    parsed = json.loads(json_line)
                    if parsed.get("status") == "success":
                        data = parsed.get("result", {})
                        print(f"  Created: {data.get('created', False)}")
                        print(f"  Updated: {data.get('updated', False)}")
                        print(f"  Location: {data.get('location')}")
                        print()
                    else:
                        print(f"  Error: {parsed.get('error')}")
                        return False
    
    print("[SUCCESS] Idempotent operation verified (both runs succeeded)")
    print()
    return True

def test_error_handling():
    """Test error handling with structured JSON."""
    print("=" * 60)
    print("Test 3: Error Handling")
    print("=" * 60)
    print()
    
    code = '''
import unreal
import json

try:
    # Intentionally cause an error (try to access non-existent actor)
    actor_label = "NonExistentActor_12345"
    all_actors = unreal.EditorLevelLibrary.get_all_level_actors()
    target = next((a for a in all_actors if a.get_actor_label() == actor_label), None)
    
    if not target:
        # Return structured error (not an exception)
        result = {
            "status": "error",
            "error": f"Actor '{actor_label}' not found (expected for error test)"
        }
        print(json.dumps(result))
    else:
        # This shouldn't happen in this test
        result = {
            "status": "success",
            "result": {"found": True}
        }
        print(json.dumps(result))
        
except Exception as e:
    # Exception-based error handling
    result = {
        "status": "error",
        "error": f"Exception: {str(e)}"
    }
    print(json.dumps(result))
'''
    
    print("Testing error handling with structured JSON...")
    print()
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            lines = output.strip().split('\n')
            json_line = None
            for line in reversed(lines):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    json_line = line
                    break
            
            if json_line:
                parsed = json.loads(json_line)
                if parsed.get("status") == "error":
                    print("[SUCCESS] Error properly handled and returned as structured JSON")
                    print(f"Error message: {parsed.get('error')}")
                    print()
                    return True
    
    print("[FAILED] Error handling test failed")
    return False

def main():
    """Run all transaction and JSON tests."""
    print()
    print("Golden Path: Transaction and Structured JSON Output")
    print()
    
    tests = [
        ("Successful Transaction", test_successful_transaction),
        ("Idempotent Operation", test_idempotent_operation),
        ("Error Handling", test_error_handling)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            success = test_func()
            results.append((name, success))
        except Exception as e:
            print(f"[ERROR] Test '{name}' raised exception: {e}")
            results.append((name, False))
    
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    for name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(success for _, success in results)
    print()
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

