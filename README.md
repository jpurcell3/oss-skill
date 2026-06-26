# oss-check

An **OSS compliance checking skill** for AI assistants that validates open source dependencies are sourced through approved Artifactory virtual repositories.

## What this is

This repository contains the **oss-check** skill implementation - a self-contained, lightweight OSS compliance scanner that directly integrates with GitHub, Jenkins, and Artifactory APIs to validate dependency compliance.

### Architecture

The skill is self-contained (Option A from SDD):

- **Skill Layer** (this repo): Complete scanning implementation with no external service dependencies
- **Direct API Integration**: GitHub API, Jenkins API, Artifactory validation
- **Ecosystem Support**: Node/NPM, Python/PyPI, Maven, Go
- **Jenkins Runtime Evidence**: Optional integration to reduce false positives

This approach provides:
- Self-contained deployment (no external service required)
- Lightweight, fast execution
- Direct control over scanning logic
- Easy distribution via AgentOps

**Note:** See [docs/SDD-HLD.md](docs/SDD-HLD.md) for detailed architecture documentation.

## Installation

### Prerequisites

1. **Python 3.8+**
2. **AgentOps Framework** for skill distribution (optional, for IDE integration)
3. **Access to**: GitHub Enterprise API, Jenkins Server, Artifactory Server

### Skill Installation

#### Option 1: Standalone CLI (Recommended for testing)

```bash
cd projects/oss-skill
pip install -r requirements.txt
python oss_check.py <repo> [options]
```

#### Option 2: AgentOps Framework (for IDE integration)

```bash
cd AgentOps
bash scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/oss-check'
```

### Configuration

Configure the skill by editing `config.yaml` (searched in standard locations):

```yaml
github:
  api_url: https://eos2git.cec.lab.emc.com/api/v3
  org: ISG-Edge
  token: ${GITHUB_TOKEN}  # or set directly

jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net
  user: ${JENKINS_USER}
  token: ${JENKINS_TOKEN}

artifactory:
  base_url: isgedge.artifactory.cec.lab.emc.com
  allowed_hosts:
    - isgedge.artifactory.cec.lab.emc.com
    - hopjpd.artifactory.cec.lab.emc.com  # Additional Artifactory hosts
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    maven: isgedge-maven-virtual
    go: isgedge-go-virtual
    # ... other repos

policy:
  npm_registry_url: "https://{base}/artifactory/api/npm/{npm}/"
  pypi_simple_url: "https://{base}/artifactory/api/pypi/{pypi}/simple/"
  maven_repo_url: "https://{base}/artifactory/{maven}/"
  go_proxy_url: "https://{base}/artifactory/api/go/{go}/"
  include_transitive_deps: true  # Parse lockfiles for transitive dependencies
```

## Usage

### Standalone CLI

```bash
python oss_check.py <repo> [options]
```

#### Options
- `repo` (positional) - Repository name to scan
- `--org ORG` - GitHub organization (defaults to config)
- `--ref REF` - Git reference (branch/tag/SHA, defaults to repo default)
- `--config PATH` - Path to config.yaml
- `--no-jenkins` - Skip Jenkins runtime evidence phase
- `-v, --verbose` - Include detailed findings
- `--format {terminal|markdown|json}` - Output format (default: markdown)

#### Examples

```bash
# Basic scan
python oss_check.py fusion-stage --org ISG-Edge --ref main

# Verbose with findings
python oss_check.py fusion-stage --org ISG-Edge --ref main -v

# JSON output
python oss_check.py fusion-stage --org ISG-Edge --ref main --format json

# Skip Jenkins phase
python oss_check.py fusion-stage --org ISG-Edge --ref main --no-jenkins

# Use specific config
python oss_check.py fusion-stage --config c:\path\to\config.yaml -v
```

### IDE Integration (AgentOps)

Once installed via AgentOps, invoke the skill:

```
@oss-check fusion-stage
```

The skill will use the configuration from `.agents/skills/engineering/oss-check/config.yaml`.

## Documentation

- [SDD HLD](docs/SDD-HLD.md) - High-level design and architecture
- This README - Usage and configuration

## Architecture Overview

```
AI Assistant → OSS Check Skill → GitHub API, Jenkins API, Artifactory
                                   ↓
                            OSSScannerOrchestrator
                                   ↓
                            Ecosystem Scanners (NPM, Python, Maven, Go)
                                   ↓
                            Jenkins Analyzer
                                   ↓
                            Compliance Assessment
```

The skill:
1. Loads configuration from `config.yaml`
2. Detects manifest files in repository (package.json, requirements.txt, etc.)
3. Parses manifests and extracts components
4. Analyzes registry configuration (npmrc, pip.conf, etc.)
5. Optionally fetches Jenkins runtime evidence
6. Assesses compliance status (COMPLIANT, TRANSLATED, NON_COMPLIANT)
7. Generates findings and recommendations
8. Formats and displays results

## Distribution Strategy

### Current State

- Self-contained skill implementation in `projects/oss-skill/`
- No external service dependencies
- Can be used standalone or via AgentOps framework
- Configuration via YAML file

### Features

- **Multi-ecosystem support**: NPM, Python, Maven, Go
- **Optional transitive dependencies**: Parse lockfiles (package-lock.json, yarn.lock, etc.)
- **Jenkins runtime evidence**: Detect compliant proxy configurations in CI/CD
- **Artifactory allowlist**: Support multiple Artifactory hosts for compliance
- **Compliance statuses**: COMPLIANT, COMPLIANT_RUNTIME, TRANSLATED, NON_COMPLIANT
- **Flexible output**: Terminal, Markdown, JSON formats
- **Large file handling**: Automatic fallback to raw GitHub API for files >1MB

## Development

### Running the Standalone CLI

```bash
cd projects/oss-skill
python oss_check.py fusion-stage --org ISG-Edge --ref main -v
```

## License

MIT
