"""Base class for ecosystem-specific scanning."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..core.models import Component


class BaseEcosystem(ABC):
    """
    Abstract base class for ecosystem-specific scanning.

    Each ecosystem (NPM, Python, Maven, Go, Docker) implements this interface
    to provide ecosystem-specific parsing and analysis.
    """

    ecosystem_name: str = ""

    def __init__(self, artifactory_config: Dict[str, Any], policy_config: Dict[str, str]):
        """
        Initialize ecosystem scanner.

        Args:
            artifactory_config: Artifactory configuration
            policy_config: Policy configuration for expected endpoints
        """
        self.artifactory_config = artifactory_config
        self.policy_config = policy_config

    @abstractmethod
    def detect_manifests(self, repo_files: List[str]) -> List[str]:
        """
        Detect manifest files for this ecosystem.

        Args:
            repo_files: List of all files in repository

        Returns:
            List of manifest file paths for this ecosystem
        """
        pass

    @abstractmethod
    def parse_manifest(self, manifest_path: str, content: str) -> List[Component]:
        """
        Parse manifest file and extract components.

        Args:
            manifest_path: Path to manifest file
            content: Content of manifest file

        Returns:
            List of extracted components
        """
        pass

    @abstractmethod
    def detect_registry_config(self, repo_files: Dict[str, str]) -> Optional[str]:
        """
        Detect registry/mirror configuration in repository.

        Args:
            repo_files: Dictionary of file path -> content

        Returns:
            Detected registry endpoint URL or None
        """
        pass

    @abstractmethod
    def get_expected_endpoint(self) -> str:
        """
        Get expected compliant registry endpoint for this ecosystem.

        Returns:
            Expected registry endpoint URL
        """
        pass

    def validate_component(self, component: Component) -> bool:
        """
        Validate component data.

        Args:
            component: Component to validate

        Returns:
            True if component is valid
        """
        return (
            component.name
            and component.version
            and component.ecosystem == self.ecosystem_name
        )
