# 🌟 Aura AI - Aesthetic Analysis & Conversation Decoding Platform

A full-stack application that combines React frontend with Django backend to provide AI-powered aesthetic analysis and conversation decoding services.

## 🚀 Features

### 📸 Aesthetic Analyzer
- Upload Instagram posts for aesthetic analysis
- Get aesthetic scores and visual style insights
- Platform-specific recommendations
- Color palette analysis
- Mood and vibe detection

### 💬 Conversation Decoder
- Analyze chat logs and conversation patterns
- Understand communication styles
- Response timing analysis
- Mood and personality insights
- Relationship dynamics assessment

## 🛠️ Tech Stack

### Frontend
- **React 19.1.1** - Modern UI framework
- **React Router** - Client-side routing
- **CSS3** - Styling with custom properties
- **React Context** - State management

### Backend
- **Django 4.2+** - Python web framework
- **Django REST Framework** - API development
- **SQLite** - Development database
- **CORS Headers** - Cross-origin requests
- **Pillow** - Image processing

## 📁 Project Structure

```
aura-ai/
├── frontend/                 # React application
│   ├── public/              # Static assets
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── contexts/        # React context providers
│   │   ├── pages/           # Page components
│   │   ├── services/        # API services
│   │   ├── styles/          # Global styles
│   │   └── utils/           # Utility functions
│   └── package.json
├── backend/                 # Django application
│   ├── aura_ai/            # Django project settings
│   ├── api/                # Main API application
│   ├── manage.py
│   ├── requirements.txt
│   └── README.md
├── start-dev.bat           # Windows development script
├── start-dev.sh            # Unix development script
└── package.json            # Root package.json
```

## 🚀 Quick Start

### Option 1: Automated Setup (Windows)
```bash
# Run the automated setup script
start-dev.bat
```

### Option 2: Automated Setup (macOS/Linux)
```bash
# Make script executable and run
chmod +x start-dev.sh
./start-dev.sh
```

### Option 3: Manual Setup

#### Prerequisites
- Python 3.8+
- Node.js 16+
- npm or yarn

#### Backend Setup
```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
python manage.py makemigrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser

# Start Django server
python manage.py runserver
```

#### Frontend Setup
```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start React development server
npm start
```

## 🌐 Access Points

Once both servers are running:

- **Frontend Application**: http://localhost:3000
- **Backend API**: http://localhost:8000/api
- **Django Admin Panel**: http://localhost:8000/admin

## 🔗 API Integration

The frontend automatically detects backend availability:
- ✅ **Connected Mode**: Uses Django backend API for real analysis
- 🔄 **Demo Mode**: Falls back to mock data when backend is unavailable

### Connection Status
A connection indicator in the top-right corner shows:
- 🟢 **Backend Connected**: Full functionality available
- 🔴 **Demo Mode**: Using mock data for demonstration

## 📡 API Endpoints

### Health & Status
- `GET /api/health/` - Backend health check

### Authentication
- `POST /api/register/` - User registration
- `POST /api/login/` - User login
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update user profile

### Analysis Services
- `POST /api/aesthetic-analysis/` - Analyze image aesthetics
- `POST /api/conversation-analysis/` - Analyze conversation patterns

## 🎨 Frontend Features

### Design System
- Responsive design for all screen sizes
- Dark/Light theme support
- Custom CSS properties for consistent styling
- Accessible components with ARIA labels

### User Experience
- File drag & drop support
- Real-time analysis feedback
- Error boundaries for graceful error handling
- Toast notifications for user feedback
- Loading states and progress indicators

### Performance
- Lazy loading for non-critical components
- Memoized components to prevent unnecessary re-renders
- Optimized bundle size with code splitting

## 🔧 Development

### Available Scripts

#### Root Level
```bash
npm run dev          # Start both frontend and backend
npm run setup        # Setup both applications
npm run build        # Build frontend for production
npm run test         # Run all tests
```

#### Frontend
```bash
npm start            # Start development server
npm run build        # Build for production
npm test             # Run tests
npm run eject        # Eject from Create React App
```

#### Backend
```bash
python manage.py runserver      # Start development server
python manage.py test           # Run tests
python manage.py makemigrations # Create database migrations
python manage.py migrate        # Apply migrations
python manage.py shell          # Django shell
```

## 🧪 Testing

### Frontend Testing
```bash
cd frontend
npm test
```

### Backend Testing
```bash
cd backend
python manage.py test
```

## 🏗️ Production Deployment

### Frontend
```bash
cd frontend
npm run build
# Deploy the 'build' folder to your static hosting service
```

### Backend
1. Set up production database (PostgreSQL recommended)
2. Configure environment variables
3. Set `DEBUG=False` in settings
4. Configure static file serving
5. Use a production WSGI server (Gunicorn)

### Environment Variables

#### Frontend (.env)
```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_API_TIMEOUT=30000
```

#### Backend (.env)
```env
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com
DATABASE_URL=postgres://user:password@localhost:5432/aura_ai
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- React team for the amazing frontend framework
- Django team for the robust backend framework
- All contributors and testers

## 📞 Support

If you encounter any issues:

1. Check the connection status indicator
2. Ensure both servers are running
3. Check console logs for errors
4. Refer to individual README files in frontend/ and backend/ directories

---

**Happy Analyzing! 🌟**