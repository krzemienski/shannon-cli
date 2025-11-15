"""
Shannon V3.5 Autonomous Executor

Enhancement layer on existing Shannon Framework that adds:
- Library discovery (don't reinvent the wheel)
- 3-tier functional validation
- Atomic git commits
- Research-driven iteration
- System prompt customization

Architecture:
    /shannon:exec skill (in Shannon Framework)
      ↓
    Orchestrates existing skills:
      - /shannon:prime (context)
      - /shannon:analyze (understanding)
      - /shannon:wave (execution)
      ↓
    Wraps with new functionality:
      - LibraryDiscoverer (find existing packages)
      - ValidationOrchestrator (validate functionally)
      - GitManager (atomic commits)

Created: November 15, 2025
Part of: Shannon V3.5 implementation
"""

from .prompts import (
    LIBRARY_DISCOVERY_INSTRUCTIONS,
    FUNCTIONAL_VALIDATION_INSTRUCTIONS,
    GIT_WORKFLOW_INSTRUCTIONS,
    get_combined_core_instructions
)

from .task_enhancements import (
    get_enhancement_for_project,
    get_all_project_types
)

from .prompt_enhancer import PromptEnhancer

from .models import (
    LibraryRecommendation,
    ValidationCriteria,
    ExecutionStep,
    ExecutionPlan,
    ValidationResult,
    GitCommit,
    ExecutionResult
)

from .library_discoverer import LibraryDiscoverer
from .validator import ValidationOrchestrator
from .git_manager import GitManager
from .simple_executor import SimpleTaskExecutor

__all__ = [
    # Prompts
    'LIBRARY_DISCOVERY_INSTRUCTIONS',
    'FUNCTIONAL_VALIDATION_INSTRUCTIONS',
    'GIT_WORKFLOW_INSTRUCTIONS',
    'get_combined_core_instructions',
    'get_enhancement_for_project',
    'get_all_project_types',
    
    # Components
    'PromptEnhancer',
    'LibraryDiscoverer',
    'ValidationOrchestrator',
    'GitManager',
    'SimpleTaskExecutor',
    
    # Models
    'LibraryRecommendation',
    'ValidationCriteria',
    'ExecutionStep',
    'ExecutionPlan',
    'ValidationResult',
    'GitCommit',
    'ExecutionResult'
]

__version__ = '3.5.0'

