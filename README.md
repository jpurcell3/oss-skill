# oss-check

An **OSS compliance checking skill** for AI assistants that validates open source dependencies are sourced through approved Artifactory virtual repositories.

## What this is

This repository contains the **oss-check** skill implementation. The skill provides comprehensive OSS compliance scanning by integrating with the **OSS Compliance Service** (`oss-compliance-webapp`), which performs detailed analysis of dependencies across multiple ecosystems (Node/NPM, Python/PyPI, Maven, Go, Docker) with optional Jenkins runtime evidence integration.

### Architecture

The skill follows a service-based architecture:

- **Skill Layer** (this repo): Lightweight wrapper that handles configuration, user interaction, and result formatting
- **Service Layer** (`oss-compliance-webapp`): Comprehensive scanning service with full compliance logic
- **External Services**: GitHub API, Jenkins API, Artifactory

This approach allows the skill to remain lightweight while leveraging the powerful, battle-tested scanning capabilities of the full compliance scanner.

**Note:** This implementation represents a service-based approach. See [docs/SDD-HLD.md](docs/SDD-HLD.md) for detailed architecture documentation and alternative approaches.

## Installation

### Prerequisites

1. **OSS Compliance Service** must be deployed and accessible
   - See [OSS Compliance Webapp](../oss-compliance-webapp/) for service setup
   - Service can run locally (`python app.py`) or as a Docker container
   - Default URL: `http://localhost:5000`

2. **AgentOps Framework** for skill distribution
   - Clone AgentOps repository
   - Follow AgentOps setup instructions

### Skill Installation

Install the skill using the AgentOps framework:

```bash
cd AgentOps
bash scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/oss-check'
```

### Configuration

Configure the skill by editing `.agents/skills/engineering/oss-check/config.yaml`:

```yaml
service:
  url: http://localhost:5000  # OSS Compliance Service URL
  timeout: 300

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
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    maven: isgedge-maven-virtual
    go: isgedge-go-virtual
    # ... other repos
```

## Usage

Once installed and configured, invoke the skill in your AI assistant:

```
@oss-check fusion-stage
```

### Options

- `--include-jenkins true|false` - Include Jenkins runtime evidence (default: true)
- `-v` - Verbose mode with detailed findings
- `--format table|json|markdown` - Output format (default: table)

### Examples

```
@oss-check fusion-stage --include-jenkins true
@oss-check fusion-stage -v
@oss-check org/repo --format json
```

See the [User Guide](USER_GUIDE.md) for detailed usage instructions and configuration options.

## Documentation

- [User Guide](USER_GUIDE.md) - Detailed usage and configuration
- [SDD HLD](docs/SDD-HLD.md) - High-level design and architecture
- [Technical Specs](docs/technical-specs.md) - API specifications and technical details

## Architecture Overview

```
AI Assistant → OSS Check Skill → OSS Compliance Service → External APIs
                                   ↓
                            RemoteRepositoryScanner
                                   ↓
                            ComplianceScanner
                                   ↓
                            GitHub, Jenkins, Artifactory
```

The skill:
1. Loads configuration from `config.yaml`
2. Parses user input (repo name, options)
3. Makes HTTP request to OSS Compliance Service
4. Formats and displays results
5. Handles errors gracefully

## Distribution Strategy

### Current State (Phase 1)

- Skill implementation in `projects/oss-skill/`
- Requires `oss-compliance-webapp` to be available locally
- Manual setup of both components

### Recommended Approach (Phase 2+)

See [SDD HLD](docs/SDD-HLD.md) for the recommended service-based architecture:
- Package OSS Compliance Service as Docker image
- Move skill to AgentOps global skills
- Skill calls service via REST API
- Clear separation of concerns and distribution mechanism

## Development

### Running the Standalone Script

For testing without the full AgentOps framework:

```bash
cd projects/oss-skill
python simple_oss_check.py fusion-stage --include-jenkins true
python simple_oss_check.py fusion-stage -v  # verbose mode
```

### Setting Up the Service

```bash
cd projects/oss-compliance-webapp
python app.py  # Runs service on localhost:5000
```

## License

MIT
