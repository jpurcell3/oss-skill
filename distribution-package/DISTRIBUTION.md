# OSS Check Skill - Distribution Guide

This document explains how to package and distribute the oss-check skill for various use cases, including installation in AI agents like Devin, Claude, and other development environments.

---

## 📦 Distribution Formats

### 1. **Python Package (Recommended)**

The skill can be distributed as a standard Python package via PyPI or private package repositories.

#### **Build Distribution Package**

```bash
# Install build dependencies
pip install build twine

# Build wheel and source distribution
python -m build

# Output:
# dist/oss_check_skill-1.0.0-py3-none-any.whl
# dist/oss-check-skill-1.0.0.tar.gz
```

#### **Install from PyPI**

```bash
pip install oss-check-skill
```

#### **Install from Wheel File**

```bash
pip install dist/oss_check_skill-1.0.0-py3-none-any.whl
```

#### **Install from Source**

```bash
pip install dist/oss-check-skill-1.0.0.tar.gz
```

#### **Install in Development Mode**

```bash
cd /path/to/oss-skill
pip install -e .
```

#### **Usage After Installation**

```bash
# CLI command (available after installation)
oss-check scan fusion-stage
oss-check list-repos
oss-check check-config
```

---

### 2. **Devin Skill Integration**

For Devin integration, the skill files need to be placed in the `.devin/skills/` directory.

#### **Manual Installation**

```bash
# Copy skill directory to Devin skills folder
mkdir -p ~/.devin/skills/oss-check
cp -r skills/oss-check/* ~/.devin/skills/oss-check/

# Or for project-specific skills
mkdir -p .devin/skills/oss-check
cp -r skills/oss-check/* .devin/skills/oss-check/
```

#### **Installation Script**

Create an installation script `install_devin.sh`:

```bash
#!/bin/bash
# Install oss-check skill for Devin

DEVIN_SKILLS_DIR="$HOME/.devin/skills"
SKILL_NAME="oss-check"

# Create skills directory if it doesn't exist
mkdir -p "$DEVIN_SKILLS_DIR"

# Copy skill files
cp -r "skills/$SKILL_NAME" "$DEVIN_SKILLS_DIR/"

echo "✅ OSS Check Skill installed for Devin"
echo "📁 Location: $DEVIN_SKILLS_DIR/$SKILL_NAME"
echo "🚀 Usage: Ask Devin to 'oss-check [repository-name]'"
```

#### **Windows Installation Script**

Create `install_devin.ps1`:

```powershell
# Install oss-check skill for Devin

$devinSkillsDir = "$env:USERPROFILE\.devin\skills"
$skillName = "oss-check"

# Create skills directory if it doesn't exist
if (-not (Test-Path $devinSkillsDir)) {
    New-Item -ItemType Directory -Path $devinSkillsDir -Force
}

# Copy skill files
Copy-Item -Recurse "skills\$skillName" "$devinSkillsDir\" -Force

Write-Host "✅ OSS Check Skill installed for Devin" -ForegroundColor Green
Write-Host "📁 Location: $devinSkillsDir\$skillName" -ForegroundColor Cyan
Write-Host "🚀 Usage: Ask Devin to 'oss-check [repository-name]'" -ForegroundColor Yellow
```

---

### 3. **SDD Kit Format**

For SDD Kit integration, follow the AgentOps structure:

#### **Directory Structure**

```
oss-check-skill/
├── SKILL.md              # Skill definition
├── oss_compliance.py     # CLI entry point
├── src/
│   └── oss_compliance/
│       ├── __init__.py
│       ├── scanner.py
│       ├── config.py
│       └── reporter.py
├── pyproject.toml        # Package configuration
├── README.md             # Documentation
└── DISTRIBUTION.md       # This file
```

#### **SDD Kit Installation**

```bash
# Add to AgentOps repository
cp -r oss-check-skill /path/to/AgentOps/skills/oss-check

# Or as a global skill
cp -r oss-check-skill ~/.agents/skills/oss-check
```

---

### 4. **Docker Container Distribution**

For containerized environments, create a Docker image with the skill pre-installed.

#### **Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

# Copy skill files
COPY src/ src/
COPY skills/ skills/
COPY oss_compliance.py .

# Set up configuration
ENV PYTHONPATH=/app/src:$PYTHONPATH

# Default command
CMD ["python", "oss_compliance.py", "--help"]
```

#### **Build Docker Image**

```bash
docker build -t oss-check-skill:1.0.0 .
```

#### **Run Docker Container**

```bash
# Interactive shell
docker run -it --rm oss-check-skill:1.0.0 bash

# Scan a repository
docker run -it --rm \
  -v /path/to/config:/app/config \
  oss-check-skill:1.0.0 \
  python oss_compliance.py scan fusion-stage --config /app/config/oss_compliance_config.yaml
```

---

### 5. **GitHub Release Distribution**

For easy distribution via GitHub releases.

#### **Create Release**

```bash
# Tag the release
git tag -a v1.0.0 -m "OSS Check Skill v1.0.0 - Initial release"
git push origin v1.0.0

# Build distribution packages
python -m build

# Upload to GitHub Release
gh release create v1.0.0 \
  dist/oss_check_skill-1.0.0-py3-none-any.whl \
  dist/oss-check-skill-1.0.0.tar.gz \
  --notes "Initial release of OSS Check Skill"
```

#### **Install from GitHub Release**

```bash
# Direct download and install
pip install https://github.com/your-org/oss-check-skill/releases/download/v1.0.0/oss_check_skill-1.0.0-py3-none-any.whl
```

---

## 🎯 **Installation Methods by Use Case**

### **For Local Development**

```bash
# Development mode (editable)
cd /path/to/oss-skill
pip install -e .
```

### **For Production Deployment**

```bash
# From PyPI
pip install oss-check-skill

# From private repository
pip install --index-url https://your-private-pypi.com/simple oss-check-skill
```

### **For AI Agent Integration**

#### **Devin**
```bash
# Manual skill installation
mkdir -p ~/.devin/skills/oss-check
cp -r skills/oss-check/* ~/.devin/skills/oss-check/
```

#### **Claude Desktop**
```bash
# Add to Claude Desktop configuration
mkdir -p ~/.claude/skills/oss-check
cp -r skills/oss-check/* ~/.claude/skills/oss-check/
```

#### **Cursor AI**
```bash
# Add to Cursor skills directory
mkdir -p ~/.cursor/skills/oss-check
cp -r skills/oss-check/* ~/.cursor/skills/oss-check/
```

---

## 🔧 **Configuration Distribution**

### **Configuration Template**

The skill includes a configuration template that users can customize:

```bash
# Copy example configuration
cp oss_compliance_config.yaml.example ~/.oss-check-config.yaml

# Edit with your credentials
nano ~/.oss-check-config.yaml
```

### **Environment Variables**

For production use, environment variables are recommended:

```bash
export GITHUB_TOKEN=your_token
export GITHUB_API_URL=https://api.github.com
export GITHUB_ORG=your_organization
export JENKINS_URL=https://your-jenkins.com
export JENKINS_USER=your_user
export JENKINS_TOKEN=your_token
```

---

## 📋 **Pre-Installation Checklist**

Before distributing the skill, ensure:

- [ ] **Package metadata updated** (pyproject.toml)
- [ ] **Dependencies specified correctly** (requirements.txt or pyproject.toml)
- [ ] **Skill file properly formatted** (SKILL.md)
- [ ] **Documentation complete** (README.md, DISTRIBUTION.md)
- [ ] **Tests passing** (pytest)
- [ ] **No sensitive data in repository** (use .gitignore)
- [ ] **Version number updated** (semantic versioning)
- [ ] **License file included** (LICENSE)
- [ ] **Changelog maintained** (CHANGELOG.md)

---

## 🚀 **Distribution Workflow**

### **Automated Distribution Pipeline**

```yaml
# .github/workflows/distribute.yml
name: Build and Distribute

on:
  release:
    types: [created]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install build dependencies
        run: |
          pip install build twine
      
      - name: Build package
        run: |
          python -m build
      
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
        run: |
          twine upload dist/*
      
      - name: Upload to GitHub Release
        uses: softprops/action-gh-release@v1
        with:
          files: dist/*
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## 📦 **Package Contents**

### **Wheel Package Contents**

```
oss_check_skill-1.0.0-py3-none-any.whl
├── oss_compliance/
│   ├── __init__.py
│   ├── scanner.py
│   ├── config.py
│   └── reporter.py
├── oss_compliance_config.yaml.example
└── metadata files
```

### **Source Distribution Contents**

```
oss-check-skill-1.0.0.tar.gz
├── oss-check-skill-1.0.0/
│   ├── src/
│   │   └── oss_compliance/
│   ├── skills/
│   │   └── oss-check/
│   ├── oss_compliance.py
│   ├── pyproject.toml
│   ├── README.md
│   └── other files
```

---

## 🎓 **Best Practices for Distribution**

1. **Semantic Versioning**: Use MAJOR.MINOR.PATCH format
2. **Changelog**: Maintain CHANGELOG.md for each release
3. **Testing**: Ensure all tests pass before distribution
4. **Documentation**: Keep README.md up to date
5. **Security**: Never include credentials in distributed packages
6. **Dependencies**: Pin dependency versions for stability
7. **Compatibility**: Test on multiple Python versions
8. **Metadata**: Maintain accurate package metadata

---

## 🔗 **Distribution Channels**

### **Public Distribution**
- **PyPI**: Public Python Package Index
- **GitHub Releases**: Direct downloads from GitHub
- **Conda**: Conda package manager (if applicable)

### **Private Distribution**
- **Private PyPI**: Using devpi or Artifactory
- **Internal Git Repository**: For enterprise distribution
- **Docker Registry**: For containerized distribution
- **File System**: For local network distribution

---

## 📞 **Support and Documentation**

For installation issues or questions:
- **Documentation**: See README.md
- **Issues**: Report via GitHub Issues
- **Support**: Contact development team

---

## 🔄 **Version Updates**

When updating the skill:

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Run tests to ensure compatibility
4. Build new distribution packages
5. Create new GitHub release
6. Publish to distribution channels
7. Announce to users

---

**Last Updated**: 2026-06-23  
**Version**: 1.0.0  
**Maintained By**: Development Team