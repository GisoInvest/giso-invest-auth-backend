# GISO Invest Authentication Service

A Flask-based authentication API for the GISO Invest property investment platform.

## Features

- User registration and login
- Secure password hashing
- Session token management
- Cross-device authentication
- CORS support for frontend integration

## Quick Deploy

### Railway (Recommended)
1. Create account at [railway.app](https://railway.app)
2. Upload this folder or connect GitHub repo
3. Railway will auto-detect Flask and deploy
4. Your API will be available at: `https://your-app.railway.app`

### Heroku
1. Install Heroku CLI
2. `heroku create your-app-name`
3. `git push heroku main`

### Local Development
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python src/main.py
```

## Environment Variables

- `SECRET_KEY`: Flask secret key (auto-generated if not set)
- `DATABASE_URL`: Database connection string (SQLite used if not set)
- `PORT`: Server port (defaults to 5001)
- `FLASK_ENV`: Set to 'production' for production deployment

## API Endpoints

- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/auth/validate` - Session validation
- `POST /api/auth/logout` - User logout
- `GET /health` - Health check

## Database

- Development: SQLite (automatic)
- Production: PostgreSQL (set DATABASE_URL)

The database schema is automatically created on first run.

