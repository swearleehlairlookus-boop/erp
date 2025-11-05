# POLMED Mobile Clinic ERP - Backend System

A comprehensive, production-ready healthcare management system backend for POLMED's Mobile Clinic in South Africa, built with Flask, MySQL, and modern API standards.

---

## 🏥 Healthcare Features

### Clinical Management
- **Multi-stage Visit Workflow** - 5-stage clinical process (Registration → Assessment → Consultation → Counseling → Closure)
- **Patient Management** - Complete patient profiles with medical history, allergies, chronic conditions
- **Vital Signs Tracking** - Comprehensive vital signs recording (BP, HR, Temp, O2 sat, etc.)
- **Clinical Documentation** - Structured clinical notes with ICD-10 coding
- **Prescription Management** - Drug database with dosage tracking
- **Referral System** - Internal and external referral management with urgency levels

### Patient Services
- **PALMED Integration** - Medical aid member verification and claim support
- **Patient Registration** - Multi-field patient registration with validation
- **Medical History** - Track chronic conditions, allergies, medications
- **Appointment Booking** - Public-facing appointment scheduling system
- **Patient Portal Access** - Secure patient data access

### Operations Management
- **Multi-Clinic Support** - Support for multiple clinic locations
- **Route Planning** - Province-based routing to police stations, schools, community centers
- **Appointment Scheduling** - Slot-based appointment system with capacity management
- **Location Management** - Track clinic locations with GPS coordinates and facilities

### Inventory & Asset Management
- **Asset Lifecycle** - Track medical equipment from purchase to retirement
- **Consumable Tracking** - Medicine and supply inventory management
- **Stock Alerts** - Low inventory and expiry date warnings
- **Warranty Management** - Equipment warranty tracking and maintenance scheduling
- **Supplier Management** - Track suppliers and purchase history

### System Administration
- **Role-Based Access Control** - 8 predefined roles with granular permissions
- **Audit Logging** - Complete audit trail of all system activities
- **User Management** - Staff user creation and permission assignment
- **Health Monitoring** - System health checks and performance metrics
- **Analytics & Reporting** - Dashboard metrics and data export

---

## 🏗️ System Architecture

### Technology Stack
- **Backend Framework:** Flask 2.3+
- **Database:** MySQL 8.0+
- **Authentication:** JWT (JSON Web Tokens)
- **Security:** bcrypt password hashing, CORS support
- **API Standard:** RESTful JSON API

### Project Structure

\`\`\`
app/
├── __init__.py              # Package initialization
├── database.py              # Database connection singleton
├── auth.py                  # JWT authentication and RBAC
├── auth_routes.py           # Authentication endpoints
├── patient_routes.py        # Patient management
├── clinical_routes.py       # Clinical workflow
├── inventory_routes.py      # Inventory management
├── routes_appointments.py   # Routes and appointments
└── health_sync.py           # Health checks and sync

scripts/
├── db_schema_v2.sql         # Database schema
├── create_admin_user.py     # Admin user setup
├── validate_backend.py      # System validation
├── run_tests.py             # API tests
├── deploy.sh                # Production deployment
├── startup.sh               # Application startup
├── requirements.txt         # Python dependencies
└── config.py                # Configuration

.env.example                 # Environment template
BACKEND_README.md            # Detailed API documentation
DEPLOYMENT_GUIDE.md          # Production deployment guide
BACKEND_CLEANUP_COMPLETED.md # Migration summary
\`\`\`

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- MySQL 8.0 or higher
- pip package manager

### Installation

1. **Clone the repository**
   \`\`\`bash
   cd palmedclinicerp
   \`\`\`

2. **Install Python dependencies**
   \`\`\`bash
   pip install -r scripts/requirements.txt
   \`\`\`

3. **Configure environment**
   \`\`\`bash
   cp .env.example .env
   # Edit .env with your database credentials
   \`\`\`

4. **Setup database**
   \`\`\`bash
   mysql -u root -p < scripts/db_schema_v2.sql
   \`\`\`

5. **Create admin user**
   \`\`\`bash
   python scripts/create_admin_user.py
   \`\`\`

6. **Validate installation**
   \`\`\`bash
   python scripts/validate_backend.py
   \`\`\`

7. **Run tests**
   \`\`\`bash
   python scripts/run_tests.py
   \`\`\`

8. **Start application**
   \`\`\`bash
   python -m flask run
   \`\`\`

Backend will be available at: `http://localhost:5000`

---

## 📚 API Documentation

### Authentication
\`\`\`
POST   /api/auth/login       - User login
GET    /api/auth/me          - Get current user
POST   /api/auth/logout      - User logout
GET    /api/auth/verify      - Verify token
\`\`\`

### Patients
\`\`\`
GET    /api/patients                  - List patients
POST   /api/patients                  - Create patient
GET    /api/patients/<id>             - Get patient details
PUT    /api/patients/<id>             - Update patient
POST   /api/patients/<id>/deactivate  - Deactivate patient
\`\`\`

### Clinical
\`\`\`
POST   /api/visits                    - Create visit
GET    /api/visits/<id>               - Get visit details
POST   /api/vital-signs               - Record vitals
POST   /api/clinical-notes            - Create clinical note
POST   /api/referrals                 - Create referral
\`\`\`

### Inventory
\`\`\`
GET    /api/assets                    - List assets
POST   /api/assets                    - Create asset
POST   /api/inventory/stock           - Record stock
GET    /api/inventory/alerts          - Get stock alerts
\`\`\`

### Routes & Appointments
\`\`\`
GET    /api/routes                    - List routes
POST   /api/appointments              - Book appointment
GET    /api/appointments/availability - Check availability
\`\`\`

### Health & Monitoring
\`\`\`
GET    /api/health                    - Basic health check
GET    /api/health/detailed           - Detailed health report
GET    /api/dashboard/stats           - Dashboard statistics
\`\`\`

For complete API documentation, see: [BACKEND_README.md](./BACKEND_README.md)

---

## 🔐 Security Features

- **JWT Authentication** - Secure token-based authentication
- **Role-Based Access Control** - Fine-grained permission management
- **Password Hashing** - bcrypt secure password storage
- **Audit Logging** - Complete activity tracking
- **CORS Support** - Configurable cross-origin requests
- **Input Validation** - Server-side validation on all endpoints
- **SQL Injection Protection** - Parameterized queries throughout
- **Session Management** - Secure token lifecycle management

---

## 📊 Database Schema

### Core Tables (13 tables)

1. **user_roles** - Role definitions and permissions
2. **users** - System users (doctors, nurses, admin, etc.)
3. **audit_log** - Activity tracking for compliance
4. **patients** - Patient information with PALMED integration
5. **patient_contacts** - Emergency and secondary contacts
6. **patient_visits** - Clinical visit records
7. **vital_signs** - Vital signs measurements
8. **workflow_stages** - Visit workflow definitions
9. **clinical_notes** - Clinical documentation
10. **referrals** - Internal and external referrals
11. **prescriptions** - Medication prescriptions
12. **drug_database** - South African drug catalog
13. **routes** - Multi-location clinic routes
14. **locations** - Clinic visit locations
15. **appointments** - Appointment slots and bookings
16. **assets** - Medical equipment tracking
17. **asset_maintenance** - Equipment maintenance logs
18. **consumables** - Medical supplies inventory
19. **inventory_stock** - Stock batch tracking
20. **inventory_usage** - Consumable usage tracking
21. **suppliers** - Supplier information
22. **daily_metrics** - System metrics and analytics

---

## 👥 User Roles

| Role | Permissions |
|------|------------|
| **Administrator** | Full system access, user management, configuration |
| **Doctor** | Patient management, clinical consultation, prescriptions, referrals |
| **Nurse** | Patient vitals, nursing assessments, referral viewing |
| **Clerk** | Patient registration, appointment scheduling |
| **Social Worker** | Patient counseling, psychosocial support, referrals |
| **Inventory Manager** | Asset tracking, stock management, supplier management |
| **Finance** | Financial reports, payment tracking, analytics |
| **Viewer** | Read-only access to all patient and visit data |

---

## 🔧 Configuration

### Environment Variables

\`\`\`env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=palmed_clinic_erp

# Flask
FLASK_ENV=production
FLASK_APP=run.py
SECRET_KEY=your-secret-key

# JWT
JWT_SECRET=your-jwt-secret
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# PALMED Integration
PALMED_API_URL=https://api.palmed.org
PALMED_API_KEY=your-palmed-key

# Email (for notifications)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/polmed_clinic.log
\`\`\`

See `.env.example` for complete configuration template.

---

## 📋 Deployment

### Production Checklist

- [ ] Database backups configured
- [ ] Environment variables set securely
- [ ] SSL/TLS certificates installed
- [ ] Firewall rules configured
- [ ] Health monitoring enabled
- [ ] Log rotation configured
- [ ] Admin users created
- [ ] PALMED integration tested
- [ ] API endpoints tested
- [ ] CORS configured correctly

### Deployment Steps

\`\`\`bash
# 1. Prepare server
bash scripts/deploy.sh production

# 2. Run database migrations
python scripts/validate_backend.py

# 3. Run tests
python scripts/run_tests.py

# 4. Start application
systemctl start polmed-clinic-backend

# 5. Verify health
curl http://localhost:5000/api/health
\`\`\`

For detailed deployment instructions, see: [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)

---

## 🧪 Testing

### Run All Tests
\`\`\`bash
python scripts/run_tests.py
\`\`\`

### Test Categories
- Authentication tests
- Patient endpoint tests
- Clinical workflow tests
- Inventory management tests
- Permission and authorization tests
- Error handling tests

---

## 📝 API Examples

### Login Example
\`\`\`bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "doctor@polmed.org",
    "password": "password123"
  }'
\`\`\`

Response:
\`\`\`json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "user_id": 1,
      "email": "doctor@polmed.org",
      "first_name": "John",
      "last_name": "Doe",
      "role": "doctor"
    }
  }
}
\`\`\`

### Create Patient Example
\`\`\`bash
curl -X POST http://localhost:5000/api/patients \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1985-05-15",
    "gender": "Female",
    "phone_number": "0798765432",
    "medical_aid_number": "PALMED123456",
    "province": "Western Cape"
  }'
\`\`\`

---

## 🐛 Troubleshooting

### Database Connection Error
- Check MySQL service is running: `systemctl status mysql`
- Verify credentials in `.env` file
- Check database exists: `mysql -u root -p -e "SHOW DATABASES;"`

### Port Already in Use
\`\`\`bash
# Find and kill process using port 5000
lsof -i :5000
kill -9 <PID>
\`\`\`

### JWT Token Invalid
- Token may be expired - login again
- Secret key may have changed - restart application
- Check JWT_SECRET in `.env` file

### Permission Denied Errors
- Verify user has correct role assigned
- Check role permissions in database
- Verify token contains correct role information

See [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) for more troubleshooting tips.

---

## 📖 Documentation

- [BACKEND_README.md](./BACKEND_README.md) - Detailed API documentation
- [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md) - Production deployment guide
- [BACKEND_CLEANUP_COMPLETED.md](./BACKEND_CLEANUP_COMPLETED.md) - Migration summary
- [FRONTEND_BACKEND_INTEGRATION.md](./FRONTEND_BACKEND_INTEGRATION.md) - Frontend integration guide

---

## 🔄 PALMED Integration

The system includes built-in PALMED medical aid integration:

- Member verification via PALMED API
- Automatic medical aid claim processing
- Member status synchronization
- Benefit limitation checking

See endpoint: `POST /api/sync/palmed`

---

## 📊 Monitoring & Analytics

### Health Checks
\`\`\`bash
# Basic health check
curl http://localhost:5000/api/health

# Detailed health report
curl http://localhost:5000/api/health/detailed
\`\`\`

### Dashboard Statistics
\`\`\`bash
# Get system statistics
curl http://localhost:5000/api/dashboard/stats \
  -H "Authorization: Bearer <token>"
\`\`\`

---

## 🤝 Contributing

This is a production system. All changes must:
1. Include comprehensive testing
2. Update relevant documentation
3. Follow Flask best practices
4. Include audit logging where applicable
5. Maintain backward compatibility

---

## 📄 License

POLMED Mobile Clinic ERP - Backend System
Proprietary - All Rights Reserved

---

## 📞 Support

For issues or questions:
1. Check troubleshooting section
2. Review documentation files
3. Contact POLMED technical support

---

## ✅ Status

**Production Ready** - November 3, 2025

This backend has been completely redesigned and modernized with:
- Clean modular architecture
- Enterprise-grade security
- Comprehensive healthcare domain modeling
- Production deployment readiness
- Complete API documentation

---

**Last Updated:** November 3, 2025  
**Version:** 2.0  
**Maintainer:** POLMED Development Team
