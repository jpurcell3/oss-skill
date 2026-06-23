#!/bin/bash
# Install oss-check skill for Devin AI Agent

set -e

echo "🚀 Installing OSS Check Skill for Devin..."

# Detect OS and set appropriate paths
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    DEVIN_SKILLS_DIR="$HOME/.devin/skills"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    DEVIN_SKILLS_DIR="$HOME/.devin/skills"
else
    # Windows (Git Bash)
    DEVIN_SKILLS_DIR="$USERPROFILE/.devin/skills"
fi

SKILL_NAME="oss-check"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create skills directory if it doesn't exist
echo "📁 Creating skills directory: $DEVIN_SKILLS_DIR"
mkdir -p "$DEVIN_SKILLS_DIR"

# Copy skill files
echo "📋 Copying skill files..."
cp -r "$SCRIPT_DIR/skills/$SKILL_NAME" "$DEVIN_SKILLS_DIR/"

# Copy CLI tool (optional)
if [ -f "$SCRIPT_DIR/oss_compliance.py" ]; then
    echo "🔧 Copying CLI tool..."
    cp "$SCRIPT_DIR/oss_compliance.py" "$DEVIN_SKILLS_DIR/$SKILL_NAME/"
fi

# Copy configuration template (optional)
if [ -f "$SCRIPT_DIR/oss_compliance_config.yaml.example" ]; then
    echo "⚙️  Copying configuration template..."
    cp "$SCRIPT_DIR/oss_compliance_config.yaml.example" "$DEVIN_SKILLS_DIR/$SKILL_NAME/"
fi

echo "✅ OSS Check Skill installed successfully!"
echo ""
echo "📁 Location: $DEVIN_SKILLS_DIR/$SKILL_NAME"
echo "🚀 Usage: Ask Devin to 'oss-check [repository-name]'"
echo ""
echo "📝 Next steps:"
echo "  1. Copy configuration template: cp $DEVIN_SKILLS_DIR/$SKILL_NAME/oss_compliance_config.yaml.example ~/.oss-check-config.yaml"
echo "  2. Edit configuration with your credentials"
echo "  3. Test the skill: oss-check scan fusion-stage"