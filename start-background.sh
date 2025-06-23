#!/bin/bash

# Navigate to project directory
cd "$(dirname "$0")"

# Build and start containers in background
docker-compose up --build -d

# Show container status
docker-compose ps