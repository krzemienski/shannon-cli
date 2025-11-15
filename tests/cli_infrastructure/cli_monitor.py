"""
tests/cli_infrastructure/cli_monitor.py

Core utility for executing Shannon CLI commands and monitoring output.
"""

import subprocess
import time
import re
import asyncio
from typing import List, Dict, Any, Optional, Literal, Tuple
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class OutputSnapshot:
    """
    Single snapshot of CLI output at a point in time

    Captured at regular intervals (default 250ms) to track telemetry changes.
    """

    timestamp: float              # Unix timestamp
    elapsed_seconds: float        # Seconds since command start
    output: str                   # Recent output (last N lines)
    full_output: str             # Complete output so far
    snapshot_number: int         # Sequence number
    is_final: bool = False       # True for final snapshot after completion

    def extract_state(self) -> Optional[str]:
        """
        Extract operational state from output

        Looks for state indicators in output:
        - WAITING_API: Waiting for API response
        - WAITING_DEPENDENCY: Waiting for another agent
        - WAITING: Generic waiting state
        - ACTIVE: Currently executing
        - COMPLETE: Finished successfully
        - FAILED: Error occurred

        Returns:
            State string or None if no state detected
        """

        state_patterns = {
            'WAITING_API': r'WAITING.*API|API.*WAITING|WAITING_API',
            'WAITING_DEPENDENCY': r'WAITING.*DEPENDENCY|WAITING_DEPENDENCY|Blocked by',
            'WAITING': r'WAITING|Waiting',
            'ACTIVE': r'ACTIVE|Running|Processing',
            'COMPLETE': r'COMPLETE|✓|Done|Finished',
            'FAILED': r'FAILED|✗|Error|Failed'
        }

        # Check in priority order
        for state, pattern in state_patterns.items():
            if re.search(pattern, self.output, re.IGNORECASE):
                return state

        return None

    def extract_progress(self) -> Optional[float]:
        """
        Extract progress percentage from output

        Recognizes formats:
        - "42%"
        - "Progress: 42%"
        - "▓▓▓▓░░░░░░ 42%"
        - Progress bars: "▓▓▓▓░░░░░░"

        Returns:
            Progress as float 0.0-1.0, or None if not found
        """

        # Method 1: Direct percentage "42%"
        match = re.search(r'(\d+)%', self.output)
        if match:
            return float(match.group(1)) / 100.0

        # Method 2: Progress bar blocks
        match = re.search(r'(▓+)(░+)', self.output)
        if match:
            filled = len(match.group(1))
            empty = len(match.group(2))
            total = filled + empty
            return filled / total if total > 0 else None

        # Method 3: Fraction "3/10"
        match = re.search(r'(\d+)/(\d+)', self.output)
        if match:
            current = int(match.group(1))
            total = int(match.group(2))
            return current / total if total > 0 else None

        return None

    def extract_metrics(self) -> Dict[str, Any]:
        """
        Extract cost/tokens/duration metrics from output

        Recognizes formats:
        - Cost: "$2.34" or "$0.12"
        - Tokens: "8.2K" or "8200"
        - Duration: "45s" or "2m 15s" or "1h 30m"

        Returns:
            Dictionary with keys: cost_usd, tokens_thousands, duration_seconds
        """

        metrics = {}

        # Extract cost: "$2.34"
        match = re.search(r'\$(\d+\.\d+)', self.output)
        if match:
            metrics['cost_usd'] = float(match.group(1))

        # Extract tokens: "8.2K" or "8200"
        match = re.search(r'(\d+\.?\d*)K\s*tokens?', self.output, re.IGNORECASE)
        if match:
            metrics['tokens_thousands'] = float(match.group(1))
        else:
            # Try raw number
            match = re.search(r'(\d+)\s*tokens?', self.output, re.IGNORECASE)
            if match:
                metrics['tokens_thousands'] = float(match.group(1)) / 1000.0

        # Extract duration: "2m 15s" or "45s" or "1h 30m"
        duration_seconds = 0

        # Hours
        match = re.search(r'(\d+)h', self.output)
        if match:
            duration_seconds += int(match.group(1)) * 3600

        # Minutes
        match = re.search(r'(\d+)m', self.output)
        if match:
            duration_seconds += int(match.group(1)) * 60

        # Seconds
        match = re.search(r'(\d+)s', self.output)
        if match:
            duration_seconds += int(match.group(1))

        if duration_seconds > 0:
            metrics['duration_seconds'] = duration_seconds

        return metrics

    def extract_agent_states(self) -> List[Dict[str, Any]]:
        """
        Extract agent states from wave telemetry

        Recognizes format:
        "#1 backend-builder 67% WAITING_API (12.4s)"

        Returns:
            List of dicts with keys: agent_number, agent_type, progress, state, duration
        """

        agents = []

        # Pattern: "#1 backend-builder 67% WAITING_API (12.4s)"
        pattern = r'#(\d+)\s+(\S+)\s+(\d+)%\s+(\w+)'

        for match in re.finditer(pattern, self.output):
            agent_info = {
                'agent_number': int(match.group(1)),
                'agent_type': match.group(2),
                'progress': int(match.group(3)) / 100.0,
                'state': match.group(4)
            }

            # Try to extract duration if present
            duration_match = re.search(r'\((\d+\.?\d*)s\)',
                                     self.output[match.end():match.end()+20])
            if duration_match:
                agent_info['duration_seconds'] = float(duration_match.group(1))

            agents.append(agent_info)

        return agents


@dataclass
class PerformanceSample:
    """One performance measurement sample"""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    num_threads: int
    open_files: int


class PerformanceMetrics:
    """
    Monitor resource usage during CLI execution

    Samples CPU, memory, threads, open files every 1 second.
    """

    def __init__(self):
        self.pid: Optional[int] = None
        self.samples: List[PerformanceSample] = []
        self.monitor_task: Optional[asyncio.Task] = None

    def start_monitoring(self, pid: int):
        """Start monitoring process"""
        self.pid = pid
        # Note: Monitoring would be started in async context

    async def _monitor_loop(self):
        """Continuous monitoring loop"""
        try:
            import psutil
            process = psutil.Process(self.pid)

            while process.is_running():
                try:
                    sample = PerformanceSample(
                        timestamp=time.time(),
                        cpu_percent=process.cpu_percent(interval=0.1),
                        memory_mb=process.memory_info().rss / (1024 * 1024),
                        num_threads=process.num_threads(),
                        open_files=len(process.open_files())
                    )

                    self.samples.append(sample)
                    await asyncio.sleep(1.0)

                except Exception:
                    break

        except Exception:
            pass

    def stop_monitoring(self):
        """Stop monitoring"""
        if self.monitor_task:
            self.monitor_task.cancel()

    def get_peak_memory_mb(self) -> float:
        """Get peak memory usage"""
        return max(s.memory_mb for s in self.samples) if self.samples else 0.0

    def get_avg_cpu_percent(self) -> float:
        """Get average CPU usage"""
        return sum(s.cpu_percent for s in self.samples) / len(self.samples) if self.samples else 0.0

    def get_summary(self) -> Dict[str, Any]:
        """Get performance summary"""
        if not self.samples:
            return {}

        return {
            'peak_memory_mb': self.get_peak_memory_mb(),
            'avg_cpu_percent': self.get_avg_cpu_percent(),
            'max_threads': max(s.num_threads for s in self.samples),
            'max_open_files': max(s.open_files for s in self.samples),
            'sample_count': len(self.samples)
        }


@dataclass
class MonitorResult:
    """
    Result of monitoring CLI command execution

    Contains all captured snapshots, performance metrics, and analysis methods.
    """

    command: str                          # Command executed
    exit_code: int                        # Exit code (0 = success)
    snapshots: List[OutputSnapshot]       # All captured snapshots
    performance: PerformanceMetrics      # Performance metrics
    duration_seconds: float              # Total duration
    output_lines: int                    # Total output lines
    total_output: str                    # Complete output text

    def validate_success(self) -> bool:
        """Check if command succeeded"""
        return self.exit_code == 0

    def validate_completion(self) -> bool:
        """Check if command completed (even if with error)"""
        return len(self.snapshots) > 0 and self.snapshots[-1].is_final

    def get_state_timeline(self) -> List[Tuple[float, str]]:
        """
        Get timeline of state transitions

        Returns:
            List of (elapsed_seconds, state) tuples
        """
        timeline = []
        for snapshot in self.snapshots:
            state = snapshot.extract_state()
            if state:
                timeline.append((snapshot.elapsed_seconds, state))

        return timeline

    def get_progress_timeline(self) -> List[Tuple[float, float]]:
        """
        Get timeline of progress values

        Returns:
            List of (elapsed_seconds, progress) tuples
        """
        timeline = []
        for snapshot in self.snapshots:
            progress = snapshot.extract_progress()
            if progress is not None:
                timeline.append((snapshot.elapsed_seconds, progress))

        return timeline

    def get_metrics_timeline(self) -> List[Tuple[float, Dict[str, Any]]]:
        """
        Get timeline of metrics

        Returns:
            List of (elapsed_seconds, metrics_dict) tuples
        """
        timeline = []
        for snapshot in self.snapshots:
            metrics = snapshot.extract_metrics()
            if metrics:
                timeline.append((snapshot.elapsed_seconds, metrics))

        return timeline

    def validate_monotonic_progress(self) -> bool:
        """
        Verify progress never decreases

        Returns:
            True if progress is monotonic (or no progress data)
        """
        timeline = self.get_progress_timeline()
        if len(timeline) < 2:
            return True

        progress_values = [p for _, p in timeline]
        return all(
            progress_values[i] <= progress_values[i+1]
            for i in range(len(progress_values) - 1)
        )

    def validate_state_transitions(self, expected_sequence: List[str]) -> bool:
        """
        Verify states appear in expected order

        Args:
            expected_sequence: List of states in expected order
                Example: ['WAITING', 'ACTIVE', 'COMPLETE']

        Returns:
            True if states appear in expected order
        """
        timeline = self.get_state_timeline()
        states = [state for _, state in timeline]

        # Remove consecutive duplicates
        unique_states = []
        for state in states:
            if not unique_states or unique_states[-1] != state:
                unique_states.append(state)

        # Check if expected states appear in order
        state_idx = 0
        for expected_state in expected_sequence:
            try:
                idx = unique_states.index(expected_state, state_idx)
                state_idx = idx + 1
            except ValueError:
                return False

        return True

    def get_summary(self) -> Dict[str, Any]:
        """Get execution summary"""
        return {
            'command': self.command,
            'exit_code': self.exit_code,
            'success': self.validate_success(),
            'duration_seconds': self.duration_seconds,
            'output_lines': self.output_lines,
            'snapshot_count': len(self.snapshots),
            'state_timeline': self.get_state_timeline(),
            'progress_timeline': self.get_progress_timeline(),
            'final_metrics': self.snapshots[-1].extract_metrics() if self.snapshots else {},
            'performance': self.performance.get_summary()
        }


class CLIMonitor:
    """
    Execute Shannon CLI commands and monitor output streams

    Core testing utility for CLI functional tests.
    Captures output at regular intervals to validate telemetry behavior.

    Usage:
        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', 'spec.md'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        assert result.validate_success()
        assert result.validate_monotonic_progress()
    """

    def __init__(self):
        self.snapshots: List[OutputSnapshot] = []
        self.performance_metrics = PerformanceMetrics()

    def run_and_monitor(
        self,
        command: List[str],
        snapshot_interval_ms: int = 250,
        timeout_seconds: int = 300,
        capture_mode: Literal['stream', 'buffer'] = 'stream',
        cwd: Optional[str] = None,
        track_performance: bool = False
    ) -> MonitorResult:
        """
        Execute CLI command and monitor output

        Args:
            command: CLI command as list (e.g., ['shannon', 'analyze', 'spec.md'])
            snapshot_interval_ms: Frequency to capture output snapshots (default 250ms = 4 Hz)
            timeout_seconds: Maximum execution time (default 300s = 5 minutes)
            capture_mode:
                - 'stream': Capture output in real-time (for telemetry validation)
                - 'buffer': Wait for completion (for result validation)
            cwd: Working directory for command execution
            track_performance: Whether to track CPU/memory (requires psutil)

        Returns:
            MonitorResult with exit_code, snapshots, performance_metrics

        Raises:
            TimeoutError: If command exceeds timeout
        """

        # Reset state
        self.snapshots = []
        self.performance_metrics = PerformanceMetrics()

        # Start process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # Merge stderr into stdout
            text=True,
            bufsize=1,  # Line-buffered for streaming
            cwd=cwd
        )

        # Start performance monitoring if requested
        if track_performance:
            self.performance_metrics.start_monitoring(process.pid)

        start_time = time.time()
        output_buffer = []

        # Snapshot timer
        last_snapshot_time = start_time
        snapshot_count = 0

        try:
            # Stream output
            while True:
                # Read line with timeout
                line = process.stdout.readline()

                if not line:
                    # Process ended
                    if process.poll() is not None:
                        break
                    continue

                now = time.time()
                output_buffer.append(line)

                # Take snapshot at specified interval
                if (now - last_snapshot_time) >= (snapshot_interval_ms / 1000):
                    snapshot = OutputSnapshot(
                        timestamp=now,
                        elapsed_seconds=now - start_time,
                        output=''.join(output_buffer[-50:]),  # Last 50 lines
                        full_output=''.join(output_buffer),
                        snapshot_number=snapshot_count
                    )

                    self.snapshots.append(snapshot)
                    last_snapshot_time = now
                    snapshot_count += 1

                # Check timeout
                if (now - start_time) > timeout_seconds:
                    process.kill()
                    raise TimeoutError(
                        f"Command exceeded {timeout_seconds}s timeout"
                    )

            # Wait for completion
            returncode = process.wait()

            # Final snapshot
            final_snapshot = OutputSnapshot(
                timestamp=time.time(),
                elapsed_seconds=time.time() - start_time,
                output=''.join(output_buffer[-50:]),
                full_output=''.join(output_buffer),
                snapshot_number=snapshot_count,
                is_final=True
            )
            self.snapshots.append(final_snapshot)

        finally:
            # Stop performance monitoring
            self.performance_metrics.stop_monitoring()

        return MonitorResult(
            command=' '.join(command),
            exit_code=returncode,
            snapshots=self.snapshots,
            performance=self.performance_metrics,
            duration_seconds=time.time() - start_time,
            output_lines=len(output_buffer),
            total_output=''.join(output_buffer)
        )
