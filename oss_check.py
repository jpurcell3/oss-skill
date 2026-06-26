#!/usr/bin/env python3
"""CLI entrypoint for Option A OSS Check skill (self-contained)."""

import argparse
from pathlib import Path
import sys

from oss_check_impl import ConfigLoader, OSSScannerOrchestrator
from oss_check_impl.utils.formatters import (
    format_terminal,
    format_markdown,
    format_json,
)


def build_orchestrator(config_path: str | None) -> OSSScannerOrchestrator:
    cfg = ConfigLoader(config_path)
    github = cfg.get_github_config()
    artifactory = cfg.get_artifactory_config()
    policy = cfg.get_policy_config()
    jenkins = cfg.get_jenkins_config()
    include_transitive = policy.get("include_transitive_deps", True)
    return OSSScannerOrchestrator(github, artifactory, policy, jenkins, include_transitive)


def main() -> None:
    p = argparse.ArgumentParser(description="OSS Check (Option A)")
    p.add_argument("repo", help="Repository name (defaults to config org)")
    p.add_argument("--org", help="Override GitHub org from config")
    p.add_argument("--ref", default=None, help="Git ref (branch/tag/SHA), default: repo default")
    p.add_argument("--config", default=None, help="Path to config.yaml")
    p.add_argument("--no-jenkins", action="store_true", help="Skip Jenkins evidence phase")
    p.add_argument("-v", "--verbose", action="store_true", help="Verbose output (include findings)")
    p.add_argument(
        "--format",
        choices=["terminal", "markdown", "json"],
        default="markdown",
        help="Output format",
    )
    args = p.parse_args()

    orch = build_orchestrator(args.config)
    org = args.org or orch.github_client.org
    ref = args.ref or orch.github_client.get_default_branch(args.repo)

    result = orch.scan(
        repo_name=args.repo,
        org=org,
        ref=ref,
        include_jenkins=not args.no_jenkins,
        verbose=args.verbose,
    )

    report = result.to_dict()

    if args.format == "terminal":
        output = format_terminal(report, verbose=args.verbose)
    elif args.format == "json":
        output = format_json(report, verbose=args.verbose)
    else:
        output = format_markdown(report, verbose=args.verbose)

    # Ensure sane stdout encoding
    try:
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
    except Exception:
        pass

    print(output)


if __name__ == "__main__":
    main()
