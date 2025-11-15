"""
Shannon V3.1 Dashboard - Rendering Engine

Four-layer renderer system for interactive dashboard:
- Layer 1: Session overview with progress and metrics
- Layer 2: Agent list table with selection
- Layer 3: Agent detail with 4-panel layout
- Layer 4: Message stream with virtual scrolling

Author: Shannon Framework
Version: 3.1.0
"""

from typing import Dict, List, Optional, Tuple
from datetime import datetime

from rich.panel import Panel
from rich.table import Table
from rich.layout import Layout
from rich.text import Text
from rich.console import Group
from rich.padding import Padding
from rich.align import Align

from .models import (
    DashboardSnapshot,
    DashboardUIState,
    AgentSnapshot,
    MessageEntry,
    SessionSnapshot,
    ContextSnapshot,
    MessageHistory
)


class Layer1Renderer:
    """
    Session overview renderer.

    Shows goal, phase/wave, progress, agent summary, metrics, and controls.
    Border color reflects session state.
    """

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        """Render session overview panel."""
        lines: List[Text] = []

        # Goal (if north_star set)
        if snapshot.session.north_star_goal:
            goal_text = Text()
            goal_text.append("🎯 ", style="bold yellow")
            goal_text.append(snapshot.session.north_star_goal, style="bold white")
            lines.append(goal_text)
            lines.append(Text())  # Blank line

        # Phase/Wave
        phase_line = self._render_phase_wave(snapshot)
        lines.append(phase_line)
        lines.append(Text())  # Blank line

        # Progress bar
        progress_line = self._render_progress(snapshot)
        lines.append(progress_line)
        lines.append(Text())  # Blank line

        # Agent summary (if wave execution)
        if snapshot.session.wave_number is not None:
            agent_line = self._render_agent_summary(snapshot)
            lines.append(agent_line)
            lines.append(Text())  # Blank line

        # Metrics
        metrics_line = self._render_metrics(snapshot)
        lines.append(metrics_line)
        lines.append(Text())  # Blank line

        # Current operation
        operation_line = self._render_current_operation(snapshot)
        lines.append(operation_line)
        lines.append(Text())  # Blank line

        # Controls
        controls_line = self._render_controls()
        lines.append(controls_line)

        # Determine border color based on state
        border_style = self._get_border_style(snapshot)

        # Create panel
        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Shannon V3.1 Dashboard[/bold]",
            border_style=border_style,
            padding=(1, 2),
        )

    def _render_phase_wave(self, snapshot: DashboardSnapshot) -> Text:
        """Render phase/wave information."""
        text = Text()

        if snapshot.session.wave_number is not None:
            # Wave execution
            current = snapshot.session.wave_number
            total = snapshot.session.total_waves or 0
            phase = snapshot.session.current_phase or "Unknown"

            text.append(f"Wave {current}/{total}: ", style="cyan")
            text.append(phase, style="bold white")
        else:
            # Phase execution
            phase = snapshot.session.current_phase or "Unknown"
            text.append("Phase: ", style="cyan")
            text.append(phase, style="bold white")

        return text

    def _render_progress(self, snapshot: DashboardSnapshot) -> Text:
        """Render progress bar."""
        text = Text()

        progress = snapshot.session.overall_progress  # 0.0-1.0

        percentage = int(progress * 100)
        bar_width = 10
        filled = int(progress * bar_width)
        empty = bar_width - filled

        # Progress bar
        text.append("▓" * filled, style="bold green")
        text.append("░" * empty, style="dim white")
        text.append(f" {percentage}%", style="bold white")

        return text

    def _render_agent_summary(self, snapshot: DashboardSnapshot) -> Text:
        """Render agent summary counts."""
        text = Text()
        text.append("Agents: ", style="bold white")

        active = sum(1 for a in snapshot.agents if a.status == 'active')
        complete = sum(1 for a in snapshot.agents if a.status == 'complete')
        waiting = sum(1 for a in snapshot.agents if a.status == 'pending')
        failed = sum(1 for a in snapshot.agents if a.status == 'failed')

        parts = []
        if active > 0:
            parts.append((f"{active} active", "cyan"))
        if complete > 0:
            parts.append((f"{complete} complete", "green"))
        if waiting > 0:
            parts.append((f"{waiting} waiting", "yellow"))
        if failed > 0:
            parts.append((f"{failed} failed", "red"))

        for i, (part, style) in enumerate(parts):
            if i > 0:
                text.append(", ", style="dim white")
            text.append(part, style=style)

        return text

    def _render_metrics(self, snapshot: DashboardSnapshot) -> Text:
        """Render session metrics."""
        text = Text()

        # Cost
        cost = snapshot.session.total_cost_usd
        text.append(f"${cost:.2f}", style="bold green")
        text.append(" | ", style="dim white")

        # Tokens
        tokens = snapshot.session.total_tokens
        if tokens >= 1000:
            text.append(f"{tokens / 1000:.1f}K tokens", style="cyan")
        else:
            text.append(f"{tokens} tokens", style="cyan")
        text.append(" | ", style="dim white")

        # Duration
        duration_sec = snapshot.session.elapsed_seconds
        if duration_sec >= 3600:
            hours = int(duration_sec // 3600)
            minutes = int((duration_sec % 3600) // 60)
            text.append(f"{hours}h {minutes}m", style="yellow")
        elif duration_sec >= 60:
            minutes = int(duration_sec // 60)
            seconds = int(duration_sec % 60)
            text.append(f"{minutes}m {seconds}s", style="yellow")
        else:
            text.append(f"{int(duration_sec)}s", style="yellow")
        text.append(" | ", style="dim white")

        # Message count
        msg_count = snapshot.session.message_count
        text.append(f"{msg_count} msgs", style="magenta")

        return text

    def _render_current_operation(self, snapshot: DashboardSnapshot) -> Text:
        """Render current operation status."""
        text = Text()

        # Find first non-complete agent
        active_agent = None
        for agent in snapshot.agents:
            if agent.status != 'complete':
                active_agent = agent
                break

        if active_agent:
            if active_agent.status == 'pending':
                # Waiting for API
                wait_time = active_agent.wait_duration_seconds or 0
                text.append("⏳ ", style="yellow")
                text.append(f"Waiting for Agent #{active_agent.agent_id}", style="bold yellow")
                text.append(f" ({int(wait_time)}s)", style="dim yellow")
            elif active_agent.status == 'active':
                # Active work
                text.append("⚙ ", style="cyan")
                text.append(active_agent.current_operation or "Working...", style="bold cyan")
            elif active_agent.status == 'failed':
                # Failed
                text.append("❌ ", style="red")
                text.append(f"Agent #{active_agent.agent_id} failed", style="bold red")
            else:
                # Starting
                text.append("▶ ", style="green")
                text.append("Starting...", style="bold green")
        else:
            # All complete
            text.append("✓ ", style="green")
            text.append("All tasks complete", style="bold green")

        return text

    def _render_controls(self) -> Text:
        """Render keyboard controls."""
        text = Text()
        text.append("[↵] Agents", style="bold cyan")
        text.append(" | ", style="dim white")
        text.append("[q] Quit", style="bold red")
        text.append(" | ", style="dim white")
        text.append("[h] Help", style="bold yellow")
        return text

    def _get_border_style(self, snapshot: DashboardSnapshot) -> str:
        """Determine border color based on session state."""
        # Check for any failed agents
        if any(a.status == 'failed' for a in snapshot.agents):
            return "red"

        # Check if all complete
        if all(a.status == 'complete' for a in snapshot.agents) and snapshot.agents:
            return "green"

        # Check if any waiting
        if any(a.status == 'pending' for a in snapshot.agents):
            return "yellow"

        # Active work
        return "cyan"


class Layer2Renderer:
    """
    Agent list table renderer.

    Shows all agents with progress, state, time, and blocking status.
    Highlights selected agent.
    """

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        """Render agent list table panel."""
        # Create table
        table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim white",
            expand=True,
        )

        # Define columns
        table.add_column("#", justify="right", width=4)
        table.add_column("Type", width=20)
        table.add_column("Progress", width=15)
        table.add_column("State", width=15)
        table.add_column("Time", width=10)
        table.add_column("Blocking", width=20)

        # Add agent rows
        for agent in snapshot.agents:
            is_selected = (agent.agent_id == ui_state.focused_agent_id)
            self._add_agent_row(table, agent, is_selected)

        # Footer
        footer = self._render_footer(ui_state)

        # Combine table and footer
        content = Group(table, Text(), footer)

        return Panel(
            content,
            title="[bold]Agent List[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

    def _add_agent_row(self, table: Table, agent: AgentSnapshot, is_selected: bool) -> None:
        """Add a single agent row to the table."""
        # Style based on selection
        if is_selected:
            style = "bold white on blue"
        else:
            style = ""

        # Agent ID
        agent_id = Text(f"#{agent.agent_id}", style=style)

        # Type/Name
        agent_type = Text(agent.agent_type or "unknown", style=style)

        # Progress bar
        progress = self._render_progress_bar(agent.progress, is_selected)

        # State
        state = self._render_state(agent.status, is_selected)

        # Time
        time_text = Text(self._format_time(agent.elapsed_seconds), style=style)

        # Blocking info
        blocking = self._render_blocking(agent, is_selected)

        table.add_row(agent_id, agent_type, progress, state, time_text, blocking)

    def _render_progress_bar(self, percent: float, is_selected: bool) -> Text:
        """Render progress bar for agent."""
        text = Text()

        bar_width = 5
        filled = int((percent / 100) * bar_width)
        empty = bar_width - filled

        if is_selected:
            text.append("▓" * filled, style="bold green on blue")
            text.append("░" * empty, style="dim white on blue")
            text.append(f" {int(percent)}%", style="bold white on blue")
        else:
            text.append("▓" * filled, style="green")
            text.append("░" * empty, style="dim white")
            text.append(f" {int(percent)}%", style="white")

        return text

    def _render_state(self, state: str, is_selected: bool) -> Text:
        """Render agent state with color."""
        text = Text()

        state_str = state.upper()

        if is_selected:
            # Override color when selected
            text.append(state_str, style="bold white on blue")
        else:
            # Normal state colors
            if state == 'pending':
                text.append(state_str, style="yellow")
            elif state == 'active':
                text.append(state_str, style="cyan")
            elif state == 'complete':
                text.append(state_str, style="green")
            elif state == 'failed':
                text.append(state_str, style="red")
            else:
                text.append(state_str, style="white")

        return text

    def _render_blocking(self, agent: AgentSnapshot, is_selected: bool) -> Text:
        """Render blocking information."""
        text = Text()

        if agent.blocking_agent_id:
            style = "bold white on blue" if is_selected else "yellow"
            text.append(agent.blocking_agent_id, style=style)
        else:
            style = "bold white on blue" if is_selected else "dim white"
            text.append("-", style=style)

        return text

    def _format_time(self, seconds: float) -> str:
        """Format duration as string."""
        if seconds >= 3600:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
        elif seconds >= 60:
            minutes = int(seconds // 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        else:
            return f"{int(seconds)}s"

    def _render_footer(self, ui_state: DashboardUIState) -> Text:
        """Render footer with controls."""
        text = Text()

        if ui_state.focused_agent_id is not None:
            text.append(f"Selected: Agent #{ui_state.focused_agent_id}", style="bold white")
            text.append(" | ", style="dim white")

        text.append("[1-9] Select", style="cyan")
        text.append(" | ", style="dim white")
        text.append("[↵] Detail", style="cyan")
        text.append(" | ", style="dim white")
        text.append("[Esc] Back", style="yellow")

        return text


class Layer3Renderer:
    """
    Agent detail renderer with 4-panel layout.

    Panels:
    - Top: Agent info (always visible)
    - Left: Context (toggleable with 'c')
    - Right: Tool history (toggleable with 't')
    - Bottom: Current operation and controls (always visible)
    """

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Layout:
        """Render agent detail layout with 4 panels."""
        # Find selected agent
        agent = self._find_agent(snapshot, ui_state.focused_agent_id)
        if not agent:
            # Fallback if agent not found
            return self._render_error()

        # Create layout
        layout = Layout()

        # Split into top and bottom
        layout.split_column(
            Layout(name="top", size=6),
            Layout(name="middle"),
            Layout(name="bottom", size=4),
        )

        # Render top panel (agent info)
        layout["top"].update(self._render_agent_info(agent))

        # Render middle section (context + tool history)
        layout["middle"].update(self._render_middle_section(agent, snapshot.context, ui_state))

        # Render bottom panel (current operation)
        layout["bottom"].update(self._render_current_operation(agent))

        return layout

    def _find_agent(self, snapshot: DashboardSnapshot, agent_id: Optional[int]) -> Optional[AgentSnapshot]:
        """Find agent by ID."""
        if agent_id is None:
            return None

        for agent in snapshot.agents:
            if agent.agent_id == agent_id:
                return agent

        return None

    def _render_agent_info(self, agent: AgentSnapshot) -> Panel:
        """Render top panel with agent information."""
        lines: List[Text] = []

        # Agent ID and type
        title_line = Text()
        title_line.append(f"Agent #{agent.agent_id}: ", style="bold cyan")
        title_line.append(agent.agent_type or "unknown", style="bold white")
        lines.append(title_line)

        # Task
        if agent.task_description:
            task_line = Text()
            task_line.append("Task: ", style="cyan")
            task_line.append(agent.task_description, style="white")
            lines.append(task_line)

        # Status
        status_line = Text()
        status_line.append("Status: ", style="cyan")
        status_text = agent.status.upper()

        if agent.status == 'pending':
            wait_time = agent.wait_duration_seconds or 0
            status_line.append(f"{status_text} ({wait_time:.1f}s)", style="yellow")
        elif agent.status == 'active':
            status_line.append(status_text, style="cyan")
        elif agent.status == 'complete':
            status_line.append(status_text, style="green")
        elif agent.status == 'failed':
            status_line.append(status_text, style="red")
        else:
            status_line.append(status_text, style="white")

        lines.append(status_line)

        # Progress
        progress_line = Text()
        progress_line.append("Progress: ", style="cyan")

        bar_width = 10
        percent = agent.progress
        filled = int((percent / 100) * bar_width)
        empty = bar_width - filled

        progress_line.append("▓" * filled, style="bold green")
        progress_line.append("░" * empty, style="dim white")
        progress_line.append(f" {int(percent)}%", style="bold white")

        lines.append(progress_line)

        content = Group(*lines)
        return Panel(content, border_style="cyan", padding=(0, 1))

    def _render_middle_section(self, agent: AgentSnapshot, context: ContextSnapshot, ui_state: DashboardUIState) -> Layout:
        """Render middle section with context and tool history."""
        layout = Layout()

        show_context = ui_state.show_context_panel
        show_tools = ui_state.show_tool_history

        if show_context and show_tools:
            # Show both panels
            layout.split_row(
                Layout(self._render_context_panel(context), name="context", ratio=30),
                Layout(self._render_tool_history_panel(agent), name="tools", ratio=70),
            )
        elif show_context:
            # Only context
            layout.update(self._render_context_panel(context))
        elif show_tools:
            # Only tools
            layout.update(self._render_tool_history_panel(agent))
        else:
            # Neither - show placeholder
            layout.update(Panel(
                Align.center("[Press 'c' for context, 't' for tool history]", vertical="middle"),
                border_style="dim white"
            ))

        return layout

    def _render_context_panel(self, context: ContextSnapshot) -> Panel:
        """Render left panel with context information."""
        lines: List[Text] = []

        # Codebase files
        lines.append(Text("📁 Codebase:", style="bold yellow"))
        if context.codebase_file_list:
            lines.append(Text(f"  {context.codebase_files_loaded} files", style="cyan"))
            for file in context.codebase_file_list[:5]:  # Show first 5
                lines.append(Text(f"  {file}", style="dim white"))
            if len(context.codebase_file_list) > 5:
                lines.append(Text(f"  ... and {len(context.codebase_file_list) - 5} more", style="dim white"))
        else:
            lines.append(Text("  None", style="dim white"))

        lines.append(Text())  # Blank line

        # Memory
        lines.append(Text("🧠 Memory:", style="bold yellow"))
        if context.memory_list:
            lines.append(Text(f"  {context.memories_active} active", style="cyan"))
            for memory in context.memory_list[:3]:  # Show first 3
                lines.append(Text(f"  {memory}", style="dim white"))
            if len(context.memory_list) > 3:
                lines.append(Text(f"  ... and {len(context.memory_list) - 3} more", style="dim white"))
        else:
            lines.append(Text("  None", style="dim white"))

        lines.append(Text())  # Blank line

        # Tools
        lines.append(Text("🔧 Tools:", style="bold yellow"))
        tool_count = context.tools_available or 0
        lines.append(Text(f"  {tool_count} available", style="cyan"))
        for tool in context.tool_list[:5]:
            lines.append(Text(f"  {tool}", style="dim white"))

        lines.append(Text())  # Blank line

        # MCP servers
        lines.append(Text("🔌 MCP:", style="bold yellow"))
        if context.mcp_server_list:
            lines.append(Text(f"  {context.mcp_servers_connected} connected", style="cyan"))
            for server in context.mcp_server_list[:3]:  # Show first 3
                status_icon = "✅" if server.status == 'connected' else "❌"
                lines.append(Text(f"  {server.name} {status_icon}", style="green" if server.status == 'connected' else "red"))
            if len(context.mcp_server_list) > 3:
                lines.append(Text(f"  ... and {len(context.mcp_server_list) - 3} more", style="dim white"))
        else:
            lines.append(Text("  None", style="dim white"))

        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Context[/bold]",
            border_style="yellow",
            padding=(1, 1),
        )

    def _render_tool_history_panel(self, agent: AgentSnapshot) -> Panel:
        """Render right panel with tool call history."""
        lines: List[Text] = []

        # Tool call summary
        lines.append(Text(f"Total tool calls: {agent.tool_calls_count}", style="cyan"))
        lines.append(Text())
        
        # Files created
        if agent.files_created:
            lines.append(Text("Files Created:", style="bold green"))
            for file in agent.files_created[:8]:
                lines.append(Text(f"  ✓ {file}", style="green"))
            if len(agent.files_created) > 8:
                lines.append(Text(f"  ... and {len(agent.files_created) - 8} more", style="dim white"))
            lines.append(Text())
        
        # Files modified
        if agent.files_modified:
            lines.append(Text("Files Modified:", style="bold yellow"))
            for file in agent.files_modified[:8]:
                lines.append(Text(f"  ✎ {file}", style="yellow"))
            if len(agent.files_modified) > 8:
                lines.append(Text(f"  ... and {len(agent.files_modified) - 8} more", style="dim white"))
        
        if not agent.files_created and not agent.files_modified and agent.tool_calls_count == 0:
            lines.append(Text("No activity yet", style="dim white"))

        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Tool History[/bold]",
            border_style="yellow",
            padding=(1, 1),
        )

    def _render_current_operation(self, agent: AgentSnapshot) -> Panel:
        """Render bottom panel with current operation."""
        lines: List[Text] = []

        # Current operation
        if agent.status == 'pending':
            op_line = Text()
            op_line.append("⏳ Waiting: ", style="bold yellow")
            op_line.append("Claude API /v1/messages", style="white")
            lines.append(op_line)

            # Request size
            req_line = Text()
            req_line.append("Request: ", style="cyan")
            tokens = agent.current_request_tokens or 0
            req_line.append(f"{tokens / 1000:.0f}K tokens", style="white")
            lines.append(req_line)

            # Wait time
            wait_line = Text()
            wait_line.append("Time waiting: ", style="cyan")
            wait_time = agent.wait_duration_seconds or 0
            wait_line.append(f"{wait_time:.1f}s", style="yellow")
            lines.append(wait_line)
        elif agent.current_operation:
            op_line = Text()
            op_line.append("⚙ ", style="cyan")
            op_line.append(agent.current_operation, style="bold white")
            lines.append(op_line)
        else:
            lines.append(Text("Ready", style="dim white"))

        # Controls
        controls_line = Text()
        controls_line.append("[↵] Messages", style="cyan")
        controls_line.append(" | ", style="dim white")
        controls_line.append("[Esc] Agents", style="yellow")
        controls_line.append(" | ", style="dim white")
        controls_line.append("[1-9] Switch", style="cyan")
        controls_line.append(" | ", style="dim white")
        controls_line.append("[t] Tools", style="yellow")
        controls_line.append(" | ", style="dim white")
        controls_line.append("[c] Context", style="yellow")
        lines.append(controls_line)

        content = Group(*lines)
        return Panel(content, border_style="cyan", padding=(0, 1))

    def _render_error(self) -> Layout:
        """Render error layout when agent not found."""
        layout = Layout()
        layout.update(Panel(
            Align.center("Agent not found", vertical="middle"),
            border_style="red"
        ))
        return layout


class Layer4Renderer:
    """
    Message stream renderer with virtual scrolling.

    Shows conversation messages with:
    - Syntax highlighting by role
    - Thinking block expansion
    - Truncation indicators
    - Scroll position tracking
    """

    def __init__(self):
        """Initialize renderer with syntax cache."""
        self._syntax_cache: Dict[int, Text] = {}

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        """Render message stream panel with virtual scrolling."""
        # Find selected agent
        agent = self._find_agent(snapshot, ui_state.focused_agent_id)
        if not agent or not agent.messages:
            return self._render_empty()

        # Calculate viewport
        total_messages = len(agent.messages)
        viewport_start = ui_state.message_scroll_offset
        viewport_size = 20  # Show 20 messages at a time
        viewport_end = min(viewport_start + viewport_size, total_messages)

        # Render visible messages
        lines: List[Text] = []
        for i in range(viewport_start, viewport_end):
            message = agent.messages[i]
            message_text = self._render_message(message, i, ui_state)
            lines.append(message_text)
            lines.append(Text())  # Blank line between messages

        # Scroll indicator
        scroll_indicator = self._render_scroll_indicator(
            viewport_start, viewport_end, total_messages
        )
        lines.append(scroll_indicator)
        lines.append(Text())  # Blank line

        # Controls
        controls = self._render_controls()
        lines.append(controls)

        content = Group(*lines)
        return Panel(
            content,
            title="[bold]Message Stream[/bold]",
            border_style="cyan",
            padding=(1, 2),
        )

    def _find_agent(self, snapshot: DashboardSnapshot, agent_id: Optional[int]) -> Optional[AgentSnapshot]:
        """Find agent by ID."""
        if agent_id is None:
            return None

        for agent in snapshot.agents:
            if agent.agent_id == agent_id:
                return agent

        return None

    def _render_message(self, message: MessageEntry, index: int, ui_state: DashboardUIState) -> Text:
        """Render a single message with syntax highlighting."""
        # Check cache
        if index in self._syntax_cache:
            return self._syntax_cache[index]

        text = Text()

        # Role prefix with color
        role = message.role.upper()
        if role == "USER":
            text.append("→ USER: ", style="bold blue")
        elif role == "ASSISTANT":
            text.append("← ASSISTANT: ", style="bold green")
        elif role.startswith("TOOL_USE"):
            tool_name = message.content[:50] if message.content else ""
            text.append(f"→ TOOL_USE: {tool_name}", style="bold yellow")
            self._syntax_cache[index] = text
            return text
        elif role.startswith("TOOL_RESULT"):
            text.append("← TOOL_RESULT: ", style="bold cyan")
        else:
            text.append(f"{role}: ", style="bold white")

        # Content handling
        content = message.content or ""

        # Check for thinking blocks
        if message.is_thinking:
            line_count = content.count("\n") + 1
            is_expanded = index in ui_state.expanded_message_ids

            if is_expanded:
                # Show full thinking content
                text.append("\n[thinking]\n", style="dim yellow")
                text.append(content[:500], style="dim white")  # Limit to 500 chars
                if len(content) > 500:
                    text.append("\n... [truncated]", style="dim yellow")
                text.append("\n[/thinking]", style="dim yellow")
            else:
                # Show collapsed indicator
                text.append(f"[thinking] {line_count} lines ", style="dim yellow")
                text.append("(press Space to expand)", style="dim cyan")
        else:
            # Regular content
            if len(content) > 200:
                # Truncated
                text.append(content[:200], style="white")
                text.append(" ... ", style="dim white")
                text.append("[truncated - press Enter to see full]", style="dim cyan")
            else:
                # Full content
                text.append(content, style="white")

        # Cache result
        self._syntax_cache[index] = text
        return text

    def _render_scroll_indicator(self, start: int, end: int, total: int) -> Text:
        """Render scroll position indicator."""
        text = Text()
        text.append(f"[Message {start + 1}-{end} of {total}]", style="dim cyan")

        if start > 0:
            text.append(" ↑ More above", style="yellow")
        if end < total:
            text.append(" ↓ More below", style="yellow")

        return text

    def _render_controls(self) -> Text:
        """Render keyboard controls."""
        text = Text()
        text.append("[↑↓] Scroll", style="cyan")
        text.append(" | ", style="dim white")
        text.append("[Enter] Expand", style="cyan")
        text.append(" | ", style="dim white")
        text.append("[Space] Toggle thinking", style="yellow")
        text.append(" | ", style="dim white")
        text.append("[Esc] Back", style="yellow")
        text.append(" | ", style="dim white")
        text.append("[1-9] Switch", style="cyan")
        return text

    def _render_empty(self) -> Panel:
        """Render empty state when no messages."""
        content = Align.center(
            "No messages yet",
            vertical="middle"
        )
        return Panel(
            content,
            title="[bold]Message Stream[/bold]",
            border_style="dim white",
            padding=(5, 2),
        )
