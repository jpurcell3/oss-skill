# OSS Check — User Guide & Examples

This project provides **oss-check** in two forms:

1) **Lightweight agent skill** (recommended for interactive use in Devin)
2) **Python CLI** (useful for automation / CI)

This document focuses on **examples** for both.

---

## 1) Devin Skill: `oss-check`

### Where it is installed (this repo)
- Skill files: `.agents/skills/engineering/oss-check/`
- Devin bridge: `.devin/skills/oss-check`

If the bridge exists, Devin should auto-discover the skill.

### Basic scan
Use natural language, or invoke explicitly:

```
@oss-check fusion-stage
```

### Request a specific format
```
@oss-check fusion-stage --format markdown
```

### Include / exclude Jenkins runtime evidence
```
@oss-check fusion-stage --include-jenkins true
@oss-check fusion-stage --include-jenkins false
```

### Scan a different org or ref
```
@oss-check ISG-Edge/fusion-stage
@oss-check fusion-stage --org ISG-Edge --ref main
```

### Ask for remediation steps
```
@oss-check fusion-stage
Then: "Show me the top 10 non-compliant components and the exact config changes to fix them."
```

### Common follow-up prompts
- "Summarize findings by ecosystem (npm/python/maven/go)."
- "Generate a minimal `.npmrc` and tell me where to put it."
- "Assume Jenkins is the source of truth; re-score compliance using runtime evidence."

---

## 2) Skill Configuration

The lightweight skill reads a small side config file:

- `.agents/skills/engineering/oss-check/config.yaml`

It defines:
- GitHub API URL + org
- Jenkins URL (optional)
- Artifactory base URL + virtual repos
- Policy URL templates (expected compliant endpoints)

If Jenkins requires auth, provide credentials via environment variables (recommended):
- `JENKINS_USER`
- `JENKINS_TOKEN`

---

## 3) Python CLI: `oss_check.py`

### Basic scan
```
python oss_check.py scan fusion-stage
```

### JSON output
```
python oss_check.py scan fusion-stage --format json
```

### Markdown output
```
python oss_check.py scan fusion-stage --format markdown
```

### Validate configuration
```
python oss_check.py check-config
```

### List repositories
```
python oss_check.py list-repos
```

### Use a specific config file
```
python oss_check.py scan fusion-stage --config oss_check_config.yaml
python oss_check.py check-config --config oss_check_config.yaml
python oss_check.py list-repos --config oss_check_config.yaml
```

---

## 4) Typical Remediation Examples

### A) NPM: enforce Artifactory registry
**Option 1: repo root `.npmrc`**

```
registry=https://isgedge.artifactory.cec.lab.emc.com/artifactory/api/npm/isgedge-npm-virtual/
always-auth=true
```

**Option 2: `package.json` publishConfig**

```json
{
  "publishConfig": {
    "registry": "https://isgedge.artifactory.cec.lab.emc.com/artifactory/api/npm/isgedge-npm-virtual/"
  }
}
```

### B) Python: enforce Artifactory PyPI index
**Option 1: requirements directive**

```
--index-url https://isgedge.artifactory.cec.lab.emc.com/artifactory/api/pypi/isgedge-pypi-virtual/simple/
```

**Option 2: pip config**

```
pip config set global.index-url https://isgedge.artifactory.cec.lab.emc.com/artifactory/api/pypi/isgedge-pypi-virtual/simple/
```

---

## 5) Troubleshooting

### Skill doesn’t show up in Devin
1) Confirm the bridge exists:
   - `.devin/skills/oss-check`
2) Confirm the skill files exist:
   - `.agents/skills/engineering/oss-check/SKILL.md`

### Jenkins evidence not detected
- Ensure `jenkins.url` is present in the skill `config.yaml`
- Provide `JENKINS_USER` / `JENKINS_TOKEN`
- Verify the Jenkins job name may not match the repo exactly (the skill uses fuzzy matching and caps at 3 jobs)

### GitHub access issues
- Ensure GitHub token/credentials are available to the agent environment
- If using `gh`, ensure authentication is valid for the target GitHub Enterprise instance
