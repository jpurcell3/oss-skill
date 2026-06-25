# github-ops

GitHub operations manager for managing PRs, issues, repositories, workflows, and authentication using gh CLI.

## Quick Start

```
@github-ops pr list              # List pull requests
@github-ops pr create            # Create a new PR
@github-ops issue list           # List issues
@github-ops workflow list        # List workflows
@github-ops run list             # List workflow runs
```

## Features

- Pull request management (list, create, view, merge, close)
- Issue management (list, create, view, comment)
- Repository operations (clone, fork, view)
- Workflow management (list, view, trigger, enable, disable)
- Workflow run management (list, view, watch, rerun, cancel)
- Authentication with persistent token storage
- Context-aware operations (fork vs upstream detection)

## Authentication

The skill automatically handles GitHub authentication:
- First use: asks for GitHub token and saves it to `~/.github-ops-token`
- Subsequent use: automatically loads saved token
- Supports both GitHub.com and GitHub Enterprise

## Workflow Limitations

GitHub Actions workflows cannot run in fork repositories. The skill automatically detects this and targets the upstream repository for workflow operations.
