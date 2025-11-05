# POLMED Healthcare ERP - Backend Redesign Guide v2

## Overview

This document outlines the complete backend redesign for the POLMED Mobile Clinic ERP system. The redesign follows healthcare industry best practices with proper layered architecture, security, and compliance standards.

## Key Improvements

### 1. **Comprehensive Database Schema**
- **Healthcare-specific design** with proper relationships
- **HIPAA/GDPR-compliant** audit logging
- **South African context** - PALMED integration, provinces, medical aid numbers
- **Clinical domain modeling** - visits, vital signs, referrals, prescriptions

### 2. **Professional Architecture**
- **Layered design**: DatabaseLayer → ServiceLayer → APILayer
- **Separation of concerns**: Auth, Validation, Audit, Error handling
- **JWT-based authentication** with role-based access control (RBAC)
- **Comprehensive error handling** and logging

### 3. **Inventory & Asset Management**
- **Batch tracking** for consumables with expiry management
- **Asset lifecycle** - purchase, maintenance, depreciation
- **Stock level alerts** and reorder triggers
- **Usage history** for compliance and cost analysis

### 4. **Clinical Workflow**
- **Multi-stage workflow** - Registration → Assessment → Consultation → Counseling → Closure
- **Clinical notes** with ICD-10 coding
- **Prescription management** - drug database, dosing, duration
- **Referral tracking** - internal and external with status

### 5. **Route & Appointment System**
- **Route planning** - provinces, location types, date ranges
- **Appointment slots** generated from route locations
- **Location management** - police stations, schools, community centers
- **Booking references** for patient tracking

## Database Schema

### Core Entities

\`\`\`
Users (authentication and authorization)
├── user_roles (administrator, doctor, nurse, clerk, etc.)
└── audit_log (compliance tracking)

Patients (patient master data)
├── patient_visits (clinical encounters)
├── vital_signs (measurements during visits)
├── patient_contacts (emergency and other contacts)
└── patient_conditions (chronic conditions, allergies, medications)

Clinical Workflow
├── workflow_stages (Registration, Assessment, etc.)
├── clinical_notes (notes per stage)
├── prescriptions (medications)
├── referrals (internal/external referrals)
└── drug_database (South African medicines)

Routes & Appointments
├── routes (clinic schedules by province)
├── locations (police stations, schools, etc.)
├── route_locations (many-to-many with timing)
└── appointments (individual appointment slots)

Inventory
├── assets (equipment, vehicles, furniture)
├── asset_categories (medical, vehicles, IT, etc.)
├── asset_maintenance (maintenance log)
├── consumables (medicines, supplies)
├── consumable_categories (medicines, PPE, etc.)
├── suppliers (vendor management)
├── inventory_stock (batch tracking with expiry)
└── inventory_usage (consumption tracking)

Analytics
└── daily_metrics (KPI tracking)
\`\`\`

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `GET /api/auth/me` - Get current user

### Patient Management
- `GET /api/patients` - List patients with pagination
- `POST /api/patients` - Create patient
- `GET /api/patients/{id}` - Get patient details
- `PUT /api/patients/{id}` - Update patient

### Visits & Clinical
- `POST /api/patients/{id}/visits` - Create visit
- `POST /api/visits/{id}/vital-signs` - Record vital signs
- `POST /api/visits/{id}/clinical-notes` - Add clinical note
- `POST /api/visits/{id}/prescriptions` - Create prescription
- `GET /api/visits/{id}/prescriptions` - Get prescriptions

### Routes & Appointments
- `GET /api/routes` - List routes
- `POST /api/routes` - Create route
- `GET /api/appointments` - List appointments
- `POST /api/appointments/{id}/book` - Book appointment

### Inventory
- `GET /api/inventory/assets` - List assets
- `POST /api/inventory/assets` - Create asset
- `GET /api/inventory/consumables` - List consumables
- `POST /api/inventory/stock/receive` - Receive stock
- `GET /api/inventory/alerts/expiry` - Expiry alerts

### Dashboard & Health
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/health` - Health check

## Migration Steps

### 1. **Prepare New Database**
\`\`\`bash
# Create new database
mysql -u root -p < scripts/db_schema_v2.sql

# Verify schema
mysql -u root -p -e "USE palmed_clinic_erp; SHOW TABLES;"
\`\`\`

### 2. **Deploy New Backend**
\`\`\`bash
# Install dependencies
pip install flask flask-cors mysql-connector-python pyjwt python-dotenv

# Start new backend
python app_v2.py
\`\`\`

### 3. **Update Frontend API Service**
- Replace `lib/api-service.ts` with new version
- All endpoints maintain backward compatibility
- Frontend code requires no changes

### 4. **Data Migration** (if needed)
- Extract data from old database
- Transform to new schema format
- Load into new database
- Verify data integrity

## Security Best Practices Implemented

1. **Authentication**
   - JWT tokens with 24-hour expiration
   - Password hashing with werkzeug.security
   - Token validation on every request

2. **Authorization**
   - Role-based access control (RBAC)
   - Route-level permissions
   - User role verification

3. **Audit Trail**
   - All changes logged to audit_log table
   - User, action, timestamp, old/new values
   - IP address and user agent tracking

4. **Data Protection**
   - UTF-8MB4 encoding for international characters
   - HIPAA-compliant field naming
   - Sensitive data handling

5. **Input Validation**
   - Required field validation
   - Type checking (int, float, date)
   - SQL injection prevention with parameterized queries

## Monitoring & Maintenance

### Health Checks
\`\`\`bash
curl http://localhost:5000/api/health
\`\`\`

### Database Optimization
\`\`\`sql
-- Analyze performance
ANALYZE TABLE patients;
ANALYZE TABLE patient_visits;

-- Add indexes if needed
CREATE INDEX idx_patient_visits_patient_date 
ON patient_visits(patient_id, visit_date);
\`\`\`

### Audit Log Review
\`\`\`sql
SELECT * FROM audit_log 
WHERE action = 'INSERT' AND created_at > DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY created_at DESC;
\`\`\`

## Performance Considerations

1. **Database Connections**: Connection pooling recommended for production
2. **Query Optimization**: Proper indexing on frequently queried fields
3. **Pagination**: Default 20 records per page to reduce load
4. **Caching**: Consider caching frequently accessed routes and locations

## Support & Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify DB_HOST, DB_NAME, DB_USER, DB_PASSWORD in environment
   - Check MySQL server is running
   - Verify user permissions

2. **Token Validation Failed**
   - Ensure JWT_SECRET is consistent across requests
   - Check token expiration time
   - Verify Bearer token format

3. **Permission Denied**
   - Verify user role is in allowed_roles
   - Check user is_active = TRUE
   - Review role permissions in user_roles table

## Next Steps

1. Deploy database schema v2
2. Deploy backend v2 (app_v2.py)
3. Update frontend API service
4. Run comprehensive testing
5. Monitor system performance
6. Migrate production data
7. Decommission old backend

---
**Version**: 2.0.0
**Last Updated**: 2025-11-03
**Status**: Ready for Production Deployment
