# OSS Check User Guide

**OSS Check** is a lightweight, agent-native skill for scanning repositories for open source software (OSS) compliance. It helps you identify whether dependencies are sourced through approved Artifactory virtual repositories or directly from public registries.

---

## Quick Start

### Installation
The skill is designed for AI assistants like **Devin**. Install it using the AgentOps framework:

```bash
bash AgentOps/scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/*'
```

### Basic Usage
Once installed, invoke the skill in your AI assistant:

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

The skill uses **agent orchestration** (via `gh` CLI and Jenkins HTTP APIs) rather than a full scanner implementation, making it lightweight and efficient.

---

## Configuration

The skill uses a configuration file located at:
```
.agents/skills/engineering/oss-check/config.yaml
```

### Configuration Structure

```yaml
github:
  api_url: https://eos2git.cec.lab.emc.com/api/v3  # Your GitHub Enterprise URL
  org: ISG-Edge                                     # Your GitHub organization

jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net   # Your Jenkins server
  # Optional. Prefer environment variables:
  # JENKINS_USER and JENKINS_TOKEN
  # user:
  # token:

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

policy:
  npm_registry_url: "https://{base}/artifactory/api/npm/{npm}/"
  pypi_simple_url: "https://{base}/artifactory/api/pypi/{pypi}/simple/"
  maven_repo_url: "https://{base}/artifactory/{maven}/"
  go_proxy_url: "https://{base}/artifactory/api/go/{go}/"
```

### Setting Up Jenkins Credentials (Optional)

For Jenkins runtime evidence, set environment variables:

```bash
export JENKINS_USER=your-username
export JENKINS_TOKEN=your-token
```

Or add credentials to the config file:
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

### Specify Organization
```
@oss-check fusion-stage --org ISG-Edge
```

### Include Jenkins Runtime Evidence
```
@oss-check fusion-stage --include-jenkins true
```

### Request Specific Output Format
```
@oss-check fusion-stage --format markdown
@oss-check fusion-stage --format json
```

### Scan Local Repository
```
@oss-check /path/to/local/repo
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

### 1. Dependency Manifest Detection
The skill uses GitHub API to check for dependency files without cloning the entire repository:

**Node.js:** `package.json`, `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`
**Python:** `requirements.txt`, `pyproject.toml`, `setup.py`, `Pipfile`
**Maven:** `pom.xml`
**Go:** `go.mod`

### 2. Dependency Extraction
For each ecosystem, the skill extracts package names and versions from the manifest files.

### 3. Registry Configuration Analysis
The skill checks for Artifactory configuration:

**NPM:** `.npmrc` file and `publishConfig.registry` in `package.json`
**Python:** `pip.conf`, `pip.ini`, `Pipfile` sources, and `--index-url` directives
**Maven:** `settings.xml` for mirrors/repositories
**Go:** `GOPROXY` settings

### 4. Jenkins Runtime Evidence (Optional)
When enabled, the skill:
- Searches for Jenkins jobs matching the repository name
- Inspects job configuration XML and build logs
- Looks for registry/mirror settings applied during CI

### 5. Compliance Assessment
The skill compares detected endpoints against expected Artifactory virtual repositories and determines compliance status.

---

## Common Issues

### Skill Not Showing Up in Devin
1. Verify the skill files exist: `.agents/skills/engineering/oss-check/`
2. Verify the bridge exists: `.devin/skills/oss-check`
3. Restart Devin if needed

### Jenkins Evidence Not Detected
- Ensure `jenkins.url` is configured in `config.yaml`
- Provide Jenkins credentials via environment variables or config file
- Verify Jenkins job name may not match repository exactly (skill uses fuzzy matching)

### GitHub Access Issues
- Ensure GitHub CLI (`gh`) is installed
- Authenticate to your GitHub Enterprise instance
- Verify token has appropriate scopes

---

## Troubleshooting

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
For GitHub Enterprise:
```bash
gh auth login --hostname eos2git.cec.lab.emc.com --with-token
```

For Jenkins:
```bash
# Test Jenkins access
curl -u $JENKINS_USER:$JENKINS_TOKEN $JENKINS_URL/api/json
```

---

## Advanced Usage

### Scan Multiple Repositories
You can scan multiple repositories sequentially:

```
@oss-check fusion-stage
@oss-check fusion-apiservice
@oss-check dap-ui
```

### Focus on Specific Ecosystem
The skill automatically detects which ecosystems are present. To focus on specific ecosystems, ensure your target repository only contains those dependency files.

### Custom Artifactory Endpoints
Modify the `policy` section in `config.yaml` to customize expected compliant endpoints for your organization.

---

## Best Practices

1. **Keep Configuration Updated**: Regularly update Artifactory virtual repository names in `config.yaml`
2. **Use Environment Variables**: Store sensitive credentials in environment variables rather than config files
3. **Test with Known Repositories**: Validate skill behavior with repositories you know are compliant
4. **Review Recommendations**: Always review the remediation steps provided by the skill
5. **Monitor Jenkins Jobs**: Ensure Jenkins job names follow naming conventions for better fuzzy matching

---

## Support

For issues or questions:
- Check the skill documentation: `.agents/skills/engineering/oss-check/SKILL.md`
- Verify configuration: `.agents/skills/engineering/oss-check/config.yaml`
- Test with a simple repository first
