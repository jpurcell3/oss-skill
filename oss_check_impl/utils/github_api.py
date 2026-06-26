"""GitHub API utilities for manifest detection and file retrieval."""

import logging
import json
from typing import Dict, List, Optional, Any
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import base64

logger = logging.getLogger(__name__)


class GitHubAPIClient:
    """Client for GitHub API operations."""

    def __init__(self, api_url: str, org: str, token: str, timeout: int = 30):
        """
        Initialize GitHub API client.

        Args:
            api_url: GitHub API base URL (e.g., https://api.github.com or https://eos2git.cec.lab.emc.com/api/v3)
            org: GitHub organization
            token: GitHub personal access token
            timeout: Request timeout in seconds
        """
        self.api_url = api_url.rstrip("/")
        self.org = org
        self.token = token
        self.timeout = timeout

    def _make_request(self, endpoint: str) -> Dict[str, Any]:
        """
        Make authenticated request to GitHub API.

        Args:
            endpoint: API endpoint (relative to base URL)

        Returns:
            JSON response as dictionary

        Raises:
            HTTPError: If request fails
            URLError: If network error occurs
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "oss-check-skill",
        }

        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=self.timeout) as response:
                data = response.read().decode("utf-8")
                return json.loads(data)
        except HTTPError as e:
            # Downgrade 404 to debug; callers often treat it as "not found" during probing
            try:
                code = getattr(e, "code", None)
            except Exception:
                code = None
            if code == 404:
                logger.debug(f"GitHub API 404: Not Found at {url}")
            else:
                logger.error(f"GitHub API error {getattr(e, 'code', 'unknown')}: {getattr(e, 'reason', 'error')} at {url}")
            raise
        except URLError as e:
            logger.error(f"Network error accessing GitHub API: {e.reason}")
            raise

    def get_repository_contents(
        self, repo: str, path: str = "", ref: str = "main"
    ) -> List[Dict[str, Any]]:
        """
        Get contents of a directory in repository.

        Args:
            repo: Repository name
            path: Path within repository (empty for root)
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            List of file/directory objects

        Raises:
            HTTPError: If repository or path not found
        """
        path_param = f"/{path}" if path else ""
        endpoint = f"repos/{self.org}/{repo}/contents{path_param}?ref={ref}"

        try:
            logger.debug(f"Fetching contents from {self.org}/{repo}{path_param}")
            response = self._make_request(endpoint)

            # Handle single file response
            if isinstance(response, dict) and "type" in response:
                return [response]

            # Handle directory listing
            if isinstance(response, list):
                return response

            return []
        except HTTPError as e:
            if e.code == 404:
                logger.debug(f"Path not found: {path}")
                return []
            raise

    def get_file_content(
        self, repo: str, file_path: str, ref: str = "main"
    ) -> Optional[str]:
        """
        Get content of a file in repository.

        Args:
            repo: Repository name
            file_path: Path to file within repository
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content as string, or None if not found

        Raises:
            HTTPError: If request fails
        """
        endpoint = f"repos/{self.org}/{repo}/contents/{file_path}?ref={ref}"

        try:
            logger.debug(f"Fetching file {file_path} from {self.org}/{repo}")
            response = self._make_request(endpoint)

            if "content" in response and len(response.get("content", "")) > 0:
                try:
                    # Content is base64 encoded
                    content = base64.b64decode(response["content"]).decode("utf-8")
                    return content
                except Exception as e:
                    logger.debug(f"Failed to decode base64 for {file_path}: {e}")
                    # Fall through to try raw endpoint
            
            # If content is empty or truncated, or file is too large (>1MB), use raw endpoint
            if len(response.get("content", "")) == 0 or response.get("size", 0) > 1000000:
                logger.debug(f"File {file_path} has truncated/empty content or is too large, trying raw endpoint")
                return self._get_raw_file_content(repo, file_path, ref)

            return None
        except HTTPError as e:
            if e.code == 404:
                logger.debug(f"File not found: {file_path}")
                return None
            raise

    def _get_raw_file_content(
        self, repo: str, file_path: str, ref: str = "main"
    ) -> Optional[str]:
        """
        Get raw content of a file using the raw.githubusercontent.com endpoint.

        Args:
            repo: Repository name
            file_path: Path to file within repository
            ref: Git reference (branch, tag, or commit SHA)

        Returns:
            File content as string, or None if not found
        """
        try:
            # Use raw.githubusercontent.com for large files
            # Format: https://raw.githubusercontent.com/org/repo/ref/file_path
            # For GitHub Enterprise, we need to construct the raw URL differently
            if "github.com" in self.api_url:
                raw_url = f"https://raw.githubusercontent.com/{self.org}/{repo}/{ref}/{file_path}"
            else:
                # For GitHub Enterprise, use the api_url base
                # e.g., https://eos2git.cec.lab.emc.com/raw/org/repo/ref/file_path
                base = self.api_url.replace("/api/v3", "")
                raw_url = f"{base}/raw/{self.org}/{repo}/{ref}/{file_path}"
            
            logger.debug(f"Fetching raw content from {raw_url}")
            headers = {
                "Authorization": f"token {self.token}",
                "User-Agent": "oss-check-skill",
            }
            
            request = Request(raw_url, headers=headers)
            with urlopen(request, timeout=self.timeout) as response:
                return response.read().decode("utf-8")
        except HTTPError as e:
            if e.code == 404:
                logger.debug(f"Raw file not found: {file_path}")
                return None
            logger.error(f"Error fetching raw file {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching raw file {file_path}: {e}")
            return None

    def list_files_recursive(
        self,
        repo: str,
        path: str = "",
        ref: str = "main",
        max_depth: int = 3,
        current_depth: int = 0,
    ) -> List[str]:
        """
        Recursively list all files in repository up to max depth.

        Args:
            repo: Repository name
            path: Starting path
            ref: Git reference
            max_depth: Maximum directory depth to traverse
            current_depth: Current recursion depth

        Returns:
            List of file paths
        """
        if current_depth >= max_depth:
            return []

        files = []
        try:
            contents = self.get_repository_contents(repo, path, ref)

            for item in contents:
                if item["type"] == "file":
                    files.append(item["path"])
                elif item["type"] == "dir":
                    # Recursively list subdirectory
                    subfiles = self.list_files_recursive(
                        repo, item["path"], ref, max_depth, current_depth + 1
                    )
                    files.extend(subfiles)
        except Exception as e:
            logger.warning(f"Error listing files in {path}: {e}")

        return files

    def detect_manifest_files(
        self, repo: str, ref: str = "main"
    ) -> Dict[str, List[str]]:
        """
        Detect dependency manifest files in repository.

        Searches for common manifest files across ecosystems:
        - Node/NPM: package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
        - Python: requirements.txt, requirements-*.txt, pyproject.toml, setup.py, Pipfile
        - Maven: pom.xml
        - Go: go.mod
        - Docker: Dockerfile

        Args:
            repo: Repository name
            ref: Git reference

        Returns:
            Dictionary mapping ecosystem -> list of manifest file paths
        """
        manifest_patterns = {
            "npm": [
                "package.json",
                "package-lock.json",
                "yarn.lock",
                "pnpm-lock.yaml",
            ],
            "python": [
                "requirements.txt",
                "pyproject.toml",
                "setup.py",
                "Pipfile",
            ],
            "maven": ["pom.xml"],
            "go": ["go.mod"],
            "docker": ["Dockerfile"],
        }

        detected = {ecosystem: [] for ecosystem in manifest_patterns}
        seen_paths = set()

        # Search in root and common subdirectories
        search_paths = ["", "backend", "services", "apps", "src", "packages"]

        for search_path in search_paths:
            try:
                contents = self.get_repository_contents(repo, search_path, ref)

                for item in contents:
                    if item["type"] != "file":
                        continue

                    file_name = item["name"]
                    file_path = item["path"]

                    # Check for exact matches
                    for ecosystem, patterns in manifest_patterns.items():
                        if file_name in patterns and file_path not in seen_paths:
                            detected[ecosystem].append(file_path)
                            seen_paths.add(file_path)
                            logger.debug(f"Found {ecosystem} manifest: {file_path}")

                    # Check for requirements-*.txt pattern
                    if file_name.startswith("requirements-") and file_name.endswith(
                        ".txt"
                    ) and file_path not in seen_paths:
                        detected["python"].append(file_path)
                        seen_paths.add(file_path)
                        logger.debug(f"Found Python requirements: {file_path}")

            except Exception as e:
                logger.warning(f"Error searching {search_path}: {e}")

        # Shallow recursive search to catch nested manifests (depth <= 3)
        try:
            all_files = self.list_files_recursive(repo, "", ref, max_depth=3, current_depth=0)
            for file_path in all_files:
                file_name = file_path.split("/")[-1]
                for ecosystem, patterns in manifest_patterns.items():
                    if file_name in patterns and file_path not in seen_paths:
                        detected[ecosystem].append(file_path)
                        seen_paths.add(file_path)
                if file_name.startswith("requirements-") and file_name.endswith(".txt") and file_path not in seen_paths:
                    detected["python"].append(file_path)
                    seen_paths.add(file_path)
        except Exception as e:
            logger.warning(f"Error in recursive manifest discovery: {e}")

        # Remove empty entries
        return {k: v for k, v in detected.items() if v}

    def get_default_branch(self, repo: str) -> str:
        """
        Get default branch of repository.

        Args:
            repo: Repository name

        Returns:
            Default branch name (usually 'main' or 'master')

        Raises:
            HTTPError: If request fails
        """
        endpoint = f"repos/{self.org}/{repo}"

        try:
            response = self._make_request(endpoint)
            return response.get("default_branch", "main")
        except Exception as e:
            logger.warning(f"Error getting default branch: {e}")
            return "main"
