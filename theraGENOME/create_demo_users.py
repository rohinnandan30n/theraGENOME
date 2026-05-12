#!/usr/bin/env python3
"""
Create demo users for testing TheraGENOME application
Run this BEFORE starting the backend for the first time
"""

import sys
sys.path.insert(0, '.')

from backend.auth import create_user, get_user_by_email

def create_demo_users():
    """Create demo users for testing"""
    
    demo_users = [
        {
            'email': 'patient@demo.com',
            'password': 'password123',
            'role': 'patient',
            'full_name': 'John Doe'
        },
        {
            'email': 'patient2@demo.com',
            'password': 'password123',
            'role': 'patient',
            'full_name': 'Jane Smith'
        },
        {
            'email': 'doctor@hospital.com',
            'password': 'password123',
            'role': 'doctor',
            'full_name': 'Dr. Sarah Johnson',
            'license_number': 'MD123456',
            'specialization': 'Pharmacogenomics'
        },
        {
            'email': 'doctor2@hospital.com',
            'password': 'password123',
            'role': 'doctor',
            'full_name': 'Dr. Michael Chen',
            'license_number': 'MD654321',
            'specialization': 'Genetics'
        }
    ]
    
    print("Creating demo users...")
    print("-" * 60)
    
    for user_data in demo_users:
        email = user_data['email']
        
        # Check if user already exists
        existing_user = get_user_by_email(email)
        if existing_user:
            print(f"✓ User already exists: {email}")
            continue
        
        try:
            user = create_user(
                email=user_data['email'],
                password=user_data['password'],
                role=user_data['role'],
                full_name=user_data.get('full_name'),
                license_number=user_data.get('license_number'),
                specialization=user_data.get('specialization')
            )
            
            role_label = user_data['role'].upper()
            print(f"✓ Created {role_label}: {email}")
            print(f"  Password: {user_data['password']}")
            print(f"  Full Name: {user_data.get('full_name', 'N/A')}")
            
        except Exception as e:
            print(f"✗ Failed to create {email}: {str(e)}")
    
    print("-" * 60)
    print("Demo user setup complete!")
    print("\nTest Credentials:")
    print("  Patient: patient@demo.com / password123")
    print("  Patient 2: patient2@demo.com / password123")
    print("  Doctor: doctor@hospital.com / password123")
    print("  Doctor 2: doctor2@hospital.com / password123")

if __name__ == '__main__':
    create_demo_users()
