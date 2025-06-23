#!/bin/bash
# Safe Git configuration script
echo "🚀 Setting up Git configuration"
read -p "Enter your full name: " name
read -p "Enter your GitHub email: " email

git config --global user.name "$name"
git config --global user.email "$email"

echo "✅ Git configured for: $name <$email>"
echo "ℹ️ Next steps:"
echo "1. Generate GitHub token at https://github.com/settings/tokens"
echo "2. Use token as password when pushing"