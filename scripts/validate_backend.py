#!/usr/bin/env python3
"""
POLMED Backend Validation Script
Comprehensive backend health check and validation
"""

import sys
import json
import os
from datetime import datetime
import mysql.connector
from mysql.connector import Error

# Configuration
DB_HOST = os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com')
DB_NAME = os.environ.get('DB_NAME', 'mobile_clinic_erp')
DB_USER = os.environ.get('DB_USER', 'dbadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025')

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def get_db_connection():
    """Get database connection with proper SSL settings for Azure"""
    return mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        use_unicode=True,
        charset='utf8mb4',
        ssl_disabled=False,
        ssl_verify_cert=False,
        ssl_verify_identity=False
    )

def print_status(message: str, status: str):
    """Print formatted status message"""
    if status == 'success':
        print(f"{Colors.GREEN}✓{Colors.END} {message}")
    elif status == 'error':
        print(f"{Colors.RED}✗{Colors.END} {message}")
    elif status == 'warning':
        print(f"{Colors.YELLOW}⚠{Colors.END} {message}")
    else:
        print(f"{Colors.BLUE}•{Colors.END} {message}")

def check_database_connection():
    """Check database connectivity"""
    print(f"\n{Colors.BLUE}=== Database Connectivity ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        if conn.is_connected():
            print_status("Connected to MySQL database", "success")
            conn.close()
            return True
        else:
            print_status("Failed to connect to MySQL", "error")
            return False
    
    except Error as e:
        print_status(f"Database connection error: {e}", "error")
        return False

def check_database_schema():
    """Check database schema validity"""
    print(f"\n{Colors.BLUE}=== Database Schema ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor()
        
        # Check for critical tables
        required_tables = [
            'users', 'user_roles', 'patients', 'patient_visits',
            'vital_signs', 'clinical_notes', 'routes', 'appointments',
            'inventory_stock', 'consumables', 'assets', 'referrals',
            'audit_log'
        ]
        
        cursor.execute("SHOW TABLES")
        existing_tables = {table[0] for table in cursor.fetchall()}
        
        all_exist = True
        for table in required_tables:
            if table in existing_tables:
                print_status(f"Table '{table}' exists", "success")
            else:
                print_status(f"Table '{table}' missing", "error")
                all_exist = False
        
        cursor.close()
        conn.close()
        
        return all_exist
    
    except Exception as e:
        print_status(f"Schema check error: {e}", "error")
        return False

def check_default_roles():
    """Check if default user roles exist"""
    print(f"\n{Colors.BLUE}=== User Roles ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT role_name FROM user_roles")
        roles = {row['role_name'] for row in cursor.fetchall()}
        
        expected_roles = [
            'administrator', 'doctor', 'nurse', 'clerk',
            'social_worker', 'inventory_manager', 'finance', 'viewer'
        ]
        
        all_exist = True
        for role in expected_roles:
            if role in roles:
                print_status(f"Role '{role}' exists", "success")
            else:
                print_status(f"Role '{role}' missing", "warning")
                all_exist = False
        
        cursor.close()
        conn.close()
        
        return all_exist
    
    except Exception as e:
        print_status(f"Role check error: {e}", "error")
        return False

def check_database_indexes():
    """Check for critical indexes"""
    print(f"\n{Colors.BLUE}=== Database Indexes ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(dictionary=True)
        
        # Check for key indexes
        cursor.execute("SHOW INDEX FROM patients WHERE Key_name = 'idx_medical_aid_number'")
        if cursor.fetchone():
            print_status("Patient medical_aid_number index exists", "success")
        else:
            print_status("Patient medical_aid_number index missing", "warning")
        
        cursor.execute("SHOW INDEX FROM patient_visits WHERE Key_name = 'idx_patient_id'")
        if cursor.fetchone():
            print_status("Visit patient_id index exists", "success")
        else:
            print_status("Visit patient_id index missing", "warning")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print_status(f"Index check error: {e}", "error")
        return False

def check_database_size():
    """Check database size and usage"""
    print(f"\n{Colors.BLUE}=== Database Size ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute(f"""
            SELECT 
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
            FROM information_schema.tables
            WHERE table_schema = '{DB_NAME}'
        """)
        
        result = cursor.fetchone()
        size_mb = result['size_mb'] if result else 0
        
        print_status(f"Database size: {size_mb} MB", "success")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print_status(f"Size check error: {e}", "error")
        return False

def check_sample_data():
    """Check if sample data exists"""
    print(f"\n{Colors.BLUE}=== Sample Data ==={Colors.END}")
    
    try:
        conn = get_db_connection()
        
        cursor = conn.cursor(dictionary=True)
        
        # Check users
        cursor.execute("SELECT COUNT(*) as count FROM users")
        user_count = cursor.fetchone()['count']
        if user_count > 0:
            print_status(f"{user_count} users in system", "success")
        else:
            print_status("No users found - run setup wizard", "warning")
        
        # Check patients
        cursor.execute("SELECT COUNT(*) as count FROM patients WHERE is_active = TRUE")
        patient_count = cursor.fetchone()['count']
        print_status(f"{patient_count} active patients", "success" if patient_count > 0 else "warning")
        
        # Check routes
        cursor.execute("SELECT COUNT(*) as count FROM routes WHERE is_active = TRUE")
        route_count = cursor.fetchone()['count']
        print_status(f"{route_count} active routes", "success" if route_count > 0 else "warning")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Exception as e:
        print_status(f"Sample data check error: {e}", "error")
        return False

def check_environment():
    """Check environment configuration"""
    print(f"\n{Colors.BLUE}=== Environment Configuration ==={Colors.END}")
    
    required_env_vars = [
        'DB_HOST', 'DB_NAME', 'DB_USER', 'JWT_SECRET'
    ]
    
    all_set = True
    for var in required_env_vars:
        if os.environ.get(var):
            print_status(f"{var} is set", "success")
        else:
            print_status(f"{var} is not set", "error")
            all_set = False
    
    return all_set

def main():
    """Run all validation checks"""
    print(f"\n{Colors.BLUE}╔═══════════════════════════════════════════╗")
    print(f"║  POLMED Backend Validation Script v2.0   ║")
    print(f"╚═══════════════════════════════════════════╝{Colors.END}\n")
    
    checks = [
        ("Environment", check_environment),
        ("Database Connection", check_database_connection),
        ("Database Schema", check_database_schema),
        ("User Roles", check_default_roles),
        ("Database Indexes", check_database_indexes),
        ("Database Size", check_database_size),
        ("Sample Data", check_sample_data),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print_status(f"{name} check failed: {e}", "error")
            results[name] = False
    
    # Summary
    print(f"\n{Colors.BLUE}=== Validation Summary ==={Colors.END}")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    if passed == total:
        print_status(f"All checks passed ({passed}/{total})", "success")
        print(f"\n{Colors.GREEN}Backend is ready for deployment!{Colors.END}\n")
        return 0
    else:
        print_status(f"Some checks failed ({passed}/{total})", "warning")
        print(f"\n{Colors.YELLOW}Please review and fix any issues above.{Colors.END}\n")
        return 1

if __name__ == '__main__':
    sys.exit(main())

