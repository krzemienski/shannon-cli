"""
Dashboard Data Provider - Aggregate all Shannon managers into unified snapshots

Polls MetricsCollector, AgentStateTracker, ContextManager, SessionManager at 4 Hz
and creates immutable DashboardSnapshot objects for rendering.

Created: 2025-11-14
Part of: V3.1 Wave 0 (Data Foundation)
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import time
import json

from shannon.metrics.collector import MetricsCollector
from .models import (
    DashboardSnapshot,
    SessionSnapshot,
    AgentSnapshot,
    ContextSnapshot,
    MessageHistory,
    MessageEntry,
    MCPServerInfo
)


class DashboardDataProvider:
    """
    Aggregates data from all Shannon subsystems

    Provides unified get_snapshot() for dashboard rendering.
    Thread-safe with caching for performance.

    Usage:
        provider = DashboardDataProvider(
            metrics=metrics_collector,
            agents=agent_state_tracker,
            context=context_manager,
            session=session_manager
        )

        snapshot = provider.get_snapshot(focused_agent_id='agent-1')
        # Returns immutable DashboardSnapshot
    """

    def __init__(
        self,
        metrics: MetricsCollector,
        agents: Optional[Any] = None,  # AgentStateTracker
        context: Optional[Any] = None,  # ContextManager
        session: Optional[Any] = None,  # SessionManager
        interceptor: Optional[Any] = None  # MessageInterceptor
    ):
        """
        Initialize data provider

        Args:
            metrics: MetricsCollector (required)
            agents: AgentStateTracker (optional, for wave execution)
            context: ContextManager (optional, for context visibility)
            session: SessionManager (optional, for session metadata)
            interceptor: MessageInterceptor (optional, for message history)
        """
        self.metrics = metrics
        self.agents = agents
        self.context = context
        self.session = session
        self.interceptor = interceptor

        # Cache for performance (50ms TTL to reduce polling overhead)
        self._last_snapshot_time = 0.0
        self._cached_snapshot: Optional[DashboardSnapshot] = None
        self._snapshot_ttl = 0.05  # 50ms

    def get_snapshot(
        self,
        focused_agent_id: Optional[str] = None
    ) -> DashboardSnapshot:
        """
        Get complete dashboard state snapshot

        Args:
            focused_agent_id: Agent to get message history for (Layer 3/4)

        Returns:
            Immutable DashboardSnapshot with all current state
        """
        now = time.time()

        # Check cache (reduces polling from 4 Hz to effective 20 Hz max)
        if (self._cached_snapshot and
            (now - self._last_snapshot_time) < self._snapshot_ttl and
            self._cached_snapshot.messages is None):  # Don't cache if messages requested
            return self._cached_snapshot

        # Build fresh snapshot
        snapshot = DashboardSnapshot(
            session=self._get_session_snapshot(),
            agents=self._get_agent_snapshots(),
            context=self._get_context_snapshot(),
            messages=self._get_message_history(focused_agent_id) if focused_agent_id else None,
            captured_at=now
        )

        # Update cache (only if no focused agent - message history changes frequently)
        if focused_agent_id is None:
            self._cached_snapshot = snapshot
            self._last_snapshot_time = now

        return snapshot

    def _get_session_snapshot(self) -> SessionSnapshot:
        """
        Build session snapshot from SessionManager + MetricsCollector

        Combines session metadata with live metrics.
        """
        # Get metrics
        metrics_snapshot = self.metrics.get_snapshot()

        # Get session data (if available)
        session_data = {}
        if self.session and hasattr(self.session, 'get_current_session'):
            try:
                session_data = self.session.get_current_session() or {}
            except:
                pass

        # Count agent states
        agent_counts = self._count_agent_states()

        return SessionSnapshot(
            session_id=session_data.get('session_id', f'session_{int(time.time())}'),
            command_name=session_data.get('command', 'unknown'),
            north_star_goal=session_data.get('goal'),
            current_phase=session_data.get('phase', metrics_snapshot.current_stage),
            overall_progress=metrics_snapshot.progress,
            start_time=metrics_snapshot.start_time or datetime.now(),
            elapsed_seconds=metrics_snapshot.duration_seconds,
            total_cost_usd=metrics_snapshot.cost_total,
            total_tokens=metrics_snapshot.tokens_total,
            message_count=metrics_snapshot.message_count,
            wave_number=session_data.get('wave_number'),
            total_waves=session_data.get('total_waves'),
            agents_total=agent_counts['total'],
            agents_active=agent_counts['active'],
            agents_complete=agent_counts['complete'],
            agents_waiting=agent_counts['waiting'],
            agents_failed=agent_counts['failed'],
            current_operation=metrics_snapshot.current_operation or 'Processing...',
            last_activity=metrics_snapshot.last_activity,
            last_activity_time=metrics_snapshot.last_activity_time
        )

    def _count_agent_states(self) -> Dict[str, int]:
        """Count agents by state"""
        if not self.agents or not hasattr(self.agents, 'get_all_states'):
            return {'total': 0, 'active': 0, 'complete': 0, 'waiting': 0, 'failed': 0}

        try:
            all_states = self.agents.get_all_states()
        except:
            return {'total': 0, 'active': 0, 'complete': 0, 'waiting': 0, 'failed': 0}

        active = sum(1 for s in all_states if s.status == 'active')
        complete = sum(1 for s in all_states if s.status == 'complete')
        failed = sum(1 for s in all_states if s.status == 'failed')
        waiting = sum(1 for s in all_states if s.status == 'pending')  # pending = waiting

        return {
            'total': len(all_states),
            'active': active,
            'complete': complete,
            'waiting': waiting,
            'failed': failed
        }

    def _get_agent_snapshots(self) -> List[AgentSnapshot]:
        """
        Build agent snapshots from AgentStateTracker

        Converts AgentState objects to immutable AgentSnapshot objects.
        """
        if not self.agents or not hasattr(self.agents, 'get_all_states'):
            return []

        try:
            agent_states = self.agents.get_all_states()
        except:
            return []

        snapshots = []
        for i, state in enumerate(agent_states):
            # Determine waiting reason
            waiting_reason = None
            wait_duration = None

            if state.status in ('pending', 'active'):
                # Check if we can infer waiting reason from state
                # This would be populated by AgentStateTracker if it tracks waiting states
                waiting_reason = getattr(state, 'waiting_reason', None)

                # Calculate wait duration if waiting
                if waiting_reason and state.started_at:
                    wait_duration = (datetime.now() - state.started_at).total_seconds()

            snapshots.append(AgentSnapshot(
                agent_id=state.agent_id,
                agent_number=i + 1,  # Display numbers are 1-indexed
                agent_type=state.agent_type,
                task_description=state.task_description,
                status=state.status,
                progress=state.progress_percent / 100.0,  # Convert to 0.0-1.0
                started_at=state.started_at,
                elapsed_seconds=state.duration_minutes * 60 if state.duration_minutes else 0.0,
                current_operation=self._infer_current_operation(state),
                waiting_reason=waiting_reason,
                wait_duration_seconds=wait_duration,
                blocking_agent_id=None,  # Would need dependency tracking
                cost_usd=state.cost_usd,
                tokens_input=state.tokens_input,
                tokens_output=state.tokens_output,
                files_created=state.files_created,
                files_modified=state.files_modified,
                tool_calls_count=len(state.tool_calls),
                 recent_tool_calls=self._format_recent_tool_calls(state.tool_calls),
                error_message=state.error_message
            ))

        return snapshots

    def _infer_current_operation(self, agent_state: Any) -> Optional[str]:
        """Infer what agent is currently doing"""

        # Check last tool call
        if agent_state.tool_calls:
            last_tool = agent_state.tool_calls[-1]
            tool_name = last_tool.get('name', 'unknown')
            return f"Executing: {tool_name}"

        # Check last activity
        if hasattr(agent_state, 'last_activity'):
            return agent_state.last_activity

        # Default
        if agent_state.status == 'active':
            return "Processing..."

        return None

    def _format_recent_tool_calls(self, tool_calls: Any) -> List[str]:
        """Return human-readable summary of recent tool calls."""
        if not tool_calls:
            return []

        # Only show the most recent 10 entries to avoid large payloads
        recent_calls = tool_calls[-10:]
        return [self._summarize_tool_call(call) for call in recent_calls]

    def _summarize_tool_call(self, call: Any) -> str:
        """Convert a raw tool call dict into a short readable string."""
        arrow = "→"
        name = "tool"
        detail = ""

        if isinstance(call, dict):
            name = (call.get('name') or call.get('tool') or call.get('command') or name)

            direction = str(call.get('direction', 'call')).lower()
            if direction in ("result", "response", "output"):
                arrow = "←"

            status = call.get('status')
            duration = call.get('duration_ms') or call.get('duration')
            args = call.get('args') or call.get('input') or call.get('command')

            details: List[str] = []
            if status:
                details.append(f"[{status}]")

            if duration:
                try:
                    details.append(f"{float(duration):.0f}ms")
                except (ValueError, TypeError):
                    details.append(str(duration))

            if isinstance(args, (dict, list)):
                try:
                    details.append(json.dumps(args)[:80])
                except TypeError:
                    details.append(str(args)[:80])
            elif args:
                details.append(str(args)[:80])

            detail = " ".join(filter(None, details))
        else:
            detail = str(call)

        summary = f"{arrow} {name}"
        if detail:
            summary = f"{summary} {detail}"

        return summary.strip()

    def _get_context_snapshot(self) -> ContextSnapshot:
        """
        Build context snapshot from ContextManager

        Shows what context has been loaded.
        """
        if not self.context or not hasattr(self.context, 'get_state'):
            return ContextSnapshot(
                codebase_files_loaded=0,
                memories_active=0,
                tools_available=0,
                mcp_servers_connected=0
            )

        try:
            context_state = self.context.get_state()
        except:
            return ContextSnapshot(
                codebase_files_loaded=0,
                memories_active=0,
                tools_available=0,
                mcp_servers_connected=0
            )

        # Extract context dimensions
        loaded_files = context_state.get('loaded_files', [])
        active_memories = context_state.get('active_memories', [])
        available_tools = context_state.get('available_tools', [])
        mcp_servers = context_state.get('mcp_servers', [])

        # Build MCP server info
        mcp_info_list = []
        for server in mcp_servers:
            if isinstance(server, dict):
                mcp_info_list.append(MCPServerInfo(
                    name=server.get('name', 'unknown'),
                    status=server.get('status', 'unknown'),
                    tools_provided=server.get('tool_count', 0),
                    tool_names=server.get('tools', [])
                ))

        return ContextSnapshot(
            codebase_files_loaded=len(loaded_files),
            codebase_file_list=loaded_files[:20],  # Limit to first 20 for display
            codebase_total_bytes=context_state.get('total_bytes', 0),
            memories_active=len(active_memories),
            memory_list=active_memories[:10],  # Limit to first 10
            tools_available=len(available_tools),
            tool_list=available_tools[:20],  # Limit to first 20
            mcp_servers_connected=len(mcp_servers),
            mcp_server_list=mcp_info_list
        )

    def _get_message_history(
        self,
        agent_id: str
    ) -> Optional[MessageHistory]:
        """
        Build message history for focused agent

        Converts raw SDK messages to structured MessageEntry objects.
        """
        if not self.agents or not hasattr(self.agents, 'get_state'):
            return None

        try:
            state = self.agents.get_state(agent_id)
        except:
            return None

        if not state:
            return None

        # Convert raw messages to MessageEntry objects
        entries = []
        for i, raw_msg in enumerate(state.all_messages):
            entry = self._parse_message(i, raw_msg)
            entries.append(entry)

        return MessageHistory(
            agent_id=agent_id,
            messages=entries,
            total_messages=len(entries)
        )

    def _parse_message(self, index: int, raw_message: Any) -> MessageEntry:
        """
        Parse SDK message into structured MessageEntry

        Handles: user messages, assistant responses, tool uses, tool results, thinking blocks
        """
        # Default values
        role = 'assistant'
        content = str(raw_message)
        tool_name = None
        tool_params = None
        is_thinking = False

        # Detect message type
        if hasattr(raw_message, 'role'):
            role = raw_message.role

        if hasattr(raw_message, 'type'):
            msg_type = raw_message.type

            if msg_type == 'tool_use':
                role = 'tool_use'
                tool_name = getattr(raw_message, 'name', 'unknown')
                tool_params = getattr(raw_message, 'input', {})
                content = f"Tool: {tool_name}\nParams: {tool_params}"

            elif msg_type == 'tool_result':
                role = 'tool_result'
                content = getattr(raw_message, 'content', str(raw_message))

            elif msg_type == 'thinking':
                is_thinking = True
                content = getattr(raw_message, 'thinking', str(raw_message))

        # Create preview (first 500 chars)
        content_preview = content[:500]
        is_truncated = len(content) > 500

        return MessageEntry(
            index=index,
            role=role,
            content=content,
            content_preview=content_preview,
            is_truncated=is_truncated,
            timestamp=datetime.now(),  # Would extract from message if available
            tool_name=tool_name,
            tool_params=tool_params,
            is_thinking=is_thinking,
            thinking_expanded=False  # Default collapsed
        )
