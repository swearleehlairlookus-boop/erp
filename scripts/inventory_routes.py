"""
POLMED Backend - Inventory Management Routes
Asset lifecycle, consumable tracking, stock alerts, and supplier management
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timezone, timedelta
from auth import require_auth, require_role
from database import get_db_connection

inventory_bp = Blueprint('inventory', __name__, url_prefix='/api/inventory')

# ============================================================================
# ASSET MANAGEMENT
# ============================================================================

@inventory_bp.route('/assets', methods=['GET'])
@require_auth
def get_assets():
    """
    Get paginated list of medical assets
    Query params: page, per_page, status, location
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        status = request.args.get('status', '').strip()
        location = request.args.get('location', '').strip()
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Build query
        query = "SELECT * FROM assets WHERE 1=1"
        count_query = "SELECT COUNT(*) as total FROM assets WHERE 1=1"
        params = []
        
        if status:
            query += " AND status = %s"
            count_query += " AND status = %s"
            params.append(status)
        
        if location:
            query += " AND location LIKE %s"
            count_query += " AND location LIKE %s"
            params.append(f"%{location}%")
        
        # Get total count
        cursor.execute(count_query, params)
        total = cursor.fetchone()['total']
        
        # Get paginated results
        query += " ORDER BY created_at DESC LIMIT %s OFFSET %s"
        cursor.execute(query, params + [per_page, offset])
        assets = cursor.fetchall()
        
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': assets,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/assets', methods=['POST'])
@require_role('inventory_manager', 'administrator')
def create_asset():
    """
    Create new medical asset
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['asset_name', 'serial_number', 'manufacturer', 'location']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Check for duplicate serial number
        cursor.execute(
            "SELECT id FROM assets WHERE serial_number = %s",
            (data.get('serial_number'),)
        )
        
        if cursor.fetchone():
            cursor.close()
            db_conn.close()
            return jsonify({
                'success': False,
                'error': 'Asset with this serial number already exists'
            }), 409
        
        # Create asset
        cursor.execute(
            """
            INSERT INTO assets (
                asset_tag, asset_name, serial_number, category_id, manufacturer, model,
                purchase_date, warranty_expiry, location, purchase_cost, status,
                created_by_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                data.get('asset_tag', f"AST-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                data.get('asset_name'),
                data.get('serial_number'),
                data.get('category_id'),
                data.get('manufacturer'),
                data.get('model'),
                data.get('purchase_date'),
                data.get('warranty_expiry'),
                data.get('location'),
                data.get('purchase_cost', 0),
                data.get('status', 'operational'),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        asset_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'asset', %s, %s, %s)
            """,
            (request.user_id, asset_id, datetime.now(timezone.utc), f'Created asset: {data.get("asset_name")}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Asset created successfully',
            'data': {'asset_id': asset_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/assets/<int:asset_id>', methods=['GET'])
@require_auth
def get_asset(asset_id):
    """
    Get asset details
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM assets WHERE id = %s", (asset_id,))
        asset = cursor.fetchone()
        
        if not asset:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        
        # Get usage history
        cursor.execute(
            """
            SELECT * FROM asset_usage_history
            WHERE asset_id = %s
            ORDER BY usage_date DESC
            LIMIT 10
            """,
            (asset_id,)
        )
        
        usage_history = cursor.fetchall()
        asset['usage_history'] = usage_history
        
        cursor.close()
        db_conn.close()
        
        return jsonify({'success': True, 'data': asset}), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/assets/<int:asset_id>/status', methods=['PUT'])
@require_role('inventory_manager', 'administrator')
def update_asset_status(asset_id):
    """
    Update asset status (operational, maintenance, retired, etc.)
    """
    try:
        data = request.get_json()
        
        if not data or 'status' not in data:
            return jsonify({'success': False, 'error': 'status is required'}), 400
        
        valid_statuses = ['operational', 'maintenance', 'retired', 'lost', 'damaged']
        new_status = data.get('status')
        
        if new_status not in valid_statuses:
            return jsonify({
                'success': False,
                'error': f'Invalid status. Must be one of: {", ".join(valid_statuses)}'
            }), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        cursor.execute(
            """
            UPDATE assets
            SET status = %s, updated_at = %s
            WHERE id = %s
            """,
            (new_status, datetime.now(timezone.utc), asset_id)
        )
        
        if cursor.rowcount == 0:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Asset not found'}), 404
        
        # Log usage
        cursor.execute(
            """
            INSERT INTO asset_usage_history (asset_id, usage_date, status_change, notes)
            VALUES (%s, %s, %s, %s)
            """,
            (asset_id, datetime.now(timezone.utc), new_status, data.get('notes', ''))
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Asset status updated to {new_status}'
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CONSUMABLE MANAGEMENT
# ============================================================================

@inventory_bp.route('/consumables', methods=['GET'])
@require_auth
def get_consumables():
    """
    Get paginated list of consumables/medicines
    Query params: page, per_page, status, category
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM consumables WHERE is_active = TRUE")
        total = cursor.fetchone()['total']
        
        # Get paginated results
        cursor.execute(
            """
            SELECT * FROM consumables
            WHERE is_active = TRUE
            ORDER BY item_name ASC
            LIMIT %s OFFSET %s
            """,
            (per_page, offset)
        )
        
        consumables = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': consumables,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/consumables', methods=['POST'])
@require_role('inventory_manager', 'administrator')
def create_consumable():
    """
    Create new consumable/medicine record
    """
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'unit', 'category_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Create consumable
        cursor.execute(
            """
            INSERT INTO consumables (
                name, description, category_id, unit, unit_cost, reorder_level,
                maximum_stock, is_active, created_by_id, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE, %s, %s)
            """,
            (
                data.get('name'),
                data.get('description', ''),
                data.get('category_id'),
                data.get('unit'),
                data.get('unit_cost', 0),
                data.get('reorder_level', 10),
                data.get('maximum_stock', 100),
                request.user_id,
                datetime.now(timezone.utc)
            )
        )
        
        consumable_id = cursor.lastrowid
        
        # Log audit
        cursor.execute(
            """
            INSERT INTO audit_log (user_id, action, entity_type, entity_id, timestamp, details)
            VALUES (%s, 'CREATE', 'consumable', %s, %s, %s)
            """,
            (request.user_id, consumable_id, datetime.now(timezone.utc), f'Created consumable: {data.get("name")}')
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': 'Consumable created successfully',
            'data': {'consumable_id': consumable_id}
        }), 201
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/stock', methods=['GET'])
@require_auth
def get_inventory_stock():
    """
    Get current inventory stock levels
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 20))
        offset = (page - 1) * per_page
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM inventory_stock WHERE status = 'Active'")
        total = cursor.fetchone()['total']
        
        # Get stock with consumable details
        cursor.execute(
            """
            SELECT
                s.*,
                c.item_name,
                c.unit_of_measure,
                c.reorder_level,
                c.max_stock_level
            FROM inventory_stock s
            JOIN consumables c ON s.consumable_id = c.id
            WHERE s.status = 'Active'
            ORDER BY s.updated_at DESC
            LIMIT %s OFFSET %s
            """,
            (per_page, offset)
        )
        
        stock = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': stock,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': (total + per_page - 1) // per_page
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/stock/<int:stock_id>/adjust', methods=['PUT'])
@require_role('inventory_manager', 'administrator')
def adjust_stock(stock_id):
    """
    Adjust stock quantity (add/remove/dispense)
    """
    try:
        data = request.get_json()
        
        if 'adjustment' not in data or 'reason' not in data:
            return jsonify({
                'success': False,
                'error': 'adjustment and reason are required'
            }), 400
        
        adjustment = int(data.get('adjustment'))
        reason = data.get('reason')
        
        if adjustment == 0:
            return jsonify({'success': False, 'error': 'adjustment cannot be zero'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Get current stock
        cursor.execute(
            "SELECT quantity_current FROM inventory_stock WHERE id = %s AND status = 'Active'",
            (stock_id,)
        )
        
        stock = cursor.fetchone()
        
        if not stock:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': 'Stock record not found'}), 404
        
        # Calculate new quantity
        new_quantity = stock['quantity_current'] + adjustment
        
        if new_quantity < 0:
            cursor.close()
            db_conn.close()
            return jsonify({
                'success': False,
                'error': f'Adjustment would result in negative stock. Current: {stock["quantity_current"]}'
            }), 400
        
        # Update stock
        cursor.execute(
            """
            UPDATE inventory_stock
            SET quantity_current = %s, updated_at = %s
            WHERE id = %s
            """,
            (new_quantity, datetime.now(timezone.utc), stock_id)
        )
        
        # Log adjustment
        cursor.execute(
            """
            INSERT INTO stock_adjustment_log (stock_id, adjustment, reason, adjusted_by_id, adjustment_date)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (stock_id, adjustment, reason, request.user_id, datetime.now(timezone.utc))
        )
        
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Stock adjusted by {adjustment}',
            'data': {'new_quantity': new_quantity}
        }), 200
    
    except ValueError:
        return jsonify({'success': False, 'error': 'adjustment must be an integer'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# STOCK ALERTS
# ============================================================================

@inventory_bp.route('/alerts/expiry', methods=['GET'])
@require_auth
def get_expiry_alerts():
    """
    Get consumables expiring within specified days
    Query params: days_ahead (default: 90)
    """
    try:
        days_ahead = int(request.args.get('days_ahead', 90))
        
        if days_ahead < 1:
            return jsonify({'success': False, 'error': 'days_ahead must be positive'}), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        # Calculate expiry cutoff date
        expiry_cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        cursor.execute(
            """
            SELECT
                s.id,
                s.batch_number,
                c.item_name,
                s.expiry_date,
                s.quantity_current,
                DATEDIFF(s.expiry_date, NOW()) as days_until_expiry
            FROM inventory_stock s
            JOIN consumables c ON s.consumable_id = c.id
            WHERE s.status = 'Active'
                AND s.expiry_date IS NOT NULL
                AND s.expiry_date <= %s
                AND s.expiry_date > NOW()
            ORDER BY s.expiry_date ASC
            """,
            (expiry_cutoff.date(),)
        )
        
        alerts = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'days_ahead': days_ahead
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/alerts/low-stock', methods=['GET'])
@require_auth
def get_low_stock_alerts():
    """
    Get consumables below reorder level
    """
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute(
            """
            SELECT
                s.id,
                c.item_name,
                c.unit_of_measure,
                s.quantity_current,
                c.reorder_level,
                c.max_stock_level,
                s.unit_cost,
                (c.reorder_level - s.quantity_current) * s.unit_cost as reorder_cost
            FROM inventory_stock s
            JOIN consumables c ON s.consumable_id = c.id
            WHERE s.status = 'Active'
                AND s.quantity_current <= c.reorder_level
            ORDER BY s.quantity_current ASC
            """
        )
        
        alerts = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'total_reorder_cost': sum(alert.get('reorder_cost', 0) for alert in alerts)
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/alerts/warranty', methods=['GET'])
@require_auth
def get_warranty_expiry_alerts():
    """
    Get equipment with warranty expiring soon
    Query params: days_ahead (default: 30)
    """
    try:
        days_ahead = int(request.args.get('days_ahead', 30))
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        warranty_cutoff = datetime.now(timezone.utc) + timedelta(days=days_ahead)
        
        cursor.execute(
            """
            SELECT
                id,
                asset_name,
                asset_tag,
                serial_number,
                manufacturer,
                warranty_expiry,
                DATEDIFF(warranty_expiry, NOW()) as days_until_expiry,
                status
            FROM assets
            WHERE warranty_expiry IS NOT NULL
                AND warranty_expiry <= %s
                AND warranty_expiry > NOW()
            ORDER BY warranty_expiry ASC
            """,
            (warranty_cutoff.date(),)
        )
        
        alerts = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': alerts,
            'summary': {
                'total_alerts': len(alerts),
                'days_ahead': days_ahead
            }
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# CATEGORIES AND REFERENCE DATA
# ============================================================================

@inventory_bp.route('/asset-categories', methods=['GET'])
@require_auth
def get_asset_categories():
    """Get all asset categories"""
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, category_name as name, description, 
                   calibration_frequency_months, depreciation_rate, 
                   is_active, created_at
            FROM asset_categories 
            WHERE is_active = 1 
            ORDER BY category_name
        """)
        
        categories = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': categories
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/consumable-categories', methods=['GET'])
@require_auth
def get_consumable_categories():
    """Get all consumable categories"""
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, category_name as name, description, 
                   is_active, created_at
            FROM consumable_categories 
            WHERE is_active = 1 
            ORDER BY category_name
        """)
        
        categories = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': categories
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/suppliers', methods=['GET'])
@require_auth
def get_suppliers():
    """Get all suppliers"""
    try:
        db_conn = get_db_connection()
        cursor = db_conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, supplier_name as name, contact_person, 
                   phone, email, address, tax_number, 
                   is_active, created_at, updated_at
            FROM suppliers 
            WHERE is_active = 1 
            ORDER BY supplier_name
        """)
        
        suppliers = cursor.fetchall()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': suppliers
        }), 200
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/suppliers', methods=['POST'])
@require_auth
@require_role(['admin', 'inventory_manager'])
def create_supplier():
    """Create a new supplier"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'contact_person', 'phone', 'email']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'{field} is required'
                }), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        cursor.execute("""
            INSERT INTO suppliers (supplier_name, contact_person, phone, email, 
                                 address, tax_number, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 1, NOW(), NOW())
        """, (
            data['name'],
            data['contact_person'],
            data['phone'],
            data['email'],
            data.get('address', ''),
            data.get('tax_number', '')
        ))
        
        supplier_id = cursor.lastrowid
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {'id': supplier_id},
            'message': 'Supplier created successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@inventory_bp.route('/stock/receive', methods=['POST'])
@require_auth
@require_role(['admin', 'inventory_manager', 'nurse'])
def receive_stock():
    """Receive new stock shipment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['consumable_id', 'batch_number', 'quantity_received', 
                          'unit_cost', 'manufacture_date', 'expiry_date', 'supplier_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False, 
                    'error': f'{field} is required'
                }), 400
        
        db_conn = get_db_connection()
        cursor = db_conn.cursor()
        
        # Calculate total cost
        total_cost = float(data['quantity_received']) * float(data['unit_cost'])
        
        cursor.execute("""
            INSERT INTO inventory_stock (
                consumable_id, batch_number, supplier_id, quantity_received, 
                quantity_current, quantity_used, unit_cost, total_cost, 
                manufacture_date, expiry_date, received_date, location, 
                status, received_by, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, 0, %s, %s, %s, %s, CURDATE(), %s, 'Active', %s, NOW(), NOW())
        """, (
            data['consumable_id'],
            data['batch_number'],
            data['supplier_id'],
            data['quantity_received'],
            data['quantity_received'],  # quantity_current starts same as received
            data['unit_cost'],
            total_cost,
            data['manufacture_date'],
            data['expiry_date'],
            data.get('location', 'Main Store'),
            data.get('received_by', 1)  # Default to user 1 if not provided
        ))
        
        stock_id = cursor.lastrowid
        db_conn.commit()
        cursor.close()
        db_conn.close()
        
        return jsonify({
            'success': True,
            'data': {'id': stock_id},
            'message': 'Stock received successfully'
        }), 201
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ASSET MAINTENANCE
# ============================================================================

@inventory_bp.route('/assets/<int:asset_id>/maintenance', methods=['GET', 'POST'])
@require_auth
def asset_maintenance(asset_id):
    """
    GET: List all maintenance records for an asset
    POST: Create a new maintenance record for an asset
    """
    db_conn = get_db_connection()
    cursor = db_conn.cursor(dictionary=True)
    if request.method == 'GET':
        try:
            cursor.execute(
                """
                SELECT * FROM asset_maintenance
                WHERE asset_id = %s
                ORDER BY maintenance_date DESC, created_at DESC
                """,
                (asset_id,)
            )
            records = cursor.fetchall()
            cursor.close()
            db_conn.close()
            return jsonify({'success': True, 'data': records}), 200
        except Exception as e:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500
    elif request.method == 'POST':
        try:
            data = request.get_json()
            required_fields = ['maintenance_type', 'maintenance_date']
            for field in required_fields:
                if not data.get(field):
                    cursor.close()
                    db_conn.close()
                    return jsonify({'success': False, 'error': f'{field} is required'}), 400

            cursor.execute(
                """
                INSERT INTO asset_maintenance (
                    asset_id, maintenance_date, maintenance_type, description, cost, performed_by, next_due_date, notes, created_by, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    asset_id,
                    data['maintenance_date'],
                    data['maintenance_type'],
                    data.get('description'),
                    data.get('cost'),
                    data.get('performed_by'),
                    data.get('next_due_date'),
                    data.get('notes'),
                    getattr(request, 'user_id', None),
                    datetime.now(timezone.utc)
                )
            )
            db_conn.commit()
            new_id = cursor.lastrowid
            cursor.execute("SELECT * FROM asset_maintenance WHERE id = %s", (new_id,))
            new_record = cursor.fetchone()
            cursor.close()
            db_conn.close()
            return jsonify({'success': True, 'data': new_record, 'message': 'Maintenance record created'}), 201
        except Exception as e:
            cursor.close()
            db_conn.close()
            return jsonify({'success': False, 'error': str(e)}), 500