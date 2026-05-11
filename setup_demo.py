#!/usr/bin/env python3
"""
TheraGENOME AI — Demo Setup & Launch Script
============================================
Quick setup and testing for the demo control panel.
"""

import subprocess
import sys
import time
import os
from pathlib import Path


def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70 + "\n")


def print_step(number, text):
    """Print a numbered step."""
    print(f"  [{number}] {text}")


def print_success(text):
    """Print success message."""
    print(f"  ✓ {text}")


def print_warning(text):
    """Print warning message."""
    print(f"  ⚠ {text}")


def print_error(text):
    """Print error message."""
    print(f"  ✗ {text}")


def check_requirements():
    """Check if all requirements are met."""
    print_header("Checking Prerequisites")

    # Check Python version
    print_step(1, "Checking Python version...")
    if sys.version_info >= (3, 10):
        print_success(f"Python {sys.version_info.major}.{sys.version_info.minor}")
    else:
        print_error(
            f"Python 3.10+ required (found {sys.version_info.major}.{sys.version_info.minor})"
        )
        return False

    # Check FastAPI
    print_step(2, "Checking FastAPI...")
    try:
        import fastapi
        print_success(f"FastAPI {fastapi.__version__}")
    except ImportError:
        print_warning("FastAPI not installed. Install with: pip install fastapi uvicorn")
        return False

    # Check files exist
    print_step(3, "Checking file structure...")
    files = [
        "frontend/index.html",
        "frontend/assets/css/styles.css",
        "frontend/assets/js/app.js",
        "backend/main.py",
        "backend/chatbot/demo.py",
        "backend/chatbot/demo_api.py",
    ]

    all_exist = True
    for file in files:
        if Path(file).exists():
            print_success(f"{file}")
        else:
            print_error(f"{file} not found")
            all_exist = False

    return all_exist


def start_backend():
    """Start the FastAPI backend server."""
    print_header("Starting Backend Server")

    print_step(1, "Launching FastAPI backend on port 8000...")
    print_warning("This will run in the foreground. Open another terminal for the frontend.")
    print()

    try:
        subprocess.run(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "backend.main:app",
                "--reload",
                "--port",
                "8000",
            ],
            cwd=os.getcwd(),
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("  Backend stopped")
        print("=" * 70)


def start_frontend():
    """Start a local HTTP server for the frontend."""
    print_header("Starting Frontend Server")

    print_step(1, "Launching HTTP server on port 8001...")
    print("  ℹ Frontend will be available at: http://localhost:8001")
    print()

    try:
        os.chdir("frontend")
        subprocess.run(
            [sys.executable, "-m", "http.server", "8001"],
            cwd=os.getcwd(),
        )
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("  Frontend stopped")
        print("=" * 70)
    finally:
        os.chdir("..")


def test_api():
    """Test the demo API."""
    print_header("Testing Demo API")

    try:
        import requests
    except ImportError:
        print_warning("requests library not installed. Skipping API test.")
        return False

    print_step(1, "Waiting for backend to start...")
    time.sleep(2)

    endpoints = [
        ("Health Check", "GET", "http://localhost:8000/health"),
        ("Demo Info", "GET", "http://localhost:8000/api/demo/info"),
        ("Available Cases", "GET", "http://localhost:8000/api/demo/cases"),
    ]

    all_ok = True
    for name, method, url in endpoints:
        try:
            if method == "GET":
                response = requests.get(url, timeout=5)
            else:
                response = requests.post(url, timeout=5)

            if response.status_code == 200:
                print_success(f"{name}: {response.status_code}")
            else:
                print_error(f"{name}: {response.status_code}")
                all_ok = False
        except Exception as e:
            print_error(f"{name}: {str(e)}")
            all_ok = False

    return all_ok


def main():
    """Main setup flow."""
    print_header("TheraGENOME AI — Demo Control Panel Setup")

    # Check requirements
    if not check_requirements():
        print_header("Setup Failed")
        print_error("Please install missing dependencies and try again.")
        sys.exit(1)

    print_success("All prerequisites met!")

    # Menu
    print_header("What would you like to do?")
    print("  [1] Run backend server (on port 8000)")
    print("  [2] Run frontend server (on port 8001)")
    print("  [3] Run both servers (in separate processes)")
    print("  [4] Test API endpoints only")
    print("  [5] Exit")
    print()

    choice = input("Enter your choice [1-5]: ").strip()

    if choice == "1":
        start_backend()
    elif choice == "2":
        start_frontend()
    elif choice == "3":
        print_header("Running Both Servers")
        print_warning(
            "Note: This will run backend in foreground.\n"
            "Open another terminal to run: python setup.py (and select option 2)"
        )
        start_backend()
    elif choice == "4":
        test_api()
    elif choice == "5":
        print("Goodbye!")
        sys.exit(0)
    else:
        print_error("Invalid choice")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("  Interrupted by user")
        print("=" * 70)
        sys.exit(0)
