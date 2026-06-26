"""NPM/Node.js ecosystem scanning."""

import json
import logging
import re
from typing import List, Dict, Any, Optional

from ..core.models import Component, ComplianceStatus, Severity
from .base import BaseEcosystem

logger = logging.getLogger(__name__)


class NPMEcosystem(BaseEcosystem):
    """NPM/Node.js package ecosystem scanner."""

    ecosystem_name = "npm"

    def __init__(self, artifactory_config: Dict[str, Any], policy_config: Dict[str, str], include_transitive_deps: bool = True):
        """Initialize NPM ecosystem scanner.
        
        Args:
            artifactory_config: Artifactory configuration
            policy_config: Policy configuration
            include_transitive_deps: Include transitive dependencies from lockfiles (default: True)
        """
        super().__init__(artifactory_config, policy_config)
        self.include_transitive_deps = include_transitive_deps

    def detect_manifests(self, repo_files: List[str]) -> List[str]:
        """
        Detect NPM manifest files.

        Looks for:
        - package.json (primary)
        - package-lock.json (lockfile, if include_transitive_deps=True)
        - yarn.lock (yarn lockfile, if include_transitive_deps=True)
        - pnpm-lock.yaml (pnpm lockfile, if include_transitive_deps=True)

        Args:
            repo_files: List of all files in repository

        Returns:
            List of NPM manifest file paths
        """
        npm_manifests = ["package.json"]
        
        # Include lockfiles only if transitive deps are enabled
        if self.include_transitive_deps:
            npm_manifests.extend([
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
            ])

        detected = []
        for file_path in repo_files:
            file_name = file_path.split("/")[-1]
            if file_name in npm_manifests:
                detected.append(file_path)
                logger.debug(f"Detected NPM manifest: {file_path}")

        return detected

    def parse_manifest(self, manifest_path: str, content: str) -> List[Component]:
        """
        Parse NPM manifest file and extract components.

        Supports:
        - package.json (dependencies, devDependencies, peerDependencies)
        - package-lock.json (lockfile format)
        - yarn.lock (yarn lockfile format)
        - pnpm-lock.yaml (pnpm lockfile format)

        Args:
            manifest_path: Path to manifest file
            content: Content of manifest file

        Returns:
            List of extracted components
        """
        components = []

        try:
            if manifest_path.endswith("package.json"):
                components = self._parse_package_json(manifest_path, content)
            elif manifest_path.endswith("package-lock.json"):
                components = self._parse_package_lock(manifest_path, content)
            elif manifest_path.endswith("yarn.lock"):
                components = self._parse_yarn_lock(manifest_path, content)
            elif manifest_path.endswith("pnpm-lock.yaml"):
                components = self._parse_pnpm_lock(manifest_path, content)
        except Exception as e:
            logger.error(f"Error parsing {manifest_path}: {e}")

        return components

    def _parse_package_json(self, manifest_path: str, content: str) -> List[Component]:
        """Parse package.json file."""
        components = []

        try:
            data = json.loads(content)

            # Extract dependencies
            for dep_type in ["dependencies", "devDependencies", "peerDependencies"]:
                deps = data.get(dep_type, {})
                for name, version in deps.items():
                    component = Component(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem_name,
                        manifest_file=manifest_path,
                    )
                    components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {manifest_path}: {e}")

        return components

    def _parse_package_lock(
        self, manifest_path: str, content: str
    ) -> List[Component]:
        """Parse package-lock.json file."""
        components = []

        try:
            data = json.loads(content)
            packages = data.get("packages", {})

            for package_path, package_info in packages.items():
                # Skip root package
                if package_path == "":
                    continue

                name = package_info.get("name")
                version = package_info.get("version")

                if name and version:
                    component = Component(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem_name,
                        manifest_file=manifest_path,
                    )
                    components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {manifest_path}: {e}")

        return components

    def _parse_yarn_lock(self, manifest_path: str, content: str) -> List[Component]:
        """Parse yarn.lock file."""
        components = []

        try:
            # Parse yarn.lock format: name@version: ... version "..."
            lines = content.split("\n")
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                # Look for package entries (name@version:)
                if "@" in line and line.endswith(":"):
                    # Extract name and version from entry
                    parts = line.rstrip(":").split("@")

                    # Handle scoped packages (@org/package)
                    if line.startswith("@"):
                        name = "@" + parts[1]
                        version_part = parts[2] if len(parts) > 2 else ""
                    else:
                        name = parts[0]
                        version_part = parts[1] if len(parts) > 1 else ""

                    # Find version line
                    i += 1
                    while i < len(lines):
                        version_line = lines[i].strip()
                        if version_line.startswith('version "'):
                            version = version_line.split('"')[1]
                            component = Component(
                                name=name,
                                version=version,
                                ecosystem=self.ecosystem_name,
                                manifest_file=manifest_path,
                            )
                            components.append(component)
                            break
                        elif version_line and not version_line.startswith('"'):
                            break
                        i += 1

                i += 1

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing yarn.lock: {e}")

        return components

    def _parse_pnpm_lock(self, manifest_path: str, content: str) -> List[Component]:
        """Parse pnpm-lock.yaml file."""
        components = []

        try:
            # Simple YAML parsing for pnpm-lock.yaml
            # Format: packages: { 'name@version': { ... } }
            lines = content.split("\n")

            for line in lines:
                # Look for package entries like 'name@version':
                if "'" in line and "@" in line and ":" in line:
                    # Extract package name and version
                    match = re.search(r"'([^']+)':", line)
                    if match:
                        package_spec = match.group(1)
                        if "@" in package_spec:
                            # Split on last @ to handle scoped packages
                            parts = package_spec.rsplit("@", 1)
                            if len(parts) == 2:
                                name, version = parts
                                component = Component(
                                    name=name,
                                    version=version,
                                    ecosystem=self.ecosystem_name,
                                    manifest_file=manifest_path,
                                )
                                components.append(component)

            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing pnpm-lock.yaml: {e}")

        return components

    def detect_registry_config(self, repo_files: Dict[str, str]) -> Optional[str]:
        """
        Detect NPM registry configuration.

        Looks for:
        - .npmrc file with registry setting
        - publishConfig.registry in package.json
        - npm config set registry in CI configs

        Args:
            repo_files: Dictionary of file path -> content

        Returns:
            Detected registry URL or None
        """
        # Check .npmrc file
        if ".npmrc" in repo_files:
            content = repo_files[".npmrc"]
            registry = self._extract_registry_from_npmrc(content)
            if registry:
                logger.debug(f"Found NPM registry in .npmrc: {registry}")
                return registry

        # Check package.json for publishConfig
        if "package.json" in repo_files:
            try:
                data = json.loads(repo_files["package.json"])
                publish_config = data.get("publishConfig", {})
                registry = publish_config.get("registry")
                if registry:
                    logger.debug(f"Found NPM registry in package.json: {registry}")
                    return registry
            except json.JSONDecodeError:
                pass

        # Check for npm config in CI configs
        for file_path, content in repo_files.items():
            if any(
                x in file_path.lower() for x in [".github", ".gitlab", ".circleci"]
            ):
                registry = self._extract_npm_config_from_ci(content)
                if registry:
                    logger.debug(f"Found NPM registry in CI config: {registry}")
                    return registry

        return None

    def _extract_registry_from_npmrc(self, content: str) -> Optional[str]:
        """Extract registry URL from .npmrc file."""
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("registry="):
                return line.split("=", 1)[1].strip()
        return None

    def _extract_npm_config_from_ci(self, content: str) -> Optional[str]:
        """Extract npm registry config from CI configuration."""
        # Look for npm config set registry commands
        match = re.search(r"npm\s+config\s+set\s+registry\s+([^\s\n]+)", content)
        if match:
            return match.group(1)

        # Look for NPM_CONFIG_REGISTRY environment variable
        match = re.search(r"NPM_CONFIG_REGISTRY=([^\s\n]+)", content)
        if match:
            return match.group(1)

        return None

    def get_expected_endpoint(self) -> str:
        """
        Get expected compliant NPM registry endpoint.

        Returns:
            Expected registry URL template
        """
        return self.policy_config.get(
            "npm_registry_url",
            "https://{base}/artifactory/api/npm/{npm}/",
        )
