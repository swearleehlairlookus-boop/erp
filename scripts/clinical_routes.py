"""
POLMED Backend - Clinical Workflow Routes
Patient visits, vital signs, clinical notes, prescriptions, and referrals
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone
from auth import require_auth, require_role
from database import get_db_connection
import mysql.connector
import json

clinical_bp = Blueprint('clinical', __name__, url_prefix='/api')

# ============================================================================
# VISIT MANAGEMENT
# ============================================================================

@clinical_bp.route('/patients/<int:patient_id>/visits', methods=['GET'])
@require_auth
def get_patient_visits(patient_id):
    """
    Get all visits for a patient
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Verify patient exists
        cursor.execute("SELECT id FROM patients WHERE id = %s AND is_active = TRUE", (patient_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Get visits
        cursor.execute(
            """
            SELECT * FROM patient_visits
            WHERE patient_id = %s AND is_active = TRUE
            ORDER BY visit_date DESC
            LIMIT %s OFFSET %s
            """,
            (patient_id, per_page, offset)
        )
        
        visits = cursor.fetchall()
        
        # Get total count
        cursor.execute(
            "SELECT COUNT(*) as total FROM patient_visits WHERE patient_id = %s AND is_active = TRUE",
            (patient_id,)
        )
        
        total = cursor.fetchone()['total']
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': visits,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@clinical_bp.route('/patients/<int:patient_id>/visits', methods=['POST'])
@require_role('doctor', 'nurse', 'administrator')
def create_visit(patient_id):
    """
    Create new patient visit
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        # Validate required fields
        required_fields = ['visit_date', 'visit_type', 'chief_complaint']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify patient exists
        cursor.execute("SELECT id FROM patients WHERE id = %s AND is_active = TRUE", (patient_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Create visit
        visit_stage = 'registration'
        cursor.execute(
            """
            INSERT INTO patient_visits (
                patient_id, visit_date, visit_time, visit_type, chief_complaint,
                current_stage, route_id, location_id, created_by_id, created_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (
                patient_id,
                data.get('visit_date'),
                data.get('visit_time', '09:00'),
                data.get('visit_type'),
                data.get('chief_complaint'),
                visit_stage,
                data.get('route_id'),
                data.get('location_id'),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        visit_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, table_name, record_id, created_at, new_values)
            VALUES (%s, 'CREATE', 'visit', %s, %s, %s)
            """,
            (request.user_id, visit_id, datetime.now(timezone.utc), json.dumps({'info': f'Created visit for patient {patient_id}'}) )
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Visit created successfully',
            'data': {'visit_id': visit_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@clinical_bp.route('/visits/<int:visit_id>', methods=['GET'])
@require_auth
def get_visit_details(visit_id):
    """
    Get complete visit details including vital signs and notes
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get visit
        cursor.execute(
            "SELECT * FROM patient_visits WHERE id = %s AND is_active = TRUE",
            (visit_id,)
        )
        
        visit = cursor.fetchone()
        
        if not visit:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Visit not found'}), 404
        
        # Get vital signs
        cursor.execute(
            "SELECT * FROM vital_signs WHERE visit_id = %s ORDER BY recorded_at DESC",
            (visit_id,)
        )
        vital_signs = cursor.fetchall()
        
        # Get clinical notes
        cursor.execute(
            "SELECT * FROM clinical_notes WHERE visit_id = %s ORDER BY created_at DESC",
            (visit_id,)
        )
        clinical_notes = cursor.fetchall()
        
        # Get prescriptions
        cursor.execute(
            "SELECT * FROM prescriptions WHERE visit_id = %s AND is_active = TRUE ORDER BY created_at DESC",
            (visit_id,)
        )
        prescriptions = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        visit['vital_signs'] = vital_signs
        visit['clinical_notes'] = clinical_notes
        visit['prescriptions'] = prescriptions
        
        return jsonify({'success': True, 'data': visit}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@clinical_bp.route('/visits/<int:visit_id>/update-stage', methods=['PUT'])
@require_role('doctor', 'nurse', 'administrator')
def update_visit_stage(visit_id):
    """
    Update visit stage in the clinical workflow
    Valid stages: registration, assessment, consultation, counseling, closure
    """
    try:
        data = request.get_json()
        
        if not data or 'new_stage' not in data:
            return jsonify({'success': False, 'error': 'new_stage is required'}), 400
        
        valid_stages = ['registration', 'assessment', 'consultation', 'counseling', 'closure']
        new_stage = data.get('new_stage')
        
        if new_stage not in valid_stages:
            return jsonify({'success': False, 'error': f'Invalid stage. Must be one of: {", ".join(valid_stages)}'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Update stage
        cursor.execute(
            """
            UPDATE patient_visits
            SET current_stage = %s, updated_at = %s
            WHERE id = %s AND is_active = TRUE
            """,
            (new_stage, datetime.now(timezone.utc), visit_id)
        )
        
        if cursor.rowcount == 0:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Visit not found'}), 404
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, table_name, record_id, created_at, new_values)
            VALUES (%s, 'UPDATE', 'visit', %s, %s, %s)
            """,
            (request.user_id, visit_id, datetime.now(timezone.utc), json.dumps({'info': f'Visit stage updated to: {new_stage}'}) )
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Visit stage updated to {new_stage}'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# VITAL SIGNS
# ============================================================================

@clinical_bp.route('/visits/<int:visit_id>/vital-signs', methods=['POST'])
@require_role('nurse', 'doctor', 'administrator')
def record_vital_signs(visit_id):
    """
    Record vital signs for a visit
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'Request body required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify visit exists
        cursor.execute(
            "SELECT id FROM patient_visits WHERE id = %s AND is_active = TRUE",
            (visit_id,)
        )
        
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Visit not found'}), 404
        
        # Record vital signs
        cursor.execute(
            """
            INSERT INTO vital_signs (
                visit_id, systolic_bp, diastolic_bp, heart_rate, temperature,
                weight, height, oxygen_saturation, blood_glucose, nursing_notes,
                recorded_by_id, recorded_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                visit_id,
                data.get('systolic_bp'),
                data.get('diastolic_bp'),
                data.get('heart_rate'),
                data.get('temperature'),
                data.get('weight'),
                data.get('height'),
                data.get('oxygen_saturation'),
                data.get('blood_glucose'),
                data.get('nursing_notes'),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'vital_signs', %s, %s, %s)
            """,
            (request.user_id, cursor.lastrowid, datetime.now(timezone.utc), f'Recorded vital signs for visit {visit_id}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Vital signs recorded successfully'
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CLINICAL NOTES
# ============================================================================

@clinical_bp.route('/visits/<int:visit_id>/clinical-notes', methods=['POST'])
@require_role('doctor', 'nurse', 'administrator')
def create_clinical_note(visit_id):
    """
    Create clinical note for a visit
    """
    try:
        data = request.get_json()
        
        if not data or 'note_content' not in data:
            return jsonify({'success': False, 'error': 'note_content is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify visit exists
        cursor.execute(
            "SELECT id FROM patient_visits WHERE id = %s AND is_active = TRUE",
            (visit_id,)
        )
        
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Visit not found'}), 404
        
        # Create note
        cursor.execute(
            """
            INSERT INTO clinical_notes (
                visit_id, note_content, note_type, icd10_codes, created_by_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (
                visit_id,
                data.get('note_content'),
                data.get('note_type', 'general'),
                ','.join(data.get('icd10_codes', [])) if data.get('icd10_codes') else None,
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        note_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'clinical_note', %s, %s, %s)
            """,
            (request.user_id, note_id, datetime.now(timezone.utc), f'Created clinical note for visit {visit_id}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Clinical note created successfully',
            'data': {'note_id': note_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# PRESCRIPTIONS
# ============================================================================

@clinical_bp.route('/visits/<int:visit_id>/prescriptions', methods=['POST'])
@require_role('doctor', 'administrator')
def create_prescription(visit_id):
    """
    Create prescription for a visit
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['drug_id', 'quantity', 'frequency', 'duration_days']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify visit exists
        cursor.execute(
            "SELECT id FROM patient_visits WHERE id = %s AND is_active = TRUE",
            (visit_id,)
        )
        
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Visit not found'}), 404
        
        # Create prescription
        cursor.execute(
            """
            INSERT INTO prescriptions (
                visit_id, drug_id, quantity, frequency, duration_days,
                special_instructions, created_by_id, created_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, TRUE)
            """,
            (
                visit_id,
                data.get('drug_id'),
                data.get('quantity'),
                data.get('frequency'),
                data.get('duration_days'),
                data.get('special_instructions', ''),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        prescription_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'prescription', %s, %s, %s)
            """,
            (request.user_id, prescription_id, datetime.now(timezone.utc), f'Created prescription for visit {visit_id}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Prescription created successfully',
            'data': {'prescription_id': prescription_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# REFERRALS
# ============================================================================

@clinical_bp.route('/patients/<int:patient_id>/referrals', methods=['GET'])
@require_auth
def get_patient_referrals(patient_id):
    """
    Get all referrals for a patient
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Verify patient exists
        cursor.execute("SELECT id FROM patients WHERE id = %s AND is_active = TRUE", (patient_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Get referrals
        cursor.execute(
            """
            SELECT * FROM referrals
            WHERE patient_id = %s AND is_active = TRUE
            ORDER BY created_at DESC
            """,
            (patient_id,)
        )
        
        referrals = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({'success': True, 'data': referrals}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@clinical_bp.route('/patients/<int:patient_id>/referrals', methods=['POST'])
@require_role('doctor', 'nurse', 'social_worker', 'administrator')
def create_referral(patient_id):
    """
    Create referral for patient
    """
    try:
        data = request.get_json()
        
        if not data or 'referral_type' not in data:
            return jsonify({'success': False, 'error': 'referral_type is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Verify patient exists
        cursor.execute("SELECT id FROM patients WHERE id = %s AND is_active = TRUE", (patient_id,))
        if not cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Patient not found'}), 404
        
        # Create referral
        cursor.execute(
            """
            INSERT INTO referrals (
                patient_id, referral_type, from_stage, to_stage, external_provider,
                department, reason, urgency, appointment_date, referral_status,
                created_by_id, created_at, is_active
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'pending', %s, %s, TRUE)
            """,
            (
                patient_id,
                data.get('referral_type'),
                data.get('from_stage'),
                data.get('to_stage'),
                data.get('external_provider'),
                data.get('department'),
                data.get('reason'),
                data.get('urgency', 'routine'),
                data.get('appointment_date'),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        referral_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'referral', %s, %s, %s)
            """,
            (request.user_id, referral_id, datetime.now(timezone.utc), f'Created referral for patient {patient_id}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Referral created successfully',
            'data': {'referral_id': referral_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@clinical_bp.route('/referrals/<int:referral_id>/status', methods=['PUT'])
@require_role('doctor', 'social_worker', 'administrator')
def update_referral_status(referral_id):
    """
    Update referral status
    Valid statuses: pending, approved, rejected, completed
    """
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'status is required'}), 400
        
        valid_statuses = ['pending', 'approved', 'rejected', 'completed']
        new_status = data.get('status')
        
        if new_status not in valid_statuses:
            return jsonify({'success': False, 'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        cursor.execute(
            """
            UPDATE referrals
            SET referral_status = %s, updated_at = %s
            WHERE id = %s AND is_active = TRUE
            """,
            (new_status, datetime.now(timezone.utc), referral_id)
        )
        
        if cursor.rowcount == 0:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Referral not found'}), 404
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'UPDATE', 'referral', %s, %s, %s)
            """,
            (request.user_id, referral_id, datetime.now(timezone.utc), f'Referral status updated to: {new_status}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Referral status updated to {new_status}'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
