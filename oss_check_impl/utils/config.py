"""Configuration loading and validation for OSS Check skill."""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional


class ConfigLoader:
    """Load and validate configuration from YAML file."""

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize configuration loader.

        Args:
            config_path: Path to config.yaml file. If None, searches standard locations.
        """
        self.config_path = self._find_config(config_path)
        self.config = self._load_config()
        self._validate_config()

    def _find_config(self, config_path: Optional[str]) -> Path:
        """
        Find configuration file.

        Searches in this order:
        1. Provided config_path
        2. Current directory
        3. .agents/skills/engineering/oss-check/
        4. ~/.oss-check/config.yaml

        Args:
            config_path: Explicit path to config file

        Returns:
            Path to configuration file

        Raises:
            FileNotFoundError: If no configuration file found
        """
        search_paths = []

        if config_path:
            search_paths.append(Path(config_path))

        search_paths.extend([
            Path("config.yaml"),
            Path("oss_check_config.yaml"),
            Path(".agents/skills/engineering/oss-check/config.yaml"),
            # AgentOps global skills repo (common in this workspace)
            Path("../../AgentOps/global/skills/engineering/oss-check/config.yaml"),
            Path.home() / ".oss-check" / "config.yaml",
        ])

        for path in search_paths:
            if path.exists():
                return path

        raise FileNotFoundError(
            f"Configuration file not found. Searched: {[str(p) for p in search_paths]}"
        )

    def _load_config(self) -> Dict[str, Any]:
        """
        Load and parse YAML configuration file.

        Returns:
            Configuration dictionary

        Raises:
            yaml.YAMLError: If YAML parsing fails
            IOError: If file cannot be read
        """
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)
                if config is None:
                    config = {}
                return config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(
                f"Failed to parse configuration file {self.config_path}: {e}"
            )
        except IOError as e:
            raise IOError(
                f"Failed to read configuration file {self.config_path}: {e}"
            )

    def _validate_config(self) -> None:
        """
        Validate configuration structure and required fields.

        Raises:
            ValueError: If required configuration is missing or invalid
        """
        required_sections = ["github", "artifactory"]

        for section in required_sections:
            if section not in self.config:
                raise ValueError(
                    f"Missing required configuration section: {section}"
                )

        # Validate GitHub config
        github_config = self.config.get("github", {})
        if not github_config.get("api_url"):
            raise ValueError("Missing github.api_url in configuration")
        if not github_config.get("org"):
            raise ValueError("Missing github.org in configuration")

        # Validate Artifactory config
        artifactory_config = self.config.get("artifactory", {})
        if not artifactory_config.get("base_url"):
            raise ValueError("Missing artifactory.base_url in configuration")
        if not artifactory_config.get("virtual_repos"):
            raise ValueError("Missing artifactory.virtual_repos in configuration")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value by dot-notation key.

        Examples:
            config.get("github.api_url")
            config.get("artifactory.virtual_repos.npm")

        Args:
            key: Configuration key with dot notation
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default

        return value

    def get_github_config(self) -> Dict[str, str]:
        """
        Get GitHub configuration with environment variable substitution.

        Returns:
            GitHub configuration dictionary
        """
        config = self.config.get("github", {}).copy()

        # Allow environment variable override for token
        if "token" in config:
            config["token"] = os.getenv("GITHUB_TOKEN", config["token"])
        else:
            config["token"] = os.getenv("GITHUB_TOKEN", "")

        return config

    def get_jenkins_config(self) -> Dict[str, str]:
        """
        Get Jenkins configuration with environment variable substitution.

        Returns:
            Jenkins configuration dictionary
        """
        config = self.config.get("jenkins", {}).copy()

        # Allow environment variable overrides
        if "user" in config:
            config["user"] = os.getenv("JENKINS_USER", config["user"])
        else:
            config["user"] = os.getenv("JENKINS_USER", "")

        if "token" in config:
            config["token"] = os.getenv("JENKINS_TOKEN", config["token"])
        else:
            config["token"] = os.getenv("JENKINS_TOKEN", "")

        return config

    def get_artifactory_config(self) -> Dict[str, Any]:
        """
        Get Artifactory configuration.

        Returns:
            Artifactory configuration dictionary
        """
        return self.config.get("artifactory", {})

    def get_policy_config(self) -> Dict[str, str]:
        """
        Get policy configuration for expected registry URLs.

        Returns:
            Policy configuration dictionary
        """
        return self.config.get("policy", {})

    def to_dict(self) -> Dict[str, Any]:
        """
        Get entire configuration as dictionary.

        Returns:
            Configuration dictionary
        """
        return self.config.copy()
