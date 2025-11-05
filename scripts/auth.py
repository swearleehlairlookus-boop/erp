"""
POLMED Backend - Authentication Module
JWT-based authentication with role-based access control
"""

from functools import wraps
from datetime import datetime, timezone, timedelta
import os
import jwt
from flask import request, jsonify, current_app
import mysql.connector
from werkzeug.security import check_password_hash

def create_token(user_id: int, email: str, role: str, expires_in_hours: int = 24):
    """
    Create JWT token for authenticated user
    """
    payload = {
        'user_id': user_id,
        'email': email,
        'role': role,
        'iat': datetime.now(timezone.utc),
        'exp': datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
    }
    
    secret = os.environ.get('JWT_SECRET', 'your-secret-key')
    algorithm = os.environ.get('JWT_ALGORITHM', 'HS256')
    
    return jwt.encode(payload, secret, algorithm=algorithm)

def verify_token(token: str):
    """
    Verify JWT token and return payload
    Returns None if token is invalid or expired
    """
    try:
        secret = os.environ.get('JWT_SECRET', 'your-secret-key')
        algorithm = os.environ.get('JWT_ALGORITHM', 'HS256')
        
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
    except Exception:
        return None

def get_token_from_request():
    """
    Extract JWT token from Authorization header
    Expected format: Authorization: Bearer <token>
    """
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header.startswith('Bearer '):
        return None
    
    return auth_header[7:]  # Remove 'Bearer ' prefix

def require_auth(f):
    """
    Decorator to require valid JWT authentication
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({
                'success': False,
                'error': 'Missing authentication token'
            }), 401
        
        payload = verify_token(token)
        
        if not payload:
            return jsonify({
                'success': False,
                'error': 'Invalid or expired token'
            }), 401
        
        # Store user info in request context
        request.user_id = payload.get('user_id')
        request.user_email = payload.get('email')
        request.user_role = payload.get('role')
        
        return f(*args, **kwargs)
    
    return decorated_function

def require_role(*allowed_roles):
    """
    Decorator to require specific user roles
    Usage: @require_role('doctor', 'nurse')
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = get_token_from_request()
            
            if not token:
                return jsonify({
                    'success': False,
                    'error': 'Missing authentication token'
                }), 401
            
            payload = verify_token(token)
            
            if not payload:
                return jsonify({
                    'success': False,
                    'error': 'Invalid or expired token'
                }), 401
            
            user_role = payload.get('role')
            
            if user_role not in allowed_roles:
                return jsonify({
                    'success': False,
                    'error': f'User role does not have permission to access this resource'
                }), 403
            
            # Store user info in request context
            request.user_id = payload.get('user_id')
            request.user_email = payload.get('email')
            request.user_role = user_role
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def get_current_user(db_connection):
    """
    Get current authenticated user details from database
    """
    if not hasattr(request, 'user_id'):
        return None
    
    try:
        cursor = db_connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.phone_number,
                u.is_active,
                r.role_name,
                u.clinic_id
            FROM users u
            LEFT JOIN user_roles r ON u.role_id = r.id
            WHERE u.id = %s
        """, (request.user_id,))
        
        user = cursor.fetchone()
        cursor.close()
        
        return user
    
    except Exception as e:
        print(f"Error fetching user: {e}")
        return None

def verify_user_credentials(db_connection, email: str, password: str):
    """
    Verify user email and password
    Returns user data if valid, None if invalid
    """
    try:
        cursor = db_connection.cursor(dictionary=True)
        
        cursor.execute("""
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
        """, (email,))
        
        user = cursor.fetchone()
        cursor.close()
        
        if not user:
            return None
        
        # Verify password
        if not check_password_hash(user['password_hash'], password):
            return None
        
        return user
    
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None

def check_permission(db_connection, user_id: int, resource: str, action: str):
    """
    Check if user has permission for specific resource action
    """
    try:
        cursor = db_connection.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM role_permissions rp
            JOIN users u ON u.role_id = rp.role_id
            JOIN resources r ON r.id = rp.resource_id
            WHERE u.id = %s
                AND r.resource_name = %s
                AND rp.action = %s
        """, (user_id, resource, action))
        
        result = cursor.fetchone()
        cursor.close()
        
        return result and result['count'] > 0
    
    except Exception as e:
        print(f"Error checking permission: {e}")
        return False
