@echo off
echo 🚀 Starting Aura AI Development Environment...

:: Check prerequisites
echo Checking prerequisites...

where python >nul 2>nul
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

where node >nul 2>nul
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 16+ first.
    pause
    exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
    echo ❌ npm is not installed. Please install npm first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

:: Setup Backend
echo.
echo Setting up Django Backend...
cd backend

:: Check if virtual environment exists
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Install Python dependencies
echo Installing Python dependencies...
pip install -r requirements.txt

:: Setup database
echo Setting up database...
python manage.py makemigrations
python manage.py migrate

:: Start Django server
echo Starting Django development server...
start "Django Server" cmd /k "python manage.py runserver"

cd ..

:: Setup Frontend
echo.
echo Setting up React Frontend...
cd frontend

:: Install Node.js dependencies
echo Installing Node.js dependencies...
call npm install

:: Start React development server
echo Starting React development server...
start "React Server" cmd /k "npm start"

cd ..

echo.
echo 🎉 Aura AI is now running!
echo Frontend: http://localhost:3000
echo Backend API: http://localhost:8000  
echo Django Admin: http://localhost:8000/admin
echo.
echo Press any key to continue...
pause >nul