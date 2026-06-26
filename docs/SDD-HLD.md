# OSS Check Skill - High Level Design (HLD)

## 1. Overview

The OSS Check skill is an AI assistant skill that performs open source software compliance scanning on repositories. It validates that dependencies are sourced through approved Artifactory virtual repositories and optionally incorporates Jenkins runtime evidence to reduce false positives.

### 1.1 Current Architecture

The skill is implemented as a **self-contained, lightweight scanner** (Option A):

**Implementation (projects/oss-skill):**
- Location: `projects/oss-skill/oss_check.py`
- Implementation: Complete scanning implementation with direct API integrations
- Components:
  - `OSSScannerOrchestrator`: Main scanning orchestrator
  - Ecosystem scanners: NPM, Python, Maven, Go
  - `JenkinsAnalyzer`: Jenkins runtime evidence extraction
  - `GitHubAPIClient`: GitHub API integration
  - `JenkinsAPIClient`: Jenkins API integration
- Dependencies: No external service dependencies
- Deployment: Standalone CLI or AgentOps skill

**Features:**
- Multi-ecosystem support (NPM, Python, Maven, Go)
- Optional transitive dependency parsing (package-lock.json, yarn.lock, pnpm-lock.yaml)
- Jenkins runtime evidence with multi-strategy job matching (5 strategies)
- Artifactory allowlist support for multiple hosts
- Compliance statuses: COMPLIANT, COMPLIANT_RUNTIME, TRANSLATED, NON_COMPLIANT
- Large file handling (automatic fallback to raw GitHub API)
- Flexible output formats (terminal, markdown, JSON)

## 2. Architecture Decision: Option A (Self-Contained)

### 2.1 Rationale

The self-contained approach was chosen for the following reasons:

1. **Simplicity**: No external service dependencies, easier deployment and troubleshooting
2. **Performance**: Direct API calls, no network overhead between skill and service
3. **Control**: Full control over scanning logic, easier to customize and extend
4. **AgentOps Alignment**: Follows AgentOps skill patterns for lightweight, self-contained skills
5. **Distribution**: Simple to distribute as part of AgentOps or standalone CLI
6. **Maintainability**: Single codebase, no version compatibility issues between skill and service

### 2.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant (Cascade)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ @oss-check fusion-stage
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              OSS Check Skill (oss_check.py)                   │
│  - OSSScannerOrchestrator                                    │
│  - ConfigLoader                                              │
│  - CLI Argument Parsing                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ Direct API Calls
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Scanner Components                         │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Ecosystem Scanners                                  │   │
│  │  - NPMEcosystem (package.json, package-lock.json)    │   │
│  │  - PythonEcosystem (requirements.txt, pyproject.toml) │   │
│  │  - MavenEcosystem (pom.xml)                           │   │
│  │  - GoEcosystem (go.mod)                               │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ JenkinsAnalyzer                                     │   │
│  │  - Multi-strategy job matching (5 strategies)         │   │
│  │  - Console output parsing                           │   │
│  │  - Runtime evidence extraction                       │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ GitHubAPIClient                                      │   │
│  │  - Manifest detection                                │   │
│  │  - File content retrieval (with large file support)  │   │
│  │  - Repository listing                                │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
           │                                 │
           ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│  Jenkins Server  │              │  GitHub API      │
│  - Runtime       │              │  - Repo Files   │
│    Evidence      │              │  - Configs      │
└──────────────────┘              └──────────────────┘
```

### 3.2 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     AI Assistant (Cascade)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ @oss-check fusion-stage
                           ▼
┌─────────────────────────────────────────────────────────────┐
│              OSS Check Skill (AgentOps)                      │
│  - simple_oss_check.py                                       │
│  - config.yaml                                               │
│  - skill.yaml                                                │
│  - SKILL.md                                                  │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           │ HTTP Request
                           │ POST /api/scan
                           ▼
┌─────────────────────────────────────────────────────────────┐
│         OSS Compliance Service (oss-compliance-webapp)       │
│  - Flask Web Service                                         │
│  - RemoteRepositoryScanner                                  │
│  - ComplianceScanner                                        │
│  - Jenkins Integration                                       │
│  - GitHub Integration                                        │
│  - Artifactory Validation                                    │
└──────────┬─────────────────────────────────┬────────────────┘
           │                                 │
           │                                 │
           ▼                                 ▼
┌──────────────────┐              ┌──────────────────┐
│  Jenkins Server  │              │  GitHub API      │
│  - Runtime       │              │  - Repo Files   │
│    Evidence      │              │  - Configs      │
└──────────────────┘              └──────────────────┘
```

### 2.3 Component Details

#### 2.3.1 OSSScannerOrchestrator

**Location:** `oss_check_impl/core/scanner.py`

**Responsibilities:**
- Coordinate scanning workflow across all phases
- Manage ecosystem scanners
- Apply Jenkins runtime evidence
- Assess compliance status
- Generate findings and recommendations

**Phases:**
1. Manifest detection (package.json, requirements.txt, pom.xml, go.mod, lockfiles)
2. Manifest parsing and component extraction
3. Registry configuration analysis (npmrc, pip.conf, etc.)
4. Jenkins runtime evidence (optional)
5. Compliance assessment
6. Findings generation

#### 2.3.2 Ecosystem Scanners

**Location:** `oss_check_impl/ecosystems/`

**NPMEcosystem:**
- Detects: package.json, package-lock.json, yarn.lock, pnpm-lock.yaml
- Parses: Direct and transitive dependencies (optional)
- Detects registry config: .npmrc

**PythonEcosystem:**
- Detects: requirements.txt, pyproject.toml, Pipfile, setup.py
- Parses: Direct dependencies
- Detects registry config: pip.conf, pip.ini, pyproject.toml

**MavenEcosystem:**
- Detects: pom.xml
- Parses: Direct dependencies
- Detects registry config: pom.xml (repositories section)

**GoEcosystem:**
- Detects: go.mod, go.sum
- Parses: Direct dependencies
- Detects registry config: go.mod (proxy directives)

#### 2.3.3 JenkinsAnalyzer

**Location:** `oss_check_impl/core/jenkins_analyzer.py`

**Responsibilities:**
- List all Jenkins jobs
- Match jobs to repository using 5 strategies:
  1. Exact substring match
  2. Normalized name match
  3. Word-based match
  4. Acronym match
  5. GitHub URL in job console output
- Extract runtime evidence from job console output
- Extract registry endpoints from job configs
- Prefer Artifactory endpoints over other registries

#### 2.3.4 GitHubAPIClient

**Location:** `oss_check_impl/utils/github_api.py`

**Responsibilities:**
- Get repository contents
- Get file content (with large file support)
- List files recursively
- Detect manifest files
- Handle GitHub Enterprise API differences

**Large File Handling:**
- Files >1MB trigger automatic fallback to raw content endpoint
- Supports both GitHub.com and GitHub Enterprise raw URL formats

#### 2.3.5 Configuration

**Location:** `config.yaml`

**Configuration Structure:**
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
    - hopjpd.artifactory.cec.lab.emc.com
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    maven: isgedge-maven-virtual
    go: isgedge-go-virtual

policy:
  npm_registry_url: "https://{base}/artifactory/api/npm/{npm}/"
  pypi_simple_url: "https://{base}/artifactory/api/pypi/{pypi}/simple/"
  maven_repo_url: "https://{base}/artifactory/{maven}/"
  go_proxy_url: "https://{base}/artifactory/api/go/{go}/"
  include_transitive_deps: true
```

**Environment Variables:**
- `GITHUB_TOKEN` - GitHub personal access token
- `JENKINS_USER` - Jenkins username
- `JENKINS_TOKEN` - Jenkins API token

## 3. Dependencies

### 3.1 Python Dependencies
- Python 3.8+
- `PyYAML` - Configuration parsing
- `requests` - HTTP client for API calls
- `urllib3` - URL handling

### 3.2 External Dependencies
- GitHub Enterprise API (or GitHub.com)
- Jenkins Server
- Artifactory Server
- Network connectivity to these services

### 3.3 Optional Dependencies
- AgentOps framework (for IDE integration)
- None for standalone CLI usage

## 4. Deployment Flow

### 4.1 Standalone CLI Deployment

1. **Clone Repository:**
   ```bash
   cd projects/oss-skill
   ```

2. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure:**
   - Create or edit `config.yaml`
   - Set GitHub, Jenkins, Artifactory credentials

4. **Run:**
   ```bash
   python oss_check.py <repo> [options]
   ```

### 4.2 AgentOps Skill Deployment

1. **Install Skill via AgentOps:**
   ```bash
   cd AgentOps
   bash scripts/apply-skills.sh \
     --agent devin \
     --project-root <your-project> \
     --path 'engineering/oss-check'
   ```

2. **Configure Skill:**
   - Edit `.agents/skills/engineering/oss-check/config.yaml`
   - Configure GitHub, Jenkins, Artifactory credentials

3. **Invoke:**
   ```
   @oss-check fusion-stage
   ```

### 4.3 Runtime Flow

1. User invokes skill (CLI or IDE)
2. Skill loads configuration from config.yaml
3. Skill detects manifest files in repository
4. Skill parses manifests and extracts components
5. Skill analyzes registry configuration
6. Optionally, skill fetches Jenkins runtime evidence
7. Skill assesses compliance status
8. Skill generates findings and recommendations
9. Skill formats and displays results

## 5. Distribution Strategy

### 5.1 Standalone CLI Distribution
- **As Python Package:**
  - Publish to internal PyPI
  - Install via `pip install oss-check`
  - Run as module: `oss-check <repo> [options]`

- **As Archive:**
  - Distribute as tarball/zip
  - Users extract and run directly
  - No installation required

### 5.2 AgentOps Skill Distribution
- **Via AgentOps:** Skill is part of AgentOps global skills
- **Installation:** Standard AgentOps skill installation
- **Updates:** Via AgentOps release mechanism
- **Size:** Moderate (scanning logic + ecosystem scanners)

### 5.3 Documentation
- Installation guide for standalone and AgentOps usage
- Configuration reference
- Troubleshooting guide
- API documentation for GitHub, Jenkins, Artifactory integrations

## 6. Compliance Statuses

### 6.1 Status Definitions

**COMPLIANT:**\- Repository-level registry configuration matches expected Artifactory endpoint
- Component is compliant at source

**COMPLIANT_RUNTIME:**\- Repository-level configuration does not match expected endpoint
- Jenkins runtime evidence shows component is sourced from compliant Artifactory host
- Component is compliant at runtime (via CI/CD proxy)

**TRANSLATED:**\- Repository-level configuration does not match expected endpoint
- Jenkins runtime evidence shows component is sourced from Artifactory proxy
- Component is translated through Jenkins proxy to compliant endpoint

**NON_COMPLIANT:**\- Repository-level configuration does not match expected endpoint
- No Jenkins runtime evidence found
- Component is non-compliant

### 6.2 Status Determination Logic

1. **Initial Assessment:**
   - Check repository-level registry configuration (npmrc, pip.conf, etc.)
   - If matches expected Artifactory endpoint → COMPLIANT
   - If does not match → NON_COMPLIANT (pending Jenkins evidence)

2. **Jenkins Evidence Application:**
   - If Jenkins evidence shows component from allowed Artifactory host:
     - If host is expected endpoint → COMPLIANT_RUNTIME
     - If host is proxy → TRANSLATED
   - If no Jenkins evidence → NON_COMPLIANT

3. **Artifactory Allowlist:**
   - Check if runtime evidence host is in `artifactory.allowed_hosts`
   - Only allowlist hosts are considered for COMPLIANT_RUNTIME/TRANSLATED status

## 7. Security Considerations

1. **Credentials:**
   - GitHub, Jenkins, Artifactory credentials stored in config.yaml
   - Use environment variables where possible (preferred)
   - Never log credentials in output
   - Config file should not be committed to version control

2. **Network Security:**
   - Skill needs access to GitHub, Jenkins, Artifactory APIs
   - Configure firewall rules appropriately
   - Use internal network when possible
   - HTTPS required for all API communications

3. **Artifactory Access:**
   - Credentials must have read access to virtual repositories
   - Allowlist hosts should be validated
   - Regular review of allowed hosts list

## 8. Monitoring and Observability

1. **Logging:**
   - Log scan phases and progress
   - Track component counts and compliance status
   - Error logging for troubleshooting
   - Debug logs for API calls

2. **Metrics:**
   - Scan duration per phase
   - Component counts by ecosystem
   - Jenkins jobs analyzed vs. matched
   - Runtime configs found
   - Compliance percentages

3. **Output:**
   - Summary table with key metrics
   - Detailed findings in verbose mode
   - JSON output for integration with other tools

## 9. Future Enhancements

1. **Additional Ecosystems:**
   - Docker (Dockerfile, docker-compose.yml)
   - Ruby (Gemfile, Gemfile.lock)
   - PHP (composer.json, composer.lock)
   - Rust (Cargo.toml, Cargo.lock)

2. **Enhanced Jenkins Integration:**
   - Support for Jenkins Pipeline as Code
   - Multi-branch pipeline support
   - Jenkinsfile parsing

3. **Caching:**
   - Cache GitHub API responses
   - Cache Jenkins job listings
   - Cache manifest parsing results

4. **Batch Operations:**
   - Scan multiple repositories in single run
   - Scan multiple branches/tags

5. **CI/CD Integration:**
   - GitHub Actions integration
   - Jenkins pipeline integration
   - GitLab CI integration

6. **Reporting:**
   - HTML report generation
   - Historical trend analysis
   - Compliance dashboard

7. **Performance:**
   - Parallel manifest parsing
   - Parallel Jenkins job analysis
   - Incremental scanning (only changed files)

## 10. Implementation Status

### Completed Features
- ✅ Self-contained scanning implementation (Option A)
- ✅ Multi-ecosystem support (NPM, Python, Maven, Go)
- ✅ GitHub API integration with large file handling
- ✅ Jenkins integration with multi-strategy job matching
- ✅ Jenkins runtime evidence extraction
- ✅ Artifactory allowlist support
- ✅ Compliance status assessment (COMPLIANT, COMPLIANT_RUNTIME, TRANSLATED, NON_COMPLIANT)
- ✅ Optional transitive dependency parsing
- ✅ Flexible output formats (terminal, markdown, JSON)
- ✅ Configuration via YAML with environment variable support

### Known Limitations
- GitHub Enterprise raw endpoint may truncate very large files (>10MB)
- Transitive dependency parsing limited to lockfiles (package-lock.json, yarn.lock, pnpm-lock.yaml)
- Jenkins job matching may miss jobs with non-standard naming conventions
- No caching of API responses
- No historical scan result storage

### Testing Recommendations
- Test against repositories with various ecosystem combinations
- Test with and without Jenkins evidence
- Test with transitive deps enabled and disabled
- Test large file handling (>1MB lockfiles)
- Test with multiple Artifactory hosts in allowlist
- Test error handling (missing files, API failures, etc.)
