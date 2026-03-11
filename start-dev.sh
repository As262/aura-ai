#!/bin/bash

# Aura AI Development Setup Script

echo "🚀 Starting Aura AI Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
echo -e "${BLUE}Checking prerequisites...${NC}"

if ! command_exists python; then
    echo -e "${RED}❌ Python is not installed. Please install Python 3.8+ first.${NC}"
    exit 1
fi

if ! command_exists node; then
    echo -e "${RED}❌ Node.js is not installed. Please install Node.js 16+ first.${NC}"
    exit 1
fi

if ! command_exists npm; then
    echo -e "${RED}❌ npm is not installed. Please install npm first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Prerequisites check passed${NC}"

# Setup Backend
echo -e "\n${BLUE}Setting up Django Backend...${NC}"
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install Python dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
pip install -r requirements.txt

# Setup database
echo -e "${YELLOW}Setting up database...${NC}"
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
read -p "Do you want to create a Django superuser? (y/n): " create_superuser
if [ "$create_superuser" = "y" ] || [ "$create_superuser" = "Y" ]; then
    python manage.py createsuperuser
fi

# Start Django server in background
echo -e "${YELLOW}Starting Django development server...${NC}"
python manage.py runserver &
DJANGO_PID=$!

cd ..

# Setup Frontend
echo -e "\n${BLUE}Setting up React Frontend...${NC}"
cd frontend

# Install Node.js dependencies
echo -e "${YELLOW}Installing Node.js dependencies...${NC}"
npm install

# Start React development server
echo -e "${YELLOW}Starting React development server...${NC}"
npm start &
REACT_PID=$!

cd ..

echo -e "\n${GREEN}🎉 Aura AI is now running!${NC}"
echo -e "${GREEN}Frontend: http://localhost:3000${NC}"
echo -e "${GREEN}Backend API: http://localhost:8000${NC}"
echo -e "${GREEN}Django Admin: http://localhost:8000/admin${NC}"

echo -e "\n${YELLOW}Press Ctrl+C to stop both servers${NC}"

# Function to cleanup background processes
cleanup() {
    echo -e "\n${YELLOW}Stopping servers...${NC}"
    kill $DJANGO_PID 2>/dev/null
    kill $REACT_PID 2>/dev/null
    echo -e "${GREEN}✅ Servers stopped${NC}"
    exit 0
}

# Set trap to cleanup on script exit
trap cleanup SIGINT SIGTERM

# Wait for background processes
wait