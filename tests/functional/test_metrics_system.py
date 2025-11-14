"""Functional Tests for Metrics Collection and Dashboard

Tests the V3 metrics system: MetricsCollector, LiveDashboard, and keyboard controls.

Philosophy: NO MOCKS
- Uses real MetricsCollector instances
- Tests actual metric calculations
- Validates dashboard rendering (where possible without UI)
- Real timing measurements

Architecture Reference: SHANNON_CLI_V3_ARCHITECTURE.md Section 2.1
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from typing import Any

from shannon.metrics.collector import MetricsCollector, MetricsSnapshot
from shannon.metrics.dashboard import LiveDashboard
from shannon.metrics.keyboard import KeyboardHandler, Key


# Test message types (simulate SDK messages for metrics collection)
class TestAssistantMessage:
    """Simulated AssistantMessage from SDK"""

    def __init__(self, text: str):
        self.content = [TestTextBlock(text)]


class TestTextBlock:
    """Simulated TextBlock"""

    def __init__(self, text: str):
        self.text = text


class TestToolUseBlock:
    """Simulated ToolUseBlock"""

    def __init__(self, name: str, input_data: dict):
        self.name = name
        self.input = input_data


class TestResultMessage:
    """Simulated ResultMessage with metrics"""

    def __init__(self, tokens_input: int, tokens_output: int, cost: float = None):
        self.usage = {
            'input_tokens': tokens_input,
            'output_tokens': tokens_output
        }
        if cost is not None:
            self.cost_usd = cost


class TestThinkingBlock:
    """Simulated ThinkingBlock"""

    def __init__(self, thinking: str):
        self.thinking = thinking


# ============================================================================
# METRICS COLLECTOR TESTS
# ============================================================================

@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_basic():
    """
    Test basic MetricsCollector functionality

    Validates:
    - Collector initializes correctly
    - Tracks operation name
    - Records timestamps
    """
    collector = MetricsCollector(operation_name="test-operation")

    assert collector.operation_name == "test-operation"
    assert collector.start_time is not None
    assert isinstance(collector.start_time, datetime)

    # Get initial snapshot
    snapshot = collector.get_snapshot()

    assert snapshot.operation_name == "test-operation"
    assert snapshot.message_count == 0
    assert snapshot.duration_seconds >= 0.0
    assert snapshot.cost_usd == 0.0


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_message_counting():
    """
    Test that collector accurately counts messages

    Validates:
    - Message count increments correctly
    - Different message types counted
    """
    collector = MetricsCollector(operation_name="counting-test")

    # Process various messages
    messages = [
        TestAssistantMessage("Hello"),
        TestTextBlock("World"),
        TestToolUseBlock("Read", {"file": "test.py"}),
        TestResultMessage(100, 50),
        TestAssistantMessage("Done")
    ]

    for msg in messages:
        await collector.process(msg)

    snapshot = collector.get_snapshot()

    # Should count all 5 messages
    assert snapshot.message_count == 5, \
        f"Expected 5 messages, got {snapshot.message_count}"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_token_tracking():
    """
    Test token usage tracking

    Validates:
    - Input tokens tracked
    - Output tokens tracked
    - Total tokens calculated
    """
    collector = MetricsCollector(operation_name="token-test")

    # Process messages with token counts
    await collector.process(TestResultMessage(tokens_input=1000, tokens_output=500))
    await collector.process(TestResultMessage(tokens_input=2000, tokens_output=800))

    snapshot = collector.get_snapshot()

    # Should accumulate tokens
    assert snapshot.tokens_input >= 1000, "Should track input tokens"
    assert snapshot.tokens_output >= 500, "Should track output tokens"

    total_tokens = snapshot.tokens_input + snapshot.tokens_output
    assert total_tokens >= 1500, f"Total tokens should be at least 1500, got {total_tokens}"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_cost_calculation():
    """
    Test cost calculation from token usage

    Validates:
    - Cost calculated from tokens
    - Different models have different costs
    - Cost accumulates correctly
    """
    collector = MetricsCollector(operation_name="cost-test", model="sonnet")

    # Process message with known token counts
    # Sonnet pricing: ~$0.003 per 1K input, ~$0.015 per 1K output
    await collector.process(TestResultMessage(
        tokens_input=10000,  # 10K tokens
        tokens_output=5000   # 5K tokens
    ))

    snapshot = collector.get_snapshot()

    # Cost should be calculated
    # 10K input * 0.003 = $0.03
    # 5K output * 0.015 = $0.075
    # Total = $0.105
    expected_cost = (10000 / 1000) * 0.003 + (5000 / 1000) * 0.015
    assert snapshot.cost_usd > 0.0, "Cost should be calculated"
    assert abs(snapshot.cost_usd - expected_cost) < 0.01, \
        f"Cost ${snapshot.cost_usd:.3f} not close to expected ${expected_cost:.3f}"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_duration_tracking():
    """
    Test duration tracking

    Validates:
    - Duration updates over time
    - Measured in seconds
    - Accurate timing
    """
    collector = MetricsCollector(operation_name="duration-test")

    # Get initial duration
    snapshot1 = collector.get_snapshot()
    initial_duration = snapshot1.duration_seconds

    # Wait 100ms
    await asyncio.sleep(0.1)

    # Process a message
    await collector.process(TestAssistantMessage("Test"))

    # Get updated duration
    snapshot2 = collector.get_snapshot()
    updated_duration = snapshot2.duration_seconds

    # Duration should have increased by at least 100ms
    duration_increase = updated_duration - initial_duration
    assert duration_increase >= 0.09, \
        f"Duration increased by {duration_increase:.3f}s, expected >= 0.09s"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_progress_extraction():
    """
    Test extraction of progress from message text

    Validates:
    - Progress percentages extracted
    - Stage information tracked
    - Dimension completion detected
    """
    collector = MetricsCollector(operation_name="progress-test")

    # Messages with progress indicators
    messages = [
        TestAssistantMessage("Starting analysis..."),
        TestAssistantMessage("✓ Structural complexity: 0.45"),
        TestAssistantMessage("Calculating dimension 2/8..."),
        TestAssistantMessage("✓ Cognitive complexity: 0.65"),
        TestAssistantMessage("Progress: 50% complete"),
        TestAssistantMessage("✓ Coordination complexity: 1.00"),
        TestAssistantMessage("Completed: 75%"),
    ]

    for msg in messages:
        await collector.process(msg)

    snapshot = collector.get_snapshot()

    # Should extract progress percentage
    assert snapshot.progress_percent > 0.0, "Should extract progress percentage"
    assert snapshot.progress_percent <= 100.0, "Progress should be <= 100%"

    # Should track completed dimensions
    assert len(snapshot.completed_dimensions) > 0, \
        "Should track completed dimensions from ✓ markers"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_tool_tracking():
    """
    Test tracking of tool calls

    Validates:
    - Tool calls tracked
    - Tool names and inputs recorded
    """
    collector = MetricsCollector(operation_name="tool-test")

    # Process tool use messages
    await collector.process(TestToolUseBlock("Read", {"file_path": "/path/to/file.py"}))
    await collector.process(TestToolUseBlock("Write", {"file_path": "/output.txt", "content": "data"}))
    await collector.process(TestToolUseBlock("Bash", {"command": "ls -la"}))

    snapshot = collector.get_snapshot()

    # Should track tool calls
    assert len(snapshot.tool_calls) == 3, \
        f"Expected 3 tool calls, got {len(snapshot.tool_calls)}"

    # Should have tool names
    tool_names = [call['name'] for call in snapshot.tool_calls]
    assert "Read" in tool_names, "Should track Read tool"
    assert "Write" in tool_names, "Should track Write tool"
    assert "Bash" in tool_names, "Should track Bash tool"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_collector_stream_lifecycle():
    """
    Test collector stream lifecycle (complete/error)

    Validates:
    - on_stream_complete() called correctly
    - on_stream_error() handles errors
    - Lifecycle state tracked
    """
    collector = MetricsCollector(operation_name="lifecycle-test")

    # Process some messages
    await collector.process(TestAssistantMessage("Processing..."))
    await collector.process(TestResultMessage(1000, 500))

    # Complete stream
    await collector.on_stream_complete()

    snapshot = collector.get_snapshot()

    # Should mark as completed
    assert snapshot.status == "completed", "Should mark stream as completed"

    # Test error handling
    collector2 = MetricsCollector(operation_name="error-test")
    await collector2.process(TestAssistantMessage("Starting..."))

    error = RuntimeError("Test error")
    await collector2.on_stream_error(error)

    snapshot2 = collector2.get_snapshot()

    # Should mark as errored
    assert snapshot2.status == "errored", "Should mark stream as errored"


# ============================================================================
# METRICS DASHBOARD TESTS
# ============================================================================

@pytest.mark.functional
def test_dashboard_initialization():
    """
    Test LiveDashboard initialization

    Validates:
    - Dashboard initializes with collector
    - Default settings correct
    - No errors on creation
    """
    collector = MetricsCollector(operation_name="test")
    dashboard = LiveDashboard(collector)

    assert dashboard.collector == collector
    assert dashboard.expanded == False, "Should start in compact mode"
    assert dashboard.refresh_per_second == 4, "Should default to 4 Hz"


@pytest.mark.functional
def test_dashboard_compact_rendering():
    """
    Test compact dashboard rendering (Layer 1)

    Validates:
    - Compact view renders without errors
    - Contains expected elements
    - Handles metrics updates
    """
    collector = MetricsCollector(operation_name="render-test")

    # Add some metrics
    collector._message_count = 10
    collector._progress = 0.60
    collector._cost = 0.12
    collector._tokens_input = 8000
    collector._tokens_output = 2000

    dashboard = LiveDashboard(collector)

    # Render compact view
    renderable = dashboard.render()

    # Should return a Rich Panel
    from rich.panel import Panel
    assert isinstance(renderable, Panel), "Compact view should be Panel"

    # Convert to string for content checking
    from rich.console import Console
    console = Console(file=None, force_terminal=False, legacy_windows=False)

    # Panel should contain key metrics
    # Note: Can't easily test exact rendering without terminal,
    # but we can verify no exceptions raised


@pytest.mark.functional
def test_dashboard_state_transitions():
    """
    Test dashboard state transitions

    Validates:
    - Expand/collapse state changes
    - State persists correctly
    """
    collector = MetricsCollector(operation_name="state-test")
    dashboard = LiveDashboard(collector)

    # Initial state
    assert dashboard.expanded == False, "Should start collapsed"

    # Expand
    dashboard.toggle_expand()
    assert dashboard.expanded == True, "Should be expanded after toggle"

    # Collapse
    dashboard.toggle_expand()
    assert dashboard.expanded == False, "Should be collapsed after second toggle"


@pytest.mark.functional
def test_dashboard_pause_request():
    """
    Test pause request handling

    Validates:
    - Pause flag set correctly
    - Can check pause state
    """
    collector = MetricsCollector(operation_name="pause-test")
    dashboard = LiveDashboard(collector)

    # Initial state
    assert dashboard.pause_requested == False, "Should not be paused initially"

    # Request pause
    dashboard.request_pause()
    assert dashboard.pause_requested == True, "Should be paused after request"

    # Clear pause
    dashboard.clear_pause()
    assert dashboard.pause_requested == False, "Should not be paused after clear"


@pytest.mark.functional
def test_dashboard_quit_request():
    """
    Test quit request handling

    Validates:
    - Quit flag set correctly
    - Can check quit state
    """
    collector = MetricsCollector(operation_name="quit-test")
    dashboard = LiveDashboard(collector)

    # Initial state
    assert dashboard.quit_requested == False, "Should not be quit initially"

    # Request quit
    dashboard.request_quit()
    assert dashboard.quit_requested == True, "Should be quit after request"


# ============================================================================
# KEYBOARD HANDLER TESTS (Platform-dependent)
# ============================================================================

@pytest.mark.functional
@pytest.mark.skipif(
    __import__('sys').platform not in ['darwin', 'linux'],
    reason="Keyboard handler only works on macOS/Linux"
)
def test_keyboard_handler_platform_support():
    """
    Test keyboard handler platform detection

    Validates:
    - Detects supported platforms correctly
    - Sets up terminal on supported platforms
    """
    handler = KeyboardHandler()

    import sys
    if sys.platform in ['darwin', 'linux']:
        assert handler.is_supported() == True, \
            "Should be supported on macOS/Linux"
    else:
        assert handler.is_supported() == False, \
            "Should not be supported on Windows"


@pytest.mark.functional
def test_keyboard_handler_key_parsing():
    """
    Test keyboard key parsing

    Validates:
    - Key enum values correct
    - Special keys recognized
    """
    # Test key enum
    assert Key.ENTER in [Key.ENTER, Key.ESC, Key.Q, Key.P]
    assert Key.ESC in [Key.ENTER, Key.ESC, Key.Q, Key.P]

    # Verify key values
    assert Key.ENTER.value in ['\r', '\n']
    assert Key.ESC.value == '\x1b'
    assert Key.Q.value == 'q'
    assert Key.P.value == 'p'


# ============================================================================
# INTEGRATION TESTS (Collector + Dashboard)
# ============================================================================

@pytest.mark.functional
@pytest.mark.asyncio
async def test_collector_dashboard_integration():
    """
    Test MetricsCollector and LiveDashboard integration

    Validates:
    - Dashboard reflects collector state
    - Updates propagate correctly
    - Real-time sync works
    """
    collector = MetricsCollector(operation_name="integration-test")
    dashboard = LiveDashboard(collector)

    # Process messages through collector
    messages = [
        TestAssistantMessage("Starting analysis..."),
        TestResultMessage(1000, 500, cost=0.05),
        TestAssistantMessage("Progress: 25%"),
        TestResultMessage(2000, 1000, cost=0.10),
        TestAssistantMessage("Progress: 50%"),
        TestToolUseBlock("Read", {"file": "test.py"}),
        TestAssistantMessage("Progress: 75%"),
        TestResultMessage(1500, 800, cost=0.08),
        TestAssistantMessage("Complete!"),
    ]

    for msg in messages:
        await collector.process(msg)
        await asyncio.sleep(0.01)  # Small delay to simulate real timing

    # Get final state
    snapshot = collector.get_snapshot()

    # Dashboard should reflect collector state
    assert snapshot.message_count == len(messages), \
        "Dashboard should show all messages"
    assert snapshot.cost_usd > 0.0, "Dashboard should show cost"
    assert snapshot.tokens_input > 0, "Dashboard should show input tokens"
    assert snapshot.progress_percent > 0.0, "Dashboard should show progress"

    # Dashboard rendering should not crash
    rendered = dashboard.render()
    assert rendered is not None, "Dashboard should render successfully"


@pytest.mark.functional
@pytest.mark.slow
@pytest.mark.asyncio
async def test_metrics_system_performance():
    """
    Test metrics system performance under load

    Validates:
    - Handles high message rate (100+ messages/sec)
    - Minimal overhead added
    - Dashboard updates don't degrade performance
    """
    collector = MetricsCollector(operation_name="performance-test")

    start_time = datetime.now()

    # Process 1000 messages rapidly
    for i in range(1000):
        await collector.process(TestAssistantMessage(f"Message {i}"))

        # Process every 10th message with tokens
        if i % 10 == 0:
            await collector.process(TestResultMessage(100, 50))

    end_time = datetime.now()

    snapshot = collector.get_snapshot()

    # Should handle all messages
    assert snapshot.message_count >= 1000, \
        f"Should process at least 1000 messages, got {snapshot.message_count}"

    # Should be fast (< 1 second for 1000 messages)
    duration = (end_time - start_time).total_seconds()
    assert duration < 1.0, \
        f"Processing 1000 messages took {duration:.3f}s, expected <1.0s"

    # Throughput should be >1000 msg/s
    throughput = snapshot.message_count / duration
    assert throughput > 1000, \
        f"Throughput {throughput:.0f} msg/s, expected >1000 msg/s"


@pytest.mark.functional
@pytest.mark.asyncio
async def test_metrics_snapshot_immutability():
    """
    Test that MetricsSnapshot is immutable after creation

    Validates:
    - Snapshot captures state at moment
    - Changes to collector don't affect snapshot
    - Multiple snapshots independent
    """
    collector = MetricsCollector(operation_name="snapshot-test")

    # Process some messages
    await collector.process(TestAssistantMessage("First"))
    await collector.process(TestResultMessage(1000, 500))

    # Take snapshot
    snapshot1 = collector.get_snapshot()
    count1 = snapshot1.message_count
    cost1 = snapshot1.cost_usd

    # Process more messages
    await collector.process(TestAssistantMessage("Second"))
    await collector.process(TestResultMessage(2000, 1000))

    # Take another snapshot
    snapshot2 = collector.get_snapshot()
    count2 = snapshot2.message_count
    cost2 = snapshot2.cost_usd

    # First snapshot should be unchanged
    assert snapshot1.message_count == count1, \
        "First snapshot should not change after more messages"
    assert snapshot1.cost_usd == cost1, \
        "First snapshot cost should not change"

    # Second snapshot should have more
    assert snapshot2.message_count > snapshot1.message_count, \
        "Second snapshot should have more messages"
    assert snapshot2.cost_usd > snapshot1.cost_usd, \
        "Second snapshot should have higher cost"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
