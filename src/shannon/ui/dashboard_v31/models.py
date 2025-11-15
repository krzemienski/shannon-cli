"""
Shannon V3.1 Data Models

Immutable data models for dashboard state.
All models are frozen dataclasses for thread-safe sharing between update loop and render loop.

Created: 2025-11-14
Part of: V3.1 Wave 0 (Data Foundation)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


@dataclass(frozen=True)
class MCPServerInfo:
    """MCP server connection information"""
    name: str
    status: Literal['connected', 'disconnected', 'error']
    tools_provided: int
    tool_names: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ContextSnapshot:
    """
    Context dimensions state snapshot

    Shows what context the agent/session has loaded.
    """
    # Codebase context
    codebase_files_loaded: int
    codebase_file_list: List[str] = field(default_factory=list)
    codebase_total_bytes: int = 0

    # Memory context
    memories_active: int = 0
    memory_list: List[str] = field(default_factory=list)

    # Tool context
    tools_available: int = 0
    tool_list: List[str] = field(default_factory=list)

    # MCP context
    mcp_servers_connected: int = 0
    mcp_server_list: List[MCPServerInfo] = field(default_factory=list)


@dataclass(frozen=True)
class MessageEntry:
    """
    Single message in SDK conversation

    Represents one message from USER, ASSISTANT, tool_use, or tool_result.
    """
    index: int  # Sequence number in conversation
    role: Literal['user', 'assistant', 'tool_use', 'tool_result']
    content: str  # Full content
    content_preview: str  # First 500 chars for display
    is_truncated: bool  # True if content > 500 chars
    timestamp: datetime

    # For tool messages
    tool_name: Optional[str] = None
    tool_params: Optional[Dict[str, Any]] = None

    # For thinking blocks
    is_thinking: bool = False
    thinking_expanded: bool = False  # UI state for collapse/expand


@dataclass(frozen=True)
class MessageHistory:
    """Complete message history for one agent"""
    agent_id: str
    messages: List[MessageEntry] = field(default_factory=list)
    total_messages: int = 0


@dataclass(frozen=True)
class AgentSnapshot:
    """
    Single agent state snapshot

    Immutable snapshot of agent state for rendering.
    """
    # Identity
    agent_id: str
    agent_number: int  # Display number (1, 2, 3...)
    agent_type: str  # 'backend-builder', 'frontend-builder', etc.
    task_description: str

    # Status
    status: Literal['pending', 'active', 'complete', 'failed']
    progress: float  # 0.0-1.0

    # Timing
    started_at: Optional[datetime] = None
    elapsed_seconds: float = 0.0

    # State detail
    current_operation: Optional[str] = None  # "Reading spec.md"
    waiting_reason: Optional[str] = None  # "WAITING_API", "WAITING_DEPENDENCY"
    wait_duration_seconds: Optional[float] = None
    blocking_agent_id: Optional[str] = None  # If WAITING_DEPENDENCY

    # Metrics
    cost_usd: float = 0.0
    tokens_input: int = 0
    tokens_output: int = 0

    # Artifacts
    files_created: List[str] = field(default_factory=list)
    files_modified: List[str] = field(default_factory=list)
    tool_calls_count: int = 0
    recent_tool_calls: List[str] = field(default_factory=list)

    # Error
    error_message: Optional[str] = None


@dataclass(frozen=True)
class SessionSnapshot:
    """
    Session-level state snapshot

    High-level view of entire execution (command, goal, progress, metrics).
    """
    # Session identity
    session_id: str
    command_name: str  # 'analyze', 'wave', 'task'
    north_star_goal: Optional[str] = None

    # Phase/Wave context
    current_phase: str = "Initializing"  # 'Analysis', 'Wave 2/5', etc.
    overall_progress: float = 0.0  # 0.0-1.0

    # Timing
    start_time: datetime = field(default_factory=datetime.now)
    elapsed_seconds: float = 0.0

    # Global metrics
    total_cost_usd: float = 0.0
    total_tokens: int = 0
    message_count: int = 0

    # Wave context (if command == 'wave')
    wave_number: Optional[int] = None
    total_waves: Optional[int] = None

    # Agent summary (if wave)
    agents_total: int = 0
    agents_active: int = 0
    agents_complete: int = 0
    agents_waiting: int = 0
    agents_failed: int = 0

    # Current operation (operational telemetry)
    current_operation: str = ""  # "Analyzing dependencies dimension"
    last_activity: Optional[str] = None  # "Completed Cognitive dimension"
    last_activity_time: Optional[datetime] = None


@dataclass(frozen=True)
class DashboardSnapshot:
    """
    Complete immutable dashboard state snapshot

    Created at 4 Hz by DashboardDataProvider.
    Contains all data needed to render any layer.
    """
    # Session-level state
    session: SessionSnapshot

    # Agent-level state (empty list if no wave)
    agents: List[AgentSnapshot] = field(default_factory=list)

    # Context state
    context: ContextSnapshot = field(default_factory=lambda: ContextSnapshot(
        codebase_files_loaded=0,
        memories_active=0,
        tools_available=0,
        mcp_servers_connected=0
    ))

    # Message history (for focused agent only)
    messages: Optional[MessageHistory] = None

    # Snapshot metadata
    captured_at: float = field(default_factory=lambda: datetime.now().timestamp())


@dataclass
class KeyEvent:
    """Keyboard event"""
    key: str  # 'enter', 'escape', '1', 'up', 'down', etc.
    modifiers: List[str] = field(default_factory=list)  # 'ctrl', 'shift', 'alt'

    @property
    def is_number(self) -> bool:
        """Check if key is a number 1-9"""
        return self.key.isdigit() and '1' <= self.key <= '9'

    @property
    def is_arrow(self) -> bool:
        """Check if key is arrow key"""
        return self.key in ('up', 'down', 'left', 'right')


@dataclass
class DashboardUIState:
    """
    Mutable UI navigation state

    Tracks user's position in navigation hierarchy.
    Updated by NavigationController in response to keyboard events.
    """
    # Layer navigation
    current_layer: Literal[1, 2, 3, 4] = 1

    # Agent selection (Layer 2+)
    focused_agent_id: Optional[str] = None
    agent_selection_index: int = 0  # For table highlighting (0-indexed)

    # Message scrolling (Layer 4)
    message_scroll_offset: int = 0  # Which message at top of viewport
    message_selection_index: int = 0  # For highlighting
    viewport_height: int = 20  # Messages visible at once

    # Panel toggles (Layer 3)
    show_tool_history: bool = True
    show_context_panel: bool = True

    # Help overlay
    show_help: bool = False

    # Transition state (for animations)
    transitioning_to_layer: Optional[int] = None

    def can_navigate_to_layer_2(self, snapshot: DashboardSnapshot) -> bool:
        """Check if Layer 2 navigation is available"""
        # Layer 2 only makes sense with multiple agents
        return len(snapshot.agents) > 1

    def can_navigate_to_layer_3(self, snapshot: DashboardSnapshot) -> bool:
        """Check if Layer 3 navigation is available"""
        # Layer 3 requires either:
        # - A focused agent (multi-agent wave with selection)
        # - Single agent (auto-focus)
        return (self.focused_agent_id is not None or
                len(snapshot.agents) == 1)

    def can_navigate_to_layer_4(self, snapshot: DashboardSnapshot) -> bool:
        """Check if Layer 4 navigation is available"""
        # Layer 4 requires message history
        return (snapshot.messages is not None and
                snapshot.messages.total_messages > 0)

    def get_focused_agent(self, snapshot: DashboardSnapshot) -> Optional[AgentSnapshot]:
        """Get currently focused agent snapshot"""
        if not self.focused_agent_id:
            # Auto-focus on single agent
            if len(snapshot.agents) == 1:
                return snapshot.agents[0]
            return None

        # Find by ID
        return next(
            (agent for agent in snapshot.agents
             if agent.agent_id == self.focused_agent_id),
            None
        )

    def clone_with_layer(self, layer: int) -> 'DashboardUIState':
        """Create copy with different layer"""
        import dataclasses
        return dataclasses.replace(self, current_layer=layer)

    def clone_with_focused_agent(self, agent_id: str, index: int) -> 'DashboardUIState':
        """Create copy with different focused agent"""
        import dataclasses
        return dataclasses.replace(
            self,
            focused_agent_id=agent_id,
            agent_selection_index=index
        )

    def clone_with_scroll_offset(self, offset: int) -> 'DashboardUIState':
        """Create copy with different scroll position"""
        import dataclasses
        return dataclasses.replace(self, message_scroll_offset=offset)
