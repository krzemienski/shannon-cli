"""
tests/cli_infrastructure/output_parser.py

Utilities for parsing Shannon CLI output and extracting structured data.
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class DashboardState:
    """Parsed dashboard state"""
    command: Optional[str] = None
    cost_usd: Optional[float] = None
    tokens_k: Optional[float] = None
    duration_s: Optional[int] = None
    progress_percent: Optional[float] = None
    state: Optional[str] = None
    layer: int = 1


@dataclass
class AgentState:
    """Parsed agent state"""
    agent_number: int
    agent_type: str
    progress_percent: float
    state: str
    duration_s: Optional[float] = None
    blocking_agent: Optional[int] = None
    api_call: Optional[str] = None


class OutputParser:
    """
    Parse Shannon CLI output to extract structured data

    Usage:
        parser = OutputParser()
        state = parser.parse_dashboard(output)
        agents = parser.parse_agent_telemetry(output)
    """

    @staticmethod
    def parse_dashboard(output: str) -> DashboardState:
        """
        Parse dashboard output

        Args:
            output: CLI output text

        Returns:
            DashboardState with extracted fields
        """

        state = DashboardState()

        # Extract command
        match = re.search(r'Shannon:\s*(\S+)', output)
        if match:
            state.command = match.group(1)

        # Extract cost
        match = re.search(r'\$(\d+\.\d+)', output)
        if match:
            state.cost_usd = float(match.group(1))

        # Extract tokens
        match = re.search(r'(\d+\.?\d*)K\s*tokens?', output, re.IGNORECASE)
        if match:
            state.tokens_k = float(match.group(1))

        # Extract duration
        duration_s = 0
        match = re.search(r'(\d+)h', output)
        if match:
            duration_s += int(match.group(1)) * 3600
        match = re.search(r'(\d+)m', output)
        if match:
            duration_s += int(match.group(1)) * 60
        match = re.search(r'(\d+)s', output)
        if match:
            duration_s += int(match.group(1))
        if duration_s > 0:
            state.duration_s = duration_s

        # Extract progress
        match = re.search(r'(\d+)%', output)
        if match:
            state.progress_percent = float(match.group(1))

        # Extract state
        state_patterns = {
            'WAITING_API': r'WAITING.*API|WAITING_API',
            'WAITING_DEPENDENCY': r'WAITING.*DEPENDENCY|WAITING_DEPENDENCY',
            'WAITING': r'WAITING',
            'ACTIVE': r'ACTIVE',
            'COMPLETE': r'COMPLETE',
            'FAILED': r'FAILED'
        }

        for state_name, pattern in state_patterns.items():
            if re.search(pattern, output, re.IGNORECASE):
                state.state = state_name
                break

        # Detect layer
        if 'AGENTS:' in output or 'agent' in output.lower():
            state.layer = 2
        if 'STREAMING:' in output or 'dimensions' in output.lower():
            state.layer = 3
        if 'MESSAGE' in output and ('USER:' in output or 'ASSISTANT:' in output):
            state.layer = 4

        return state

    @staticmethod
    def parse_agent_telemetry(output: str) -> List[AgentState]:
        """
        Parse agent telemetry from wave output

        Args:
            output: CLI output text

        Returns:
            List of AgentState objects
        """

        agents = []

        # Pattern: "#1 backend-builder 67% WAITING_API (12.4s)"
        pattern = r'#(\d+)\s+(\S+)\s+(\d+)%\s+(\w+)'

        for match in re.finditer(pattern, output):
            agent = AgentState(
                agent_number=int(match.group(1)),
                agent_type=match.group(2),
                progress_percent=float(match.group(3)),
                state=match.group(4)
            )

            # Try to extract duration
            duration_match = re.search(
                r'\((\d+\.?\d*)s\)',
                output[match.end():match.end()+30]
            )
            if duration_match:
                agent.duration_s = float(duration_match.group(1))

            # Try to extract blocking agent
            blocker_match = re.search(
                r'Blocked by:.*#(\d+)',
                output[match.end():match.end()+100]
            )
            if blocker_match:
                agent.blocking_agent = int(blocker_match.group(1))

            # Try to extract API call
            api_match = re.search(
                r'API:\s*([^\n]+)',
                output[match.end():match.end()+100]
            )
            if api_match:
                agent.api_call = api_match.group(1).strip()

            agents.append(agent)

        return agents

    @staticmethod
    def parse_metrics_timeline(output: str) -> List[Tuple[str, Dict[str, Any]]]:
        """
        Parse metrics from multi-line output

        Useful for parsing output captured over time.

        Args:
            output: Complete CLI output

        Returns:
            List of (line, metrics_dict) tuples
        """

        timeline = []

        for line in output.splitlines():
            metrics = {}

            # Cost
            match = re.search(r'\$(\d+\.\d+)', line)
            if match:
                metrics['cost_usd'] = float(match.group(1))

            # Tokens
            match = re.search(r'(\d+\.?\d*)K', line)
            if match:
                metrics['tokens_k'] = float(match.group(1))

            # Duration
            duration_s = 0
            match = re.search(r'(\d+)m', line)
            if match:
                duration_s += int(match.group(1)) * 60
            match = re.search(r'(\d+)s', line)
            if match:
                duration_s += int(match.group(1))
            if duration_s > 0:
                metrics['duration_s'] = duration_s

            if metrics:
                timeline.append((line, metrics))

        return timeline

    @staticmethod
    def extract_layer_hints(output: str) -> Dict[str, bool]:
        """
        Extract layer hints from output

        Args:
            output: CLI output

        Returns:
            Dict with keys: compact_hint, expand_hint, collapse_hint, quit_hint
        """

        hints = {
            'compact_hint': False,
            'expand_hint': False,
            'collapse_hint': False,
            'quit_hint': False
        }

        if re.search(r'Press.*↵|Press.*Enter', output, re.IGNORECASE):
            hints['expand_hint'] = True

        if re.search(r'Press.*ESC|Press.*Esc', output, re.IGNORECASE):
            hints['collapse_hint'] = True

        if re.search(r'Press.*q|Press.*Q', output, re.IGNORECASE):
            hints['quit_hint'] = True

        # Check if currently compact (expand hint present, collapse hint not)
        if hints['expand_hint'] and not hints['collapse_hint']:
            hints['compact_hint'] = True

        return hints
