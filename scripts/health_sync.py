"""
POLMED Backend - Health Checks and PALMED Sync
System health monitoring and PALMED medical aid synchronization
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from auth import require_auth, require_role
from database import get_db_connection
import os

health_bp = Blueprint('health', __name__, url_prefix='/api/health')
sync_bp = Blueprint('sync', __name__, url_prefix='/api/sync')

# ============================================================================
# HEALTH CHECKS
# ============================================================================

@health_bp.route('', methods=['GET'])
def health_check():
    """
    Basic health check endpoint (public)
    Returns system status and version
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '2.0.0',
            'environment': os.environ.get('FLASK_ENV', 'production')
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@health_bp.route('/detailed', methods=['GET'])
@require_role('administrator')
def detailed_health_check():
    """
    Detailed health check with database and service status
    Requires admin role
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        health_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '2.0.0',
            'checks': {}
        }
        
        # 1. Database connectivity
        try:
            cursor.execute("SELECT 1")
            cursor.fetchone()
            health_data['checks']['database'] = {
                'status': 'healthy',
                'message': 'Database connection successful'
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'unhealthy',
                'message': f'Database error: {str(e)}'
            }
        
        # 2. Database tables
        try:
            cursor.execute("""
                SELECT COUNT(*) as table_count
                FROM information_schema.tables
                WHERE table_schema = DATABASE()
            """)
            result = cursor.fetchone()
            table_count = result['table_count']
            
            health_data['checks']['tables'] = {
                'status': 'healthy' if table_count >= 13 else 'degraded',
                'tables_found': table_count,
                'expected': 13
            }
        except Exception as e:
            health_data['checks']['tables'] = {
                'status': 'unhealthy',
                'message': f'Error checking tables: {str(e)}'
            }
        
        # 3. User count
        try:
            cursor.execute("SELECT COUNT(*) as count FROM users WHERE is_active = TRUE")
            result = cursor.fetchone()
            active_users = result['count']
            
            health_data['checks']['users'] = {
                'status': 'healthy',
                'active_users': active_users
            }
        except Exception as e:
            health_data['checks']['users'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # 4. Patient data
        try:
            cursor.execute("SELECT COUNT(*) as count FROM patients WHERE is_active = TRUE")
            result = cursor.fetchone()
            patient_count = result['count']
            
            health_data['checks']['patients'] = {
                'status': 'healthy',
                'total': patient_count
            }
        except Exception as e:
            health_data['checks']['patients'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # 5. Active routes
        try:
            cursor.execute("SELECT COUNT(*) as count FROM routes WHERE is_active = TRUE")
            result = cursor.fetchone()
            route_count = result['count']
            
            health_data['checks']['routes'] = {
                'status': 'healthy',
                'active_routes': route_count
            }
        except Exception as e:
            health_data['checks']['routes'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # 6. Pending referrals
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM referrals
                WHERE referral_status = 'pending' AND is_active = TRUE
            """)
            result = cursor.fetchone()
            pending_referrals = result['count']
            
            health_data['checks']['referrals'] = {
                'status': 'healthy',
                'pending': pending_referrals
            }
        except Exception as e:
            health_data['checks']['referrals'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # 7. Low stock alerts
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM inventory_stock s
                JOIN consumables c ON s.consumable_id = c.id
                WHERE s.is_active = TRUE AND s.quantity_current <= c.reorder_level
            """)
            result = cursor.fetchone()
            low_stock_count = result['count']
            
            health_data['checks']['inventory'] = {
                'status': 'healthy' if low_stock_count < 5 else 'warning',
                'low_stock_alerts': low_stock_count
            }
        except Exception as e:
            health_data['checks']['inventory'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        # 8. Audit log
        try:
            cursor.execute("""
                SELECT COUNT(*) as count FROM audit_log
                WHERE timestamp >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """)
            result = cursor.fetchone()
            audit_count = result['count']
            
            health_data['checks']['audit'] = {
                'status': 'healthy',
                'events_24h': audit_count
            }
        except Exception as e:
            health_data['checks']['audit'] = {
                'status': 'unhealthy',
                'message': str(e)
            }
        
        cursor.close()
        db_conn.close()
        
        # Determine overall status
        statuses = [check.get('status') for check in health_data['checks'].values()]
        if 'unhealthy' in statuses:
            overall_status = 'unhealthy'
        elif 'warning' in statuses:
            overall_status = 'warning'
        else:
            overall_status = 'healthy'
        
        health_data['overall_status'] = overall_status
        
        return jsonify({
            'success': True,
            'data': health_data
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }), 503

@health_bp.route('/database', methods=['GET'])
@require_role('administrator')
def database_health():
    """
    Check database health metrics
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        metrics = {}
        
        # Database size
        cursor.execute(f"""
            SELECT
                ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) as size_mb
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
        """)
        result = cursor.fetchone()
        metrics['database_size_mb'] = result['size_mb']
        
        # Active connections
        cursor.execute("SHOW STATUS LIKE 'Threads_connected'")
        result = cursor.fetchone()
        metrics['active_connections'] = result['Value'] if result else 0
        
        # Table row counts
        cursor.execute("""
            SELECT
                TABLE_NAME,
                TABLE_ROWS
            FROM information_schema.tables
            WHERE table_schema = DATABASE()
            ORDER BY TABLE_ROWS DESC
        """)
        
        metrics['tables'] = {}
        for row in cursor.fetchall():
            metrics['tables'][row['TABLE_NAME']] = row['TABLE_ROWS']
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': metrics
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 503

# ============================================================================
# PALMED SYNCHRONIZATION
# ============================================================================

@sync_bp.route('/palmed-members', methods=['GET'])
@require_role('administrator', 'doctor', 'clerk')
def sync_palmed_members():
    """
    Sync PALMED medical aid members
    This endpoint would integrate with PALMED API for member verification
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get patients with PALMED medical aid
        cursor.execute("""
            SELECT
                id,
                medical_aid_number,
                first_name,
                last_name,
                phone_number,
                email,
                is_palmed_member,
                created_at
            FROM patients
            WHERE is_palmed_member = TRUE AND is_active = TRUE
            ORDER BY created_at DESC
            LIMIT 100
        """)
        
        palmed_members = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'members': palmed_members,
                'total_count': len(palmed_members),
                'sync_timestamp': datetime.now(timezone.utc).isoformat(),
                'note': 'Integration with actual PALMED API required for live verification'
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/patient-visits', methods=['POST'])
@require_role('administrator', 'doctor')
def sync_patient_visits():
    """
    Sync patient visits to external system
    Useful for reporting and analytics
    """
    try:
        data = request.get_json() or {}
        
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        
        if not date_from or not date_to:
            return jsonify({
                'success': False,
                'error': 'date_from and date_to are required'
            }), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get visits in date range
        cursor.execute("""
            SELECT
                pv.id,
                pv.patient_id,
                p.first_name,
                p.last_name,
                p.medical_aid_number,
                pv.visit_date,
                pv.visit_type,
                pv.chief_complaint,
                pv.current_stage,
                r.route_name,
                l.location_name
            FROM patient_visits pv
            JOIN patients p ON pv.patient_id = p.id
            LEFT JOIN routes r ON pv.route_id = r.id
            LEFT JOIN locations l ON pv.location_id = l.id
            WHERE pv.visit_date BETWEEN %s AND %s
            ORDER BY pv.visit_date DESC
        """, (date_from, date_to))
        
        visits = cursor.fetchall()
        
        # Log sync
        cursor.execute("""
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'SYNC', 'visits', 0, %s, %s)
        """, (request.user_id, datetime.now(timezone.utc), f'Synced {len(visits)} visits'))
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'visits': visits,
                'total_count': len(visits),
                'date_range': {
                    'from': date_from,
                    'to': date_to
                },
                'sync_timestamp': datetime.now(timezone.utc).isoformat()
            }
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/dashboard-stats', methods=['GET'])
@require_auth
def get_dashboard_stats():
    """
    Get comprehensive dashboard statistics
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        stats = {
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Today's stats
        today = datetime.now().date()
        
        cursor.execute("""
            SELECT COUNT(*) as count FROM patient_visits
            WHERE visit_date = %s AND is_active = TRUE
        """, (today,))
        stats['today_patients'] = cursor.fetchone()['count']
        
        # Active routes
        cursor.execute("""
            SELECT COUNT(*) as count FROM routes
            WHERE is_active = TRUE AND end_date >= CURDATE()
        """)
        stats['active_routes'] = cursor.fetchone()['count']
        
        # Pending referrals
        cursor.execute("""
            SELECT COUNT(*) as count FROM referrals
            WHERE referral_status = 'pending' AND is_active = TRUE
        """)
        stats['pending_referrals'] = cursor.fetchone()['count']
        
        # Pending appointments
        cursor.execute("""
            SELECT COUNT(*) as count FROM appointments
            WHERE appointment_status = 'pending' AND appointment_date >= CURDATE()
        """)
        stats['pending_appointments'] = cursor.fetchone()['count']
        
        # Low stock alerts
        cursor.execute("""
            SELECT COUNT(*) as count FROM inventory_stock s
            JOIN consumables c ON s.consumable_id = c.id
            WHERE s.is_active = TRUE AND s.quantity_current <= c.reorder_level
        """)
        stats['low_stock_alerts'] = cursor.fetchone()['count']
        
        # Expiry alerts (next 30 days)
        cursor.execute("""
            SELECT COUNT(*) as count FROM inventory_stock
            WHERE is_active = TRUE
                AND expiry_date IS NOT NULL
                AND expiry_date <= DATE_ADD(NOW(), INTERVAL 30 DAY)
                AND expiry_date > NOW()
        """)
        stats['expiry_alerts'] = cursor.fetchone()['count']
        
        # Total active patients
        cursor.execute("""
            SELECT COUNT(*) as count FROM patients WHERE is_active = TRUE
        """)
        stats['total_patients'] = cursor.fetchone()['count']
        
        # Active users
        cursor.execute("""
            SELECT COUNT(*) as count FROM users WHERE is_active = TRUE
        """)
        stats['active_users'] = cursor.fetchone()['count']
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': stats
        }), 200
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
