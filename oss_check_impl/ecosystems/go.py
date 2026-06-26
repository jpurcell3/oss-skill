"""Go modules ecosystem scanning."""

import logging
import re
from typing import List, Dict, Any, Optional

from ..core.models import Component
from .base import BaseEcosystem

logger = logging.getLogger(__name__)


class GoEcosystem(BaseEcosystem):
    """Go modules ecosystem scanner."""

    ecosystem_name = "go"

    def detect_manifests(self, repo_files: List[str]) -> List[str]:
        detected: List[str] = []
        for path in repo_files:
            if path.split("/")[-1] == "go.mod":
                detected.append(path)
                logger.debug(f"Detected Go manifest: {path}")
        return detected

    def parse_manifest(self, manifest_path: str, content: str) -> List[Component]:
        components: List[Component] = []
        try:
            in_require_block = False
            for line in content.splitlines():
                s = line.strip()
                if not s or s.startswith("//"):
                    continue
                if s.startswith("require ("):
                    in_require_block = True
                    continue
                if in_require_block and s == ")":
                    in_require_block = False
                    continue
                if s.startswith("require ") and not s.startswith("require ("):
                    s = s[len("require "):].strip()
                if in_require_block or s.startswith("require ") or not s.startswith("module "):
                    # lines like: github.com/org/pkg v1.2.3 // indirect
                    parts = s.split()
                    if len(parts) >= 2:
                        name = parts[0]
                        version = parts[1]
                        # skip directives like replace, go, module etc.
                        if name not in ("replace", "go", "module"):
                            components.append(
                                Component(
                                    name=name,
                                    version=version,
                                    ecosystem=self.ecosystem_name,
                                    manifest_file=manifest_path,
                                )
                            )
        except Exception as e:
            logger.error(f"Error parsing go.mod: {e}")
        return components

    def detect_registry_config(self, repo_files: Dict[str, str]) -> Optional[str]:
        # GOPROXY in CI or env-like files
        for fname, content in repo_files.items():
            if any(x in fname.lower() for x in [".github", ".gitlab", ".circleci", "Dockerfile", "Makefile"]):
                m = re.search(r"GOPROXY=([^\s\n]+)", content)
                if m:
                    return m.group(1)
                m = re.search(r"go\s+env\s+-w\s+GOPROXY=([^\s\n]+)", content)
                if m:
                    return m.group(1)
        # go env -w GOPRIVATE often appears; keep for evidence but not a registry URL
        return None

    def get_expected_endpoint(self) -> str:
        return self.policy_config.get(
            "go_proxy_url",
            "https://{base}/artifactory/api/go/{go}/",
        )
