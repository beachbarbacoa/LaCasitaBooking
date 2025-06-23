# Environment Setup Guide

## Node.js Installation (macOS)

### Method 1: Official Installer (Recommended)
1. Go to [Node.js official download page](https://nodejs.org/)
2. Download the **LTS version** (marked "Recommended For Most Users")
3. Open the downloaded `.pkg` file
4. Follow the installation wizard steps
5. Verify installation in Terminal:
   ```bash
   node -v
   # Should show version v18.x or higher
   npm -v
   # Should show version 9.x or higher
   ```

### Method 2: Using Homebrew
1. Install Homebrew if not already installed:
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```
2. Install Node.js:
   ```bash
   brew install node
   ```
3. Verify installation as above

---

## Wasp Installation
Once Node.js is installed:
```bash
npm install -g wasp
```

Verify installation:
```bash
wasp --version
# Should show version 0.11.x or higher
```

---

## Project Initialization
1. Create project directory:
   ```bash
   mkdir wasp-core && cd wasp-core
   ```
2. Initialize Wasp project:
   ```bash
   wasp new .
   ```
3. Start development server:
   ```bash
   wasp start
   ```

---

## Troubleshooting

### Node.js not found after installation
Add Node.js to your PATH:
```bash
echo 'export PATH="/usr/local/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc
```

### Permission Errors
Fix npm permissions:
```bash
mkdir ~/.npm-global
npm config set prefix '~/.npm-global'
echo 'export PATH=~/.npm-global/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```

### Wasp Command Not Found
Link Wasp manually:
```bash
npm link wasp
```

---

## Next Steps
After successful setup, proceed with:
1. Building concierge features
2. Implementing QR code system
3. Developing mobile PWAs