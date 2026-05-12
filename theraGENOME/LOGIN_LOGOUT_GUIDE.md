LOGIN/LOGOUT TROUBLESHOOTING GUIDE
================================================================================

ISSUE FIXED
-----------
After logging out, users could not login again. The issue was that the backend
session was not being properly cleared when logging out.

ROOT CAUSE
----------
In backend/auth_api.py, the logout endpoint only deleted the browser cookie but
did not remove the session from the server-side sessions dictionary. This caused:
1. Session token remained in memory on server
2. Login validation may have failed due to stale session state
3. Users were blocked from logging in again

SOLUTION APPLIED
-----------------
Updated the /logout endpoint to:
1. Accept the session token from the cookie
2. Delete the session from the server-side sessions dictionary
3. Delete the cookie from the client
4. Respond with success message

Before:
    @auth_router.post("/logout")
    async def logout(response: Response):
        response.delete_cookie("session_token")
        return {"success": True}

After:
    @auth_router.post("/logout")
    async def logout(response: Response, session_token: Optional[str] = Cookie(None)):
        if session_token and session_token in sessions:
            del sessions[session_token]
        response.delete_cookie("session_token")
        return {"success": True}


TEST CREDENTIALS
================================================================================

The following demo users have been created for testing:

PATIENTS:
  Email:    patient@demo.com
  Password: password123
  Name:     John Doe

  Email:    patient2@demo.com
  Password: password123
  Name:     Jane Smith

DOCTORS:
  Email:    doctor@hospital.com
  Password: password123
  Name:     Dr. Sarah Johnson
  License:  MD123456

  Email:    doctor2@hospital.com
  Password: password123
  Name:     Dr. Michael Chen
  License:  MD654321


HOW TO TEST LOGIN/LOGOUT
================================================================================

1. START SERVERS:
   Terminal 1 - Backend:
   $ cd "c:\Users\Rohin Nandan\OneDrive\Desktop\Frontend -integration\theraGENOME"
   $ python -m backend.main

   Terminal 2 - Frontend:
   $ python -m http.server 3000 --directory frontend/

2. NAVIGATE TO APPLICATION:
   http://localhost:3000/index.html

3. LOGIN TEST SEQUENCE:
   a) Click "Patient Login" tab
   b) Enter: patient@demo.com / password123
   c) Click "Login"
   d) Should redirect to /reports.html
   e) Verify reports page loads successfully

4. LOGOUT TEST:
   a) On reports.html page, click "Logout" button (red button in top-right)
   b) Should redirect to /login.html with cleared session

5. RE-LOGIN TEST (THE CRITICAL FIX):
   a) On login page, enter same credentials
   b) Should login successfully (no errors)
   c) Should redirect to /reports.html again

6. MULTIPLE SESSIONS TEST:
   a) Open another browser tab with login page
   b) Login with different user (patient2@demo.com)
   c) Both tabs should maintain separate sessions
   d) Logout in one tab should not affect the other


TECHNICAL DETAILS
================================================================================

Session Management Flow:
  1. Login Request
     ↓
  2. Backend authenticates user
     ↓
  3. Backend generates session token
     ↓
  4. Backend stores: sessions[token] = {"user_id": ..., "email": ..., "role": ...}
     ↓
  5. Backend sets httpOnly cookie: session_token = token
     ↓
  6. Frontend receives response, stores in sessionStorage
     ↓
  7. Frontend redirects to /reports.html

  Session Verification:
     ↓
  Browser sends cookie with request (httpOnly, automatic)
     ↓
  Backend checks: if session_token in sessions
     ↓
  If valid, return user data
     ↓
  If invalid, return 401 Unauthorized

  Logout:
     ↓
  Backend deletes: del sessions[token]  ← THE FIX
     ↓
  Backend deletes cookie: response.delete_cookie("session_token")
     ↓
  Frontend clears: sessionStorage.clear()
     ↓
  Frontend redirects to /login.html


DEBUGGING TIPS
================================================================================

1. CHECK BACKEND LOGS:
   Look for login/logout messages in the backend terminal

2. CHECK BROWSER CONSOLE:
   - Right-click → Inspect → Console tab
   - Look for any JavaScript errors
   - Check Network tab to see HTTP requests/responses

3. VERIFY COOKIES:
   - Right-click → Inspect → Application tab
   - Find "Cookies" → http://localhost:3000
   - Should see "session_token" after login
   - Should be gone after logout

4. VERIFY SESSION STORAGE:
   - Right-click → Inspect → Application tab
   - Find "Session Storage" → http://localhost:3000
   - Should have: userRole = "patient", userEmail = "patient@demo.com"
   - Should be empty after logout

5. TEST API ENDPOINTS DIRECTLY:

   LOGIN:
   $ curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"patient@demo.com","password":"password123","role":"patient"}' \
     -i

   VERIFY SESSION:
   $ curl -X GET http://localhost:8000/api/v1/auth/verify-session \
     -b "session_token=YOUR_TOKEN_HERE" \
     -i

   LOGOUT:
   $ curl -X POST http://localhost:8000/api/v1/auth/logout \
     -b "session_token=YOUR_TOKEN_HERE" \
     -i


COMMON ISSUES & SOLUTIONS
================================================================================

ISSUE: "Connection error. Please try again."
  CAUSE: Backend not running or CORS misconfigured
  FIX:   1. Check backend is running on port 8000
         2. Check CORS allows http://localhost:3000
         3. Check browser console for actual error

ISSUE: "Invalid email or password"
  CAUSE: Wrong credentials or user doesn't exist
  FIX:   1. Use credentials from TEST CREDENTIALS above
         2. Run create_demo_users.py to recreate users
         3. Check database: theragenome.db

ISSUE: Can't login after logout
  CAUSE: Session not properly cleared (FIXED in this update)
  FIX:   1. Backend restarted with new logout code
         2. If still failing, restart backend: python -m backend.main

ISSUE: Stuck on login page after closing browser
  CAUSE: Browser didn't save session state properly
  FIX:   1. Clear browser cache and cookies
         2. Close all tabs and open new tab
         3. Try login again

ISSUE: Multiple tabs logout affecting each other
  CAUSE: sessionStorage is per-tab, not global (expected behavior)
  FIX:   Not a bug - this is correct security behavior
         Each tab maintains its own session


NEXT STEPS
================================================================================

1. Test the login/logout flow with the credentials provided
2. Try multiple sessions in different browser tabs
3. Verify the 3D simulator works after login
4. Test the analysis results upload functionality
5. If issues persist, check logs in backend terminal


FILES MODIFIED
================================================================================

backend/auth_api.py
  - Updated logout() function to properly clear server-side session
  - Line 283-296

create_demo_users.py (NEW)
  - Script to create demo users for testing
  - Run once to initialize test credentials


ENVIRONMENT INFO
================================================================================

Backend:     http://localhost:8000
Frontend:    http://localhost:3000
Database:    theragenome.db (SQLite)
Session:     httpOnly secure cookie + server-side dictionary
Database:    User model with password hash (PBKDF2 with salt)

