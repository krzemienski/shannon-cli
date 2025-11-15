"""
Interactive Dashboard - Main V3.1 Dashboard Implementation

Ties together data provider, navigation, rendering, and keyboard handling
into complete 4-layer interactive TUI.

Created: 2025-11-14
Part of: V3.1 Wave 3 (Integration)
"""

import asyncio
import threading
import time
from typing import Optional
from rich.console import Console
from rich.live import Live

from .models import DashboardUIState, DashboardSnapshot
from .data_provider import DashboardDataProvider
from .navigation import NavigationController
from .keyboard import EnhancedKeyboardHandler
from .renderers import (
    Layer1Renderer,
    Layer2Renderer,
    Layer3Renderer,
    Layer4Renderer
)


class InteractiveDashboard:
    """
    Complete interactive dashboard with 4-layer navigation

    Architecture:
        User Input (keyboard) → NavigationController → UI State
        Data Sources (managers) → DashboardDataProvider → Data Snapshot
        (UI State + Data Snapshot) → Layer Renderers → Rich Components
        Rich Components → Rich.Live → Terminal (4 Hz refresh)

    Usage:
        dashboard = InteractiveDashboard(
            metrics=metrics_collector,
            agents=agent_tracker,
            context=context_mgr,
            session=session_mgr
        )

        with dashboard:
            # Dashboard runs, user can navigate
            await your_long_running_operation()

        # Dashboard stops, terminal restored
    """

    def __init__(
        self,
        metrics,
        agents=None,
        context=None,
        session=None,
        interceptor=None,
        console: Optional[Console] = None,
        refresh_per_second: int = 4
    ):
        """
        Initialize interactive dashboard

        Args:
            metrics: MetricsCollector (required)
            agents: AgentStateTracker (optional, enables Layer 2)
            context: ContextManager (optional, enables context visibility)
            session: SessionManager (optional, enables goal display)
            interceptor: MessageInterceptor (optional, for message history)
            console: Rich Console (creates default if None)
            refresh_per_second: Update frequency (default 4 Hz)
        """
        # Data layer
        self.data_provider = DashboardDataProvider(
            metrics=metrics,
            agents=agents,
            context=context,
            session=session,
            interceptor=interceptor
        )

        # State layer
        self.ui_state = DashboardUIState(current_layer=1)
        self.navigator = NavigationController()

        # Rendering layer
        self.layer1 = Layer1Renderer()
        self.layer2 = Layer2Renderer()
        self.layer3 = Layer3Renderer()
        self.layer4 = Layer4Renderer()

        # Input layer
        self.keyboard = EnhancedKeyboardHandler()

        # Rich components
        self.console = console or Console()
        self.refresh_per_second = refresh_per_second
        self._live: Optional[Live] = None

        # Control flags
        self.running = False
        self.quit_requested = False
        self._update_thread: Optional[threading.Thread] = None

    def __enter__(self):
        """Start dashboard in context manager"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop dashboard in context manager"""
        self.stop()
        return False

    def start(self):
        """
        Start interactive dashboard

        Sets up keyboard handler and Rich Live display.
        Begins 4 Hz update loop.
        """
        # Setup keyboard
        try:
            self.keyboard.setup_nonblocking()
        except RuntimeError:
            # Windows or terminal doesn't support raw mode
            # Fall back to non-interactive mode
            pass

        # Create Rich Live display
        self._live = Live(
            self._render_current_layer(),
            console=self.console,
            refresh_per_second=self.refresh_per_second,
            transient=False
        )

        self.running = True
        self._live.start()

        # Start background update loop
        self._update_thread = threading.Thread(
            target=self.run_update_loop,
            daemon=True
        )
        self._update_thread.start()

    def stop(self):
        """
        Stop interactive dashboard

        Restores terminal and stops live display.
        """
        self.running = False

        update_thread = self._update_thread
        if update_thread and update_thread is not threading.current_thread():
            update_thread.join(timeout=1.0)
        self._update_thread = None

        if self._live:
            self._live.stop()
            self._live = None

        # Restore terminal
        try:
            self.keyboard.restore_terminal()
        except:
            pass

    def update(self):
        """
        Single update cycle (called at 4 Hz)

        Steps:
        1. Get fresh data snapshot
        2. Poll for keyboard input
        3. Update UI state based on input
        4. Render current layer
        5. Update live display
        """
        if not self.running or not self._live:
            return

        # Step 1: Get data
        snapshot = self.data_provider.get_snapshot(
            focused_agent_id=self.ui_state.focused_agent_id
        )

        # Step 2: Poll keyboard (non-blocking)
        try:
            key = self.keyboard.poll_key(timeout=0.01)

            # Step 3: Handle key
            if key:
                # Check for global quit
                if key.key == 'q':
                    self.quit_requested = True
                    self.running = False
                    return

                # Navigate
                self.ui_state = self.navigator.handle_key(key, self.ui_state, snapshot)

        except:
            # Keyboard not available (Windows or non-interactive)
            pass

        # Step 4: Render
        renderable = self._render_current_layer(snapshot, self.ui_state)

        # Step 5: Update display
        self._live.update(renderable)

    def run_update_loop(self, duration_seconds: Optional[float] = None):
        """
        Run update loop for specified duration

        Args:
            duration_seconds: How long to run (None = run until quit)
        """
        start_time = time.time()

        while self.running:
            self.update()

            # Check duration
            if duration_seconds:
                if (time.time() - start_time) >= duration_seconds:
                    break

            # Check quit
            if self.quit_requested:
                break

            # Sleep for next cycle (4 Hz = 250ms)
            time.sleep(1.0 / self.refresh_per_second)

    def _render_current_layer(
        self,
        snapshot: Optional[DashboardSnapshot] = None,
        ui_state: Optional[DashboardUIState] = None
    ):
        """
        Render appropriate layer based on UI state

        Args:
            snapshot: Data snapshot (gets fresh if None)
            ui_state: UI state (uses self.ui_state if None)

        Returns:
            Rich renderable (Panel or Layout)
        """
        # Get current state
        if snapshot is None:
            snapshot = self.data_provider.get_snapshot(
                focused_agent_id=self.ui_state.focused_agent_id
            )

        if ui_state is None:
            ui_state = self.ui_state

        # Help overlay takes precedence
        if ui_state.show_help:
            return self._render_help_overlay(ui_state.current_layer)

        # Render layer
        if ui_state.current_layer == 1:
            return self.layer1.render(snapshot, ui_state)
        elif ui_state.current_layer == 2:
            return self.layer2.render(snapshot, ui_state)
        elif ui_state.current_layer == 3:
            return self.layer3.render(snapshot, ui_state)
        elif ui_state.current_layer == 4:
            return self.layer4.render(snapshot, ui_state)

        # Fallback
        return self.layer1.render(snapshot, ui_state)

    def _render_help_overlay(self, current_layer: int):
        """
        Render context-aware help overlay

        Shows keyboard shortcuts relevant to current layer.
        """
        from rich.panel import Panel
        from rich.text import Text

        help_text = Text()

        help_text.append(f"Shannon V3.1 Interactive Dashboard\n", style="bold cyan")
        help_text.append(f"Current Layer: Layer {current_layer}\n\n", style="yellow")

        if current_layer == 1:
            help_text.append("Navigation:\n", style="bold")
            help_text.append("  [↵] Enter    → Navigate to agents/details\n")
            help_text.append("  [q] Quit     → Exit dashboard\n")
            help_text.append("  [h] Help     → Toggle this help\n")

        elif current_layer == 2:
            help_text.append("Navigation:\n", style="bold")
            help_text.append("  [1-9]        → Select agent by number\n")
            help_text.append("  [↵] Enter    → View agent detail\n")
            help_text.append("  [Esc]        → Back to session overview\n")
            help_text.append("  [q] Quit     → Exit dashboard\n")
            help_text.append("  [h] Help     → Toggle this help\n")

        elif current_layer == 3:
            help_text.append("Navigation:\n", style="bold")
            help_text.append("  [↵] Enter    → View message stream\n")
            help_text.append("  [Esc]        → Back to agent list\n")
            help_text.append("  [1-9]        → Switch to agent N\n\n")
            help_text.append("Panels:\n", style="bold")
            help_text.append("  [t]          → Toggle tool history\n")
            help_text.append("  [c]          → Toggle context panel\n\n")
            help_text.append("General:\n", style="bold")
            help_text.append("  [q] Quit     → Exit dashboard\n")
            help_text.append("  [h] Help     → Toggle this help\n")

        elif current_layer == 4:
            help_text.append("Scrolling:\n", style="bold")
            help_text.append("  [↑↓] or [jk] → Scroll one message\n")
            help_text.append("  [PgUp/PgDn]  → Scroll 10 messages\n")
            help_text.append("  [Home/End]   → Jump to start/end\n\n")
            help_text.append("Actions:\n", style="bold")
            help_text.append("  [Enter]      → Expand truncated message\n")
            help_text.append("  [Space]      → Toggle thinking block\n\n")
            help_text.append("Navigation:\n", style="bold")
            help_text.append("  [Esc]        → Back to agent detail\n")
            help_text.append("  [1-9]        → Switch to agent N\n")
            help_text.append("  [q] Quit     → Exit dashboard\n")
            help_text.append("  [h] Help     → Toggle this help\n")

        help_text.append("\n[dim]Press [h] or [Esc] to close help[/dim]")

        return Panel(
            help_text,
            title="[bold]Help[/bold]",
            border_style="cyan",
            padding=(1, 2)
        )
