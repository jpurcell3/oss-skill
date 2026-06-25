#!/usr/bin/env python3
"""
Simple OSS Compliance Checker
Standalone script with no external dependencies
"""

import sys
import json
import base64
import urllib.request
import urllib.error
import yaml
from pathlib import Path

def load_config():
    """Load configuration from config file"""
    config_path = Path('.devin/skills/oss-check/config.yaml')
    if not config_path.exists():
        config_path = Path('.agents/skills/engineering/oss-check/config.yaml')
    
    if not config_path.exists():
        print("Error: config.yaml not found")
        sys.exit(1)
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def make_github_api_call(url, token):
    """Make a GitHub API call with authentication"""
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'OSS-Check-Script'
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        # Disable SSL verification for internal GitHub Enterprise
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            data = response.read()
            return json.loads(data.decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        print(f"HTTP Error {e.code}: {e.reason}")
        return None
    except Exception as e:
        print(f"Error making API call: {e}")
        return None

def check_file_exists(api_url, token, org, repo, file_path):
    """Check if a file exists in the repository"""
    url = f"{api_url}/repos/{org}/{repo}/contents/{file_path}"
    return make_github_api_call(url, token)

def get_file_content(api_url, token, org, repo, file_path):
    """Get file content from repository"""
    url = f"{api_url}/repos/{org}/{repo}/contents/{file_path}"
    result = make_github_api_call(url, token)
    
    if result and 'content' in result:
        try:
            content = base64.b64decode(result['content']).decode('utf-8')
            return content
        except Exception as e:
            print(f"Error decoding {file_path}: {e}")
            return None
    return None

def check_jenkins_job(jenkins_url, user, token, repo_name):
    """Check Jenkins for runtime evidence"""
    if not jenkins_url or not user or not token:
        return None
    
    try:
        import ssl
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        
        # Get job list
        auth_url = f"{jenkins_url}/api/json"
        req = urllib.request.Request(auth_url)
        
        # Add basic auth
        credentials = f"{user}:{token}"
        b64_credentials = base64.b64encode(credentials.encode()).decode()
        req.add_header('Authorization', f'Basic {b64_credentials}')
        
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            jobs_data = json.loads(response.read().decode('utf-8'))
            
            # Look for jobs matching the repo name
            matching_jobs = []
            if 'jobs' in jobs_data:
                for job in jobs_data['jobs']:
                    if repo_name.lower() in job['name'].lower():
                        matching_jobs.append(job)
            
            return matching_jobs[:3]  # Limit to 3 matches
    except Exception as e:
        print(f"Jenkins check failed: {e}")
        return None

def scan_repository(repo_name, config, include_jenkins=False):
    """Scan a repository for OSS compliance"""
    api_url = config['github']['api_url']
    org = config['github']['org']
    token = config['github'].get('token')
    
    if not token:
        print("Error: No GitHub token found in config")
        return None
    
    print(f"Scanning repository: {org}/{repo_name}")
    print("=" * 60)
    
    # Step 1: Check for dependency manifests
    print("\n[1] Checking for dependency manifests...")
    manifests = {
        'package.json': check_file_exists(api_url, token, org, repo_name, 'package.json'),
        'requirements.txt': check_file_exists(api_url, token, org, repo_name, 'requirements.txt'),
        'pyproject.toml': check_file_exists(api_url, token, org, repo_name, 'pyproject.toml'),
        'pom.xml': check_file_exists(api_url, token, org, repo_name, 'pom.xml'),
        'go.mod': check_file_exists(api_url, token, org, repo_name, 'go.mod')
    }
    
    found_manifests = [k for k, v in manifests.items() if v is not None]
    print(f"Found manifests: {', '.join(found_manifests) if found_manifests else 'None'}")
    
    if not found_manifests:
        print("No supported dependency manifests found")
        return None
    
    # Step 2: Check for registry configuration
    print("\n[2] Checking for registry configuration...")
    config_files = {
        '.npmrc': check_file_exists(api_url, token, org, repo_name, '.npmrc'),
        'pip.conf': check_file_exists(api_url, token, org, repo_name, 'pip.conf'),
        'settings.xml': check_file_exists(api_url, token, org, repo_name, 'settings.xml')
    }
    
    found_configs = [k for k, v in config_files.items() if v is not None]
    print(f"Found config files: {', '.join(found_configs) if found_configs else 'None'}")
    
    # Step 3: Analyze configuration
    print("\n[3] Analyzing configuration...")
    compliance_status = {}
    
    if '.npmrc' in found_configs:
        npmrc_content = get_file_content(api_url, token, org, repo_name, '.npmrc')
        if npmrc_content:
            print(f".npmrc content:")
            print(npmrc_content)
            
            # Check if it uses Artifactory (any Artifactory domain)
            if 'artifactory' in npmrc_content.lower():
                compliance_status['npm'] = 'compliant'
                print(f"[OK] NPM configured to use Artifactory")
            else:
                compliance_status['npm'] = 'non-compliant'
                print(f"[WARNING] NPM not configured to use approved Artifactory")
    
    # Step 4: Jenkins runtime evidence (optional)
    print("\n[4] Checking Jenkins runtime evidence...")
    jenkins_config = config.get('jenkins', {})
    jenkins_url = jenkins_config.get('url')
    jenkins_user = jenkins_config.get('user')
    jenkins_token = jenkins_config.get('token')
    
    if include_jenkins:
        jenkins_jobs = check_jenkins_job(jenkins_url, jenkins_user, jenkins_token, repo_name)
    else:
        jenkins_jobs = None
        print("Jenkins checks skipped (use --include-jenkins to enable)")
    
    if jenkins_jobs:
        print(f"Found {len(jenkins_jobs)} matching Jenkins jobs:")
        for job in jenkins_jobs:
            print(f"  - {job['name']}")
        compliance_status['jenkins'] = 'evidence_found'
    else:
        print("No Jenkins evidence found or no Jenkins credentials configured")
        compliance_status['jenkins'] = 'no_evidence'
    
    # Step 5: Generate report
    print("\n[5] Generating compliance report...")
    print("=" * 60)
    
    compliant_count = sum(1 for v in compliance_status.values() if v in ['compliant', 'evidence_found'])
    total_checks = len(compliance_status)
    
    print(f"\n## OSS Check: {repo_name}")
    print(f"\n| Metric | Value |")
    print(f"|---|:---|")
    print(f"| Total checks | {total_checks} |")
    print(f"| Compliant | {compliant_count} |")
    print(f"| Non-compliant | {total_checks - compliant_count} |")
    print(f"| Compliance | {compliant_count/total_checks*100 if total_checks > 0 else 0:.1f}% |")
    
    print(f"\n### Key findings:")
    for check, status in compliance_status.items():
        symbol = "[OK]" if status in ['compliant', 'evidence_found'] else "[WARNING]"
        print(f"- {symbol} {check}: {status}")
    
    print(f"\n### Recommendations:")
    if compliance_status.get('npm') == 'non-compliant':
        print(f"- Configure .npmrc to use Artifactory registry")
    if compliance_status.get('jenkins') == 'no_evidence':
        print(f"- Configure Jenkins credentials for runtime evidence")
    
    return compliance_status

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python simple_oss_check.py <repo-name> [--include-jenkins]")
        sys.exit(1)
    
    repo_name = sys.argv[1]
    include_jenkins = '--include-jenkins' in sys.argv
    
    print("Simple OSS Compliance Checker")
    print("=" * 60)
    
    try:
        config = load_config()
        print(f"Configuration loaded:")
        print(f"  - GitHub API: {config['github']['api_url']}")
        print(f"  - Organization: {config['github']['org']}")
        print(f"  - Artifactory: {config['artifactory']['base_url']}")
        
        result = scan_repository(repo_name, config, include_jenkins)
        
        if result:
            print("\n[OK] Scan completed successfully")
        else:
            print("\n[ERROR] Scan failed")
            sys.exit(1)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
