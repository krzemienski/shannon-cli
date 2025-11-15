"""
Data Models for Shannon V3.5 Autonomous Executor

Defines structures for:
- Library recommendations
- Execution plans
- Execution steps
- Validation criteria
- Execution results

Created: November 15, 2025
Part of: Shannon V3.5 implementation
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


@dataclass
class LibraryRecommendation:
    """Recommended open-source library option"""
    name: str
    description: str
    repository_url: str
    stars: int
    last_updated: datetime
    package_manager: str  # npm, pip, cocoapods, spm, maven, crates
    install_command: str  # "npm install X", "pip install X", etc.
    why_recommended: str
    score: float  # 0-100 quality score
    weekly_downloads: Optional[int] = None
    license: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'name': self.name,
            'description': self.description,
            'repository_url': self.repository_url,
            'stars': self.stars,
            'last_updated': self.last_updated.isoformat(),
            'package_manager': self.package_manager,
            'install_command': self.install_command,
            'why_recommended': self.why_recommended,
            'score': self.score,
            'weekly_downloads': self.weekly_downloads,
            'license': self.license
        }


@dataclass
class ValidationCriteria:
    """Validation requirements for an execution step"""
    tier1_commands: List[str]  # Static: build, lint, types
    tier2_commands: List[str]  # Unit/Integration tests
    tier3_checks: List[str]  # Functional validation steps
    success_indicators: List[str]  # What indicates success
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'tier1': self.tier1_commands,
            'tier2': self.tier2_commands,
            'tier3': self.tier3_checks,
            'success_indicators': self.success_indicators
        }


@dataclass
class ExecutionStep:
    """Single step in execution plan"""
    number: int
    description: str
    files_to_modify: List[str]
    expected_changes: str
    validation_criteria: ValidationCriteria
    estimated_duration_seconds: int
    libraries_needed: List[str] = field(default_factory=list)
    fallback_approaches: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'number': self.number,
            'description': self.description,
            'files_to_modify': self.files_to_modify,
            'expected_changes': self.expected_changes,
            'validation': self.validation_criteria.to_dict(),
            'estimated_seconds': self.estimated_duration_seconds,
            'libraries': self.libraries_needed,
            'fallbacks': self.fallback_approaches
        }


@dataclass
class ExecutionPlan:
    """Complete execution plan for a task"""
    task_description: str
    steps: List[ExecutionStep]
    libraries_discovered: List[LibraryRecommendation]
    research_summary: str
    total_estimated_minutes: int
    branch_name: str
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage in SessionManager"""
        return {
            'task': self.task_description,
            'steps': [step.to_dict() for step in self.steps],
            'libraries': [lib.to_dict() for lib in self.libraries_discovered],
            'research': self.research_summary,
            'estimated_minutes': self.total_estimated_minutes,
            'branch': self.branch_name,
            'created_at': self.created_at.isoformat()
        }


@dataclass
class ValidationResult:
    """Results from 3-tier validation"""
    tier1_passed: bool
    tier2_passed: bool
    tier3_passed: bool
    
    tier1_details: Dict[str, Any] = field(default_factory=dict)
    tier2_details: Dict[str, Any] = field(default_factory=dict)
    tier3_details: Dict[str, Any] = field(default_factory=dict)
    
    failures: List[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    
    @property
    def all_passed(self) -> bool:
        """Check if all tiers passed"""
        return self.tier1_passed and self.tier2_passed and self.tier3_passed
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'tier1': {'passed': self.tier1_passed, 'details': self.tier1_details},
            'tier2': {'passed': self.tier2_passed, 'details': self.tier2_details},
            'tier3': {'passed': self.tier3_passed, 'details': self.tier3_details},
            'all_passed': self.all_passed,
            'failures': self.failures,
            'duration_seconds': self.duration_seconds
        }


@dataclass
class GitCommit:
    """Record of a git commit"""
    hash: str
    message: str
    files: List[str]
    validation_passed: bool
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'hash': self.hash,
            'message': self.message,
            'files': self.files,
            'validation_passed': self.validation_passed,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class ExecutionResult:
    """Final result of autonomous execution"""
    success: bool
    task_description: str
    steps_completed: int
    steps_total: int
    commits_created: List[GitCommit]
    branch_name: str
    duration_seconds: float
    cost_usd: float
    libraries_used: List[str]
    validations_passed: int
    validations_failed: int
    iterations_total: int = 0
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for storage"""
        return {
            'success': self.success,
            'task': self.task_description,
            'steps_completed': self.steps_completed,
            'steps_total': self.steps_total,
            'commits': [c.to_dict() for c in self.commits_created],
            'branch': self.branch_name,
            'duration_seconds': self.duration_seconds,
            'cost_usd': self.cost_usd,
            'libraries_used': self.libraries_used,
            'validations_passed': self.validations_passed,
            'validations_failed': self.validations_failed,
            'iterations': self.iterations_total,
            'error': self.error_message
        }

