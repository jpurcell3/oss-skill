# OSS Check Skill - High Level Design (HLD)

## 1. Overview

The OSS Check skill is an AI assistant skill that performs open source software compliance scanning on repositories. It validates that dependencies are sourced through approved Artifactory virtual repositories and optionally incorporates Jenkins runtime evidence to reduce false positives.

### 1.1 Current Architecture

The skill currently exists in two forms with a **mismatch** between definition and implementation:

**Skill Definition (AgentOps):**
- Location: `AgentOps/global/skills/engineering/oss-check/`
- Name: `oss-check`
- Described as: "lightweight, agent-native" using platform tooling (GitHub CLI, Jenkins HTTP APIs)
- Expected behavior: Agent orchestrates scanning using existing platform tools

**Actual Implementation (projects/oss-skill):**
- Location: `projects/oss-skill/simple_oss_check.py`
- Implementation: Wrapper script that imports `RemoteRepositoryScanner` from `oss-compliance-webapp`
- Actual behavior: Delegates to heavy Python scanner with comprehensive compliance logic
- Dependencies: Requires `oss-compliance-webapp` project to be available locally

### 1.2 Problem Statement

The current implementation does not follow the AgentOps skill architecture:
1. The skill definition describes a lightweight approach, but implementation uses heavy scanner
2. The skill is not self-contained - depends on external `oss-compliance-webapp` project
3. No clear distribution mechanism - users must have multiple repos available
4. Unclear whether `oss-compliance-webapp` should run as a service or be imported as library
5. Not aligned with AgentOps skill distribution patterns

## 2. Architecture Options

### Option A: Self-Contained Lightweight Skill (Align with SKILL.md)

Implement the skill as described in SKILL.md - using agent orchestration with platform tools:

**Components:**
- Skill script: Implements scanning logic using GitHub API, Jenkins API, and Artifactory API calls
- No external scanner dependency
- Agent makes direct API calls to gather evidence

**Pros:**
- Self-contained, easy to distribute
- Lightweight, fast execution
- Matches AgentOps skill pattern
- No external service dependencies

**Cons:**
- Less comprehensive than full scanner
- Would need to re-implement scanning logic
- May miss some edge cases handled by full scanner

**Distribution:**
- Single skill package in AgentOps
- Install via AgentOps skill distribution mechanism
- Configuration via skill's config.yaml

### Option B: Service-Based Architecture

Keep the current approach but properly architect it as a service:

**Components:**
1. **OSS Compliance Service** (`oss-compliance-webapp`):
   - Runs as a Flask web service
   - Exposes REST API for scanning operations
   - Can be deployed as container or local service

2. **OSS Check Skill** (`oss-skill`):
   - Lightweight wrapper that calls OSS Compliance Service API
   - Handles configuration and result formatting
   - Distributed as part of AgentOps

**Pros:**
- Leverages existing comprehensive scanner
- Service can be shared across multiple skills/users
- Scanner can be updated independently
- Supports both local and container deployment

**Cons:**
- Requires service to be running
- More complex deployment
- Network dependency between skill and service
- Not truly self-contained

**Distribution:**
- Skill: Distributed via AgentOps
- Service: Distributed as Docker image or Python package with installation instructions

### Option C: Library-Based Distribution

Package `oss-compliance-webapp` as a Python library and include as dependency:

**Components:**
- Package `oss-compliance-webapp` as installable Python package
- Skill includes it as dependency in requirements.txt/pyproject.toml
- Skill imports scanner classes directly

**Pros:**
- Still comprehensive scanning
- No network dependency
- Simpler than service-based
- Can be versioned and updated

**Cons:**
- Larger skill distribution size
- Python dependency management
- Still not "lightweight"
- May have conflicting dependencies with other skills

**Distribution:**
- Skill package with scanner library as dependency
- Install via pip + AgentOps skill installation

## 3. Recommended Architecture: Option B (Service-Based)

### 3.1 Rationale

Given the existing investment in `oss-compliance-webapp` and its comprehensive scanning capabilities, the service-based approach offers the best balance:

1. **Leverages Existing Investment**: The full scanner is already built and tested
2. **Separation of Concerns**: Service handles scanning, skill handles orchestration
3. **Flexibility**: Service can be deployed locally or as container
4. **Shareability**: Multiple skills/users can use the same service
5. **AgentOps Alignment**: Skill remains lightweight and follows agent patterns

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

### 3.3 Component Details

#### 3.3.1 OSS Check Skill (AgentOps)

**Location:** `AgentOps/global/skills/engineering/oss-check/`

**Files:**
- `SKILL.md` - Skill definition and usage
- `skill.yaml` - Skill metadata
- `config.yaml` - Configuration (GitHub, Jenkins, Artifactory)
- `simple_oss_check.py` - Skill implementation (moved from projects/oss-skill)

**Responsibilities:**
- Load configuration from config.yaml
- Parse user input (repo name, options)
- Call OSS Compliance Service API
- Format and display results
- Handle errors gracefully

**Configuration:**
```yaml
service:
  url: http://localhost:5000  # OSS Compliance Service URL
  timeout: 300  # seconds

github:
  api_url: https://eos2git.cec.lab.emc.com/api/v3
  org: ISG-Edge
  token: ${GITHUB_TOKEN}  # or from config

jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net
  user: ${JENKINS_USER}
  token: ${JENKINS_TOKEN}

artifactory:
  base_url: isgedge.artifactory.cec.lab.emc.com
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    # ... other repos
```

#### 3.3.2 OSS Compliance Service

**Location:** `projects/oss-compliance-webapp/`

**Components:**
- Flask web service exposing REST API
- Existing scanner classes (`RemoteRepositoryScanner`, `ComplianceScanner`)
- Jenkins integration
- GitHub integration
- Artifactory validation

**API Endpoints:**
```
POST /api/scan
Request body:
{
  "repo_name": "fusion-stage",
  "include_jenkins": true,
  "verbose": false,
  "config": {
    "github": {...},
    "jenkins": {...},
    "artifactory": {...}
  }
}

Response:
{
  "summary": {
    "total_components": 256,
    "compliant": 179,
    "non_compliant": 77,
    "compliance_percentage": 69.9
  },
  "findings": [...],
  "recommendations": [...],
  "verbose_details": {...}  # if verbose=true
}
```

**Deployment Options:**
1. **Local Development:** `python app.py` runs service on localhost:5000
2. **Container:** Docker image with service
3. **Production:** Deployed to internal server/container registry

## 4. Dependencies

### 4.1 Skill Dependencies
- Python 3.8+
- `requests` library (for HTTP calls to service)
- AgentOps framework (for skill distribution)

### 4.2 Service Dependencies
- Python 3.8+
- Flask
- PyGithub
- Requests
- Jenkins API libraries
- Existing scanner dependencies

### 4.3 External Dependencies
- GitHub Enterprise API
- Jenkins Server
- Artifactory Server
- Network connectivity to these services

## 5. Deployment Flow

### 5.1 Initial Setup

1. **Deploy OSS Compliance Service:**
   ```bash
   cd projects/oss-compliance-webapp
   # Option A: Local
   python app.py
   
   # Option B: Container
   docker build -t oss-compliance-service .
   docker run -p 5000:5000 oss-compliance-service
   ```

2. **Install Skill via AgentOps:**
   ```bash
   cd AgentOps
   bash scripts/apply-skills.sh \
     --agent devin \
     --project-root <your-project> \
     --path 'engineering/oss-check'
   ```

3. **Configure Skill:**
   - Edit `.agents/skills/engineering/oss-check/config.yaml`
   - Set service URL to point to deployed service
   - Configure GitHub, Jenkins, Artifactory credentials

### 5.2 Runtime Flow

1. User invokes: `@oss-check fusion-stage`
2. AI assistant loads skill configuration
3. Skill makes HTTP POST to OSS Compliance Service
4. Service downloads repo, scans, incorporates Jenkins evidence
5. Service returns JSON results
6. Skill formats results as table/display
7. User sees compliance summary

## 6. Distribution Strategy

### 6.1 Skill Distribution
- **Via AgentOps:** Skill is part of AgentOps global skills
- **Installation:** Standard AgentOps skill installation
- **Updates:** Via AgentOps release mechanism
- **Size:** Minimal (just wrapper script + config)

### 6.2 Service Distribution
- **As Docker Image:**
  - Publish to internal container registry
  - Versioned tags (e.g., `oss-compliance-service:1.0.0`)
  - Users pull and run image
  
- **As Python Package:**
  - Publish to internal PyPI
  - Install via `pip install oss-compliance-service`
  - Run as module: `python -m oss_compliance_service`

- **Documentation:**
  - Installation guide for local vs container deployment
  - Configuration requirements
  - Troubleshooting guide

### 6.3 Version Compatibility
- Skill version tracks compatible service versions
- Service API versioning to prevent breaking changes
- Skill includes service version requirement in config

## 7. Migration Path

### Phase 1: Immediate (Current State)
- Keep `simple_oss_check.py` in `projects/oss-skill/`
- Document that it requires `oss-compliance-webapp` to be available locally
- Update documentation to clarify current architecture

### Phase 2: Service API Development
- Add REST API endpoints to `oss-compliance-webapp`
- Ensure scanner can be invoked programmatically
- Add proper error handling and JSON responses

### Phase 3: Skill Migration
- Move `simple_oss_check.py` to AgentOps skill directory
- Update to call service API instead of importing scanner
- Update SKILL.md to reflect service-based architecture
- Update config.yaml to include service URL

### Phase 4: Distribution
- Package service as Docker image
- Publish installation documentation
- Update AgentOps skill distribution

## 8. Security Considerations

1. **Credentials:**
   - GitHub, Jenkins, Artifactory credentials stored in skill config
   - Use environment variables where possible
   - Never log credentials

2. **Service Security:**
   - If deployed publicly, require authentication
   - Use HTTPS for service communication
   - Rate limiting to prevent abuse

3. **Network Security:**
   - Service needs access to GitHub, Jenkins, Artifactory
   - Configure firewall rules appropriately
   - Use internal network when possible

## 9. Monitoring and Observability

1. **Service Logging:**
   - Log scan requests and results
   - Track performance metrics
   - Error logging for troubleshooting

2. **Skill Logging:**
   - Log API calls to service
   - Track user invocations
   - Error handling

3. **Metrics:**
   - Scan success/failure rates
   - Scan duration
   - Service health checks

## 10. Future Enhancements

1. **Async Scanning:** Support long-running scans with status polling
2. **Batch Scanning:** Scan multiple repos in single request
3. **Caching:** Cache results to avoid redundant scans
4. **Webhook Support:** Notify on scan completion
5. **Result Storage:** Store historical scan results
6. **Integration with CI/CD:** GitHub Actions, Jenkins pipeline integration
