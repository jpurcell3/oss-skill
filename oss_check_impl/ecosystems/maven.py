"""Maven ecosystem scanning."""

import logging
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional

from ..core.models import Component
from .base import BaseEcosystem

logger = logging.getLogger(__name__)


class MavenEcosystem(BaseEcosystem):
    """Maven Java ecosystem scanner."""

    ecosystem_name = "maven"

    def detect_manifests(self, repo_files: List[str]) -> List[str]:
        maven_manifests = ["pom.xml"]
        detected: List[str] = []
        for path in repo_files:
            if path.split("/")[-1] in maven_manifests:
                detected.append(path)
                logger.debug(f"Detected Maven manifest: {path}")
        return detected

    def parse_manifest(self, manifest_path: str, content: str) -> List[Component]:
        components: List[Component] = []
        try:
            root = ET.fromstring(content)
            # namespaces are often omitted; handle simple POMs
            deps_parent = root.find("dependencies")
            if deps_parent is None:
                # Try with namespace if present
                # crude detection: extract default namespace from tag like {ns}project
                ns = None
                if root.tag.startswith("{") and "}" in root.tag:
                    ns = root.tag.split("}", 1)[0][1:]
                if ns:
                    deps_parent = root.find(f"{{{ns}}}dependencies")
            if deps_parent is not None:
                for dep in list(deps_parent):
                    def _get(tag: str) -> Optional[str]:
                        el = dep.find(tag)
                        if el is None and ns:
                            el = dep.find(f"{{{ns}}}{tag}")
                        return el.text.strip() if el is not None and el.text else None

                    group_id = _get("groupId") or ""
                    artifact_id = _get("artifactId") or ""
                    version = _get("version") or "unknown"

                    name = f"{group_id}:{artifact_id}" if group_id else artifact_id
                    if name:
                        components.append(
                            Component(
                                name=name,
                                version=version,
                                ecosystem=self.ecosystem_name,
                                manifest_file=manifest_path,
                            )
                        )
            logger.debug(f"Extracted {len(components)} components from {manifest_path}")
        except Exception as e:
            logger.error(f"Error parsing pom.xml: {e}")
        return components

    def detect_registry_config(self, repo_files: Dict[str, str]) -> Optional[str]:
        # Prefer settings.xml (repo or .mvn/) if present
        for key in ("settings.xml",):
            if key in repo_files:
                try:
                    root = ET.fromstring(repo_files[key])
                    # look for mirrors/url first
                    mirrors = root.find("mirrors")
                    if mirrors is not None:
                        for m in list(mirrors):
                            url = m.findtext("url")
                            if url:
                                return url.strip()
                    # fall back to repositories/url
                    repos = root.find("profiles")
                    if repos is not None:
                        # scan any urls under repositories
                        for prof in list(repos):
                            repolist = prof.find("repositories")
                            if repolist is not None:
                                for rep in list(repolist):
                                    url = rep.findtext("url")
                                    if url:
                                        return url.strip()
                except Exception:
                    pass
        # Fallback to pom.xml <repositories><repository><url>
        if "pom.xml" in repo_files:
            try:
                root = ET.fromstring(repo_files["pom.xml"])
                repos = root.find("repositories")
                if repos is not None:
                    for rep in list(repos):
                        url = rep.findtext("url")
                        if url:
                            return url.strip()
            except Exception:
                pass
        # CI configs: look for -s settings.xml or -Dmaven.repo.local
        for fname, content in repo_files.items():
            if any(x in fname.lower() for x in [".github", ".gitlab", ".circleci"]):
                m = re.search(r"mvn\s+[^\n]*-s\s+([^\s\n]+)", content)
                if m:
                    return "settings.xml"
                m = re.search(r"-Dmaven\.repo\.local=([^\s\n]+)", content)
                if m:
                    return m.group(1)
        return None

    def get_expected_endpoint(self) -> str:
        return self.policy_config.get(
            "maven_repo_url",
            "https://{base}/artifactory/{maven}/",
        )
