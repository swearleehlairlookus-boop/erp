"""
POLMED Backend - Routes & Appointment Management
Clinic scheduling, location management, appointment booking, and availability
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from auth import require_auth, require_role
from database import get_db_connection
import uuid
import json

routes_bp = Blueprint('routes', __name__, url_prefix='/api/routes')
appointments_bp = Blueprint('appointments', __name__, url_prefix='/api/appointments')

# ============================================================================
# ROUTE MANAGEMENT
# ============================================================================

@routes_bp.route('', methods=['GET'])
@require_auth
def get_routes():
    """
    Get paginated list of clinic routes
    Query params: page, per_page, province, is_active
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        province = request.args.get('province', '').strip()
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM routes WHERE is_active = %s"
        count_query = "SELECT COUNT(*) as total FROM routes WHERE is_active = %s"
        params = [is_active]
        
        if province:
            query += " AND province = %s"
            count_query += " AND province = %s"
            params.append(province)
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY start_date DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [per_page, offset])
        routes = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': routes,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@routes_bp.route('', methods=['POST'])
@require_role('administrator', 'inventory_manager')
def create_route():
    """
    Create new clinic route
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['route_name', 'province', 'start_date', 'end_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Create route
        cursor.execute(
            """
            INSERT INTO routes (
                route_name, description, province, route_type, start_date, end_date,
                start_time, end_time, max_appointments_per_day, is_active,
                created_by_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
            """,
            (
                data.get('route_name'),
                data.get('description', ''),
                data.get('province'),
                data.get('route_type', 'mobile_clinic'),
                data.get('start_date'),
                data.get('end_date'),
                data.get('start_time', '08:00'),
                data.get('end_time', '17:00'),
                data.get('max_appointments_per_day', 50),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        route_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, table_name, record_id, created_at, new_values)
            VALUES (%s, 'CREATE', 'route', %s, %s, %s)
            """,
            (request.user_id, route_id, datetime.now(timezone.utc), json.dumps({'info': f'Created route: {data.get("route_name")}'}) )
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Route created successfully',
            'data': {'route_id': route_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@routes_bp.route('/<int:route_id>/locations', methods=['GET'])
@require_auth
def get_route_locations(route_id):
    """
    Get all locations for a specific route
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Verify route exists
        cursor.execute("SELECT id FROM routes WHERE id = %s AND is_active = TRUE", (route_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Route not found'}), 404
        
        # Get locations
        cursor.execute(
            """
            SELECT * FROM locations
            WHERE route_id = %s AND is_active = TRUE
            ORDER BY visit_sequence ASC
            """,
            (route_id,)
        )
        
        locations = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({'success': True, 'data': locations}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@routes_bp.route('/<int:route_id>/locations', methods=['POST'])
@require_role('administrator', 'inventory_manager')
def add_location_to_route(route_id):
    """
    Add location to a route
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['location_name', 'location_type', 'visit_date']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify route exists
        cursor.execute("SELECT id FROM routes WHERE id = %s AND is_active = TRUE", (route_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Route not found'}), 404
        
        # Add location
        cursor.execute(
            """
            INSERT INTO locations (
                route_id, location_name, location_type, address, province,
                visit_date, visit_sequence, max_appointments, is_active, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE, %s)
            """,
            (
                route_id,
                data.get('location_name'),
                data.get('location_type'),
                data.get('address', ''),
                data.get('province', ''),
                data.get('visit_date'),
                data.get('visit_sequence', 1),
                data.get('max_appointments', 50),
                datetime.now(timezone.utc)
            )
        )
        
        location_id = cursor.lastrowid
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Location added to route successfully',
            'data': {'location_id': location_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# APPOINTMENT MANAGEMENT
# ============================================================================

@appointments_bp.route('/available', methods=['GET'])
def get_available_appointments():
    """
    Get available appointment slots (public endpoint)
    Query params: province, date_from, date_to, location_type
    """
    try:
        province = request.args.get('province', '').strip()
        date_from = request.args.get('date_from', '').strip()
        date_to = request.args.get('date_to', '').strip()
        location_type = request.args.get('location_type', '').strip()
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Build query
        query = """
            SELECT
                l.id as location_id,
                l.location_name,
                l.location_type,
                l.address,
                l.visit_date,
                r.route_name,
                r.province,
                (l.max_appointments - COUNT(a.id)) as available_slots,
                l.max_appointments
            FROM locations l
            JOIN routes r ON l.route_id = r.id
            LEFT JOIN appointments a ON l.id = a.location_id AND a.appointment_status IN ('confirmed', 'pending')
            WHERE l.is_active = TRUE
                AND r.is_active = TRUE
                AND l.visit_date >= CURDATE()
        """
        
        params = []
        
        if province:
            query += " AND r.province = %s"
            params.append(province)
        
        if date_from:
            query += " AND l.visit_date >= %s"
            params.append(date_from)
        
        if date_to:
            query += " AND l.visit_date <= %s"
            params.append(date_to)
        
        if location_type:
            query += " AND l.location_type = %s"
            params.append(location_type)
        
        query += " GROUP BY l.id, r.id HAVING available_slots > 0 ORDER BY l.visit_date ASC"
        
        cursor.execute(query, params)
        appointments = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': appointments,
            'summary': {
                'total_available': len(appointments)
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@appointments_bp.route('', methods=['POST'])
def book_appointment():
    """
    Book appointment (public endpoint for patients)
    Required: location_id, first_name, last_name, phone_number, medical_aid_number
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['location_id', 'first_name', 'last_name', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Verify location exists and has available slots
        cursor.execute(
            """
            SELECT
                l.*,
                (l.max_appointments - COUNT(a.id)) as available_slots
            FROM locations l
            LEFT JOIN appointments a ON l.id = a.location_id AND a.appointment_status IN ('confirmed', 'pending')
            WHERE l.id = %s AND l.is_active = TRUE
            GROUP BY l.id
            """,
            (data.get('location_id'),)
        )
        
        location = cursor.fetchone()
        
        if not location:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Location not found'}), 404
        
        if location['available_slots'] <= 0:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'No available slots at this location'}), 409
        
        # Generate booking reference
        booking_reference = f"APT-{datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        
        # Create appointment
        cursor.execute(
            """
            INSERT INTO appointments (
                location_id, booking_reference, first_name, last_name, phone_number,
                medical_aid_number, appointment_status, appointment_date, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, 'confirmed', %s, %s)
            """,
            (
                data.get('location_id'),
                booking_reference,
                data.get('first_name'),
                data.get('last_name'),
                data.get('phone_number'),
                data.get('medical_aid_number', ''),
                location['visit_date'],
                datetime.now(timezone.utc)
            )
        )
        
        appointment_id = cursor.lastrowid
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Appointment booked successfully',
            'data': {
                'appointment_id': appointment_id,
                'booking_reference': booking_reference,
                'appointment_date': str(location['visit_date']),
                'location': location['location_name']
            }
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@appointments_bp.route('/<booking_reference>', methods=['GET'])
def get_appointment_by_reference(booking_reference):
    """
    Get appointment details by booking reference (public endpoint)
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT
                a.*,
                l.location_name,
                l.location_type,
                l.address,
                r.route_name,
                r.start_time,
                r.end_time
            FROM appointments a
            JOIN locations l ON a.location_id = l.id
            JOIN routes r ON l.route_id = r.id
            WHERE a.booking_reference = %s
            """,
            (booking_reference,)
        )
        
        appointment = cursor.fetchone()
        cursor.close()
        db_conn.close()
        
        if not appointment:
            return jsonify({'success': False, 'error': 'Appointment not found'}), 404
        
        return jsonify({'success': True, 'data': appointment}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@appointments_bp.route('/<int:appointment_id>/cancel', methods=['POST'])
@require_auth
def cancel_appointment(appointment_id):
    """
    Cancel appointment
    """
    try:
        data = request.get_json() or {}
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Update appointment status
        cursor.execute(
            """
            UPDATE appointments
            SET appointment_status = 'cancelled', cancellation_reason = %s, updated_at = %s
            WHERE id = %s
            """,
            (data.get('cancellation_reason', ''), datetime.now(timezone.utc), appointment_id)
        )
        
        if cursor.rowcount == 0:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Appointment not found'}), 404
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Appointment cancelled successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# DASHBOARD STATISTICS
# ============================================================================

@appointments_bp.route('/stats/today', methods=['GET'])
@require_auth
def get_today_appointment_stats():
    """
    Get appointment statistics for today
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get today's appointment counts
        today = datetime.now().date()
        
        cursor.execute(
            """
            SELECT
                SUM(CASE WHEN a.appointment_status = 'confirmed' THEN 1 ELSE 0 END) as confirmed,
                SUM(CASE WHEN a.appointment_status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN a.appointment_status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN a.appointment_status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                COUNT(*) as total
            FROM appointments a
            JOIN locations l ON a.location_id = l.id
            WHERE l.visit_date = %s
            """,
            (today,)
        )
        
        stats = cursor.fetchone()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {
                'date': str(today),
                'confirmed': stats.get('confirmed') or 0,
                'pending': stats.get('pending') or 0,
                'completed': stats.get('completed') or 0,
                'cancelled': stats.get('cancelled') or 0,
                'total': stats.get('total') or 0
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
