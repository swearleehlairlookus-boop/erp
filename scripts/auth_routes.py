"""
POLMED Backend - Authentication Routes
Login, logout, and user profile endpoints
"""

from flask import Blueprint, request, jsonify, current_app
from auth import (
    create_token, verify_user_credentials, require_auth, get_current_user
)
from database import get_db_connection
from datetime import datetime, timezone

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User login endpoint
    Returns JWT token on successful authentication
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({
                'success': False,
                'error': 'Email and password are required'
            }), 400
        
        # Get database connection
        db_conn = get_db_connection()
        
        # Verify credentials
        user = verify_user_credentials(db_conn, email, password)
        
        if not user:
            db_conn.close()
            return jsonify({
                'success': False,
                'error': 'Invalid email or password'
            }), 401
        
        # Check if user is active
        if not user.get('is_active'):
            db_conn.close()
            return jsonify({
                'success': False,
                'error': 'User account is inactive'
            }), 403
        
        # Create JWT token
        token = create_token(
            user_id=user['id'],
            email=user['email'],
            role=user['role_name']
        )
        
        # Log login activity
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, table_name, record_id, ip_address, user_agent)
            VALUES (%s, 'LOGIN', 'users', %s, %s, %s)
        """, (user['id'], user['id'], request.environ.get('REMOTE_ADDR', ''), request.headers.get('User-Agent', '')))
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': {
                    'user_id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'role': user['role_name']
                }
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user_endpoint():
    """
    Get current authenticated user details
    Requires valid JWT token
    """
    try:
        db_conn = get_db_connection()
        
        user = get_current_user(db_conn)
        db_conn.close()
        
        if not user:
            return jsonify({
                'success': False,
                'error': 'User not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': {
                'id': user['id'],
                'email': user['email'],
                'first_name': user['first_name'],
                'last_name': user['last_name'],
                'phone_number': user['phone_number'],
                'role_name': user['role_name'],
                'is_active': user['is_active']
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/logout', methods=['POST'])
@require_auth
def logout():
    """
    User logout endpoint
    Logs the logout activity
    """
    try:
        db_conn = get_db_connection()
        
        # Log logout activity
        cursor = db_conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, table_name, record_id, ip_address, user_agent)
            VALUES (%s, 'LOGOUT', 'users', %s, %s, %s)
        """, (request.user_id, request.user_id, request.environ.get('REMOTE_ADDR', ''), request.headers.get('User-Agent', '')))
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Logged out successfully'
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@auth_bp.route('/verify', methods=['GET'])
@require_auth
def verify_token_endpoint():
    """
    Verify current token is valid
    """
    return jsonify({
        'success': True,
        'data': {
            'user_id': request.user_id,
            'email': request.user_email,
            'role': request.user_role
        }
    }), 200
