"""
Simple Flask test server without database dependencies
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone
import jwt
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key-for-development'

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Mock user data for testing - synced with database test users
MOCK_USERS = {
    'admin@polmed.org': {
        'id': 1,
        'email': 'admin@polmed.org',
        'password': 'password123',
        'first_name': 'System',
        'last_name': 'Administrator',
        'role_name': 'administrator',
        'is_active': True
    },
    'admin.test@polmed.co.za': {
        'id': 2,
        'email': 'admin.test@polmed.co.za',
        'password': 'admin123',
        'first_name': 'Test',
        'last_name': 'Administrator',
        'role_name': 'administrator',
        'is_active': True
    },
    'doctor@polmed.org': {
        'id': 3,
        'email': 'doctor@polmed.org',
        'password': 'doctor123',
        'first_name': 'Dr. Jane',
        'last_name': 'Smith',
        'role_name': 'doctor',
        'is_active': True
    },
    'doctor.test@polmed.co.za': {
        'id': 4,
        'email': 'doctor.test@polmed.co.za',
        'password': 'doctor123',
        'first_name': 'Dr. John',
        'last_name': 'Williams',
        'role_name': 'doctor',
        'is_active': True
    },
    'nurse.test@polmed.co.za': {
        'id': 5,
        'email': 'nurse.test@polmed.co.za',
        'password': 'nurse123',
        'first_name': 'Mary',
        'last_name': 'Johnson',
        'role_name': 'nurse',
        'is_active': True
    },
    'clerk.test@polmed.co.za': {
        'id': 6,
        'email': 'clerk.test@polmed.co.za',
        'password': 'clerk123',
        'first_name': 'Sarah',
        'last_name': 'Williams',
        'role_name': 'clerk',
        'is_active': True
    }
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """Simple health check without database"""
    return jsonify({
        'success': True,
        'status': 'healthy',
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'message': 'Backend server is running',
        'version': '2.0.0'
    })

@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint"""
    return jsonify({
        'success': True,
        'message': 'POLMED Backend API Test',
        'version': '2.0.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/login',
            'health': '/api/health'
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Mock login endpoint for testing"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Check if user exists and password matches
        user = MOCK_USERS.get(email)
        if not user or user['password'] != password:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Create a simple JWT token (for testing only)
        token_payload = {
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role_name'],
            'exp': datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
        }
        
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        # Remove password from user data and add role field for frontend compatibility
        user_data = {k: v for k, v in user.items() if k != 'password'}
        user_data['role'] = user_data['role_name']  # Frontend expects 'role' field
        
        return jsonify({
            'success': True,
            'data': {
                'token': token,
                'user': user_data
            },
            'message': 'Login successful'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/auth/me', methods=['GET'])
def get_current_user():
    """Get current user info from token"""
    try:
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'success': False, 'error': 'No valid token provided'}), 401
        
        token = auth_header.split(' ')[1]
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        
        user = MOCK_USERS.get(payload['email'])
        if not user:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        # Remove password from user data
        user_data = {k: v for k, v in user.items() if k != 'password'}
        
        return jsonify({
            'success': True,
            'data': user_data
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting POLMED Test Backend Server...")
    print("Available at: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)