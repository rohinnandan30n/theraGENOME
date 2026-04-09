# TheraGenome Authentication System

## Overview

This document describes the authentication system for TheraGenome that differentiates between **Patient** and **Doctor** user roles.

---

## System Architecture

### User Roles

1. **Patient Role**
   - Can login with email and password
   - Access: Patient-only view of medical reports
   - Restrictions: Cannot see clinical analysis or doctor-specific features

2. **Doctor Role**
   - Must register with professional credentials
   - Email verification: Medical institution domain required
   - License verification: Medical license number required
   - Access: Full access including clinical analysis and advanced features
   - Specialization field: For professional categorization

### Authentication Flow

```
User Login/Registration
         ↓
Input Credentials (email, password, and role-specific details)
         ↓
Backend Validation (email domain, license number, format checks)
         ↓
Password Hashing (PBKDF2-SHA256 with salt)
         ↓
User Creation in Database
         ↓
Session Token Generation
         ↓
Cookie-based Session Storage
         ↓
Redirect to App with User Role
```

---

## Component Details

### 1. Frontend - Login Page (`frontend/login.html`)

**Features:**
- Responsive design with branding section
- Two modes: Patient Login and Doctor Registration
- Real-time form validation
- Error handling and success messages
- Loading states for async operations

**Patient Login Form:**
```
- Email Address (required)
- Password (required)
```

**Doctor Registration Form:**
```
- Hospital/Medical Email (required, medical domain verification)
- Medical License Number (required, minimum 5 characters)
- Specialization (dropdown with common specializations)
- Full Name (required)
- Password (required, minimum 8 characters)
- Confirm Password (required, must match)
```

**Validation Rules:**
- Email format validation
- Medical domain validation (for doctors): hospital, clinic, medical, health, etc.
- License number: Minimum 5 characters
- Password: Minimum 8 characters
- Passwords must match (doctor registration)

### 2. Backend - Authentication Module (`backend/auth.py`)

**Database Model (SQLite):**
```python
users table:
- id (String, Primary Key)
- email (String, Unique)
- password_hash (String, with salt)
- role (String: 'patient' or 'doctor')
- full_name (String, optional)
- license_number (String, optional, for doctors)
- specialization (String, optional, for doctors)
- is_verified (Boolean, default: False for doctors, True for patients)
- created_at (DateTime)
- last_login (DateTime)
```

**Key Functions:**
- `hash_password(password)` - PBKDF2-SHA256 with salt
- `verify_password(password, salt, stored_hash)` - Verify password
- `create_user(...)` - Create new user
- `authenticate_user(email, password)` - Authenticate user
- `get_user_by_email(email)` - Retrieve user

### 3. Backend - Authentication API (`backend/auth_api.py`)

**Endpoints:**

#### POST `/api/v1/auth/login`
Login as a patient.
```json
Request:
{
  "email": "patient@example.com",
  "password": "password123",
  "role": "patient"
}

Response (200 OK):
{
  "success": true,
  "message": "Login successful",
  "user": {
    "email": "patient@example.com",
    "role": "patient",
    "full_name": null
  }
}

Response (401 Unauthorized):
{
  "detail": "Invalid email or password"
}
```

#### POST `/api/v1/auth/register-doctor`
Register as a doctor.
```json
Request:
{
  "email": "doctor@hospital.com",
  "password": "securepass123",
  "full_name": "Dr. John Smith",
  "license_number": "MD-1234567",
  "specialization": "Cardiology",
  "role": "doctor"
}

Response (200 OK):
{
  "success": true,
  "message": "Doctor registration successful. Your account is pending verification.",
  "user": {
    "email": "doctor@hospital.com",
    "role": "doctor",
    "full_name": "Dr. John Smith",
    "specialization": "Cardiology",
    "is_verified": false
  }
}

Response (400 Bad Request):
{
  "detail": "Invalid medical email domain"
}
```

#### GET `/api/v1/auth/user`
Get current logged-in user information.
```json
Response (200 OK):
{
  "email": "user@example.com",
  "role": "patient|doctor",
  "full_name": "Full Name",
  "specialization": "Specialization (doctor only)",
  "is_verified": true|false
}

Response (401 Unauthorized):
{
  "detail": "Not authenticated"
}
```

#### GET `/api/v1/auth/verify-session`
Verify if current session is valid.
```json
Response (200 OK):
{
  "authenticated": true,
  "role": "patient|doctor",
  "email": "user@example.com"
}

OR

{
  "authenticated": false
}
```

#### POST `/api/v1/auth/logout`
Logout current user (clear session).
```json
Response (200 OK):
{
  "success": true,
  "message": "Logged out successfully"
}
```

### 4. Frontend - Authentication Guard

**File:** `frontend/reports.html`

**Features:**
- Checks authentication status on page load
- Redirects to login if not authenticated
- Stores user role in sessionStorage
- Provides logout functionality

**Authentication Check Flow:**
```javascript
window.load → checkAuthentication()
            → fetch /api/v1/auth/verify-session
            → if not authenticated → redirect to /login.html
            → if authenticated → store role in sessionStorage
            → initialize ReportAnalyzerUI with user role
```

---

## Session Management

**Method:** Cookie-based sessions with secure tokens

**Session Storage:** In-memory dictionary (in production, use Redis or database)

**Session Token:**
- 32-character URL-safe random token
- Stored in httpOnly cookie
- 24-hour expiration

**Cookie Settings:**
```
Name: session_token
httpOnly: true
Secure: false (set to true in production with HTTPS)
SameSite: lax
Max-Age: 86400 (24 hours)
```

---

## Security Features

1. **Password Hashing:**
   - Algorithm: PBKDF2-SHA256
   - Salt: 16-byte random hex
   - 100,000 iterations

2. **Email Validation:**
   - Medical domain verification for doctors
   - Unique email constraint in database

3. **Session Security:**
   - Secure session tokens
   - HttpOnly cookies (prevents XSS attacks)
   - Session expiration

4. **Input Validation:**
   - Email format validation
   - License number validation (minimum length)
   - Password strength requirements

---

## Database

**Location:** `theragenome.db` (SQLite, in project root)

**Initialization:** Automatic on first run via SQLAlchemy

**Tables:**
- `users` - User accounts with role and credentials

---

## Medical Domains Recognized

The system accepts medical institution emails containing:
- `hospital`
- `clinic`
- `medical`
- `health`
- `healthcare`
- `med`
- `dr`
- `doctor`
- `.edu` (universities)
- `university`

**Examples of Valid Medical Emails:**
- `doctor@hospital.com`
- `Dr@clinic.org`
- `physician@medical-center.com`
- `practitioner@healthcare.gov`
- `doctor@university.edu`

---

## Specializations Available

1. General Practice
2. Cardiology
3. Oncology
4. Neurology
5. Pathology
6. Genetics
7. Internal Medicine
8. Other

---

## Frontend User Experience

### Login Flow (Patient)
1. Click "Patient Login" tab
2. Enter email and password
3. Click "Login as Patient"
4. Redirect to `/reports.html` with patient mode enabled
5. View limited to patient-specific features

### Registration Flow (Doctor)
1. Click "Doctor Register" tab
2. Fill in hospital email (must be medical domain)
3. Enter medical license number
4. Select specialization
5. Enter full name
6. Set password (minimum 8 characters)
7. Click "Register as Doctor"
8. Redirect to `/reports.html` with doctor mode enabled
9. Account marked as pending verification (admin approval required)

### Logout
1. Click "Logout" button in header
2. Session cleared
3. Redirect to `/login.html`

---

## Integration with Report Analyzer

**Patient Mode:**
- ✓ Upload reports
- ✓ Paste text analysis
- ✓ View summary
- ✓ View test results
- ✗ No clinical analysis tab
- ✗ No doctor-specific features

**Doctor Mode:**
- ✓ All patient features
- ✓ Clinical analysis tab
- ✓ Advanced organ involvement analysis
- ✓ Drug interaction assessment
- ✓ Clinical recommendations
- ✓ Full diagnostic capabilities

---

## Error Handling

**Common Errors:**

| Error | Cause | Resolution |
|-------|-------|-----------|
| "Invalid email or password" | Wrong credentials | Check email and password |
| "Email already registered" | Account exists | Login instead or use different email |
| "Invalid medical email domain" | Non-medical email (doc) | Use official institution email |
| "License number must be valid" | License too short | Enter at least 5-character license |
| "Password must be at least 8 characters" | Weak password | Use stronger password |
| "Passwords do not match" | Password fields don't match | Ensure both fields are identical |
| "Not authenticated" | Session expired/invalid | Login again |

---

## Development Notes

### Testing Credentials

**Patient Account (for testing):**
```
Email: patient@example.com
Password: password123
Role: patient
```

**Doctor Account (for testing):**
```
Email: doctor@hospital.com
Password: securepass123
Full Name: Dr. John Smith
License Number: MD-1234567
Specialization: Cardiology
Role: doctor
is_verified: pending
```

### Running the Application

**Terminal 1 - Backend:**
```bash
cd c:\Users\shiva\Desktop\Integration-theragenome2
C:/Users/shiva/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m uvicorn backend.main:app --host localhost --port 8000 --reload
```

**Terminal 2 - Frontend:**
```bash
cd c:\Users\shiva\Desktop\Integration-theragenome2\frontend
C:/Users/shiva/AppData/Local/Microsoft/WindowsApps/python3.11.exe -m http.server 8001
```

**Access Application:**
- Login Page: `http://localhost:8001/login.html`
- Report Analyzer: `http://localhost:8001/reports.html` (requires authentication)

---

## Future Enhancements

1. **Email Verification:** Send verification link to email
2. **Admin Dashboard:** Approve/reject doctor registrations
3. **Password Reset:** Forgot password functionality
4. **Two-Factor Authentication:** SMS or TOTP-based 2FA
5. **OAuth Integration:** Google, Microsoft, Apple sign-in
6. **Redis Sessions:** Replace in-memory sessions with Redis for scaling
7. **License Verification API:** Real-time license validation
8. **Audit Logging:** Track login/logout events
9. **Role-Based Access Control (RBAC):** More granular permissions
10. **Account Management:** Profile updates, password change

---

## Notes

- Database file (`theragenome.db`) is created automatically on first run
- All passwords are salted and hashed - never stored in plain text
- Session tokens are randomly generated and cryptographically secure
- Medical domain validation is case-insensitive
- Doctors are marked as pending verification - admin approval is required for full access (feature for future enhancement)
