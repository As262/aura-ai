#!/bin/bash

# AI Model Setup Script for Aura AI
echo "🤖 Setting up AI models and dependencies for Aura AI..."

# Create directories for models
echo "📁 Creating model directories..."
mkdir -p backend/models/pretrained
mkdir -p backend/models/weights

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt

# Download pre-trained models (optional - models will be downloaded on first use)
echo "🔄 AI models will be automatically downloaded on first use..."

# Create model configuration file
cat > models/model_config.json << EOL
{
    "models": {
        "pose_detection": {
            "name": "MediaPipe Pose",
            "type": "pose_estimation",
            "status": "ready"
        },
        "face_analysis": {
            "name": "MediaPipe Face Mesh",
            "type": "face_detection",
            "status": "ready"
        },
        "aesthetic_scoring": {
            "name": "Custom Heuristic Model",
            "type": "aesthetic_analysis",
            "status": "ready"
        }
    },
    "version": "1.0.0",
    "last_updated": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOL

echo "✅ AI setup completed!"
echo "🚀 Start the development server with: python manage.py runserver"