#!/usr/bin/env python3
"""
OSS Compliance Scanner - CLI Entry Point

Standalone command-line interface for OSS compliance scanning.
Intelligently determines local vs. remote repositories automatically.
"""

import argparse
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oss_compliance.scanner import ComplianceScanner
from oss_compliance.config import ComplianceConfig
from oss_compliance.reporter import ComplianceReporter


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description='OSS Compliance Scanner - Standalone compliance scanning tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python oss_compliance.py scan fusion-stage
  python oss_compliance.py scan /path/to/local/repo
  python oss_compliance.py scan fusion-stage --format json
  python oss_compliance.py list-repos
  python oss_compliance.py check-config
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', help='Scan repository for OSS compliance')
    scan_parser.add_argument('target', help='Repository name or local path (auto-detected)')
    scan_parser.add_argument('--format', choices=['terminal', 'json', 'markdown'], 
                       default='terminal', help='Output format')
    scan_parser.add_argument('--config', help='Path to configuration file')
    
    # List repositories command
    list_parser = subparsers.add_parser('list-repos', help='List available repositories')
    list_parser.add_argument('--config', help='Path to configuration file')
    
    # Check config command
    check_parser = subparsers.add_parser('check-config', help='Validate configuration')
    check_parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    # Load configuration
    config = ComplianceConfig(args.config)
    
    # Execute command
    if args.command == 'scan':
        scanner = ComplianceScanner(config)
        results = scanner.scan_repository(args.target)
        
        # Generate report
        reporter = ComplianceReporter()
        report = reporter.generate_report(results, args.format)
        print(report)
        
    elif args.command == 'list-repos':
        scanner = ComplianceScanner(config)
        repos = scanner.list_repositories()
        print(f"Available repositories: {len(repos)}")
        for repo in repos:
            print(f"  - {repo}")
    
    elif args.command == 'check-config':
        config = ComplianceConfig(args.config)
        if config.validate():
            print("[PASS] Configuration is valid")
            print(f"  GitHub API URL: {config.get_github_api_url()}")
            print(f"  GitHub Organization: {config.get_github_org()}")
            print(f"  Artifactory Base: {config.get_artifactory_base()}")
        else:
            print("[FAIL] Configuration validation failed")
            sys.exit(1)


if __name__ == '__main__':
    main()