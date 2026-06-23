# Installation Guide

This guide provides step-by-step instructions for installing the oss-check skill in various environments.

---

## 🎯 **Quick Installation**

### **Option 1: Python Package (Recommended)**

```bash
pip install oss-check-skill
```

### **Option 2: Development Mode**

```bash
cd /path/to/oss-skill
pip install -e .
```

### **Option 3: Devin AI Agent**

```bash
# Linux/macOS
bash install_devin.sh

# Windows PowerShell
.\install_devin.ps1
```

---

## 📦 **Detailed Installation Methods**

### **1. Python Package Installation**

#### **From PyPI (when published)**

```bash
pip install oss-check-skill
```

#### **From Wheel File**

```bash
# Download the wheel file
wget https://github.com/your-org/oss-check-skill/releases/download/v1.0.0/oss_check_skill-1.0.0-py3-none-any.whl

# Install
pip install oss_check_skill-1.0.0-py3-none-any.whl
```

#### **From Source Distribution**

```bash
# Download source distribution
wget https://github.com/your-org/oss-check-skill/releases/download/v1.0.0/oss-check-skill-1.0.0.tar.gz

# Install
pip install oss-check-skill-1.0.0.tar.gz
```

#### **From Local Repository**

```bash
cd /path/to/oss-skill
pip install .
```

#### **Development Mode (Editable)**

```bash
cd /path/to/oss-skill
pip install -e .
```

**Benefits of development mode:**
- Changes to source code are immediately reflected
- No need to reinstall after modifications
- Useful for development and testing

---

### **2. Devin AI Agent Installation**

#### **Manual Installation**

```bash
# Create Devin skills directory
mkdir -p ~/.devin/skills/oss-check

# Copy skill files
cp -r skills/oss-check/* ~/.devin/skills/oss-check/
```

#### **Automated Installation**

```bash
# Linux/macOS
chmod +x install_devin.sh
bash install_devin.sh

# Windows PowerShell
.\install_devin.ps1
```

#### **Project-Specific Installation**

```bash
# For a specific project
mkdir -p .devin/skills/oss-check
cp -r skills/oss-check/* .devin/skills/oss-check/
```

#### **Verify Installation**

```bash
# Check skill file exists
ls -la ~/.devin/skills/oss-check/SKILL.md
```

---

### **3. Claude Desktop Installation**

#### **Manual Installation**

```bash
# Create Claude skills directory
mkdir -p ~/.claude/skills/oss-check

# Copy skill files
cp -r skills/oss-check/* ~/.claude/skills/oss-check/
```

#### **Verify Installation**

```bash
# Check skill file exists
ls -la ~/.claude/skills/oss-check/SKILL.md
```

---

### **4. Cursor AI Installation**

#### **Manual Installation**

```bash
# Create Cursor skills directory
mkdir -p ~/.cursor/skills/oss-check

# Copy skill files
cp -r skills/oss-check/* ~/.cursor/skills/oss-check/
```

---

### **5. Docker Installation**

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

## ⚙️ **Configuration Setup**

### **Configuration File**

```bash
# Copy example configuration
cp oss_compliance_config.yaml.example ~/.oss-check-config.yaml

# Edit with your credentials
nano ~/.oss-check-config.yaml
```

### **Environment Variables**

```bash
# GitHub Configuration
export GITHUB_TOKEN=your_github_token
export GITHUB_API_URL=https://api.github.com
export GITHUB_ORG=your_organization

# Jenkins Configuration (optional)
export JENKINS_URL=https://your-jenkins.com
export JENKINS_USER=your_username
export JENKINS_TOKEN=your_jenkins_token

# Artifactory Configuration (optional)
export ARTIFACTORY_BASE=artifactory.example.com
export VIRTUAL_REPO_NPM=npm-virtual
```

### **Configuration Priority**

1. Environment variables (highest priority)
2. Configuration file
3. Default values (lowest priority)

---

## ✅ **Verification**

### **Verify Python Installation**

```bash
# Check if package is installed
pip show oss-check-skill

# Test CLI command
oss-check --help
oss-check check-config
```

### **Verify Devin Installation**

```bash
# Check skill file exists
ls -la ~/.devin/skills/oss-check/SKILL.md

# Test with Devin
# Ask: "oss-check fusion-stage"
```

### **Verify Functionality**

```bash
# Test configuration
oss-check check-config

# List repositories
oss-check list-repos

# Scan a repository
oss-check scan fusion-stage

# Generate JSON report
oss-check scan fusion-stage --format json > report.json

# Generate Markdown report
oss-check scan fusion-stage --format markdown > report.md
```

---

## 🔄 **Updating Installation**

### **Update Python Package**

```bash
# From PyPI
pip install --upgrade oss-check-skill

# From local repository
cd /path/to/oss-skill
pip install --upgrade .
```

### **Update Devin Skill**

```bash
# Re-run installation script
bash install_devin.sh

# Or manual update
cp -r skills/oss-check/* ~/.devin/skills/oss-check/
```

---

## 🗑️ **Uninstallation**

### **Uninstall Python Package**

```bash
pip uninstall oss-check-skill
```

### **Remove Devin Skill**

```bash
rm -rf ~/.devin/skills/oss-check
```

### **Remove Configuration**

```bash
rm ~/.oss-check-config.yaml
```

---

## 🔧 **Troubleshooting**

### **ImportError: No module named 'oss_compliance'**

```bash
# Reinstall the package
pip install --force-reinstall oss-check-skill

# Or in development mode
cd /path/to/oss-skill
pip install -e .
```

### **Skill not found in Devin**

```bash
# Verify skill file location
ls -la ~/.devin/skills/oss-check/SKILL.md

# Check Devin configuration
cat ~/.devin/instructions.md
```

### **Configuration not loading**

```bash
# Verify configuration file path
oss-check check-config

# Check environment variables
echo $GITHUB_TOKEN
echo $GITHUB_API_URL
```

### **GitHub API authentication failed**

```bash
# Verify token is set
echo $GITHUB_TOKEN

# Test token
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user
```

---

## 📞 **Support**

For installation issues:
- Check [DISTRIBUTION.md](DISTRIBUTION.md) for distribution options
- Review [README.md](README.md) for usage instructions
- Report issues via GitHub Issues

---

**Last Updated**: 2026-06-23  
**Version**: 1.0.0