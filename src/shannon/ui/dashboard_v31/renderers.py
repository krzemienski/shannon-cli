"""
Rendering layer for the Shannon V3.1 interactive dashboard.

Provides four Rich-based renderers:
    - Layer 1: Session overview
    - Layer 2: Agent list/table
    - Layer 3: Agent detail (context + tools)
    - Layer 4: Message stream with virtual scrolling
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from rich.console import Group
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .models import (
    AgentSnapshot,
    ContextSnapshot,
    DashboardSnapshot,
    DashboardUIState,
    MessageEntry,
)


class Layer1Renderer:
    """Render Layer 1: Session overview."""

    PROGRESS_CHARS = 10
    WAIT_THRESHOLD_SECONDS = 5.0

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        session = snapshot.session
        sections: List[str] = []

        if session.north_star_goal:
            sections.append(f"🎯 [bold]{session.north_star_goal}[/bold]")
            sections.append("")

        sections.append(self._phase_line(session))
        sections.append("")
        sections.append(self._progress_line(session))
        sections.append("")

        if session.agents_total:
            sections.append(self._agent_summary_line(session))
            sections.append("")

        sections.append(self._current_operation_line(session))
        sections.append("")
        sections.append(self._metrics_line(session))
        sections.append("")
        sections.append(self._controls_line(snapshot))

        body = "\n".join(section for section in sections if section is not None)

        return Panel(
            body,
            title=f"[bold]Shannon V3.1 - {session.command_name}[/bold]",
            border_style=self._border_style(session),
            padding=(0, 1),
        )

    def _phase_line(self, session) -> str:
        if session.wave_number and session.total_waves:
            return (
                f"[cyan]Wave {session.wave_number}/{session.total_waves}: "
                f"{session.current_phase}[/cyan]"
            )

        return f"[cyan]{session.current_phase}[/cyan]"

    def _progress_line(self, session) -> str:
        progress = max(0.0, min(1.0, session.overall_progress or 0.0))
        filled = int(progress * self.PROGRESS_CHARS)
        bar = "▓" * filled + "░" * (self.PROGRESS_CHARS - filled)
        return f"{bar} {progress:.0%}"

    def _agent_summary_line(self, session) -> str:
        parts = [
            f"[cyan]{session.agents_active} active[/cyan]",
            f"[green]{session.agents_complete} complete[/green]",
            f"[yellow]{session.agents_waiting} waiting[/yellow]",
        ]
        if session.agents_failed:
            parts.append(f"[red]{session.agents_failed} failed[/red]")
        return "Agents: " + ", ".join(parts)

    def _current_operation_line(self, session) -> str:
        operation = session.current_operation or "Processing..."
        wait_seconds: Optional[float] = None
        if session.last_activity_time:
            wait_seconds = (datetime.now() - session.last_activity_time).total_seconds()

        if wait_seconds and wait_seconds > self.WAIT_THRESHOLD_SECONDS:
            return f"[yellow]⏳ {operation} ({wait_seconds:.0f}s)[/yellow]"

        if session.agents_active > 0:
            return f"[cyan]⚙  {operation}[/cyan]"

        if session.agents_complete and session.agents_complete == session.agents_total:
            return f"[green]✓ {operation}[/green]"

        return f"[cyan]{operation}[/cyan]"

    def _metrics_line(self, session) -> str:
        cost = f"${session.total_cost_usd:.2f}"
        tokens = (
            f"{session.total_tokens / 1000:.1f}K"
            if session.total_tokens >= 1000
            else str(session.total_tokens)
        )
        duration = f"{session.elapsed_seconds:.0f}s"
        messages = f"{session.message_count} msgs"
        return f"[dim]{cost} | {tokens} | {duration} | {messages}[/dim]"

    def _controls_line(self, snapshot: DashboardSnapshot) -> str:
        if len(snapshot.agents) > 1:
            return "[dim][↵] Agents | [q] Quit | [h] Help[/dim]"
        return "[dim][↵] Details | [q] Quit | [h] Help[/dim]"

    def _border_style(self, session) -> str:
        if session.agents_failed > 0:
            return "red"
        if session.agents_total and session.agents_complete == session.agents_total:
            return "green"
        if session.agents_waiting > session.agents_active:
            return "yellow"
        if session.agents_active > 0:
            return "cyan"
        return "green"


class Layer2Renderer:
    """Render Layer 2: Agent list with selection."""

    PROGRESS_CHARS = 10

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        agents = snapshot.agents
        if not agents:
            return Panel(
                "[dim]No agents running[/dim]",
                title="[bold]Agents[/bold]",
                border_style="dim",
                padding=(0, 1),
            )

        selected_index = min(
            max(ui_state.agent_selection_index, 0), max(len(agents) - 1, 0)
        )

        id_lookup = {agent.agent_id: agent.agent_number for agent in agents}

        table = Table(
            show_header=True,
            header_style="bold cyan",
            box=None,
            pad_edge=False,
            expand=True,
        )
        table.add_column("#", justify="right", width=3)
        table.add_column("Type", width=20)
        table.add_column("Progress", width=18)
        table.add_column("State", width=14)
        table.add_column("Time", justify="right", width=8)
        table.add_column("Blocking", width=12)

        for idx, agent in enumerate(agents):
            row_style = "bold white on blue" if idx == selected_index else None
            table.add_row(
                str(agent.agent_number),
                agent.agent_type,
                self._progress_bar(agent.progress),
                self._state_label(agent),
                self._time_label(agent),
                self._blocking_label(agent, id_lookup),
                style=row_style,
            )

        footer_lines = [
            self._selected_agent_line(agents[selected_index]),
            "[dim][1-9] Select | [↵] Detail | [Esc] Back | [h] Help[/dim]",
        ]

        wave_info = (
            f"Wave {snapshot.session.wave_number}"
            if snapshot.session.wave_number
            else "Agents"
        )

        return Panel(
            Group(table, Text("\n".join(footer_lines))),
            title=f"[bold]{wave_info}[/bold]",
            border_style="cyan",
            padding=(0, 1),
        )

    def _progress_bar(self, value: float) -> str:
        value = max(0.0, min(1.0, value))
        filled = int(value * self.PROGRESS_CHARS)
        return f"{'▓' * filled}{'░' * (self.PROGRESS_CHARS - filled)} {value:.0%}"

    def _state_label(self, agent: AgentSnapshot) -> str:
        if agent.waiting_reason:
            return f"[yellow]{agent.waiting_reason}[/yellow]"

        color_map = {
            "pending": "dim",
            "active": "cyan",
            "complete": "green",
            "failed": "red",
        }
        color = color_map.get(agent.status, "white")
        return f"[{color}]{agent.status.upper()}[/{color}]"

    def _time_label(self, agent: AgentSnapshot) -> str:
        if agent.wait_duration_seconds:
            return f"{agent.wait_duration_seconds:.0f}s"
        if agent.elapsed_seconds >= 60:
            minutes = agent.elapsed_seconds // 60
            return f"{minutes:.0f}m"
        if agent.elapsed_seconds > 0:
            return f"{agent.elapsed_seconds:.0f}s"
        return "-"

    def _blocking_label(
        self, agent: AgentSnapshot, id_lookup: Dict[str, int]
    ) -> str:
        if agent.blocking_agent_id and agent.blocking_agent_id in id_lookup:
            return f"#{id_lookup[agent.blocking_agent_id]}"
        return "-"

    def _selected_agent_line(self, agent: AgentSnapshot) -> str:
        line = f"Selected: Agent #{agent.agent_number} ({agent.agent_type})"
        if agent.waiting_reason:
            line += f" · {agent.waiting_reason}"
        elif agent.current_operation:
            line += f" · {agent.current_operation}"
        return line


class Layer3Renderer:
    """Render Layer 3: Agent detail view."""

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState):
        agent = ui_state.get_focused_agent(snapshot)
        if not agent:
            return Panel("[red]No agent selected[/red]", border_style="red")

        layout = Layout()
        layout.split_column(
            Layout(name="info", size=5),
            Layout(name="middle"),
            Layout(name="operation", size=5),
        )

        layout["info"].update(self._render_agent_info(agent))

        middle = layout["middle"]
        if ui_state.show_context_panel and ui_state.show_tool_history:
            middle.split_row(
                Layout(name="context", ratio=3),
                Layout(name="tools", ratio=7),
            )
            middle["context"].update(self._render_context_panel(snapshot.context))
            middle["tools"].update(self._render_tool_history(agent))
        elif ui_state.show_context_panel:
            middle.update(self._render_context_panel(snapshot.context))
        elif ui_state.show_tool_history:
            middle.update(self._render_tool_history(agent))
        else:
            middle.update(
                Panel(
                    "[dim]Panels hidden. Press [c] or [t] to toggle.[/dim]",
                    border_style="dim",
                )
            )

        layout["operation"].update(self._render_operation_panel(agent))
        return layout

    def _render_agent_info(self, agent: AgentSnapshot) -> Panel:
        lines = [
            f"[bold]Agent #{agent.agent_number}: {agent.agent_type}[/bold]",
            f"Task: {agent.task_description}",
            f"Status: {agent.status.upper()}",
            self._progress_bar(agent.progress),
        ]
        return Panel("\n".join(lines), border_style="cyan", padding=(0, 1))

    def _render_context_panel(self, context: ContextSnapshot) -> Panel:
        lines: List[str] = []

        lines.append(f"📁 Codebase: {context.codebase_files_loaded} files")
        for path in context.codebase_file_list[:5]:
            lines.append(f"   {path}")
        if len(context.codebase_file_list) > 5:
            lines.append(f"   ... {len(context.codebase_file_list) - 5} more")
        lines.append("")

        lines.append(f"🧠 Memory: {context.memories_active} active")
        for mem in context.memory_list[:5]:
            lines.append(f"   {mem}")
        if len(context.memory_list) > 5:
            lines.append(f"   ... {len(context.memory_list) - 5} more")
        lines.append("")

        lines.append(f"🔧 Tools: {context.tools_available} available")
        for tool in context.tool_list[:5]:
            lines.append(f"   {tool}")
        if len(context.tool_list) > 5:
            lines.append(f"   ... {len(context.tool_list) - 5} more")
        lines.append("")

        lines.append(f"🔌 MCP: {context.mcp_servers_connected} connected")
        for server in context.mcp_server_list[:5]:
            icon = "✅" if server.status == "connected" else "❌"
            lines.append(f"   {server.name} {icon} ({server.tools_provided} tools)")

        return Panel(
            "\n".join(lines) if lines else "[dim]No context loaded[/dim]",
            title="Context Loaded",
            border_style="blue",
            padding=(0, 1),
        )

    def _render_tool_history(self, agent: AgentSnapshot) -> Panel:
        if agent.recent_tool_calls:
            body = "\n".join(agent.recent_tool_calls)
        else:
            body = "[dim]No tool calls recorded[/dim]"

        body += f"\n\n({agent.tool_calls_count} calls total)"

        return Panel(
            body,
            title="Tool Call History",
            border_style="yellow",
            padding=(0, 1),
        )

    def _render_operation_panel(self, agent: AgentSnapshot) -> Panel:
        if agent.waiting_reason:
            wait = (
                f"{agent.wait_duration_seconds:.0f}s"
                if agent.wait_duration_seconds
                else "-"
            )
            lines = [
                f"[yellow]⏳ Waiting: {agent.waiting_reason} ({wait})[/yellow]",
                "[dim][Esc] Back | [1-9] Switch | [t] Tools | [c] Context[/dim]",
            ]
            border = "yellow"
        elif agent.current_operation:
            lines = [
                f"[green]⚙  {agent.current_operation}[/green]",
                "[dim][Esc] Back | [↵] Messages | [1-9] Switch[/dim]",
            ]
            border = "green"
        else:
            lines = [
                "[cyan]Idle[/cyan]",
                "[dim][Esc] Back | [↵] Messages | [1-9] Switch[/dim]",
            ]
            border = "cyan"

        return Panel(
            "\n".join(lines),
            title="Current Operation",
            border_style=border,
            padding=(0, 1),
        )

    def _progress_bar(self, value: float) -> str:
        value = max(0.0, min(1.0, value))
        filled = int(value * Layer2Renderer.PROGRESS_CHARS)
        return f"{'▓' * filled}{'░' * (Layer2Renderer.PROGRESS_CHARS - filled)} {value:.0%}"


class Layer4Renderer:
    """Render Layer 4: Message stream with virtual scrolling."""

    def __init__(self):
        self._cache: Dict[Tuple[int, bool], Text] = {}

    def render(self, snapshot: DashboardSnapshot, ui_state: DashboardUIState) -> Panel:
        history = snapshot.messages
        if not history or not history.messages:
            return Panel(
                "[dim]No messages available[/dim]",
                title="[bold]Message Stream[/bold]",
                border_style="dim",
                padding=(0, 1),
            )

        total = len(history.messages)
        viewport = max(1, ui_state.viewport_height)
        max_offset = max(0, total - viewport)
        offset = min(max(0, ui_state.message_scroll_offset), max_offset)

        visible = history.messages[offset : offset + viewport]

        renderables: List[Text] = []
        for msg in visible:
            renderables.append(self._render_message(msg))
            renderables.append(Text())

        renderables.append(self._footer_text(offset, viewport, total))
        content = Group(*renderables)

        agent = ui_state.get_focused_agent(snapshot)
        if agent:
            title = f"[bold]Messages: Agent #{agent.agent_number} ({agent.agent_type})[/bold]"
        else:
            title = "[bold]Message Stream[/bold]"

        return Panel(content, title=title, border_style="cyan", padding=(0, 1))

    def _render_message(self, msg: MessageEntry) -> Text:
        cache_key = (msg.index, msg.is_thinking and msg.thinking_expanded)
        if cache_key in self._cache:
            return self._cache[cache_key]

        text = Text()
        prefix, style = self._prefix_for_role(msg)
        text.append(prefix, style=style)

        if msg.is_thinking:
            text.append(self._format_thinking(msg), style="dim")
        elif msg.role == "tool_use":
            text.append(self._format_tool_use(msg), style="white")
        elif msg.role == "tool_result":
            text.append(self._format_tool_result(msg), style="white")
        else:
            text.append(self._format_content(msg), style="white")

        if not msg.is_thinking:
            self._cache[cache_key] = text

        return text

    def _prefix_for_role(self, msg: MessageEntry) -> Tuple[str, str]:
        if msg.role == "user":
            return "→ USER: ", "bold blue"
        if msg.role == "assistant" and msg.is_thinking:
            return "← ASSISTANT [thinking]: ", "dim"
        if msg.role == "assistant":
            return "← ASSISTANT: ", "bold green"
        if msg.role == "tool_use":
            return f"→ TOOL_USE: {msg.tool_name or 'unknown'} ", "bold yellow"
        if msg.role == "tool_result":
            return "← TOOL_RESULT: ", "bold cyan"
        return "→ ", "white"

    def _format_content(self, msg: MessageEntry) -> str:
        content = msg.content_preview if msg.is_truncated else msg.content
        if msg.is_truncated:
            content += "\n[dim][truncated - press Enter to expand][/dim]"
        return content

    def _format_tool_use(self, msg: MessageEntry) -> str:
        params = ""
        if msg.tool_params:
            params = f"\n[dim]{json.dumps(msg.tool_params, indent=2)[:400]}[/dim]"
        base = msg.content_preview if msg.is_truncated else msg.content
        if msg.is_truncated:
            base += "\n[dim][truncated - press Enter to expand][/dim]"
        return f"{base}{params}"

    def _format_tool_result(self, msg: MessageEntry) -> str:
        content = msg.content_preview if msg.is_truncated else msg.content
        if msg.is_truncated:
            content += "\n[dim][truncated - press Enter to expand][/dim]"
        return content

    def _format_thinking(self, msg: MessageEntry) -> str:
        if msg.thinking_expanded:
            return msg.content
        line_count = msg.content.count("\n") + 1
        return f"{line_count} lines (press Space to expand)"

    def _footer_text(self, offset: int, viewport: int, total: int) -> Text:
        text = Text()
        text.append(
            f"[dim]Message {offset + 1}-{min(offset + viewport, total)} of {total}[/dim]\n"
        )
        text.append("[dim][↑↓] Scroll | [Enter] Expand | [Esc] Back | [1-9] Switch[/dim]")
        return text

