# setup.sh
#!/bin/bash

echo "Setting up UI String Translator..."

# Create .env files if they don't exist
if [ ! -f ./backend/.env ]; then
  echo "Creating backend/.env file..."
  echo "GEMINI_API_KEY=" > ./backend/.env
  echo "GITHUB_TOKEN=" >> ./backend/.env
  echo "Backend .env file created. Please edit it to add your API keys."
fi

if [ ! -f ./frontend/.env ]; then
  echo "Creating frontend/.env file..."
  echo "REACT_APP_API_URL=http://localhost:8000" > ./frontend/.env
  echo "Frontend .env file created."
fi

# Start the application with Docker Compose
echo "Starting application with Docker Compose..."
docker-compose up --build

echo "Setup complete!"