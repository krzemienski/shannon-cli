"""
Shannon Session Manager

File-based session storage compatible with Serena MCP API.
Provides atomic file operations and async I/O support.

Storage Location: ~/.shannon/sessions/{session_id}/
Format: Individual JSON files per memory key

Created for: Wave 1 - Foundation & Infrastructure
Component: Data & Storage Specialist
"""

import json
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiofiles

# Import config - will be available after Agent 1 completes
try:
    from shannon.config import ShannonConfig
except ImportError:
    # Fallback for independent development
    class ShannonConfig:
        """Minimal config fallback for development"""
        def __init__(self):
            self.session_dir = Path.home() / '.shannon' / 'sessions'


class ISessionStore(ABC):
    """
    Session storage interface - Serena MCP compatible.

    This abstract interface ensures compatibility with Serena MCP's
    memory management API while allowing file-based implementation.

    All Shannon components should use this interface rather than
    directly accessing SessionManager to maintain abstraction.
    """

    @abstractmethod
    def write_memory(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data with key to session storage.

        Args:
            key: Memory key (e.g., 'spec_analysis', 'wave_1_complete')
            data: JSON-serializable data to store

        Raises:
            IOError: If write operation fails
        """
        pass

    @abstractmethod
    def read_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load data by key, None if not found.

        Args:
            key: Memory key to retrieve

        Returns:
            Stored data dictionary or None if key doesn't exist

        Raises:
            IOError: If read operation fails
            json.JSONDecodeError: If stored data is corrupted
        """
        pass

    @abstractmethod
    def list_memories(self) -> List[str]:
        """
        List all keys in session.

        Returns:
            List of memory keys stored in this session
        """
        pass

    @abstractmethod
    def delete_memory(self, key: str) -> None:
        """
        Delete data by key.

        Args:
            key: Memory key to delete

        Note:
            Does not raise error if key doesn't exist (idempotent)
        """
        pass


class SessionManager(ISessionStore):
    """
    File-based session storage in ~/.shannon/sessions/{session_id}/

    Features:
        - Atomic file writes (temp file + rename)
        - JSON storage with pretty printing
        - Automatic directory creation
        - Serena MCP API compatible
        - Async I/O support
        - Session metadata tracking

    Contract Guarantees:
        - write_memory() creates JSON file atomically
        - read_memory() returns exact data saved (or None)
        - Round-trip preserves data: read_memory(k) == data after write_memory(k, data)

    Example:
        >>> session = SessionManager('my_session_123')
        >>> session.write_memory('test', {'key': 'value'})
        >>> data = session.read_memory('test')
        >>> assert data == {'key': 'value'}
    """

    def __init__(self, session_id: str, config: Optional[ShannonConfig] = None):
        """
        Initialize session manager.

        Args:
            session_id: Unique session identifier
            config: Optional Shannon configuration (defaults to standard config)
        """
        self.session_id = session_id
        self.config = config or ShannonConfig()
        self.session_dir = self.config.session_dir / session_id

        # Create session directory if it doesn't exist
        self.session_dir.mkdir(parents=True, exist_ok=True)

        # Session metadata file
        self.metadata_file = self.session_dir / 'session.json'
        self._load_or_create_metadata()

    def _load_or_create_metadata(self) -> None:
        """
        Load existing metadata or create new session metadata.

        Metadata tracks session creation time, last update, and status.
        """
        if self.metadata_file.exists():
            with open(self.metadata_file) as f:
                self.metadata = json.load(f)
                # Update timestamp
                self.metadata['updated_at'] = datetime.now().isoformat()
        else:
            # Create new metadata
            self.metadata = {
                'session_id': self.session_id,
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat(),
                'status': 'active'
            }

        # Save metadata
        self._save_metadata()

    def _save_metadata(self) -> None:
        """Save session metadata atomically."""
        self._write_json_atomic(self.metadata_file, self.metadata)

    def _write_json_atomic(self, file_path: Path, data: Any) -> None:
        """
        Write JSON data to file atomically.

        Uses temp file + rename pattern to ensure atomicity.
        If the write fails, the original file is not corrupted.

        Args:
            file_path: Target file path
            data: Data to write (must be JSON-serializable)

        Raises:
            IOError: If write or rename fails
            TypeError: If data is not JSON-serializable
        """
        # Create temp file in the same directory for atomic rename
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix='.tmp_',
            suffix='.json'
        )

        try:
            # Write to temp file
            with open(temp_fd, 'w') as f:
                json.dump(data, f, indent=2, default=str)

            # Atomic rename (POSIX guarantee)
            temp_path_obj = Path(temp_path)
            temp_path_obj.rename(file_path)

        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink(missing_ok=True)
            except:
                pass
            raise IOError(f"Failed to write {file_path}: {e}") from e

    def write_memory(self, key: str, data: Dict[str, Any]) -> None:
        """
        Save data to {session_dir}/{key}.json atomically.

        Uses atomic write pattern:
        1. Write to temp file
        2. Rename to final (atomic operation)

        Args:
            key: Memory key (e.g., 'spec_analysis', 'wave_1_complete')
            data: JSON-serializable data

        Raises:
            IOError: If write operation fails
            TypeError: If data is not JSON-serializable

        Example:
            >>> session.write_memory('analysis', {'complexity': 0.61})
        """
        file_path = self.session_dir / f"{key}.json"
        self._write_json_atomic(file_path, data)

        # Update metadata
        self.metadata['updated_at'] = datetime.now().isoformat()
        self._save_metadata()

    def read_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load from {session_dir}/{key}.json.

        Args:
            key: Memory key to retrieve

        Returns:
            Stored data dictionary or None if key doesn't exist

        Raises:
            json.JSONDecodeError: If stored data is corrupted

        Example:
            >>> data = session.read_memory('analysis')
            >>> if data:
            ...     print(f"Complexity: {data['complexity']}")
        """
        file_path = self.session_dir / f"{key}.json"

        if not file_path.exists():
            return None

        try:
            with open(file_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(
                f"Corrupted data in {file_path}: {e.msg}",
                e.doc,
                e.pos
            ) from e

    def list_memories(self) -> List[str]:
        """
        List all .json files in session directory (excluding session.json).

        Returns:
            List of memory keys (filenames without .json extension)

        Example:
            >>> keys = session.list_memories()
            >>> print(f"Stored memories: {', '.join(keys)}")
        """
        if not self.session_dir.exists():
            return []

        # Get all .json files except session.json
        json_files = [
            f.stem for f in self.session_dir.glob('*.json')
            if f.name != 'session.json'
        ]

        return sorted(json_files)

    def delete_memory(self, key: str) -> None:
        """
        Delete {key}.json file.

        Args:
            key: Memory key to delete

        Note:
            Idempotent - does not raise error if key doesn't exist

        Example:
            >>> session.delete_memory('temp_data')
        """
        file_path = self.session_dir / f"{key}.json"

        if file_path.exists():
            file_path.unlink()

            # Update metadata
            self.metadata['updated_at'] = datetime.now().isoformat()
            self._save_metadata()

    def has_memory(self, key: str) -> bool:
        """
        Check if memory key exists.

        Args:
            key: Memory key to check

        Returns:
            True if key exists, False otherwise

        Example:
            >>> if session.has_memory('analysis'):
            ...     data = session.read_memory('analysis')
        """
        return (self.session_dir / f"{key}.json").exists()

    def clear_all(self) -> None:
        """
        Delete all memory files (keeps session.json metadata).

        Warning:
            This operation cannot be undone!

        Example:
            >>> session.clear_all()  # Remove all stored memories
        """
        for key in self.list_memories():
            self.delete_memory(key)

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get session metadata and statistics.

        Returns:
            Dictionary with session info including:
                - session_id
                - created_at
                - updated_at
                - status
                - memory_count
                - memory_keys

        Example:
            >>> info = session.get_session_info()
            >>> print(f"Session has {info['memory_count']} memories")
        """
        memories = self.list_memories()
        return {
            **self.metadata,
            'memory_count': len(memories),
            'memory_keys': memories,
            'session_dir': str(self.session_dir)
        }

    def start_session(self, command: str, goal: Optional[str] = None, **kwargs) -> None:
        """
        Start a new session with command context.

        Args:
            command: Command being executed ('analyze', 'wave', 'task')
            goal: Optional north star goal
            **kwargs: Additional session data (phase, wave_number, total_waves, etc.)

        Example:
            >>> session.start_session('analyze', goal='Analyze specification')
            >>> session.start_session('wave', wave_number=2, total_waves=5)
        """
        session_data = {
            'command': command,
            'goal': goal,
            'started_at': datetime.now().isoformat(),
            **kwargs
        }
        self.write_memory('__session__', session_data)

    def update_session(self, **kwargs) -> None:
        """
        Update current session data.

        Args:
            **kwargs: Session fields to update (phase, progress, etc.)

        Example:
            >>> session.update_session(phase='Wave 2/5', progress=0.4)
        """
        current = self.read_memory('__session__') or {}
        current.update(kwargs)
        current['updated_at'] = datetime.now().isoformat()
        self.write_memory('__session__', current)

    def get_current_session(self) -> Optional[Dict[str, Any]]:
        """
        Get current session execution context.

        Returns:
            Dictionary with session data:
                - session_id: str
                - command: str ('analyze', 'wave', 'task')
                - goal: Optional[str] (north star goal)
                - phase: Optional[str] (current phase)
                - wave_number: Optional[int]
                - total_waves: Optional[int]
                - started_at: str (ISO timestamp)
                - updated_at: str (ISO timestamp)

            None if no active session.

        Example:
            >>> session_data = session.get_current_session()
            >>> if session_data:
            ...     print(f"Running: {session_data['command']}")
        """
        data = self.read_memory('__session__')
        if data:
            # Add session_id to response
            data['session_id'] = self.session_id
        return data

    @staticmethod
    def list_all_sessions(config: Optional[ShannonConfig] = None) -> List[str]:
        """
        List all session IDs in the sessions directory.

        Args:
            config: Optional Shannon configuration

        Returns:
            List of session IDs

        Example:
            >>> sessions = SessionManager.list_all_sessions()
            >>> print(f"Found {len(sessions)} sessions")
        """
        cfg = config or ShannonConfig()
        sessions_dir = cfg.session_dir

        if not sessions_dir.exists():
            return []

        return [
            d.name for d in sessions_dir.iterdir()
            if d.is_dir()
        ]

    # Async I/O methods for high-performance scenarios

    async def async_write_memory(self, key: str, data: Dict[str, Any]) -> None:
        """
        Async version of write_memory for high-performance scenarios.

        Args:
            key: Memory key
            data: JSON-serializable data

        Example:
            >>> await session.async_write_memory('analysis', data)
        """
        file_path = self.session_dir / f"{key}.json"

        # Create temp file
        temp_fd, temp_path = tempfile.mkstemp(
            dir=file_path.parent,
            prefix='.tmp_',
            suffix='.json'
        )

        try:
            # Write to temp file asynchronously
            async with aiofiles.open(temp_path, 'w') as f:
                content = json.dumps(data, indent=2, default=str)
                await f.write(content)

            # Close the file descriptor
            import os
            os.close(temp_fd)

            # Atomic rename
            Path(temp_path).rename(file_path)

            # Update metadata
            self.metadata['updated_at'] = datetime.now().isoformat()
            await self._async_save_metadata()

        except Exception as e:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink(missing_ok=True)
            except:
                pass
            raise IOError(f"Failed to write {file_path}: {e}") from e

    async def async_read_memory(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Async version of read_memory for high-performance scenarios.

        Args:
            key: Memory key to retrieve

        Returns:
            Stored data dictionary or None if key doesn't exist

        Example:
            >>> data = await session.async_read_memory('analysis')
        """
        file_path = self.session_dir / f"{key}.json"

        if not file_path.exists():
            return None

        async with aiofiles.open(file_path) as f:
            content = await f.read()
            return json.loads(content)

    async def _async_save_metadata(self) -> None:
        """Save session metadata asynchronously."""
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.metadata_file.parent,
            prefix='.tmp_',
            suffix='.json'
        )

        try:
            async with aiofiles.open(temp_path, 'w') as f:
                content = json.dumps(self.metadata, indent=2, default=str)
                await f.write(content)

            import os
            os.close(temp_fd)

            Path(temp_path).rename(self.metadata_file)

        except Exception as e:
            try:
                Path(temp_path).unlink(missing_ok=True)
            except:
                pass
            raise IOError(f"Failed to write metadata: {e}") from e


# Convenience function for quick session access
def get_session(session_id: str, config: Optional[ShannonConfig] = None) -> SessionManager:
    """
    Get or create a SessionManager instance.

    Args:
        session_id: Session identifier
        config: Optional Shannon configuration

    Returns:
        SessionManager instance

    Example:
        >>> session = get_session('my_session')
        >>> session.write_memory('test', {'key': 'value'})
    """
    return SessionManager(session_id, config)


__all__ = ['ISessionStore', 'SessionManager', 'get_session']
