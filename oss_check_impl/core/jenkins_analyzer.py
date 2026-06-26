"""Analyze Jenkins jobs for runtime registry evidence."""

import logging
import re
from typing import Dict, Any

from ..utils.jenkins_api import JenkinsAPIClient

logger = logging.getLogger(__name__)


class JenkinsAnalyzer:
    """Lightweight runtime evidence analyzer for Jenkins."""

    def __init__(self, jenkins_cfg: Dict[str, str]):
        url = (jenkins_cfg or {}).get("url", "").strip()
        user = (jenkins_cfg or {}).get("user", "")
        token = (jenkins_cfg or {}).get("token", "")
        self.enabled = bool(url)
        self.client = JenkinsAPIClient(url, user=user, token=token) if url else None

    def _extract_endpoints_from_text(self, text: str) -> Dict[str, str]:
        """Search console text for registry endpoints per ecosystem."""
        ev: Dict[str, str] = {}

        # NPM - multiple patterns to match different Jenkins configurations
        # Pattern 1: npm config set registry <url>
        m = re.search(r"npm\s+config\s+set\s+registry\s+([^\s\n]+)", text)
        if m:
            ev["npm"] = m.group(1).strip()
        
        # Pattern 2: NPM_CONFIG_REGISTRY=<url>
        m = re.search(r"NPM_CONFIG_REGISTRY=([^\s\n]+)", text)
        if m and "npm" not in ev:
            ev["npm"] = m.group(1).strip()
        
        # Pattern 3: registry=<url> (in .npmrc content or shell scripts)
        m = re.search(r"registry\s*=\s*(https?://[^\s\n]+)", text)
        if m and "npm" not in ev:
            candidate = m.group(1).strip()
            # Only treat as npm registry if it looks like an npm registry
            if "npm" in candidate or "artifactory" in candidate:
                ev["npm"] = candidate
        
        # Pattern 4: npm install with --registry flag
        m = re.search(r"npm\s+[^\n]*--registry\s+([^\s\n]+)", text)
        if m and "npm" not in ev:
            ev["npm"] = m.group(1).strip()

        # Python
        m = re.search(r"pip\s+config\s+set\s+global\.index-url\s+([^\s\n]+)", text)
        if m:
            ev["python"] = m.group(1).strip()
        m = re.search(r"--index-url\s+([^\s\n]+)", text)
        if m and "python" not in ev:
            ev["python"] = m.group(1).strip()
        m = re.search(r"PIP_INDEX_URL=([^\s\n]+)", text)
        if m and "python" not in ev:
            ev["python"] = m.group(1).strip()

        # Maven (simple heuristic: any Artifactory URL seen in a mvn command)
        m = re.search(r"mvn[^\"]*https?://[^\s\n\"]+", text)
        if m:
            url_match = re.search(r"https?://[^\s\n\"]+", m.group(0))
            if url_match:
                ev["maven"] = url_match.group(0).strip()

        # Go
        m = re.search(r"GOPROXY=([^\s\n]+)", text)
        if m:
            ev["go"] = m.group(1).strip()
        m = re.search(r"go\s+env\s+-w\s+GOPROXY=([^\s\n]+)", text)
        if m and "go" not in ev:
            ev["go"] = m.group(1).strip()

        return ev

    def _matches_repository(self, job_name: str, repo_name: str, job_config: str = None) -> bool:
        """Check if Jenkins job matches repository using multiple strategies (like scanner)."""
        job_lower = job_name.lower()
        repo_lower = repo_name.lower()
        
        # Strategy 1: Exact substring match
        if repo_lower in job_lower:
            logger.debug(f"Job '{job_name}' matches repo '{repo_name}' (exact substring)")
            return True
        
        # Strategy 2: Match with underscores/hyphens normalized
        repo_normalized = repo_lower.replace('-', '').replace('_', '')
        job_normalized = job_lower.replace('-', '').replace('_', '')
        if repo_normalized in job_normalized:
            logger.debug(f"Job '{job_name}' matches repo '{repo_name}' (normalized)")
            return True
        
        # Strategy 3: Match individual words (for multi-word repos)
        repo_words = set(repo_lower.replace('-', ' ').replace('_', ' ').split())
        job_words = set(job_lower.replace('-', ' ').replace('_', ' ').split())
        
        # Remove common words that don't help matching
        common_words = {'multibranch', 'pipeline', 'build', 'test', 'deploy', 'service', 'svc', 'stage', 'ui', 'system'}
        repo_words_filtered = repo_words - common_words
        job_words_filtered = job_words - common_words
        
        # If any significant words match, consider it a match
        matching_words = repo_words_filtered.intersection(job_words_filtered)
        if matching_words:
            logger.debug(f"Job '{job_name}' matches repo '{repo_name}' (word match: {matching_words})")
            return True
        
        # Strategy 4: Acronym matching (e.g., "fusion-stage" -> "fs")
        if len(repo_words_filtered) >= 2:
            repo_acronym = ''.join([word[0] for word in sorted(repo_words_filtered) if word and len(word) > 0])
            if len(repo_acronym) >= 2 and repo_acronym in job_lower:
                logger.debug(f"Job '{job_name}' matches repo '{repo_name}' (acronym: {repo_acronym})")
                return True
        
        # Strategy 5: GitHub URL matching in job config (if available)
        if job_config:
            # Look for GitHub URL patterns in config
            github_patterns = [
                repo_lower,
                f"/{repo_lower}.git",
                f"/{repo_lower}/",
            ]
            
            config_lower = job_config.lower()
            for pattern in github_patterns:
                if pattern in config_lower:
                    logger.debug(f"Job '{job_name}' matches repo '{repo_name}' (GitHub URL in config)")
                    return True
        
        return False

    def analyze(self, repo_hint: str, max_jobs: int = 50) -> Dict[str, Any]:
        """Analyze Jenkins for jobs related to repo_hint and extract endpoints.

        Returns dict with: jobs_analyzed, configs_found, evidence {ecosystem->endpoint}
        """
        if not self.enabled or not self.client:
            return {"jobs_analyzed": 0, "configs_found": 0, "evidence": {}}

        try:
            all_jobs = self.client.list_all_jobs(max_jobs=50)
            logger.debug(f"Jenkins listed {len(all_jobs)} total jobs")
        except Exception as e:
            logger.warning(f"Failed to list Jenkins jobs: {e}")
            all_jobs = []

        # pick candidate jobs using multi-strategy matching
        repo_lower = (repo_hint or "").lower()
        
        candidates = []
        for j in all_jobs:
            name = j.get("name", "")
            url = j.get("url", "")
            
            # Skip multibranch and branch indexing jobs
            if "multibranch" in name.lower() or "branch-indexing" in name.lower():
                continue
            
            # Try name-based matching first
            if self._matches_repository(name, repo_hint):
                candidates.append(j)
                continue
            
            # For jobs that don't match by name, check recent build console for GitHub URL
            # Check all non-multibranch jobs to find GitHub URL matches
            try:
                console = self.client.get_last_success_console(url) or ""
                if console and self._matches_repository(name, repo_hint, console):
                    candidates.append(j)
            except Exception as e:
                logger.debug(f"Error checking console for {name}: {e}")
                pass
        
        logger.debug(f"Found {len(candidates)} matching jobs")
        # If no candidates with repo match, just take first N jobs as fallback (excluding multibranch)
        if not candidates and all_jobs:
            candidates = [j for j in all_jobs if "multibranch" not in j.get("name", "").lower() and "branch-indexing" not in j.get("name", "").lower()]
            candidates = candidates[:max_jobs]
            logger.debug(f"No repo-specific jobs found, analyzing first {len(candidates)} non-multibranch jobs")
        else:
            # Analyze all non-multibranch jobs, not just matched ones
            all_non_multibranch = [j for j in all_jobs if "multibranch" not in j.get("name", "").lower() and "branch-indexing" not in j.get("name", "").lower()]
            candidates = all_non_multibranch[:max_jobs]
            logger.debug(f"Analyzing all {len(candidates)} non-multibranch jobs for endpoints")

        evidence: Dict[str, str] = {}
        jobs_analyzed = 0
        configs_found = 0

        for job in candidates:
            url = job.get("url")
            if not url:
                continue
            jobs_analyzed += 1
            try:
                cfg = self.client.get_job_config_xml(url) or ""
                console = self.client.get_last_success_console(url) or ""
                logger.debug(f"Job {job.get('name')}: console length={len(console)}, config length={len(cfg)}")
                # Prefer console-based explicit commands
                ev_console = self._extract_endpoints_from_text(console)
                ev_cfg = self._extract_endpoints_from_text(cfg)
                logger.debug(f"Job {job.get('name')}: ev_console={ev_console}, ev_cfg={ev_cfg}")
                for eco, endpoint in {**ev_cfg, **ev_console}.items():
                    if endpoint:
                        # Prefer Artifactory endpoints over others
                        if eco not in evidence:
                            evidence[eco] = endpoint
                            configs_found += 1
                            logger.debug(f"Found {eco} endpoint: {endpoint}")
                        elif "artifactory" in endpoint.lower() and "artifactory" not in evidence[eco].lower():
                            # Replace with Artifactory endpoint if current one isn't
                            evidence[eco] = endpoint
                            logger.debug(f"Replaced {eco} endpoint with Artifactory: {endpoint}")
            except Exception as e:
                logger.debug(f"Error analyzing job {job.get('name')}: {e}")
                continue

        return {"jobs_analyzed": jobs_analyzed, "configs_found": configs_found, "evidence": evidence}
