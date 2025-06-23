#!/bin/bash

# Navigate to project directory
cd "$(dirname "$0")"

# Clean previous containers and images
docker-compose down -v --rmi all

# Build and start containers
docker-compose up --build