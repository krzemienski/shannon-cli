"""
CLI Testing Infrastructure

Utilities for executing and monitoring Shannon CLI commands.
"""

from .cli_monitor import CLIMonitor, MonitorResult, OutputSnapshot, PerformanceMetrics

__all__ = [
    'CLIMonitor',
    'MonitorResult',
    'OutputSnapshot',
    'PerformanceMetrics',
]
