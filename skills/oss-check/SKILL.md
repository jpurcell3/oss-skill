# OSS Check Skill

> **Skill Type:** Utility / Code Analysis  
> **Domain:** OSS Compliance Scanning  
> **Status:** Active

> **Standalone OSS compliance checking skill for development environments** — Scans repositories for OSS compliance issues without requiring the full web application. Can be used independently in Devin, Claude, or other AI assistants.

---

## Description

This skill provides standalone OSS compliance scanning capabilities that can be used independently of the OSS Compliance Web Application. It scans repositories for compliance issues related to open-source software dependencies, ensuring they are sourced through approved artifact repositories rather than direct public sources.

**Key Capabilities:**
- **Standalone Operation**: Works without web application installation
- **Multiple Scanning Modes**: Basic compliance analysis and enhanced endpoint analysis
- **Flexible Configuration**: Uses environment variables or simple YAML config
- **Multiple Repository Support**: GitHub Enterprise, GitHub.com, and local repositories
- **Terminal-Friendly Output**: CLI-formatted results for easy integration
- **Report Generation**: JSON, Markdown, and summary reports

---

## When to Use This Skill

Invoke this skill when:
- Scanning repositories for OSS compliance issues from command line
- Automating compliance checks in CI/CD pipelines
- Testing configuration without web application UI
- Performing batch operations on multiple repositories
- Debugging scanner behavior with direct code access
- Integrating compliance checks into development workflows

---

## Quick Start

### Installation

```bash
# Add to your project (standalone usage)
cd your-project/
git clone <oss-check-repo> oss-check
cd oss-check
pip install -e .
```

### Basic Usage

```bash
# Scan a local repository
python -m oss_compliance scan --repo-path /path/to/repo

# Scan a remote GitHub repository
python -m oss_compliance scan --repo fusion-stage --org ISG-Edge --api-url https://eos2git.cec.lab.emc.com/api/v3

# Scan with enhanced analysis
python -m oss_compliance scan --repo fusion-stage --enhanced --org ISG-Edge
```

### Environment Variables

```bash
# Required for GitHub scanning
export GITHUB_TOKEN=your_github_token
export GITHUB_API_URL=https://api.github.com
export GITHUB_ORG=your_organization

# Optional for Jenkins integration
export JENKINS_URL=https://your-jenkins-server.com
export JENKINS_USER=your_username
export JENKINS_TOKEN=your_jenkins_token

# Optional for Artifactory configuration
export ARTIFACTORY_BASE=artifactory.example.com
export VIRTUAL_REPO_NPM=npm-virtual
export VIRTUAL_REPO_PYPI=pypi-virtual
export VIRTUAL_REPO_MAVEN=maven-virtual
```

---

## Trigger Phrases

| Trigger Phrase | CLI Command | Action |
|---|---|---|
| "oss-check [name]" | `oss_compliance.py scan [name]` | Scan repository for compliance issues |
| "check OSS compliance of [name]" | `oss_compliance.py scan [name]` | Scan repository for compliance issues |
| "scan repository [name] for OSS compliance" | `oss_compliance.py scan [name]` | Scan repository for compliance issues |
| "scan [name] with enhanced analysis" | `oss_compliance.py scan [name] --enhanced` | Enhanced scan with runtime evidence |
| "scan local repository at [path]" | `oss_compliance.py scan [path]` | Scan local repository (auto-detected) |
| "scan /path/to/repository" | `oss_compliance.py scan /path/to/repository` | Scan local repository (auto-detected) |
| "list repositories from GitHub" | `oss_compliance.py list-repos` | List available repositories |
| "generate compliance report for [name]" | `oss_compliance.py scan [name] --format markdown` | Generate compliance report |
| "check GitHub configuration" | `oss_compliance.py check-config` | Validate GitHub connectivity |

**Note**: The scanner automatically detects whether the target is a local path or remote repository name:
- Contains path separators (`/` or `\`) → local path
- Starts with `.` or `~` → local path  
- Path exists on filesystem → local path
- Otherwise → remote repository name

---

## Input/Output Contract

### Inputs

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `target` | string | Yes | Repository name OR local filesystem path (auto-detected) |
| `use_enhanced` | boolean | No | Enable enhanced endpoint analysis (default: false) |
| `output_format` | string | No | Output format: json, markdown, terminal (default: terminal) |

**Auto-Detection Rules**:
- `fusion-stage` → Remote repository
- `/path/to/repo` → Local repository  
- `./my-project` → Local repository
- `~/projects/my-project` → Local repository
- `my-project` (if exists locally) → Local repository
- `my-project` (if doesn't exist locally) → Remote repository

### Outputs

| Field | Type | Description |
|-------|------|-------------|
| `repository_name` | string | Name of the scanned repository |
| `scan_type` | string | Type of scan performed (basic/enhanced) |
| `scan_timestamp` | string | ISO timestamp of scan |
| `total_items` | integer | Total OSS components found |
| `compliant_items` | integer | Compliant OSS components |
| `non_compliant_items` | integer | Non-compliant OSS components |
| `compliance_percentage` | float | Compliance percentage (0-100) |
| `total_findings` | integer | Total compliance findings |
| `findings` | array | Detailed compliance findings |
| `endpoint_configurations` | array | Endpoint configuration details (enhanced scan) |

---

## Implementation Details

### Core Components

```python
# Main scanner class
class ComplianceScanner:
    def scan_repository(repo_name, repo_path=None, use_enhanced=False)
    def _scan_local_repository(repo_path, repo_name)
    def _scan_remote_repository(repo_name)
    def _scan_go_modules(repo_path)
    def _scan_python_requirements(repo_path)
    def _scan_node_packages(repo_path)
    def _scan_maven_poms(repo_path)

# Configuration manager
class ComplianceConfig:
    def __init__(config_file=None)
    def get_github_token()
    def get_github_api_url()
    def get_github_org()
    def get_virtual_repos()
    def validate()

# Report generator
class ComplianceReporter:
    def generate_report(scan_results, output_format='terminal')
    def generate_json_report(scan_results)
    def generate_markdown_report(scan_results)
    def generate_terminal_report(scan_results)
```

### Scanning Logic

The scanner performs the following analysis:

1. **Go Modules**: Scans `go.mod` files for direct GitHub URLs and GOPROXY configuration
2. **Python Requirements**: Scans `requirements*.txt` files for direct GitHub URLs and index-url configuration
3. **Node Packages**: Scans `package.json` files for registry configuration
4. **Maven POMs**: Scans `pom.xml` files for repository/mirror configuration
5. **Jenkinsfiles**: Scans for direct package installation commands
6. **Dockerfiles**: Scans for direct package installation commands

### Compliance Rules

| File Type | Non-Compliant Pattern | Compliant Configuration |
|-----------|---------------------|------------------------|
| Go Modules | Direct github.com URLs | GOPROXY configured to Artifactory |
| Python | Direct github.com URLs | --index-url pointing to Artifactory |
| Node.js | No registry configured | npm registry pointing to Artifactory |
| Maven | No repository/mirror | Repository/mirror pointing to Artifactory |

---

## Error Handling

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| GitHub API rate limit | Too many API calls | Use caching, increase interval between scans |
| Token decryption failure | Invalid ENCRYPTION_KEY | Verify environment variable is set correctly |
| Repository not found | Incorrect org/repo name | Verify organization and repository name |
| SSL verification error | Self-signed certificates | Set SSL_VERIFY=false in environment |

### Error Recovery

The skill implements automatic retry for transient failures:
- Network timeouts: Retry up to 3 times with exponential backoff
- Rate limiting: Wait for reset before retrying
- Token expiration: Prompt for new token

---

## Examples

### Example 1: Basic Remote Scan

```bash
# Environment setup
export GITHUB_TOKEN=ghp_xxxxxxxxxxxx
export GITHUB_ORG=ISG-Edge
export GITHUB_API_URL=https://eos2git.cec.lab.emc.com/api/v3

# Scan repository
python -m oss_compliance scan --repo fusion-stage

# Output
╔════════════════════════════════════════════════════════════╗
║           OSS Compliance Scan Results                      ║
╠════════════════════════════════════════════════════════════╣
║ Repository: fusion-stage                                   ║
║ Instance: eos2git (ISG-Edge)                              ║
║ Scan Type: Basic                                        ║
║ Timestamp: 2026-06-23 19:07:53                            ║
╠════════════════════════════════════════════════════════════╣
║ Total Components: 262                                     ║
║ Compliant: 185     ████████████████████░░░░░░░░░░░░░░░  ║
║ Non-Compliant: 77   ████████░░░░░░░░░░░░░░░░░░░░░░░░░░  ║
║ Compliance: 70.61%                                         ║
║ Status: NEEDS ATTENTION                                   ║
╚════════════════════════════════════════════════════════════╝
```

### Example 2: Local Repository Scan

```bash
# Scan local repository
python -m oss_compliance scan --local /path/to/local/repo --repo-name my-project

# Output
Scanning repository: my-project
[PROGRESS] Scanning Go modules...
[PROGRESS] Scanning Python requirements...
[PROGRESS] Scanning Node packages...
[PROGRESS] Scanning Maven POMs...
[DONE] Scan completed
Total Components: 45
Compliant: 40 (88.89%)
Non-Compliant: 5 (11.11%)
```

### Example 3: Enhanced Scan with Runtime Evidence

```bash
# Enhanced scan with Jenkins integration
export JENKINS_URL=https://your-jenkins.com
export JENKINS_USER=your-user
export JENKINS_TOKEN=your-token

python -m oss_compliance scan --repo fusion-stage --enhanced --org ISG-Edge

# Output includes runtime configuration evidence from Jenkins logs
Runtime Configurations Found:
  - PIP index-url: https://isgedge.artifactory.cec.lab.emc.com/pypi/simple/
  - NPM registry: https://isgedge.artifactory.cec.lab.emc.com/npm/
  - Maven mirror: https://isgedge.artifactory.cec.lab.emc.com/maven/
```

---

## Dependencies

### Required Dependencies

```toml
[dependencies]
requests>=2.31.0
PyYAML>=6.0.1
urllib3>=2.0.0
cryptography>=41.0.0
```

### Optional Dependencies (for enhanced scanning)

```toml
[dependencies.optional]
beautifulsoup4>=4.12.0
lxml>=4.9.0
```

---

## Configuration

### YAML Configuration File

Create `oss_compliance_config.yaml`:

```yaml
github:
  api_url: https://api.github.com
  org: your-organization
  token: your_github_token

jenkins:
  url: https://your-jenkins-server.com
  user: your-username
  token: your_jenkins_token

artifactory:
  base_url: artifactory.example.com
  virtual_repos:
    npm: npm-virtual
    pypi: pypi-virtual
    maven: maven-virtual
    docker: docker-virtual
    go: go-virtual

ssl_verify: false
cache_ttl_hours: 24
```

### Environment Variables Override

Environment variables take precedence over YAML configuration:

```bash
export GITHUB_TOKEN=override_token
export GITHUB_API_URL=override_url
export GITHUB_ORG=override_org
```

---

## Integration with AI Agents

### Devin Integration

Add to `.devin/instructions.md`:

```markdown
## OSS Compliance Scanning

To scan repositories for OSS compliance:
- "Invoke the oss-check skill to scan [repository-name]"
- "Use oss-check to check compliance of [repository-name]"
- "Run OSS compliance scan on [repository-name]"

The skill is located at: oss-check/
```

### Claude Integration

Add to project instructions:

```markdown
## OSS Compliance Scanning

Available commands:
- "Scan repository [name] for OSS compliance"
- "Check OSS compliance of [repository-name]"
- "Generate compliance report for [repository-name]"

Usage: python -m oss_compliance scan --repo [name]
```

---

## Testing

### Unit Tests

```bash
# Run unit tests
pytest tests/test_scanner.py
pytest tests/test_config.py
pytest tests/test_reporter.py
```

### Integration Tests

```bash
# Test with real repository
python -m oss_compliance scan --repo test-repo --org test-org

# Test local repository
python -m oss_compliance scan --local /path/to/test/repo
```

---

## Limitations

### Current Limitations

- **No Real-time Progress**: Only shows final results (no progress bars)
- **Limited Interactive Capabilities**: Compared to full web UI
- **No Visual Charts**: Text-based output only
- **No Database Storage**: Reports are generated but not persisted
- **No PR Creation**: Cannot create pull requests (web app only)

### Future Enhancements

- Real-time progress reporting
- Interactive mode with step-by-step workflows
- Visual report generation (PDF, HTML)
- Database integration for report storage
- PR creation capability
- CI/CD platform integration

---

## Troubleshooting

### Skill Not Found

**Problem**: Skill not loading in AI agent  
**Solution**: Verify skill file exists at `oss-check-skill/` and is properly configured in agent instructions

### Configuration Issues

**Problem**: Configuration not loading  
**Solution**: Verify `oss_compliance_config.yaml` exists and YAML syntax is valid

### API Issues

**Problem**: GitHub API calls failing  
**Solution**: Verify token has required permissions, check rate limits, test network connectivity

---

## Version History

- **v1.0** (2026-06-23): Initial standalone skill creation
  - Basic and enhanced scanning capabilities
  - GitHub and local repository support
  - Terminal-friendly output
  - Environment variable configuration
  - Report generation (JSON, Markdown, terminal)

---

## Related Documentation

- [README.md](README.md) - Project overview and setup
- [CONFIGURATION.md](docs/CONFIGURATION.md) - Configuration reference
- [API_REFERENCE.md](docs/API_REFERENCE.md) - API documentation (if applicable)
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines

---

**Skill Version**: 1.0  
**Last Updated**: 2026-06-23  
**Maintained By**: Development Team  
**Dependencies**: Python 3.9+, requests>=2.31.0, PyYAML>=6.0.1