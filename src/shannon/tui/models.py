"""
Data models for the TUI Agent Orchestration System.

Defines the core data structures used throughout the orchestration engine
including task graphs, node definitions, complexity levels, and status tracking.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4


class TaskComplexity(Enum):
    """Task complexity level determining agent count and resource allocation."""

    SIMPLE = "simple"          # 3-5 agents
    MEDIUM = "medium"          # 5-10 agents
    HIGH = "high"              # 10-20 agents
    CRITICAL = "critical"      # 20+ agents


class TaskStatus(Enum):
    """Execution status of a task node."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


class AgentStatus(Enum):
    """Status of an individual agent."""

    IDLE = "idle"
    SPAWNING = "spawning"
    ACTIVE = "active"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class ModelTier(Enum):
    """Model tier assignment for task execution."""

    FAST = "fast"              # Research, triage, simple lookups
    STANDARD = "standard"      # Coding, implementation, refactoring
    COMPLEX = "complex"        # Architecture, design, complex analysis


class TaskType(Enum):
    """Category of task for routing and model selection."""

    RESEARCH = "research"
    ANALYSIS = "analysis"
    ARCHITECTURE = "architecture"
    DESIGN = "design"
    IMPLEMENTATION = "implementation"
    TESTING = "testing"
    VALIDATION = "validation"
    REFACTORING = "refactoring"
    DOCUMENTATION = "documentation"
    TRIAGE = "triage"
    REVIEW = "review"


@dataclass
class ProjectInfo:
    """Information about the project being worked on."""

    root_path: str
    language: Optional[str] = None
    framework: Optional[str] = None
    build_system: Optional[str] = None
    test_framework: Optional[str] = None
    file_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskNode:
    """
    A single node in the task execution graph.

    Represents one unit of work to be executed by an agent,
    with dependencies on other nodes and associated metadata.
    """

    node_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    description: str = ""
    task_type: TaskType = TaskType.IMPLEMENTATION
    model_tier: ModelTier = ModelTier.STANDARD
    status: TaskStatus = TaskStatus.PENDING
    agent_status: AgentStatus = AgentStatus.IDLE

    # Graph edges
    dependencies: Set[str] = field(default_factory=set)
    dependents: Set[str] = field(default_factory=set)

    # Execution tracking
    agent_id: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Context injection
    context: Dict[str, Any] = field(default_factory=dict)
    output_artifacts: List[str] = field(default_factory=list)

    # Grouping
    phase: int = 0
    parallel_group: Optional[str] = None

    @property
    def is_ready(self) -> bool:
        """Check if all dependencies are satisfied."""
        return self.status == TaskStatus.PENDING and len(self.dependencies) == 0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration if completed."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize node to dictionary."""
        return {
            "node_id": self.node_id,
            "title": self.title,
            "description": self.description,
            "task_type": self.task_type.value,
            "model_tier": self.model_tier.value,
            "status": self.status.value,
            "agent_status": self.agent_status.value,
            "dependencies": list(self.dependencies),
            "dependents": list(self.dependents),
            "agent_id": self.agent_id,
            "result": self.result,
            "error": self.error,
            "retry_count": self.retry_count,
            "phase": self.phase,
            "parallel_group": self.parallel_group,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


@dataclass
class TaskGraph:
    """
    Directed acyclic graph of task nodes representing a decomposed task.

    Manages the full set of nodes, dependency resolution, and
    progress tracking across the orchestration lifecycle.
    """

    graph_id: str = field(default_factory=lambda: str(uuid4()))
    prompt: str = ""
    complexity: TaskComplexity = TaskComplexity.SIMPLE
    nodes: Dict[str, TaskNode] = field(default_factory=dict)

    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    total_phases: int = 0

    @property
    def node_list(self) -> List[TaskNode]:
        """Get all nodes as a list."""
        return list(self.nodes.values())

    @property
    def completed_count(self) -> int:
        """Count of completed nodes."""
        return sum(
            1 for n in self.nodes.values()
            if n.status == TaskStatus.COMPLETED
        )

    @property
    def failed_count(self) -> int:
        """Count of failed nodes."""
        return sum(
            1 for n in self.nodes.values()
            if n.status == TaskStatus.FAILED
        )

    @property
    def total_count(self) -> int:
        """Total number of nodes."""
        return len(self.nodes)

    @property
    def progress_percent(self) -> float:
        """Overall progress as a percentage."""
        if not self.nodes:
            return 0.0
        return (self.completed_count / self.total_count) * 100.0

    @property
    def is_complete(self) -> bool:
        """Check if all nodes are in a terminal state."""
        terminal = {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.SKIPPED}
        return all(n.status in terminal for n in self.nodes.values())

    def add_node(self, node: TaskNode) -> None:
        """Add a node to the graph."""
        self.nodes[node.node_id] = node

    def add_dependency(self, from_id: str, to_id: str) -> None:
        """Add a dependency edge: from_id depends on to_id."""
        if from_id in self.nodes and to_id in self.nodes:
            self.nodes[from_id].dependencies.add(to_id)
            self.nodes[to_id].dependents.add(from_id)

    def get_ready_nodes(self) -> List[TaskNode]:
        """Get all nodes whose dependencies are fully satisfied."""
        ready = []
        for node in self.nodes.values():
            if node.status != TaskStatus.PENDING:
                continue
            deps_satisfied = all(
                self.nodes[dep_id].status == TaskStatus.COMPLETED
                for dep_id in node.dependencies
                if dep_id in self.nodes
            )
            if deps_satisfied:
                ready.append(node)
        return ready

    def get_nodes_by_phase(self, phase: int) -> List[TaskNode]:
        """Get all nodes in a specific phase."""
        return [n for n in self.nodes.values() if n.phase == phase]

    def mark_completed(self, node_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """Mark a node as completed."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = TaskStatus.COMPLETED
            node.agent_status = AgentStatus.COMPLETED
            node.completed_at = datetime.utcnow()
            node.result = result

    def mark_failed(self, node_id: str, error: str) -> None:
        """Mark a node as failed."""
        if node_id in self.nodes:
            node = self.nodes[node_id]
            node.status = TaskStatus.FAILED
            node.agent_status = AgentStatus.FAILED
            node.error = error
            node.completed_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Serialize graph to dictionary."""
        return {
            "graph_id": self.graph_id,
            "prompt": self.prompt,
            "complexity": self.complexity.value,
            "nodes": {nid: n.to_dict() for nid, n in self.nodes.items()},
            "total_phases": self.total_phases,
            "progress_percent": self.progress_percent,
            "created_at": self.created_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


# ---------------------------------------------------------------------------
# Model configuration and agent models
# ---------------------------------------------------------------------------


@dataclass
class ModelConfig:
    """Configuration for a model tier including model ID and resource limits."""

    model_id: str
    max_tokens: int = 16384
    temperature: float = 0.0
    timeout_seconds: int = 300
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "model_id": self.model_id,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "max_retries": self.max_retries,
            "metadata": self.metadata,
        }


@dataclass
class AgentConfig:
    """Configuration for spawning an agent."""

    agent_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    model_tier: ModelTier = ModelTier.STANDARD
    task_type: TaskType = TaskType.IMPLEMENTATION
    max_tokens: int = 16384
    temperature: float = 0.0
    timeout_seconds: int = 300
    tools: List[str] = field(default_factory=list)
    system_instructions: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "model_tier": self.model_tier.value,
            "task_type": self.task_type.value,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "timeout_seconds": self.timeout_seconds,
            "tools": self.tools,
            "system_instructions": self.system_instructions,
            "metadata": self.metadata,
        }


@dataclass
class AgentState:
    """Runtime state of a managed agent within the TUI orchestration system."""

    agent_id: str = field(default_factory=lambda: str(uuid4()))
    config: Optional[AgentConfig] = None
    task_node_id: Optional[str] = None
    status: AgentStatus = AgentStatus.IDLE

    # Execution artefacts
    thoughts: List[str] = field(default_factory=list)
    actions: List[Dict[str, Any]] = field(default_factory=list)
    text_output: List[str] = field(default_factory=list)
    progress: float = 0.0
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Metrics
    tokens_in: int = 0
    tokens_out: int = 0
    cost_usd: float = 0.0

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate execution duration if started."""
        if self.started_at:
            end = self.completed_at or datetime.utcnow()
            return (end - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "agent_id": self.agent_id,
            "config": self.config.to_dict() if self.config else None,
            "task_node_id": self.task_node_id,
            "status": self.status.value,
            "thoughts": self.thoughts,
            "actions": self.actions,
            "text_output": self.text_output,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "tokens_in": self.tokens_in,
            "tokens_out": self.tokens_out,
            "cost_usd": self.cost_usd,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentState":
        """Deserialize from dictionary."""
        state = cls(
            agent_id=data.get("agent_id", str(uuid4())),
            task_node_id=data.get("task_node_id"),
            status=AgentStatus(data.get("status", "idle")),
            thoughts=data.get("thoughts", []),
            actions=data.get("actions", []),
            text_output=data.get("text_output", []),
            progress=data.get("progress", 0.0),
            result=data.get("result"),
            error=data.get("error"),
            tokens_in=data.get("tokens_in", 0),
            tokens_out=data.get("tokens_out", 0),
            cost_usd=data.get("cost_usd", 0.0),
        )
        if data.get("created_at"):
            state.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("started_at"):
            state.started_at = datetime.fromisoformat(data["started_at"])
        if data.get("completed_at"):
            state.completed_at = datetime.fromisoformat(data["completed_at"])
        return state


# ---------------------------------------------------------------------------
# Context and memory models
# ---------------------------------------------------------------------------


class MemoryType(Enum):
    """Types of memory entries."""

    DECISION = "decision"
    INSIGHT = "insight"
    ERROR_PATTERN = "error_pattern"
    CODE_PATTERN = "code_pattern"
    ARCHITECTURE = "architecture"
    REQUIREMENT = "requirement"
    CONVERSATION = "conversation"
    SESSION_NOTE = "session_note"
    AGENT_OUTPUT = "agent_output"


@dataclass
class ContextItem:
    """A single item of context available to agents."""

    item_id: str = field(default_factory=lambda: str(uuid4()))
    content: str = ""
    source: str = ""
    context_type: str = "general"
    relevance_score: float = 1.0
    token_estimate: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "item_id": self.item_id,
            "content": self.content,
            "source": self.source,
            "context_type": self.context_type,
            "relevance_score": self.relevance_score,
            "token_estimate": self.token_estimate,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContextItem":
        """Deserialize from dictionary."""
        item = cls(
            item_id=data.get("item_id", str(uuid4())),
            content=data.get("content", ""),
            source=data.get("source", ""),
            context_type=data.get("context_type", "general"),
            relevance_score=data.get("relevance_score", 1.0),
            token_estimate=data.get("token_estimate", 0),
            metadata=data.get("metadata", {}),
        )
        if data.get("created_at"):
            item.created_at = datetime.fromisoformat(data["created_at"])
        return item


@dataclass
class MemoryEntry:
    """A persistent memory entry stored across tiers."""

    memory_id: str = field(default_factory=lambda: str(uuid4()))
    memory_type: MemoryType = MemoryType.SESSION_NOTE
    content: str = ""
    source_task: str = ""
    source_agent: str = ""
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    access_count: int = 0
    relevance_score: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "memory_id": self.memory_id,
            "memory_type": self.memory_type.value,
            "content": self.content,
            "source_task": self.source_task,
            "source_agent": self.source_agent,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "relevance_score": self.relevance_score,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MemoryEntry":
        """Deserialize from dictionary."""
        entry = cls(
            memory_id=data.get("memory_id", str(uuid4())),
            memory_type=MemoryType(data.get("memory_type", "session_note")),
            content=data.get("content", ""),
            source_task=data.get("source_task", ""),
            source_agent=data.get("source_agent", ""),
            tags=data.get("tags", []),
            access_count=data.get("access_count", 0),
            relevance_score=data.get("relevance_score", 1.0),
            metadata=data.get("metadata", {}),
        )
        if data.get("created_at"):
            entry.created_at = datetime.fromisoformat(data["created_at"])
        if data.get("updated_at"):
            entry.updated_at = datetime.fromisoformat(data["updated_at"])
        return entry


# ---------------------------------------------------------------------------
# Validation models
# ---------------------------------------------------------------------------


class ValidatorType(Enum):
    """Types of validators available for project validation."""

    BROWSER = "browser"
    CLI = "cli"
    API = "api"
    IOS_SIMULATOR = "ios_simulator"


class ValidationStatus(Enum):
    """Status of a validation step or run."""

    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class ValidationStep:
    """A single validation step to be executed by a validator."""

    step_id: str = field(default_factory=lambda: str(uuid4()))
    name: str = ""
    description: str = ""
    validator_type: ValidatorType = ValidatorType.CLI
    command: Optional[str] = None
    expected_exit_code: int = 0
    expected_output: Optional[str] = None
    url: Optional[str] = None
    method: str = "GET"
    body: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    expected_status_code: Optional[int] = None
    expected_body_pattern: Optional[str] = None
    status: ValidationStatus = ValidationStatus.PENDING
    output: Optional[str] = None
    error: Optional[str] = None
    screenshot_path: Optional[str] = None
    duration_seconds: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "description": self.description,
            "validator_type": self.validator_type.value,
            "command": self.command,
            "expected_exit_code": self.expected_exit_code,
            "expected_output": self.expected_output,
            "url": self.url,
            "method": self.method,
            "body": self.body,
            "headers": self.headers,
            "expected_status_code": self.expected_status_code,
            "expected_body_pattern": self.expected_body_pattern,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "screenshot_path": self.screenshot_path,
            "duration_seconds": self.duration_seconds,
            "metadata": self.metadata,
        }


@dataclass
class ValidationPlan:
    """A plan containing multiple validation steps to execute."""

    plan_id: str = field(default_factory=lambda: str(uuid4()))
    task_description: str = ""
    steps: List[ValidationStep] = field(default_factory=list)
    validator_types: List[ValidatorType] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "plan_id": self.plan_id,
            "task_description": self.task_description,
            "steps": [s.to_dict() for s in self.steps],
            "validator_types": [v.value for v in self.validator_types],
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


@dataclass
class ValidationRun:
    """Result of executing a validation plan."""

    run_id: str = field(default_factory=lambda: str(uuid4()))
    plan_id: str = ""
    status: ValidationStatus = ValidationStatus.PENDING
    steps: List[ValidationStep] = field(default_factory=list)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    retry_history: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def passed_count(self) -> int:
        """Count of passed steps."""
        return sum(1 for s in self.steps if s.status == ValidationStatus.PASSED)

    @property
    def failed_count(self) -> int:
        """Count of failed steps."""
        return sum(
            1 for s in self.steps
            if s.status in (ValidationStatus.FAILED, ValidationStatus.ERROR)
        )

    @property
    def all_passed(self) -> bool:
        """Check if all steps passed."""
        return all(
            s.status in (ValidationStatus.PASSED, ValidationStatus.SKIPPED)
            for s in self.steps
        )

    @property
    def failed_steps(self) -> List[ValidationStep]:
        """Get list of failed steps."""
        return [
            s for s in self.steps
            if s.status in (ValidationStatus.FAILED, ValidationStatus.ERROR)
        ]

    @property
    def duration_seconds(self) -> Optional[float]:
        """Calculate total run duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "run_id": self.run_id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "steps": [s.to_dict() for s in self.steps],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": (
                self.completed_at.isoformat() if self.completed_at else None
            ),
            "retry_count": self.retry_count,
            "retry_history": self.retry_history,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "all_passed": self.all_passed,
            "metadata": self.metadata,
        }
