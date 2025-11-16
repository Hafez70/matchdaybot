# GitHub Setup Script for FIFA Match Tracker
# PowerShell version for Windows

Write-Host "🚀 FIFA Match Tracker - GitHub Setup" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# Check if git is installed
try {
    git --version | Out-Null
    Write-Host "✅ Git is installed" -ForegroundColor Green
} catch {
    Write-Host "❌ Git is not installed. Please install git first." -ForegroundColor Red
    Write-Host "Download from: https://git-scm.com/download/win" -ForegroundColor Yellow
    exit 1
}

Write-Host ""

# Check if already initialized
if (Test-Path .git) {
    Write-Host "⚠️  Git repository already initialized" -ForegroundColor Yellow
    $response = Read-Host "Do you want to remove existing git history and start fresh? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Remove-Item -Recurse -Force .git
        Write-Host "✅ Removed existing git history" -ForegroundColor Green
    } else {
        Write-Host "ℹ️  Keeping existing git configuration" -ForegroundColor Cyan
    }
}

# Initialize git if not already done
if (!(Test-Path .git)) {
    Write-Host "📦 Initializing git repository..." -ForegroundColor Cyan
    git init
    Write-Host "✅ Git repository initialized" -ForegroundColor Green
    Write-Host ""
}

# Check for sensitive files
Write-Host "🔐 Checking for sensitive files..." -ForegroundColor Cyan
if (Test-Path config.env) {
    Write-Host "⚠️  Found config.env - This file is already in .gitignore (GOOD)" -ForegroundColor Yellow
}
if (Test-Path fifa_data.json) {
    Write-Host "⚠️  Found fifa_data.json - This file is already in .gitignore (GOOD)" -ForegroundColor Yellow
}
Write-Host ""

# Get repository URL
Write-Host "📝 GitHub Repository Setup" -ForegroundColor Cyan
Write-Host ""
$github_user = Read-Host "Enter your GitHub username"
$repo_name = Read-Host "Enter repository name (e.g., fifa-match-tracker)"

$REPO_URL = "https://github.com/$github_user/$repo_name.git"

Write-Host ""
Write-Host "Repository URL: $REPO_URL" -ForegroundColor Cyan
Write-Host ""

# Add all files
Write-Host "📁 Adding files to git..." -ForegroundColor Cyan
git add .

# Show what will be committed
Write-Host ""
Write-Host "📋 Files to be committed:" -ForegroundColor Cyan
git status --short
Write-Host ""

$response = Read-Host "Do these files look correct? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "❌ Setup cancelled. Please review files and try again." -ForegroundColor Red
    exit 1
}

# Create commit
Write-Host ""
Write-Host "💾 Creating initial commit..." -ForegroundColor Cyan
git commit -m "Initial commit: FIFA Match Tracking Bot v2.0 - Modular Edition

Features:
- User registration system with Telegram ID
- League system with unique invite codes
- Support for 1v1, 2v2, 1v2, 2v1 match types
- League-scoped statistics and leaderboards
- Persian calendar support
- Name editing (users can edit own names)
- Comprehensive documentation
- Modular architecture with clean separation of concerns

Documentation:
- Complete setup guides
- Migration instructions for existing users
- Architecture documentation
- Visual feature maps"

Write-Host "✅ Initial commit created" -ForegroundColor Green
Write-Host ""

# Add remote
Write-Host "🔗 Adding remote repository..." -ForegroundColor Cyan
$remotes = git remote
if ($remotes -contains "origin") {
    Write-Host "⚠️  Remote 'origin' already exists. Removing it..." -ForegroundColor Yellow
    git remote remove origin
}

git remote add origin $REPO_URL
Write-Host "✅ Remote repository added" -ForegroundColor Green
Write-Host ""

# Rename branch to main
Write-Host "🌿 Setting up main branch..." -ForegroundColor Cyan
git branch -M main
Write-Host "✅ Branch renamed to main" -ForegroundColor Green
Write-Host ""

# Push
Write-Host "🚀 Ready to push to GitHub!" -ForegroundColor Cyan
Write-Host ""
Write-Host "⚠️  IMPORTANT: Make sure you have created the repository on GitHub first!" -ForegroundColor Yellow
Write-Host "   Go to: https://github.com/new" -ForegroundColor Yellow
Write-Host "   Repository name: $repo_name" -ForegroundColor Yellow
Write-Host "   Description: Professional Telegram bot for FIFA match tracking" -ForegroundColor Yellow
Write-Host "   Do NOT initialize with README, .gitignore, or license" -ForegroundColor Yellow
Write-Host ""
$response = Read-Host "Have you created the repository on GitHub? (y/n)"
if ($response -ne 'y' -and $response -ne 'Y') {
    Write-Host "ℹ️  Please create the repository on GitHub first, then run:" -ForegroundColor Cyan
    Write-Host "   git push -u origin main" -ForegroundColor White
    exit 0
}

Write-Host ""
Write-Host "🚀 Pushing to GitHub..." -ForegroundColor Cyan
git push -u origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "🎉 SUCCESS! Your project is now on GitHub!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📍 Repository URL: https://github.com/$github_user/$repo_name" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Go to your repository on GitHub" -ForegroundColor White
    Write-Host "2. Add topics: telegram-bot, fifa, python, match-tracker" -ForegroundColor White
    Write-Host "3. Add a description" -ForegroundColor White
    Write-Host "4. (Optional) Create a release: v2.0.0" -ForegroundColor White
    Write-Host ""
    Write-Host "⭐ Don't forget to star your own repository!" -ForegroundColor Yellow
} else {
    Write-Host ""
    Write-Host "❌ Push failed. Common issues:" -ForegroundColor Red
    Write-Host "   - Repository doesn't exist on GitHub" -ForegroundColor Yellow
    Write-Host "   - Authentication failed (try SSH instead)" -ForegroundColor Yellow
    Write-Host "   - No permission to push" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "To retry manually:" -ForegroundColor Cyan
    Write-Host "   git push -u origin main" -ForegroundColor White
}

