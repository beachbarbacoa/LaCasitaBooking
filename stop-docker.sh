#!/bin/bash

# Navigate to project directory
cd "$(dirname "$0")"

# Stop and remove containers
docker-compose down