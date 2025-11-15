"""Live Metrics Dashboard for Shannon CLI V3.0+

V3.1 Integration: This module now wraps InteractiveDashboard for backwards compatibility
while providing enhanced 4-layer navigation when agents/context are available.

Backwards Compatible Behavior:
- With only MetricsCollector: Simple 2-layer view (V3.0 behavior)
- With AgentStateTracker: Full 4-layer interactive TUI (V3.1 behavior)

Architecture:
    V3.0: MetricsCollector → LiveDashboard → Rich.Live → Terminal
    V3.1: All Managers → InteractiveDashboard → 4 Layers → Terminal

Design Decision:
    - Automatic upgrade: If agents/context available, use V3.1
    - Graceful fallback: If not, use V3.0 simple view
    - Same API: No breaking changes for existing code
"""

from typing import Optional, Callable
from collections import deque
from datetime import datetime
import asyncio

from rich.console import Console, RenderableType
from rich.layout import Layout
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.live import Live
from rich.text import Text
from rich.table import Table

from shannon.metrics.collector import MetricsCollector, MetricsSnapshot
from shannon.metrics.keyboard import KeyboardHandler, Key


class LiveDashboard:
    """
    Two-layer live metrics dashboard

    Displays real-time metrics from MetricsCollector with keyboard control.

    Usage:
        collector = MetricsCollector()
        dashboard = LiveDashboard(collector)

        # Run in context manager
        with dashboard:
            # Dashboard updates at 4 Hz automatically
            # Keyboard controls work
            await long_running_operation()

    Layer 1 (default):
        ┌─ Shannon: spec-analysis ──┐
        │ ▓▓▓▓▓▓░░░░ 60% (5/8 dims) │
        │ $0.12 | 8.2K | 45s        │
        │ Press ↵ for streaming     │
        └────────────────────────────┘

    Layer 2 (expanded):
        - Full screen layout
        - Progress bar at top
        - Streaming output (last 100 messages)
        - Completed stages list
        - Live metrics table
        - Keyboard controls

    Keyboard Events:
        - Enter: toggle_expand()
        - Esc: collapse()
        - q: request_quit()
        - p: request_pause()
    """

    def __init__(
        self,
        collector: MetricsCollector,
        console: Optional[Console] = None,
        refresh_per_second: int = 4,
        buffer_size: int = 100,
        agents=None,  # V3.1: AgentStateTracker
        context=None,  # V3.1: ContextManager
        session=None  # V3.1: SessionManager
    ):
        """
        Initialize live dashboard with message streaming

        Args:
            collector: MetricsCollector instance to read from
            console: Rich console (creates default if None)
            refresh_per_second: UI refresh rate (default: 4 Hz)
            buffer_size: Max streaming messages to buffer
            agents: (V3.1) AgentStateTracker for multi-agent support
            context: (V3.1) ContextManager for context visibility
            session: (V3.1) SessionManager for session tracking
        """
        self.collector = collector
        self.console = console or Console()
        self.refresh_per_second = refresh_per_second
        self.buffer_size = buffer_size

        # V3.1: Check if we should use InteractiveDashboard
        self._use_v31 = agents is not None
        self._v31_dashboard = None

        if self._use_v31:
            # Use V3.1 InteractiveDashboard
            try:
                from shannon.ui.dashboard_v31 import InteractiveDashboard
                self._v31_dashboard = InteractiveDashboard(
                    metrics=collector,
                    agents=agents,
                    context=context,
                    session=session,
                    console=console,
                    refresh_per_second=refresh_per_second
                )
            except Exception as e:
                # Fallback to V3.0 if V3.1 fails
                import logging
                logging.warning(f"Failed to initialize V3.1 dashboard, using V3.0: {e}")
                self._use_v31 = False

        # V3.0 components (fallback or when no agents)
        self.expanded = False
        self.streaming_buffer: deque[str] = deque(maxlen=buffer_size)
        self.keyboard = KeyboardHandler()
        self.quit_requested = False
        self.pause_requested = False
        self._live: Optional[Live] = None
        self._progress: Optional[Progress] = None
        self._last_snapshot: Optional[MetricsSnapshot] = None

    def __enter__(self):
        """Start dashboard in context manager"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop dashboard in context manager"""
        self.stop()
        return False

    def start(self) -> None:
        """
        Start dashboard rendering

        V3.1: Delegates to InteractiveDashboard if available
        V3.0: Uses simple LiveDashboard
        """
        if self._use_v31 and self._v31_dashboard:
            # Use V3.1 interactive dashboard
            self._v31_dashboard.start()
            # Sync quit flags
            self.quit_requested = self._v31_dashboard.quit_requested
        else:
            # V3.0 fallback
            self.keyboard.setup_nonblocking()
            self._live = Live(
                self.render(),
                console=self.console,
                refresh_per_second=self.refresh_per_second,
                transient=False
            )
            self._live.start()

    def stop(self) -> None:
        """
        Stop dashboard rendering

        V3.1: Delegates to InteractiveDashboard if available
        V3.0: Cleans up simple dashboard
        """
        if self._use_v31 and self._v31_dashboard:
            # Stop V3.1 dashboard
            self._v31_dashboard.stop()
            # Sync quit flag
            self.quit_requested = self._v31_dashboard.quit_requested
        else:
            # V3.0 cleanup
            if self._live:
                self._live.stop()
                self._live = None
            self.keyboard.restore_terminal()

    def update(self, streaming_message: Optional[str] = None) -> None:
        """
        Update dashboard state

        V3.1: Delegates to InteractiveDashboard.update()
        V3.0: Updates simple dashboard

        Args:
            streaming_message: New message to add to buffer (optional)
        """
        if self._use_v31 and self._v31_dashboard:
            # V3.1: Use interactive dashboard update
            self._v31_dashboard.update()
            # Sync quit flag
            self.quit_requested = self._v31_dashboard.quit_requested
        else:
            # V3.0: Traditional update
            if streaming_message:
                self.streaming_buffer.append(streaming_message)
            self._last_snapshot = self.collector.get_snapshot()
            self._handle_keyboard()
            if self._live:
                self._live.update(self.render())

    def render(self) -> RenderableType:
        """
        Render appropriate view based on state

        Returns:
            Panel (compact) or Layout (detailed)
        """
        # Get current snapshot
        snapshot = self._last_snapshot or self.collector.get_snapshot()

        if self.expanded:
            return self._create_detailed_layout(snapshot)
        else:
            return self._create_compact_layout(snapshot)

    def _create_compact_layout(self, snapshot: MetricsSnapshot) -> Panel:
        """
        Create OPERATIONAL TELEMETRY compact view

        Shows WHAT is running, WHERE we are, WHAT we're waiting for

        Args:
            snapshot: Current operational state and metrics

        Returns:
            Panel with live operational display
        """
        lines = []

        # Line 1: Current stage/operation
        stage_display = snapshot.current_stage if snapshot.current_stage else "Initializing"
        lines.append(f"[bold]{snapshot.current_operation}[/bold] - {stage_display}")

        # Line 2: Progress bar with stage count
        progress_chars = 10
        filled = int(snapshot.progress * progress_chars)
        bar = '▓' * filled + '░' * (progress_chars - filled)

        stage_info = ""
        if snapshot.total_stages > 0:
            completed = len(snapshot.completed_stages)
            stage_info = f" ({completed}/{snapshot.total_stages} stages)"

        lines.append(f"{bar} {snapshot.progress:.0%}{stage_info}")

        # Line 3: Operational state - WHAT we're doing/waiting for
        if snapshot.waiting_for:
            # WAITING state - show what we're blocked on
            wait_time = ""
            if snapshot.last_activity_time:
                wait_seconds = (datetime.now() - snapshot.last_activity_time).total_seconds()
                wait_time = f" ({wait_seconds:.0f}s...)"

            lines.append(f"[yellow]⏳ {snapshot.waiting_for}{wait_time}[/yellow]")

        elif snapshot.agent_status == "ACTIVE" and snapshot.last_activity:
            # ACTIVE state - show recent activity
            lines.append(f"[green]⚙[/green]  {snapshot.last_activity}")

        elif snapshot.is_complete:
            lines.append("[green]✅ Complete[/green]")

        elif snapshot.has_error:
            lines.append(f"[red]✗ Error: {snapshot.error_message}[/red]")

        else:
            lines.append("[dim]Processing...[/dim]")

        # Line 4: Metrics
        cost_str = f"${snapshot.cost_total:.2f}"
        tokens_k = snapshot.tokens_total / 1000
        tokens_str = f"{tokens_k:.1f}K" if tokens_k > 0 else "0"
        duration_str = f"{snapshot.duration_seconds:.0f}s" if snapshot.duration_seconds > 0 else "0s"

        lines.append(f"{cost_str} | {tokens_str} | {duration_str} | {snapshot.message_count} msgs")

        # Line 5: Controls
        lines.append("[dim][↵] Details | [Esc] Hide | [q] Quit[/dim]")

        content = "\n".join(lines)

        # Border color based on status
        if snapshot.has_error:
            border_style = "red"
        elif snapshot.is_complete:
            border_style = "green"
        elif snapshot.waiting_for:
            border_style = "yellow"  # Waiting
        else:
            border_style = "cyan"  # Active

        return Panel(
            content,
            title="[cyan]Shannon CLI V3 - Live Operations[/cyan]",
            border_style=border_style,
            padding=(0, 1)
        )

    def _create_detailed_layout(self, snapshot: MetricsSnapshot) -> Layout:
        """
        Create detailed full-screen layout

        Args:
            snapshot: Current metrics

        Returns:
            Layout with detailed display
        """
        layout = Layout()

        # Split into sections
        layout.split_column(
            Layout(name="progress", size=3),
            Layout(name="streaming", ratio=1),  # Takes most space
            Layout(name="stages", size=5),
            Layout(name="metrics", size=5),
            Layout(name="controls", size=1)
        )

        # Populate sections
        layout["progress"].update(self._render_progress(snapshot))
        layout["streaming"].update(self._render_streaming())
        layout["stages"].update(self._render_stages(snapshot))
        layout["metrics"].update(self._render_metrics(snapshot))
        layout["controls"].update(self._render_controls())

        return layout

    def _render_progress(self, snapshot: MetricsSnapshot) -> Panel:
        """
        Render progress bar panel

        Args:
            snapshot: Current metrics

        Returns:
            Panel with progress bar
        """
        # Create progress bar
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        )

        task = progress.add_task(
            snapshot.current_stage,
            total=100,
            completed=snapshot.progress * 100
        )

        return Panel(progress, border_style="cyan")

    def _render_streaming(self) -> Panel:
        """
        Render streaming output buffer

        Returns:
            Panel with buffered messages
        """
        # Get last N messages
        messages = list(self.streaming_buffer)[-20:]  # Show last 20 lines

        if not messages:
            content = Text("Waiting for output...", style="dim")
        else:
            # Join messages with newlines
            content = Text("\n".join(messages))

        return Panel(
            content,
            title="Streaming Output",
            border_style="blue"
        )

    def _render_stages(self, snapshot: MetricsSnapshot) -> Panel:
        """
        Render completed stages

        Args:
            snapshot: Current metrics

        Returns:
            Panel with stage list
        """
        if not snapshot.completed_stages:
            content = Text("No stages completed yet", style="dim")
        else:
            # Create bullet list
            lines = []
            for stage in snapshot.completed_stages:
                lines.append(f"✓ {stage}")

            content = Text("\n".join(lines), style="green")

        return Panel(
            content,
            title=f"Completed Stages ({len(snapshot.completed_stages)}/{snapshot.total_stages})",
            border_style="green"
        )

    def _render_metrics(self, snapshot: MetricsSnapshot) -> Panel:
        """
        Render live metrics table

        Args:
            snapshot: Current metrics

        Returns:
            Panel with metrics table
        """
        table = Table.grid(padding=(0, 2))
        table.add_column(style="cyan", justify="right")
        table.add_column(style="white")

        # Cost
        table.add_row("Cost:", f"${snapshot.cost_total:.4f}")
        table.add_row("  Input:", f"${snapshot.cost_input:.4f}")
        table.add_row("  Output:", f"${snapshot.cost_output:.4f}")

        table.add_row("", "")  # Spacer

        # Tokens
        table.add_row("Tokens:", f"{snapshot.tokens_total:,}")
        table.add_row("  Input:", f"{snapshot.tokens_input:,}")
        table.add_row("  Output:", f"{snapshot.tokens_output:,}")

        table.add_row("", "")  # Spacer

        # Timing
        table.add_row("Duration:", f"{snapshot.duration_seconds:.1f}s")

        table.add_row("", "")  # Spacer

        # Messages
        table.add_row("Messages:", f"{snapshot.message_count}")
        if snapshot.error_count > 0:
            table.add_row("Errors:", f"{snapshot.error_count}", style="red")

        return Panel(table, title="Metrics", border_style="yellow")

    def _render_controls(self) -> Panel:
        """
        Render keyboard controls

        Returns:
            Panel with control hints
        """
        controls = "[Esc] Collapse | [q] Quit | [p] Pause"
        return Panel(controls, border_style="dim")

    def _handle_keyboard(self) -> None:
        """
        Handle keyboard input (non-blocking)

        Checks for key presses and updates state accordingly.
        """
        key = self.keyboard.read_key(timeout=0.0)

        if key is None:
            return

        if key == Key.ENTER:
            self.expanded = True

        elif key == Key.ESC:
            self.expanded = False

        elif key == Key.Q:
            self.quit_requested = True

        elif key == Key.P:
            self.pause_requested = not self.pause_requested

    def toggle_expand(self) -> None:
        """Toggle between compact and detailed views"""
        self.expanded = not self.expanded

    def collapse(self) -> None:
        """Force collapse to compact view"""
        self.expanded = False

    def expand(self) -> None:
        """Force expand to detailed view"""
        self.expanded = True


# Async helper for integration with async workflows

async def run_with_dashboard(
    collector: MetricsCollector,
    operation: Callable,
    console: Optional[Console] = None
) -> None:
    """
    Run async operation with live dashboard

    Convenience wrapper for running operations with dashboard.

    Args:
        collector: MetricsCollector instance
        operation: Async callable to run
        console: Optional Rich console

    Example:
        collector = MetricsCollector()

        async def my_operation():
            # Do work
            pass

        await run_with_dashboard(collector, my_operation)
    """
    dashboard = LiveDashboard(collector, console=console)

    try:
        dashboard.start()

        # Run operation with periodic dashboard updates
        operation_task = asyncio.create_task(operation())
        update_task = asyncio.create_task(_update_loop(dashboard))

        # Wait for operation to complete
        await operation_task

        # Stop update loop
        update_task.cancel()
        try:
            await update_task
        except asyncio.CancelledError:
            pass

    finally:
        dashboard.stop()


async def _update_loop(dashboard: LiveDashboard) -> None:
    """
    Periodic dashboard update loop

    Args:
        dashboard: Dashboard to update
    """
    while True:
        dashboard.update()
        await asyncio.sleep(0.25)  # 4 Hz
