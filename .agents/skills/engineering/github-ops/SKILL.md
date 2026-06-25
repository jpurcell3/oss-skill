---
name: github-ops
description: "GitHub operations manager — manage PRs, issues, repositories, workflows, and authentication using gh CLI. Usage: @github-ops <operation>"
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

# GitHub Operations

Use this skill for any GitHub operations using the `gh` CLI, including pull requests, issues, repositories, workflows, and authentication.

## When to invoke

Invoke this skill when the user asks to:
- List, create, view, merge, or close pull requests
- List, create, view, or comment on issues
- Clone, fork, or view repository information
- List, view, trigger, enable, or disable workflows
- List, view, watch, rerun, cancel, or delete workflow runs
- Authenticate with GitHub or check auth status
- Search for issues, PRs, or code

The LLM already knows the `gh` CLI syntax - use standard `gh` commands directly.

## Context detection

Before executing any GitHub operation, detect the repository and branch context:

### 1. Check if current directory is a git repository
```bash
git rev-parse --show-toplevel
```

### 2. If in a git repository, extract repository information
```bash
# Get current branch
git rev-parse --abbrev-ref HEAD

# Get remote URLs
git remote get-url origin
git remote get-url upstream

# Extract repo owner/name from remote URL
# Example: git@github.com:owner/repo.git or https://github.com/owner/repo.git
```

### 3. Determine target repository
- If `upstream` remote exists → use upstream for workflow operations, origin for PR operations
- If only `origin` remote exists → use origin for all operations
- If user explicitly specifies `--repo <owner/repo>` → use user-specified repo
- If not in git repo and no user specification → ask user for target repository

### 4. Determine target branch
- If in git repository → use current branch (`git rev-parse --abbrev-ref HEAD`)
- If user specifies `--ref <branch>` → use user-specified branch
- For workflow triggers → default to `main` unless user specifies otherwise
- If not in git repo and no user specification → ask user for target branch

### 5. Fork vs upstream detection
- Check if `origin` and `upstream` remotes point to different repositories
- If they differ → assume fork-based workflow (origin = fork, upstream = upstream)
- Extract fork owner and upstream org from remote URLs
- Use this information for branch naming conventions and PR creation

### 6. Context decision matrix

| Context | In git repo? | Has upstream? | User specified? | Target for PRs | Target for workflows |
|---------|-------------|---------------|-----------------|----------------|---------------------|
| Main clone in fork workflow | Yes | Yes | No | origin → upstream | upstream |
| Main clone single remote | Yes | No | No | origin | origin |
| Worktree in fork workflow | Yes | Yes | No | origin → upstream | upstream |
| No git context | No | N/A | No | Ask user | Ask user |
| User specified | Any | Any | Yes | User-specified | User-specified |

### 7. Example context detection flow
```bash
# Check if in git repo
if git rev-parse --show-toplevel >/dev/null 2>&1; then
  # Get current branch
  CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)

  # Check for upstream remote
  if git remote get-url upstream >/dev/null 2>&1; then
    # Fork-based workflow
    FORK_OWNER=$(git remote get-url origin | sed 's|.*[:/]\([^/]*\)/.*|\1|')
    UPSTREAM_ORG=$(git remote get-url upstream | sed 's|.*[:/]\([^/]*\)/.*|\1|')
    REPO_NAME=$(basename "$(git rev-parse --show-toplevel)")
    TARGET_REPO="${UPSTREAM_ORG}/${REPO_NAME}"
  else
    # Single remote workflow
    TARGET_REPO=$(git remote get-url origin | sed -E 's#^[a-z]+://##; s#^[^@]*@##; s#^[^:/]*[:/]##; s#\.git$##')
  fi
else
  # Not in git repo - ask user
  ask_user_question "Which repository do you want to operate on?"
fi
```

## Project-specific conventions

### Fork-based workflow
- PRs are created from fork to upstream
- Use `origin` for fork remote, `upstream` for upstream remote
- Branch naming: `usr/<fork-owner>/<feature-name>` (follow git-worktree conventions)

### Workflow limitations
- **CRITICAL**: GitHub Actions workflows CANNOT run in fork repositories
- Workflow operations (list, view, run, enable, disable) MUST be performed on the upstream repository
- When working with workflows, ensure you're operating on the upstream repo, not the fork
- Use `--repo <upstream-owner>/<repo-name>` flag if needed to target upstream explicitly

### Workflow conventions
- Check if workflows exist in upstream before attempting operations
- Use appropriate branch refs when triggering workflows (typically main or develop branches in upstream)
- Watch long-running workflows to provide status updates
- Rerun failed workflows before creating new ones

### GitHub token management
- Check authentication status before operations: `gh auth status`
- **First time setup**: Ask user to provide a token, then authenticate and save it
- **Subsequent usage**: Automatically use existing saved token
- Token should have appropriate scopes: repo, workflow, read:org, etc.
- For workflow operations, token must have `workflow` scope

### Token storage
- **Primary**: Save to `~/.github-ops-token` file for user-specific persistent storage
  - Create `~/.github-ops-token` file automatically when user provides token
  - Save token and metadata in structured format:
    ```
    GITHUB_TOKEN=<token>
    GITHUB_USERNAME=<username>
    GITHUB_INSTANCE=<github.com or enterprise hostname>
    GITHUB_AUTH_DATE=<ISO timestamp>
    ```
  - Set appropriate file permissions (chmod 600)
  - Load automatically in future sessions
- **Alternative**: Use `gh auth login` - stores token securely in user's credential manager

### Extracting username and instance from token
- Use GitHub API to get user info when token is provided:
  ```bash
  curl -H "Authorization: token <token>" https://<instance>/api/v3/user
  ```
- Default instance: github.com (or detect from target repository context)
- Enterprise detection: Use target repository's instance for Enterprise setups

### Security
- **Set restrictive permissions** on `~/.github-ops-token` (chmod 600 - read/write by owner only)
- **Never commit token files** - User home directory files are not in git repos

### Destructive operations
- **MUST** get user confirmation before: merge, close, delete, disable, cancel operations
- Ask for confirmation using `ask_user_question`

## Error handling

### Authentication protocol

Before any GitHub operation, follow this authentication check:

1. **Detect target repository context** (follow context detection protocol first)
   - Determine if target is GitHub.com or GitHub Enterprise
   - Extract organization/repo information
   - Identify if this is a fork-based workflow

2. **Check for existing token file and load if available:**
   ```bash
   if [ -f ~/.github-ops-token ]; then
     # Load all variables from the token file
     export $(cat ~/.github-ops-token | grep -v '^#' | xargs)
   fi
   ```

3. **Check authentication status:**
   ```bash
   gh auth status
   ```
   Note: This checks overall GitHub authentication, not access to a specific repository

4. **If authenticated:**
   - Verify authentication matches target context (GitHub.com vs Enterprise)
   - If metadata exists in `~/.github-ops-token`, compare with target context:
     - Check if `GITHUB_INSTANCE` matches target repository's instance
     - Inform user if there's a mismatch: "Authenticated to $GITHUB_INSTANCE as $GITHUB_USERNAME, but target is <target-instance>"
   - Check if authenticated user has access to target repository by attempting a simple operation like:
     ```bash
     gh repo view <target-repo> --json nameWithOwner
     ```
   - If repo access fails, proceed to step 5
   - If repo access succeeds, proceed with operation

5. **If not authenticated or access insufficient:**
   - Check if `~/.github-ops-token` file exists
   - **If token file exists**: Load and use it (already done in step 2), then re-check authentication
   - **If token file does not exist**: 
     - Ask user to provide GitHub personal access token: "Please provide your GitHub personal access token for authentication"
     - Extract GitHub username and instance from the token using GitHub API:
       ```bash
       curl -H "Authorization: token <token>" https://<instance>/api/v3/user
       ```
     - Create `~/.github-ops-token` file with token and metadata:
       ```bash
       cat > ~/.github-ops-token << EOF
       GITHUB_TOKEN=<token>
       GITHUB_USERNAME=<username>
       GITHUB_INSTANCE=<instance>
       GITHUB_AUTH_DATE=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
       EOF
       ```
     - Set file permissions: `chmod 600 ~/.github-ops-token`
     - Load all variables: `export $(cat ~/.github-ops-token | grep -v '^#' | xargs)`
     - Verify: `gh auth status`

6. **Token scopes validation based on target:**
   - For workflow operations: verify `workflow` scope
   - For PR operations: verify `repo` scope
   - For organization access: verify `read:org` scope
   - For specific target repo: verify token has access to that repository
   - If scopes are insufficient, inform user which scopes are needed and why

7. **Enterprise vs GitHub.com detection:**
   ```bash
   # Extract hostname from remote URL
   REMOTE_URL=$(git remote get-url origin)
   if [[ "$REMOTE_URL" == *"github.com"* ]]; then
     HOST="github.com"
   else
     # Extract enterprise hostname
     HOST=$(echo "$REMOTE_URL" | sed -E 's#^[a-z]+://##; s#^[^@]*@##; s#[:/].*##')
   fi
   ```
   - Use detected hostname for authentication context
   - Inform user if authenticating to Enterprise instance

### Missing gh CLI
```bash
Error: GitHub CLI (gh) is not installed.
Install it from: https://cli.github.com/
Or run: curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg && echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null && sudo apt update && sudo apt install gh
```

### Not authenticated
```bash
Error: Not authenticated with GitHub.
Run: gh auth login
```

### Authentication context mismatch
```bash
Error: Authentication context does not match target repository.
Current authentication: <current-host>
Target repository: <target-host>/<target-org>/<target-repo>
Please re-authenticate with the correct GitHub instance or provide a token with access to the target repository.
```

### Insufficient repository access
```bash
Error: Authenticated user does not have access to target repository <target-repo>.
Please verify:
1. Your account has access to <target-org>/<target-repo>
2. Your token has the necessary scopes for this repository
3. You are authenticated to the correct GitHub instance
```

### Rate limiting
Inform users when rate-limited and suggest waiting or using authentication tokens with appropriate scopes.

### Workflow operations in forks
```bash
Error: GitHub Actions workflows cannot run in fork repositories.
Workflow operations must be performed on the upstream repository.
Use: gh workflow list --repo <upstream-owner>/<repo-name>
```

## CRITICAL Rules

- **MUST** check if `gh` is installed before executing any command
- **MUST** detect repository and branch context before operations (follow context detection protocol)
- **MUST** automatically load token and metadata from `~/.github-ops-token` if file exists before checking authentication
- **MUST** check authentication status with target repository context before operations (follow authentication protocol)
- **MUST** verify authentication matches target context (GitHub.com vs Enterprise, org access, repo access)
- **MUST** compare persisted metadata (username, instance) with target context and inform user of mismatches
- **MUST** ask user for GitHub token on first use if `~/.github-ops-token` does not exist
- **MUST** automatically save provided token with metadata to `~/.github-ops-token`
- **MUST** set restrictive permissions (chmod 600) on `~/.github-ops-token` file
- **MUST** validate token scopes before performing operations based on target repository requirements
- **MUST** handle errors gracefully and provide helpful error messages
- **MUST NOT** perform destructive operations (merge, close, delete, disable, cancel) without user confirmation
- **MUST NOT** attempt to run workflows in fork repositories - workflows only work in upstream
- **MUST** ensure workflow operations target the upstream repository
- **MUST** respect GitHub API rate limits and inform users if rate-limited
- **MUST** use appropriate flags for JSON output when parsing results programmatically
