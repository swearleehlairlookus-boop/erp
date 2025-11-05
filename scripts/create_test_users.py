#!/usr/bin/env python3
"""
Script to create test user accounts for POLMED Mobile Clinic ERP
Uses existing roles and data structure from the database
"""

import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from datetime import datetime
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'db-polmed.mysql.database.azure.com'),
    'database': os.environ.get('DB_NAME', 'mobile_clinic_erp'),
    'user': os.environ.get('DB_USER', 'dbadmin'),
    'password': os.environ.get('DB_PASSWORD', 'Polm3d!DB@2025'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'autocommit': False,
    'use_unicode': True,
    'charset': 'utf8mb4',
    'ssl_disabled': False,
    'ssl_verify_cert': False,
    'ssl_verify_identity': False
}

# Test users data - using exact role names from your data
# Includes both active and pending users for comprehensive testing
TEST_USERS = [
    # System Administrator - Full access
    {
        'username': 'admin_main',
            'email': 'admin.main@polmed.org',
        'password': 'password123',
        'first_name': 'System',
        'last_name': 'Administrator',
        'role_name': 'administrator',
        'phone_number': '+27123456789',
        'geographic_restrictions': '["National"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Alternative admin account
    {
        'username': 'admin_alt',
        'email': 'admin.test@polmed.co.za',
        'password': 'admin123',
        'first_name': 'Test',
        'last_name': 'Administrator',
        'role_name': 'administrator',
        'phone_number': '+27123456780',
        'geographic_restrictions': '["National"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Primary Doctor - Active
    {
        'username': 'doctor_main',
        'email': 'doctor@polmed.org',
        'password': 'doctor123',
        'first_name': 'Dr. Jane',
        'last_name': 'Smith',
        'role_name': 'doctor',
        'phone_number': '+27123456790',
        'geographic_restrictions': '["KwaZulu-Natal"]',
        'mp_number': 'MP123456',
        'is_active': True,
        'requires_approval': False
    },
    # Secondary Doctor - Active
    {
        'username': 'doctor_test',
        'email': 'doctor.test@polmed.co.za',
        'password': 'doctor123',
        'first_name': 'Dr. John',
        'last_name': 'Williams',
        'role_name': 'doctor',
        'phone_number': '+27123456791',
        'geographic_restrictions': '["Gauteng"]',
        'mp_number': 'MP654321',
        'is_active': True,
        'requires_approval': False
    },
    # Nurse - Primary
    {
        'username': 'nurse_test',
        'email': 'nurse.test@polmed.co.za',
        'password': 'nurse123',
        'first_name': 'Mary',
        'last_name': 'Johnson',
        'role_name': 'nurse',
        'phone_number': '+27123456792',
        'geographic_restrictions': '["KwaZulu-Natal"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Nurse - Secondary
    {
        'username': 'nurse_alt',
        'email': 'nurse.alt@polmed.co.za',
        'password': 'nurse456',
        'first_name': 'Susan',
        'last_name': 'Davis',
        'role_name': 'nurse',
        'phone_number': '+27123456793',
        'geographic_restrictions': '["Western Cape"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Administrative Clerk
    {
        'username': 'clerk_test',
        'email': 'clerk.test@polmed.co.za',
        'password': 'clerk123',
        'first_name': 'Sarah',
        'last_name': 'Williams',
        'role_name': 'clerk',
        'phone_number': '+27123456794',
        'geographic_restrictions': '["KwaZulu-Natal"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Social Worker
    {
        'username': 'social_test',
        'email': 'social.test@polmed.co.za',
        'password': 'social123',
        'first_name': 'David',
        'last_name': 'Brown',
        'role_name': 'social_worker',
        'phone_number': '+27123456795',
        'geographic_restrictions': '["KwaZulu-Natal"]',
        'mp_number': None,
        'is_active': True,
        'requires_approval': False
    },
    # Pending Doctor (for approval testing)
    {
        'username': 'doctor_pending',
        'email': 'doctor.pending@polmed.co.za',
        'password': 'testdoc123',
        'first_name': 'Dr. Michael',
        'last_name': 'Doe',
        'role_name': 'doctor',
        'phone_number': '+27123456796',
        'geographic_restrictions': '["Gauteng"]',
        'mp_number': 'MP789012',
        'is_active': False,
        'requires_approval': True
    },
    # Inactive User (for testing user management)
    {
        'username': 'user_inactive',
        'email': 'inactive.user@polmed.co.za',
        'password': 'inactive123',
        'first_name': 'Inactive',
        'last_name': 'User',
        'role_name': 'clerk',
        'phone_number': '+27123456797',
        'geographic_restrictions': '["Eastern Cape"]',
        'mp_number': None,
        'is_active': False,
        'requires_approval': False
    }
]

class DatabaseManager:
    """Database connection and query management"""
    
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                logger.info("Database connection successful")
                return connection
        except Error as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = False):
        connection = DatabaseManager.get_connection()
        if not connection:
            logger.error("No database connection available")
            return None
        
        try:
            cursor = connection.cursor(dictionary=True)
            cursor.execute(query, params or ())
            
            if fetch:
                result = cursor.fetchall()
            else:
                connection.commit()
                result = cursor.rowcount
            
            return result
        except Error as e:
            logger.error(f"Query execution error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

def get_role_id(role_name: str) -> int:
    """Get role ID by role name from existing data"""
    query = "SELECT id FROM user_roles WHERE role_name = %s"
    result = DatabaseManager.execute_query(query, (role_name,), fetch=True)
    
    if result and len(result) > 0:
        return result[0]['id']
    else:
        logger.error(f"Role '{role_name}' not found")
        return None

def list_existing_roles():
    """List all existing roles in the database"""
    # First try with role_description, fall back without it
    query_with_desc = "SELECT id, role_name, role_description FROM user_roles ORDER BY role_name"
    query_without_desc = "SELECT id, role_name FROM user_roles ORDER BY role_name"
    
    roles = DatabaseManager.execute_query(query_with_desc, fetch=True)
    
    # If that fails, try without role_description column
    if roles is None:
        roles = DatabaseManager.execute_query(query_without_desc, fetch=True)
    
    if roles:
        print("\nExisting roles in database:")
        print("-" * 50)
        for role in roles:
            description = role.get('role_description', 'N/A')
            print(f"ID: {role['id']:<3} | Name: {role['role_name']:<15} | Description: {description}")
        return True
    else:
        print("No roles found in database!")
        return False

def user_exists(email: str) -> bool:
    """Check if user with given email already exists"""
    query = "SELECT id FROM users WHERE email = %s"
    result = DatabaseManager.execute_query(query, (email,), fetch=True)
    return result is not None and len(result) > 0

def create_user(user_data: dict) -> bool:
    """Create a single user with hashed password"""
    try:
        # Check if user already exists
        if user_exists(user_data['email']):
            logger.warning(f"User {user_data['email']} already exists, skipping...")
            return True
        
        # Get role ID from existing data
        role_id = get_role_id(user_data['role_name'])
        if not role_id:
            logger.error(f"Cannot create user {user_data['email']}: role '{user_data['role_name']}' not found")
            return False
        
        # Generate hashed password using the same method as Flask
        password_hash = generate_password_hash(user_data['password'])
        
        # Insert user into database - try with all fields first, then fallback
        insert_query_full = """
        INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                          phone_number, mp_number, geographic_restrictions, is_active, 
                          requires_approval, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        insert_query_basic = """
        INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                          phone_number, is_active, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        # Try full insert first
        result = DatabaseManager.execute_query(insert_query_full, (
            user_data['username'],
            user_data['email'],
            password_hash,
            role_id,
            user_data['first_name'],
            user_data['last_name'],
            user_data['phone_number'],
            user_data['mp_number'],
            user_data['geographic_restrictions'],
            user_data['is_active'],
            user_data['requires_approval'],
            datetime.now()
        ))
        
        # If that fails, try basic insert
        if result is None:
            logger.warning(f"Full insert failed for {user_data['email']}, trying basic insert...")
            result = DatabaseManager.execute_query(insert_query_basic, (
                user_data['username'],
                user_data['email'],
                password_hash,
                role_id,
                user_data['first_name'],
                user_data['last_name'],
                user_data['phone_number'],
                user_data['is_active'],
                datetime.now()
            ))
        
        if result:
            logger.info(f"Successfully created user: {user_data['email']} ({user_data['role_name']})")
            status = "Active" if user_data['is_active'] else "Pending Approval"
            print(f"✓ Created: {user_data['email']} | Password: {user_data['password']} | Role: {user_data['role_name']} | Status: {status}")
            return True
        else:
            logger.error(f"Failed to create user: {user_data['email']}")
            return False
            
    except Exception as e:
        logger.error(f"Error creating user {user_data['email']}: {e}")
        return False

def verify_password_hashing():
    """Test password hashing to ensure it matches Flask app method"""
    test_password = "test123"
    hash1 = generate_password_hash(test_password)
    
    # Test verification
    from werkzeug.security import check_password_hash
    verify1 = check_password_hash(hash1, test_password)
    verify2 = check_password_hash(hash1, "wrong_password")
    
    logger.info(f"Password hashing verification - correct: {verify1}, wrong: {verify2}")
    return verify1 and not verify2

def test_user_login(email: str, password: str) -> bool:
    """
    Test login for a created user - simulates the authentication flow
    This matches the verify_user_credentials function from auth.py
    """
    try:
        query = """
            SELECT
                u.id,
                u.email,
                u.password_hash,
                u.first_name,
                u.last_name,
                u.is_active,
                r.role_name
            FROM users u
            LEFT JOIN user_roles r ON u.role_id = r.id
            WHERE u.email = %s AND u.is_active = TRUE
        """
        
        user_result = DatabaseManager.execute_query(query, (email,), fetch=True)
        
        if not user_result or len(user_result) == 0:
            logger.error(f"User {email} not found or not active")
            return False
        
        user = user_result[0]
        
        # Verify password using same method as auth.py
        from werkzeug.security import check_password_hash
        if not check_password_hash(user['password_hash'], password):
            logger.error(f"Password verification failed for {email}")
            return False
        
        logger.info(f"✓ Login test successful for {email} ({user['role_name']})")
        return True
        
    except Exception as e:
        logger.error(f"Error testing login for {email}: {e}")
        return False

def test_all_user_logins():
    """Test login functionality for all created active users"""
    print("\n" + "=" * 60)
    print("Testing Login Functionality")
    print("=" * 60)
    
    success_count = 0
    active_users = [user for user in TEST_USERS if user['is_active']]
    
    for user_data in active_users:
        if test_user_login(user_data['email'], user_data['password']):
            success_count += 1
            print(f"✓ {user_data['email']:<30} | {user_data['role_name']:<15} | Login OK")
        else:
            print(f"✗ {user_data['email']:<30} | {user_data['role_name']:<15} | Login FAILED")
    
    print(f"\nLogin test results: {success_count}/{len(active_users)} successful")
    return success_count == len(active_users)

def display_existing_users():
    """Display existing users for reference"""
    query = """
    SELECT u.username, u.email, ur.role_name, u.is_active, 
           COALESCE(u.requires_approval, 0) as requires_approval
    FROM users u
    LEFT JOIN user_roles ur ON u.role_id = ur.id
    ORDER BY u.created_at DESC
    LIMIT 10
    """
    users = DatabaseManager.execute_query(query, fetch=True)
    
    if users and len(users) > 0:
        print("\nExisting users (last 10):")
        print("-" * 80)
        for user in users:
            status = "Active" if user['is_active'] else "Pending" if user.get('requires_approval', 0) else "Inactive"
            role_name = user.get('role_name', 'Unknown')
            print(f"{user['email']:<30} | {role_name:<15} | {status}")
    else:
        print("\nNo existing users found or users table is empty.")

def generate_mock_server_users():
    """Generate Python code for updating test_server.py with consistent user data"""
    active_users = [user for user in TEST_USERS if user['is_active']]
    
    print(f"\n🔧 Mock Server Update Code:")
    print("=" * 60)
    print("# Copy this code to update MOCK_USERS in test_server.py")
    print("MOCK_USERS = {")
    
    for user in active_users:
        print(f"    '{user['email']}': {{")
        print(f"        'id': {TEST_USERS.index(user) + 1},")
        print(f"        'email': '{user['email']}',")
        print(f"        'password': '{user['password']}',")
        print(f"        'first_name': '{user['first_name']}',")
        print(f"        'last_name': '{user['last_name']}',")
        print(f"        'role_name': '{user['role_name']}',")
        print(f"        'is_active': {str(user['is_active']).lower()}")
        print(f"    }},")
    
    print("}")
    print("\n# This ensures test_server.py has the same credentials as the database")

def main():
    """Main function to create test users"""
    print("=" * 60)
    print("POLMED Mobile Clinic - Test User Creation Script")
    print("Using existing database roles and structure")
    print("=" * 60)
    
    # Test database connection
    connection = DatabaseManager.get_connection()
    if not connection:
        print("❌ Database connection failed!")
        print("Please check your database configuration and ensure MySQL is running.")
        return
    connection.close()
    print("✓ Database connection successful")
    
    # List existing roles
    if not list_existing_roles():
        print("❌ No roles found in database! Please run your data setup script first.")
        return
    
    # Show existing users
    display_existing_users()
    
    # Verify password hashing
    if not verify_password_hashing():
        print("❌ Password hashing verification failed!")
        return
    print("✓ Password hashing verification successful")
    
    print("\n" + "=" * 60)
    print("Creating test users...")
    print("=" * 60)
    
    # Create all test users
    success_count = 0
    for user_data in TEST_USERS:
        if create_user(user_data):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"User creation completed: {success_count}/{len(TEST_USERS)} successful")
    print("=" * 60)
    
    if success_count > 0:
        # Test login functionality for active users
        login_test_success = test_all_user_logins()
        
        print("\n" + "=" * 60)
        print("Test Login Credentials Summary")
        print("=" * 60)
        
        # Categorize users by status
        active_users = [user for user in TEST_USERS if user['is_active']]
        pending_users = [user for user in TEST_USERS if user['requires_approval']]
        inactive_users = [user for user in TEST_USERS if not user['is_active'] and not user['requires_approval']]
        
        if active_users:
            print("\n🟢 ACTIVE USERS (Ready for Login):")
            print("-" * 50)
            for user in active_users:
                print(f"✓ {user['email']:<35} | {user['password']:<12} | {user['role_name']}")
        
        if pending_users:
            print("\n🟡 PENDING APPROVAL:")
            print("-" * 50)
            for user in pending_users:
                print(f"⏳ {user['email']:<35} | {user['password']:<12} | {user['role_name']}")
        
        if inactive_users:
            print("\n🔴 INACTIVE USERS:")
            print("-" * 50)
            for user in inactive_users:
                print(f"❌ {user['email']:<35} | {user['password']:<12} | {user['role_name']}")
        
        print("\n" + "=" * 60)
        print("USAGE INSTRUCTIONS")
        print("=" * 60)
        print("1. Frontend Login: Use any ACTIVE user credentials above")
        print("2. Mock Server: admin@polmed.org / password123 & doctor@polmed.org / doctor123")
        print("3. Database Login: Any active user listed above")
        
        print(f"\n📊 Statistics:")
        print(f"   - Total users created: {success_count}")
        print(f"   - Active users: {len(active_users)}")
        print(f"   - Pending approval: {len(pending_users)}")
        print(f"   - Inactive users: {len(inactive_users)}")
        print(f"   - Login test: {'✓ PASSED' if login_test_success else '✗ FAILED'}")
        
        print(f"\n🔧 Admin Actions:")
        print("To approve pending users:")
        print("UPDATE users SET is_active = TRUE, requires_approval = FALSE")
        print("WHERE requires_approval = TRUE;")
        
        print("\nTo activate inactive users:")
        print("UPDATE users SET is_active = TRUE WHERE is_active = FALSE;")
        
        # Generate mock server update code
        generate_mock_server_users()

if __name__ == "__main__":
    main()