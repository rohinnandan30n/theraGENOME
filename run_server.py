#!/usr/bin/env python
"""
TheraGenome Complete Server - Runs both main app + API server
All endpoints available on port 8000
"""

import uvicorn
import sys

if __name__ == "__main__":
    print("=" * 70)
    print("Starting TheraGenome Complete Server")
    print("=" * 70)
    print()
    print("✓ Authentication endpoints:  /api/v1/auth/*")
    print("✓ Chatbot endpoints:         /api/v1/chatbot/*")
    print("✓ Analysis endpoints:        /api/v1/classify")
    print("✓ Report endpoints:          /api/v1/report/*")
    print("✓ Health check:              /health")
    print()
    print("Frontend: http://localhost:3000")
    print("Backend:  http://localhost:8000")
    print("=" * 70)
    print()
    
    # Run the API server (which has all endpoints)
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
