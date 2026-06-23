# Install oss-check skill for Devin AI Agent (Windows)

$ErrorActionPreference = "Stop"

Write-Host "🚀 Installing OSS Check Skill for Devin..." -ForegroundColor Cyan

# Set paths
$devinSkillsDir = "$env:USERPROFILE\.devin\skills"
$skillName = "oss-check"
$scriptDir = $PSScriptRoot

# Create skills directory if it doesn't exist
Write-Host "📁 Creating skills directory: $devinSkillsDir" -ForegroundColor Yellow
if (-not (Test-Path $devinSkillsDir)) {
    New-Item -ItemType Directory -Path $devinSkillsDir -Force | Out-Null
}

# Copy skill files
Write-Host "📋 Copying skill files..." -ForegroundColor Yellow
Copy-Item -Recurse "$scriptDir\skills\$skillName" "$devinSkillsDir\" -Force

# Copy CLI tool (optional)
if (Test-Path "$scriptDir\oss_compliance.py") {
    Write-Host "🔧 Copying CLI tool..." -ForegroundColor Yellow
    Copy-Item "$scriptDir\oss_compliance.py" "$devinSkillsDir\$skillName\" -Force
}

# Copy configuration template (optional)
if (Test-Path "$scriptDir\oss_compliance_config.yaml.example") {
    Write-Host "⚙️  Copying configuration template..." -ForegroundColor Yellow
    Copy-Item "$scriptDir\oss_compliance_config.yaml.example" "$devinSkillsDir\$skillName\" -Force
}

Write-Host "✅ OSS Check Skill installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "📁 Location: $devinSkillsDir\$skillName" -ForegroundColor Cyan
Write-Host "🚀 Usage: Ask Devin to 'oss-check [repository-name]'" -ForegroundColor Yellow
Write-Host ""
Write-Host "📝 Next steps:" -ForegroundColor White
Write-Host "  1. Copy configuration template to your home directory" -ForegroundColor Gray
Write-Host "  2. Edit configuration with your credentials" -ForegroundColor Gray
Write-Host "  3. Test the skill with: oss-check scan fusion-stage" -ForegroundColor Gray
