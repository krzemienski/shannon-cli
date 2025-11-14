"""
Validation Gates Framework

Wave-based validation gates for Shannon V3 implementation.
"""

from .gate_framework import (
    TestStatus,
    TestResult,
    GateResult,
    ValidationGate,
    GateChecker
)

__all__ = [
    'TestStatus',
    'TestResult',
    'GateResult',
    'ValidationGate',
    'GateChecker',
]
