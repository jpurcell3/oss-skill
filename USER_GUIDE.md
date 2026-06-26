# OSS Check User Guide

**OSS Check** is a skill for scanning repositories for open source software (OSS) compliance. It helps you identify whether dependencies are sourced through approved Artifactory virtual repositories or directly from public registries, with optional Jenkins runtime evidence integration.

---

## Quick Start

### Prerequisites

Before using the skill, you must have the **OSS Compliance Service** deployed and accessible:

1. **Deploy OSS Compliance Service** (`oss-compliance-webapp`)
   - Navigate to `projects/oss-compliance-webapp/`
   - Run locally: `python app.py` (runs on `http://localhost:5000`)
   - Or deploy as Docker container
   - Ensure the service is running before using the skill

2. **Install the Skill**
   The skill is designed for AI assistants like **Devin**. Install it using the AgentOps framework:

```bash
cd AgentOps
bash scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/oss-check'
```

3. **Configure the Skill**
   Edit `.agents/skills/engineering/oss-check/config.yaml` to set the service URL and credentials.

### Basic Usage
Once installed and configured, invoke the skill in your AI assistant:

```
@oss-check fusion-stage
```

---

## What It Does

OSS Check analyzes repositories to determine if their open source dependencies comply with your organization's Artifactory policies. It supports:

- **NPM/Node.js** packages
- **Python/PyPI** packages
- **Maven** dependencies
- **Go modules**
- **Docker** images
- **Helm** charts

The skill integrates with the **OSS Compliance Service** (`oss-compliance-webapp`), which performs comprehensive scanning including:
- Dependency manifest analysis
- Registry/mirror configuration detection
- Jenkins runtime evidence integration
- False positive elimination
- Detailed compliance reporting

**Architecture:** The skill acts as a lightweight wrapper that calls the OSS Compliance Service via HTTP, which then performs the actual scanning using the `RemoteRepositoryScanner` and `ComplianceScanner` components.

---

## Configuration

The skill uses a configuration file located at:
```
.agents/skills/engineering/oss-check/config.yaml
```

### Configuration Structure

```yaml
# Service Configuration
service:
  url: http://localhost:5000  # OSS Compliance Service URL
  timeout: 300  # Request timeout in seconds

# GitHub Configuration
github:
  api_url: https://eos2git.cec.lab.emc.com/api/v3  # Your GitHub Enterprise URL
  org: ISG-Edge                                     # Your GitHub organization
  token: ${GITHUB_TOKEN}  # or set directly (not recommended)

# Jenkins Configuration
jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net   # Your Jenkins server
  # Prefer environment variables: JENKINS_USER and JENKINS_TOKEN
  # user:
  # token:

# Artifactory Configuration
artifactory:
  base_url: isgedge.artifactory.cec.lab.emc.com
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    maven: isgedge-maven-virtual
    docker: isgedge-docker-virtual
    go: isgedge-go-virtual
    helm: isgedge-helm-virtual
    rpm: isgedge-rpm-virtual
    factoryos: isgedge-factoryos-virtual
    debian: isgedge-manufacturing-debian-virtual

# Policy Configuration
policy:
  npm_registry_url: "https://{base}/artifactory/api/npm/{npm}/"
  pypi_simple_url: "https://{base}/artifactory/api/pypi/{pypi}/simple/"
  maven_repo_url: "https://{base}/artifactory/{maven}/"
  go_proxy_url: "https://{base}/artifactory/api/go/{go}/"

# Output Configuration
output:
  format: table  # table, json, or markdown
  show_recommendations: true
  max_findings_display: 50
```

### Setting Up Credentials

**GitHub Token:**
Set via environment variable (recommended):
```bash
export GITHUB_TOKEN=your-github-token
```

**Jenkins Credentials:**
For Jenkins runtime evidence, set environment variables:
```bash
export JENKINS_USER=your-username
export JENKINS_TOKEN=your-token
```

Or add credentials to the config file (less secure):
```yaml
jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net
  user: your-username
  token: your-token
```

---

## Usage Examples

### Basic Repository Scan
```
@oss-check fusion-stage
```

### Include Jenkins Runtime Evidence
```
@oss-check fusion-stage --include-jenkins true
```

### Verbose Mode with Detailed Findings
```
@oss-check fusion-stage -v
```

### Request Specific Output Format
```
@oss-check fusion-stage --format json
@oss-check fusion-stage --format markdown
```

### Combine Options
```
@oss-check fusion-stage --include-jenkins true -v --format json
```

---

## Output Format

### Default Markdown Output

The skill returns a markdown report with:

- **Executive Summary Table**
  - Total components
  - Compliant components
  - Non-compliant components
  - Compliance percentage

- **Findings by Ecosystem**
  - Manifest source
  - Expected compliant endpoint
  - Detected endpoint
  - Compliance status

- **Top Non-Compliant Components**
  - List of problematic packages

- **Remediation Steps**
  - Concrete configuration snippets to fix compliance issues

### JSON Output

When requested, the skill returns JSON with:
```json
{
  "repository_name": "fusion-stage",
  "scan_timestamp": "2026-06-25T20:30:00Z",
  "total_components": 254,
  "compliant_components": 180,
  "non_compliant_components": 74,
  "compliance_percentage": 70.87,
  "component_mappings": [...]
}
```

---

## How It Works

### Architecture Overview

The skill follows a service-based architecture:

1. **Skill Layer** (`simple_oss_check.py`):
   - Loads configuration from `config.yaml`
   - Parses user input (repo name, options)
   - Makes HTTP request to OSS Compliance Service
   - Formats and displays results
   - Handles errors gracefully

2. **Service Layer** (`oss-compliance-webapp`):
   - Receives scan request via HTTP API
   - Downloads repository files
   - Scans dependency manifests
   - Integrates Jenkins runtime evidence
   - Eliminates false positives
   - Returns comprehensive compliance report

3. **External Services**:
   - GitHub API: Repository files and metadata
   - Jenkins API: Build configurations and logs
   - Artifactory: Virtual repository validation

### Scan Process

When you invoke `@oss-check fusion-stage`:

1. **Configuration Loading**: Skill loads config from `config.yaml`
2. **Service Request**: Skill makes HTTP POST to OSS Compliance Service
3. **Repository Download**: Service downloads repository files via GitHub API
4. **Manifest Scanning**: Service scans for dependency files across ecosystems
5. **Jenkins Integration**: Service fetches Jenkins job configs and builds (if enabled)
6. **Compliance Analysis**: Service analyzes endpoints against Artifactory policies
7. **False Positive Elimination**: Service uses runtime evidence to downgrade findings
8. **Report Generation**: Service generates comprehensive compliance report
9. **Result Formatting**: Skill formats results as table/json/markdown
10. **Display**: User sees compliance summary with recommendations

---

## Common Issues

### Service Not Reachable
**Error**: "Could not connect to OSS Compliance Service"

**Solutions**:
1. Verify the OSS Compliance Service is running:
   ```bash
   curl http://localhost:5000/api/health
   ```
2. Check `service.url` in `config.yaml` matches the service location
3. If service is running remotely, ensure network connectivity and firewall rules allow access
4. Check service logs for errors

### Skill Not Showing Up in Devin
1. Verify the skill files exist: `.agents/skills/engineering/oss-check/`
2. Verify the bridge exists: `.devin/skills/oss-check`
3. Restart Devin if needed

### Jenkins Evidence Not Detected
- Ensure `jenkins.url` is configured in `config.yaml`
- Provide Jenkins credentials via environment variables or config file
- Verify Jenkins job name may not match repository exactly (service uses fuzzy matching)
- Check Jenkins API accessibility from the service

### GitHub Access Issues
- Verify GitHub token has appropriate scopes (repo, read:org)
- Check `github.api_url` in config matches your GitHub Enterprise instance
- Ensure the service can reach the GitHub API

### Scan Timeout
**Error**: "Scan exceeded timeout limit"

**Solutions**:
1. Increase `service.timeout` in `config.yaml` (default: 300 seconds)
2. For large repositories, consider scanning without Jenkins evidence first
3. Check if the repository has an unusually large number of dependencies

---

## Troubleshooting

### Service Health Check
Verify the OSS Compliance Service is running and healthy:
```bash
curl http://localhost:5000/api/health
# Expected response: {"status":"healthy","version":"...","timestamp":"..."}
```

### Skill Discovery
If Devin doesn't discover the skill:
```bash
# Check bridge exists
Get-ChildItem .devin\skills | Select-Object Name,LinkType,Target

# Check skill files exist
ls .agents\skills\engineering\oss-check
```

### Configuration Validation
Test your configuration by asking the skill to check a repository you know exists.

### Authentication Issues
Test external service accessibility from the OSS Compliance Service:

**GitHub:**
```bash
curl -H "Authorization: token $GITHUB_TOKEN" $GITHUB_API_URL/user
```

**Jenkins:**
```bash
curl -u $JENKINS_USER:$JENKINS_TOKEN $JENKINS_URL/api/json
```

---

## Advanced Usage

### Running Without AgentOps Framework

For testing or standalone use, you can run the skill script directly:

```bash
cd projects/oss-skill
python simple_oss_check.py fusion-stage --include-jenkins true
python simple_oss_check.py fusion-stage -v  # verbose mode
python simple_oss_check.py fusion-stage --format json
```

**Note:** This still requires the OSS Compliance Service to be running.

### Scan Multiple Repositories
You can scan multiple repositories sequentially:

```
@oss-check fusion-stage
@oss-check fusion-apiservice
@oss-check dap-ui
```

### Custom Artifactory Endpoints
Modify the `policy` section in `config.yaml` to customize expected compliant endpoints for your organization.

---

## Best Practices

1. **Ensure Service Availability**: Always verify the OSS Compliance Service is running before using the skill
2. **Keep Configuration Updated**: Regularly update Artifactory virtual repository names in `config.yaml`
3. **Use Environment Variables**: Store sensitive credentials in environment variables rather than config files
4. **Test with Known Repositories**: Validate skill behavior with repositories you know are compliant
5. **Review Recommendations**: Always review the remediation steps provided by the skill
6. **Monitor Service Health**: Check service health endpoint periodically to ensure availability
7. **Use Verbose Mode for Debugging**: Use `-v` flag when troubleshooting scan issues

---

## Deployment Options

### Local Development

For local development and testing:

1. **Start the OSS Compliance Service:**
   ```bash
   cd projects/oss-compliance-webapp
   python app.py
   ```

2. **Run the skill directly:**
   ```bash
   cd projects/oss-skill
   python simple_oss_check.py fusion-stage
   ```

### Container Deployment

For production or team use:

1. **Build the service Docker image:**
   ```bash
   cd projects/oss-compliance-webapp
   docker build -t oss-compliance-service:latest .
   ```

2. **Run the service container:**
   ```bash
   docker run -d -p 5000:5000 \
     -e GITHUB_TOKEN=$GITHUB_TOKEN \
     -e JENKINS_USER=$JENKINS_USER \
     -e JENKINS_TOKEN=$JENKINS_TOKEN \
     oss-compliance-service:latest
   ```

3. **Update skill config to point to container URL:**
   ```yaml
   service:
     url: http://localhost:5000
   ```

### Team/Shared Deployment

For team-wide deployment:

1. Deploy the OSS Compliance Service to a shared server or Kubernetes cluster
2. Provide the service URL to team members
3. Each team member installs the skill via AgentOps
4. Each member configures their skill to point to the shared service
5. Credentials can be managed centrally or per-user via environment variables

---

## Architecture Notes

### Current Implementation (Phase 1)

The current implementation uses a **library import** approach:
- The skill script (`simple_oss_check.py`) directly imports `RemoteRepositoryScanner` from `oss-compliance-webapp`
- This requires `oss-compliance-webapp` to be available in the local filesystem
- The skill and scanner run in the same Python process

### Recommended Implementation (Phase 2)

See [SDD HLD](docs/SDD-HLD.md) for the recommended **service-based** architecture:
- Package `oss-compliance-webapp` as a standalone service with REST API
- Skill calls service via HTTP instead of importing as library
- Clear separation of concerns and easier distribution
- Service can be deployed independently (local, container, or server)

### Migration Path

The SDD HLD document outlines a phased migration approach:
- **Phase 1** (Current): Library import, manual setup
- **Phase 2**: Add REST API to oss-compliance-webapp
- **Phase 3**: Migrate skill to call service API
- **Phase 4**: Package and distribute both components

See [docs/SDD-HLD.md](docs/SDD-HLD.md) for complete migration details.

---

## Support

For issues or questions:
- Check the skill documentation: `.agents/skills/engineering/oss-check/SKILL.md`
- Verify configuration: `.agents/skills/engineering/oss-check/config.yaml`
- Test with a simple repository first
