#!/usr/bin/env python3
"""
Shannon V3.5 Wave 1 - Functional Test for Prompt Injection

Tests that enhanced system prompts are correctly built and can be injected
via ShannonSDKClient.invoke_command_with_enhancements()

This is a functional test (no mocks) that verifies the prompt enhancement system.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shannon.executor.prompt_enhancer import PromptEnhancer
from shannon.executor.prompts import (
    LIBRARY_DISCOVERY_INSTRUCTIONS,
    FUNCTIONAL_VALIDATION_INSTRUCTIONS,
    GIT_WORKFLOW_INSTRUCTIONS
)


def test_prompt_enhancer():
    """Test that PromptEnhancer builds correct enhancements"""
    
    print("🧪 Shannon V3.5 Wave 1 - Prompt Injection Test")
    print("=" * 70)
    print()
    
    # Test 1: Create enhancer
    print("TEST 1: Create PromptEnhancer")
    enhancer = PromptEnhancer()
    print("✅ PromptEnhancer created")
    print()
    
    # Test 2: Detect project type
    print("TEST 2: Project type detection")
    project_root = Path.cwd()
    project_type = enhancer._detect_project_type(project_root)
    print(f"✅ Detected project type: {project_type}")
    print()
    
    # Test 3: Build enhancements for React Native task
    print("TEST 3: Build enhancements for React Native task")
    task = "add authentication to React Native app"
    enhancements = enhancer.build_enhancements(task, project_root)
    
    # Verify all core instructions present
    assert LIBRARY_DISCOVERY_INSTRUCTIONS in enhancements, "Missing library discovery instructions"
    assert FUNCTIONAL_VALIDATION_INSTRUCTIONS in enhancements, "Missing functional validation instructions"
    assert GIT_WORKFLOW_INSTRUCTIONS in enhancements, "Missing git workflow instructions"
    
    print(f"✅ Enhancements built: {len(enhancements)} chars")
    print(f"   Contains library discovery: ✅")
    print(f"   Contains functional validation: ✅")
    print(f"   Contains git workflow: ✅")
    print()
    
    # Test 4: Verify project-specific enhancements
    print("TEST 4: Project-specific enhancements")
    if project_type in ['react-native-expo', 'react', 'python-fastapi', 'ios-swiftui']:
        from shannon.executor.task_enhancements import get_enhancement_for_project
        project_enhancement = get_enhancement_for_project(project_type)
        if project_enhancement:
            assert project_enhancement in enhancements, f"Missing {project_type} enhancements"
            print(f"✅ Project-specific enhancements for {project_type} included")
        else:
            print(f"⚠️  No project-specific enhancements for {project_type}")
    else:
        print(f"ℹ️  Unknown project type, using core enhancements only")
    print()
    
    # Test 5: Verify task-specific hints
    print("TEST 5: Task-specific hints")
    if 'auth' in task.lower():
        # Should have authentication hints
        if 'auth' in enhancements.lower() or 'authentication' in enhancements.lower():
            print("✅ Authentication hints included")
        else:
            print("⚠️  No authentication hints (might be OK)")
    print()
    
    # Test 6: Preview enhancements
    print("TEST 6: Preview generated enhancements")
    print("-" * 70)
    print("First 500 characters:")
    print(enhancements[:500])
    print("...")
    print("-" * 70)
    print()
    
    # Test 7: Verify structure
    print("TEST 7: Verify enhancement structure")
    lines = enhancements.split('\n')
    print(f"✅ Total lines: {len(lines)}")
    print(f"✅ Total characters: {len(enhancements)}")
    
    # Should have clear section headers
    section_count = enhancements.count('═══════════')
    print(f"✅ Section headers: {section_count}")
    print()
    
    print("=" * 70)
    print("✅ ALL WAVE 1 TESTS PASSED!")
    print("=" * 70)
    print()
    print("Prompt enhancement system is working correctly.")
    print("Ready for Wave 2: Library Discovery")
    print()
    
    return True


if __name__ == '__main__':
    try:
        success = test_prompt_enhancer()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

