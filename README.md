# oss-check

A **lightweight, agent-native OSS compliance checking skill** for AI assistants.

## What this is

This repository contains the **oss-check** skill — a minimal, agent-native implementation for scanning repositories for open source software compliance issues. It uses **agent orchestration + existing platform tooling** (GitHub CLI, Jenkins HTTP APIs, Artifactory configuration) rather than shipping a full scanner implementation.

## Installation

This skill is designed to be used with AI assistants like Devin. Install it using the AgentOps framework:

```bash
bash AgentOps/scripts/apply-skills.sh \
  --agent devin \
  --project-root <your-project> \
  --path 'engineering/*'
```

## Usage

Once installed, invoke the skill in your AI assistant:

```
@oss-check fusion-stage
```

See the skill documentation for detailed usage:
- `.agents/skills/engineering/oss-check/SKILL.md`

## Configuration

The skill uses a side configuration file:
- `.agents/skills/engineering/oss-check/config.yaml`

Configure your GitHub organization, Jenkins instance, and Artifactory virtual repositories there.

## License

MIT
