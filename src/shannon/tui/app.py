"""
Shannon TUI Agent Orchestration System - Main Application.

The central Textual application that wires together all screens,
the orchestration engine, memory system, agent adapter, validation
engine, skill loader, and project scanner into a unified TUI experience.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shannon.communication.events import EventBus, EventType, Event, get_event_bus
from shannon.tui.models import (
    AgentState,
    AgentStatus,
    ContextItem,
    MemoryEntry,
    MemoryType,
    ModelConfig,
    ModelTier,
    ProjectInfo,
    TaskComplexity,
    TaskGraph,
    TaskNode,
    TaskStatus,
)

logger = logging.getLogger(__name__)

# Try importing Textual — gracefully degrade if not installed
try:
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.screen import Screen
    from textual.widgets import (
        Footer,
        Header,
        Static,
    )

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False
    App = object
    Screen = object
    ComposeResult = Any


# ---------------------------------------------------------------------------
# Application State — shared across all screens
# ---------------------------------------------------------------------------


class AppState:
    """Centralised mutable state shared by every screen in the TUI."""

    def __init__(self) -> None:
        self.session_id: str = str(uuid4())[:8]
        self.session_start: datetime = datetime.utcnow()

        # Project
        self.project_info: Optional[ProjectInfo] = None
        self.project_path: Optional[str] = None

        # Task / Execution
        self.current_graph: Optional[TaskGraph] = None
        self.task_history: List[Dict[str, Any]] = []
        self.active_agents: Dict[str, AgentState] = {}
        self.focused_agent_id: Optional[str] = None

        # Memory & Context
        self.memories: List[MemoryEntry] = []
        self.context_utilization: Dict[str, float] = {
            "L1": 0.0,
            "L2": 0.0,
            "L3": 0.0,
            "L4": 0.0,
        }

        # Skills & Plugins
        self.active_skills: List[str] = []
        self.active_plugins: List[str] = []
        self.total_skills: int = 0
        self.total_plugins: int = 0

        # Settings
        self.models: Dict[str, ModelConfig] = {
            "complex": ModelConfig(model_id="claude-opus-4-6", max_tokens=16384),
            "standard": ModelConfig(model_id="claude-sonnet-4-6", max_tokens=16384),
            "fast": ModelConfig(model_id="claude-haiku-4-5-20251001", max_tokens=8192),
        }
        self.max_parallel_agents: int = 10
        self.max_validation_retries: int = 5
        self.auto_approve_writes: bool = True
        self.validation_required: bool = True  # locked

        # Logs
        self.log_entries: List[Dict[str, Any]] = []

        # Validation
        self.validation_results: List[Dict[str, Any]] = []

    @property
    def session_duration_str(self) -> str:
        """Human-readable session duration."""
        delta = datetime.utcnow() - self.session_start
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours > 0:
            return f"{hours}h {minutes:02d}m"
        return f"{minutes}m {seconds:02d}s"

    def add_log(
        self,
        source: str,
        message: str,
        level: str = "INFO",
        agent_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Append a log entry."""
        self.log_entries.append(
            {
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
                "source": source,
                "level": level,
                "message": message,
                "agent_id": agent_id,
                "data": data or {},
            }
        )

    def add_task_to_history(self, title: str, status: str) -> None:
        """Record a completed/failed task."""
        self.task_history.insert(
            0,
            {
                "title": title,
                "status": status,
                "timestamp": datetime.utcnow().strftime("%H:%M:%S"),
            },
        )


# ---------------------------------------------------------------------------
# Orchestration Controller — bridges TUI ↔ backend subsystems
# ---------------------------------------------------------------------------


class OrchestrationController:
    """
    Bridges the TUI application with the backend orchestration subsystems.

    Holds references to the orchestration engine, agent adapter, memory system,
    validation engine, skill loader, and project scanner.  Exposes high-level
    async methods that screens can call without knowing backend details.
    """

    def __init__(self, state: AppState, event_bus: EventBus) -> None:
        self.state = state
        self.event_bus = event_bus

        # Lazy-initialise subsystems to avoid circular imports
        self._engine = None
        self._adapter = None
        self._memory = None
        self._validator = None
        self._skills = None
        self._scanner = None

    # -- lazy properties ------------------------------------------------------

    @property
    def engine(self):
        if self._engine is None:
            from shannon.tui.orchestration_engine import OrchestrationEngine
            self._engine = OrchestrationEngine(
                event_bus=self.event_bus,
                agent_adapter=self.adapter,
                memory_system=self.memory,
                skill_loader=self.skills,
                validation_engine=self.validator,
            )
        return self._engine

    @property
    def adapter(self):
        if self._adapter is None:
            from shannon.tui.agent_adapter import AgentAdapter
            self._adapter = AgentAdapter(event_bus=self.event_bus)
        return self._adapter

    @property
    def memory(self):
        if self._memory is None:
            from shannon.tui.memory_system import MemorySystem
            self._memory = MemorySystem(
                session_id=self.state.session_id,
                event_bus=self.event_bus,
            )
        return self._memory

    @property
    def validator(self):
        if self._validator is None:
            from shannon.tui.validation_engine import ValidationEngine
            self._validator = ValidationEngine(event_bus=self.event_bus)
        return self._validator

    @property
    def skills(self):
        if self._skills is None:
            from shannon.tui.skill_loader import SkillLoader
            self._skills = SkillLoader()
        return self._skills

    @property
    def scanner(self):
        if self._scanner is None:
            from shannon.tui.project_scanner import ProjectScanner
            self._scanner = ProjectScanner(event_bus=self.event_bus)
        return self._scanner

    # -- high-level actions ---------------------------------------------------

    async def submit_task(self, prompt: str) -> TaskGraph:
        """Decompose and execute a task from a user prompt."""
        self.state.add_log("ORCH", f"Task received: {prompt!r}")

        graph = await self.engine.execute_task(
            prompt=prompt,
            project_info=self.state.project_info,
        )

        self.state.current_graph = graph
        status = "completed" if graph.is_complete and graph.failed_count == 0 else "failed"
        self.state.add_task_to_history(prompt[:60], status)
        return graph

    async def decompose_task(self, prompt: str) -> TaskGraph:
        """Decompose without executing — for preview in PromptScreen."""
        from shannon.tui.orchestration_engine import ComplexityAssessor, TaskDecomposer

        assessor = ComplexityAssessor()
        decomposer = TaskDecomposer()

        complexity = assessor.assess(prompt)
        graph = decomposer.decompose(prompt, complexity, self.state.project_info)

        self.state.current_graph = graph
        self.state.add_log("ORCH", f"Complexity: {complexity.value} — {graph.total_count} nodes")
        return graph

    async def onboard_project(self, project_path: str) -> ProjectInfo:
        """Scan and onboard a project."""
        self.state.add_log("ORCH", f"Onboarding project: {project_path}")
        info = await self.scanner.scan(project_path)
        self.state.project_info = info
        self.state.project_path = project_path
        self.state.context_utilization["L3"] = 100.0
        self.state.add_log("ORCH", f"Onboarding complete: {info.framework or 'unknown'} project")
        return info

    async def search_memories(self, query: str) -> List[MemoryEntry]:
        """Search memory system."""
        return await self.memory.search(query)

    async def create_memory(
        self, content: str, memory_type: MemoryType, tags: List[str]
    ) -> MemoryEntry:
        """Create a new memory entry."""
        entry = MemoryEntry(
            memory_type=memory_type,
            content=content,
            tags=tags,
        )
        await self.memory.store(entry)
        self.state.memories.append(entry)
        return entry


# ---------------------------------------------------------------------------
# Main TUI Application
# ---------------------------------------------------------------------------

if TEXTUAL_AVAILABLE:

    class ShannonTUI(App):
        """Shannon Agent Orchestration TUI — main Textual application."""

        TITLE = "Shannon Agent Orchestrator"
        SUB_TITLE = "TUI Agent Orchestration System v1.0"
        CSS_PATH = "app.tcss"

        BINDINGS = [
            Binding("d", "switch_screen('dashboard')", "Dashboard", show=True),
            Binding("p", "switch_screen('prompt')", "Prompt", show=True),
            Binding("o", "switch_screen('onboarding')", "Onboard", show=True),
            Binding("m", "switch_screen('memory')", "Memory", show=True),
            Binding("v", "switch_screen('validation')", "Validation", show=True),
            Binding("ctrl+s", "switch_screen('settings')", "Settings", show=True),
            Binding("l", "switch_screen('logs')", "Logs", show=True),
            Binding("q", "quit", "Quit", show=True),
        ]

        def __init__(self, project_path: Optional[str] = None, **kwargs):
            super().__init__(**kwargs)
            self.app_state = AppState()
            self.event_bus = get_event_bus()
            self.controller = OrchestrationController(self.app_state, self.event_bus)

            if project_path:
                self.app_state.project_path = project_path

            # Register event handlers for live updates
            self._setup_event_handlers()

        def _setup_event_handlers(self) -> None:
            """Wire event bus to TUI updates."""
            async def on_agent_spawned(event: Event):
                agent_data = event.data
                self.app_state.add_log(
                    "AGT",
                    f"Spawned: {agent_data.get('name', 'unknown')}",
                    agent_id=agent_data.get("agent_id"),
                )

            async def on_agent_completed(event: Event):
                agent_data = event.data
                self.app_state.add_log(
                    "AGT",
                    f"Completed: {agent_data.get('name', 'unknown')}",
                    agent_id=agent_data.get("agent_id"),
                )

            async def on_validation_result(event: Event):
                self.app_state.validation_results.append(event.data)
                status = event.data.get("status", "unknown")
                self.app_state.add_log("VALID", f"Validation: {status}")

            asyncio.get_event_loop().run_until_complete(
                self.event_bus.subscribe(EventType.AGENT_SPAWNED, on_agent_spawned)
            ) if asyncio.get_event_loop().is_running() else None
            asyncio.get_event_loop().run_until_complete(
                self.event_bus.subscribe(EventType.AGENT_COMPLETED, on_agent_completed)
            ) if asyncio.get_event_loop().is_running() else None

        def compose(self) -> ComposeResult:
            """Build the initial widget tree — starts on dashboard."""
            yield Header()
            yield Static(self._render_dashboard(), id="main-content")
            yield Footer()

        def on_mount(self) -> None:
            """Set up screens after mount."""
            self._install_screens()

        def _install_screens(self) -> None:
            """Lazily install all screen instances."""
            try:
                from shannon.tui.screens.dashboard import DashboardScreen, PromptScreen
                self.install_screen(
                    DashboardScreen(self.app_state, self.controller), name="dashboard"
                )
                self.install_screen(
                    PromptScreen(self.app_state, self.controller), name="prompt"
                )
            except ImportError:
                logger.warning("Dashboard/Prompt screens not available")

            try:
                from shannon.tui.screens.execution import ExecutionScreen, OnboardingScreen
                self.install_screen(
                    ExecutionScreen(self.app_state, self.controller), name="execution"
                )
                self.install_screen(
                    OnboardingScreen(self.app_state, self.controller), name="onboarding"
                )
            except ImportError:
                logger.warning("Execution/Onboarding screens not available")

            try:
                from shannon.tui.screens.panels import (
                    MemoryScreen,
                    ValidationScreen,
                    SettingsScreen,
                    LogScreen,
                )
                self.install_screen(
                    MemoryScreen(self.app_state, self.controller), name="memory"
                )
                self.install_screen(
                    ValidationScreen(self.app_state, self.controller), name="validation"
                )
                self.install_screen(
                    SettingsScreen(self.app_state, self.controller), name="settings"
                )
                self.install_screen(
                    LogScreen(self.app_state, self.controller), name="logs"
                )
            except ImportError:
                logger.warning("Panel screens not available")

        def action_switch_screen(self, screen_name: str) -> None:
            """Switch to a named screen."""
            try:
                self.push_screen(screen_name)
            except Exception as e:
                logger.error(f"Cannot switch to screen {screen_name}: {e}")

        def _render_dashboard(self) -> str:
            """Render a text-based dashboard as fallback content."""
            s = self.app_state
            lines = [
                "=" * 62,
                "  Shannon Agent Orchestrator v2.0",
                f"  Session: {s.session_id}  |  Duration: {s.session_duration_str}",
                "=" * 62,
                "",
                f"  Project: {s.project_path or '(none loaded)'}",
                f"  Stack:   {s.project_info.framework if s.project_info else 'N/A'}",
                "",
                "  Context Utilization:",
                f"    L1 Active:  {'█' * int(s.context_utilization['L1'] / 10)}{'░' * (10 - int(s.context_utilization['L1'] / 10))} {s.context_utilization['L1']:.0f}%",
                f"    L2 Session: {'█' * int(s.context_utilization['L2'] / 10)}{'░' * (10 - int(s.context_utilization['L2'] / 10))} {s.context_utilization['L2']:.0f}%",
                f"    L3 Project: {'█' * int(s.context_utilization['L3'] / 10)}{'░' * (10 - int(s.context_utilization['L3'] / 10))} {s.context_utilization['L3']:.0f}%",
                f"    L4 Global:  {'█' * int(s.context_utilization['L4'] / 10)}{'░' * (10 - int(s.context_utilization['L4'] / 10))} {s.context_utilization['L4']:.0f}%",
                "",
                f"  Memory: {len(s.memories)} entries  |  Tasks: {len(s.task_history)} complete",
                f"  Skills: {len(s.active_skills)}/{s.total_skills} active  |  Plugins: {len(s.active_plugins)}/{s.total_plugins} active",
                "",
                "  Recent Tasks:",
            ]
            for task in s.task_history[:5]:
                icon = "✅" if task["status"] == "completed" else "❌"
                lines.append(f"    {icon} {task['title']:<45} {task['timestamp']}")
            if not s.task_history:
                lines.append("    (no tasks yet)")
            lines.extend([
                "",
                "─" * 62,
                "  [P] Prompt  [O] Onboard  [M] Memory  [S] Settings",
                "  [V] Validate  [L] Logs  [Q] Quit",
                "─" * 62,
            ])
            return "\n".join(lines)

else:
    # Stub when Textual is not installed
    class ShannonTUI:  # type: ignore[no-redef]
        """Stub TUI for environments without Textual."""

        def __init__(self, project_path: Optional[str] = None, **kwargs):
            self.app_state = AppState()
            self.event_bus = get_event_bus()
            self.controller = OrchestrationController(self.app_state, self.event_bus)

        def run(self) -> None:
            print("Textual is not installed. Install with: pip install textual")
            print("Falling back to CLI mode.")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def run_tui(project_path: Optional[str] = None) -> None:
    """Launch the Shannon TUI Agent Orchestration System."""
    app = ShannonTUI(project_path=project_path)
    app.run()


if __name__ == "__main__":
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else None
    run_tui(project_path=path)
