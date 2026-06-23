# OSS Check Skill

> **Standalone OSS Compliance Checking for Development Environments**  
> **Version:** 1.0.0  
> **Status:** Active

A standalone OSS compliance checking skill that can be used independently in development environments like Devin, Claude, or other AI assistants without requiring the full OSS Compliance Web Application installation.

## 🎯 Purpose

This skill provides core OSS compliance scanning capabilities for:
- Repository scanning (local and remote)
- Compliance analysis and reporting
- Configuration management
- Integration with GitHub, Jenkins, and Artifactory
- CLI-friendly output for automation

## ✨ Key Features

### Intelligent Auto-Detection
The scanner automatically determines whether you're scanning a local repository or a remote repository based on the input:
- `fusion-stage` → Remote repository
- `/path/to/repo` → Local repository
- `./my-project` → Local repository
- `~/projects/my-project` → Local repository

**No need to specify --local or --remote flags!**

### Standalone Operation
- Works without web application installation
- Uses environment variables or simple YAML config
- No database required
- Self-contained Python package

### Multiple Output Formats
- Terminal (default) - ASCII art formatted
- JSON - Machine-readable for automation
- Markdown - Human-readable documentation

## 🚀 Quick Start

### Installation

```bash
# Clone the skill
cd your-project/
git clone <repository-url> oss-skill
cd oss-skill

# Install dependencies
pip install -e .
```

### Basic Usage

```bash
# Scan a remote GitHub repository (auto-detected)
python oss_compliance.py scan fusion-stage

# Scan a local repository (auto-detected)
python oss_compliance.py scan /path/to/repository

# Scan with enhanced analysis
python oss_compliance.py scan fusion-stage --enhanced

# Generate JSON report
python oss_compliance.py scan fusion-stage --format json

# Generate Markdown report
python oss_compliance.py scan fusion-stage --format markdown

# List available repositories
python oss_compliance.py list-repos

# Check configuration
python oss_compliance.py check-config
```

## ⚙️ Configuration

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

### YAML Configuration

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

## 📊 Output Formats

### Terminal (Default)
```
======================================================================
OSS Compliance Scan Results
======================================================================
Repository: fusion-stage
Scan Type: basic
Timestamp: 2026-06-23 19:07:53
----------------------------------------------------------------------
Total Components: 262
Compliant: 185
Non-Compliant: 77
Compliance: 70.61%
Total Findings: 42
----------------------------------------------------------------------
```

### JSON
```json
{
  "repository_name": "fusion-stage",
  "scan_type": "basic",
  "total_items": 262,
  "compliant_items": 185,
  "non_compliant_items": 77,
  "compliance_percentage": 70.61,
  "total_findings": 42
}
```

### Markdown
```markdown
# OSS Compliance Analysis Report

**Repository:** fusion-stage
**Scan Date:** 2026-06-23T19:07:53

## Executive Summary
- **Total Components:** 262
- **Compliant:** 185 (70.61%)
- **Non-Compliant:** 77 (29.4%)
```

## 🔧 Integration with AI Agents

### Devin Integration

Add to `.devin/instructions.md`:

```markdown
## OSS Compliance Checking

To scan repositories for OSS compliance:
- "Invoke the oss-check skill to scan [repository-name]"
- "Use oss-check to check compliance of [repository-name]"
- "Run OSS compliance check on [repository-name]"

The scanner automatically detects local vs. remote repositories.
```

### Claude Integration

Add to project instructions:

```markdown
## OSS Compliance Checking

Available commands:
- "oss-check [name]"
- "Check OSS compliance of [repository-name]"
- "Generate compliance report for [repository-name]"

Usage: python oss_compliance.py scan [name]

The scanner automatically detects local vs. remote repositories.
```

## 📁 Project Structure

```
oss-skill/
├── oss_compliance.py              # CLI entry point
├── src/
│   └── oss_compliance/
│       ├── __init__.py           # Package init
│       ├── scanner.py            # Core scanner with auto-detection
│       ├── config.py             # Configuration manager
│       └── reporter.py            # Report generator
├── skills/
│   └── oss-check/
│       └── SKILL.md               # Skill definition
├── tests/                       # Unit tests
├── docs/                        # Documentation
├── examples/                    # Usage examples
├── pyproject.toml               # Package configuration
└── README.md                    # This file
```

## 🧠 Intelligent Auto-Detection

The scanner uses smart heuristics to determine repository type:

| Input | Detected As | Reason |
|-------|-------------|--------|
| `fusion-stage` | Remote | No path separators |
| `/path/to/repo` | Local | Contains `/` |
| `./my-project` | Local | Starts with `.` |
| `~/projects/my-project` | Local | Starts with `~` |
| `my-project` (exists locally) | Local | Filesystem check |
| `my-project` (doesn't exist) | Remote | Default to remote |

## 📋 Dependencies

```toml
[dependencies]
requests>=2.31.0
PyYAML>=6.0.1
urllib3>=2.0.0
cryptography>=41.0.0
```

## 🧪 Testing

```bash
# Run unit tests
pytest tests/

# Test with real repository
python oss_compliance.py scan test-repo --org test-org

# Test local repository
python oss_compliance.py scan /path/to/test/repo
```

## 🚨 Limitations

### Current Limitations
- No real-time progress bars (only final results)
- Limited interactive capabilities compared to full web UI
- No visual charts or graphs
- No database storage (reports generated but not persisted)
- No PR creation capability (web app only)

### Future Enhancements
- Real-time progress reporting
- Interactive mode with step-by-step workflows
- Visual report generation (PDF, HTML)
- Database integration for report storage
- PR creation capability
- CI/CD platform integration

## 📝 License

MIT License - See LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please see CONTRIBUTING.md for guidelines.

## 📞 Support

For issues or questions, please open an issue in the repository.

---

**Version:** 1.0.0  
**Last Updated:** 2026-06-23  
**Follows:** SDD Framework (AgentOps)