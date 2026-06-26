"""Main scanning orchestrator for OSS Check skill."""

import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List
import re
from urllib.parse import urlparse

from .models import (
    ScanResult,
    ComplianceSummary,
    Component,
    Finding,
    ComplianceStatus,
    Severity,
)
from ..utils.github_api import GitHubAPIClient
from ..ecosystems.npm import NPMEcosystem
from ..ecosystems.python import PythonEcosystem
from ..ecosystems.maven import MavenEcosystem
from ..ecosystems.go import GoEcosystem
from .jenkins_analyzer import JenkinsAnalyzer


logger = logging.getLogger(__name__)


class OSSScannerOrchestrator:
    """
    Orchestrates the OSS compliance scanning workflow.

    Coordinates:
    - Manifest detection
    - Dependency extraction
    - Registry configuration analysis
    - Jenkins integration
    - Compliance assessment
    """

    def __init__(
        self,
        github_config: Dict[str, str],
        artifactory_config: Dict[str, Any],
        policy_config: Dict[str, str],
        jenkins_config: Optional[Dict[str, str]] = None,
        include_transitive_deps: bool = True,
    ):
        """
        Initialize scanner orchestrator.

        Args:
            github_config: GitHub API configuration
            artifactory_config: Artifactory configuration
            policy_config: Policy configuration for expected endpoints
            jenkins_config: Jenkins configuration (optional)
            include_transitive_deps: Include transitive dependencies from lockfiles (default: True)
        """
        self.github_config = github_config
        self.artifactory_config = artifactory_config
        self.policy_config = policy_config
        self.jenkins_config = jenkins_config or {}
        self.include_transitive_deps = include_transitive_deps

        # Initialize GitHub API client
        self.github_client = GitHubAPIClient(
            api_url=github_config.get("api_url", "https://api.github.com"),
            org=github_config.get("org", ""),
            token=github_config.get("token", ""),
        )

        # Initialize ecosystem scanners
        self.ecosystems = {
            "npm": NPMEcosystem(artifactory_config, policy_config, include_transitive_deps),
            "python": PythonEcosystem(artifactory_config, policy_config),
            "maven": MavenEcosystem(artifactory_config, policy_config),
            "go": GoEcosystem(artifactory_config, policy_config),
        }

        logger.info("OSS Scanner Orchestrator initialized")

    def scan(
        self,
        repo_name: str,
        org: Optional[str] = None,
        ref: str = "main",
        include_jenkins: bool = True,
        verbose: bool = False,
    ) -> ScanResult:
        """
        Perform OSS compliance scan on a repository.

        Args:
            repo_name: Repository name
            org: GitHub organization (uses config default if not provided)
            ref: Git reference (branch, tag, or commit SHA)
            include_jenkins: Include Jenkins runtime evidence
            verbose: Include verbose details in results

        Returns:
            ScanResult with compliance information
        """
        org = org or self.github_config.get("org")
        scan_timestamp = datetime.utcnow().isoformat() + "Z"

        logger.info(f"Starting scan of {org}/{repo_name} at {ref}")

        result = ScanResult(
            repository_name=repo_name,
            organization=org,
            ref=ref,
            scan_timestamp=scan_timestamp,
        )

        try:
            # Stash repo/ref for downstream helpers
            self._current_repo = repo_name
            self._current_ref = ref
            # Phase 1: Detect manifests
            logger.info("Phase 1: Detecting dependency manifests")
            manifests = self._detect_manifests(org, repo_name, ref)
            try:
                result.verbose_details["detected_manifests"] = manifests
            except Exception:
                pass

            if not manifests:
                logger.warning(f"No dependency manifests found in {org}/{repo_name}")
                result.errors.append("No dependency manifests found")
                return result

            # Phase 2: Parse manifests and extract components
            logger.info("Phase 2: Parsing manifests and extracting components")
            components = self._parse_manifests(manifests, org, repo_name, ref)
            result.components = components

            # Phase 3: Analyze registry configuration
            logger.info("Phase 3: Analyzing registry configuration")
            self._analyze_registry_config(components)

            # Phase 4: Jenkins integration (optional)
            if include_jenkins and self.jenkins_config.get("url"):
                logger.info("Phase 4: Analyzing Jenkins runtime evidence")
                jenkins_info = self._analyze_jenkins(org, repo_name)
                result.jenkins_jobs_analyzed = jenkins_info.get("jobs_analyzed", 0)
                result.runtime_configs_found = jenkins_info.get("configs_found", 0)
                self._apply_jenkins_evidence(components, jenkins_info)
                # Stash evidence for verbose output
                try:
                    result.verbose_details["jenkins_evidence"] = jenkins_info
                except Exception:
                    pass

            # Phase 5: Compliance assessment
            logger.info("Phase 5: Assessing compliance")
            self._assess_compliance(components, result)

            # Phase 6: Generate findings and recommendations
            logger.info("Phase 6: Generating findings and recommendations")
            self._generate_findings(components, result)

            logger.info(
                f"Scan complete: {result.summary.compliant} compliant, "
                f"{result.summary.non_compliant} non-compliant"
            )

        except Exception as e:
            logger.error(f"Scan failed: {e}", exc_info=True)
            result.errors.append(f"Scan failed: {str(e)}")

        return result

    def _detect_manifests(
        self, org: str, repo: str, ref: str
    ) -> Dict[str, List[str]]:
        """
        Detect dependency manifest files in repository.

        Args:
            org: GitHub organization
            repo: Repository name
            ref: Git reference

        Returns:
            Dictionary of ecosystem -> list of manifest file paths
        """
        logger.debug(f"Detecting manifests in {org}/{repo} at {ref}")

        try:
            # Use GitHub API to detect manifests
            manifests = self.github_client.detect_manifest_files(repo, ref)
            logger.info(f"Found manifests: {manifests}")
            return manifests
        except Exception as e:
            logger.error(f"Error detecting manifests: {e}")
            return {}

    def _parse_manifests(
        self, manifests: Dict[str, List[str]], org: str, repo: str, ref: str
    ) -> List[Component]:
        """
        Parse manifest files and extract components.

        Args:
            manifests: Dictionary of ecosystem -> list of manifest file paths
            org: GitHub organization
            repo: Repository name
            ref: Git reference

        Returns:
            List of extracted components
        """
        components = []

        try:
            for ecosystem, manifest_paths in manifests.items():
                if ecosystem not in self.ecosystems:
                    logger.debug(f"Skipping unsupported ecosystem {ecosystem}")
                    continue

                ecosystem_scanner = self.ecosystems[ecosystem]

                for manifest_path in manifest_paths:
                    try:
                        # Fetch manifest content from GitHub
                        content = self.github_client.get_file_content(
                            repo, manifest_path, ref
                        )

                        if content:
                            # Parse manifest
                            parsed_components = ecosystem_scanner.parse_manifest(
                                manifest_path, content
                            )
                            components.extend(parsed_components)
                            logger.debug(
                                f"Parsed {len(parsed_components)} components from {manifest_path}"
                            )
                    except Exception as e:
                        logger.error(f"Error parsing {manifest_path}: {e}")

            logger.info(f"Extracted {len(components)} total components")
        except Exception as e:
            logger.error(f"Error in manifest parsing: {e}")

        return components

    def _analyze_registry_config(self, components: List[Component]) -> None:
        """
        Analyze registry configuration for components.

        Args:
            components: List of components to analyze
        """
        logger.debug(f"Analyzing registry config for {len(components)} components")

        if not components:
            return

        # Determine which ecosystems are present
        present_ecosystems = {c.ecosystem for c in components}

        # Build a small set of candidate files to fetch for registry detection
        candidate_names = set()
        if "npm" in present_ecosystems:
            candidate_names.update({
                ".npmrc",
                "package.json",
            })
        if "python" in present_ecosystems:
            candidate_names.update({
                "pip.conf",
                "pip.ini",
                "Pipfile",
                "pyproject.toml",
                "requirements.txt",
            })

        # Include common CI folders for both ecosystems (workflows often hold configs)
        ci_prefixes = [".github/", ".gitlab/", ".circleci/"]

        # Collect repository files up to a shallow depth to limit API calls
        try:
            # Infer repo/org/ref from any component already populated by scan()
            # We rely on prior phases populating github_client context and using the same ref
            # Here, we cannot directly access repo and ref; instead, fetch a shallow listing from root
            # and common subfolders for known filenames
            # Note: We use the GitHub API client to gather candidate paths
            # Since repo and ref are not passed here, we store them temporarily on the instance in scan()
            repo = getattr(self, "_current_repo", None)
            ref = getattr(self, "_current_ref", None)
            if not repo or not ref:
                logger.warning("Repository context missing during registry analysis; skipping")
                return

            # List root files and common subfolders only
            repo_files_paths = set()
            for base in ["", "backend", "services", "apps", "src", "packages"]:
                try:
                    entries = self.github_client.get_repository_contents(repo, base, ref)
                    for item in entries:
                        if item.get("type") != "file":
                            continue
                        path = item.get("path", "")
                        name = item.get("name", "")
                        if name in candidate_names:
                            repo_files_paths.add(path)
                        # pick up requirements-*.txt
                        if name.startswith("requirements-") and name.endswith(".txt"):
                            repo_files_paths.add(path)
                        # include CI files (workflows YAML)
                        for pfx in ci_prefixes:
                            if path.startswith(pfx):
                                repo_files_paths.add(path)
                except Exception as e:
                    logger.debug(f"Skipping search in {base}: {e}")

            # Fetch contents for selected files
            repo_files: Dict[str, str] = {}
            for fp in repo_files_paths:
                content = self.github_client.get_file_content(repo, fp, ref)
                if content is not None:
                    repo_files[fp.split("/")[-1] if "/" in fp else fp] = content

        except Exception as e:
            logger.warning(f"Could not gather repository files for registry analysis: {e}")
            return

        # Detect registry per ecosystem
        detected_registry_by_eco: Dict[str, Optional[str]] = {}
        expected_by_eco: Dict[str, Optional[str]] = {}

        for eco_name, eco_scanner in self.ecosystems.items():
            if eco_name not in present_ecosystems:
                continue
            try:
                detected = eco_scanner.detect_registry_config(repo_files)
            except Exception as e:
                logger.debug(f"Registry detection failed for {eco_name}: {e}")
                detected = None
            detected_registry_by_eco[eco_name] = detected

            # Build expected endpoint from policy + artifactory config
            try:
                expected_tpl = eco_scanner.get_expected_endpoint()
                art = self.artifactory_config or {}
                base = art.get("base_url", "")
                vrepos = (art.get("virtual_repos") or {})
                expected = expected_tpl.format(
                    base=base,
                    npm=vrepos.get("npm", ""),
                    pypi=vrepos.get("pypi", ""),
                    maven=vrepos.get("maven", ""),
                    go=vrepos.get("go", ""),
                )
            except Exception as e:
                logger.debug(
                    f"Failed to build expected endpoint for {eco_name}: {e}"
                )
                expected = None
            expected_by_eco[eco_name] = expected

        def _normalize(url: Optional[str]) -> Optional[str]:
            if not url:
                return url
            u = url.strip()
            # Strip embedded credentials if present
            try:
                u = re.sub(r"://[^@]+@", "://", u)
            except Exception:
                pass
            try:
                while u.endswith('/') and len(u) > 8:
                    u = u[:-1]
            except Exception:
                pass
            return u

        # Allowlist for registry hosts (from policy)
        allowed_hosts: List[str] = []
        try:
            ah = self.policy_config.get("allowed_registry_hosts")
            if isinstance(ah, list):
                allowed_hosts = [str(h).lower() for h in ah]
        except Exception:
            pass

        # Update components with detected/expected endpoints and status
        for c in components:
            detected = _normalize(detected_registry_by_eco.get(c.ecosystem))
            expected = _normalize(expected_by_eco.get(c.ecosystem))
            c.detected_endpoint = detected
            c.expected_endpoint = expected

            compliant = False
            if expected and detected and (detected.startswith(expected)):
                compliant = True
            elif detected and allowed_hosts:
                try:
                    host = urlparse(detected).hostname or ""
                    host = host.lower()
                    if any(host == h or host.endswith("." + h) for h in allowed_hosts):
                        compliant = True
                except Exception:
                    pass

            if compliant:
                c.status = ComplianceStatus.COMPLIANT
                c.severity = Severity.INFO
                c.notes = (
                    "Registry configured to compliant endpoint"
                    if expected and detected and detected.startswith(expected)
                    else "Registry host allowed by policy"
                )
            else:
                # No repo-level registry or mismatch -> mark non-compliant for Phase 1
                c.status = ComplianceStatus.NON_COMPLIANT
                c.severity = Severity.HIGH
                if not detected:
                    c.notes = "No repository-level registry configuration detected"
                else:
                    c.notes = "Registry does not match expected compliant endpoint"

        # Stash verbose details for debugging
        try:
            # Attach to a temporary attribute for later inclusion if result collects it
            self._last_registry_analysis = {
                "detected_registry_by_ecosystem": detected_registry_by_eco,
                "expected_by_ecosystem": expected_by_eco,
                "files_considered": sorted(repo_files_paths),
            }
        except Exception:
            pass

    def _analyze_jenkins(self, org: str, repo: str) -> Dict[str, Any]:
        """
        Analyze Jenkins jobs for runtime evidence.

        Args:
            org: GitHub organization
            repo: Repository name

        Returns:
            Dictionary with Jenkins analysis results
        """
        logger.debug(f"Analyzing Jenkins for {org}/{repo}")
        try:
            analyzer = JenkinsAnalyzer(self.jenkins_config)
            info = analyzer.analyze(repo)
            return info
        except Exception as e:
            logger.debug(f"Jenkins analysis failed: {e}")
            return {"jobs_analyzed": 0, "configs_found": 0, "evidence": {}}

    def _apply_jenkins_evidence(
        self, components: List[Component], jenkins_info: Dict[str, Any]
    ) -> None:
        """
        Apply Jenkins runtime evidence to components.

        Args:
            components: List of components
            jenkins_info: Jenkins analysis results
        """
        logger.debug(f"Applying Jenkins evidence to {len(components)} components")
        evidence: Dict[str, str] = jenkins_info.get("evidence", {}) if isinstance(jenkins_info, dict) else {}
        logger.debug(f"Jenkins evidence: {evidence}")

        def _normalize(url: Optional[str]) -> Optional[str]:
            if not url:
                return url
            u = url.strip()
            try:
                while u.endswith('/') and len(u) > 8:
                    u = u[:-1]
            except Exception:
                pass
            return u

        def _is_allowed_artifactory(url: str) -> bool:
            """Check if URL uses an allowed Artifactory host."""
            allowed_hosts = (self.artifactory_config or {}).get("allowed_hosts", [])
            if not allowed_hosts:
                # Fallback to base_url if no allowed_hosts specified
                base = (self.artifactory_config or {}).get("base_url", "")
                allowed_hosts = [base] if base else []
            
            url_lower = url.lower()
            for host in allowed_hosts:
                if host.lower() in url_lower:
                    return True
            return False

        for c in components:
            ev = _normalize(evidence.get(c.ecosystem))
            exp = _normalize(c.expected_endpoint)
            if ev and exp:
                # Check if Jenkins evidence uses an allowed Artifactory host
                if _is_allowed_artifactory(ev):
                    if c.status != ComplianceStatus.COMPLIANT:
                        # If no repo-level config but Jenkins evidence matches, mark as TRANSLATED
                        if not c.detected_endpoint:
                            c.status = ComplianceStatus.TRANSLATED
                            c.runtime_evidence = True
                            c.severity = Severity.INFO
                            c.notes = "Compliant via runtime proxy (Jenkins)"
                        else:
                            # Repo-level config mismatch, but Jenkins fixes it
                            c.status = ComplianceStatus.COMPLIANT_RUNTIME
                            c.runtime_evidence = True
                            c.severity = Severity.INFO
                            c.notes = "Compliant at runtime via Jenkins configuration"

    def _assess_compliance(
        self, components: List[Component], result: ScanResult
    ) -> None:
        """
        Assess compliance status for all components.

        Args:
            components: List of components
            result: Scan result to update
        """
        summary = ComplianceSummary(total_components=len(components))

        for component in components:
            if component.status == ComplianceStatus.COMPLIANT:
                summary.compliant += 1
            elif component.status == ComplianceStatus.COMPLIANT_RUNTIME:
                summary.compliant_runtime += 1
            elif component.status == ComplianceStatus.TRANSLATED:
                summary.translated += 1
            else:
                summary.non_compliant += 1

        result.summary = summary
        # Include verbose registry analysis details if available
        if hasattr(self, "_last_registry_analysis"):
            result.verbose_details["registry_analysis"] = getattr(
                self, "_last_registry_analysis"
            )
        logger.debug(f"Compliance assessment: {summary.compliance_percentage}%")

    def _generate_findings(
        self, components: List[Component], result: ScanResult
    ) -> None:
        """
        Generate findings and recommendations aggregated by endpoint configuration.

        Args:
            components: List of components
            result: Scan result to update
        """
        # Group non-compliant components by ecosystem and endpoint
        findings_by_key: Dict[str, Dict[str, Any]] = {}
        
        for component in components:
            if component.status == ComplianceStatus.NON_COMPLIANT:
                # Create a key based on ecosystem and detected endpoint
                key = f"{component.ecosystem}::{component.detected_endpoint or 'none'}"
                
                if key not in findings_by_key:
                    findings_by_key[key] = {
                        "ecosystem": component.ecosystem,
                        "detected_endpoint": component.detected_endpoint,
                        "message": (
                            "No repository-level registry configuration detected"
                            if not component.detected_endpoint
                            else "Registry does not match expected compliant endpoint"
                        ),
                        "recommendation": "Configure registry to approved Artifactory endpoint",
                        "affected_count": 0,
                        "sample_component": component
                    }
                
                findings_by_key[key]["affected_count"] += 1

        # Create aggregated findings
        for finding_data in findings_by_key.values():
            sample = finding_data.pop("sample_component")
            result.findings.append(
                Finding(
                    component=sample,
                    message=finding_data["message"],
                    recommendation=finding_data["recommendation"],
                    affected_count=finding_data["affected_count"],
                )
            )

        # Generate high-level recommendations
        if findings_by_key:
            if "npm" in [f["ecosystem"] for f in findings_by_key.values()]:
                result.recommendations.append(
                    "Add .npmrc or publishConfig.registry pointing to Artifactory virtual repo"
                )
            if "python" in [f["ecosystem"] for f in findings_by_key.values()]:
                result.recommendations.append(
                    "Add pip.conf (index-url) or use --index-url to approved PyPI virtual repo"
                )

            result.recommendations.append(
                "Route public dependencies through organization Artifactory proxies"
            )

            for finding_data in findings_by_key.values():
                result.recommendations.append(
                    f"Update {finding_data['ecosystem']} configuration to approved endpoint "
                    f"({finding_data['affected_count']} components affected)"
                )

        logger.debug(
            f"Generated {len(result.findings)} aggregated findings and {len(result.recommendations)} recommendations"
        )
