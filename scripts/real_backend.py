"""
POLMED Backend - Real Database API Server
Connects to MySQL database and provides proper API endpoints
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timezone, timedelta
import jwt
import os
import mysql.connector
from mysql.connector import Error
from werkzeug.security import check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('JWT_SECRET', 'test-secret-key-for-development')

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

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

class DatabaseManager:
    """Database connection and query management"""
    
    @staticmethod
    def get_connection():
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            if connection.is_connected():
                return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None
    
    @staticmethod
    def execute_query(query: str, params: tuple = None, fetch: bool = False):
        connection = DatabaseManager.get_connection()
        if not connection:
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
            print(f"Query execution error: {e}")
            if connection:
                connection.rollback()
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()

def verify_user_credentials(email: str, password: str):
    """Verify user email and password against database"""
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
        
        result = DatabaseManager.execute_query(query, (email,), fetch=True)
        
        if not result or len(result) == 0:
            return None
        
        user = result[0]
        
        # Verify password
        if not check_password_hash(user['password_hash'], password):
            return None
        
        return user
        
    except Exception as e:
        print(f"Error verifying credentials: {e}")
        return None

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check with database connectivity"""
    try:
        connection = DatabaseManager.get_connection()
        if connection:
            connection.close()
            db_status = 'connected'
        else:
            db_status = 'disconnected'
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'message': 'POLMED Backend API with Database',
            'version': '2.1.0',
            'database': db_status
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api', methods=['GET'])
def api_root():
    """API root endpoint"""
    return jsonify({
        'success': True,
        'message': 'POLMED Backend API with Database',
        'version': '2.1.0',
        'status': 'running',
        'endpoints': {
            'auth': '/api/auth/login',
            'health': '/api/health',
            'dashboard': '/api/dashboard/stats',
            'users': '/api/users'
        }
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Database-backed login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'success': False, 'error': 'Email and password required'}), 400
        
        # Verify credentials against database
        user = verify_user_credentials(email, password)
        if not user:
            return jsonify({'success': False, 'error': 'Invalid email or password'}), 401
        
        # Create JWT token
        token_payload = {
            'user_id': user['id'],
            'email': user['email'],
            'role': user['role_name'],
            'exp': datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
        }
        
        token = jwt.encode(token_payload, app.config['SECRET_KEY'], algorithm='HS256')
        
        # Prepare user data for frontend
        user_data = {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'role_name': user['role_name'],
            'role': user['role_name'],  # Frontend expects 'role' field
            'is_active': user['is_active']
        }
        
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

@app.route('/api/dashboard/stats', methods=['GET'])
def get_dashboard_stats():
    """Get dashboard statistics from database"""
    try:
        stats = {}
        
        # Get total patients count
        result = DatabaseManager.execute_query(
            "SELECT COUNT(*) as count FROM patients WHERE is_active = TRUE", 
            fetch=True
        )
        stats['totalPatients'] = result[0]['count'] if result else 0
        
        # Get today's visits
        today = datetime.now().date()
        result = DatabaseManager.execute_query(
            "SELECT COUNT(*) as count FROM patient_visits WHERE DATE(visit_date) = %s",
            (today,),
            fetch=True
        )
        stats['todaysAppointments'] = result[0]['count'] if result else 0
        
        # Get completed visits today
        result = DatabaseManager.execute_query(
            "SELECT COUNT(*) as count FROM patient_visits WHERE DATE(visit_date) = %s AND visit_status = 'completed'",
            (today,),
            fetch=True
        )
        stats['completedVisits'] = result[0]['count'] if result else 0
        
        # Get pending visits (not completed)
        result = DatabaseManager.execute_query(
            "SELECT COUNT(*) as count FROM patient_visits WHERE visit_status IN ('check_in', 'in_progress')",
            fetch=True
        )
        stats['pendingTasks'] = result[0]['count'] if result else 0
        
        # Get recent activity (last 10 visits)
        recent_activity = DatabaseManager.execute_query("""
            SELECT 
                pv.id,
                pv.visit_status,
                pv.visit_date,
                pv.visit_time,
                p.first_name,
                p.last_name,
                u.first_name as staff_first_name,
                u.last_name as staff_last_name
            FROM patient_visits pv
            LEFT JOIN patients p ON pv.patient_id = p.id
            LEFT JOIN users u ON pv.created_by = u.id
            ORDER BY pv.created_at DESC
            LIMIT 10
        """, fetch=True)
        
        # Format recent activity
        formatted_activity = []
        if recent_activity:
            for activity in recent_activity:
                formatted_activity.append({
                    'id': activity['id'],
                    'type': 'visit',
                    'description': f"Visit - {activity['first_name']} {activity['last_name']} ({activity['visit_status']})",
                    'timestamp': f"{activity['visit_date']}T{activity['visit_time'] or '00:00:00'}Z" if activity['visit_date'] else datetime.now().isoformat(),
                    'user': f"{activity['staff_first_name']} {activity['staff_last_name']}" if activity['staff_first_name'] else 'System'
                })
        
        # Get upcoming tasks (pending visits)
        upcoming_tasks = DatabaseManager.execute_query("""
            SELECT 
                pv.id,
                pv.chief_complaint,
                pv.visit_date,
                pv.visit_time,
                p.first_name,
                p.last_name
            FROM patient_visits pv
            LEFT JOIN patients p ON pv.patient_id = p.id
            WHERE pv.visit_status IN ('check_in', 'in_progress')
            ORDER BY pv.visit_date ASC, pv.visit_time ASC
            LIMIT 5
        """, fetch=True)
        
        # Format upcoming tasks
        formatted_tasks = []
        if upcoming_tasks:
            for task in upcoming_tasks:
                formatted_tasks.append({
                    'id': task['id'],
                    'title': f"Patient Visit - {task['first_name']} {task['last_name']}",
                    'description': task['chief_complaint'] or 'Scheduled visit',
                    'dueDate': f"{task['visit_date']}T{task['visit_time'] or '09:00:00'}Z" if task['visit_date'] else datetime.now().isoformat(),
                    'priority': 'medium',
                    'type': 'visit'
                })
        
        # Role-specific metrics
        role_metrics = {
            'metricType': 'clinical',
            'patientsToday': stats['todaysAppointments'],
            'averageWaitTime': 15,  # Could calculate from actual data
            'completionRate': round((stats['completedVisits'] / max(stats['todaysAppointments'], 1)) * 100, 1)
        }
        
        dashboard_data = {
            'totalPatients': stats['totalPatients'],
            'todaysAppointments': stats['todaysAppointments'],
            'pendingTasks': stats['pendingTasks'],
            'completedVisits': stats['completedVisits'],
            'upcomingTasks': formatted_tasks,
            'recentActivity': formatted_activity,
            'roleSpecificMetrics': role_metrics
        }
        
        return jsonify({
            'success': True,
            'data': dashboard_data
        })
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    """Get users from database"""
    try:
        users = DatabaseManager.execute_query("""
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.phone_number,
                u.is_active,
                r.role_name
            FROM users u
            LEFT JOIN user_roles r ON u.role_id = r.id
            ORDER BY u.created_at DESC
        """, fetch=True)
        
        # Format users for frontend
        formatted_users = []
        if users:
            for user in users:
                formatted_users.append({
                    'id': user['id'],
                    'email': user['email'],
                    'first_name': user['first_name'],
                    'last_name': user['last_name'],
                    'phone_number': user['phone_number'],
                    'role_name': user['role_name'],
                    'role': user['role_name'],  # Frontend compatibility
                    'is_active': user['is_active']
                })
        
        return jsonify({
            'success': True,
            'data': formatted_users
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
        
        # Get fresh user data from database
        user_data = DatabaseManager.execute_query("""
            SELECT 
                u.id,
                u.email,
                u.first_name,
                u.last_name,
                u.phone_number,
                u.is_active,
                r.role_name
            FROM users u
            LEFT JOIN user_roles r ON u.role_id = r.id
            WHERE u.email = %s AND u.is_active = TRUE
        """, (payload['email'],), fetch=True)
        
        if not user_data:
            return jsonify({'success': False, 'error': 'User not found'}), 404
        
        user = user_data[0]
        formatted_user = {
            'id': user['id'],
            'email': user['email'],
            'first_name': user['first_name'],
            'last_name': user['last_name'],
            'phone_number': user['phone_number'],
            'role_name': user['role_name'],
            'role': user['role_name'],  # Frontend compatibility
            'is_active': user['is_active']
        }
        
        return jsonify({
            'success': True,
            'data': formatted_user
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'error': 'Token has expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting POLMED Backend Server with Database...")
    print("Available at: http://localhost:5000")
    print("Database:", DB_CONFIG['host'])
    app.run(host='0.0.0.0', port=5000, debug=True)