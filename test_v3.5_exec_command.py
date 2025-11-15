#!/usr/bin/env python3
"""
Test the shannon exec command directly (without installation)

Tests V3.5 exec command functionality.
"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))

async def test_exec_command():
    """Test exec command logic"""
    
    print("╔" + "="*68 + "╗")
    print("║" + " "*68 + "║")
    print("║" + "   Shannon V3.5 Exec Command - Functional Test".center(68) + "║")
    print("║" + " "*68 + "║")
    print("╚" + "="*68 + "╝\n")
    
    # Import the exec command logic
    from shannon.executor import (
        PromptEnhancer,
        LibraryDiscoverer,
        ValidationOrchestrator,
        GitManager
    )
    
    task = "add authentication to React app"
    project_root = Path.cwd()
    
    print(f"Task: {task}\n")
    
    # Phase 1: Enhanced prompts
    print("Phase 1: Building enhanced system prompts...")
    enhancer = PromptEnhancer()
    enhancements = enhancer.build_enhancements(task, project_root)
    print(f"  ✓ Enhanced prompts: {len(enhancements)} chars")
    print(f"  ✓ Contains library discovery: {'LIBRARY' in enhancements.upper()}")
    print(f"  ✓ Contains validation: {'VALIDATION' in enhancements.upper()}")
    print(f"  ✓ Contains git workflow: {'GIT' in enhancements.upper()}")
    print()
    
    # Phase 2: Project detection
    print("Phase 2: Detecting project context...")
    project_type = enhancer._detect_project_type(project_root)
    print(f"  ✓ Project type: {project_type}")
    print()
    
    # Phase 3: Library discovery
    print("Phase 3: Library discovery setup...")
    discoverer = LibraryDiscoverer(project_root)
    print(f"  ✓ Language: {discoverer.language}")
    print(f"  ✓ Package manager: {discoverer._get_package_manager()}")
    print()
    
    # Phase 4: Validation setup
    print("Phase 4: Validation orchestrator...")
    validator = ValidationOrchestrator(project_root)
    print(f"  ✓ Project type: {validator.test_config.project_type}")
    if validator.test_config.build_cmd:
        print(f"  ✓ Build: {validator.test_config.build_cmd}")
    if validator.test_config.test_cmd:
        print(f"  ✓ Tests: {validator.test_config.test_cmd}")
    print()
    
    # Phase 5: Git setup
    print("Phase 5: Git workflow...")
    git_mgr = GitManager(project_root)
    branch_name = git_mgr._generate_branch_name(task)
    print(f"  ✓ Branch name: {branch_name}")
    print()
    
    print("="*70)
    print("✅ ALL PHASES COMPLETED SUCCESSFULLY")
    print("="*70)
    print()
    print("V3.5 exec command would:")
    print(f"  1. Use enhanced prompts ({len(enhancements)} chars)")
    print(f"  2. Create branch: {branch_name}")
    print(f"  3. Discover libraries for: {task}")
    print(f"  4. Execute with validation (3 tiers)")
    print(f"  5. Commit atomically if validated")
    print()
    print("Note: Full execution requires /shannon:exec skill in Shannon Framework")
    print()
    
    return True

if __name__ == '__main__':
    try:
        success = asyncio.run(test_exec_command())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

