#!/bin/bash

# GitHub Setup Script for FIFA Match Tracker
# This script will help you publish your project to GitHub

echo "🚀 FIFA Match Tracker - GitHub Setup"
echo "===================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install git first."
    exit 1
fi

echo "✅ Git is installed"
echo ""

# Check if already initialized
if [ -d .git ]; then
    echo "⚠️  Git repository already initialized"
    read -p "Do you want to remove existing git history and start fresh? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf .git
        echo "✅ Removed existing git history"
    else
        echo "ℹ️  Keeping existing git configuration"
    fi
fi

# Initialize git if not already done
if [ ! -d .git ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
    echo ""
fi

# Check for sensitive files
echo "🔐 Checking for sensitive files..."
if [ -f config.env ]; then
    echo "⚠️  Found config.env - This file is already in .gitignore (GOOD)"
fi
if [ -f fifa_data.json ]; then
    echo "⚠️  Found fifa_data.json - This file is already in .gitignore (GOOD)"
fi
echo ""

# Get repository URL
echo "📝 GitHub Repository Setup"
echo ""
read -p "Enter your GitHub username: " github_user
read -p "Enter repository name (e.g., fifa-match-tracker): " repo_name

REPO_URL="https://github.com/${github_user}/${repo_name}.git"

echo ""
echo "Repository URL: $REPO_URL"
echo ""

# Add all files
echo "📁 Adding files to git..."
git add .

# Show what will be committed
echo ""
echo "📋 Files to be committed:"
git status --short
echo ""

read -p "Do these files look correct? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Setup cancelled. Please review files and try again."
    exit 1
fi

# Create commit
echo ""
echo "💾 Creating initial commit..."
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

echo "✅ Initial commit created"
echo ""

# Add remote
echo "🔗 Adding remote repository..."
if git remote | grep -q origin; then
    echo "⚠️  Remote 'origin' already exists. Removing it..."
    git remote remove origin
fi

git remote add origin "$REPO_URL"
echo "✅ Remote repository added"
echo ""

# Rename branch to main
echo "🌿 Setting up main branch..."
git branch -M main
echo "✅ Branch renamed to main"
echo ""

# Push
echo "🚀 Ready to push to GitHub!"
echo ""
echo "⚠️  IMPORTANT: Make sure you have created the repository on GitHub first!"
echo "   Go to: https://github.com/new"
echo "   Repository name: $repo_name"
echo "   Description: Professional Telegram bot for FIFA match tracking"
echo "   Do NOT initialize with README, .gitignore, or license"
echo ""
read -p "Have you created the repository on GitHub? (y/n): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "ℹ️  Please create the repository on GitHub first, then run:"
    echo "   git push -u origin main"
    exit 0
fi

echo ""
echo "🚀 Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 SUCCESS! Your project is now on GitHub!"
    echo ""
    echo "📍 Repository URL: https://github.com/${github_user}/${repo_name}"
    echo ""
    echo "Next steps:"
    echo "1. Go to your repository on GitHub"
    echo "2. Add topics: telegram-bot, fifa, python, match-tracker"
    echo "3. Add a description"
    echo "4. (Optional) Create a release: v2.0.0"
    echo ""
    echo "⭐ Don't forget to star your own repository!"
else
    echo ""
    echo "❌ Push failed. Common issues:"
    echo "   - Repository doesn't exist on GitHub"
    echo "   - Authentication failed (try SSH instead)"
    echo "   - No permission to push"
    echo ""
    echo "To retry manually:"
    echo "   git push -u origin main"
fi

