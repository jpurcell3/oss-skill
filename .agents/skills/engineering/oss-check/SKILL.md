---
name: oss-check
description: "OSS compliance checker — scan repositories for open source dependency compliance by analyzing package manager configuration and (optionally) Jenkins runtime evidence. Usage: @oss-check <repo-or-path> [options]"
triggers:
  - user
  - model
allowed-tools:
  - read
  - grep
  - glob
  - exec
  - ask_user_question
---

# OSS Check

A **lightweight, agent-native** OSS compliance scanning skill. This skill aims to match the functionality of the heavier Python CLI by using **agent orchestration + existing platform tooling** (e.g., `gh` and Jenkins HTTP APIs) rather than shipping a full scanner implementation.

## When to use

Use this skill when you need to:
- Determine whether a repository’s OSS dependencies are sourced via **approved Artifactory virtual repositories**
- Identify **non-compliant components** (direct public registries) for:
  - **Node/NPM**
  - **Python/PyPI**
  - **Maven**
  - **Go modules**
- Optionally incorporate **Jenkins runtime evidence** (registry/mirror settings in CI)
- Produce a compliance summary plus actionable remediation steps

## Inputs

- **Target**: repository name (`org/repo` or `repo`) or local repo path
- **Optional**:
  - `--org <org>` (default from config)
  - `--ref <branch|tag|sha>` (default: default branch)
  - `--include-jenkins true|false` (default: true)
  - `--format terminal|json|markdown` (default: markdown)

## Configuration

This skill expects a small side config file placed alongside the skill:

- `config.yaml` (recommended)

Config schema (example):
```yaml
github:
  api_url: https://eos2git.cec.lab.emc.com/api/v3
  org: ISG-Edge

jenkins:
  url: https://osj-isg-03-prd.cec.delllabs.net
  # credentials are optional; if missing, skip Jenkins evidence

artifactory:
  base_url: isgedge.artifactory.cec.lab.emc.com
  virtual_repos:
    npm: isgedge-npm-virtual
    pypi: isgedge-pypi-virtual
    maven: isgedge-maven-virtual
    go: isgedge-go-virtual

policy:
  # expected “compliant” endpoints
  npm_registry_url: "https://{base}/artifactory/api/npm/{npm}/"
  pypi_simple_url: "https://{base}/artifactory/api/pypi/{pypi}/simple/"
  maven_repo_url: "https://{base}/artifactory/{maven}/"
  go_proxy_url: "https://{base}/artifactory/api/go/{go}/"
```

## Steps (Agent Procedure)

### 0) Resolve target context
1. If `target` is a local path: treat as local repo.
2. If `target` looks like `owner/repo`: use it.
3. Else: use `github.org` from config and assume `org/target`.

### 1) Identify dependency manifests quickly (no full clone)
Use GitHub contents API (via `gh api`) to check for these files at repo root (and common subpaths):

**Node**
- `package.json`
- `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`

**Python**
- `requirements.txt`, `requirements-*.txt`
- `pyproject.toml`
- `setup.py`
- `Pipfile`

**Maven**
- `pom.xml`

**Go**
- `go.mod`

If none exist, return: “No supported dependency manifests found”.

### 2) Extract declared dependencies
For each ecosystem found:

**NPM**
- Fetch `package.json` (and lockfile if present).
- Collect package names/versions where available.

**Python**
- Fetch `requirements*.txt` and parse pinned/unpinned requirements.
- Fetch `pyproject.toml` and extract dependencies.

**Maven**
- Fetch `pom.xml` and extract `groupId:artifactId:version` where specified.

**Go**
- Fetch `go.mod` and extract module requirements.

### 3) Determine declared registry/mirror configuration
Determine whether builds are configured to use Artifactory:

**NPM**
- Check `.npmrc` (repo root) and `publishConfig.registry` in `package.json`.
- If absent, treat as default public registry (non-compliant) unless Jenkins evidence overrides.

**Python**
- Check `pip.conf`, `pip.ini`, `Pipfile` sources, and requirements directives like `--index-url` / `--extra-index-url`.

**Maven**
- Check `settings.xml` (if present) for mirrors/repositories.

**Go**
- Check for `GOPROXY` settings in repo config/docs.

### 4) Optional: Incorporate Jenkins runtime evidence
If `--include-jenkins`:

**Goal:** detect registry/mirror configuration that is applied during CI (even if not committed in the repo).

**Preconditions:**
- If `jenkins.url` is not configured, skip.
- If Jenkins requires auth and no credentials are available, skip.

**Credentials (recommended):**
- `JENKINS_USER` and `JENKINS_TOKEN` in the agent environment, or add `jenkins.user` / `jenkins.token` to `config.yaml`.

**Procedure (lightweight, no Jenkins-specific dependency skill required):**
1. Enumerate candidate jobs using Jenkins JSON API (prefer query endpoints if available).
   - If no search endpoint is available, fetch the top-level job list and fuzzy-match names containing the repo name.
   - Limit to **≤ 3** candidate jobs.

2. For each candidate job:
   - Fetch job config XML (often reveals build steps that set registry variables)
   - Fetch last successful build console text (often contains `npm config set registry ...`, `pip config set global.index-url ...`, etc.)

Example calls (adjust as needed for your Jenkins instance):
```bash
# Top-level jobs (may be nested in folders)
curl -fsSL -u "$JENKINS_USER:$JENKINS_TOKEN" \
  "$JENKINS_URL/api/json?tree=jobs[name,url]"

# Job config.xml
curl -fsSL -u "$JENKINS_USER:$JENKINS_TOKEN" \
  "$JOB_URL/config.xml"

# Last successful build console output
curl -fsSL -u "$JENKINS_USER:$JENKINS_TOKEN" \
  "$JOB_URL/lastSuccessfulBuild/consoleText"
```

**Evidence to look for:**
- NPM: `npm config set registry`, `.npmrc` writes, `NPM_CONFIG_REGISTRY=...`
- Python: `pip config set global.index-url`, `--index-url`, `PIP_INDEX_URL=...`
- Maven: `settings.xml`, `<mirror>`, `-s settings.xml`, `mvn -Dmaven.repo.local=...`
- Go: `GOPROXY=...`, `go env -w GOPROXY=...`

If Jenkins evidence indicates compliant registries/mirrors, treat components as compliant **at runtime**, but still report missing repo-local configuration as a remediation opportunity.

### 5) Produce results
Return:
- Summary: total components, compliant count, non-compliant count, compliance %
- Findings:
  - For each component/ecosystem, show:
    - manifest source
    - expected compliant endpoint
    - detected endpoint (declared and/or runtime)
    - compliance status
- Recommendations:
  - Concrete configuration snippets to add (`.npmrc`, `pip.conf`, Maven `settings.xml`, etc.)

## Output format
Default to **Markdown** with:
- Executive summary table
- Findings by ecosystem
- Top non-compliant components
- Remediation steps

If user requests JSON, return a JSON object with fields:
- `repository_name`, `scan_timestamp`, `total_components`, `compliant_components`, `non_compliant_components`, `compliance_percentage`, `component_mappings[]`

## Gotchas

- Repos may have manifests under subfolders (e.g., `backend/package.json`). Check common subpaths: `backend/`, `services/`, `apps/`, `src/`.
- Don’t assume registry config exists even if dependencies exist.
- Lockfiles may be large; prefer `package.json` first.
- Jenkins may not have a 1:1 job name match; try fuzzy match and limit search.

## Examples

### Example input
```
@oss-check fusion-stage
```

### Example output (abbreviated)
```
## OSS Check: fusion-stage

| Metric | Value |
|---|---:|
| Total components | 254 |
| Compliant | 180 |
| Non-compliant | 74 |
| Compliance | 70.87% |

### Key findings
- Backend packages missing repo-local registry configuration; Jenkins sets a compliant registry at runtime.

### Recommendations
- Add `.npmrc` with Artifactory registry.
- Add `publishConfig.registry` to backend package.json.
```

## Performance and automation

- Prefer `gh api --hostname <host>` (uses existing CLI auth) over platform-native GitHub calls that may prompt.
- Use Git Trees API with `recursive=1` to reduce network round-trips and capture nested manifests reliably.
- Fetch file bodies with `Accept: application/vnd.github.v3.raw` to avoid base64 handling on some shells.
- Pin scans to a specific commit SHA (resolve default branch HEAD when `--ref` omitted) and display it in output; use the SHA to key a local cache.
- Scope Jenkins evidence to the branch derived from `--ref` and fetch only `job/<repo>/job/<branch>/lastSuccessfulBuild/consoleText`; grep narrow patterns like `npm config set registry|NPM_CONFIG_REGISTRY|\.npmrc|artifactory`.
- To minimize prompts in IDEs, allowlist read-only commands such as:
  - `gh api --hostname eos2git.cec.lab.emc.com /repos/*`
  - `gh api --hostname eos2git.cec.lab.emc.com /repos/*/git/trees*`
  - `gh api --hostname eos2git.cec.lab.emc.com /repos/*/contents*`
  - `Invoke-WebRequest -Uri https://osj-isg-03-prd.cec.delllabs.net/*`
- Use a local repo path as `target` when available to avoid network calls entirely.

## Environment-based credentials

- Do not store GitHub or Jenkins tokens in `config.yaml`.
- Use gh CLI authentication for GitHub requests.
- Set Jenkins credentials via environment variables (recommended):
  - `JENKINS_URL`, `JENKINS_USER`, `JENKINS_TOKEN`
