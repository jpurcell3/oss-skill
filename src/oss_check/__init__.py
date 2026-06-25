"""
OSS Compliance Skill Library

A standalone library for OSS compliance scanning that can be used independently
in development environments like Devin, Claude, or other AI assistants without
requiring the full web application installation.

This library provides:
- Repository scanning capabilities
- Compliance analysis
- Report generation
- Configuration management
- Integration with GitHub, Jenkins, and Artifactory
"""

__version__ = "1.0.0"
__author__ = "Development Team"

from .scanner import ComplianceScanner
from .config import ComplianceConfig
from .reporter import ComplianceReporter

__all__ = [
    "ComplianceScanner",
    "ComplianceConfig", 
    "ComplianceReporter",
]