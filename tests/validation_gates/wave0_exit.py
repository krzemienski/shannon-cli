"""
Wave 0 Exit Gate: Testing Infrastructure Validation

Validates that all testing infrastructure components work correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli_infrastructure.cli_monitor import CLIMonitor, OutputSnapshot
from cli_infrastructure.output_parser import OutputParser
from validation_gates.gate_framework import TestResult, TestStatus, ValidationGate


async def test_cli_monitor_basic_execution() -> TestResult:
    """Test CLIMonitor can execute commands"""

    try:
        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['echo', 'Hello World'],
            snapshot_interval_ms=100,
            timeout_seconds=5
        )

        assert result.validate_success(), "Command should succeed"
        assert 'Hello World' in result.total_output, "Output should contain 'Hello World'"
        assert len(result.snapshots) >= 1, "Should capture at least 1 snapshot"

        return TestResult(
            test_name="test_cli_monitor_basic_execution",
            status=TestStatus.PASSED,
            message="CLIMonitor executes commands successfully",
            duration_seconds=result.duration_seconds
        )
    except Exception as e:
        return TestResult(
            test_name="test_cli_monitor_basic_execution",
            status=TestStatus.FAILED,
            message=f"Failed: {str(e)}"
        )


async def test_output_parser_extracts_metrics() -> TestResult:
    """Test OutputParser can extract data"""

    try:
        output = "$0.12 | 8.2K tokens | 45s"

        parser = OutputParser()
        state = parser.parse_dashboard(output)

        assert state.cost_usd == 0.12, f"Expected cost 0.12, got {state.cost_usd}"
        assert state.tokens_k == 8.2, f"Expected tokens 8.2K, got {state.tokens_k}"
        assert state.duration_s == 45, f"Expected duration 45s, got {state.duration_s}"

        return TestResult(
            test_name="test_output_parser_extracts_metrics",
            status=TestStatus.PASSED,
            message="OutputParser extracts metrics correctly"
        )
    except Exception as e:
        return TestResult(
            test_name="test_output_parser_extracts_metrics",
            status=TestStatus.FAILED,
            message=f"Failed: {str(e)}"
        )


async def test_output_snapshot_extracts_state() -> TestResult:
    """Test OutputSnapshot can extract operational states"""

    try:
        snapshot = OutputSnapshot(
            timestamp=0.0,
            elapsed_seconds=0.0,
            output="Status: WAITING_API for response",
            full_output="Status: WAITING_API for response",
            snapshot_number=0
        )

        state = snapshot.extract_state()
        assert state == 'WAITING_API', f"Expected WAITING_API, got {state}"

        return TestResult(
            test_name="test_output_snapshot_extracts_state",
            status=TestStatus.PASSED,
            message="OutputSnapshot extracts states correctly"
        )
    except Exception as e:
        return TestResult(
            test_name="test_output_snapshot_extracts_state",
            status=TestStatus.FAILED,
            message=f"Failed: {str(e)}"
        )


async def test_output_snapshot_extracts_progress() -> TestResult:
    """Test OutputSnapshot can extract progress"""

    try:
        snapshot = OutputSnapshot(
            timestamp=0.0,
            elapsed_seconds=0.0,
            output="Progress: 42%",
            full_output="Progress: 42%",
            snapshot_number=0
        )

        progress = snapshot.extract_progress()
        assert progress == 0.42, f"Expected 0.42, got {progress}"

        return TestResult(
            test_name="test_output_snapshot_extracts_progress",
            status=TestStatus.PASSED,
            message="OutputSnapshot extracts progress correctly"
        )
    except Exception as e:
        return TestResult(
            test_name="test_output_snapshot_extracts_progress",
            status=TestStatus.FAILED,
            message=f"Failed: {str(e)}"
        )


async def test_validation_gate_framework() -> TestResult:
    """Test ValidationGate framework"""

    try:
        gate = ValidationGate(phase=0, gate_type='test')

        async def dummy_test():
            return TestResult(
                test_name="dummy",
                status=TestStatus.PASSED,
                message="Dummy test"
            )

        gate.add_test(dummy_test)
        result = await gate.run_all_tests()

        assert result.passed, "Gate should pass"
        assert result.total_tests == 1, f"Expected 1 test, got {result.total_tests}"

        return TestResult(
            test_name="test_validation_gate_framework",
            status=TestStatus.PASSED,
            message="ValidationGate framework functional"
        )
    except Exception as e:
        return TestResult(
            test_name="test_validation_gate_framework",
            status=TestStatus.FAILED,
            message=f"Failed: {str(e)}"
        )


async def run_wave0_exit_gate():
    """Run Wave 0 exit gate validation"""

    gate = ValidationGate(phase=0, gate_type='exit')

    # Add all tests
    gate.add_test(test_cli_monitor_basic_execution)
    gate.add_test(test_output_parser_extracts_metrics)
    gate.add_test(test_output_snapshot_extracts_state)
    gate.add_test(test_output_snapshot_extracts_progress)
    gate.add_test(test_validation_gate_framework)

    # Run all tests
    result = await gate.run_all_tests()
    result.display()

    return result


if __name__ == "__main__":
    import asyncio

    print("\n" + "="*60)
    print("Shannon V3 - Wave 0 Exit Gate")
    print("Testing Infrastructure Validation")
    print("="*60)

    result = asyncio.run(run_wave0_exit_gate())

    if result.passed:
        print("\n✅ Wave 0 COMPLETE - Testing infrastructure ready!")
        sys.exit(0)
    else:
        print("\n❌ Wave 0 FAILED - Fix issues before proceeding")
        sys.exit(1)
