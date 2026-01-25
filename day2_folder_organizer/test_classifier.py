#!/usr/bin/env python3
"""
Test script for the enhanced get_available_models function.
This tests the function without requiring ollama to be installed.
"""

import subprocess
import sys
import os

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_get_available_models():
    """Test the get_available_models function with mock scenarios"""

    # Test 1: Ollama not installed
    print("Test 1: Ollama not installed")
    try:
        # Mock subprocess to simulate ollama not found
        original_run = subprocess.run
        def mock_run(cmd, **kwargs):
            if cmd[0] == 'which' and cmd[1] == 'ollama':
                return type('MockResult', (), {'returncode': 1, 'stdout': '', 'stderr': ''})()
            return original_run(cmd, **kwargs)

        subprocess.run = mock_run

        # Import after mocking
        from classifier import get_available_models
        models, status = get_available_models()
        print(f"  Result: models={models}, status='{status}'")
        assert status == 'not_installed', f"Expected 'not_installed', got '{status}'"
        print("  ✅ PASS")

    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 2: Ollama installed but no models
    print("\nTest 2: Ollama installed but no models")
    try:
        def mock_run2(cmd, **kwargs):
            if cmd == ['which', 'ollama']:
                return type('MockResult', (), {'returncode': 0, 'stdout': '/usr/bin/ollama', 'stderr': ''})()
            elif cmd == ['ollama', 'list']:
                return type('MockResult', (), {'returncode': 0, 'stdout': 'NAME\n', 'stderr': ''})()
            return original_run(cmd, **kwargs)

        subprocess.run = mock_run2

        # Re-import to get fresh function
        import importlib
        import classifier
        importlib.reload(classifier)
        from classifier import get_available_models

        models, status = get_available_models()
        print(f"  Result: models={models}, status='{status}'")
        assert status == 'no_models' or status == 'ok', f"Expected 'no_models' or 'ok', got '{status}'"
        print("  ✅ PASS")

    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Test 3: Ollama with models
    print("\nTest 3: Ollama with models")
    try:
        def mock_run3(cmd, **kwargs):
            if cmd == ['which', 'ollama']:
                return type('MockResult', (), {'returncode': 0, 'stdout': '/usr/bin/ollama', 'stderr': ''})()
            elif cmd == ['ollama', 'list']:
                return type('MockResult', (), {'returncode': 0, 'stdout': 'NAME\nllama2:7b\ncodellama:7b\ngemma3:4b\n', 'stderr': ''})()
            return original_run(cmd, **kwargs)

        subprocess.run = mock_run3

        importlib.reload(classifier)
        from classifier import get_available_models

        models, status = get_available_models()
        print(f"  Result: models={models}, status='{status}'")
        assert status == 'ok', f"Expected 'ok', got '{status}'"
        assert len(models) == 3, f"Expected 3 models, got {len(models)}"
        assert 'gemma3:4b' in models, f"'gemma3:4b' not in models: {models}"
        print("  ✅ PASS")

    except Exception as e:
        print(f"  ❌ FAIL: {e}")

    # Restore original subprocess.run
    subprocess.run = original_run

if __name__ == "__main__":
    print("Testing enhanced get_available_models function...")
    test_get_available_models()
    print("\nTest completed!")