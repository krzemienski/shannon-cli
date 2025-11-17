"""
Dashboard Event Client

Socket.IO client for CLI to send events to dashboard server.
Solves the architectural issue where CLI and server are separate processes.
"""

import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from socketio import AsyncClient

logger = logging.getLogger(__name__)


class DashboardEventClient:
    """
    Socket.IO client for CLI to send execution events to dashboard server.

    The CLI process uses this client to connect to the dashboard server
    and send events, which the server then broadcasts to connected dashboards.

    This solves the architectural problem where CLI tried to call server's
    sio.emit() directly, which doesn't work across separate processes.

    Usage:
        client = DashboardEventClient('http://localhost:8000', 'session_123')
        await client.connect()
        await client.emit_event('skill:started', {'skill': 'test'})
        await client.disconnect()
    """

    def __init__(self, server_url: str, session_id: str):
        """
        Initialize dashboard event client.

        Args:
            server_url: Dashboard server URL (e.g., 'http://localhost:8000')
            session_id: Unique session ID for this execution
        """
        self.client = AsyncClient()
        self.server_url = server_url
        self.session_id = session_id
        self.connected = False

        logger.info(f"Dashboard client initialized: {server_url}, session={session_id}")

    async def connect(self, timeout: float = 5.0) -> bool:
        """
        Connect to dashboard server.

        Args:
            timeout: Connection timeout in seconds

        Returns:
            True if connected, False if failed
        """
        try:
            logger.info(f"Connecting to dashboard server: {self.server_url}")

            await asyncio.wait_for(
                self.client.connect(self.server_url),
                timeout=timeout
            )

            self.connected = True
            logger.info(f"Dashboard client connected: {self.session_id}")
            return True

        except asyncio.TimeoutError:
            logger.warning(f"Dashboard connection timeout after {timeout}s")
            return False
        except Exception as e:
            logger.warning(f"Dashboard connection failed: {e}")
            return False

    async def emit_event(self, event_type: str, data: Dict[str, Any]) -> bool:
        """
        Emit event to dashboard server.

        The server will receive this and broadcast to all connected dashboards.

        Args:
            event_type: Event type (e.g., 'skill:started', 'execution:completed')
            data: Event data dictionary

        Returns:
            True if emitted successfully, False otherwise
        """
        if not self.connected:
            logger.warning(f"Cannot emit event {event_type}: Not connected")
            print(f"[DashboardClient] Cannot emit {event_type}: Not connected", flush=True)
            return False

        try:
            # Send event to server via 'cli_event' channel
            event_payload = {
                'session_id': self.session_id,
                'event_type': event_type,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }

            print(f"[DashboardClient] Emitting cli_event: {event_type}", flush=True)
            await self.client.emit('cli_event', event_payload)

            logger.info(f"Emitted event to dashboard: {event_type}")  # Changed debug → info
            return True

        except Exception as e:
            logger.error(f"Failed to emit event {event_type}: {e}")
            print(f"[DashboardClient] Error emitting {event_type}: {e}", flush=True)
            return False

    async def disconnect(self):
        """Disconnect from dashboard server."""
        if self.connected:
            try:
                await self.client.disconnect()
                self.connected = False
                logger.info(f"Dashboard client disconnected: {self.session_id}")
            except Exception as e:
                logger.warning(f"Error disconnecting: {e}")

    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
