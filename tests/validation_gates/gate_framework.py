"""
tests/validation_gates/gate_framework.py

Framework for implementing validation gates with consistent structure.
"""

import asyncio
from typing import List, Dict, Any, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum


class TestStatus(Enum):
    """Test result status"""
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    ERROR = "error"


@dataclass
class TestResult:
    """Result of one CLI functional test"""

    test_name: str                        # Test function name
    status: TestStatus                    # Pass/fail/skip/error
    message: str                          # Description of result
    details: Dict[str, Any] = field(default_factory=dict)  # Additional data
    duration_seconds: float = 0.0         # Test execution time

    @property
    def passed(self) -> bool:
        return self.status == TestStatus.PASSED

    @property
    def skipped(self) -> bool:
        return self.status == TestStatus.SKIPPED

    @property
    def failed(self) -> bool:
        return self.status in [TestStatus.FAILED, TestStatus.ERROR]


@dataclass
class GateResult:
    """Result of running validation gate"""

    phase: int                            # Wave/phase number
    gate_type: str                        # 'entry' or 'exit'
    passed: bool                          # Overall pass/fail
    total_tests: int                      # Total test count
    passed_tests: int                     # Passed test count
    failed_tests: int                     # Failed test count
    skipped_tests: int                    # Skipped test count
    pass_rate: float                      # Pass rate (0.0-1.0)
    test_results: List[TestResult]        # Individual test results
    duration_seconds: float = 0.0         # Total gate execution time

    def display(self):
        """Display gate result to console"""

        status_icon = '✅' if self.passed else '❌'
        status_text = 'PASSED' if self.passed else 'FAILED'

        print(f"\n{status_icon} Phase {self.phase} {self.gate_type.upper()} GATE: {status_text}")
        print(f"   Tests: {self.passed_tests}/{self.total_tests - self.skipped_tests} passed")
        print(f"   Duration: {self.duration_seconds:.1f}s")

        if self.skipped_tests > 0:
            print(f"   Skipped: {self.skipped_tests}")

        if self.failed_tests > 0:
            print(f"\n   Failures:")
            for result in self.test_results:
                if result.failed:
                    print(f"   • {result.test_name}: {result.message}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            'phase': self.phase,
            'gate_type': self.gate_type,
            'passed': self.passed,
            'total_tests': self.total_tests,
            'passed_tests': self.passed_tests,
            'failed_tests': self.failed_tests,
            'skipped_tests': self.skipped_tests,
            'pass_rate': self.pass_rate,
            'duration_seconds': self.duration_seconds,
            'test_results': [
                {
                    'test_name': r.test_name,
                    'status': r.status.value,
                    'message': r.message,
                    'details': r.details,
                    'duration_seconds': r.duration_seconds
                }
                for r in self.test_results
            ]
        }


class ValidationGate:
    """
    Base class for validation gates

    Subclass to implement entry/exit gates for each phase.
    """

    def __init__(self, phase: int, gate_type: str):
        self.phase = phase
        self.gate_type = gate_type
        self.tests: List[Callable[[], Awaitable[TestResult]]] = []

    def add_test(self, test_func: Callable[[], Awaitable[TestResult]]):
        """Add test to gate"""
        self.tests.append(test_func)

    async def run_all_tests(self) -> GateResult:
        """
        Run all tests in gate

        Returns:
            GateResult with pass/fail and individual test results
        """

        import time

        start_time = time.time()
        results = []

        for test_func in self.tests:
            try:
                result = await test_func()
                results.append(result)

                if result.passed:
                    print(f"✅ PASS: {result.test_name}")
                elif result.skipped:
                    print(f"⏭️  SKIP: {result.test_name}")
                else:
                    print(f"❌ FAIL: {result.test_name}")
                    print(f"   {result.message}")

            except Exception as e:
                # Test crashed
                results.append(TestResult(
                    test_name=test_func.__name__,
                    status=TestStatus.ERROR,
                    message=f"Test crashed: {str(e)}",
                    details={'exception_type': type(e).__name__}
                ))
                print(f"💥 ERROR: {test_func.__name__}")
                print(f"   {str(e)}")

        # Calculate statistics
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if r.failed)
        skipped = sum(1 for r in results if r.skipped)
        total = len(results)

        testable = total - skipped
        pass_rate = (passed / testable) if testable > 0 else 0.0

        # Gate passes if all non-skipped tests pass
        gate_passed = (failed == 0)

        duration = time.time() - start_time

        return GateResult(
            phase=self.phase,
            gate_type=self.gate_type,
            passed=gate_passed,
            total_tests=total,
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            pass_rate=pass_rate,
            test_results=results,
            duration_seconds=duration
        )


class GateChecker:
    """
    CLI gate checker - runs validation gates

    Usage:
        checker = GateChecker()
        result = await checker.check_phase(1)
    """

    def __init__(self):
        self.gates: Dict[int, ValidationGate] = {}

    def register_gate(self, gate: ValidationGate):
        """Register a validation gate"""
        self.gates[gate.phase] = gate

    async def check_phase(self, phase: int) -> GateResult:
        """
        Run all tests for one phase

        Args:
            phase: Phase number to check

        Returns:
            GateResult with pass/fail
        """

        if phase not in self.gates:
            raise ValueError(f"No gate registered for phase {phase}")

        gate = self.gates[phase]

        print(f"\n┌─────────────────────────────────────┐")
        print(f"│ Phase {phase} {gate.gate_type.title()} Gate: CLI Testing │")
        print(f"└─────────────────────────────────────┘\n")

        result = await gate.run_all_tests()
        result.display()

        return result

    async def check_all_phases(self) -> List[GateResult]:
        """
        Run all implemented phase gates

        Returns:
            List of GateResult objects
        """

        results = []

        for phase in sorted(self.gates.keys()):
            result = await self.check_phase(phase)
            results.append(result)

            # Stop at first failure
            if not result.passed:
                print(f"\n⚠️  Phase {phase} gate failed - subsequent phases blocked")
                break

        # Summary
        self._display_summary(results)

        return results

    def _display_summary(self, results: List[GateResult]):
        """Display summary of all gate results"""

        print(f"\n╔═══════════════════════════════════════════════════════╗")
        print(f"║ Shannon V3 Validation Gates Summary                  ║")
        print(f"╠═══════════════════════════════════════════════════════╣")

        for result in results:
            status_icon = '✅' if result.passed else '❌'
            print(f"║ Phase {result.phase}: {status_icon} {result.passed_tests}/{result.total_tests - result.skipped_tests} tests passed")

        print(f"╠═══════════════════════════════════════════════════════╣")

        total_passed = sum(r.passed_tests for r in results)
        total_tests = sum(r.total_tests - r.skipped_tests for r in results)
        overall_passed = all(r.passed for r in results)

        print(f"║ Overall: {total_passed}/{total_tests} tests passed")
        print(f"║ Status: {'✅ ALL GATES PASSED' if overall_passed else '❌ GATES FAILED'}")
        print(f"╚═══════════════════════════════════════════════════════╝\n")
