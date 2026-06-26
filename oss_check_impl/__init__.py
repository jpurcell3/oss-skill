"""
OSS Check Skill - Open Source Software Compliance Scanner

A lightweight, high-performance skill for scanning repositories to ensure
open source dependencies are sourced through approved Artifactory virtual
repositories.
"""

__version__ = "1.0.0"
__author__ = "jpurcell"

from .core.scanner import OSSScannerOrchestrator
from .utils.config import ConfigLoader

__all__ = [
    "OSSScannerOrchestrator",
    "ConfigLoader",
]
