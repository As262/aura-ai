# Aura AI Backend

A Django REST API backend for the Aura AI application providing aesthetic analysis and conversation decoding services.

## Features

- User authentication and profiles
- Aesthetic image analysis API
- Conversation analysis API
- RESTful API endpoints
- CORS support for frontend integration
- Admin interface for data management

## Setup Instructions

### Prerequisites
- Python 3.8+
- pip (Python package manager)

### Installation

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment:**
   - Windows:
     ```bash
     venv\Scripts\activate
     ```
   - macOS/Linux:
     ```bash
     source venv/bin/activate
     ```

4. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

5. **Set up environment variables:**
   ```bash
   copy .env.example .env
   ```
   Edit the `.env` file with your configuration.

6. **Run database migrations:**
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

7. **Create a superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

8. **Start the development server:**
   ```bash
   python manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## API Endpoints

### Health Check
- `GET /api/health/` - Check if the API is running

### Authentication
- `POST /api/register/` - Register a new user
- `POST /api/login/` - User login

### User Profile
- `GET /api/profile/` - Get user profile
- `PUT /api/profile/` - Update user profile

### Aesthetic Analysis
- `POST /api/aesthetic-analysis/` - Analyze an image for aesthetic properties

### Conversation Analysis
- `POST /api/conversation-analysis/` - Analyze conversation text

## Project Structure

```
backend/
├── aura_ai/           # Django project settings
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/               # Main API application
│   ├── migrations/
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── models.py
│   ├── serializers.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Development

### Running Tests
```bash
python manage.py test
```

### Creating New Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Accessing Admin Interface
Visit `http://localhost:8000/admin/` and login with your superuser credentials.

## Technologies Used

- Django 4.2+
- Django REST Framework
- django-cors-headers
- python-decouple
- Pillow (for image handling)

## Next Steps

1. Implement actual AI/ML models for aesthetic and conversation analysis
2. Add user authentication with JWT tokens
3. Implement file upload validation and security
4. Add rate limiting and API throttling
5. Set up production database (PostgreSQL)
6. Add comprehensive error handling and logging
7. Implement caching for improved performance