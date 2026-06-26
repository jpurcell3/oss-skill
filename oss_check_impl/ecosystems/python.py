"""Python/PyPI ecosystem scanning."""

import logging
import re
import json
from typing import List, Dict, Any, Optional

from ..core.models import Component, ComplianceStatus, Severity
from .base import BaseEcosystem

logger = logging.getLogger(__name__)


class PythonEcosystem(BaseEcosystem):
    """Python/PyPI package ecosystem scanner."""

    ecosystem_name = "python"

    def detect_manifests(self, repo_files: List[str]) -> List[str]:
        """
        Detect Python manifest files.

        Looks for:
        - requirements.txt (primary)
        - requirements-*.txt (environment-specific)
        - pyproject.toml (modern Python)
        - setup.py (legacy)
        - Pipfile (pipenv)

        Args:
            repo_files: List of all files in repository

        Returns:
            List of Python manifest file paths
        """
        python_manifests = [
            "requirements.txt",
            "pyproject.toml",
            "setup.py",
            "Pipfile",
        ]

        detected = []
        for file_path in repo_files:
            file_name = file_path.split("/")[-1]

            # Check exact matches
            if file_name in python_manifests:
                detected.append(file_path)
                logger.debug(f"Detected Python manifest: {file_path}")

            # Check requirements-*.txt pattern
            elif file_name.startswith("requirements-") and file_name.endswith(".txt"):
                detected.append(file_path)
                logger.debug(f"Detected Python requirements: {file_path}")

        return detected

    def parse_manifest(self, manifest_path: str, content: str) -> List[Component]:
        """
        Parse Python manifest file and extract components.

        Supports:
        - requirements.txt (pip format)
        - requirements-*.txt (environment-specific)
        - pyproject.toml (PEP 518/517)
        - setup.py (setuptools)
        - Pipfile (pipenv)

        Args:
            manifest_path: Path to manifest file
            content: Content of manifest file

        Returns:
            List of extracted components
        """
        components = []

        try:
            if manifest_path.endswith("requirements.txt") or manifest_path.endswith(
                ".txt"
            ):
                components = self._parse_requirements_txt(manifest_path, content)
            elif manifest_path.endswith("pyproject.toml"):
                components = self._parse_pyproject_toml(manifest_path, content)
            elif manifest_path.endswith("setup.py"):
                components = self._parse_setup_py(manifest_path, content)
            elif manifest_path.endswith("Pipfile"):
                components = self._parse_pipfile(manifest_path, content)
        except Exception as e:
            logger.error(f"Error parsing {manifest_path}: {e}")

        return components

    def _parse_requirements_txt(
        self, manifest_path: str, content: str
    ) -> List[Component]:
        """Parse requirements.txt file."""
        components = []

        for line in content.split("\n"):
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue

            # Skip options like -i, -f, etc.
            if line.startswith("-"):
                continue

            # Parse requirement line
            # Format: package==version, package>=version, package, etc.
            component = self._parse_requirement_line(line, manifest_path)
            if component:
                components.append(component)

        logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        return components

    def _parse_requirement_line(
        self, line: str, manifest_path: str
    ) -> Optional[Component]:
        """Parse a single requirement line."""
        # Remove extras and environment markers
        line = re.sub(r"\[.*?\]", "", line)  # Remove [extras]
        line = re.sub(r";.*", "", line)  # Remove ;markers

        # Extract package name and version
        # Patterns: package, package==1.0, package>=1.0, package[extra]==1.0, etc.
        match = re.match(r"^([a-zA-Z0-9._-]+)(.*)", line)
        if not match:
            return None

        name = match.group(1)
        version_spec = match.group(2)

        # Extract version (use first version found)
        version = "unknown"
        if version_spec:
            # Try to extract version from operators like ==, >=, <=, ~=, !=
            version_match = re.search(r"[=!<>~]+\s*([a-zA-Z0-9._-]+)", version_spec)
            if version_match:
                version = version_match.group(1)

        return Component(
            name=name,
            version=version,
            ecosystem=self.ecosystem_name,
            manifest_file=manifest_path,
        )

    def _parse_pyproject_toml(
        self, manifest_path: str, content: str
    ) -> List[Component]:
        """Parse pyproject.toml file."""
        components = []

        try:
            # Simple TOML parsing for dependencies
            # Look for [project] dependencies or [tool.poetry] dependencies
            in_dependencies = False
            in_project = False
            in_poetry = False

            for line in content.split("\n"):
                line = line.strip()

                # Check section headers
                if line == "[project]":
                    in_project = True
                    in_poetry = False
                elif line == "[tool.poetry]":
                    in_poetry = True
                    in_project = False
                elif line.startswith("["):
                    in_dependencies = False
                    in_project = False
                    in_poetry = False

                # Check for dependencies section
                if line == "dependencies = [" or line == "dependencies=[":
                    in_dependencies = True
                    continue

                # Parse dependency lines
                if in_dependencies:
                    if line == "]":
                        in_dependencies = False
                    elif line:
                        # Extract package and version from quoted string
                        match = re.search(r'"([^"]+)"', line)
                        if match:
                            component = self._parse_requirement_line(
                                match.group(1), manifest_path
                            )
                            if component:
                                components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing pyproject.toml: {e}")

        return components

    def _parse_setup_py(self, manifest_path: str, content: str) -> List[Component]:
        """Parse setup.py file."""
        components = []

        try:
            # Extract install_requires list
            match = re.search(r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL)
            if match:
                requires_str = match.group(1)
                # Extract quoted strings
                for req in re.findall(r'"([^"]+)"|\'([^\']+)\'', requires_str):
                    requirement = req[0] or req[1]
                    component = self._parse_requirement_line(requirement, manifest_path)
                    if component:
                        components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing setup.py: {e}")

        return components

    def _parse_pipfile(self, manifest_path: str, content: str) -> List[Component]:
        """Parse Pipfile (pipenv format)."""
        components = []

        try:
            # Simple parsing for [packages] and [dev-packages] sections
            in_packages = False
            in_dev_packages = False

            for line in content.split("\n"):
                line = line.strip()

                if line == "[packages]":
                    in_packages = True
                    in_dev_packages = False
                elif line == "[dev-packages]":
                    in_dev_packages = True
                    in_packages = False
                elif line.startswith("["):
                    in_packages = False
                    in_dev_packages = False

                # Parse package lines
                if (in_packages or in_dev_packages) and "=" in line:
                    # Format: package = "version" or package = "*"
                    parts = line.split("=", 1)
                    if len(parts) == 2:
                        name = parts[0].strip().strip('"\'')
                        version_spec = parts[1].strip().strip('"\'')

                        # Extract version
                        version = version_spec if version_spec != "*" else "latest"

                        component = Component(
                            name=name,
                            version=version,
                            ecosystem=self.ecosystem_name,
                            manifest_file=manifest_path,
                        )
                        components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing Pipfile: {e}")

        return components

    def detect_registry_config(self, repo_files: Dict[str, str]) -> Optional[str]:
        """
        Detect Python registry configuration.

        Looks for:
        - pip.conf or pip.ini with index-url
        - Pipfile sources
        - requirements.txt with -i or --index-url
        - pyproject.toml with index-url

        Args:
            repo_files: Dictionary of file path -> content

        Returns:
            Detected registry URL or None
        """
        # Check pip.conf
        if "pip.conf" in repo_files:
            registry = self._extract_pip_config(repo_files["pip.conf"])
            if registry:
                logger.debug(f"Found Python registry in pip.conf: {registry}")
                return registry

        # Check pip.ini
        if "pip.ini" in repo_files:
            registry = self._extract_pip_config(repo_files["pip.ini"])
            if registry:
                logger.debug(f"Found Python registry in pip.ini: {registry}")
                return registry

        # Check Pipfile
        if "Pipfile" in repo_files:
            registry = self._extract_pipfile_source(repo_files["Pipfile"])
            if registry:
                logger.debug(f"Found Python registry in Pipfile: {registry}")
                return registry

        # Check requirements.txt files
        for file_path, content in repo_files.items():
            if "requirements" in file_path and file_path.endswith(".txt"):
                registry = self._extract_pip_index_from_requirements(content)
                if registry:
                    logger.debug(f"Found Python registry in {file_path}: {registry}")
                    return registry

        # Check for pip config in CI configs
        for file_path, content in repo_files.items():
            if any(x in file_path.lower() for x in [".github", ".gitlab", ".circleci"]):
                registry = self._extract_pip_config_from_ci(content)
                if registry:
                    logger.debug(f"Found Python registry in CI config: {registry}")
                    return registry

        return None

    def _extract_pip_config(self, content: str) -> Optional[str]:
        """Extract index-url from pip.conf or pip.ini."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("index-url"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None

    def _extract_pipfile_source(self, content: str) -> Optional[str]:
        """Extract source URL from Pipfile."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("url"):
                parts = line.split("=", 1)
                if len(parts) == 2:
                    url = parts[1].strip().strip('"\'')
                    return url
        return None

    def _extract_pip_index_from_requirements(self, content: str) -> Optional[str]:
        """Extract --index-url from requirements.txt."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("-i ") or line.startswith("--index-url "):
                parts = line.split(None, 1)
                if len(parts) == 2:
                    return parts[1]
        return None

    def _extract_pip_config_from_ci(self, content: str) -> Optional[str]:
        """Extract pip config from CI configuration."""
        # Look for pip config set global.index-url commands
        match = re.search(
            r"pip\s+config\s+set\s+global\.index-url\s+([^\s\n]+)", content
        )
        if match:
            return match.group(1)

        # Look for --index-url in pip install commands
        match = re.search(r"pip\s+install.*--index-url\s+([^\s\n]+)", content)
        if match:
            return match.group(1)

        # Look for PIP_INDEX_URL environment variable
        match = re.search(r"PIP_INDEX_URL=([^\s\n]+)", content)
        if match:
            return match.group(1)

        return None

    def get_expected_endpoint(self) -> str:
        """
        Get expected compliant Python registry endpoint.

        Returns:
            Expected registry URL template
        """
        return self.policy_config.get(
            "pypi_simple_url",
            "https://{base}/artifactory/api/pypi/{pypi}/simple/",
        )
