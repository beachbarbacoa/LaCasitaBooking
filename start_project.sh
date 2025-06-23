#!/bin/bash

# Fix Node.js PATH
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Verify Node.js
node -v || { echo "Node.js not found. Please install it first."; exit 1; }
npm -v || { echo "npm not found. Please install Node.js."; exit 1; }

# Start Wasp project
cd wasp-core
wasp start