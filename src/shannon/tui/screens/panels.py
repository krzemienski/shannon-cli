"""
TUI Screen panels for the Agent Orchestration System.

Provides four Screen classes:
  - MemoryScreen: Memory & Context Explorer (Screen 5)
  - ValidationScreen: Functional Validation Dashboard (Screen 6)
  - SettingsScreen: Settings & Configuration (Screen 7)
  - LogScreen: Full Log Viewer (Screen 8)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

try:
    from textual.app import ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
    from textual.screen import Screen
    from textual.widgets import (
        Button,
        Footer,
        Header,
        Input,
        RichLog,
        Select,
        Static,
        Switch,
    )

    TEXTUAL_AVAILABLE = True
except ImportError:
    TEXTUAL_AVAILABLE = False

    # Stub base classes so the module can be imported without Textual
    class _StubComposeResult:
        """Placeholder for ComposeResult when Textual is not installed."""
        pass

    ComposeResult = _StubComposeResult  # type: ignore[misc,assignment]

    class Binding:  # type: ignore[no-redef]
        """Stub Binding."""
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            pass

    class Screen:  # type: ignore[no-redef]
        """Stub Screen base class."""
        BINDINGS: list = []
        CSS: str = ""

        def compose(self) -> list:
            return []

        def push_screen(self, *a: Any, **kw: Any) -> None:
            pass

        def pop_screen(self, *a: Any, **kw: Any) -> None:
            pass

        def query_one(self, *a: Any, **kw: Any) -> Any:
            return None

        def query(self, *a: Any, **kw: Any) -> list:
            return []

    class Container:  # type: ignore[no-redef]
        pass

    class Horizontal:  # type: ignore[no-redef]
        pass

    class Vertical:  # type: ignore[no-redef]
        pass

    class ScrollableContainer:  # type: ignore[no-redef]
        pass

    class Static:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class Input:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class Button:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class RichLog:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

        def write(self, *a: Any, **kw: Any) -> None:
            pass

        def clear(self) -> None:
            pass

    class Select:  # type: ignore[no-redef]
        BLANK: str = ""
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class Switch:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class Header:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

    class Footer:  # type: ignore[no-redef]
        def __init__(self, *a: Any, **kw: Any) -> None:
            pass

from shannon.tui.models import (
    MemoryEntry,
    MemoryType,
    ModelTier,
    ValidationRun,
    ValidationStatus,
    ValidationStep,
    ValidatorType,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MEMORY_TYPE_COLORS: Dict[MemoryType, str] = {
    MemoryType.DECISION: "blue",
    MemoryType.INSIGHT: "green",
    MemoryType.ERROR_PATTERN: "red",
    MemoryType.CODE_PATTERN: "yellow",
    MemoryType.ARCHITECTURE: "purple",
    MemoryType.REQUIREMENT: "cyan",
    MemoryType.CONVERSATION: "white",
    MemoryType.SESSION_NOTE: "dim white",
}

MEMORY_TYPE_ICONS: Dict[MemoryType, str] = {
    MemoryType.DECISION: "\u25cf",       # filled circle
    MemoryType.INSIGHT: "\u2736",        # six-pointed star
    MemoryType.ERROR_PATTERN: "\u2718",  # heavy ballot X
    MemoryType.CODE_PATTERN: "\u2261",   # identical to
    MemoryType.ARCHITECTURE: "\u2302",   # house / arch
    MemoryType.REQUIREMENT: "\u25b6",    # right-pointing triangle
    MemoryType.CONVERSATION: "\u25cb",   # open circle
    MemoryType.SESSION_NOTE: "\u25a1",   # white square
}

VALIDATOR_ICONS: Dict[ValidatorType, str] = {
    ValidatorType.BROWSER: "\U0001f310",       # globe
    ValidatorType.CLI: "\u2328",               # keyboard
    ValidatorType.API: "\u21c4",               # right-left arrows
    ValidatorType.IOS_SIMULATOR: "\U0001f4f1", # mobile phone
}

STATUS_ICONS: Dict[ValidationStatus, str] = {
    ValidationStatus.PENDING: "\u25cb",   # open circle
    ValidationStatus.RUNNING: "\u25d4",   # circle quarter
    ValidationStatus.PASSED: "\u2714",    # check mark
    ValidationStatus.FAILED: "\u2718",    # heavy X
    ValidationStatus.SKIPPED: "\u2796",   # heavy minus
    ValidationStatus.ERROR: "\u26a0",     # warning sign
}

LOG_LEVEL_COLORS: Dict[str, str] = {
    "DEBUG": "dim white",
    "INFO": "green",
    "WARN": "yellow",
    "ERROR": "red",
}


# ===================================================================
# Screen 5: Memory & Context Explorer
# ===================================================================


class MemoryScreen(Screen):
    """Memory & Context Explorer screen.

    Displays searchable memory entries colour-coded by type alongside
    context-tier utilisation bars (L1-L4).
    """

    BINDINGS = [
        Binding("n", "new_memory", "New Memory", key_display="N"),
        Binding("d", "delete_memory", "Delete", key_display="D"),
        Binding("f", "focus_filter", "Filter", key_display="F"),
        Binding("escape", "go_back", "Back", key_display="Esc"),
    ]

    CSS = """
    MemoryScreen {
        layout: vertical;
    }

    #memory-search-bar {
        dock: top;
        height: 3;
        padding: 0 1;
    }

    #memory-content {
        height: 1fr;
    }

    #memory-list-container {
        height: 3fr;
        border: round $primary;
        padding: 0 1;
    }

    .memory-entry {
        height: 3;
        padding: 0 1;
        margin: 0 0 1 0;
    }

    .memory-icon {
        width: 3;
    }

    .memory-type-label {
        width: 16;
        color: $text-muted;
    }

    .memory-preview {
        width: 1fr;
    }

    .memory-time {
        width: 20;
        text-align: right;
        color: $text-muted;
    }

    .memory-source {
        width: 20;
        text-align: right;
        color: $text-muted;
    }

    #context-bars-panel {
        height: auto;
        max-height: 12;
        border: round $secondary;
        padding: 1;
    }

    .context-tier-row {
        height: 1;
        margin: 0 0 1 0;
    }

    .tier-label {
        width: 6;
    }

    .tier-bar {
        width: 1fr;
    }

    .tier-pct {
        width: 8;
        text-align: right;
    }
    """

    def __init__(
        self,
        memories: Optional[List[MemoryEntry]] = None,
        context_utilization: Optional[Dict[str, float]] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._memories: List[MemoryEntry] = memories or []
        self._filtered: List[MemoryEntry] = list(self._memories)
        self._context_util: Dict[str, float] = context_utilization or {
            "L1": 0.0,
            "L2": 0.0,
            "L3": 0.0,
            "L4": 0.0,
        }

    # -- compose --------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        with Container(id="memory-search-bar"):
            yield Input(
                placeholder="Search memories...",
                id="memory-search-input",
            )
        with Vertical(id="memory-content"):
            with ScrollableContainer(id="memory-list-container"):
                for entry in self._filtered:
                    yield self._make_memory_widget(entry)
                if not self._filtered:
                    yield Static(
                        "[dim]No memory entries to display.[/dim]",
                        id="memory-empty",
                    )
            with Container(id="context-bars-panel"):
                yield Static(
                    "[bold]Context Tier Utilization[/bold]",
                    id="context-bars-title",
                )
                for tier in ("L1", "L2", "L3", "L4"):
                    pct = self._context_util.get(tier, 0.0)
                    yield self._make_tier_bar(tier, pct)
        yield Footer()

    # -- helpers --------------------------------------------------------

    @staticmethod
    def _make_memory_widget(entry: MemoryEntry) -> Static:
        """Build a Static widget representing a single memory entry."""
        color = MEMORY_TYPE_COLORS.get(entry.memory_type, "white")
        icon = MEMORY_TYPE_ICONS.get(entry.memory_type, "\u25cf")
        preview = entry.content[:100].replace("\n", " ")
        if len(entry.content) > 100:
            preview += "\u2026"
        time_str = entry.created_at.strftime("%Y-%m-%d %H:%M")
        source = entry.source_task or "n/a"
        line = (
            f"[{color}]{icon}[/{color}]  "
            f"[{color} bold]{entry.memory_type.value:<15}[/{color} bold] "
            f"{preview:<102} "
            f"[dim]{time_str}[/dim]  "
            f"[dim]src: {source}[/dim]"
        )
        return Static(line, classes="memory-entry")

    @staticmethod
    def _make_tier_bar(tier: str, pct: float) -> Static:
        """Build a context-tier utilisation bar."""
        bar_width = 40
        filled = int(bar_width * pct / 100.0)
        empty = bar_width - filled
        bar_str = "\u2588" * filled + "\u2591" * empty
        if pct >= 90:
            color = "red"
        elif pct >= 70:
            color = "yellow"
        else:
            color = "green"
        return Static(
            f"  {tier}  [{color}]{bar_str}[/{color}]  {pct:5.1f}%",
            classes="context-tier-row",
        )

    # -- public API -----------------------------------------------------

    def search(self, query: str) -> None:
        """Filter displayed memories by *query* substring (case-insensitive)."""
        query_lower = query.lower()
        if not query_lower:
            self._filtered = list(self._memories)
        else:
            self._filtered = [
                m
                for m in self._memories
                if query_lower in m.content.lower()
                or query_lower in m.memory_type.value.lower()
                or query_lower in m.source_task.lower()
                or any(query_lower in tag.lower() for tag in m.tags)
            ]
        self._refresh_memory_list()

    def add_memory_display(self, entry: MemoryEntry) -> None:
        """Append a new MemoryEntry and refresh the list."""
        self._memories.append(entry)
        self._filtered.append(entry)
        self._refresh_memory_list()

    def refresh_context_bars(self, utilization: Dict[str, float]) -> None:
        """Update context tier utilization bars with new percentages."""
        self._context_util.update(utilization)
        try:
            panel = self.query_one("#context-bars-panel", Container)
            panel.remove_children()
            panel.mount(
                Static(
                    "[bold]Context Tier Utilization[/bold]",
                    id="context-bars-title",
                )
            )
            for tier in ("L1", "L2", "L3", "L4"):
                pct = self._context_util.get(tier, 0.0)
                panel.mount(self._make_tier_bar(tier, pct))
        except Exception:
            pass

    # -- internal -------------------------------------------------------

    def _refresh_memory_list(self) -> None:
        """Re-render the memory list area."""
        try:
            container = self.query_one(
                "#memory-list-container", ScrollableContainer
            )
            container.remove_children()
            if self._filtered:
                for entry in self._filtered:
                    container.mount(self._make_memory_widget(entry))
            else:
                container.mount(
                    Static(
                        "[dim]No matching memory entries.[/dim]",
                        id="memory-empty",
                    )
                )
        except Exception:
            pass

    # -- event handlers -------------------------------------------------

    if TEXTUAL_AVAILABLE:
        from textual.widgets import Input as _Input

        def on_input_submitted(self, event: _Input.Submitted) -> None:
            if event.input.id == "memory-search-input":
                self.search(event.value)

    def action_new_memory(self) -> None:
        """Placeholder: open new-memory dialog."""
        pass

    def action_delete_memory(self) -> None:
        """Placeholder: delete selected memory."""
        pass

    def action_focus_filter(self) -> None:
        """Focus the search input."""
        try:
            self.query_one("#memory-search-input", Input).focus()
        except Exception:
            pass

    def action_go_back(self) -> None:
        """Pop this screen."""
        try:
            self.app.pop_screen()
        except Exception:
            pass


# ===================================================================
# Screen 6: Functional Validation Dashboard
# ===================================================================


class ValidationScreen(Screen):
    """Functional Validation Dashboard.

    Shows validation run results with per-validator step details,
    retry history, and evidence counts.
    """

    BINDINGS = [
        Binding("r", "rerun", "Re-run", key_display="R"),
        Binding("d", "details", "Details", key_display="D"),
        Binding("escape", "go_back", "Back", key_display="Esc"),
    ]

    CSS = """
    ValidationScreen {
        layout: vertical;
    }

    #validation-task-header {
        dock: top;
        height: 3;
        padding: 0 1;
        background: $boost;
    }

    #validation-body {
        height: 1fr;
    }

    #validator-results-panel {
        height: 2fr;
        border: round $primary;
        padding: 1;
    }

    .validator-block {
        margin: 0 0 1 0;
    }

    .validator-header {
        height: 1;
        text-style: bold;
    }

    .step-row {
        height: 1;
        padding: 0 0 0 4;
    }

    #retry-history-panel {
        height: 1fr;
        border: round $warning;
        padding: 1;
    }

    .retry-entry {
        height: 2;
        padding: 0 1;
    }

    #evidence-summary {
        dock: bottom;
        height: 3;
        padding: 0 1;
        background: $surface;
    }
    """

    def __init__(
        self,
        task_name: str = "",
        validation_run: Optional[ValidationRun] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._task_name = task_name
        self._run = validation_run or ValidationRun()

    # -- compose --------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        yield Static(
            f"[bold]Validating:[/bold] {self._task_name or '(no task)'}  "
            f"  Status: {self._overall_status_markup()}",
            id="validation-task-header",
        )

        with Vertical(id="validation-body"):
            with ScrollableContainer(id="validator-results-panel"):
                yield Static(
                    "[bold underline]Validator Results[/bold underline]"
                )
                yield from self._compose_validator_results()

            with ScrollableContainer(id="retry-history-panel"):
                yield Static(
                    "[bold underline]Retry History[/bold underline]"
                )
                yield from self._compose_retry_history()

        yield Static(self._evidence_summary_text(), id="evidence-summary")
        yield Footer()

    # -- compose helpers ------------------------------------------------

    def _overall_status_markup(self) -> str:
        status = self._run.status
        if status == ValidationStatus.PASSED:
            return "[bold green]PASS[/bold green]"
        elif status in (ValidationStatus.FAILED, ValidationStatus.ERROR):
            return "[bold red]FAIL[/bold red]"
        elif status == ValidationStatus.RUNNING:
            return "[bold yellow]RUNNING[/bold yellow]"
        return f"[dim]{status.value.upper()}[/dim]"

    def _compose_validator_results(self):
        """Yield widgets for each validator group and its steps."""
        # Group steps by validator_type
        groups: Dict[ValidatorType, List[ValidationStep]] = {}
        for step in self._run.steps:
            groups.setdefault(step.validator_type, []).append(step)

        if not groups:
            yield Static("[dim]No validation steps recorded.[/dim]")
            return

        for vtype, steps in groups.items():
            icon = VALIDATOR_ICONS.get(vtype, "\u2022")
            vtype_label = vtype.value.replace("_", " ").title()
            # Determine overall pass/fail for this validator
            all_passed = all(
                s.status
                in (ValidationStatus.PASSED, ValidationStatus.SKIPPED)
                for s in steps
            )
            overall_tag = (
                "[bold green]PASS[/bold green]"
                if all_passed
                else "[bold red]FAIL[/bold red]"
            )
            yield Static(
                f"{icon}  [bold]{vtype_label}[/bold]  {overall_tag}",
                classes="validator-header",
            )
            for step in steps:
                s_icon = STATUS_ICONS.get(step.status, "\u2022")
                detail = ""
                if step.error:
                    detail = f" [red]{step.error}[/red]"
                elif step.output:
                    detail = f" [dim]{step.output[:60]}[/dim]"
                dur = (
                    f" ({step.duration_seconds:.1f}s)"
                    if step.duration_seconds is not None
                    else ""
                )
                yield Static(
                    f"    {s_icon}  {step.name or step.step_id}{dur}{detail}",
                    classes="step-row",
                )

    def _compose_retry_history(self):
        """Yield widgets for each retry attempt in the history."""
        if not self._run.retry_history:
            yield Static("[dim]No retries recorded.[/dim]")
            return
        for idx, attempt in enumerate(self._run.retry_history, start=1):
            reason = attempt.get("failure_reason", "unknown")
            fix = attempt.get("fix_applied", "n/a")
            yield Static(
                f"  Attempt {idx}: [red]{reason}[/red]  ->  Fix: {fix}",
                classes="retry-entry",
            )

    def _evidence_summary_text(self) -> str:
        screenshots = sum(
            1
            for s in self._run.steps
            if s.screenshot_path
        )
        http_traces = sum(
            1
            for s in self._run.steps
            if s.validator_type == ValidatorType.API
        )
        cli_logs = sum(
            1
            for s in self._run.steps
            if s.validator_type == ValidatorType.CLI and s.output
        )
        return (
            f"[bold]Evidence:[/bold]  "
            f"\U0001f4f8 Screenshots: {screenshots}   "
            f"\U0001f310 HTTP Traces: {http_traces}   "
            f"\U0001f4cb CLI Logs: {cli_logs}"
        )

    # -- actions --------------------------------------------------------

    def action_rerun(self) -> None:
        """Placeholder: re-run the current validation plan."""
        pass

    def action_details(self) -> None:
        """Placeholder: show expanded details for selected step."""
        pass

    def action_go_back(self) -> None:
        try:
            self.app.pop_screen()
        except Exception:
            pass


# ===================================================================
# Screen 7: Settings & Configuration
# ===================================================================


class SettingsScreen(Screen):
    """Settings & Configuration screen.

    Displays model tier configuration, orchestration settings,
    context tier limits, and skill/plugin counts.
    """

    BINDINGS = [
        Binding("m", "manage_skills", "Manage Skills", key_display="M"),
        Binding("p", "manage_plugins", "Manage Plugins", key_display="P"),
        Binding("escape", "go_back", "Back", key_display="Esc"),
    ]

    CSS = """
    SettingsScreen {
        layout: vertical;
    }

    .settings-section {
        border: round $primary;
        padding: 1;
        margin: 0 0 1 0;
    }

    .settings-section-title {
        text-style: bold underline;
        margin: 0 0 1 0;
    }

    .settings-row {
        height: 1;
        padding: 0 1;
    }

    .settings-label {
        width: 30;
        color: $text-muted;
    }

    .settings-value {
        width: 1fr;
    }
    """

    @dataclass
    class Config:
        """Bundled settings data passed into the screen."""

        # Models
        model_fast_id: str = "claude-3-5-haiku-latest"
        model_standard_id: str = "claude-sonnet-4-20250514"
        model_complex_id: str = "claude-opus-4-20250514"
        model_auto_update: bool = True

        # Orchestration
        max_parallel_agents: int = 10
        max_retries: int = 3
        auto_approve: bool = False

        # Context tiers
        l1_max_tokens: int = 8192
        l1_backend: str = "in-memory"
        l2_max_tokens: int = 32768
        l2_backend: str = "sqlite"
        l3_max_tokens: int = 131072
        l3_backend: str = "sqlite"
        l4_max_tokens: int = 524288
        l4_backend: str = "disk"

        # Skills / Plugins
        skills_active: int = 0
        skills_total: int = 0
        plugins_active: int = 0
        plugins_total: int = 0

    def __init__(
        self,
        config: Optional["SettingsScreen.Config"] = None,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._cfg = config or self.Config()

    # -- compose --------------------------------------------------------

    def compose(self) -> ComposeResult:
        cfg = self._cfg
        yield Header(show_clock=True)

        with ScrollableContainer():
            # -- Models section -----------------------------------------
            with Container(classes="settings-section"):
                yield Static(
                    "[bold underline]Models[/bold underline]",
                    classes="settings-section-title",
                )
                yield Static(
                    f"  {'Fast tier:':<28} {cfg.model_fast_id}",
                    classes="settings-row",
                )
                yield Static(
                    f"  {'Standard tier:':<28} {cfg.model_standard_id}",
                    classes="settings-row",
                )
                yield Static(
                    f"  {'Complex tier:':<28} {cfg.model_complex_id}",
                    classes="settings-row",
                )
                auto_str = (
                    "[green]enabled[/green]"
                    if cfg.model_auto_update
                    else "[red]disabled[/red]"
                )
                yield Static(
                    f"  {'Auto-update:':<28} {auto_str}",
                    classes="settings-row",
                )

            # -- Orchestration section ----------------------------------
            with Container(classes="settings-section"):
                yield Static(
                    "[bold underline]Orchestration[/bold underline]",
                    classes="settings-section-title",
                )
                yield Static(
                    f"  {'Max parallel agents:':<28} {cfg.max_parallel_agents}",
                    classes="settings-row",
                )
                yield Static(
                    f"  {'Max retries:':<28} {cfg.max_retries}",
                    classes="settings-row",
                )
                approve_str = (
                    "[green]enabled[/green]"
                    if cfg.auto_approve
                    else "[yellow]disabled[/yellow]"
                )
                yield Static(
                    f"  {'Auto-approve:':<28} {approve_str}",
                    classes="settings-row",
                )

            # -- Context section ----------------------------------------
            with Container(classes="settings-section"):
                yield Static(
                    "[bold underline]Context Tiers[/bold underline]",
                    classes="settings-section-title",
                )
                for tier, tokens, backend in [
                    ("L1", cfg.l1_max_tokens, cfg.l1_backend),
                    ("L2", cfg.l2_max_tokens, cfg.l2_backend),
                    ("L3", cfg.l3_max_tokens, cfg.l3_backend),
                    ("L4", cfg.l4_max_tokens, cfg.l4_backend),
                ]:
                    yield Static(
                        f"  {tier + ':':<6} max_tokens={tokens:<10} "
                        f"backend={backend}",
                        classes="settings-row",
                    )

            # -- Skills / Plugins section -------------------------------
            with Container(classes="settings-section"):
                yield Static(
                    "[bold underline]Skills & Plugins[/bold underline]",
                    classes="settings-section-title",
                )
                yield Static(
                    f"  {'Skills:':<28} "
                    f"{cfg.skills_active} active / {cfg.skills_total} total",
                    classes="settings-row",
                )
                yield Static(
                    f"  {'Plugins:':<28} "
                    f"{cfg.plugins_active} active / {cfg.plugins_total} total",
                    classes="settings-row",
                )

        yield Footer()

    # -- actions --------------------------------------------------------

    def action_manage_skills(self) -> None:
        """Placeholder: open skill management dialog."""
        pass

    def action_manage_plugins(self) -> None:
        """Placeholder: open plugin management dialog."""
        pass

    def action_go_back(self) -> None:
        try:
            self.app.pop_screen()
        except Exception:
            pass


# ===================================================================
# Screen 8: Full Log Viewer
# ===================================================================


@dataclass
class _LogEntry:
    """Internal representation of a single log line."""

    timestamp: datetime
    source: str
    level: str
    message: str
    agent_id: Optional[str] = None


class LogScreen(Screen):
    """Full Log Viewer screen.

    Provides filtered, searchable, exportable log output using a
    ``RichLog`` widget with colour-coded entries.
    """

    BINDINGS = [
        Binding("s", "search_logs", "Search", key_display="S"),
        Binding("e", "export_logs", "Export", key_display="E"),
        Binding("c", "clear_logs", "Clear", key_display="C"),
        Binding("escape", "go_back", "Back", key_display="Esc"),
    ]

    CSS = """
    LogScreen {
        layout: vertical;
    }

    #log-filter-row {
        dock: top;
        height: 3;
        padding: 0 1;
    }

    #log-filter-row Horizontal {
        height: 3;
    }

    #log-source-select {
        width: 20;
        margin: 0 1 0 0;
    }

    #log-level-select {
        width: 20;
        margin: 0 1 0 0;
    }

    #log-search-input {
        width: 1fr;
        margin: 0 1 0 0;
    }

    #log-autoscroll-label {
        width: 16;
        content-align: center middle;
    }

    #log-autoscroll-switch {
        width: 8;
    }

    #log-display {
        height: 1fr;
        border: round $primary;
    }
    """

    # Source / level filter options
    SOURCE_OPTIONS = [
        ("ALL", "ALL"),
        ("ORCH", "ORCH"),
        ("AGT", "AGT"),
        ("MEM", "MEM"),
        ("SKILL", "SKILL"),
        ("VALID", "VALID"),
    ]

    LEVEL_OPTIONS = [
        ("ALL", "ALL"),
        ("DEBUG", "DEBUG"),
        ("INFO", "INFO"),
        ("WARN", "WARN"),
        ("ERROR", "ERROR"),
    ]

    def __init__(
        self,
        name: Optional[str] = None,
        id: Optional[str] = None,
    ) -> None:
        super().__init__(name=name, id=id)
        self._entries: List[_LogEntry] = []
        self._source_filter: Optional[str] = None
        self._level_filter: Optional[str] = None
        self._search_query: str = ""
        self._auto_scroll: bool = True

    # -- compose --------------------------------------------------------

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)

        with Container(id="log-filter-row"):
            with Horizontal():
                yield Select(
                    options=[(label, value) for label, value in self.SOURCE_OPTIONS],
                    value="ALL",
                    id="log-source-select",
                    allow_blank=False,
                )
                yield Select(
                    options=[(label, value) for label, value in self.LEVEL_OPTIONS],
                    value="ALL",
                    id="log-level-select",
                    allow_blank=False,
                )
                yield Input(
                    placeholder="Search logs...",
                    id="log-search-input",
                )
                yield Static("Auto-scroll:", id="log-autoscroll-label")
                yield Switch(value=True, id="log-autoscroll-switch")

        yield RichLog(
            highlight=True,
            markup=True,
            wrap=True,
            id="log-display",
        )
        yield Footer()

    # -- public API -----------------------------------------------------

    def add_log(
        self,
        timestamp: datetime,
        source: str,
        level: str,
        message: str,
        agent_id: Optional[str] = None,
    ) -> None:
        """Append a log entry and render it if it passes current filters."""
        entry = _LogEntry(
            timestamp=timestamp,
            source=source,
            level=level.upper(),
            message=message,
            agent_id=agent_id,
        )
        self._entries.append(entry)
        if self._entry_matches(entry):
            self._render_entry(entry)

    def filter_logs(
        self,
        source: Optional[str] = None,
        level: Optional[str] = None,
    ) -> None:
        """Re-filter the displayed logs by *source* and/or *level*."""
        self._source_filter = source if source and source != "ALL" else None
        self._level_filter = level if level and level != "ALL" else None
        self._redisplay()

    def search_logs(self, query: str) -> None:
        """Filter displayed logs by a search *query* substring."""
        self._search_query = query.lower()
        self._redisplay()

    def export_logs(self, path: str) -> None:
        """Write all currently-displayed log entries to a file at *path*."""
        matching = [e for e in self._entries if self._entry_matches(e)]
        try:
            with open(path, "w") as fh:
                for entry in matching:
                    ts = entry.timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                    agent_tag = f" agent={entry.agent_id}" if entry.agent_id else ""
                    fh.write(
                        f"{ts} [{entry.source}] {entry.level}: "
                        f"{entry.message}{agent_tag}\n"
                    )
        except OSError:
            pass

    # -- internal -------------------------------------------------------

    def _entry_matches(self, entry: _LogEntry) -> bool:
        """Return True if *entry* passes the active filters."""
        if self._source_filter and entry.source != self._source_filter:
            return False
        if self._level_filter and entry.level != self._level_filter:
            return False
        if self._search_query and self._search_query not in entry.message.lower():
            return False
        return True

    def _render_entry(self, entry: _LogEntry) -> None:
        """Write a single entry to the RichLog widget."""
        try:
            log_widget = self.query_one("#log-display", RichLog)
        except Exception:
            return
        ts = entry.timestamp.strftime("%H:%M:%S.%f")[:-3]
        color = LOG_LEVEL_COLORS.get(entry.level, "white")
        agent_tag = f" [dim]agent={entry.agent_id}[/dim]" if entry.agent_id else ""
        line = (
            f"[dim]{ts}[/dim] "
            f"[bold cyan]\\[{entry.source}][/bold cyan] "
            f"[{color}]{entry.message}[/{color}]"
            f"{agent_tag}"
        )
        log_widget.write(line)
        if self._auto_scroll:
            log_widget.scroll_end(animate=False)

    def _redisplay(self) -> None:
        """Clear and re-render all matching entries."""
        try:
            log_widget = self.query_one("#log-display", RichLog)
        except Exception:
            return
        log_widget.clear()
        for entry in self._entries:
            if self._entry_matches(entry):
                self._render_entry(entry)

    # -- event handlers -------------------------------------------------

    if TEXTUAL_AVAILABLE:
        from textual.widgets import Select as _Select, Switch as _Switch, Input as _Input

        def on_select_changed(self, event: _Select.Changed) -> None:
            select_id = event.select.id
            value = str(event.value) if event.value is not None else "ALL"
            if select_id == "log-source-select":
                self._source_filter = value if value != "ALL" else None
                self._redisplay()
            elif select_id == "log-level-select":
                self._level_filter = value if value != "ALL" else None
                self._redisplay()

        def on_switch_changed(self, event: _Switch.Changed) -> None:
            if event.switch.id == "log-autoscroll-switch":
                self._auto_scroll = event.value

        def on_input_submitted(self, event: _Input.Submitted) -> None:
            if event.input.id == "log-search-input":
                self.search_logs(event.value)

    # -- actions --------------------------------------------------------

    def action_search_logs(self) -> None:
        """Focus the search input."""
        try:
            self.query_one("#log-search-input", Input).focus()
        except Exception:
            pass

    def action_export_logs(self) -> None:
        """Placeholder: prompt for export path."""
        pass

    def action_clear_logs(self) -> None:
        """Clear all logs from the display and internal store."""
        self._entries.clear()
        try:
            self.query_one("#log-display", RichLog).clear()
        except Exception:
            pass

    def action_go_back(self) -> None:
        try:
            self.app.pop_screen()
        except Exception:
            pass
