"""Shannon Dashboard Server - Socket.IO Integration.

This module provides comprehensive Socket.IO event handling and emission
for real-time communication between Shannon orchestrator and dashboard.

Key Features:
- Event handlers for connection, disconnection, and commands
- Event emission helpers for orchestrator integration
- Room-based session management
- Command processing (HALT, RESUME, ROLLBACK, REDIRECT, DECISION, INJECT)
- Connection state tracking and monitoring
- Low-latency communication (<50ms target)

Event Flow:
    Dashboard → Server: Commands (HALT, RESUME, etc.)
    Server → Dashboard: Events (skill:started, file:modified, etc.)
    Server → Orchestrator: Command execution triggers
    Orchestrator → Server: Event emission calls

Connection Lifecycle:
    1. Client connects → 'connect' event
    2. Server assigns to session room
    3. Client sends commands via 'command' event
    4. Server emits events to room
    5. Client disconnects → 'disconnect' event
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Set, Callable
from enum import Enum

from shannon.server.app import sio, active_sessions, session_lock, update_session

logger = logging.getLogger(__name__)


class CommandType(Enum):
    """Dashboard command types."""
    HALT = "HALT"              # Pause execution
    RESUME = "RESUME"          # Resume execution
    ROLLBACK = "ROLLBACK"      # Rollback N steps
    REDIRECT = "REDIRECT"      # Change execution path
    DECISION = "DECISION"      # Make decision at decision point
    INJECT = "INJECT"          # Inject new skill/command


class ExecutionState(Enum):
    """Execution state tracking."""
    RUNNING = "running"
    HALTED = "halted"
    COMPLETED = "completed"
    FAILED = "failed"


# Global state for connection management
class ConnectionManager:
    """
    Manages Socket.IO connections and their associated sessions.

    Thread-safe connection tracking with room-based session isolation.
    Supports multiple dashboards monitoring the same execution session.
    """

    def __init__(self):
        self.connections: Dict[str, Dict[str, Any]] = {}  # sid -> connection info
        self.session_rooms: Dict[str, Set[str]] = {}  # session_id -> set of sids
        self.lock = asyncio.Lock()

        # Command handlers registry
        self.command_handlers: Dict[str, Callable] = {}

        # Execution state
        self.execution_state = ExecutionState.RUNNING
        self.execution_lock = asyncio.Lock()

    async def add_connection(self, sid: str, session_id: Optional[str] = None):
        """Add new connection and join session room."""
        async with self.lock:
            self.connections[sid] = {
                "sid": sid,
                "session_id": session_id,
                "connected_at": datetime.now().isoformat(),
                "events_sent": 0,
                "commands_received": 0
            }

            if session_id:
                if session_id not in self.session_rooms:
                    self.session_rooms[session_id] = set()
                self.session_rooms[session_id].add(sid)

                # Join Socket.IO room
                await sio.enter_room(sid, session_id)

            logger.info(f"Connection added: {sid}, session: {session_id}")

    async def remove_connection(self, sid: str):
        """Remove connection and leave session rooms."""
        async with self.lock:
            if sid not in self.connections:
                return

            conn = self.connections[sid]
            session_id = conn.get("session_id")

            if session_id and session_id in self.session_rooms:
                self.session_rooms[session_id].discard(sid)
                if not self.session_rooms[session_id]:
                    del self.session_rooms[session_id]

                # Leave Socket.IO room
                await sio.leave_room(sid, session_id)

            del self.connections[sid]
            logger.info(f"Connection removed: {sid}")

    async def get_connection_count(self, session_id: Optional[str] = None) -> int:
        """Get connection count for session or total."""
        async with self.lock:
            if session_id:
                return len(self.session_rooms.get(session_id, set()))
            return len(self.connections)

    async def track_event(self, sid: str):
        """Track event sent to connection."""
        async with self.lock:
            if sid in self.connections:
                self.connections[sid]["events_sent"] += 1

    async def track_command(self, sid: str):
        """Track command received from connection."""
        async with self.lock:
            if sid in self.connections:
                self.connections[sid]["commands_received"] += 1

    def register_command_handler(self, command_type: str, handler: Callable):
        """Register a command handler function."""
        self.command_handlers[command_type] = handler
        logger.info(f"Registered command handler: {command_type}")

    async def get_execution_state(self) -> ExecutionState:
        """Get current execution state."""
        async with self.execution_lock:
            return self.execution_state

    async def set_execution_state(self, state: ExecutionState):
        """Set execution state."""
        async with self.execution_lock:
            self.execution_state = state
            logger.info(f"Execution state changed to: {state.value}")


# Global connection manager instance
conn_manager = ConnectionManager()


# ============================================================================
# Socket.IO Event Handlers
# ============================================================================

@sio.event
async def connect(sid: str, environ: Dict, auth: Optional[Dict] = None):
    """
    Handle client connection.

    Args:
        sid: Socket.IO session ID
        environ: WSGI environment dict
        auth: Optional authentication data

    Events Emitted:
        - connected: Connection confirmation with server info
    """
    logger.info(f"Dashboard connected: {sid}")

    # Extract session ID from auth or query params
    session_id = None
    if auth and "session_id" in auth:
        session_id = auth["session_id"]
    elif "QUERY_STRING" in environ:
        # Parse query string for session_id
        from urllib.parse import parse_qs
        query = parse_qs(environ["QUERY_STRING"])
        if "session_id" in query:
            session_id = query["session_id"][0]

    # Add connection to manager
    await conn_manager.add_connection(sid, session_id)

    # Send connection confirmation
    await sio.emit('connected', {
        'server_version': '4.0.0',
        'timestamp': datetime.now().isoformat(),
        'session_id': session_id,
        'capabilities': [
            'HALT', 'RESUME', 'ROLLBACK', 'REDIRECT', 'DECISION', 'INJECT'
        ]
    }, to=sid)

    # If session exists, send current state
    if session_id:
        async with session_lock:
            if session_id in active_sessions:
                await sio.emit('session:state', {
                    'session': active_sessions[session_id],
                    'timestamp': datetime.now().isoformat()
                }, to=sid)


@sio.event
async def disconnect(sid: str):
    """
    Handle client disconnection.

    Args:
        sid: Socket.IO session ID
    """
    logger.info(f"Dashboard disconnected: {sid}")
    await conn_manager.remove_connection(sid)


@sio.event
async def command(sid: str, data: Dict[str, Any]):
    """
    Handle command from dashboard.

    Args:
        sid: Socket.IO session ID
        data: Command data with 'type' and optional parameters

    Command Types:
        - HALT: Pause execution
        - RESUME: Resume execution
        - ROLLBACK: Rollback N steps
        - REDIRECT: Change execution path
        - DECISION: Make decision at decision point
        - INJECT: Inject new skill/command

    Response:
        Emits 'command:result' with success/failure
    """
    try:
        await conn_manager.track_command(sid)

        cmd_type = data.get('type')
        if not cmd_type:
            await sio.emit('command:result', {
                'success': False,
                'error': 'Command type is required',
                'timestamp': datetime.now().isoformat()
            }, to=sid)
            return

        logger.info(f"Received command: {cmd_type} from {sid}")

        # Process command based on type
        if cmd_type == CommandType.HALT.value:
            result = await handle_halt_command(sid, data)
        elif cmd_type == CommandType.RESUME.value:
            result = await handle_resume_command(sid, data)
        elif cmd_type == CommandType.ROLLBACK.value:
            result = await handle_rollback_command(sid, data)
        elif cmd_type == CommandType.REDIRECT.value:
            result = await handle_redirect_command(sid, data)
        elif cmd_type == CommandType.DECISION.value:
            result = await handle_decision_command(sid, data)
        elif cmd_type == CommandType.INJECT.value:
            result = await handle_inject_command(sid, data)
        else:
            result = {
                'success': False,
                'error': f'Unknown command type: {cmd_type}'
            }

        # Send result back to client
        await sio.emit('command:result', {
            **result,
            'timestamp': datetime.now().isoformat(),
            'command_type': cmd_type
        }, to=sid)

    except Exception as e:
        logger.error(f"Error processing command: {e}", exc_info=True)
        await sio.emit('command:result', {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, to=sid)


@sio.event
async def ping(sid: str):
    """
    Handle ping from client for latency measurement.

    Args:
        sid: Socket.IO session ID

    Response:
        Emits 'pong' immediately
    """
    await sio.emit('pong', {
        'timestamp': datetime.now().isoformat()
    }, to=sid)


@sio.event
async def subscribe(sid: str, data: Dict[str, Any]):
    """
    Subscribe to specific event types or sessions.

    Args:
        sid: Socket.IO session ID
        data: Subscription preferences

    Example:
        {
            'event_types': ['skill:*', 'file:modified'],
            'session_id': 'session_123'
        }
    """
    session_id = data.get('session_id')
    if session_id:
        await conn_manager.add_connection(sid, session_id)
        await sio.emit('subscribed', {
            'session_id': session_id,
            'timestamp': datetime.now().isoformat()
        }, to=sid)


@sio.event
async def cli_event(sid: str, data: Dict[str, Any]):
    """
    Receive events from CLI and broadcast to all dashboards.

    This handler allows the CLI (running in a separate process) to send
    execution events to the server, which then broadcasts them to all
    connected dashboard clients.

    Args:
        sid: Socket.IO session ID of the CLI client
        data: Event data with session_id, event_type, timestamp, data

    Example:
        {
            'session_id': 'do_20251116_123456_abc',
            'event_type': 'skill:started',
            'timestamp': '2025-11-16T12:34:56.789',
            'data': {'skill_name': 'code_generation', ...}
        }
    """
    print(f"[WebSocket] cli_event handler triggered! data={data}", flush=True)

    try:
        event_type = data.get('event_type')
        event_data = data.get('data', {})
        timestamp = data.get('timestamp', datetime.now().isoformat())
        session_id = data.get('session_id')

        print(f"[WebSocket] Broadcasting {event_type} to all clients", flush=True)
        logger.info(f"CLI event received: {event_type} from session {session_id}")

        # Broadcast to ALL clients (dashboard may not have session_id)
        await sio.emit(event_type, {
            'timestamp': timestamp,
            'data': event_data,
            'session_id': session_id
        })  # No room restriction - broadcast to all

        print(f"[WebSocket] Broadcast complete", flush=True)
        logger.info(f"Broadcast {event_type} to all clients")

    except Exception as e:
        print(f"[WebSocket] ERROR: {e}", flush=True)
        logger.error(f"Error handling CLI event: {e}", exc_info=True)


# ============================================================================
# Command Handlers
# ============================================================================

async def handle_halt_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle HALT command - pause execution.

    Args:
        sid: Socket.IO session ID
        data: Command data

    Returns:
        Result dict with success status
    """
    try:
        reason = data.get('reason', 'Dashboard halt request')

        # Set execution state to halted
        await conn_manager.set_execution_state(ExecutionState.HALTED)

        # Emit halt event to all connected clients
        await sio.emit('execution:halted', {
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'initiated_by': sid
        })

        logger.info(f"Execution halted by {sid}: {reason}")

        return {
            'success': True,
            'message': 'Execution halted successfully'
        }

    except Exception as e:
        logger.error(f"Error handling halt command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def handle_resume_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle RESUME command - resume execution.

    Args:
        sid: Socket.IO session ID
        data: Command data

    Returns:
        Result dict with success status
    """
    try:
        # Check if execution is halted
        state = await conn_manager.get_execution_state()
        if state != ExecutionState.HALTED:
            return {
                'success': False,
                'error': f'Cannot resume - execution is {state.value}'
            }

        # Set execution state to running
        await conn_manager.set_execution_state(ExecutionState.RUNNING)

        # Emit resume event
        await sio.emit('execution:resumed', {
            'timestamp': datetime.now().isoformat(),
            'initiated_by': sid
        })

        logger.info(f"Execution resumed by {sid}")

        return {
            'success': True,
            'message': 'Execution resumed successfully'
        }

    except Exception as e:
        logger.error(f"Error handling resume command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def handle_rollback_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle ROLLBACK command - rollback N steps.

    Args:
        sid: Socket.IO session ID
        data: Command data with 'steps' parameter

    Returns:
        Result dict with success status
    """
    try:
        steps = data.get('steps', 1)
        session_id = data.get('session_id')

        if not session_id:
            return {
                'success': False,
                'error': 'session_id is required for rollback'
            }

        # Emit rollback event
        await sio.emit('execution:rollback', {
            'steps': steps,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'initiated_by': sid
        }, room=session_id)

        logger.info(f"Rollback {steps} steps requested by {sid} for session {session_id}")

        return {
            'success': True,
            'message': f'Rollback {steps} steps initiated',
            'steps': steps
        }

    except Exception as e:
        logger.error(f"Error handling rollback command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def handle_redirect_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle REDIRECT command - change execution path.

    Args:
        sid: Socket.IO session ID
        data: Command data with 'target_skill' or 'target_path'

    Returns:
        Result dict with success status
    """
    try:
        target_skill = data.get('target_skill')
        target_path = data.get('target_path')
        session_id = data.get('session_id')

        if not (target_skill or target_path):
            return {
                'success': False,
                'error': 'target_skill or target_path is required'
            }

        # Emit redirect event
        await sio.emit('execution:redirect', {
            'target_skill': target_skill,
            'target_path': target_path,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'initiated_by': sid
        }, room=session_id if session_id else None)

        logger.info(f"Redirect to {target_skill or target_path} by {sid}")

        return {
            'success': True,
            'message': 'Redirect initiated',
            'target': target_skill or target_path
        }

    except Exception as e:
        logger.error(f"Error handling redirect command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def handle_decision_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle DECISION command - make decision at decision point.

    Args:
        sid: Socket.IO session ID
        data: Command data with 'decision_id' and 'choice'

    Returns:
        Result dict with success status
    """
    try:
        decision_id = data.get('decision_id')
        choice = data.get('choice')
        session_id = data.get('session_id')

        if not decision_id or choice is None:
            return {
                'success': False,
                'error': 'decision_id and choice are required'
            }

        # Emit decision made event
        await sio.emit('decision:made', {
            'decision_id': decision_id,
            'choice': choice,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'made_by': sid
        }, room=session_id if session_id else None)

        logger.info(f"Decision {decision_id} = {choice} by {sid}")

        return {
            'success': True,
            'message': 'Decision recorded',
            'decision_id': decision_id,
            'choice': choice
        }

    except Exception as e:
        logger.error(f"Error handling decision command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


async def handle_inject_command(sid: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle INJECT command - inject new skill/command.

    Args:
        sid: Socket.IO session ID
        data: Command data with 'skill_name' and 'parameters'

    Returns:
        Result dict with success status
    """
    try:
        skill_name = data.get('skill_name')
        parameters = data.get('parameters', {})
        session_id = data.get('session_id')
        position = data.get('position', 'next')  # 'next', 'end', or index

        if not skill_name:
            return {
                'success': False,
                'error': 'skill_name is required'
            }

        # Emit inject event
        await sio.emit('skill:injected', {
            'skill_name': skill_name,
            'parameters': parameters,
            'position': position,
            'session_id': session_id,
            'timestamp': datetime.now().isoformat(),
            'injected_by': sid
        }, room=session_id if session_id else None)

        logger.info(f"Skill {skill_name} injected at {position} by {sid}")

        return {
            'success': True,
            'message': f'Skill {skill_name} injected',
            'skill_name': skill_name,
            'position': position
        }

    except Exception as e:
        logger.error(f"Error handling inject command: {e}")
        return {
            'success': False,
            'error': str(e)
        }


# ============================================================================
# Event Emission Helpers (for Orchestrator Integration)
# ============================================================================

async def emit_skill_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit skill-related event to dashboard.

    Args:
        event_type: Event type (skill:started, skill:completed, skill:failed)
        data: Event data
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - skill:started: Skill execution began
        - skill:completed: Skill execution succeeded
        - skill:failed: Skill execution failed
        - skill:progress: Skill progress update

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_file_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit file-related event to dashboard.

    Args:
        event_type: Event type (file:modified, file:created, file:deleted)
        data: Event data with file path and details
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - file:modified: File was modified
        - file:created: New file was created
        - file:deleted: File was deleted

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_decision_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit decision-related event to dashboard.

    Args:
        event_type: Event type (decision:point, decision:made)
        data: Event data with decision details
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - decision:point: Decision point reached, waiting for input
        - decision:made: Decision was made (auto or manual)

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_validation_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit validation-related event to dashboard.

    Args:
        event_type: Event type (validation:started, validation:result)
        data: Event data with validation details
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - validation:started: Validation process started
        - validation:result: Validation completed with results

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_agent_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit agent-related event to dashboard.

    Args:
        event_type: Event type (agent:spawned, agent:progress, agent:completed)
        data: Event data with agent details
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - agent:spawned: New agent spawned
        - agent:progress: Agent progress update
        - agent:completed: Agent completed

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_checkpoint_event(
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit checkpoint created event to dashboard.

    Args:
        data: Checkpoint data
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit('checkpoint:created', {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


async def emit_execution_event(
    event_type: str,
    data: Dict[str, Any],
    session_id: Optional[str] = None
) -> None:
    """
    Emit execution state event to dashboard.

    Args:
        event_type: Event type (execution:halted, execution:resumed)
        data: Event data
        session_id: Optional session ID for room targeting (UNUSED - broadcasts to all)

    Event Types:
        - execution:halted: Execution paused
        - execution:resumed: Execution resumed

    Note:
        Broadcasts to ALL connected clients to support dashboards
        that connect without a session_id.
    """
    await sio.emit(event_type, {
        'timestamp': datetime.now().isoformat(),
        'data': data
    })  # Broadcast to all clients


# ============================================================================
# Connection Statistics
# ============================================================================

async def get_connection_stats() -> Dict[str, Any]:
    """
    Get connection statistics for monitoring.

    Returns:
        Dict with connection counts and metrics
    """
    total_connections = await conn_manager.get_connection_count()

    session_counts = {}
    async with conn_manager.lock:
        for session_id, sids in conn_manager.session_rooms.items():
            session_counts[session_id] = len(sids)

    return {
        'total_connections': total_connections,
        'sessions': session_counts,
        'timestamp': datetime.now().isoformat()
    }
