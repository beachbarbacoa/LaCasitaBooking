#!/bin/bash

# Clean Wasp installation script
echo "=== Installing Wasp Properly ==="

# Remove existing wasp installations
npm uninstall -g wasp
npm uninstall -g @wasp-lang/cli

# Clear npm cache
npm cache clean --force

# Install correct Wasp
curl -sSL https://get.wasp-lang.dev/installer.sh | sh

# Verify installation
source ~/.wasprc
wasp --version

# Create new project
mkdir wasp-core
cd wasp-core
wasp new .