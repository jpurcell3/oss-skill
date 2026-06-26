# OSS Check Skill - Technical Specifications

## 1. API Specification (OSS Compliance Service)

### 1.1 Scan Endpoint

**Endpoint:** `POST /api/scan`

**Request Headers:**
```
Content-Type: application/json
Authorization: Bearer <optional-token>  # If service requires auth
```

**Request Body:**
```json
{
  "repo_name": "string (required)",
  "org": "string (optional, defaults from config)",
  "ref": "string (optional, default branch)",
  "include_jenkins": "boolean (optional, default true)",
  "verbose": "boolean (optional, default false)",
  "config": {
    "github": {
      "api_url": "string",
      "org": "string",
      "token": "string"
    },
    "jenkins": {
      "url": "string",
      "user": "string",
      "token": "string"
    },
    "artifactory": {
      "base_url": "string",
      "virtual_repos": {
        "npm": "string",
        "pypi": "string",
        "maven": "string",
        "go": "string",
        "docker": "string"
      }
    },
    "policy": {
      "npm_registry_url": "string",
      "pypi_simple_url": "string",
      "maven_repo_url": "string",
      "go_proxy_url": "string"
    }
  }
}
```

**Response Body (Success - 200):**
```json
{
  "status": "success",
  "scan_timestamp": "ISO 8601 timestamp",
  "repository": {
    "name": "string",
    "org": "string",
    "ref": "string"
  },
  "summary": {
    "total_components": "integer",
    "compliant": "integer",
    "non_compliant": "integer",
    "compliance_percentage": "float"
  },
  "findings": [
    {
      "component": "string",
      "ecosystem": "string (npm|pypi|maven|go|docker)",
      "version": "string",
      "severity": "string (HIGH|MEDIUM|LOW|INFO)",
      "status": "string (compliant|non_compliant)",
      "manifest_file": "string",
      "detected_endpoint": "string",
      "expected_endpoint": "string",
      "runtime_evidence": "boolean"
    }
  ],
  "recommendations": [
    {
      "severity": "string",
      "message": "string",
      "affected_components": "integer"
    }
  ],
  "verbose_details": {
    "jenkins_jobs_analyzed": "integer",
    "runtime_configurations_found": "integer",
    "files_scanned": ["string"],
    "endpoint_configurations": {
      "npm": ["string"],
      "pypi": ["string"],
      "maven": ["string"],
      "go": ["string"]
    }
  }
}
```

**Response Body (Error - 4xx/5xx):**
```json
{
  "status": "error",
  "error_code": "string",
  "message": "string",
  "details": "object (optional)"
}
```

**Error Codes:**
- `INVALID_REQUEST`: Missing or invalid parameters
- `REPO_NOT_FOUND`: Repository not found or inaccessible
- `AUTH_FAILED`: Authentication failed with GitHub/Jenkins
- `SCAN_FAILED`: Scanning process failed
- `TIMEOUT`: Scan exceeded time limit

### 1.2 Health Check Endpoint

**Endpoint:** `GET /api/health`

**Response (200):**
```json
{
  "status": "healthy",
  "version": "string",
  "timestamp": "ISO 8601 timestamp"
}
```

### 1.3 Version Endpoint

**Endpoint:** `GET /api/version`

**Response (200):**
```json
{
  "version": "string",
  "api_version": "string",
  "scanner_version": "string"
}
```

## 2. Skill Configuration Schema

### 2.1 config.yaml Schema

```yaml
# Service Configuration
service:
  url: string  # URL of OSS Compliance Service
  timeout: integer  # Request timeout in seconds (default: 300)
  retry_attempts: integer  # Number of retries on failure (default: 3)
  verify_ssl: boolean  # Verify SSL certificates (default: true)

# GitHub Configuration
github:
  api_url: string  # GitHub API URL
  org: string  # Default GitHub organization
  token: string  # GitHub token (or use GITHUB_TOKEN env var)

# Jenkins Configuration
jenkins:
  url: string  # Jenkins server URL
  user: string  # Jenkins username (or use JENKINS_USER env var)
  token: string  # Jenkins API token (or use JENKINS_TOKEN env var)

# Artifactory Configuration
artifactory:
  base_url: string  # Artifactory base URL
  virtual_repos:
    npm: string  # NPM virtual repository name
    pypi: string  # PyPI virtual repository name
    maven: string  # Maven virtual repository name
    go: string  # Go virtual repository name
    docker: string  # Docker virtual repository name
    helm: string  # Helm virtual repository name (optional)
    rpm: string  # RPM virtual repository name (optional)

# Policy Configuration
policy:
  npm_registry_url: string  # Expected NPM registry URL template
  pypi_simple_url: string  # Expected PyPI simple URL template
  maven_repo_url: string  # Expected Maven repository URL template
  go_proxy_url: string  # Expected Go proxy URL template

# Output Configuration
output:
  format: string  # Output format: table, json, markdown (default: table)
  show_recommendations: boolean  # Show remediation recommendations (default: true)
  max_findings_display: integer  # Max findings to display (default: 50)
```

## 3. Data Models

### 3.1 Scan Result Model

```python
@dataclass
class ScanResult:
    status: str  # success or error
    scan_timestamp: str
    repository: RepositoryInfo
    summary: ComplianceSummary
    findings: List[Finding]
    recommendations: List[Recommendation]
    verbose_details: Optional[VerboseDetails] = None

@dataclass
class RepositoryInfo:
    name: str
    org: str
    ref: str

@dataclass
class ComplianceSummary:
    total_components: int
    compliant: int
    non_compliant: int
    compliance_percentage: float

@dataclass
class Finding:
    component: str
    ecosystem: str
    version: str
    severity: str
    status: str
    manifest_file: str
    detected_endpoint: str
    expected_endpoint: str
    runtime_evidence: bool

@dataclass
class Recommendation:
    severity: str
    message: str
    affected_components: int

@dataclass
class VerboseDetails:
    jenkins_jobs_analyzed: int
    runtime_configurations_found: int
    files_scanned: List[str]
    endpoint_configurations: Dict[str, List[str]]
```

## 4. Error Handling

### 4.1 Skill Error Handling

The skill should handle the following error scenarios:

1. **Service Unavailable:**
   - Detect connection failure to OSS Compliance Service
   - Retry with exponential backoff
   - After max retries, display user-friendly error with troubleshooting steps

2. **Service Timeout:**
   - Detect timeout during long-running scans
   - Display message indicating scan in progress
   - Suggest increasing timeout or using async mode (future)

3. **Invalid Configuration:**
   - Validate config.yaml on skill load
   - Display clear error messages for missing/invalid configuration
   - Provide example configuration in error message

4. **Authentication Failures:**
   - Detect 401/403 errors from GitHub/Jenkins
   - Suggest checking credentials in config or environment variables
   - Provide instructions for token generation

5. **Repository Not Found:**
   - Detect 404 errors from GitHub
   - Suggest checking repository name and organization
   - Offer to list available repositories

### 4.2 Service Error Handling

The service should handle:

1. **Invalid API Requests:**
   - Validate request schema
   - Return 400 with detailed error message
   - Include expected schema in error response

2. **External API Failures:**
   - Catch and log failures from GitHub/Jenkins/Artifactory
   - Return 503 with service unavailable message
   - Include which external service failed

3. **Scan Failures:**
   - Catch exceptions during scanning
   - Return 500 with error details
   - Log full stack trace for debugging

4. **Rate Limiting:**
   - Detect rate limiting from external APIs
   - Return 429 with retry-after header
   - Implement exponential backoff in client

## 5. Performance Requirements

### 5.1 Response Time Targets

- **Small repos (< 100 dependencies):** < 30 seconds
- **Medium repos (100-500 dependencies):** < 2 minutes
- **Large repos (500-1000 dependencies):** < 5 minutes
- **Very large repos (> 1000 dependencies):** < 10 minutes

### 5.2 Concurrent Scans

- Service should support at least 5 concurrent scans
- Implement queueing for higher concurrency
- Return queue position and estimated wait time

### 5.3 Resource Limits

- **Memory per scan:** < 2GB
- **Disk per scan:** < 1GB (temp files)
- **Network:** Efficient API calls, minimize redundant requests

## 6. Security Specifications

### 6.1 Credential Management

1. **Environment Variables (Preferred):**
   - `GITHUB_TOKEN`: GitHub personal access token
   - `JENKINS_USER`: Jenkins username
   - `JENKINS_TOKEN`: Jenkins API token
   - `ARTIFACTORY_USER`: Artifactory username (if needed)
   - `ARTIFACTORY_TOKEN`: Artifactory API token (if needed)

2. **Config File (Fallback):**
   - Credentials can be stored in config.yaml
   - File should have restrictive permissions (600)
   - Never log or display credentials

3. **Service Authentication:**
   - If service requires authentication, support API key or JWT
   - API key passed via Authorization header
   - Keys stored securely in environment variables

### 6.2 Network Security

1. **SSL/TLS:**
   - Always use HTTPS for external API calls
   - Validate SSL certificates (verify_ssl: true)
   - Support custom CA certificates if needed

2. **Internal Network:**
   - Service can be deployed on internal network
   - Skill can communicate via internal URLs
   - No external exposure required

### 6.3 Audit Logging

1. **Service Logs:**
   - Log all scan requests with timestamp
   - Log which repository was scanned
   - Log scan duration and result
   - Do not log credentials or sensitive data

2. **Skill Logs:**
   - Log skill invocations
   - Log service communication
   - Log errors for troubleshooting

## 7. Testing Specifications

### 7.1 Unit Tests

**Skill Tests:**
- Configuration loading and validation
- Request/response parsing
- Error handling
- Output formatting (table, json, markdown)

**Service Tests:**
- API endpoint validation
- Scanner integration
- External API mocking
- Error handling

### 7.2 Integration Tests

- End-to-end scan with test repository
- Jenkins integration test
- GitHub API integration test
- Artifactory validation test

### 7.3 Performance Tests

- Scan small, medium, large test repositories
- Measure response times
- Test concurrent scans
- Monitor resource usage

## 8. Compatibility Matrix

| Component | Version | Notes |
|-----------|---------|-------|
| Python | 3.8+ | Required for skill and service |
| Flask | 2.0+ | For service |
| PyGithub | 1.55+ | For GitHub API |
| AgentOps | Latest | For skill distribution |
| GitHub API | v3 | Enterprise or public |
| Jenkins | 2.x+ | With API access |
| Artifactory | 7.x+ | With virtual repos |

## 9. Deployment Specifications

### 9.1 Service Deployment

**Docker Image:**
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "app:app"]
```

**Environment Variables:**
```bash
FLASK_APP=app.py
FLASK_ENV=production
GITHUB_TOKEN=...
JENKINS_USER=...
JENKINS_TOKEN=...
LOG_LEVEL=INFO
```

**Health Check:**
```bash
curl http://localhost:5000/api/health
```

### 9.2 Skill Deployment

**Installation via AgentOps:**
```bash
cd AgentOps
bash scripts/apply-skills.sh \
  --agent devin \
  --project-root <project> \
  --path 'engineering/oss-check'
```

**Configuration:**
- Copy config template to project
- Edit with service URL and credentials
- Test with sample repository

## 10. Monitoring and Observability

### 10.1 Metrics to Track

1. **Service Metrics:**
   - Request count by endpoint
   - Response time percentiles (p50, p95, p99)
   - Error rate by endpoint
   - Active concurrent scans
   - Queue depth (if queuing implemented)

2. **Skill Metrics:**
   - Skill invocation count
   - Service call success/failure rate
   - Average scan duration
   - Error types and frequencies

### 10.2 Logging Levels

- **DEBUG:** Detailed diagnostic information
- **INFO:** Normal operational messages
- **WARNING:** Warning conditions (e.g., retry needed)
- **ERROR:** Error conditions requiring attention
- **CRITICAL:** Critical failures

### 10.3 Alerting

Alert on:
- Service downtime (> 5 minutes)
- Error rate > 5%
- Response time p95 > 10 minutes
- Authentication failures
- Disk space < 10%
