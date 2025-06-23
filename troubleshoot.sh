#!/bin/bash

# Navigate to project directory
cd "$(dirname "$0")"

# Check container status
echo "=== Container Status ==="
docker-compose ps

# Verify port mapping
echo "\n=== Port Mapping ==="
docker-compose port concierge-app 3000

# Check application logs
echo "\n=== Application Logs ==="
docker-compose logs concierge-app

# Test internal container access
CONTAINER_ID=$(docker-compose ps -q concierge-app)
if [ -n "$CONTAINER_ID" ]; then
  echo "\n=== Container Access Test ==="
  docker exec -it $CONTAINER_ID curl -I http://localhost:3000
fi