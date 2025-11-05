#!/usr/bin/env python3
"""
Create initial admin user for POLMED Backend
Run this after database setup to create first admin account
"""

import os
import sys
from getpass import getpass
from datetime import datetime, timezone
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

# Configuration
DB_HOST = os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com')
DB_PORT = int(os.environ.get('DB_PORT', 3306))
DB_NAME = os.environ.get('DB_NAME', 'mobile_clinic_erp')
DB_USER = os.environ.get('DB_USER', 'dbadmin')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025')

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_info(message: str):
    print(f"{Colors.BLUE}ℹ{Colors.END} {message}")

def print_success(message: str):
    print(f"{Colors.GREEN}✓{Colors.END} {message}")

def print_error(message: str):
    print(f"{Colors.RED}✗{Colors.END} {message}")

def create_admin_user():
    """Create initial admin user"""
    
    print(f"\n{Colors.BLUE}╔═════════════════════════════════════════╗")
    print(f"║  POLMED Admin User Creation Script v2.0 ║")
    print(f"╚═════════════════════════════════════════╝{Colors.END}\n")
    
    # Get user input
    print_info("Please provide the following information:")
    print()
    
    email = input("Admin Email: ").strip().lower()
    if '@' not in email:
        print_error("Invalid email format")
        return False
    
    first_name = input("First Name: ").strip()
    if not first_name:
        print_error("First name is required")
        return False
    
    last_name = input("Last Name: ").strip()
    if not last_name:
        print_error("Last name is required")
        return False
    
    phone_number = input("Phone Number: ").strip()
    if not phone_number:
        print_error("Phone number is required")
        return False
    
    print()
    while True:
        password = getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print_error("Password must be at least 8 characters")
            continue
        
        password_confirm = getpass("Confirm Password: ")
        if password != password_confirm:
            print_error("Passwords do not match")
            continue
        
        break
    
    # Connect to database
    try:
        print_info("Connecting to database...")
        
        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            use_unicode=True,
            charset='utf8mb4',
            ssl_disabled=False,
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )
        
        cursor = conn.cursor()
        
        # Check if admin role exists
        cursor.execute("SELECT id FROM user_roles WHERE role_name = 'administrator'")
        role_result = cursor.fetchone()
        
        if not role_result:
            print_error("Administrator role not found - run database setup first")
            conn.close()
            return False
        
        admin_role_id = role_result[0]
        print_success("Administrator role found")
        
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            print_error(f"User with email '{email}' already exists")
            conn.close()
            return False
        
        # Create admin user
        print_info("Creating admin user...")
        
        username = f"{first_name.lower()}_{last_name.lower()}".replace(' ', '_')
        password_hash = generate_password_hash(password)
        
        cursor.execute(
            """
            INSERT INTO users (
                username, email, password_hash, role_id, first_name, last_name,
                phone_number, is_active, requires_approval, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, FALSE, %s)
            """,
            (
                username,
                email,
                password_hash,
                admin_role_id,
                first_name,
                last_name,
                phone_number,
                datetime.now(timezone.utc)
            )
        )
        
        conn.commit()
        
        print_success("Admin user created successfully!")
        print()
        print_info("User Details:")
        print(f"  • Email: {email}")
        print(f"  • Name: {first_name} {last_name}")
        print(f"  • Role: Administrator")
        print(f"  • Username: {username}")
        print()
        print_info("You can now login with these credentials")
        
        cursor.close()
        conn.close()
        
        return True
    
    except Error as e:
        print_error(f"Database error: {e}")
        return False
    
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def main():
    try:
        success = create_admin_user()
        return 0 if success else 1
    except KeyboardInterrupt:
        print("\n")
        print_info("Operation cancelled by user")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())
