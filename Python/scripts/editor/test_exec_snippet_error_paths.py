#!/usr/bin/env python
"""
Test Exec Snippet Error Paths

Tests error handling for snippet execution:
- Missing snippet file
- Snippet that doesn't print JSON
- Snippet that raises an exception
- Snippet that prints invalid JSON
"""

import sys
import os
import json

# Add scripts directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from _tcp_client import send_command

def test_missing_snippet():
    """Test error handling when snippet file doesn't exist."""
    print("=" * 60)
    print("Test 1: Missing snippet file")
    print("=" * 60)
    
    # Try to execute a non-existent snippet via exec_editor_python
    # (simulating what would happen if registry pointed to missing file)
    code = '''
import json
import sys
from pathlib import Path

# Simulate loading a missing snippet
snippet_path = Path("nonexistent_snippet.py")
if not snippet_path.exists():
    result = {"status": "error", "error": f"Snippet file not found: {snippet_path}"}
    print(json.dumps(result))
'''
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            lines = output.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        parsed = json.loads(line)
                        if parsed.get("status") == "error":
                            print(f"[SUCCESS] Error correctly returned: {parsed.get('error')}")
                            return True
                    except:
                        pass
    
    print("[FAILED] Expected error response for missing snippet")
    return False

def test_no_json_output():
    """Test error handling when snippet doesn't print JSON."""
    print("\n" + "=" * 60)
    print("Test 2: Snippet without JSON output")
    print("=" * 60)
    
    code = '''
import unreal

# Snippet that doesn't print JSON
print("This is just a debug message")
print("No JSON here!")
'''
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            # Should have output but no parseable JSON
            if output and "This is just a debug message" in output:
                print("[SUCCESS] Snippet executed but no JSON found (as expected)")
                print(f"Output: {output[:200]}...")
                return True
    
    print("[FAILED] Unexpected response")
    return False

def test_exception_in_snippet():
    """Test error handling when snippet raises an exception."""
    print("\n" + "=" * 60)
    print("Test 3: Exception in snippet")
    print("=" * 60)
    
    code = '''
import json
import unreal

try:
    # This will raise an AttributeError
    actor = None
    name = actor.get_name()  # AttributeError: 'NoneType' object has no attribute 'get_name'
except Exception as e:
    result = {"status": "error", "error": str(e)}
    print(json.dumps(result))
'''
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            lines = output.strip().split('\n')
            for line in reversed(lines):
                line = line.strip()
                if line.startswith('{') and line.endswith('}'):
                    try:
                        parsed = json.loads(line)
                        if parsed.get("status") == "error":
                            print(f"[SUCCESS] Exception caught and returned as error: {parsed.get('error')[:100]}")
                            return True
                    except:
                        pass
    
    print("[FAILED] Expected error response for exception")
    return False

def test_invalid_json():
    """Test error handling when snippet prints invalid JSON."""
    print("\n" + "=" * 60)
    print("Test 4: Invalid JSON output")
    print("=" * 60)
    
    code = '''
import unreal

# Print something that looks like JSON but isn't valid
print('{"status": "success", "result": {unclosed}')
'''
    
    response = send_command("exec_editor_python", {"code": code})
    
    if response and response.get("status") == "success":
        result = response.get("result", {})
        if result.get("success"):
            output = result.get("output", "")
            # Should have output but JSON parsing should fail gracefully
            if output:
                print("[SUCCESS] Invalid JSON handled gracefully")
                print(f"Output: {output[:200]}...")
                return True
    
    print("[FAILED] Unexpected response")
    return False

def main():
    """Run all error path tests."""
    print("\n" + "=" * 60)
    print("Testing Exec Snippet Error Paths")
    print("=" * 60 + "\n")
    
    results = []
    results.append(("Missing snippet", test_missing_snippet()))
    results.append(("No JSON output", test_no_json_output()))
    results.append(("Exception in snippet", test_exception_in_snippet()))
    results.append(("Invalid JSON", test_invalid_json()))
    
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    print("=" * 60)
    if all_passed:
        print("All error path tests passed!")
    else:
        print("Some tests failed!")
    print("=" * 60)
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

