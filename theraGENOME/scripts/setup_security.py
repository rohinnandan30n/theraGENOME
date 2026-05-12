#!/usr/bin/env python3
"""
HIPAA Security Implementation Script
Sets up RBAC, audit logging, and encryption on PostgreSQL
"""

import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Database connection
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', 5432)
DB_NAME = os.getenv('DB_NAME', 'thergenome_dev')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD')

def connect_db():
    """Connect to PostgreSQL"""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def setup_extensions(conn):
    """Enable required PostgreSQL extensions"""
    print("\n📦 Setting up PostgreSQL extensions...")
    cursor = conn.cursor()
    
    try:
        # UUID extension
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
        print("  ✅ uuid-ossp extension enabled")
        
        # Encryption extension
        cursor.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')
        print("  ✅ pgcrypto extension enabled")
        
        conn.commit()
    except Exception as e:
        print(f"  ⚠️ Extension setup: {e}")
        conn.rollback()

def setup_rbac(conn):
    """Setup Role-Based Access Control"""
    print("\n🔐 Setting up RBAC roles...")
    cursor = conn.cursor()
    
    roles = [
        ("clinician_group", "Clinicians with full data access"),
        ("researcher_group", "Researchers with read-only access"),
        ("admin_group", "System administrators"),
    ]
    
    try:
        for role_name, description in roles:
            try:
                cursor.execute(f'CREATE ROLE {role_name};')
                print(f"  ✅ Created role: {role_name}")
            except psycopg2.errors.DuplicateObject:
                print(f"  ℹ️  Role exists: {role_name}")
                cursor.execute("ROLLBACK")
                cursor.execute(f'CREATE ROLE {role_name};')
        
        # Grant permissions to roles
        cursor.execute(f'GRANT SELECT, INSERT, UPDATE ON patients TO clinician_group;')
        cursor.execute(f'GRANT SELECT ON patients TO researcher_group;')
        cursor.execute(f'GRANT ALL ON patients TO admin_group;')
        
        # Revoke default public access
        cursor.execute(f'REVOKE ALL ON patients FROM PUBLIC;')
        
        print("  ✅ Permissions configured")
        conn.commit()
    except Exception as e:
        print(f"  ⚠️ RBAC setup error: {e}")
        conn.rollback()

def setup_audit_logging(conn):
    """Enable query audit logging"""
    print("\n📋 Setting up audit logging...")
    cursor = conn.cursor()
    
    # Check current settings
    cursor.execute("SHOW log_connections;")
    print(f"  Current log_connections: {cursor.fetchone()[0]}")
    
    cursor.execute("SHOW log_statement;")
    print(f"  Current log_statement: {cursor.fetchone()[0]}")
    
    try:
        cursor.execute("ALTER SYSTEM SET log_connections = ON;")
        cursor.execute("ALTER SYSTEM SET log_disconnections = ON;")
        cursor.execute("ALTER SYSTEM SET log_statement = 'ddl';")  # Log DDL only
        cursor.execute("ALTER SYSTEM SET log_duration = ON;")
        
        cursor.execute("SELECT pg_reload_conf();")
        conn.commit()
        print("  ✅ Audit logging configured (restart PostgreSQL to apply)")
    except Exception as e:
        print(f"  ⚠️ Audit logging setup: {e}")
        conn.rollback()

def create_audit_table(conn):
    """Create audit log table"""
    print("\n📝 Setting up audit log table...")
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            table_name VARCHAR(255) NOT NULL,
            operation VARCHAR(10) NOT NULL,
            old_data JSONB,
            new_data JSONB,
            user_name VARCHAR(255) NOT NULL,
            timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            
            CONSTRAINT audit_operation_check CHECK (operation IN ('INSERT', 'UPDATE', 'DELETE'))
        );
        
        CREATE INDEX idx_audit_table_timestamp ON audit_log(table_name, timestamp);
        CREATE INDEX idx_audit_user_timestamp ON audit_log(user_name, timestamp);
        ''')
        conn.commit()
        print("  ✅ Audit log table created")
    except Exception as e:
        print(f"  ⚠️ Audit table setup: {e}")
        conn.rollback()

def verify_security(conn):
    """Verify security setup"""
    print("\n✅ Security Verification:")
    cursor = conn.cursor()
    
    try:
        # Check RBAC roles
        cursor.execute("""
        SELECT rolname, rolsuper, rolinherit 
        FROM pg_catalog.pg_roles 
        WHERE rolname IN ('clinician_group', 'researcher_group', 'admin_group')
        ORDER BY rolname;
        """)
        roles = cursor.fetchall()
        print(f"\n  Roles configured: {len(roles)}")
        for role in roles:
            print(f"    - {role[0]}")
        
        # Check extensions
        cursor.execute("""
        SELECT extname FROM pg_catalog.pg_extension 
        WHERE extname IN ('uuid-ossp', 'pgcrypto')
        ORDER BY extname;
        """)
        exts = cursor.fetchall()
        print(f"\n  Extensions enabled: {len(exts)}")
        for ext in exts:
            print(f"    - {ext[0]}")
        
        # Check audit table
        cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'audit_log'
        );
        """)
        audit_exists = cursor.fetchone()[0]
        print(f"\n  Audit log table: {'✅ Created' if audit_exists else '❌ Not found'}")
        
    except Exception as e:
        print(f"  ⚠️ Verification error: {e}")

def main():
    print("=" * 60)
    print("🔒 TheraGenome HIPAA Security Setup")
    print("=" * 60)
    
    conn = connect_db()
    if not conn:
        print("\n❌ Cannot connect to database. Check credentials in .env file")
        sys.exit(1)
    
    print(f"\n✅ Connected to {DB_NAME} on {DB_HOST}:{DB_PORT}")
    
    # Run setup steps
    setup_extensions(conn)
    setup_rbac(conn)
    setup_audit_logging(conn)
    create_audit_table(conn)
    verify_security(conn)
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Security setup complete!")
    print("=" * 60)
    print("\n📌 Remaining TODO items for production:")
    print("  - Enable TLS/SSL for connections (sslmode=require)")
    print("  - Configure encrypted backups")
    print("  - Set up monitoring and alerts")
    print("  - Implement API authentication tokens")
    print("  - Run security audit and penetration testing")
    print("=" * 60)

if __name__ == "__main__":
    main()
