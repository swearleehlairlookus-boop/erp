# POLMED Mobile Clinic ERP - Backend API v2

## Overview

The POLMED Mobile Clinic ERP Backend is a professional-grade healthcare management system built with Flask, designed for multi-clinic healthcare delivery in South Africa. It provides comprehensive APIs for patient management, clinical workflows, inventory tracking, and route planning.

## Key Features

### Clinical Management
- **Patient Registration**: Complete patient records with PALMED integration
- **Visit Tracking**: Multi-stage clinical workflow (Registration → Assessment → Consultation → Counseling → Closure)
- **Vital Signs Recording**: Comprehensive measurement collection and analysis
- **Clinical Notes**: Structured documentation with ICD-10 coding support
- **Prescriptions**: Medication management with drug database and dispensing tracking
- **Referrals**: Internal and external referral management with status tracking

### Inventory Management
- **Asset Lifecycle**: Track medical equipment from purchase to retirement
- **Consumable Management**: Medicine and supply tracking with batch management
- **Stock Alerts**: Automatic low stock and expiry date notifications
- **Supplier Management**: Vendor information and procurement tracking
- **Usage History**: Detailed consumption analytics and cost tracking

### Route & Appointment System
- **Route Planning**: Create clinic schedules by province and location type
- **Location Management**: Police stations, schools, community centers
- **Appointment Booking**: Public-facing appointment slots with booking references
- **Availability Management**: Dynamic capacity and availability

### System Features
- **Role-Based Access Control**: 8 predefined roles with granular permissions
- **Audit Logging**: Complete compliance tracking for HIPAA/GDPR
- **JWT Authentication**: Secure token-based API access
- **Error Handling**: Comprehensive error messages and validation
- **Health Monitoring**: Built-in health check endpoints

## Technology Stack

- **Framework**: Flask 2.3.3
- **Database**: MySQL 8.0+
- **Authentication**: JWT (PyJWT 2.8.0)
- **Security**: Werkzeug password hashing
- **Database Driver**: mysql-connector-python 8.1.0
- **Server**: Gunicorn for production
- **CORS**: Flask-CORS for cross-origin support

## Installation

### Prerequisites
- Python 3.8+
- MySQL 8.0+
- pip3
- 512MB RAM minimum, 2GB recommended

### Quick Start

1. **Clone the repository**
\`\`\`bash
git clone https://github.com/polmed/clinic-erp.git
cd clinic-erp
\`\`\`

2. **Create virtual environment**
\`\`\`bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
\`\`\`

3. **Install dependencies**
\`\`\`bash
pip3 install -r scripts/requirements.txt
\`\`\`

4. **Setup database**
\`\`\`bash
mysql -u root -p < scripts/db_schema_v2.sql
\`\`\`

5. **Configure environment**
\`\`\`bash
cp .env.example .env
# Edit .env with your configuration
\`\`\`

6. **Start the backend**
\`\`\`bash
python3 app_v2.py
\`\`\`

The API will be available at `http://localhost:5000/api`

## API Documentation

### Authentication

#### Login
\`\`\`http
POST /api/auth/login
Content-Type: application/json

{
  "email": "doctor@polmed.co.za",
  "password": "securepassword"
}

Response: 200 OK
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "user": {
      "user_id": 1,
      "email": "doctor@polmed.co.za",
      "first_name": "John",
      "last_name": "Doe",
      "role": "doctor"
    }
  }
}
\`\`\`

#### Get Current User
\`\`\`http
GET /api/auth/me
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "id": 1,
    "email": "doctor@polmed.co.za",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+27123456789",
    "role_name": "doctor"
  }
}
\`\`\`

### Patient Management

#### Get Patients (Paginated)
\`\`\`http
GET /api/patients?page=1&per_page=20&search=John
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 150,
    "pages": 8
  }
}
\`\`\`

#### Create Patient
\`\`\`http
POST /api/patients
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "date_of_birth": "1990-05-15",
  "gender": "Male",
  "phone_number": "+27123456789",
  "medical_aid_number": "PAL123456789",
  "email": "john@example.com",
  "physical_address": "123 Main St, Cape Town",
  "province": "Western Cape",
  "is_palmed_member": true,
  "chronic_conditions": ["Hypertension", "Diabetes"],
  "allergies": ["Penicillin"],
  "current_medications": ["Metformin 500mg", "Lisinopril 10mg"]
}

Response: 201 Created
{
  "success": true,
  "message": "Patient created successfully"
}
\`\`\`

#### Get Patient Details
\`\`\`http
GET /api/patients/123
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "id": 123,
    "first_name": "John",
    "last_name": "Doe",
    ...
  }
}
\`\`\`

### Clinical Workflow

#### Create Visit
\`\`\`http
POST /api/patients/123/visits
Authorization: Bearer <token>
Content-Type: application/json

{
  "visit_date": "2025-11-03",
  "visit_time": "14:30",
  "visit_type": "scheduled",
  "chief_complaint": "Hypertension follow-up",
  "route_id": 5,
  "location_id": 12
}

Response: 201 Created
{
  "success": true,
  "data": {
    "visit_id": 456
  }
}
\`\`\`

#### Record Vital Signs
\`\`\`http
POST /api/visits/456/vital-signs
Authorization: Bearer <token>
Content-Type: application/json

{
  "systolic_bp": 140,
  "diastolic_bp": 90,
  "heart_rate": 72,
  "temperature": 36.8,
  "weight": 75.5,
  "height": 175,
  "oxygen_saturation": 98,
  "blood_glucose": 120,
  "nursing_notes": "Patient stable, vital signs normal"
}

Response: 201 Created
{
  "success": true,
  "message": "Vital signs recorded successfully"
}
\`\`\`

#### Create Referral
\`\`\`http
POST /api/patients/123/referrals
Authorization: Bearer <token>
Content-Type: application/json

{
  "referral_type": "external",
  "from_stage": "Doctor Consultation",
  "external_provider": "City Hospital",
  "department": "Cardiology",
  "reason": "Cardiac evaluation needed",
  "urgency": "routine",
  "appointment_date": "2025-11-10"
}

Response: 201 Created
{
  "success": true,
  "message": "Referral created successfully"
}
\`\`\`

### Inventory Management

#### Get Assets
\`\`\`http
GET /api/inventory/assets?page=1&per_page=20&status=operational
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": [...],
  "pagination": {...}
}
\`\`\`

#### Create Asset
\`\`\`http
POST /api/inventory/assets
Authorization: Bearer <token>
Content-Type: application/json

{
  "asset_tag": "MED-BP-001",
  "asset_name": "Blood Pressure Monitor",
  "serial_number": "SN12345678",
  "category_id": 1,
  "manufacturer": "Omron",
  "model": "M6 Comfort",
  "purchase_date": "2024-01-15",
  "warranty_expiry": "2026-01-15",
  "location": "Mobile Clinic 1",
  "purchase_cost": 2500.00,
  "status": "operational"
}

Response: 201 Created
{
  "success": true,
  "message": "Asset created successfully"
}
\`\`\`

#### Get Expiry Alerts
\`\`\`http
GET /api/inventory/alerts/expiry?days_ahead=90
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 1,
      "batch_number": "BATCH-001",
      "item_name": "Aspirin 500mg",
      "expiry_date": "2025-12-15",
      "quantity_current": 45,
      "days_until_expiry": 42
    }
  ]
}
\`\`\`

### Routes & Appointments

#### Get Available Appointments
\`\`\`http
GET /api/appointments/available?province=Western Cape&date_from=2025-11-10&date_to=2025-12-31
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": [
    {
      "id": 123,
      "appointment_date": "2025-11-15",
      "appointment_time": "09:00",
      "route_name": "Cape Town Route 1",
      "location_name": "Khayelitsha Clinic",
      "location_type": "police_station"
    }
  ]
}
\`\`\`

#### Create Route
\`\`\`http
POST /api/routes
Authorization: Bearer <token>
Content-Type: application/json

{
  "route_name": "Cape Town Route 1",
  "description": "Weekly clinic visits in Cape Town townships",
  "province": "Western Cape",
  "route_type": "Police Stations",
  "start_date": "2025-11-01",
  "end_date": "2025-12-31",
  "start_time": "08:00",
  "end_time": "17:00",
  "max_appointments_per_day": 50
}

Response: 201 Created
{
  "success": true,
  "message": "Route created successfully"
}
\`\`\`

### Dashboard & Analytics

#### Get Dashboard Statistics
\`\`\`http
GET /api/dashboard/stats
Authorization: Bearer <token>

Response: 200 OK
{
  "success": true,
  "data": {
    "todayPatients": 45,
    "activeRoutes": 5,
    "pendingReferrals": 3,
    "pendingAppointments": 12,
    "lowStockAlerts": 2,
    "expiryAlerts": 5
  }
}
\`\`\`

### Health Check

#### System Health
\`\`\`http
GET /api/health

Response: 200 OK
{
  "success": true,
  "status": "healthy",
  "timestamp": "2025-11-03T14:30:00Z",
  "version": "2.0.0"
}
\`\`\`

## User Roles & Permissions

| Role | Permissions | Use Case |
|------|-------------|----------|
| **Administrator** | All operations | System admin, super user |
| **Doctor** | Patient management, clinical notes, prescriptions, referrals | Medical doctors, clinical officers |
| **Nurse** | Patient registration, vital signs, assessments | Nursing staff |
| **Clerk** | Patient registration, appointment booking | Administrative staff |
| **Social Worker** | Referrals, counseling notes, patient support | Psychosocial support staff |
| **Inventory Manager** | Asset and consumable management, stock tracking | Inventory and supply chain staff |
| **Finance** | Financial reports and analytics | Finance team |
| **Viewer** | Read-only access to reports | Management and reporting |

## Error Handling

### Standard Error Response
\`\`\`json
{
  "success": false,
  "error": "Descriptive error message"
}
\`\`\`

### Common Status Codes
- `200 OK` - Successful GET request
- `201 Created` - Successful POST request
- `400 Bad Request` - Invalid request parameters
- `401 Unauthorized` - Missing or invalid authentication token
- `403 Forbidden` - User lacks required permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Duplicate resource or conflict
- `500 Internal Server Error` - Server error

## Deployment

### Development
\`\`\`bash
python3 app_v2.py
\`\`\`

### Production with Gunicorn
\`\`\`bash
gunicorn -w 4 -b 0.0.0.0:5000 app_v2:app
\`\`\`

### Docker Deployment
\`\`\`dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app_v2.py .
EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app_v2:app"]
\`\`\`

## Monitoring & Logging

### Log Files
- Main log: `logs/polmed_backend.log`
- Audit log: Database table `audit_log`
- Application errors: `logs/errors.log`

### Key Metrics to Monitor
- Request response time
- Database query performance
- API error rates
- User authentication attempts
- Inventory alert frequency

## Performance Optimization

### Database Tuning
\`\`\`sql
-- Analyze table performance
ANALYZE TABLE patients;
ANALYZE TABLE patient_visits;

-- Check index usage
SELECT * FROM performance_schema.table_io_waits_summary_by_index_usage;

-- Optimize tables
OPTIMIZE TABLE patients;
OPTIMIZE TABLE patient_visits;
\`\`\`

### API Optimization
- Implement caching for frequently accessed routes
- Use pagination for large result sets
- Add database connection pooling in production
- Enable GZIP compression

## Troubleshooting

### Database Connection Error
\`\`\`
Error: MySQL connection failed
Solution: Verify DB_HOST, DB_USER, DB_PASSWORD in .env file
\`\`\`

### JWT Token Expired
\`\`\`
Error: Invalid or expired token
Solution: User needs to login again to get fresh token
\`\`\`

### Permission Denied
\`\`\`
Error: Insufficient permissions
Solution: Check user role in database and verify route permissions
\`\`\`

## Support & Maintenance

### Daily Checks
- [ ] Backend health check passing
- [ ] Database backup completed
- [ ] No critical errors in logs
- [ ] Inventory alerts reviewed

### Weekly Maintenance
- [ ] Performance analysis
- [ ] Audit log review
- [ ] Backup verification
- [ ] Security updates check

### Monthly Review
- [ ] Database optimization
- [ ] User activity analysis
- [ ] API performance metrics
- [ ] System capacity planning

## Version History

- **v2.0.0** (2025-11-03) - Complete backend redesign with healthcare domain modeling
- **v1.0.0** (2025-08-01) - Initial backend release

## License

POLMED Mobile Clinic ERP is proprietary software owned by Masala Ramabulana Holdings (Pty) Ltd

## Contact & Support

For support, contact: support@polmed.co.za

---

**Last Updated**: 2025-11-03
**Version**: 2.0.0
**Status**: Production Ready
