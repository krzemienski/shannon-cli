"""
Dashboard and Prompt screens for the TUI Agent Orchestration System.

Provides the main home dashboard (DashboardScreen) and the task input
and decomposition view (PromptScreen) built on Textual widgets.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from shannon.tui.models import (
    ModelTier,
    TaskComplexity,
    TaskGraph,
    TaskNode,
    TaskStatus,
)

# ---------------------------------------------------------------------------
# Textual imports with graceful fallback
# ---------------------------------------------------------------------------

try:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical
    from textual.screen import Screen
    from textual.widgets import Button, Footer, Header, Static, TextArea

    _TEXTUAL_AVAILABLE = True
except ImportError:  # pragma: no cover

    _TEXTUAL_AVAILABLE = False

    # Minimal stub so the module can still be imported without textual.
    class _StubMeta(type):
        """Metaclass that silently absorbs unknown attribute access."""

        def __getattr__(cls, name: str) -> Any:
            return lambda *a, **kw: None

    class Screen(metaclass=_StubMeta):  # type: ignore[no-redef]
        """Stub Screen base class when Textual is not installed."""

        BINDINGS: list = []

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

        def compose(self) -> list:
            return []

        def push_screen(self, screen: Any) -> None:
            pass

        def pop_screen(self) -> None:
            pass

    class ComposeResult:  # type: ignore[no-redef]
        pass

    class Binding:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Container:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Horizontal(Container):  # type: ignore[no-redef]
        pass

    class Vertical(Container):  # type: ignore[no-redef]
        pass

    class Static:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.renderable = args[0] if args else ""

        def update(self, content: str) -> None:
            self.renderable = content

    class TextArea:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.text = ""

    class Button:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Header:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Footer:  # type: ignore[no-redef]
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STATUS_ICONS: Dict[str, str] = {
    TaskStatus.PENDING.value: "\u25cb",     # circle outline
    TaskStatus.QUEUED.value: "\u25d4",      # half circle
    TaskStatus.RUNNING.value: "\u25b6",     # play
    TaskStatus.COMPLETED.value: "\u2714",   # check mark
    TaskStatus.FAILED.value: "\u2718",      # cross mark
    TaskStatus.SKIPPED.value: "\u2500",     # dash
    TaskStatus.RETRYING.value: "\u21bb",    # loop
}


def _bar(label: str, fraction: float, width: int = 30) -> str:
    """Render a labelled utilization bar using block characters.

    ``fraction`` is clamped to [0.0, 1.0].  The resulting string looks like::

        L1 Hot   [████████████░░░░░░░░░░░░░░░░░░]  40%
    """
    fraction = max(0.0, min(1.0, fraction))
    filled = int(fraction * width)
    empty = width - filled
    pct = int(fraction * 100)
    filled_bar = "\u2588" * filled
    empty_bar = "\u2591" * empty
    return f"{label:<9} [{filled_bar}{empty_bar}] {pct:>3}%"


def _format_duration(seconds: float) -> str:
    """Format a duration in seconds to a human-friendly string."""
    td = timedelta(seconds=int(seconds))
    parts = []
    hours, remainder = divmod(int(td.total_seconds()), 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    parts.append(f"{secs}s")
    return " ".join(parts)


# ===================================================================
# Screen 1: Home Dashboard
# ===================================================================


class DashboardScreen(Screen):
    """Main home dashboard showing project, context, and task overview."""

    BINDINGS = [
        Binding("p", "switch_screen('prompt')", "Prompt", show=True),
        Binding("o", "switch_screen('onboard')", "Onboard", show=True),
        Binding("m", "switch_screen('memory')", "Memory", show=True),
        Binding("s", "switch_screen('settings')", "Settings", show=True),
        Binding("t", "switch_screen('tasks')", "Tasks", show=True),
        Binding("a", "switch_screen('agents')", "Agents", show=True),
        Binding("v", "switch_screen('validate')", "Validate", show=True),
        Binding("l", "switch_screen('logs')", "Logs", show=True),
    ]

    def __init__(
        self,
        app_state: Dict[str, Any],
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.app_state = app_state

    # -- data helpers -------------------------------------------------------

    def _project_name(self) -> str:
        info = self.app_state.get("project_info")
        if info is None:
            return "No project loaded"
        if hasattr(info, "root_path"):
            return info.root_path.rstrip("/").rsplit("/", 1)[-1]
        if isinstance(info, dict):
            return info.get("root_path", "unknown").rstrip("/").rsplit("/", 1)[-1]
        return str(info)

    def _detected_stack(self) -> str:
        info = self.app_state.get("project_info")
        parts: List[str] = []
        if info is None:
            return "N/A"
        for attr in ("language", "framework", "build_system"):
            val = getattr(info, attr, None) if hasattr(info, attr) else (
                info.get(attr) if isinstance(info, dict) else None
            )
            if val:
                parts.append(str(val))
        return " / ".join(parts) if parts else "N/A"

    def _primary_model(self) -> str:
        return str(self.app_state.get("primary_model", "claude-sonnet-4-20250514"))

    def _session_id(self) -> str:
        return str(self.app_state.get("session_id", "N/A"))

    def _session_duration(self) -> str:
        start = self.app_state.get("session_start_time")
        if start is None:
            return "0s"
        if isinstance(start, datetime):
            elapsed = (datetime.utcnow() - start).total_seconds()
        elif isinstance(start, (int, float)):
            elapsed = float(start)
        else:
            return "0s"
        return _format_duration(elapsed)

    # -- compose ------------------------------------------------------------

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header()

        # Title / session ID
        yield Static(
            f"[bold]Shannon Agent Orchestrator v2.0[/bold]  "
            f"Session: {self._session_id()}",
            id="dashboard-title",
        )

        # Project info section
        with Vertical(id="project-info", classes="section"):
            yield Static("[bold underline]Project[/bold underline]")
            yield Static(f"  Name  : {self._project_name()}")
            yield Static(f"  Stack : {self._detected_stack()}")
            yield Static(f"  Model : {self._primary_model()}")

        # Context utilization bars
        ctx = self.app_state.get("context_utilization", {})
        with Vertical(id="context-section", classes="section"):
            yield Static("[bold underline]Context Utilization[/bold underline]")
            yield Static(_bar("L1 Hot", ctx.get("l1", 0.0)))
            yield Static(_bar("L2 Warm", ctx.get("l2", 0.0)))
            yield Static(_bar("L3 Cold", ctx.get("l3", 0.0)))
            yield Static(_bar("L4 Arch", ctx.get("l4", 0.0)))

        # Stats row
        memory_count = self.app_state.get("memory_count", 0)
        task_history: List[Dict[str, Any]] = self.app_state.get("task_history", [])
        completed_tasks = sum(
            1 for t in task_history if t.get("status") == TaskStatus.COMPLETED.value
        )
        active_skills = self.app_state.get("active_skills_count", 0)
        active_plugins = self.app_state.get("active_plugins_count", 0)

        with Horizontal(id="stats-row", classes="section"):
            yield Static(f"  Memory entries: {memory_count}")
            yield Static(f"  Session: {self._session_duration()}")
            yield Static(f"  Tasks completed: {completed_tasks}")
            yield Static(f"  Skills: {active_skills}  Plugins: {active_plugins}")

        # Recent tasks
        with Vertical(id="recent-tasks", classes="section"):
            yield Static("[bold underline]Recent Tasks[/bold underline]")
            recent = task_history[-5:] if task_history else []
            if not recent:
                yield Static("  No tasks yet.")
            else:
                for task in reversed(recent):
                    status_val = task.get("status", TaskStatus.PENDING.value)
                    icon = _STATUS_ICONS.get(status_val, "?")
                    title = task.get("title", "Untitled")
                    ts = task.get("created_at", "")
                    if isinstance(ts, datetime):
                        ts = ts.strftime("%H:%M:%S")
                    elif isinstance(ts, str) and ts:
                        try:
                            ts = datetime.fromisoformat(ts).strftime("%H:%M:%S")
                        except ValueError:
                            pass
                    yield Static(f"  {icon} {title:<50s} {ts}")

        yield Footer()

    # -- key actions --------------------------------------------------------

    def action_switch_screen(self, screen_name: str) -> None:
        """Handle navigation hotkeys by pushing the requested screen."""
        screen_map: Dict[str, type] = {
            "prompt": PromptScreen,
        }
        target_cls = screen_map.get(screen_name)
        if target_cls is not None:
            self.app.push_screen(target_cls(app_state=self.app_state))
        else:
            # For screens not yet implemented, attempt by name so that the
            # app-level screen registry can resolve it.
            try:
                self.app.push_screen(screen_name)
            except Exception:
                pass


# ===================================================================
# Screen 2: Task Input & Decomposition
# ===================================================================


class PromptScreen(Screen):
    """Prompt entry screen with task decomposition and DAG visualisation."""

    BINDINGS = [
        Binding("escape", "go_back", "Back to Dashboard", show=True),
        Binding("enter", "submit", "Execute", show=True, priority=True),
        Binding("e", "edit_plan", "Edit Plan", show=True),
    ]

    def __init__(
        self,
        app_state: Dict[str, Any],
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self.app_state = app_state
        self._current_graph: Optional[TaskGraph] = None

    # -- compose ------------------------------------------------------------

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header()

        yield Static(
            "[bold]Task Input & Decomposition[/bold]",
            id="prompt-title",
        )

        # Prompt input area
        with Vertical(id="prompt-input-section", classes="section"):
            yield Static("[bold underline]Prompt[/bold underline]")
            yield TextArea(id="prompt-input")

        with Horizontal(id="prompt-buttons"):
            yield Button("Execute", id="btn-execute", variant="primary")
            yield Button("Edit Plan", id="btn-edit-plan", variant="default")
            yield Button("Back", id="btn-back", variant="default")

        # Analysis section (populated after decomposition)
        with Vertical(id="analysis-section", classes="section"):
            yield Static("[bold underline]Analysis[/bold underline]")
            yield Static("  Complexity : --", id="analysis-complexity")
            yield Static("  Agents     : --", id="analysis-agents")
            yield Static("  Model Mix  : --", id="analysis-model-mix")

        # Task graph visualisation area
        with Vertical(id="task-graph-section", classes="section"):
            yield Static("[bold underline]Task Graph[/bold underline]")
            yield Static(
                "  Submit a prompt to view the task decomposition graph.",
                id="task-graph-content",
            )

        # Skills & plugins
        with Vertical(id="skills-section", classes="section"):
            yield Static("[bold underline]Activated Skills & Plugins[/bold underline]")
            yield Static("  --", id="skills-content")

        yield Footer()

    # -- key actions --------------------------------------------------------

    def action_go_back(self) -> None:
        """Return to the dashboard."""
        self.app.pop_screen()

    def action_submit(self) -> None:
        """Trigger task decomposition from the prompt text area."""
        self.on_submit()

    def action_edit_plan(self) -> None:
        """Focus the prompt input for editing the plan."""
        try:
            ta = self.query_one("#prompt-input", TextArea)
            ta.focus()
        except Exception:
            pass

    # -- public API ---------------------------------------------------------

    def on_submit(self) -> None:
        """Read the prompt text, trigger decomposition, and display results.

        In a fully wired system this would call the orchestration engine.
        Here we update the analysis section and delegate to
        :meth:`show_task_graph` if a graph is available.
        """
        try:
            ta = self.query_one("#prompt-input", TextArea)
            prompt_text = ta.text.strip()
        except Exception:
            prompt_text = ""

        if not prompt_text:
            return

        # Placeholder: in production the orchestration engine would return a
        # TaskGraph.  For now, we surface the prompt in the analysis section.
        try:
            self.query_one("#analysis-complexity", Static).update(
                f"  Complexity : {TaskComplexity.MEDIUM.value}"
            )
            self.query_one("#analysis-agents", Static).update(
                "  Agents     : 5-10 (estimated)"
            )
            self.query_one("#analysis-model-mix", Static).update(
                "  Model Mix  : fast=40% / standard=40% / complex=20%"
            )
        except Exception:
            pass

        if self._current_graph is not None:
            self.show_task_graph(self._current_graph)

    def show_task_graph(self, graph: TaskGraph) -> None:
        """Render a :class:`TaskGraph` as a text-based DAG in the graph section.

        The visualisation groups nodes by *phase*, shows parallel groups
        side-by-side, and uses arrows between phases to indicate
        sequential dependencies.

        Each node line looks like::

            [standard] Implement auth module   ✔
        """
        self._current_graph = graph

        lines: List[str] = []
        lines.append(
            f"  Prompt   : {graph.prompt[:80]}{'...' if len(graph.prompt) > 80 else ''}"
        )
        lines.append(
            f"  Progress : {graph.progress_percent:.0f}% "
            f"({graph.completed_count}/{graph.total_count})"
        )
        lines.append("")

        # Group nodes by phase
        phases: Dict[int, List[TaskNode]] = defaultdict(list)
        for node in graph.node_list:
            phases[node.phase].append(node)

        sorted_phases = sorted(phases.keys())

        for idx, phase_num in enumerate(sorted_phases):
            nodes = phases[phase_num]
            lines.append(f"  ── Phase {phase_num} ──")

            # Sub-group by parallel_group within the phase
            groups: Dict[Optional[str], List[TaskNode]] = defaultdict(list)
            for n in nodes:
                groups[n.parallel_group].append(n)

            for group_key, group_nodes in groups.items():
                if group_key is not None:
                    lines.append(f"    ┌─ parallel group: {group_key}")

                for node in group_nodes:
                    tier_label = node.model_tier.value
                    status_icon = _STATUS_ICONS.get(
                        node.status.value, "?"
                    )
                    prefix = "    │ " if group_key is not None else "    "
                    lines.append(
                        f"{prefix}[{tier_label}] {node.title:<45s} {status_icon}"
                    )

                if group_key is not None:
                    lines.append("    └─")

            # Arrow between phases
            if idx < len(sorted_phases) - 1:
                lines.append("        │")
                lines.append("        ▼")

        # Update skills/plugins display
        active_skills = self.app_state.get("active_skills_count", 0)
        active_plugins = self.app_state.get("active_plugins_count", 0)
        skill_names: List[str] = self.app_state.get("active_skills", [])
        plugin_names: List[str] = self.app_state.get("active_plugins", [])
        skills_text_parts: List[str] = []
        if skill_names:
            skills_text_parts.append(f"  Skills  ({active_skills}): {', '.join(skill_names)}")
        else:
            skills_text_parts.append(f"  Skills  : {active_skills} active")
        if plugin_names:
            skills_text_parts.append(f"  Plugins ({active_plugins}): {', '.join(plugin_names)}")
        else:
            skills_text_parts.append(f"  Plugins : {active_plugins} active")

        # Push rendered content into the widgets
        try:
            self.query_one("#task-graph-content", Static).update("\n".join(lines))
            self.query_one("#skills-content", Static).update(
                "\n".join(skills_text_parts)
            )
            self.query_one("#analysis-complexity", Static).update(
                f"  Complexity : {graph.complexity.value}"
            )
            self.query_one("#analysis-agents", Static).update(
                f"  Agents     : {graph.total_count}"
            )

            # Compute model mix percentages
            tier_counts: Dict[str, int] = defaultdict(int)
            for node in graph.node_list:
                tier_counts[node.model_tier.value] += 1
            total = max(graph.total_count, 1)
            mix_parts = [
                f"{tier}={count * 100 // total}%"
                for tier, count in sorted(tier_counts.items())
            ]
            self.query_one("#analysis-model-mix", Static).update(
                f"  Model Mix  : {' / '.join(mix_parts)}"
            )
        except Exception:
            pass

    # -- button handlers ----------------------------------------------------

    def on_button_pressed(self, event: Any) -> None:
        """Handle button clicks."""
        button_id = getattr(event, "button", event)
        bid = getattr(button_id, "id", None) if hasattr(button_id, "id") else None
        if bid == "btn-execute":
            self.on_submit()
        elif bid == "btn-edit-plan":
            self.action_edit_plan()
        elif bid == "btn-back":
            self.action_go_back()
