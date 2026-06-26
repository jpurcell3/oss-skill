# OSS Check Skill - Packaging and Distribution Strategy

## Executive Summary

This document defines the packaging and distribution strategy for the OSS Check skill within the AgentOps framework. The goal is to enable seamless sharing, installation, and management of the skill while minimizing distribution size and complexity.

## Current State Analysis

### Current Implementation (Phase 1)

**Location:** `projects/oss-skill/`

**Components:**
- `simple_oss_check.py` - Wrapper script
- `config.yaml` - Configuration template
- `README.md` - Documentation
- `USER_GUIDE.md` - User documentation
- `docs/` - Design documentation

**Dependency:** Requires `oss-compliance-webapp` to be available in local filesystem at `../oss-compliance-webapp/`

**Distribution Issues:**
1. Skill is not in AgentOps global skills directory
2. Requires manual filesystem setup (sibling directory structure)
3. No automated installation process
4. Dependency on external project not clearly documented
5. No versioning or release mechanism
6. Difficult to share with other users

### AgentOps Skill Pattern

**Expected Location:** `AgentOps/global/skills/engineering/oss-check/`

**Expected Components:**
- `SKILL.md` - Skill definition and usage
- `skill.yaml` - Skill metadata
- `config.yaml` - Configuration template
- (Optional) Implementation scripts

**Distribution Mechanism:**
- Skills are distributed via AgentOps framework
- Installation via `apply-skills.sh` script
- Versioning via AgentOps releases
- Automatic dependency management

## Recommended Distribution Strategy

### Option A: Self-Contained Lightweight Skill (Recommended)

**Approach:** Implement the skill as described in the original SKILL.md - using agent orchestration with platform tools (GitHub CLI, Jenkins HTTP APIs) without external dependencies.

**Components:**
- Skill implementation uses only:
  - GitHub API (via `gh` CLI or direct HTTP)
  - Jenkins HTTP API
  - Artifactory API validation
  - Standard Python libraries
- No dependency on `oss-compliance-webapp`
- All scanning logic implemented within the skill

**Distribution:**
- Single skill package in AgentOps
- Install via standard AgentOps mechanism
- Minimal size (< 50KB)
- No external service dependency

**Pros:**
- True self-contained skill
- Easy to distribute and install
- Follows AgentOps patterns
- Minimal setup required
- No service deployment needed
- Can be used offline (with cached credentials)

**Cons:**
- Less comprehensive than full scanner
- Would need to re-implement scanning logic
- May miss some edge cases
- Development effort to implement

**Migration Effort:** High (re-implementation required)

### Option B: Service-Based Distribution

**Approach:** Package `oss-compliance-webapp` as a distributable service and update skill to call it via HTTP API.

**Components:**
1. **OSS Compliance Service Package:**
   - Docker image with service
   - Python package for local installation
   - Installation script
   - Configuration templates

2. **Skill Package:**
   - Updated skill that calls service via HTTP
   - Service URL configuration
   - Fallback to library import for local development

**Distribution:**
- Skill: Via AgentOps framework (standard)
- Service: Via Docker registry or internal PyPI
- Documentation: Installation guide for service + skill

**Pros:**
- Leverages existing comprehensive scanner
- Service can be shared across multiple skills/users
- Scanner can be updated independently
- Supports both local and container deployment

**Cons:**
- Requires service deployment
- More complex setup
- Network dependency between skill and service
- Larger distribution size (service image)
- Not truly self-contained

**Migration Effort:** Medium (add REST API to service, update skill)

### Option C: Hybrid Approach (Phased)

**Approach:** Start with Option A (lightweight) for immediate distribution, then evolve to Option B (service-based) for advanced use cases.

**Phase 1 (Immediate - Lightweight):**
- Implement basic scanning using platform APIs
- Distribute via AgentOps
- Target 80% of common use cases

**Phase 2 (Enhanced - Service):**
- Add optional service integration
- Users can deploy service for comprehensive scanning
- Skill auto-detects service availability
- Falls back to lightweight mode if service unavailable

**Distribution:**
- Phase 1: Single skill package
- Phase 2: Skill + optional service package

**Pros:**
- Immediate value with minimal effort
- Progressive enhancement
- Backward compatible
- Flexibility for users

**Cons:**
- Two implementation paths to maintain
- Potential feature divergence
- More complex testing

**Migration Effort:** Medium (start with lightweight, add service later)

## Recommended Implementation: Option A (Self-Contained)

Given the user's requirement to **minimize distribution size** and the AgentOps framework's emphasis on **lightweight, agent-native skills**, Option A is recommended.

### Rationale

1. **AgentOps Alignment:** The original SKILL.md describes a lightweight approach - this aligns with that vision
2. **Simplicity:** Single package, no service deployment, minimal setup
3. **Distribution Size:** < 50KB vs. ~500MB for Docker image
4. **User Experience:** Install and use immediately without infrastructure setup
5. **Maintenance:** Single codebase to maintain
6. **Offline Capability:** Can work with cached credentials and APIs

### Implementation Plan

#### Phase 1: Core Functionality (MVP)

**Features to Implement:**
1. Dependency manifest detection via GitHub API
2. Dependency extraction for each ecosystem
3. Registry configuration analysis
4. Basic compliance assessment
5. Summary table output
6. Recommendations generation

**Ecosystem Support (Initial):**
- Node/NPM
- Python/PyPI
- Maven
- Go modules

**Jenkins Integration (Optional):**
- Job discovery via Jenkins API
- Config XML parsing
- Console log analysis for registry settings

**Implementation Approach:**
- Use `gh` CLI where available (faster, authenticated)
- Fall back to direct GitHub API calls
- Use `requests` library for Jenkins/Artifactory APIs
- Parse configuration files with standard Python libraries

#### Phase 2: Enhanced Features

**Additional Features:**
- Docker ecosystem support
- Helm ecosystem support
- Advanced false positive detection
- Historical scan results
- Batch scanning capability
- CI/CD integration examples

## Packaging Details

### Skill Package Structure

```
AgentOps/global/skills/engineering/oss-check/
├── SKILL.md              # Skill definition and usage
├── skill.yaml            # Skill metadata
├── config.yaml           # Configuration template
├── oss_check_impl.py     # Implementation script
├── utils/
│   ├── github_api.py     # GitHub API utilities
│   ├── jenkins_api.py    # Jenkins API utilities
│   ├── parsers.py        # Dependency file parsers
│   └── compliance.py     # Compliance logic
└── tests/
    ├── test_github.py    # GitHub API tests
    ├── test_parsers.py   # Parser tests
    └── test_compliance.py # Compliance tests
```

### Dependencies

**Python Dependencies:**
- `requests` - HTTP client for API calls
- `PyYAML` - Configuration parsing
- Standard library only otherwise

**System Dependencies:**
- `gh` CLI (optional, for faster GitHub operations)
- Network access to GitHub, Jenkins, Artifactory

### Distribution Method

**Via AgentOps Framework:**
1. Add skill to `AgentOps/global/skills/engineering/oss-check/`
2. Include in AgentOps release
3. Users install via `apply-skills.sh`
4. Automatic version management

**Manual Distribution (Alternative):**
1. Zip skill directory
2. Provide installation instructions
3. Users extract to `.agents/skills/engineering/`
4. Configure as needed

## Installation Process

### Standard AgentOps Installation

```bash
# From AgentOps repository
cd AgentOps
bash scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/oss-check'
```

### Configuration

1. Copy config template to project:
   ```bash
   cp .agents/skills/engineering/oss-check/config.yaml \
      .agents/skills/engineering/oss-check/local-config.yaml
   ```

2. Edit configuration with your environment details

3. Set environment variables for credentials:
   ```bash
   export GITHUB_TOKEN=your-token
   export JENKINS_USER=your-user
   export JENKINS_TOKEN=your-token
   ```

### Usage

```
@oss-check fusion-stage
@oss-check fusion-stage --include-jenkins true
@oss-check fusion-stage -v
```

## Versioning and Releases

### Version Scheme

Follow semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR:** Breaking changes, ecosystem support changes
- **MINOR:** New features, new ecosystem support
- **PATCH:** Bug fixes, minor improvements

### Release Process

1. Update version in `skill.yaml`
2. Update CHANGELOG.md
3. Tag release in git
4. Include in AgentOps release
5. Announce to users

### Backward Compatibility

- Maintain backward compatibility for config schema
- Deprecated features supported for at least 2 minor versions
- Clear migration path for breaking changes

## Migration from Current Implementation

### For Existing Users

**Current State:**
- Using `projects/oss-skill/simple_oss_check.py`
- Requires `oss-compliance-webapp` in local filesystem

**Migration Steps:**

1. **Install New Skill:**
   ```bash
   cd AgentOps
   bash scripts/apply-skills.sh \
     --agent devin \
     --project-root <your-project> \
     --path 'engineering/oss-check'
   ```

2. **Migrate Configuration:**
   - Copy configuration from old `config.yaml`
   - Update to match new schema (add `service` section if needed)

3. **Update Invocations:**
   - Old: `python projects/oss-skill/simple_oss_check.py fusion-stage`
   - New: `@oss-check fusion-stage`

4. **Remove Old Implementation:**
   - Archive or delete `projects/oss-skill/`
   - Keep `oss-compliance-webapp` if still needed for other purposes

### For Development

**Keep Both Implementations:**
- Use lightweight skill for daily use
- Keep `oss-compliance-webapp` for advanced analysis
- Document when to use each approach

## Alternative: Service-Based Distribution (If Needed)

If the comprehensive scanner capabilities are essential and cannot be replicated in a lightweight implementation, follow this approach:

### Service Package

**Docker Image:**
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

**Distribution:**
- Publish to internal container registry
- Tag with version: `oss-compliance-service:1.0.0`
- Provide installation guide

### Skill Integration

**Updated Skill Config:**
```yaml
service:
  url: http://localhost:5000  # or remote service URL
  timeout: 300
  use_service: true  # enable service mode
```

**Fallback Logic:**
- Try service if `use_service: true`
- Fall back to lightweight mode if service unavailable
- Graceful degradation with user notification

## Decision Matrix

| Factor | Lightweight (Option A) | Service-Based (Option B) | Hybrid (Option C) |
|--------|----------------------|-------------------------|-------------------|
| Distribution Size | < 50KB | ~500MB | < 50KB + optional 500MB |
| Setup Complexity | Low | High | Low (optional high) |
| Maintenance | Low | Medium | High |
| Feature Completeness | 80% | 100% | 80% → 100% |
| AgentOps Alignment | High | Low | Medium |
| Offline Capability | Yes | No | Yes (basic) |
| Development Effort | High | Medium | Medium-High |
| Time to Market | Medium | Low | Medium |

## Recommendation

**Primary Recommendation:** Option A (Self-Contained Lightweight Skill)

**Rationale:**
1. Best alignment with AgentOps framework philosophy
2. Meets user requirement for minimal distribution size
3. Simplest user experience
4. Lowest long-term maintenance burden
5. Can be enhanced incrementally (Phase 2)

**Fallback Option:** If comprehensive scanning is critical and cannot be simplified, implement Option B (Service-Based) with clear documentation of the trade-offs.

## Next Steps

1. **Confirm Approach:** Get user approval for Option A or alternative
2. **Implement Lightweight Skill:** Develop self-contained implementation
3. **Test Thoroughly:** Validate against existing scan results
4. **Update Documentation:** Ensure all docs reflect new approach
5. **Release via AgentOps:** Package and distribute
6. **Gather Feedback:** Monitor usage and iterate

## Appendix: Current vs. Target Comparison

### Current Implementation

```
projects/oss-skill/
├── simple_oss_check.py  (imports from ../oss-compliance-webapp)
├── config.yaml
├── README.md
└── USER_GUIDE.md

Requires:
- oss-compliance-webapp in sibling directory
- Python environment with scanner dependencies
- Manual setup
```

### Target Implementation

```
AgentOps/global/skills/engineering/oss-check/
├── SKILL.md
├── skill.yaml
├── config.yaml
├── oss_check_impl.py  (self-contained)
├── utils/
│   ├── github_api.py
│   ├── jenkins_api.py
│   ├── parsers.py
│   └── compliance.py
└── tests/

Requires:
- Standard Python + requests library
- gh CLI (optional)
- Network access to APIs
- Install via AgentOps
```

### Size Comparison

- **Current:** ~50KB (script) + ~50MB (oss-compliance-webapp) = ~50MB
- **Target:** ~50KB (skill) = ~50KB
- **Reduction:** 99.9% size reduction
