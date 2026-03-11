@echo off
REM AI Model Setup Script for Aura AI (Windows)
echo 🤖 Setting up AI models and dependencies for Aura AI...

REM Create directories for models
echo 📁 Creating model directories...
if not exist "backend\models\pretrained" mkdir "backend\models\pretrained"
if not exist "backend\models\weights" mkdir "backend\models\weights"

REM Install Python dependencies
echo 📦 Installing Python dependencies...
cd backend

REM Check if virtual environment exists, if not create one
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Upgrade pip
python -m pip install --upgrade pip

REM Install requirements
pip install -r requirements.txt

REM Create model configuration file
echo 🔧 Creating model configuration...
echo { > models\model_config.json
echo   "models": { >> models\model_config.json
echo     "pose_detection": { >> models\model_config.json
echo       "name": "MediaPipe Pose", >> models\model_config.json
echo       "type": "pose_estimation", >> models\model_config.json
echo       "status": "ready" >> models\model_config.json
echo     }, >> models\model_config.json
echo     "face_analysis": { >> models\model_config.json
echo       "name": "MediaPipe Face Mesh", >> models\model_config.json
echo       "type": "face_detection", >> models\model_config.json
echo       "status": "ready" >> models\model_config.json
echo     }, >> models\model_config.json
echo     "aesthetic_scoring": { >> models\model_config.json
echo       "name": "Custom Heuristic Model", >> models\model_config.json
echo       "type": "aesthetic_analysis", >> models\model_config.json
echo       "status": "ready" >> models\model_config.json
echo     } >> models\model_config.json
echo   }, >> models\model_config.json
echo   "version": "1.0.0" >> models\model_config.json
echo } >> models\model_config.json

echo ✅ AI setup completed!
echo 🚀 Start the development server with: python manage.py runserver
echo 💡 Make sure to activate the virtual environment: venv\Scripts\activate.bat

pause