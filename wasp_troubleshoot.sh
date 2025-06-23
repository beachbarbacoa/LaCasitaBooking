#!/bin/bash

# Wasp Installation Troubleshooting Script
echo "=== Wasp Installation Troubleshooting ==="

# 1. Check Node.js installation
echo -e "\n1. Checking Node.js:"
node -v || echo "ERROR: Node.js not found. Install from https://nodejs.org/"

# 2. Check npm installation
echo -e "\n2. Checking npm:"
npm -v || echo "ERROR: npm not found. Install Node.js to get npm"

# 3. Check PATH configuration
echo -e "\n3. Checking PATH:"
echo $PATH
echo "Ensure /usr/local/bin is in your PATH"

# 4. Check Wasp installation
echo -e "\n4. Attempting Wasp installation:"
npm install -g wasp

# 5. Verify Wasp installation
echo -e "\n5. Verifying Wasp:"
wasp --version || {
    echo "ERROR: Wasp not installed correctly"
    echo "Trying alternative installation method:"
    npm install -g @wasp-lang/cli
}

# 6. Final verification
echo -e "\n6. Final verification:"
if command -v wasp &> /dev/null; then
    echo "SUCCESS: Wasp installed! Version: $(wasp --version)"
    echo "Initialize project with:"
    echo "  mkdir wasp-core && cd wasp-core"
    echo "  wasp new ."
    echo "  wasp start"
else
    echo "FAILED: Wasp still not installed"
    echo "Try manual installation:"
    echo "  npm install -g wasp@latest"
    echo "Or see documentation: https://wasp-lang.dev/docs"
fi