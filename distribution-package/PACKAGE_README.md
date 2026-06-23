# OSS Check Skill - Distribution Package v1.0.0

This distribution package contains everything needed to install and use the OSS Check Skill in various environments.

---

## 📦 Package Contents

### Python Distribution Files
- `oss_check_skill-1.0.0-py3-none-any.whl` - Wheel file for pip installation
- `oss_check_skill-1.0.0.tar.gz` - Source distribution

### Source Code
- `src/` - Core library source code
- `oss_compliance.py` - CLI entry point
- `pyproject.toml` - Package configuration

### Skill Definition
- `skills/oss-check/` - Devin/AI agent skill definition

### Documentation
- `README.md` - User documentation
- `INSTALLATION.md` - Installation guide
- `DISTRIBUTION.md` - Distribution guide
- `PACKAGE_README.md` - This file

### Installation Scripts
- `install_devin.sh` - Unix/Linux/macOS installation script
- `install_devin.ps1` - Windows PowerShell installation script

### Configuration
- `oss_compliance_config.yaml.example` - Configuration template

---

## 🚀 Quick Installation

### Option 1: Python Package Installation

```bash
# Install from wheel file
pip install oss_check_skill-1.0.0-py3-none-any.whl

# Or install from source
pip install oss_check_skill-1.0.0.tar.gz
```

### Option 2: Development Mode Installation

```bash
# Install in development mode
pip install -e .
```

### Option 3: Devin AI Agent Installation

```bash
# Linux/macOS
bash install_devin.sh

# Windows PowerShell
.\install_devin.ps1
```

---

## 📋 Installation Methods

### For Local Development
```bash
pip install -e .
```

### For Production
```bash
pip install oss_check_skill-1.0.0-py3-none-any.whl
```

### For AI Agents
- **Devin**: Run `install_devin.sh` or `install_devin.ps1`
- **Claude**: Copy `skills/oss-check/` to `~/.claude/skills/`
- **Cursor**: Copy `skills/oss-check/` to `~/.cursor/skills/`

---

## ⚙️ Configuration

### Setup Configuration File

```bash
# Copy configuration template
cp oss_compliance_config.yaml.example ~/.oss-check-config.yaml

# Edit with your credentials
nano ~/.oss-check-config.yaml
```

### Environment Variables

```bash
export GITHUB_TOKEN=your_token
export GITHUB_API_URL=https://api.github.com
export GITHUB_ORG=your_organization
```

---

## ✅ Verification

### Test Python Installation
```bash
pip show oss-check-skill
oss-check --help
```

### Test Functionality
```bash
oss-check check-config
oss-check list-repos
oss-check scan fusion-stage
```

---

## 📚 Documentation

- **README.md** - Complete user documentation
- **INSTALLATION.md** - Detailed installation instructions
- **DISTRIBUTION.md** - Distribution and packaging guide

---

## 🔧 Troubleshooting

### Installation Issues
- Ensure Python 3.9+ is installed
- Use `pip install --upgrade pip` to upgrade pip
- Try `pip install --force-reinstall oss-check-skill`

### Configuration Issues
- Verify configuration file path
- Check environment variables are set
- Run `oss-check check-config` to verify

---

## 📞 Support

For issues or questions:
- Review documentation files
- Check GitHub Issues
- Contact development team

---

## 📊 Package Information

- **Version**: 1.0.0
- **Python Version**: 3.9+
- **License**: MIT
- **Dependencies**: requests>=2.31.0, PyYAML>=6.0.1, urllib3>=2.0.0, cryptography>=41.0.0

---

## 🔄 Updates

To update to a new version:
1. Download new distribution package
2. Run installation command with `--upgrade` flag
3. Review changelog for new features

---

**Package Version**: 1.0.0  
**Release Date**: 2026-06-23  
**Maintained By**: Development Team