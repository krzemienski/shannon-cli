"""
Agent Adapter for the TUI Agent Orchestration System.

Wraps the Claude Agent SDK for spawning and managing agents within the
Shannon TUI orchestration pipeline. Provides model-tier routing, streaming
result capture, and event-bus integration.

When the Claude Agent SDK is not installed, the adapter falls back to a
lightweight mock that returns placeholder results so the rest of the system
can still be developed and tested without a live SDK dependency.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shannon.communication.events import Event, EventBus, EventType
from shannon.tui.models import (
    AgentConfig,
    AgentState,
    AgentStatus,
    ContextItem,
    ModelConfig,
    ModelTier,
    TaskNode,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Claude Agent SDK import with graceful fallback
# ---------------------------------------------------------------------------

_SDK_AVAILABLE = False

try:
    import claude_agent_sdk  # type: ignore[import-untyped]

    _SDK_AVAILABLE = True
    logger.info("Claude Agent SDK loaded successfully")
except ImportError:
    claude_agent_sdk = None  # type: ignore[assignment]
    logger.warning(
        "claude_agent_sdk not installed -- AgentAdapter will use mock execution"
    )


# ---------------------------------------------------------------------------
# Default model registry
# ---------------------------------------------------------------------------

_DEFAULT_MODEL_REGISTRY: Dict[ModelTier, ModelConfig] = {
    ModelTier.COMPLEX: ModelConfig(
        model_id="claude-opus-4-6",
        max_tokens=16384,
        temperature=0.0,
        timeout_seconds=600,
    ),
    ModelTier.STANDARD: ModelConfig(
        model_id="claude-sonnet-4-6",
        max_tokens=16384,
        temperature=0.0,
        timeout_seconds=300,
    ),
    ModelTier.FAST: ModelConfig(
        model_id="claude-haiku-4-5-20251001",
        max_tokens=8192,
        temperature=0.0,
        timeout_seconds=120,
    ),
}


# ---------------------------------------------------------------------------
# AgentAdapter
# ---------------------------------------------------------------------------


class AgentAdapter:
    """Wraps the Claude Agent SDK to spawn, execute, and manage agents.

    The adapter translates orchestration-level ``AgentConfig`` / ``TaskNode``
    objects into SDK calls, streams results back, and publishes lifecycle
    events on the shared ``EventBus``.

    Parameters
    ----------
    model_registry:
        Mapping of ``ModelTier`` to ``ModelConfig`` controlling which model
        ID, token budget, and temperature are used for each tier.
    event_bus:
        The shared Shannon ``EventBus`` used for publishing agent lifecycle
        events (``AGENT_SPAWNED``, ``AGENT_PROGRESS``, ``AGENT_COMPLETED``,
        ``AGENT_FAILED``).
    """

    def __init__(
        self,
        model_registry: Dict[ModelTier, ModelConfig],
        event_bus: EventBus,
    ) -> None:
        self._model_registry = model_registry
        self._event_bus = event_bus
        self._active_agents: Dict[str, AgentState] = {}

        logger.info(
            "AgentAdapter initialised (sdk_available=%s, tiers=%s)",
            _SDK_AVAILABLE,
            list(self._model_registry.keys()),
        )

    # -- public API ---------------------------------------------------------

    async def spawn_agent(
        self,
        config: AgentConfig,
        task_node: TaskNode,
        context_items: List[ContextItem],
    ) -> AgentState:
        """Create an ``AgentState`` and register it as *spawning*.

        This does **not** execute the agent -- call :meth:`execute_agent`
        afterwards to begin the actual SDK query.

        Parameters
        ----------
        config:
            Agent configuration (model tier, tools, etc.).
        task_node:
            The task-graph node this agent is responsible for.
        context_items:
            Pre-selected context items to inject into the system prompt.

        Returns
        -------
        AgentState
            The newly created state with ``SPAWNING`` status.
        """
        state = AgentState(
            agent_id=config.agent_id,
            config=config,
            task_node_id=task_node.node_id,
            status=AgentStatus.SPAWNING,
            created_at=datetime.utcnow(),
        )

        self._active_agents[state.agent_id] = state

        await self._event_bus.emit(
            event_type=EventType.AGENT_SPAWNED,
            data={
                "agent_id": state.agent_id,
                "task_node_id": task_node.node_id,
                "task_title": task_node.title,
                "model_tier": config.model_tier.value,
            },
            source="agent_adapter",
            correlation_id=task_node.node_id,
        )

        logger.info(
            "Agent spawned: %s for task %s (%s)",
            state.agent_id,
            task_node.title,
            config.model_tier.value,
        )

        return state

    async def execute_agent(self, state: AgentState) -> AgentState:
        """Execute the agent via the Claude Agent SDK (or mock fallback).

        Builds a system prompt from the task node description and any
        context items attached to the agent, selects the appropriate model
        based on the config's model tier, and streams the SDK response.

        During streaming the method captures:

        * **ThinkingBlock** content -> ``state.thoughts``
        * **ToolUseBlock** content -> ``state.actions``
        * **TextBlock** content    -> ``state.text_output``

        Progress events are emitted periodically so the TUI can update its
        display in real time.

        Parameters
        ----------
        state:
            The ``AgentState`` returned by :meth:`spawn_agent`.

        Returns
        -------
        AgentState
            The same state object, mutated to reflect the final outcome
            (``COMPLETED`` or ``FAILED``).
        """
        if state.config is None:
            state.status = AgentStatus.FAILED
            state.error = "AgentState has no config attached"
            await self._emit_failed(state)
            return state

        state.status = AgentStatus.ACTIVE
        state.started_at = datetime.utcnow()

        # Retrieve the task node description from context if possible
        task_description = ""
        task_node_id = state.task_node_id or ""
        if state.config.metadata.get("task_description"):
            task_description = state.config.metadata["task_description"]

        # Build the system prompt
        context_items: List[ContextItem] = state.config.metadata.get(
            "context_items", []
        )
        task_node_stub = TaskNode(
            node_id=task_node_id,
            description=task_description,
            title=state.config.name,
        )
        system_prompt = self._build_system_prompt(task_node_stub, context_items)

        model_id = self._select_model(state.config.model_tier)

        try:
            if _SDK_AVAILABLE:
                state = await self._execute_with_sdk(
                    state, system_prompt, model_id
                )
            else:
                state = await self._execute_mock(state, system_prompt, model_id)

            # Mark completed
            state.status = AgentStatus.COMPLETED
            state.completed_at = datetime.utcnow()
            state.progress = 100.0
            state.result = {
                "thoughts": state.thoughts,
                "actions": state.actions,
                "text_output": state.text_output,
            }

            await self._event_bus.emit(
                event_type=EventType.AGENT_COMPLETED,
                data={
                    "agent_id": state.agent_id,
                    "task_node_id": state.task_node_id,
                    "duration_seconds": state.duration_seconds,
                    "tokens_in": state.tokens_in,
                    "tokens_out": state.tokens_out,
                },
                source="agent_adapter",
                correlation_id=state.task_node_id,
            )

            logger.info(
                "Agent completed: %s (%.1fs)",
                state.agent_id,
                state.duration_seconds or 0,
            )

        except Exception as exc:
            state.status = AgentStatus.FAILED
            state.error = str(exc)
            state.completed_at = datetime.utcnow()
            await self._emit_failed(state)
            logger.error(
                "Agent failed: %s -- %s", state.agent_id, exc, exc_info=True
            )

        return state

    # -- class method -------------------------------------------------------

    @classmethod
    def get_default_registry(cls) -> Dict[ModelTier, ModelConfig]:
        """Return the default model registry mapping tiers to model configs.

        Returns
        -------
        Dict[ModelTier, ModelConfig]
            A copy of the built-in defaults so callers can safely mutate it.
        """
        return dict(_DEFAULT_MODEL_REGISTRY)

    # -- internal helpers ---------------------------------------------------

    def _build_system_prompt(
        self,
        task: TaskNode,
        context: List[ContextItem],
    ) -> str:
        """Assemble the full system prompt from base instructions, context, and task.

        Parameters
        ----------
        task:
            The task node whose description forms the core instruction.
        context:
            Context items to inject between the base instructions and
            the task description.

        Returns
        -------
        str
            The assembled system prompt.
        """
        parts: List[str] = []

        # Base instructions
        parts.append(
            "You are an AI agent within the Shannon orchestration system. "
            "Follow the task instructions precisely. Report progress clearly. "
            "If you encounter an error, describe it in detail so recovery "
            "can be attempted."
        )

        # Context section
        if context:
            parts.append("\n--- Relevant Context ---")
            for item in context:
                content = item.content if isinstance(item, ContextItem) else str(item)
                parts.append(f"[{getattr(item, 'context_type', 'context')}] {content}")
            parts.append("--- End Context ---\n")

        # Task description
        if task.title:
            parts.append(f"## Task: {task.title}")
        if task.description:
            parts.append(task.description)

        return "\n\n".join(parts)

    def _select_model(self, tier: ModelTier) -> str:
        """Map a ``ModelTier`` to a concrete model ID string.

        Parameters
        ----------
        tier:
            The desired model tier.

        Returns
        -------
        str
            The model identifier string (e.g. ``"claude-sonnet-4-6"``).
        """
        config = self._model_registry.get(tier)
        if config is not None:
            return config.model_id

        # Fallback mapping when tier is not in the registry
        fallback: Dict[ModelTier, str] = {
            ModelTier.COMPLEX: "claude-opus-4-6",
            ModelTier.STANDARD: "claude-sonnet-4-6",
            ModelTier.FAST: "claude-haiku-4-5-20251001",
        }
        model_id = fallback.get(tier, "claude-sonnet-4-6")
        logger.warning(
            "Model tier %s not in registry, falling back to %s",
            tier.value,
            model_id,
        )
        return model_id

    # -- SDK execution ------------------------------------------------------

    async def _execute_with_sdk(
        self,
        state: AgentState,
        system_prompt: str,
        model_id: str,
    ) -> AgentState:
        """Run an agent via the real Claude Agent SDK.

        Streams the response and populates ``state.thoughts``,
        ``state.actions``, and ``state.text_output`` from the SDK's
        block types.
        """
        assert claude_agent_sdk is not None

        config = state.config
        assert config is not None

        model_config = self._model_registry.get(
            config.model_tier,
            ModelConfig(model_id=model_id),
        )

        try:
            response = claude_agent_sdk.query(
                model=model_id,
                system=system_prompt,
                max_tokens=model_config.max_tokens,
                temperature=model_config.temperature,
            )
        except Exception as exc:
            raise RuntimeError(
                f"claude_agent_sdk.query failed: {exc}"
            ) from exc

        # Process response blocks
        block_count = 0
        blocks = getattr(response, "content", [])
        total_blocks = len(blocks) if blocks else 1

        for block in blocks:
            block_count += 1
            block_type = getattr(block, "type", "")

            if block_type == "thinking":
                text = getattr(block, "thinking", "")
                if text:
                    state.thoughts.append(text)

            elif block_type == "tool_use":
                action = {
                    "tool": getattr(block, "name", "unknown"),
                    "input": getattr(block, "input", {}),
                    "id": getattr(block, "id", str(uuid4())),
                }
                state.actions.append(action)

            elif block_type == "text":
                text = getattr(block, "text", "")
                if text:
                    state.text_output.append(text)

            # Update progress
            state.progress = min(
                95.0, (block_count / total_blocks) * 95.0
            )

            await self._emit_progress(state)

        # Capture token usage if available
        usage = getattr(response, "usage", None)
        if usage:
            state.tokens_in = getattr(usage, "input_tokens", 0)
            state.tokens_out = getattr(usage, "output_tokens", 0)

        return state

    # -- mock execution -----------------------------------------------------

    async def _execute_mock(
        self,
        state: AgentState,
        system_prompt: str,
        model_id: str,
    ) -> AgentState:
        """Simulate agent execution when the SDK is not available.

        Produces placeholder thoughts, actions, and text so that the rest
        of the orchestration pipeline can be exercised end-to-end during
        development.
        """
        logger.info(
            "Mock-executing agent %s with model %s",
            state.agent_id,
            model_id,
        )

        # Simulate streaming delay
        steps = [
            ("thinking", "Analyzing the task requirements..."),
            ("thinking", "Planning implementation approach..."),
            ("action", "Searching codebase for relevant files"),
            ("text", "Based on my analysis, here is the implementation plan..."),
            ("action", "Applying code changes"),
            ("text", "Implementation complete. All changes applied successfully."),
        ]

        for i, (step_type, content) in enumerate(steps):
            await asyncio.sleep(0.05)  # Brief delay to simulate streaming

            if step_type == "thinking":
                state.thoughts.append(content)
            elif step_type == "action":
                state.actions.append({
                    "tool": "mock_tool",
                    "input": {"description": content},
                    "id": str(uuid4()),
                })
            elif step_type == "text":
                state.text_output.append(content)

            state.progress = ((i + 1) / len(steps)) * 95.0
            await self._emit_progress(state)

        # Simulated token counts
        prompt_tokens = len(system_prompt.split())
        state.tokens_in = prompt_tokens * 2  # rough estimate
        state.tokens_out = 500

        return state

    # -- event helpers ------------------------------------------------------

    async def _emit_progress(self, state: AgentState) -> None:
        """Emit an ``AGENT_PROGRESS`` event for the given state."""
        await self._event_bus.emit(
            event_type=EventType.AGENT_PROGRESS,
            data={
                "agent_id": state.agent_id,
                "task_node_id": state.task_node_id,
                "progress": state.progress,
                "thoughts_count": len(state.thoughts),
                "actions_count": len(state.actions),
                "text_segments": len(state.text_output),
            },
            source="agent_adapter",
            correlation_id=state.task_node_id,
        )

    async def _emit_failed(self, state: AgentState) -> None:
        """Emit an ``AGENT_FAILED`` event for the given state."""
        await self._event_bus.emit(
            event_type=EventType.AGENT_FAILED,
            data={
                "agent_id": state.agent_id,
                "task_node_id": state.task_node_id,
                "error": state.error,
                "duration_seconds": state.duration_seconds,
            },
            source="agent_adapter",
            correlation_id=state.task_node_id,
        )
