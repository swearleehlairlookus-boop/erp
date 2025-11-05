"""
POLMED Backend - Patient Management Routes
Patient registration, retrieval, and profile management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from auth import require_auth, require_role
from database import get_db_connection
import mysql.connector
import json

patients_bp = Blueprint('patients', __name__, url_prefix='/api/patients')

@patients_bp.route('', methods=['GET'])
@require_auth
def get_patients():
    """
    Get paginated list of patients with optional search
    Query params: page, per_page, search, province
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        search = request.args.get('search', '').strip()
        province = request.args.get('province', '').strip()
        
        if page < 1 or per_page < 1 or per_page > 100:
            return jsonify({'success': False, 'error': 'Invalid pagination parameters'}), 400
        
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM patients WHERE is_active = TRUE"
        count_query = "SELECT COUNT(*) as total FROM patients WHERE is_active = TRUE"
        params = []
        
        if search:
            search_term = f"%{search}%"
            query += " AND (first_name LIKE %s OR last_name LIKE %s OR medical_aid_number LIKE %s OR phone_number LIKE %s)"
            count_query += " AND (first_name LIKE %s OR last_name LIKE %s OR medical_aid_number LIKE %s OR phone_number LIKE %s)"
            params = [search_term, search_term, search_term, search_term]
        
        if province:
            query += " AND province = %s"
            count_query += " AND province = %s"
            params.append(province)
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [per_page, offset])
        patients = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': patients,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@patients_bp.route('', methods=['POST'])
@require_role('doctor', 'nurse', 'clerk', 'administrator')
def create_patient():
    """
    Create new patient
    Required: first_name, last_name, date_of_birth, gender, phone_number
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['first_name', 'last_name', 'date_of_birth', 'gender', 'phone_number']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Extract data
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        date_of_birth = data.get('date_of_birth')
        gender = data.get('gender')
        phone_number = data.get('phone_number', '').strip()
        email = data.get('email', '').strip().lower() if data.get('email') else None
        medical_aid_number = data.get('medical_aid_number', '').strip()
        province = data.get('province', 'Not Specified')
        physical_address = data.get('physical_address', '').strip()
        is_palmed_member = data.get('is_palmed_member', False)
        chronic_conditions = data.get('chronic_conditions', [])
        allergies = data.get('allergies', [])
        current_medications = data.get('current_medications', [])
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Check if patient already exists (by medical aid or phone)
        cursor.execute(
            "SELECT id FROM patients WHERE medical_aid_number = %s AND is_active = TRUE",
            (medical_aid_number,)
        )
        
        if cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({
                'success': False,
                'error': 'Patient with this medical aid number already exists'
            }), 409
        
        # Insert patient
        cursor.execute(
            """
            INSERT INTO patients (
                first_name, last_name, date_of_birth, gender, phone_number, email,
                medical_aid_number, province, physical_address, is_palmed_member,
                chronic_conditions, allergies, current_medications, created_by_id,
                created_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (
                first_name, last_name, date_of_birth, gender, phone_number, email,
                medical_aid_number, province, physical_address, is_palmed_member,
                ','.join(chronic_conditions) if chronic_conditions else None,
                ','.join(allergies) if allergies else None,
                ','.join(current_medications) if current_medications else None,
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        patient_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, table_name, record_id, created_at, new_values)
            VALUES (%s, 'CREATE', 'patient', %s, %s, %s)
            """,
            (request.user_id, patient_id, datetime.now(timezone.utc), json.dumps({'info': f'Created patient: {first_name} {last_name}'}) )
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Patient created successfully',
            'data': {'patient_id': patient_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@patients_bp.route('/<int:patient_id>', methods=['GET'])
@require_auth
def get_patient(patient_id):
    """
    Get patient details by ID
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT * FROM patients WHERE id = %s AND is_active = TRUE
            """,
            (patient_id,)
        )
        
        patient = cursor.fetchone()
        cursor.close()
        db_conn.close()
        
        if not patient:
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Parse arrays
        if patient.get('chronic_conditions'):
            patient['chronic_conditions'] = patient['chronic_conditions'].split(',')
        if patient.get('allergies'):
            patient['allergies'] = patient['allergies'].split(',')
        if patient.get('current_medications'):
            patient['current_medications'] = patient['current_medications'].split(',')
        
        return jsonify({'success': True, 'data': patient}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@patients_bp.route('/<int:patient_id>', methods=['PUT'])
@require_role('doctor', 'nurse', 'clerk', 'administrator')
def update_patient(patient_id):
    """
    Update patient information
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Verify patient exists
        cursor.execute("SELECT id FROM patients WHERE id = %s AND is_active = TRUE", (patient_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Build update query dynamically
        allowed_fields = [
            'phone_number', 'email', 'province', 'physical_address',
            'chronic_conditions', 'allergies', 'current_medications'
        ]
        
        update_parts = []
        params = []
        
        for field in allowed_fields:
            if field in data:
                value = data[field]
                if isinstance(value, list):
                    value = ','.join(value)
                update_parts.append(f"{field} = %s")
                params.append(value)
        
        if not update_parts:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'No valid fields to update'}), 400
        
        # Update patient
        update_parts.append("updated_at = %s")
        params.append(datetime.now(timezone.utc))
        params.append(patient_id)
        
        query = f"UPDATE patients SET {', '.join(update_parts)} WHERE id = %s"
        cursor.execute(query, params)
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'UPDATE', 'patient', %s, %s, %s)
            """,
            (request.user_id, patient_id, datetime.now(timezone.utc), f'Updated patient information')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Patient updated successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@patients_bp.route('/<int:patient_id>/deactivate', methods=['POST'])
@require_role('doctor', 'administrator')
def deactivate_patient(patient_id):
    """
    Deactivate patient account
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        cursor.execute(
            """
            UPDATE patients SET is_active = FALSE, updated_at = %s WHERE id = %s
            """,
            (datetime.now(timezone.utc), patient_id)
        )
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'DEACTIVATE', 'patient', %s, %s, %s)
            """,
            (request.user_id, patient_id, datetime.now(timezone.utc), 'Patient account deactivated')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Patient deactivated successfully'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
