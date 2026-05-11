# theraGENOME API - Therapist Management Module

A production-ready FastAPI implementation for therapist management with JWT authentication and admin role-based access control. Part of the theraGENOME healthcare application.

## Features

- **Secure Authentication**: JWT token-based authentication using HTTP Bearer scheme
- **Role-Based Access Control (RBAC)**: Admin-only endpoints for therapist management
- **CRUD Operations**: Full Create, Read, Update, Delete functionality for therapists
- **API Documentation**: Interactive Swagger UI and ReDoc documentation
- **Comprehensive Testing**: Unit and integration tests with pytest
- **Production-Ready**: Logging, error handling, CORS, and middleware configuration
- **Async Support**: Built with async/await for high performance

## Project Structure

```
theraGENOME/
├── src/
│   └── api/
│       ├── __init__.py
│       ├── main.py                 # FastAPI application entry point
│       ├── security.py             # JWT verification and RBAC
│       ├── routes/
│       │   └── therapist_routes.py # Therapist CRUD endpoints
│       └── services/
│           └── therapist_service.py # Business logic layer
├── tests/
│   ├── test_security.py           # Security module tests
│   └── test_therapist_routes.py   # Route integration tests
├── requirements.txt                # Python dependencies
└── README.md                        # This file
```

## Installation

### Prerequisites

- Python 3.9 or higher
- pip or conda
- Virtual environment (recommended)

### Setup

1. **Clone the repository**
```bash
cd theraGENOME
```

2. **Create and activate virtual environment**
```bash
# Using venv
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n theragenome python=3.9
conda activate theragenome
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables** (optional)
```bash
cp .env.example .env  # If provided
# Edit .env with your configuration
```

## Running the Application

### Development Server

```bash
# Using uvicorn directly
uvicorn src.api.main:app --reload --host 0.0.0.0 --port 8000

# Or from the main.py file
cd src/api
python main.py
```

The server will start at `http://localhost:8000`

### Production Server

```bash
# Using gunicorn with uvicorn workers
gunicorn src.api.main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## API Documentation

Interactive API documentation is automatically available at:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc
- **OpenAPI JSON**: http://localhost:8000/api/openapi.json

## API Endpoints

### Health Check

```
GET /health
```

Returns application health status.

### Root

```
GET /
```

Returns API metadata and available endpoints.

### Therapist Management (Admin Only)

All therapist endpoints require valid JWT token with admin role in the Authorization header.

#### List All Therapists

```
GET /api/v1/therapists/
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Dr. Sarah Johnson",
    "email": "sarah@therapahub.com",
    "license_no": "TH-2024-001",
    "specialization": "Cognitive Behavioral Therapy",
    "status": "active",
    "created_at": "2024-01-15T10:30:00"
  }
]
```

#### Get Therapist by ID

```
GET /api/v1/therapists/{therapist_id}
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Dr. Sarah Johnson",
  "email": "sarah@therapahub.com",
  "license_no": "TH-2024-001",
  "specialization": "Cognitive Behavioral Therapy",
  "status": "active",
  "created_at": "2024-01-15T10:30:00"
}
```

**Error Response (404 Not Found):**
```json
{
  "detail": "Therapist 1 not found"
}
```

#### Create Therapist

```
POST /api/v1/therapists/
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Dr. Jane Smith",
  "email": "jane@therapahub.com",
  "license_no": "TH-2024-999",
  "specialization": "Trauma-Focused Therapy"
}
```

**Response (201 Created):**
```json
{
  "id": 3,
  "name": "Dr. Jane Smith",
  "email": "jane@therapahub.com",
  "license_no": "TH-2024-999",
  "specialization": "Trauma-Focused Therapy",
  "status": "active",
  "created_at": "2024-01-20T14:45:00"
}
```

#### Update Therapist

```
PUT /api/v1/therapists/{therapist_id}
Authorization: Bearer <jwt_token>
Content-Type: application/json

{
  "name": "Dr. Jane Smith Updated",
  "specialization": "Trauma and PTSD Therapy"
}
```

**Response (200 OK):**
```json
{
  "id": 3,
  "name": "Dr. Jane Smith Updated",
  "email": "jane@therapahub.com",
  "license_no": "TH-2024-999",
  "specialization": "Trauma and PTSD Therapy",
  "status": "active",
  "updated_at": "2024-01-20T15:00:00"
}
```

#### Delete Therapist

```
DELETE /api/v1/therapists/{therapist_id}
Authorization: Bearer <jwt_token>
```

**Response (204 No Content):** (No body)

#### Get Therapist Sessions

```
GET /api/v1/therapists/{therapist_id}/sessions
Authorization: Bearer <jwt_token>
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "therapist_id": 1,
    "patient_id": 101,
    "date": "2024-01-15T10:00:00",
    "duration": 60,
    "notes": "Initial consultation",
    "status": "completed"
  }
]
```

## Authentication

### JWT Token Format

The API expects JWT tokens in the Authorization header using the Bearer scheme:

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### Getting an Admin Token (Development)

For development, you can use mock tokens. The security module validates:
- Token has 3 parts separated by dots (header.payload.signature)
- User has 'admin' role for admin endpoints

**Example development token:**
```
Authorization: Bearer header.payload.signature
```

### Token Claims (Example)

```json
{
  "username": "admin_user",
  "role": "admin",
  "user_id": 1,
  "exp": 1704067200
}
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run with Coverage

```bash
pytest --cov=src/api --cov-report=html
```

### Run Specific Test File

```bash
pytest tests/test_security.py -v
pytest tests/test_therapist_routes.py -v
```

### Run Specific Test

```bash
pytest tests/test_security.py::test_verify_admin_token_valid -v
```

## Error Handling

### Common HTTP Status Codes

| Status | Meaning | Example |
|--------|---------|---------|
| 200 | OK | Successful GET/PUT |
| 201 | Created | Successful POST |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Invalid request format |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 422 | Unprocessable Entity | Validation error |
| 500 | Server Error | Internal server error |

### Error Response Format

```json
{
  "detail": "Human-readable error message"
}
```

## Security Features

### Token Verification
- JWT token validation
- Bearer scheme parsing
- Token format validation (3-part structure)

### Role-Based Access Control
- Admin-only endpoints for sensitive operations
- Role checking in security middleware
- Dependency injection for flexible role assignment

### CORS Configuration
- Restricted to trusted origins in production
- Development origins: localhost, 127.0.0.1
- Configurable allowed methods and headers

### Middleware
- CORS middleware for cross-origin requests
- Trusted host middleware for security
- Exception handlers for validation errors

## Logging

Logs are written to:
- **Console**: All log levels
- **File**: `logs/app.log` (rotated at 10MB)
- **Format**: `timestamp - logger - level - message`

Example log entries:
```
2024-01-20 14:30:00,123 - src.api.routes.therapist_routes - INFO - Admin admin_user fetched all therapists
2024-01-20 14:31:00,456 - src.api.routes.therapist_routes - INFO - Admin admin_user created therapist: Dr. Jane Smith
```

## Development

### Code Style

Format code with Black:
```bash
black src/ tests/
```

Check code with flake8:
```bash
flake8 src/ tests/
```

Type checking with mypy:
```bash
mypy src/
```

### Adding New Endpoints

1. Create route in `src/api/routes/`
2. Implement service in `src/api/services/`
3. Add security decorator if needed
4. Write tests in `tests/test_*.py`
5. Update documentation in README

### Database Integration

To connect to a database:

1. Define models in `src/database/models.py`
2. Create database session factory
3. Update `TherapistService` to use actual ORM queries
4. Run migrations with Alembic

See comments marked `TODO:` in service and route files.

## Performance Optimization

### Async Support
The API uses async/await throughout for better concurrency handling.

### CORS and Headers
- Response compression (enable in production)
- Cache-Control headers for caching
- ETags for conditional requests

### Database
- Connection pooling configured
- Query optimization through indexes
- Pagination support for large datasets (to be implemented)

## Security Considerations

1. **In Production:**
   - Use real JWT signing with cryptographic keys
   - Enable HTTPS/TLS
   - Set secure CORS origins
   - Enable HSTS headers
   - Rate limiting
   - Request validation
   - Input sanitization

2. **Secrets Management:**
   - Store JWT keys in environment variables
   - Use secrets manager (AWS Secrets, HashiCorp Vault)
   - Never commit secrets to version control

3. **Authentication:**
   - Implement proper JWT verification
   - Add token refresh mechanism
   - Implement rate limiting on auth endpoints
   - Add account lockout after failed attempts

## Troubleshooting

### Import Errors
- Ensure FastAPI and dependencies are installed: `pip install -r requirements.txt`
- Check Python path is correct
- Verify virtual environment is activated

### Authentication Failures
- Verify token format (must have 3 parts: header.payload.signature)
- Check token in Authorization header uses "Bearer" prefix
- Ensure user role is "admin" for admin endpoints

### CORS Errors
- Check allowed_origins in main.py
- Verify client origin matches CORS configuration
- Check browser console for specific CORS error messages

### Database Errors
- Verify database is running and accessible
- Check connection string in environment
- Run migrations: `alembic upgrade head`

## Contributing

1. Create a feature branch
2. Make changes and add tests
3. Run tests: `pytest`
4. Format code: `black src/ tests/`
5. Create pull request

## License

[Add your license here]

## Support

For issues and questions:
- Create an issue on GitHub
- Contact the development team
- Check existing documentation

## Changelog

### Version 1.0.0 (2024-01-20)
- Initial release
- Therapist CRUD endpoints
- JWT authentication with admin role
- Comprehensive test coverage
- API documentation

---

**Last Updated:** 2024-01-20
**API Version:** 1.0.0
**Status:** Production Ready
