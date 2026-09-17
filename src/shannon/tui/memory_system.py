"""
Memory System for the TUI Agent Orchestration System.

Manages tiered context and persistent memory across four layers:

* **L1 -- Active Context**: Current task, open files, and agent state.
  Stored as a dictionary, always fully available.
* **L2 -- Session Context**: Accumulated context items for the current
  session, bounded by a configurable maximum size.
* **L3 -- Project Index**: A keyed dictionary of project-level knowledge
  (architecture decisions, code patterns, etc.) that persists across
  sessions for the same project.
* **L4 -- Global Memory**: Cross-project learnings and patterns stored
  as an unbounded list of ``MemoryEntry`` objects.

The system supports CRUD operations on memories, keyword-based search,
session serialisation / deserialisation, and checkpoint / restore for
mid-session recovery.
"""

from __future__ import annotations

import copy
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from shannon.communication.events import EventBus, EventType
from shannon.tui.models import (
    ContextItem,
    MemoryEntry,
    MemoryType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_DEFAULT_L2_MAX_SIZE: int = 200
_DEFAULT_MAX_CONTEXT_TOKENS: int = 128_000


# ---------------------------------------------------------------------------
# MemorySystem
# ---------------------------------------------------------------------------


class MemorySystem:
    """Tiered context and persistent memory manager.

    Parameters
    ----------
    session_id:
        Unique identifier for the current orchestration session.
    project_path:
        Filesystem path to the project root.  Used as the key for L3
        project-index persistence.
    event_bus:
        Optional ``EventBus`` for emitting checkpoint and memory events.
    l2_max_size:
        Maximum number of ``ContextItem`` entries retained in the L2
        session-context ring buffer.
    """

    def __init__(
        self,
        session_id: Optional[str] = None,
        project_path: Optional[str] = None,
        event_bus: Optional[EventBus] = None,
        l2_max_size: int = _DEFAULT_L2_MAX_SIZE,
    ) -> None:
        self.session_id: str = session_id or str(uuid4())
        self.project_path: Optional[str] = project_path
        self._event_bus: Optional[EventBus] = event_bus
        self._l2_max_size: int = l2_max_size

        # L1: Active context (mutable dict)
        self._l1_active: Dict[str, Any] = {
            "current_task": None,
            "open_files": [],
            "agent_state": None,
        }

        # L2: Session context (bounded list of ContextItem)
        self._l2_session: List[ContextItem] = []

        # L3: Project index (keyed dict of MemoryEntry lists)
        self._l3_project: Dict[str, List[MemoryEntry]] = {}

        # L4: Global memories (list of MemoryEntry)
        self._l4_global: List[MemoryEntry] = []

        # Checkpoints
        self._checkpoints: Dict[str, Dict[str, Any]] = {}

        # Flat index for O(1) lookup by memory_id
        self._memory_index: Dict[str, MemoryEntry] = {}

        logger.info(
            "MemorySystem initialised (session=%s, project=%s, l2_max=%d)",
            self.session_id,
            self.project_path,
            self._l2_max_size,
        )

    # ======================================================================
    # Memory CRUD
    # ======================================================================

    def create_memory(
        self,
        memory_type: MemoryType,
        content: str,
        source_task: str = "",
        source_agent: str = "",
        tags: Optional[List[str]] = None,
    ) -> MemoryEntry:
        """Create a new memory entry and store it in the appropriate tier.

        * ``DECISION``, ``ARCHITECTURE``, ``CODE_PATTERN``, ``REQUIREMENT``
          are stored in L3 (project index).
        * Everything else goes to L4 (global).

        Parameters
        ----------
        memory_type:
            Category of the memory entry.
        content:
            Textual content of the memory.
        source_task:
            Identifier of the task that produced this memory.
        source_agent:
            Identifier of the agent that produced this memory.
        tags:
            Optional list of tags for search / filtering.

        Returns
        -------
        MemoryEntry
            The newly created entry.
        """
        entry = MemoryEntry(
            memory_type=memory_type,
            content=content,
            source_task=source_task,
            source_agent=source_agent,
            tags=tags or [],
        )

        # Route to the correct tier
        project_types = {
            MemoryType.DECISION,
            MemoryType.ARCHITECTURE,
            MemoryType.CODE_PATTERN,
            MemoryType.REQUIREMENT,
        }

        if memory_type in project_types:
            key = memory_type.value
            self._l3_project.setdefault(key, []).append(entry)
        else:
            self._l4_global.append(entry)

        # Index for fast lookup
        self._memory_index[entry.memory_id] = entry

        logger.debug(
            "Memory created: id=%s type=%s tags=%s",
            entry.memory_id,
            memory_type.value,
            tags,
        )
        return entry

    def search_memories(
        self,
        query: str,
        memory_type: Optional[MemoryType] = None,
        limit: int = 20,
    ) -> List[MemoryEntry]:
        """Search memories by keyword matching on content and tags.

        The search is case-insensitive and matches against both the
        ``content`` field and any of the ``tags``.

        Parameters
        ----------
        query:
            Free-text search query.
        memory_type:
            If provided, restrict results to this type.
        limit:
            Maximum number of results to return.

        Returns
        -------
        List[MemoryEntry]
            Matching entries sorted by relevance (match density).
        """
        query_lower = query.lower()
        query_terms = query_lower.split()
        candidates = self._all_memories(memory_type)

        scored: List[tuple[float, MemoryEntry]] = []
        for entry in candidates:
            content_lower = entry.content.lower()
            tag_text = " ".join(entry.tags).lower()
            combined = content_lower + " " + tag_text

            # Simple relevance: count of query terms present
            hits = sum(1 for term in query_terms if term in combined)
            if hits > 0:
                score = hits / len(query_terms) if query_terms else 0.0
                scored.append((score, entry))

        # Sort by score descending, then by recency
        scored.sort(key=lambda pair: (-pair[0], pair[1].created_at), reverse=False)

        results = [entry for _, entry in scored[:limit]]

        # Bump access counts
        for entry in results:
            entry.access_count += 1

        return results

    def get_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        limit: int = 50,
    ) -> List[MemoryEntry]:
        """Retrieve memories, optionally filtered by type.

        Parameters
        ----------
        memory_type:
            If provided, restrict to this type.
        limit:
            Maximum entries to return.

        Returns
        -------
        List[MemoryEntry]
            Entries ordered by creation time (newest first).
        """
        candidates = self._all_memories(memory_type)
        candidates.sort(key=lambda e: e.created_at, reverse=True)
        return candidates[:limit]

    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory entry by ID.

        Parameters
        ----------
        memory_id:
            The unique identifier of the memory to delete.

        Returns
        -------
        bool
            ``True`` if the entry was found and removed, ``False`` otherwise.
        """
        entry = self._memory_index.pop(memory_id, None)
        if entry is None:
            return False

        # Remove from L3
        for key, entries in self._l3_project.items():
            self._l3_project[key] = [
                e for e in entries if e.memory_id != memory_id
            ]

        # Remove from L4
        self._l4_global = [
            e for e in self._l4_global if e.memory_id != memory_id
        ]

        logger.debug("Memory deleted: %s", memory_id)
        return True

    def update_memory(
        self,
        memory_id: str,
        content: str,
    ) -> Optional[MemoryEntry]:
        """Update the content of an existing memory entry.

        Parameters
        ----------
        memory_id:
            The unique identifier of the memory to update.
        content:
            New content to replace the existing text.

        Returns
        -------
        Optional[MemoryEntry]
            The updated entry, or ``None`` if not found.
        """
        entry = self._memory_index.get(memory_id)
        if entry is None:
            return None

        entry.content = content
        entry.updated_at = datetime.utcnow()

        logger.debug("Memory updated: %s", memory_id)
        return entry

    # ======================================================================
    # Context management
    # ======================================================================

    def set_active_context(
        self,
        task: str,
        files: Optional[List[str]] = None,
        agent_state: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Replace the L1 active-context with new values.

        Parameters
        ----------
        task:
            Description or identifier of the currently active task.
        files:
            List of file paths currently relevant / open.
        agent_state:
            Snapshot of the current agent's runtime state.
        """
        self._l1_active = {
            "current_task": task,
            "open_files": files or [],
            "agent_state": agent_state,
        }
        logger.debug("L1 active context updated: task=%s", task)

    def add_session_context(self, entry: ContextItem) -> None:
        """Append a ``ContextItem`` to the L2 session buffer.

        If the buffer exceeds ``l2_max_size``, the oldest entries are
        discarded to make room.

        Parameters
        ----------
        entry:
            The context item to add.
        """
        self._l2_session.append(entry)

        # Prune oldest entries if over capacity
        if len(self._l2_session) > self._l2_max_size:
            overflow = len(self._l2_session) - self._l2_max_size
            self._l2_session = self._l2_session[overflow:]
            logger.debug("L2 pruned %d oldest entries", overflow)

    def get_relevant_context(
        self,
        task_description: str,
        max_tokens: int = _DEFAULT_MAX_CONTEXT_TOKENS,
    ) -> List[ContextItem]:
        """Retrieve context items across all tiers, ranked by relevance.

        The method gathers context from L1 (active), L2 (session), L3
        (project), and L4 (global) and returns a merged list that fits
        within the given token budget.

        Parameters
        ----------
        task_description:
            Description of the task to match context against.
        max_tokens:
            Approximate token budget for the returned context.

        Returns
        -------
        List[ContextItem]
            Ranked context items within the token budget.
        """
        query_terms = task_description.lower().split()
        collected: List[ContextItem] = []

        # L1: always include active context as a synthetic ContextItem
        if self._l1_active.get("current_task"):
            l1_item = ContextItem(
                content=json.dumps(self._l1_active, default=str),
                source="l1_active_context",
                context_type="active",
                relevance_score=1.0,
                token_estimate=self._estimate_tokens(
                    json.dumps(self._l1_active, default=str)
                ),
            )
            collected.append(l1_item)

        # L2: session context, scored by keyword match
        for item in self._l2_session:
            score = self._score_relevance(item.content, query_terms)
            item_copy = copy.copy(item)
            item_copy.relevance_score = max(item.relevance_score, score)
            collected.append(item_copy)

        # L3: project index entries, converted to ContextItem
        for key, entries in self._l3_project.items():
            for entry in entries:
                score = self._score_relevance(entry.content, query_terms)
                if score > 0:
                    ci = ContextItem(
                        content=entry.content,
                        source=f"l3_project/{key}",
                        context_type="project",
                        relevance_score=score,
                        token_estimate=self._estimate_tokens(entry.content),
                        metadata={
                            "memory_id": entry.memory_id,
                            "tags": entry.tags,
                        },
                    )
                    collected.append(ci)

        # L4: global memories, converted to ContextItem
        for entry in self._l4_global:
            score = self._score_relevance(entry.content, query_terms)
            if score > 0:
                ci = ContextItem(
                    content=entry.content,
                    source="l4_global",
                    context_type="global",
                    relevance_score=score,
                    token_estimate=self._estimate_tokens(entry.content),
                    metadata={
                        "memory_id": entry.memory_id,
                        "tags": entry.tags,
                    },
                )
                collected.append(ci)

        # Sort by relevance (highest first)
        collected.sort(key=lambda c: c.relevance_score, reverse=True)

        # Trim to token budget
        result: List[ContextItem] = []
        total_tokens = 0
        for item in collected:
            est = item.token_estimate or self._estimate_tokens(item.content)
            if total_tokens + est > max_tokens:
                break
            result.append(item)
            total_tokens += est

        return result

    def get_context_utilization(self) -> Dict[str, float]:
        """Return the percentage utilisation of each context tier.

        Returns
        -------
        Dict[str, float]
            Keys ``"l1"``, ``"l2"``, ``"l3"``, ``"l4"`` mapped to a
            percentage (0.0 -- 100.0).
        """
        l1_used = 1.0 if self._l1_active.get("current_task") else 0.0
        l2_used = (
            (len(self._l2_session) / self._l2_max_size) * 100.0
            if self._l2_max_size > 0
            else 0.0
        )
        l3_count = sum(len(v) for v in self._l3_project.values())
        # L3 has no hard cap; express as entry count for information
        l3_used = min(l3_count * 1.0, 100.0)
        l4_used = min(len(self._l4_global) * 1.0, 100.0)

        return {
            "l1": l1_used * 100.0,
            "l2": l2_used,
            "l3": l3_used,
            "l4": l4_used,
        }

    # ======================================================================
    # Session persistence
    # ======================================================================

    def save_session(self, path: Path) -> None:
        """Serialise the full memory system state to a JSON file.

        Parameters
        ----------
        path:
            Destination file path (will be created or overwritten).
        """
        data = self._snapshot()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
        logger.info("Session saved to %s", path)

    def load_session(self, path: Path) -> None:
        """Load memory system state from a previously saved JSON file.

        Parameters
        ----------
        path:
            Source file path.

        Raises
        ------
        FileNotFoundError
            If the file does not exist.
        json.JSONDecodeError
            If the file is not valid JSON.
        """
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        self._restore_from_snapshot(data)
        logger.info("Session loaded from %s", path)

    def create_checkpoint(self) -> str:
        """Snapshot the current state and return a checkpoint ID.

        Returns
        -------
        str
            The checkpoint identifier that can be passed to
            :meth:`restore_checkpoint`.
        """
        checkpoint_id = str(uuid4())
        self._checkpoints[checkpoint_id] = self._snapshot()

        if self._event_bus is not None:
            # Fire-and-forget -- caller is expected to run in an async context
            # but we do not require it here.
            try:
                import asyncio

                loop = asyncio.get_running_loop()
                loop.create_task(
                    self._event_bus.emit(
                        event_type=EventType.CHECKPOINT_CREATED,
                        data={
                            "checkpoint_id": checkpoint_id,
                            "session_id": self.session_id,
                        },
                        source="memory_system",
                    )
                )
            except RuntimeError:
                pass  # No running loop -- skip event

        logger.info("Checkpoint created: %s", checkpoint_id)
        return checkpoint_id

    def restore_checkpoint(self, checkpoint_id: str) -> None:
        """Restore state from a previously created checkpoint.

        Parameters
        ----------
        checkpoint_id:
            The identifier returned by :meth:`create_checkpoint`.

        Raises
        ------
        KeyError
            If the checkpoint ID is not found.
        """
        snapshot = self._checkpoints.get(checkpoint_id)
        if snapshot is None:
            raise KeyError(f"Checkpoint not found: {checkpoint_id}")

        self._restore_from_snapshot(snapshot)

        if self._event_bus is not None:
            try:
                import asyncio

                loop = asyncio.get_running_loop()
                loop.create_task(
                    self._event_bus.emit(
                        event_type=EventType.CHECKPOINT_RESTORED,
                        data={
                            "checkpoint_id": checkpoint_id,
                            "session_id": self.session_id,
                        },
                        source="memory_system",
                    )
                )
            except RuntimeError:
                pass

        logger.info("Checkpoint restored: %s", checkpoint_id)

    # ======================================================================
    # Stats
    # ======================================================================

    def get_stats(self) -> Dict[str, Any]:
        """Return summary statistics about the memory system.

        Returns
        -------
        Dict[str, Any]
            Dictionary containing memory counts, context utilisation,
            and session information.
        """
        l3_count = sum(len(v) for v in self._l3_project.values())

        return {
            "session_id": self.session_id,
            "project_path": self.project_path,
            "memory_counts": {
                "l2_session": len(self._l2_session),
                "l3_project": l3_count,
                "l4_global": len(self._l4_global),
                "total_indexed": len(self._memory_index),
            },
            "context_utilization": self.get_context_utilization(),
            "checkpoints": len(self._checkpoints),
            "l2_max_size": self._l2_max_size,
        }

    # ======================================================================
    # Private helpers
    # ======================================================================

    def _all_memories(
        self,
        memory_type: Optional[MemoryType] = None,
    ) -> List[MemoryEntry]:
        """Gather all memory entries, optionally filtered by type."""
        entries: List[MemoryEntry] = []

        for mem_list in self._l3_project.values():
            entries.extend(mem_list)
        entries.extend(self._l4_global)

        if memory_type is not None:
            entries = [e for e in entries if e.memory_type == memory_type]

        return entries

    @staticmethod
    def _estimate_tokens(text: str) -> int:
        """Rough token estimate: ~4 characters per token."""
        return max(1, len(text) // 4)

    @staticmethod
    def _score_relevance(content: str, query_terms: List[str]) -> float:
        """Score content against query terms via keyword overlap."""
        if not query_terms:
            return 0.0
        content_lower = content.lower()
        hits = sum(1 for term in query_terms if term in content_lower)
        return hits / len(query_terms)

    def _snapshot(self) -> Dict[str, Any]:
        """Produce a JSON-serialisable snapshot of all state."""
        return {
            "session_id": self.session_id,
            "project_path": self.project_path,
            "l1_active": copy.deepcopy(self._l1_active),
            "l2_session": [item.to_dict() for item in self._l2_session],
            "l3_project": {
                key: [e.to_dict() for e in entries]
                for key, entries in self._l3_project.items()
            },
            "l4_global": [e.to_dict() for e in self._l4_global],
            "snapshot_at": datetime.utcnow().isoformat(),
        }

    def _restore_from_snapshot(self, data: Dict[str, Any]) -> None:
        """Restore internal state from a snapshot dict."""
        self.session_id = data.get("session_id", self.session_id)
        self.project_path = data.get("project_path", self.project_path)

        self._l1_active = data.get("l1_active", {
            "current_task": None,
            "open_files": [],
            "agent_state": None,
        })

        self._l2_session = [
            ContextItem.from_dict(d) for d in data.get("l2_session", [])
        ]

        self._l3_project = {}
        for key, entry_dicts in data.get("l3_project", {}).items():
            self._l3_project[key] = [
                MemoryEntry.from_dict(d) for d in entry_dicts
            ]

        self._l4_global = [
            MemoryEntry.from_dict(d) for d in data.get("l4_global", [])
        ]

        # Rebuild index
        self._memory_index.clear()
        for entries in self._l3_project.values():
            for entry in entries:
                self._memory_index[entry.memory_id] = entry
        for entry in self._l4_global:
            self._memory_index[entry.memory_id] = entry

        logger.debug(
            "State restored: l2=%d, l3=%d, l4=%d",
            len(self._l2_session),
            sum(len(v) for v in self._l3_project.values()),
            len(self._l4_global),
        )
