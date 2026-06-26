#!/usr/bin/env python3
"""Simple OSS check harness that reuses the remote scanner from the compliance tool."""

import argparse
import os
os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
import sys
from contextlib import contextmanager
from pathlib import Path

try:
    import yaml
except ImportError:  # pragma: no cover - fallback in constrained environments
    print("Please install PyYAML to run the OSS compliance check.")
    sys.exit(1)

CONFIG_LOCATIONS = [
    Path('.devin/skills/oss-check/config.yaml'),
    Path('.agents/skills/engineering/oss-check/config.yaml'),
]


def load_config():
    for candidate in CONFIG_LOCATIONS:
        if candidate.exists():
            with open(candidate, 'r', encoding='utf-8') as fh:
                return yaml.safe_load(fh)
    raise FileNotFoundError('oss-check config.yaml not found in expected locations')


@contextmanager
def change_directory(path: Path):
    original = Path.cwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(original)


def configure_environment(config: dict):
    github = config.get('github', {})
    for var, value in (
        ('GITHUB_API_URL', github.get('api_url')),
        ('GITHUB_ORG', github.get('org')),
        ('GITHUB_TOKEN', github.get('token')),
    ):
        if value:
            os.environ[var] = str(value).strip()

    artifactory = config.get('artifactory', {})
    if artifactory.get('base_url'):
        os.environ['ARTIFACTORY_BASE'] = artifactory['base_url']
    for repo_name, repo_value in artifactory.get('virtual_repos', {}).items():
        if repo_value:
            key = f'VIRTUAL_REPO_{repo_name.upper()}'
            os.environ[key] = repo_value

    jenkins = config.get('jenkins', {})
    if jenkins.get('user'):
        os.environ['JENKINS_USER'] = jenkins['user']
    if jenkins.get('token'):
        os.environ['JENKINS_API_TOKEN'] = jenkins['token']
    if jenkins.get('url'):
        os.environ['JENKINS_URLS'] = jenkins['url']


def build_jenkins_config(config: dict, include_jenkins: bool) -> dict | None:
    if not include_jenkins:
        return None
    jenkins = config.get('jenkins', {})
    if not jenkins:
        return None
    urls = []
    url_value = jenkins.get('url')
    if url_value:
        urls.append(url_value.strip())
    return {
        'user': jenkins.get('user'),
        'token': jenkins.get('token'),
        'urls': urls,
    }


def build_github_instance(config: dict) -> dict:
    github = config.get('github', {})
    return {
        'api_url': github.get('api_url'),
        'token': github.get('token'),
        'org': github.get('org'),
    }


def format_table(total: int, compliant: int, non_compliant: int, compliance_pct: float) -> None:
    table = [
        ('Metric', 'Value'),
        ('Total components', total),
        ('Compliant', compliant),
        ('Non-compliant', non_compliant),
        ('Compliance', f"{compliance_pct:.1f}%"),
    ]

    width_left = max(len(str(name)) for name, _ in table) + 2
    width_right = max(len(str(value)) for _, value in table) + 2
    horizontal = '─' * (width_left + width_right + 3)

    print(f'┌{horizontal}┐')
    for index, (name, value) in enumerate(table):
        left = f' {name}'.ljust(width_left)
        right = str(value).rjust(width_right - 1)
        print(f'│{left}│ {right} │')
        if index == 0:
            print(f'├{horizontal}┤')
        elif index < len(table) - 1:
            print(f'├{horizontal}┤')
    print(f'└{horizontal}┘')


def print_summary(report: dict, verbose: bool) -> None:
    component_summary = report.get('summary', {}).get('component_analysis', {})
    if not component_summary:
        fallback = report.get('scan_summary', {})
        total = fallback.get('total_items', 0)
        compliant = fallback.get('compliant_items', 0)
        non_compliant = fallback.get('non_compliant_items', 0)
        compliance_pct = fallback.get('compliance_percentage', 0.0)
    else:
        total = component_summary.get('total_components', 0)
        compliant = component_summary.get('compliant_components', 0)
        non_compliant = component_summary.get('non_compliant_components', 0)
        compliance_pct = component_summary.get('component_compliance_percentage', 0.0)

    print('\n## OSS Compliance Summary')
    format_table(total, compliant, non_compliant, compliance_pct)

    if verbose:
        print('\n### Top findings (showing up to 5):')
        for finding in report.get('findings', [])[:5]:
            print(f"- {finding.get('severity', 'N/A')}: {finding.get('issue')} (file: {finding.get('file')})")
        print('\n### Recommendations:')
        for rec in report.get('recommendations', [])[:3]:
            print(f"- {rec.get('priority')}: {rec.get('action')} ({rec.get('count')} items)")
    else:
        for rec in report.get('recommendations', [])[:2]:
            print(f"- {rec.get('priority')}: {rec.get('action')} ({rec.get('count')} items)")


def run_scan(repo_name: str, include_jenkins: bool, verbose: bool) -> None:
    config = load_config()
    configure_environment(config)
    github_instance = build_github_instance(config)
    jenkins_config = build_jenkins_config(config, include_jenkins)

    skill_root = Path(__file__).resolve().parent
    oss_root = (skill_root.parent / 'oss-compliance-webapp').resolve()
    if not oss_root.exists():
        raise FileNotFoundError(f'Could not locate oss-compliance-webapp at {oss_root}')

    sys.path.insert(0, str(oss_root))
    try:
        from remote_scanner import RemoteRepositoryScanner, set_debug_logging
    except ImportError as exc:
        raise RuntimeError('Unable to import RemoteRepositoryScanner; ensure oss-compliance-webapp is intact') from exc

    set_debug_logging(False)

    scanner = RemoteRepositoryScanner(
        github_instance_config=github_instance,
        whitelist_urls=config.get('whitelist_urls', []),
        jenkins_config=jenkins_config
    )

    with change_directory(oss_root):
        report = scanner.scan_remote_repository(repo_name)

    print_summary(report, verbose)


def main():
    parser = argparse.ArgumentParser(description='Run OSS compliance scan using the remote scanner harnessed by the skill')
    parser.add_argument('repo', nargs='?', default='fusion-stage', help='Repository name to scan')
    parser.add_argument('--org', help='Override GitHub organization (falls back to config)')
    parser.add_argument('--no-jenkins', action='store_true', help='Skip Jenkins runtime evidence')
    parser.add_argument('-v', '--verbose', action='store_true', help='Emit extended findings')
    args = parser.parse_args()

    if args.org:
        os.environ['GITHUB_ORG'] = args.org

    try:
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='backslashreplace')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='backslashreplace')
    except Exception:
        pass

    try:
        run_scan(args.repo, not args.no_jenkins, args.verbose)
    except Exception as exc:
        print(f'Error running scan: {exc}')
        sys.exit(1)


if __name__ == '__main__':
    main()
