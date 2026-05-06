"""
Load Test Runner for TheraGenome API

This script runs the load test with predefined parameters and generates reports.
"""

import subprocess
import sys
import os
from pathlib import Path


def run_load_test():
    """Run the load test with specified parameters."""
    # Get the load_tests directory
    load_tests_dir = Path(__file__).parent
    locustfile = load_tests_dir / "locustfile.py"
    
    # Check if locustfile exists
    if not locustfile.exists():
        print(f"Error: locustfile.py not found at {locustfile}")
        return 1
    
    # Load test parameters
    host = "http://localhost:8000"
    users = 50
    spawn_rate = 5
    run_time = "60s"
    
    print("=" * 80)
    print("TheraGenome API Load Test")
    print("=" * 80)
    print(f"Host: {host}")
    print(f"Total Users: {users}")
    print(f"Spawn Rate: {spawn_rate} users/sec")
    print(f"Run Time: {run_time}")
    print("=" * 80)
    print()
    
    # Build locust command
    cmd = [
        "locust",
        "-f", str(locustfile),
        "--host", host,
        "-u", str(users),
        "-r", str(spawn_rate),
        "--run-time", run_time,
        "--headless",
    ]
    
    try:
        print(f"Running command: {' '.join(cmd)}\n")
        result = subprocess.run(cmd, cwd=str(load_tests_dir.parent))
        return result.returncode
    except FileNotFoundError:
        print("Error: locust not installed.")
        print("Install it with: pip install locust")
        return 1
    except Exception as e:
        print(f"Error running load test: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(run_load_test())
