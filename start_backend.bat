@echo off
REM TheraGenome AI - Backend Server Startup Script

echo.
echo ================================================
echo   TheraGenome AI - Backend Server
echo ================================================
echo.

REM Set the paths
set PYTHON_PATH=C:\Users\shiva\AppData\Local\Microsoft\WindowsApps\python3.11.exe
set WORK_DIR=c:\Users\shiva\Desktop\Integration-theragenome2

REM Change to working directory
cd /d %WORK_DIR%

echo Starting backend server...
echo.
echo Backend will be available at: http://localhost:8000
echo Dashboard at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
%PYTHON_PATH% backend/main.py

pause
