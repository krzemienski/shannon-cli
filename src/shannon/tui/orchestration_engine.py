"""
Core Orchestration Engine for the TUI Agent Orchestration System.

Coordinates complexity assessment, task decomposition, and parallel
agent execution across a dependency-aware task graph. Emits lifecycle
events to the EventBus and tracks progress in real time.
"""

from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Sequence
from uuid import uuid4

from shannon.communication.events import EventBus, EventType
from shannon.tui.models import (
    AgentStatus,
    ModelTier,
    ProjectInfo,
    TaskComplexity,
    TaskGraph,
    TaskNode,
    TaskStatus,
    TaskType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword / heuristic tables used by ComplexityAssessor
# ---------------------------------------------------------------------------

_SCOPE_INDICATORS: frozenset[str] = frozenset({
    "entire", "all", "system-wide", "whole", "every", "complete",
    "full", "comprehensive", "end-to-end", "global", "across",
})

_HIGH_COMPLEXITY_KEYWORDS: frozenset[str] = frozenset({
    "migrate", "migration", "rewrite", "overhaul", "redesign",
    "restructure", "refactor", "integrate", "microservice",
    "distributed", "scalable", "architecture", "platform",
    "infrastructure", "pipeline", "ci/cd", "deploy",
})

_MEDIUM_COMPLEXITY_KEYWORDS: frozenset[str] = frozenset({
    "implement", "feature", "module", "component", "api",
    "endpoint", "service", "database", "schema", "test",
    "authentication", "authorization", "crud", "dashboard",
})

_ACTION_VERBS: frozenset[str] = frozenset({
    "create", "build", "add", "implement", "write", "design",
    "update", "modify", "fix", "refactor", "test", "deploy",
    "configure", "setup", "integrate", "remove", "delete",
    "optimize", "migrate", "convert", "replace", "extract",
})

# Mapping from TaskType to the default ModelTier assignment.
_TASK_TYPE_TO_TIER: Dict[TaskType, ModelTier] = {
    TaskType.ARCHITECTURE: ModelTier.COMPLEX,
    TaskType.DESIGN: ModelTier.COMPLEX,
    TaskType.ANALYSIS: ModelTier.COMPLEX,
    TaskType.REVIEW: ModelTier.COMPLEX,
    TaskType.IMPLEMENTATION: ModelTier.STANDARD,
    TaskType.TESTING: ModelTier.STANDARD,
    TaskType.REFACTORING: ModelTier.STANDARD,
    TaskType.DOCUMENTATION: ModelTier.STANDARD,
    TaskType.RESEARCH: ModelTier.FAST,
    TaskType.TRIAGE: ModelTier.FAST,
    TaskType.VALIDATION: ModelTier.FAST,
}


# ---------------------------------------------------------------------------
# ComplexityAssessor
# ---------------------------------------------------------------------------


class ComplexityAssessor:
    """Analyse a user prompt and determine its task complexity level.

    Uses lightweight heuristics — keyword frequency, scope indicators,
    action verb count, and file-count references — to bucket the prompt
    into one of the ``TaskComplexity`` levels.
    """

    def assess(self, prompt: str) -> TaskComplexity:
        """Return the assessed ``TaskComplexity`` for *prompt*."""
        lower = prompt.lower()
        tokens = re.findall(r"[a-z0-9/\-]+", lower)
        token_set = set(tokens)

        score = 0

        # --- scope indicators ---
        scope_hits = token_set & _SCOPE_INDICATORS
        score += len(scope_hits) * 3

        # --- high-complexity keywords ---
        high_hits = token_set & _HIGH_COMPLEXITY_KEYWORDS
        score += len(high_hits) * 4

        # --- medium-complexity keywords ---
        medium_hits = token_set & _MEDIUM_COMPLEXITY_KEYWORDS
        score += len(medium_hits) * 2

        # --- distinct action verbs ---
        action_hits = token_set & _ACTION_VERBS
        score += len(action_hits) * 2

        # --- file count references (e.g. "15 files", "50+ files") ---
        file_refs = re.findall(r"(\d+)\+?\s*files?", lower)
        for ref in file_refs:
            count = int(ref)
            if count >= 50:
                score += 10
            elif count >= 20:
                score += 6
            elif count >= 5:
                score += 3

        # --- raw prompt length (long prompts often describe complex work) ---
        word_count = len(lower.split())
        if word_count > 200:
            score += 5
        elif word_count > 100:
            score += 3
        elif word_count > 50:
            score += 1

        # --- map score to complexity ---
        if score >= 20:
            return TaskComplexity.CRITICAL
        if score >= 12:
            return TaskComplexity.HIGH
        if score >= 6:
            return TaskComplexity.MEDIUM
        return TaskComplexity.SIMPLE

    # Expose the internals for testing / debugging.
    def score_breakdown(self, prompt: str) -> Dict[str, Any]:
        """Return a detailed scoring breakdown (useful for debugging)."""
        lower = prompt.lower()
        tokens = re.findall(r"[a-z0-9/\-]+", lower)
        token_set = set(tokens)
        return {
            "scope_indicators": sorted(token_set & _SCOPE_INDICATORS),
            "high_keywords": sorted(token_set & _HIGH_COMPLEXITY_KEYWORDS),
            "medium_keywords": sorted(token_set & _MEDIUM_COMPLEXITY_KEYWORDS),
            "action_verbs": sorted(token_set & _ACTION_VERBS),
            "word_count": len(lower.split()),
            "complexity": self.assess(prompt).value,
        }


# ---------------------------------------------------------------------------
# TaskDecomposer
# ---------------------------------------------------------------------------


class TaskDecomposer:
    """Decompose a user prompt into a DAG of ``TaskNode`` objects.

    The decomposer identifies discrete sub-tasks implied by the prompt,
    groups independent tasks for parallel execution, chains dependent
    tasks sequentially, and assigns an appropriate ``ModelTier`` to each
    node.
    """

    # Patterns that hint at specific task types within a prompt.
    _TYPE_PATTERNS: List[tuple[str, TaskType]] = [
        (r"\b(?:architect|design|plan|blueprint)\b", TaskType.ARCHITECTURE),
        (r"\b(?:research|investigate|explore|look\s+into|survey)\b", TaskType.RESEARCH),
        (r"\b(?:analys[ei]|assess|evaluat)\b", TaskType.ANALYSIS),
        (r"\b(?:test|spec|unit\s*test|integration\s*test)\b", TaskType.TESTING),
        (r"\b(?:refactor|restructure|clean\s*up)\b", TaskType.REFACTORING),
        (r"\b(?:document|readme|docstring|doc)\b", TaskType.DOCUMENTATION),
        (r"\b(?:review|code\s*review|audit)\b", TaskType.REVIEW),
        (r"\b(?:triage|prioriti[sz]e|classify)\b", TaskType.TRIAGE),
        (r"\b(?:valid|lint|check|verify)\b", TaskType.VALIDATION),
        (r"\b(?:implement|build|create|add|write|develop|code)\b", TaskType.IMPLEMENTATION),
    ]

    def decompose(
        self,
        prompt: str,
        complexity: TaskComplexity,
        project_info: Optional[ProjectInfo] = None,
    ) -> TaskGraph:
        """Build a ``TaskGraph`` from the user *prompt*.

        Parameters
        ----------
        prompt:
            Raw user request.
        complexity:
            Pre-assessed complexity level.
        project_info:
            Optional project metadata to influence decomposition.

        Returns
        -------
        TaskGraph
            A fully wired DAG ready for execution.
        """
        graph = TaskGraph(prompt=prompt, complexity=complexity)

        # Determine the tasks implied by the prompt.
        detected_types = self._detect_task_types(prompt)

        # Ensure at least a basic set of tasks exists.
        if not detected_types:
            detected_types = [TaskType.IMPLEMENTATION]

        # Build the initial ordered plan.
        plan = self._build_plan(detected_types, complexity, prompt, project_info)

        # Assign phases and wire dependencies.
        self._assign_phases(plan)

        for node in plan:
            graph.add_node(node)

        # Add dependency edges within the graph.
        for node in plan:
            for dep_id in node.dependencies:
                graph.add_dependency(node.node_id, dep_id)

        graph.total_phases = max((n.phase for n in plan), default=0) + 1
        return graph

    # -- internal helpers ----------------------------------------------------

    def _detect_task_types(self, prompt: str) -> List[TaskType]:
        """Scan *prompt* for recognisable task-type patterns."""
        lower = prompt.lower()
        found: List[TaskType] = []
        seen: set[TaskType] = set()
        for pattern, ttype in self._TYPE_PATTERNS:
            if re.search(pattern, lower) and ttype not in seen:
                found.append(ttype)
                seen.add(ttype)
        return found

    def _build_plan(
        self,
        task_types: List[TaskType],
        complexity: TaskComplexity,
        prompt: str,
        project_info: Optional[ProjectInfo],
    ) -> List[TaskNode]:
        """Create an ordered list of ``TaskNode`` objects for the plan."""
        nodes: List[TaskNode] = []

        # For MEDIUM+ complexity, always start with a research / analysis
        # phase so subsequent agents have shared context.
        if complexity in (
            TaskComplexity.MEDIUM,
            TaskComplexity.HIGH,
            TaskComplexity.CRITICAL,
        ):
            if TaskType.RESEARCH not in task_types:
                task_types.insert(0, TaskType.RESEARCH)
            if TaskType.ANALYSIS not in task_types:
                idx = task_types.index(TaskType.RESEARCH) + 1
                task_types.insert(idx, TaskType.ANALYSIS)

        # For HIGH / CRITICAL, include an architecture phase if absent.
        if complexity in (TaskComplexity.HIGH, TaskComplexity.CRITICAL):
            if TaskType.ARCHITECTURE not in task_types:
                idx = (
                    task_types.index(TaskType.ANALYSIS) + 1
                    if TaskType.ANALYSIS in task_types
                    else 0
                )
                task_types.insert(idx, TaskType.ARCHITECTURE)

        # Always end with validation if not explicitly present.
        if TaskType.VALIDATION not in task_types:
            task_types.append(TaskType.VALIDATION)

        # Expand implementation nodes for higher-complexity tasks.
        impl_count = self._implementation_count(complexity)

        for ttype in task_types:
            if ttype == TaskType.IMPLEMENTATION:
                # Fan-out: create multiple parallel implementation nodes.
                group_id = str(uuid4())
                for i in range(impl_count):
                    node = TaskNode(
                        title=f"Implementation task {i + 1}",
                        description=(
                            f"Implement part {i + 1}/{impl_count} of: {prompt[:120]}"
                        ),
                        task_type=TaskType.IMPLEMENTATION,
                        model_tier=ModelTier.STANDARD,
                        parallel_group=group_id,
                    )
                    nodes.append(node)
            else:
                tier = _TASK_TYPE_TO_TIER.get(ttype, ModelTier.STANDARD)
                node = TaskNode(
                    title=f"{ttype.value.capitalize()} task",
                    description=f"{ttype.value.capitalize()} phase for: {prompt[:120]}",
                    task_type=ttype,
                    model_tier=tier,
                )
                nodes.append(node)

        return nodes

    @staticmethod
    def _implementation_count(complexity: TaskComplexity) -> int:
        """Decide how many parallel implementation agents to spin up."""
        return {
            TaskComplexity.SIMPLE: 1,
            TaskComplexity.MEDIUM: 2,
            TaskComplexity.HIGH: 4,
            TaskComplexity.CRITICAL: 6,
        }.get(complexity, 1)

    def _assign_phases(self, nodes: List[TaskNode]) -> None:
        """Walk *nodes* in order and assign phase numbers + dependencies.

        Nodes in the same ``parallel_group`` share a phase and depend on the
        previous phase.  All other nodes form sequential steps.
        """
        if not nodes:
            return

        phase = 0
        i = 0
        while i < len(nodes):
            node = nodes[i]
            group = node.parallel_group

            if group is not None:
                # Collect all nodes in this parallel group.
                group_nodes = [n for n in nodes if n.parallel_group == group]
                prev_phase_nodes = [
                    n for n in nodes if n.phase == phase - 1
                ] if phase > 0 else []

                for gn in group_nodes:
                    gn.phase = phase
                    # Each parallel node depends on *all* nodes from the
                    # previous phase.
                    for prev in prev_phase_nodes:
                        gn.dependencies.add(prev.node_id)

                i += len(group_nodes)
            else:
                prev_phase_nodes = [
                    n for n in nodes if n.phase == phase - 1
                ] if phase > 0 else []
                node.phase = phase
                for prev in prev_phase_nodes:
                    node.dependencies.add(prev.node_id)
                i += 1

            phase += 1


# ---------------------------------------------------------------------------
# OrchestrationEngine
# ---------------------------------------------------------------------------


class OrchestrationEngine:
    """Top-level orchestrator that ties assessment, decomposition, and
    execution together.

    The engine walks the task graph phase-by-phase, spawns agents for
    each ready node, manages retries on failure, and emits progress
    events through the ``EventBus``.

    Parameters
    ----------
    event_bus:
        EventBus instance for lifecycle event emission.
    agent_adapter:
        Adapter responsible for creating and running agents.
    memory_system:
        Persistent memory layer for storing agent outputs.
    skill_loader:
        Loader for injecting skills/tools into agents.
    validation_engine:
        Engine used to validate implementation outputs.
    """

    MAX_RETRIES: int = 3

    def __init__(
        self,
        event_bus: EventBus,
        agent_adapter: "AgentAdapter",
        memory_system: "MemorySystem",
        skill_loader: "SkillLoader",
        validation_engine: "ValidationEngine",
    ) -> None:
        self._event_bus = event_bus
        self._agent_adapter = agent_adapter
        self._memory_system = memory_system
        self._skill_loader = skill_loader
        self._validation_engine = validation_engine

        self._assessor = ComplexityAssessor()
        self._decomposer = TaskDecomposer()

    # -- public API ----------------------------------------------------------

    async def execute_task(
        self,
        prompt: str,
        project_info: Optional[ProjectInfo] = None,
    ) -> TaskGraph:
        """Full lifecycle: assess, decompose, execute, validate, return.

        Parameters
        ----------
        prompt:
            The raw user request.
        project_info:
            Optional project metadata.

        Returns
        -------
        TaskGraph
            The completed (or partially-failed) task graph.
        """
        correlation_id = str(uuid4())

        # 1. Assess complexity.
        complexity = self._assessor.assess(prompt)
        logger.info(
            "Complexity assessed as %s for prompt: %.80s…",
            complexity.value,
            prompt,
        )

        # 2. Decompose into a task graph.
        graph = self._decomposer.decompose(prompt, complexity, project_info)

        # 3. Emit execution-started event.
        await self._event_bus.emit(
            EventType.EXECUTION_STARTED,
            data={
                "graph_id": graph.graph_id,
                "complexity": complexity.value,
                "total_nodes": graph.total_count,
                "total_phases": graph.total_phases,
                "prompt": prompt[:200],
            },
            source="orchestration_engine",
            correlation_id=correlation_id,
        )

        try:
            # 4. Execute the graph.
            await self.execute_graph(graph, correlation_id=correlation_id)

            # 5. Run validation on implementation outputs.
            await self._run_validation(graph, correlation_id=correlation_id)

        except Exception:
            logger.exception("Orchestration failed for graph %s", graph.graph_id)
        finally:
            graph.completed_at = datetime.utcnow()

            await self._event_bus.emit(
                EventType.EXECUTION_COMPLETED,
                data={
                    "graph_id": graph.graph_id,
                    "completed": graph.completed_count,
                    "failed": graph.failed_count,
                    "total": graph.total_count,
                    "progress_percent": graph.progress_percent,
                },
                source="orchestration_engine",
                correlation_id=correlation_id,
            )

        return graph

    async def execute_graph(
        self,
        graph: TaskGraph,
        *,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Walk the DAG phase-by-phase, executing ready nodes.

        Nodes within the same phase that share a ``parallel_group`` are
        executed concurrently; all others are awaited before advancing to
        the next phase.
        """
        for phase in range(graph.total_phases):
            phase_nodes = graph.get_nodes_by_phase(phase)
            if not phase_nodes:
                continue

            logger.info(
                "Executing phase %d/%d (%d nodes) for graph %s",
                phase + 1,
                graph.total_phases,
                len(phase_nodes),
                graph.graph_id,
            )

            await self._execute_phase(
                phase_nodes,
                graph,
                correlation_id=correlation_id,
            )

            # Emit progress after each phase.
            await self._event_bus.emit(
                EventType.AGENT_PROGRESS,
                data={
                    "graph_id": graph.graph_id,
                    "phase": phase,
                    "progress_percent": graph.progress_percent,
                    "completed": graph.completed_count,
                    "total": graph.total_count,
                },
                source="orchestration_engine",
                correlation_id=correlation_id,
            )

    # -- internal execution helpers ------------------------------------------

    async def _execute_phase(
        self,
        nodes: Sequence[TaskNode],
        graph: TaskGraph,
        *,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Execute a group of nodes that belong to the same phase.

        Nodes sharing a ``parallel_group`` are run concurrently; isolated
        nodes are also gathered in the same batch for maximum parallelism
        within a phase.
        """
        tasks = [
            self._execute_node(node, graph, correlation_id=correlation_id)
            for node in nodes
        ]
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _execute_node(
        self,
        node: TaskNode,
        graph: TaskGraph,
        *,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Execute a single ``TaskNode`` with full agent lifecycle.

        Steps:
        1. Mark the node as running.
        2. Emit AGENT_SPAWNED.
        3. Inject context from completed dependency nodes.
        4. Load skills for the agent.
        5. Call the agent adapter to run the task.
        6. Store the result in the memory system.
        7. Mark the node as completed (or failed with retry).
        8. Emit AGENT_COMPLETED or handle retry logic.
        """
        node.status = TaskStatus.RUNNING
        node.agent_status = AgentStatus.SPAWNING
        node.started_at = datetime.utcnow()
        agent_id = str(uuid4())
        node.agent_id = agent_id

        await self._event_bus.emit(
            EventType.AGENT_SPAWNED,
            data={
                "agent_id": agent_id,
                "node_id": node.node_id,
                "task_type": node.task_type.value,
                "model_tier": node.model_tier.value,
                "title": node.title,
            },
            source="orchestration_engine",
            correlation_id=correlation_id,
        )

        # Inject context from completed dependencies.
        dep_context: Dict[str, Any] = {}
        for dep_id in node.dependencies:
            dep_node = graph.nodes.get(dep_id)
            if dep_node and dep_node.result:
                dep_context[dep_id] = dep_node.result
        node.context["dependency_results"] = dep_context

        attempt = 0
        while attempt <= self.MAX_RETRIES:
            try:
                node.agent_status = AgentStatus.ACTIVE

                # Load any skills required for this task type.
                skills = await self._skill_loader.load_skills(node.task_type)
                node.context["skills"] = skills

                # Delegate to the agent adapter.
                result = await self._agent_adapter.execute(
                    agent_id=agent_id,
                    task_node=node,
                )

                # Store result in memory.
                await self._memory_system.store(
                    key=node.node_id,
                    data={
                        "agent_id": agent_id,
                        "task_type": node.task_type.value,
                        "result": result,
                    },
                )

                # Mark completed.
                graph.mark_completed(node.node_id, result)

                await self._event_bus.emit(
                    EventType.AGENT_COMPLETED,
                    data={
                        "agent_id": agent_id,
                        "node_id": node.node_id,
                        "status": "completed",
                        "duration_seconds": node.duration_seconds,
                    },
                    source="orchestration_engine",
                    correlation_id=correlation_id,
                )

                logger.info(
                    "Node %s completed (agent %s) in %.2fs",
                    node.node_id,
                    agent_id,
                    node.duration_seconds or 0,
                )
                return

            except Exception as exc:
                attempt += 1
                node.retry_count = attempt

                logger.warning(
                    "Node %s failed (attempt %d/%d): %s",
                    node.node_id,
                    attempt,
                    self.MAX_RETRIES + 1,
                    exc,
                )

                if attempt <= self.MAX_RETRIES:
                    node.status = TaskStatus.RETRYING
                    node.agent_status = AgentStatus.WAITING
                    # Exponential back-off: 1s, 2s, 4s.
                    await asyncio.sleep(2 ** (attempt - 1))
                else:
                    error_msg = f"Failed after {attempt} attempts: {exc}"
                    graph.mark_failed(node.node_id, error_msg)

                    await self._event_bus.emit(
                        EventType.AGENT_FAILED,
                        data={
                            "agent_id": agent_id,
                            "node_id": node.node_id,
                            "error": error_msg,
                            "retry_count": node.retry_count,
                        },
                        source="orchestration_engine",
                        correlation_id=correlation_id,
                    )

    async def _run_validation(
        self,
        graph: TaskGraph,
        *,
        correlation_id: Optional[str] = None,
    ) -> None:
        """Run validation on all completed implementation nodes."""
        impl_nodes = [
            n
            for n in graph.nodes.values()
            if n.task_type == TaskType.IMPLEMENTATION
            and n.status == TaskStatus.COMPLETED
        ]

        if not impl_nodes:
            return

        await self._event_bus.emit(
            EventType.VALIDATION_STARTED,
            data={
                "graph_id": graph.graph_id,
                "node_count": len(impl_nodes),
            },
            source="orchestration_engine",
            correlation_id=correlation_id,
        )

        for node in impl_nodes:
            try:
                validation_result = await self._validation_engine.validate(
                    node_id=node.node_id,
                    result=node.result,
                )
                node.context["validation"] = validation_result

                await self._event_bus.emit(
                    EventType.VALIDATION_RESULT,
                    data={
                        "graph_id": graph.graph_id,
                        "node_id": node.node_id,
                        "validation": validation_result,
                    },
                    source="orchestration_engine",
                    correlation_id=correlation_id,
                )

            except Exception as exc:
                logger.error(
                    "Validation failed for node %s: %s",
                    node.node_id,
                    exc,
                )
                await self._event_bus.emit(
                    EventType.VALIDATION_FAILED,
                    data={
                        "graph_id": graph.graph_id,
                        "node_id": node.node_id,
                        "error": str(exc),
                    },
                    source="orchestration_engine",
                    correlation_id=correlation_id,
                )
