"""
Shannon V3.1 - Context-Aware Help Overlay

Provides layer-specific keyboard shortcut help.
Shows only relevant shortcuts for current navigation layer.

Created: 2025-11-14
Part of: V3.1 Wave 4 (Polish & Performance)
"""

from typing import Literal
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
from rich.padding import Padding


class HelpRenderer:
    """
    Render context-aware help overlay

    Shows keyboard shortcuts relevant to current layer.
    Modal overlay that appears when user presses 'h'.
    """

    def render(
        self,
        current_layer: Literal[1, 2, 3, 4],
        has_agents: bool = False
    ) -> Panel:
        """
        Render help overlay for current layer

        Args:
            current_layer: Current navigation layer (1-4)
            has_agents: Whether agents are available (affects Layer 1 controls)

        Returns:
            Rich Panel with help content
        """
        text = Text()

        # Title
        text.append("Shannon V3.1 Interactive Dashboard\n", style="bold cyan")
        text.append(f"Current Layer: Layer {current_layer}\n\n", style="yellow")

        # Layer-specific shortcuts
        if current_layer == 1:
            self._add_layer1_help(text, has_agents)
        elif current_layer == 2:
            self._add_layer2_help(text)
        elif current_layer == 3:
            self._add_layer3_help(text)
        elif current_layer == 4:
            self._add_layer4_help(text)

        # Footer
        text.append("\n")
        text.append("Press [h] or [Esc] to close help", style="dim")

        # Wrap in panel
        return Panel(
            Padding(text, (1, 2)),
            title="[bold]Help[/bold]",
            border_style="cyan",
            padding=(0, 0)
        )

    def _add_layer1_help(self, text: Text, has_agents: bool):
        """Add Layer 1 (Session Overview) help"""

        text.append("Navigation:\n", style="bold white")
        if has_agents:
            text.append("  [↵] Enter    → Navigate to agent list\n", style="white")
        else:
            text.append("  [↵] Enter    → View session details\n", style="white")
        text.append("  [q] Quit     → Exit dashboard\n", style="white")
        text.append("  [h] Help     → Toggle this help\n", style="white")

        text.append("\n")
        text.append("About:\n", style="bold white")
        text.append("  Layer 1 shows session overview: goal, phase, progress,\n", style="dim")
        text.append("  metrics, and current operation.\n", style="dim")

    def _add_layer2_help(self, text: Text):
        """Add Layer 2 (Agent List) help"""

        text.append("Agent Selection:\n", style="bold white")
        text.append("  [1-9]        → Select agent by number\n", style="white")
        text.append("  [↵] Enter    → View selected agent detail\n", style="white")

        text.append("\n")
        text.append("Navigation:\n", style="bold white")
        text.append("  [Esc]        → Back to session overview\n", style="white")
        text.append("  [q] Quit     → Exit dashboard\n", style="white")
        text.append("  [h] Help     → Toggle this help\n", style="white")

        text.append("\n")
        text.append("About:\n", style="bold white")
        text.append("  Layer 2 lists all agents in current wave.\n", style="dim")
        text.append("  Select agent to view details and messages.\n", style="dim")

    def _add_layer3_help(self, text: Text):
        """Add Layer 3 (Agent Detail) help"""

        text.append("Navigation:\n", style="bold white")
        text.append("  [↵] Enter    → View message stream (Layer 4)\n", style="white")
        text.append("  [Esc]        → Back to agent list (or session)\n", style="white")
        text.append("  [1-9]        → Switch to agent N (stay on Layer 3)\n", style="white")

        text.append("\n")
        text.append("Panel Toggles:\n", style="bold white")
        text.append("  [t]          → Toggle tool call history\n", style="white")
        text.append("  [c]          → Toggle context panel\n", style="white")

        text.append("\n")
        text.append("General:\n", style="bold white")
        text.append("  [q] Quit     → Exit dashboard\n", style="white")
        text.append("  [h] Help     → Toggle this help\n", style="white")

        text.append("\n")
        text.append("About:\n", style="bold white")
        text.append("  Layer 3 shows agent details: task, progress, context,\n", style="dim")
        text.append("  tool calls, and current operation.\n", style="dim")

    def _add_layer4_help(self, text: Text):
        """Add Layer 4 (Message Stream) help"""

        text.append("Scrolling:\n", style="bold white")
        text.append("  [↑↓] or [jk] → Scroll one message up/down\n", style="white")
        text.append("  [PgUp/PgDn]  → Scroll 10 messages\n", style="white")
        text.append("  [Home/End]   → Jump to start/end of stream\n", style="white")
        text.append("  [g]/[G]      → Jump to start/end (vim-style)\n", style="white")

        text.append("\n")
        text.append("Message Actions:\n", style="bold white")
        text.append("  [Enter]      → Expand truncated message\n", style="white")
        text.append("  [Space]      → Toggle thinking block expand/collapse\n", style="white")

        text.append("\n")
        text.append("Navigation:\n", style="bold white")
        text.append("  [Esc]        → Back to agent detail (Layer 3)\n", style="white")
        text.append("  [1-9]        → Switch to agent N (stay on Layer 4)\n", style="white")
        text.append("  [q] Quit     → Exit dashboard\n", style="white")
        text.append("  [h] Help     → Toggle this help\n", style="white")

        text.append("\n")
        text.append("About:\n", style="bold white")
        text.append("  Layer 4 shows full SDK message stream: USER prompts,\n", style="dim")
        text.append("  ASSISTANT responses, TOOL calls/results, thinking blocks.\n", style="dim")

    def render_quick_reference(self) -> Panel:
        """
        Render compact quick reference (for onboarding)

        Returns:
            Compact panel with essential shortcuts
        """
        text = Text()

        text.append("Quick Reference\n\n", style="bold cyan")

        text.append("Essential Keys:\n", style="bold white")
        text.append("  [↵] Enter    → Navigate deeper\n", style="white")
        text.append("  [Esc]        → Navigate back\n", style="white")
        text.append("  [1-9]        → Select/switch agent\n", style="white")
        text.append("  [h]          → Toggle full help\n", style="white")
        text.append("  [q]          → Quit\n", style="white")

        text.append("\n")
        text.append("Press [h] anytime for context-aware help", style="dim")

        return Panel(
            Padding(text, (1, 2)),
            title="[bold]Quick Reference[/bold]",
            border_style="cyan"
        )


def get_layer_name(layer: Literal[1, 2, 3, 4]) -> str:
    """
    Get human-readable layer name

    Args:
        layer: Layer number (1-4)

    Returns:
        Layer name
    """
    names = {
        1: "Session Overview",
        2: "Agent List",
        3: "Agent Detail",
        4: "Message Stream"
    }
    return names.get(layer, "Unknown")


def get_available_shortcuts(layer: Literal[1, 2, 3, 4]) -> dict:
    """
    Get available keyboard shortcuts for layer

    Args:
        layer: Current layer

    Returns:
        Dict mapping keys to descriptions
    """
    shortcuts = {
        1: {
            'enter': 'Navigate to agents/details',
            'q': 'Quit dashboard',
            'h': 'Toggle help'
        },
        2: {
            '1-9': 'Select agent by number',
            'enter': 'View agent detail',
            'escape': 'Back to session overview',
            'q': 'Quit dashboard',
            'h': 'Toggle help'
        },
        3: {
            'enter': 'View message stream',
            'escape': 'Back to agent list',
            '1-9': 'Switch to agent N',
            't': 'Toggle tool history',
            'c': 'Toggle context panel',
            'q': 'Quit dashboard',
            'h': 'Toggle help'
        },
        4: {
            'up/down': 'Scroll messages',
            'j/k': 'Scroll messages (vim)',
            'page_up/page_down': 'Scroll 10 messages',
            'home/end': 'Jump to start/end',
            'g/G': 'Jump to start/end (vim)',
            'enter': 'Expand message',
            'space': 'Toggle thinking',
            'escape': 'Back to agent detail',
            '1-9': 'Switch agent',
            'q': 'Quit dashboard',
            'h': 'Toggle help'
        }
    }
    return shortcuts.get(layer, {})

