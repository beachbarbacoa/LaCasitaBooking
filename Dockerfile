FROM node:20-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl

# Install Wasp
RUN curl -sSL https://get.wasp-lang.dev/installer.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# Verify installation
RUN wasp version

# Create app directory
WORKDIR /app

# Copy project files
COPY wasp-core/ .

# Start app
CMD ["wasp", "start"]