# Docker Startup Guide

## 1. Start Docker Desktop
- Open Applications → Docker.app
- Look for the whale icon (🐳) in your status bar
- Wait until it shows "Docker Desktop is running"

## 2. Verify Installation
```bash
docker --version
docker-compose --version
docker info
```

## 3. Run Application
```bash
./run-docker.sh
```

## Troubleshooting
### If Docker won't start:
```bash
# Try manual start
open -a Docker

# Reset Docker Desktop:
1. Click whale icon → Troubleshoot → Reset to factory defaults
2. Reinstall Docker Desktop if needed
```

### If you get permission errors:
```bash
sudo ./run-docker.sh
```

## Alternative Without Docker
If Docker issues persist, we can set up a local development environment:
```bash
cd wasp-core
npm install
wasp start