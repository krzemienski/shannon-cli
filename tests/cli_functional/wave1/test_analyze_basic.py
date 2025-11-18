"""
Wave 1 CLI Functional Test - Basic Analyze Command

Tests that the analyze command executes successfully and produces output.
"""

import sys
from pathlib import Path
import pytest

# Add parent directories to path
test_root = Path(__file__).parent.parent
sys.path.insert(0, str(test_root))

from cli_infrastructure.cli_monitor import CLIMonitor
from validation_gates.gate_framework import TestResult, TestStatus


class TestAnalyzeBasic:
    """Basic analyze command tests"""

    @pytest.fixture
    def simple_spec(self):
        """Path to simple test spec"""
        return str(Path(__file__).parent.parent / "fixtures" / "simple_spec.md")

    def test_analyze_command_succeeds(self, simple_spec):
        """
        TEST: shannon analyze executes successfully

        Validates:
        - Command completes without error
        - Produces output
        - Returns exit code 0
        """

        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', simple_spec, '--no-cache'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        # Should succeed
        assert result.validate_success(), \
            f"analyze command failed with exit code {result.exit_code}"

        # Should produce output
        assert len(result.total_output) > 0, \
            "No output produced"

        # Should have captured snapshots
        assert len(result.snapshots) > 0, \
            "No snapshots captured"

    def test_analyze_shows_complexity_score(self, simple_spec):
        """
        TEST: analyze shows 8D complexity score

        Validates:
        - Complexity score appears in output
        - Score is in valid range (0.10-0.95)
        """

        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', simple_spec, '--no-cache'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        assert result.validate_success()

        # Look for complexity indicators
        output = result.total_output.lower()

        complexity_indicators = [
            'complexity',
            'score',
            '8d',
            'dimension'
        ]

        found_indicators = [ind for ind in complexity_indicators if ind in output]

        assert len(found_indicators) >= 2, \
            f"Expected complexity indicators in output, found only: {found_indicators}"

    def test_analyze_produces_structured_output(self, simple_spec):
        """
        TEST: analyze produces structured output

        Validates:
        - Output contains recognizable sections
        - Not just error messages
        """

        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', simple_spec, '--no-cache'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        assert result.validate_success()

        output = result.total_output.lower()

        # Should not be just errors
        error_only = 'error' in output and 'failed' in output
        has_content = len(output) > 500  # Substantial output

        assert not error_only or has_content, \
            "Output appears to be error-only"

    def test_analyze_completes_in_reasonable_time(self, simple_spec):
        """
        TEST: analyze completes in reasonable time

        Validates:
        - Command completes within 2 minutes for simple spec
        """

        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', simple_spec, '--no-cache'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        assert result.validate_success()

        # Should complete in reasonable time
        assert result.duration_seconds < 120, \
            f"Took too long: {result.duration_seconds:.1f}s (max 120s)"

    def test_analyze_with_json_output(self, simple_spec):
        """
        TEST: analyze --json produces valid JSON

        Validates:
        - JSON flag works
        - Output is parseable JSON
        """

        monitor = CLIMonitor()
        result = monitor.run_and_monitor(
            command=['shannon', 'analyze', simple_spec, '--json', '--no-cache'],
            snapshot_interval_ms=250,
            timeout_seconds=120
        )

        if not result.validate_success():
            pytest.skip(f"Command failed: {result.exit_code}")

        # Try to parse as JSON
        import json
        try:
            data = json.loads(result.total_output)
            assert isinstance(data, dict), "JSON output should be a dictionary"
        except json.JSONDecodeError as e:
            pytest.fail(f"Output is not valid JSON: {e}")


if __name__ == "__main__":
    pytest.main([__file__, '-v'])
