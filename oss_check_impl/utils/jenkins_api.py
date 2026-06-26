"""Jenkins API utilities for runtime evidence detection."""

import base64
import json
import logging
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)


class JenkinsAPIClient:
    """Minimal Jenkins API client (read-only)."""

    def __init__(self, base_url: str, user: str = "", token: str = "", timeout: int = 30):
        self.base_url = base_url.rstrip("/") + "/"
        self.user = user
        self.token = token
        self.timeout = timeout

    def _auth_header(self) -> Dict[str, str]:
        if self.user and self.token:
            raw = f"{self.user}:{self.token}".encode("utf-8")
            encoded = base64.b64encode(raw).decode("ascii")
            return {"Authorization": f"Basic {encoded}"}
        return {}

    def _get(self, url: str, accept: str = "*/*") -> bytes:
        headers = {
            "Accept": accept,
            "User-Agent": "oss-check-skill",
            **self._auth_header(),
        }
        req = Request(url, headers=headers)
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return resp.read()
        except HTTPError as e:
            # Suppress 404 errors - they're expected for jobs without builds
            if e.code == 404:
                logger.debug(f"Jenkins API 404: {url}")
                raise
            logger.error(f"Jenkins API error {e.code}: {e.reason}")
            raise
        except URLError as e:
            logger.error(f"Network error accessing Jenkins: {e.reason}")
            raise

    def get_json(self, path_or_url: str) -> Dict[str, Any]:
        url = path_or_url if path_or_url.startswith("http") else urljoin(self.base_url, path_or_url.lstrip("/"))
        data = self._get(url, accept="application/json")
        try:
            return json.loads(data.decode("utf-8"))
        except Exception:
            return {}

    def get_text(self, path_or_url: str) -> str:
        url = path_or_url if path_or_url.startswith("http") else urljoin(self.base_url, path_or_url.lstrip("/"))
        return self._get(url, accept="text/plain").decode("utf-8", errors="ignore")

    def get_job_children(self, job_url: str) -> List[Dict[str, Any]]:
        # Query sub-jobs (folders) for recursion
        meta = self.get_json(urljoin(job_url.rstrip("/") + "/", "api/json?tree=jobs[name,url]"))
        return meta.get("jobs", []) if isinstance(meta, dict) else []

    def list_all_jobs(self, max_jobs: int = 50) -> List[Dict[str, str]]:
        """List jobs recursively up to a simple cap."""
        jobs: List[Dict[str, str]] = []
        try:
            root = self.get_json("/api/json?tree=jobs[name,url]")
            queue: List[str] = [j["url"] for j in root.get("jobs", []) if isinstance(j, dict) and "url" in j]
            while queue and len(jobs) < max_jobs:
                url = queue.pop(0)
                jobs.append({"name": url.strip("/").split("/")[-1], "url": url})
                # Dive into folders to find nested jobs
                try:
                    children = self.get_job_children(url)
                    for c in children:
                        if isinstance(c, dict) and "url" in c:
                            queue.append(c["url"])
                except Exception:
                    pass
        except Exception:
            logger.debug("Failed to list Jenkins jobs from root")
        return jobs[:max_jobs]

    def get_job_config_xml(self, job_url: str) -> Optional[str]:
        try:
            return self.get_text(urljoin(job_url.rstrip("/") + "/", "config.xml"))
        except Exception:
            return None

    def get_last_success_console(self, job_url: str) -> Optional[str]:
        try:
            return self.get_text(urljoin(job_url.rstrip("/") + "/", "lastSuccessfulBuild/consoleText"))
        except Exception:
            return None
