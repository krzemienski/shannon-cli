"""
TUI Screens for Agent Execution and Project Onboarding.

Provides two Textual Screen classes:
- ExecutionScreen: Real-time agent execution live view with task graph sidebar.
- OnboardingScreen: Brownfield project scanning and onboarding wizard.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.reactive import reactive
    from textual.screen import Screen
    from textual.widget import Widget
    from textual.widgets import (
        Footer,
        Header,
        Input,
        Label,
        ProgressBar,
        RichLog,
        Static,
    )

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

    # ------------------------------------------------------------------
    # Stub base classes so the module can be imported without Textual
    # ------------------------------------------------------------------
    class _StubMeta(type):
        """Metaclass that silently absorbs missing Textual attributes."""

        def __new__(mcs, name, bases, namespace, **kwargs):
            return super().__new__(mcs, name, bases, namespace)

    class Screen(metaclass=_StubMeta):  # type: ignore[no-redef]
        """Stub Screen base class when Textual is not installed."""

        BINDINGS: list = []
        CSS: str = ""

        def compose(self):  # type: ignore[override]
            yield from ()

        def on_mount(self) -> None: ...

        def set_interval(self, interval: float, callback, *, name: str = "") -> None: ...

    class Widget(metaclass=_StubMeta):  # type: ignore[no-redef]
        """Stub Widget base class."""

        def compose(self):
            yield from ()

    class ComposeResult:  # type: ignore[no-redef]
        """Stub ComposeResult type alias."""

    class Container(Widget): ...  # type: ignore[no-redef]
    class Horizontal(Widget): ...  # type: ignore[no-redef]
    class Vertical(Widget): ...  # type: ignore[no-redef]
    class ScrollableContainer(Widget): ...  # type: ignore[no-redef]
    class Static(Widget): ...  # type: ignore[no-redef]
    class Label(Widget): ...  # type: ignore[no-redef]
    class ProgressBar(Widget): ...  # type: ignore[no-redef]
    class RichLog(Widget):  # type: ignore[no-redef]
        def write(self, text: str) -> None: ...
        def clear(self) -> None: ...
    class Input(Widget): ...  # type: ignore[no-redef]
    class Footer(Widget): ...  # type: ignore[no-redef]
    class Header(Widget): ...  # type: ignore[no-redef]
    class Binding:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs): ...

    reactive = lambda default=None: default  # type: ignore[assignment,no-redef]


from shannon.tui.models import (
    AgentState,
    AgentStatus,
    TaskGraph,
    TaskNode,
    TaskStatus,
)


# ======================================================================
# Helper data containers
# ======================================================================


@dataclass
class _AgentOutputState:
    """Internal bookkeeping for one agent's streamed output."""

    agent_id: str = ""
    name: str = ""
    model_id: str = ""
    tools: List[str] = field(default_factory=list)
    thoughts: List[str] = field(default_factory=list)
    actions: List[str] = field(default_factory=list)
    text_lines: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    memory_entries: int = 0


# ======================================================================
# ExecutionScreen  (Screen 3: Agent Execution Live View)
# ======================================================================


class TaskGraphSidebar(Widget):
    """Left-panel widget that displays the task graph status by phase."""

    DEFAULT_CSS = """
    TaskGraphSidebar {
        width: 35;
        dock: left;
        border-right: solid $accent;
        padding: 1;
        background: $surface;
        overflow-y: auto;
    }
    TaskGraphSidebar .phase-label {
        color: $text-muted;
        text-style: bold;
        padding: 1 0 0 0;
    }
    TaskGraphSidebar .node-row {
        padding: 0 1;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._phases: Dict[int, List[Dict[str, Any]]] = {}

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Static("TASK GRAPH", classes="phase-label")

    # -- public API --

    def set_graph(self, graph: TaskGraph) -> None:
        """Populate from a TaskGraph model."""
        self._phases.clear()
        for node in graph.node_list:
            self._phases.setdefault(node.phase, []).append(
                {
                    "node_id": node.node_id,
                    "title": node.title,
                    "status": node.status.value,
                    "progress": 0.0,
                }
            )
        self._rebuild()

    def update_node(self, node_id: str, status: str, progress: float | None = None) -> None:
        """Update a single node's status/progress and redraw."""
        for nodes in self._phases.values():
            for node in nodes:
                if node["node_id"] == node_id:
                    node["status"] = status
                    if progress is not None:
                        node["progress"] = progress
                    break
        self._rebuild()

    # -- internal --

    _STATUS_ICONS = {
        "pending": "\u231b",       # hourglass
        "queued": "\u231b",
        "running": "\u25f7",       # spinner-like circle
        "completed": "\u2714",     # checkmark
        "failed": "\u2718",        # X
        "skipped": "\u2500",
        "retrying": "\u21bb",
    }

    def _rebuild(self) -> None:
        """Rebuild child widgets from current phase data."""
        if not TEXTUAL_AVAILABLE:
            return
        # Remove existing children and re-compose
        self.query("*").remove()
        for phase_num in sorted(self._phases):
            self.mount(Static(f"PHASE {phase_num + 1}", classes="phase-label"))
            for node in self._phases[phase_num]:
                icon = self._STATUS_ICONS.get(node["status"], "?")
                progress_str = ""
                if node["status"] == "running" and node.get("progress"):
                    progress_str = f" {node['progress']:.0f}%"
                line = f"  {icon} {node['title'][:24]}{progress_str}"
                self.mount(Static(line, classes="node-row"))


class AgentOutputPanel(Widget):
    """Right-panel widget showing focused agent's output stream."""

    DEFAULT_CSS = """
    AgentOutputPanel {
        padding: 1 2;
        overflow-y: auto;
    }
    AgentOutputPanel #agent-header {
        text-style: bold;
        color: $text;
        padding-bottom: 1;
    }
    AgentOutputPanel #agent-tools {
        color: $text-muted;
        padding-bottom: 1;
    }
    AgentOutputPanel #agent-files {
        color: $success;
    }
    AgentOutputPanel #agent-memory {
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._state: _AgentOutputState = _AgentOutputState()

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Static("No agent focused", id="agent-header")
        yield Static("", id="agent-tools")
        yield RichLog(highlight=True, markup=True, id="agent-log")
        yield Static("", id="agent-files")
        yield Static("", id="agent-memory")

    # -- public API --

    def set_agent(self, state: _AgentOutputState) -> None:
        """Replace the displayed agent state entirely."""
        self._state = state
        self._refresh_header()
        self._refresh_log()
        self._refresh_footer()

    def append_thought(self, text: str) -> None:
        self._state.thoughts.append(text)
        self._write_to_log(f"[cyan]\U0001f9e0 {text}[/cyan]")

    def append_action(self, text: str) -> None:
        self._state.actions.append(text)
        self._write_to_log(f"[yellow]\U0001f527 {text}[/yellow]")

    def append_text(self, text: str) -> None:
        self._state.text_lines.append(text)
        self._write_to_log(text)

    def add_file_modified(self, path: str) -> None:
        if path not in self._state.files_modified:
            self._state.files_modified.append(path)
        self._refresh_footer()

    def set_memory_count(self, count: int) -> None:
        self._state.memory_entries = count
        self._refresh_footer()

    # -- internal --

    def _write_to_log(self, markup: str) -> None:
        if not TEXTUAL_AVAILABLE:
            return
        try:
            log_widget: RichLog = self.query_one("#agent-log", RichLog)  # type: ignore[assignment]
            log_widget.write(markup)
        except Exception:
            pass

    def _refresh_header(self) -> None:
        if not TEXTUAL_AVAILABLE:
            return
        try:
            header: Static = self.query_one("#agent-header", Static)  # type: ignore[assignment]
            header.update(
                f"Agent: {self._state.name}  |  Model: {self._state.model_id}"
            )
            tools_widget: Static = self.query_one("#agent-tools", Static)  # type: ignore[assignment]
            tools_widget.update(f"Tools: {', '.join(self._state.tools) or 'none'}")
        except Exception:
            pass

    def _refresh_log(self) -> None:
        if not TEXTUAL_AVAILABLE:
            return
        try:
            log_widget: RichLog = self.query_one("#agent-log", RichLog)  # type: ignore[assignment]
            log_widget.clear()
            for t in self._state.thoughts:
                log_widget.write(f"[cyan]\U0001f9e0 {t}[/cyan]")
            for a in self._state.actions:
                log_widget.write(f"[yellow]\U0001f527 {a}[/yellow]")
            for line in self._state.text_lines:
                log_widget.write(line)
        except Exception:
            pass

    def _refresh_footer(self) -> None:
        if not TEXTUAL_AVAILABLE:
            return
        try:
            files_widget: Static = self.query_one("#agent-files", Static)  # type: ignore[assignment]
            if self._state.files_modified:
                file_list = "\n".join(
                    f"  [green]{f}[/green]" for f in self._state.files_modified
                )
                files_widget.update(f"Files modified:\n{file_list}")
            else:
                files_widget.update("")
            mem_widget: Static = self.query_one("#agent-memory", Static)  # type: ignore[assignment]
            mem_widget.update(f"Memory entries created: {self._state.memory_entries}")
        except Exception:
            pass


class ExecutionScreen(Screen):
    """
    Screen 3: Agent Execution Live View.

    Displays real-time agent execution with a split layout:
    - Left sidebar (35 chars): Task graph with phase/node status.
    - Right panel: Focused agent output (thoughts, actions, text, files).
    - Bottom bar: Context utilization, active agents, elapsed time, controls.
    """

    BINDINGS = [
        Binding("1", "focus_agent_1", "Focus Agent 1", show=True),
        Binding("2", "focus_agent_2", "Focus Agent 2", show=True),
        Binding("3", "focus_agent_3", "Focus Agent 3", show=True),
        Binding("4", "focus_agent_4", "Focus Agent 4", show=True),
        Binding("5", "focus_agent_5", "Focus Agent 5", show=True),
        Binding("6", "focus_agent_6", "Focus Agent 6", show=True),
        Binding("7", "focus_agent_7", "Focus Agent 7", show=True),
        Binding("8", "focus_agent_8", "Focus Agent 8", show=True),
        Binding("9", "focus_agent_9", "Focus Agent 9", show=True),
        Binding("p", "pause", "Pause", show=True),
        Binding("s", "stop", "Stop", show=True),
        Binding("l", "full_log", "Full Log", show=True),
    ]

    CSS = """
    ExecutionScreen {
        layout: vertical;
    }
    ExecutionScreen #exec-body {
        layout: horizontal;
        height: 1fr;
    }
    ExecutionScreen #exec-output {
        width: 1fr;
    }
    ExecutionScreen #exec-status-bar {
        dock: bottom;
        height: 3;
        padding: 0 2;
        background: $boost;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        task_graph: TaskGraph | None = None,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._task_graph = task_graph
        self._agents: Dict[str, _AgentOutputState] = {}
        self._agent_order: List[str] = []
        self._focused_agent_id: str | None = None
        self._start_time: float = time.monotonic()
        self._paused: bool = False
        self._context_utilization: float = 0.0
        self._active_agent_count: int = 0

    # -- Compose --

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(show_clock=True)
        with Container(id="exec-body"):
            yield TaskGraphSidebar(id="exec-sidebar")
            yield AgentOutputPanel(id="exec-output")
        yield Static(
            "[1-9] Focus Agent  [P] Pause  [S] Stop  [L] Full Log",
            id="exec-status-bar",
        )

    def on_mount(self) -> None:
        """Initialize the screen after mount."""
        if self._task_graph is not None:
            sidebar = self.query_one("#exec-sidebar", TaskGraphSidebar)
            sidebar.set_graph(self._task_graph)
        self.set_interval(1.0, self._tick_timer, name="exec-timer")

    # -- Timer --

    def _tick_timer(self) -> None:
        """Update the bottom status bar every second."""
        if not TEXTUAL_AVAILABLE:
            return
        elapsed = time.monotonic() - self._start_time
        minutes, seconds = divmod(int(elapsed), 60)
        hours, minutes = divmod(minutes, 60)
        elapsed_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        ctx_pct = f"{self._context_utilization:.0f}%"
        status_text = (
            f"Context: {ctx_pct}  |  "
            f"Active agents: {self._active_agent_count}  |  "
            f"Elapsed: {elapsed_str}  |  "
            f"{'PAUSED' if self._paused else 'RUNNING'}"
            f"    [1-9] Focus Agent  [P] Pause  [S] Stop  [L] Full Log"
        )
        try:
            bar: Static = self.query_one("#exec-status-bar", Static)  # type: ignore[assignment]
            bar.update(status_text)
        except Exception:
            pass

    # -- Public API --

    def register_agent(
        self,
        agent_id: str,
        name: str = "",
        model_id: str = "",
        tools: List[str] | None = None,
    ) -> None:
        """Register an agent so it can receive output updates."""
        state = _AgentOutputState(
            agent_id=agent_id,
            name=name or agent_id[:12],
            model_id=model_id,
            tools=tools or [],
        )
        self._agents[agent_id] = state
        if agent_id not in self._agent_order:
            self._agent_order.append(agent_id)
        # Auto-focus the first registered agent
        if self._focused_agent_id is None:
            self.focus_agent(agent_id)

    def update_agent_output(
        self,
        agent_id: str,
        thought: str | None = None,
        action: str | None = None,
        text: str | None = None,
    ) -> None:
        """Stream output to the specified agent's state (and panel if focused)."""
        if agent_id not in self._agents:
            self.register_agent(agent_id)
        state = self._agents[agent_id]
        is_focused = agent_id == self._focused_agent_id
        if thought is not None:
            state.thoughts.append(thought)
            if is_focused:
                try:
                    panel = self.query_one("#exec-output", AgentOutputPanel)
                    panel.append_thought(thought)
                except Exception:
                    pass
        if action is not None:
            state.actions.append(action)
            if is_focused:
                try:
                    panel = self.query_one("#exec-output", AgentOutputPanel)
                    panel.append_action(action)
                except Exception:
                    pass
        if text is not None:
            state.text_lines.append(text)
            if is_focused:
                try:
                    panel = self.query_one("#exec-output", AgentOutputPanel)
                    panel.append_text(text)
                except Exception:
                    pass

    def update_node_status(
        self, node_id: str, status: str, progress: float | None = None
    ) -> None:
        """Update a node's status in the task graph sidebar."""
        try:
            sidebar = self.query_one("#exec-sidebar", TaskGraphSidebar)
            sidebar.update_node(node_id, status, progress)
        except Exception:
            pass

    def focus_agent(self, agent_id: str) -> None:
        """Switch the right panel to display the given agent's output."""
        if agent_id not in self._agents:
            return
        self._focused_agent_id = agent_id
        try:
            panel = self.query_one("#exec-output", AgentOutputPanel)
            panel.set_agent(self._agents[agent_id])
        except Exception:
            pass

    def set_context_utilization(self, pct: float) -> None:
        """Set the context window utilization percentage (0-100)."""
        self._context_utilization = pct

    def set_active_agent_count(self, count: int) -> None:
        """Set the number of currently active agents."""
        self._active_agent_count = count

    # -- Key bindings --

    def _focus_by_index(self, idx: int) -> None:
        """Focus the agent at the given 0-based index."""
        if 0 <= idx < len(self._agent_order):
            self.focus_agent(self._agent_order[idx])

    def action_focus_agent_1(self) -> None:
        self._focus_by_index(0)

    def action_focus_agent_2(self) -> None:
        self._focus_by_index(1)

    def action_focus_agent_3(self) -> None:
        self._focus_by_index(2)

    def action_focus_agent_4(self) -> None:
        self._focus_by_index(3)

    def action_focus_agent_5(self) -> None:
        self._focus_by_index(4)

    def action_focus_agent_6(self) -> None:
        self._focus_by_index(5)

    def action_focus_agent_7(self) -> None:
        self._focus_by_index(6)

    def action_focus_agent_8(self) -> None:
        self._focus_by_index(7)

    def action_focus_agent_9(self) -> None:
        self._focus_by_index(8)

    def action_pause(self) -> None:
        """Toggle paused state."""
        self._paused = not self._paused

    def action_stop(self) -> None:
        """Request stop (dismiss the screen)."""
        self.dismiss(result={"action": "stop"})

    def action_full_log(self) -> None:
        """Placeholder for full-log view."""
        self.dismiss(result={"action": "full_log"})


# ======================================================================
# OnboardingScreen  (Screen 4: Brownfield Project Onboarding)
# ======================================================================


class DetectedStackPanel(Widget):
    """Displays detected languages, frameworks, and build tools."""

    DEFAULT_CSS = """
    DetectedStackPanel {
        height: auto;
        padding: 1 2;
        border: solid $accent;
        margin: 1 0;
    }
    DetectedStackPanel .stack-title {
        text-style: bold;
        padding-bottom: 1;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._languages: Dict[str, float] = {}
        self._frameworks: List[str] = []
        self._build_tools: List[str] = []

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Static("Detected Stack", classes="stack-title")
        yield Static("Scanning...", id="stack-content")

    def update_stack(
        self,
        languages: Dict[str, float],
        frameworks: List[str],
        build_tools: List[str],
    ) -> None:
        """Refresh the displayed stack information."""
        self._languages = languages
        self._frameworks = frameworks
        self._build_tools = build_tools
        if not TEXTUAL_AVAILABLE:
            return
        lines: List[str] = []
        if languages:
            lines.append("[bold]Languages:[/bold]")
            for lang, pct in sorted(languages.items(), key=lambda x: -x[1]):
                bar_len = int(pct / 5)
                bar = "\u2588" * bar_len
                lines.append(f"  {lang:<14} {bar} {pct:.1f}%")
        if frameworks:
            lines.append("[bold]Frameworks:[/bold]")
            for fw in frameworks:
                lines.append(f"  \u2022 {fw}")
        if build_tools:
            lines.append("[bold]Build Tools:[/bold]")
            for bt in build_tools:
                lines.append(f"  \u2022 {bt}")
        try:
            content: Static = self.query_one("#stack-content", Static)  # type: ignore[assignment]
            content.update("\n".join(lines) if lines else "No stack detected yet.")
        except Exception:
            pass


class ContextBuildingPanel(Widget):
    """Shows progress of context-building indices."""

    DEFAULT_CSS = """
    ContextBuildingPanel {
        height: auto;
        padding: 1 2;
        border: solid $accent;
        margin: 1 0;
    }
    ContextBuildingPanel .cb-title {
        text-style: bold;
        padding-bottom: 1;
    }
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._indices: Dict[str, float] = {
            "L3 Vector Index": 0.0,
            "AST Index": 0.0,
            "Dependency Graph": 0.0,
            "Architecture Map": 0.0,
        }

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Static("Context Building", classes="cb-title")
        yield Static("", id="cb-content")

    def update_index(self, name: str, pct: float) -> None:
        """Update one index's progress percentage."""
        self._indices[name] = pct
        self._refresh()

    def update_all(self, values: Dict[str, float]) -> None:
        """Bulk-update multiple indices."""
        self._indices.update(values)
        self._refresh()

    def _refresh(self) -> None:
        if not TEXTUAL_AVAILABLE:
            return
        lines: List[str] = []
        for name, pct in self._indices.items():
            filled = int(pct / 5)
            empty = 20 - filled
            bar = f"[green]{'|' * filled}[/green]{'.' * empty}"
            lines.append(f"  {name:<20} [{bar}] {pct:.0f}%")
        try:
            content: Static = self.query_one("#cb-content", Static)  # type: ignore[assignment]
            content.update("\n".join(lines))
        except Exception:
            pass


class OnboardingScreen(Screen):
    """
    Screen 4: Brownfield Project Onboarding.

    Guides the user through scanning and analysing an existing project:
    - Path input at top.
    - Scanning progress bar with file counts.
    - Detected stack panel (languages, frameworks, build tools).
    - Context building progress (vector index, AST, dependency graph, arch map).
    - Key findings panel (scrollable).
    """

    BINDINGS = [
        Binding("v", "view_tree", "View Tree", show=True),
        Binding("d", "dep_graph", "Dep Graph", show=True),
        Binding("escape", "go_back", "Back", show=True),
    ]

    CSS = """
    OnboardingScreen {
        layout: vertical;
    }
    OnboardingScreen #onb-path-row {
        height: 3;
        padding: 1 2;
    }
    OnboardingScreen #onb-path-input {
        width: 1fr;
    }
    OnboardingScreen #onb-scan-progress-row {
        height: 3;
        padding: 0 2;
    }
    OnboardingScreen #onb-scan-bar {
        width: 1fr;
    }
    OnboardingScreen #onb-scan-label {
        width: auto;
        min-width: 30;
        padding-left: 1;
        color: $text-muted;
    }
    OnboardingScreen #onb-body {
        height: 1fr;
        layout: horizontal;
    }
    OnboardingScreen #onb-left {
        width: 1fr;
        padding: 0 1;
    }
    OnboardingScreen #onb-findings {
        width: 1fr;
        border: solid $accent;
        padding: 1 2;
        margin: 1 0;
    }
    OnboardingScreen #findings-title {
        text-style: bold;
        padding-bottom: 1;
    }
    OnboardingScreen #onb-footer {
        dock: bottom;
        height: 3;
        padding: 0 2;
        background: $boost;
        color: $text-muted;
    }
    """

    def __init__(
        self,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name=name, id=id, classes=classes)
        self._scan_total: int = 0
        self._scan_current: int = 0
        self._current_file: str = ""
        self._findings: List[str] = []

    # -- Compose --

    def compose(self) -> ComposeResult:  # type: ignore[override]
        yield Header(show_clock=True)
        with Horizontal(id="onb-path-row"):
            yield Static("Project path: ", id="onb-path-label")
            yield Input(
                placeholder="Enter project root path...",
                id="onb-path-input",
            )
        with Horizontal(id="onb-scan-progress-row"):
            yield ProgressBar(total=100, show_percentage=True, id="onb-scan-bar")
            yield Static("0 / 0 files", id="onb-scan-label")
        with Horizontal(id="onb-body"):
            with Vertical(id="onb-left"):
                yield DetectedStackPanel(id="onb-stack")
                yield ContextBuildingPanel(id="onb-context")
            with Vertical(id="onb-findings"):
                yield Static("Key Findings", id="findings-title")
                yield RichLog(
                    highlight=True,
                    markup=True,
                    id="findings-log",
                )
        yield Static(
            "[V] View Tree  [D] Dep Graph  [Esc] Back",
            id="onb-footer",
        )

    def on_mount(self) -> None:
        """Called after the screen is mounted."""

    # -- Input handling --

    def on_input_submitted(self, event: Any) -> None:
        """Handle Enter in the path input field."""
        if not TEXTUAL_AVAILABLE:
            return
        try:
            input_widget: Input = self.query_one("#onb-path-input", Input)  # type: ignore[assignment]
            path = input_widget.value.strip()
            if path:
                self.start_scan(path)
        except Exception:
            pass

    # -- Public API --

    def start_scan(self, project_path: str) -> None:
        """Begin scanning the given project path.

        This sets the input value and resets progress. Actual scanning logic
        should be driven externally by calling ``update_progress``,
        ``add_finding``, and ``update_stack_detection`` as results arrive.
        """
        if not TEXTUAL_AVAILABLE:
            return
        try:
            input_widget: Input = self.query_one("#onb-path-input", Input)  # type: ignore[assignment]
            input_widget.value = project_path
        except Exception:
            pass
        self._scan_current = 0
        self._scan_total = 0
        self._findings.clear()
        try:
            log_widget: RichLog = self.query_one("#findings-log", RichLog)  # type: ignore[assignment]
            log_widget.clear()
        except Exception:
            pass

    def update_progress(self, current: int, total: int, current_file: str) -> None:
        """Update the scanning progress bar and file counter."""
        self._scan_current = current
        self._scan_total = total
        self._current_file = current_file
        if not TEXTUAL_AVAILABLE:
            return
        try:
            bar: ProgressBar = self.query_one("#onb-scan-bar", ProgressBar)  # type: ignore[assignment]
            bar.total = total if total > 0 else 100
            bar.progress = current
        except Exception:
            pass
        try:
            label: Static = self.query_one("#onb-scan-label", Static)  # type: ignore[assignment]
            short_file = current_file
            if len(short_file) > 40:
                short_file = "..." + short_file[-37:]
            label.update(f"{current} / {total} files  {short_file}")
        except Exception:
            pass

    def add_finding(self, finding: str) -> None:
        """Append a discovery to the key findings panel."""
        self._findings.append(finding)
        if not TEXTUAL_AVAILABLE:
            return
        try:
            log_widget: RichLog = self.query_one("#findings-log", RichLog)  # type: ignore[assignment]
            log_widget.write(f"\u2022 {finding}")
        except Exception:
            pass

    def update_stack_detection(
        self,
        languages: Dict[str, float],
        frameworks: List[str],
        build_tools: List[str],
    ) -> None:
        """Update the detected stack panel with scan results."""
        if not TEXTUAL_AVAILABLE:
            return
        try:
            panel: DetectedStackPanel = self.query_one("#onb-stack", DetectedStackPanel)  # type: ignore[assignment]
            panel.update_stack(languages, frameworks, build_tools)
        except Exception:
            pass

    def update_context_building(self, values: Dict[str, float]) -> None:
        """Update context building index progress percentages."""
        if not TEXTUAL_AVAILABLE:
            return
        try:
            panel: ContextBuildingPanel = self.query_one("#onb-context", ContextBuildingPanel)  # type: ignore[assignment]
            panel.update_all(values)
        except Exception:
            pass

    # -- Key bindings --

    def action_view_tree(self) -> None:
        """Placeholder: switch to project tree view."""
        self.dismiss(result={"action": "view_tree"})

    def action_dep_graph(self) -> None:
        """Placeholder: switch to dependency graph view."""
        self.dismiss(result={"action": "dep_graph"})

    def action_go_back(self) -> None:
        """Return to the previous screen."""
        self.dismiss(result={"action": "back"})
