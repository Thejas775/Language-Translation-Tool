#!/bin/bash

# Make script exit on error
set -e

echo "Setting up UI String Translator & GitHub Integrator..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit the .env file and add your API keys."
else
    echo ".env file already exists."
fi

# Build and start the containers
echo "Building and starting Docker containers..."
docker-compose up -d --build

echo ""
echo "Setup complete! The application is running at http://localhost:8501"
echo "To stop the application, run: docker-compose down"