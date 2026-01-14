# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Floripa Square Moments backend - a FastAPI application for event photo management with AWS Rekognition facial recognition search. Users can upload photos to events and search for photos containing their face.

## Commands

### Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
uvicorn app.main:app --reload --port 8080

# Run with multiple workers (production-like)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --workers 2
```

### Database Migrations (Alembic)
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade one revision
alembic downgrade -1
```

### Docker
```bash
# Build and run with docker-compose (includes Traefik reverse proxy)
docker-compose up --build

# Build image only
docker build -t moments-backend .
```

### Testing
```bash
pytest
```

## Architecture

### Layer Structure
- **app/routes/**: FastAPI route handlers - thin layer that delegates to services
- **app/services/**: Business logic and external service integrations (S3, Rekognition, DB)
- **app/schemas/**: Pydantic models and SQLAlchemy table definitions (combined in same files)
- **app/security/**: JWT authentication and role-based authorization

### Database
- Async PostgreSQL via SQLAlchemy + asyncpg
- Connection management in `app/services/db.py` - use `get_conn` dependency for database sessions
- Table definitions are in `app/schemas/*.py` alongside Pydantic models
- Metadata is centralized in `app/schemas/base.py`

### Authentication
- JWT tokens with role-based access control
- Three roles: `USER`, `ADMIN`, `PHOTOGRAPHER`
- Use dependency functions from `app/security/jwt.py`:
  - `require_admin` - admin only
  - `require_photographer` - photographer only
  - `require_user` - regular user only
  - `require_any_user` - any authenticated user
- Basic auth for admin endpoints via `app/security/auth.py`

### AWS Services
- **S3** (`app/services/s3.py`): Photo storage with presigned URLs
- **Rekognition** (`app/services/rekognition.py`): Face indexing and search
  - Collections are created per event with prefix `evt-{event_slug}`
  - Photos are indexed with their UUID as ExternalImageId

### Key Data Flow
1. Photo upload: Route receives file -> validates -> uploads to S3 -> indexes faces in Rekognition -> stores metadata in DB
2. Face search: Route receives selfie -> calls Rekognition search -> maps ExternalImageIds to photo records -> returns presigned URLs

## Environment Variables

Required in `.env`:
- `DATABASE_URL` - PostgreSQL connection string (use asyncpg driver: `postgresql+asyncpg://...`)
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `S3_BUCKET_RAW` - S3 bucket for photo storage
- `SECRET_KEY` - JWT signing key
- `BASIC_ADMIN_USER`, `BASIC_ADMIN_PASS` - Basic auth credentials

## Code Patterns

### Async Operations
CPU-intensive operations (bcrypt, Rekognition calls) run in ThreadPoolExecutor to avoid blocking:
```python
loop = asyncio.get_running_loop()
result = await loop.run_in_executor(executor, blocking_function, args)
```

### Adding New Routes
1. Create route file in `app/routes/`
2. Register router in `app/main.py` (either on `api_router` or directly on `app`)
3. Use appropriate auth dependency for protected endpoints
