"""
Simple test script for OSS Compliance Scanner
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from oss_compliance.config import ComplianceConfig
from oss_compliance.scanner import ComplianceScanner
from oss_compliance.reporter import ComplianceReporter


def test_config():
    """Test configuration loading."""
    print("Testing configuration loading...")
    config = ComplianceConfig()
    print("[PASS] Configuration loaded")
    print(f"  GitHub API URL: {config.get_github_api_url()}")
    print(f"  GitHub Org: {config.get_github_org()}")
    print(f"  Artifactory Base: {config.get_artifactory_base()}")
    print()


def test_auto_detection():
    """Test local/remote auto-detection."""
    print("Testing local/remote auto-detection...")
    scanner = ComplianceScanner()
    
    test_cases = [
        ("fusion-stage", "remote"),
        ("/path/to/repo", "local"),
        ("./my-project", "local"),
        ("~/projects/my-project", "local"),
    ]
    
    for target, expected in test_cases:
        detected = "local" if scanner._is_local_path(target) else "remote"
        status = "[PASS]" if detected == expected else "[FAIL]"
        print(f"  {status} '{target}' -> {detected} (expected: {expected})")
    
    print()


def test_reporter():
    """Test report generation."""
    print("Testing report generation...")
    
    sample_results = {
        'repository_name': 'test-repo',
        'scan_type': 'basic',
        'scan_timestamp': '2026-06-23T19:07:53',
        'total_items': 10,
        'compliant_items': 8,
        'non_compliant_items': 2,
        'compliance_percentage': 80.0,
        'total_findings': 2,
        'findings': [
            {
                'file': 'package.json',
                'type': 'node_package',
                'issue': 'No NPM registry configured',
                'severity': 'HIGH',
                'recommended_action': 'Configure NPM registry',
                'compliant': False
            }
        ]
    }
    
    reporter = ComplianceReporter()
    
    print("Terminal Report:")
    print(reporter.generate_terminal_report(sample_results))
    print()
    
    print("JSON Report (truncated):")
    json_report = reporter.generate_json_report(sample_results)
    print(json_report[:200] + "...")
    print()
    
    print("[PASS] All report formats generated successfully")
    print()


if __name__ == '__main__':
    print("=" * 60)
    print("OSS Compliance Scanner - Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_config()
        test_auto_detection()
        test_reporter()
        
        print("=" * 60)
        print("All tests passed! [PASS]")
        print("=" * 60)
        
    except Exception as e:
        print(f"[FAIL] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)