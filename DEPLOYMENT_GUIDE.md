# POLMED Mobile Clinic ERP - Deployment Guide

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Local Development Setup](#local-development-setup)
3. [Production Deployment](#production-deployment)
4. [Database Migration](#database-migration)
5. [Health Monitoring](#health-monitoring)
6. [Troubleshooting](#troubleshooting)
7. [Performance Optimization](#performance-optimization)
8. [Security Hardening](#security-hardening)

---

## Pre-Deployment Checklist

### Essential Tasks

- [ ] Database schema created and migrated
- [ ] Admin user created and tested
- [ ] Environment variables configured
- [ ] JWT secret key generated (min 32 characters)
- [ ] CORS origins configured correctly
- [ ] SSL/TLS certificates obtained (production)
- [ ] Backup system in place
- [ ] Logging configured
- [ ] Health check endpoint responding
- [ ] All unit tests passing

### Testing Checklist

- [ ] Authentication flow working (login/logout)
- [ ] Patient registration functioning
- [ ] Visit creation and management
- [ ] Vital signs recording
- [ ] Referral creation
- [ ] Inventory tracking
- [ ] Route and appointment management
- [ ] Role-based access control enforced
- [ ] Error handling working correctly

---

## Local Development Setup

### Quick Start (5 minutes)

1. **Clone repository**
   \`\`\`bash
   git clone https://github.com/polmed/clinic-erp.git
   cd clinic-erp
   \`\`\`

2. **Create virtual environment**
   \`\`\`bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
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
   # Edit .env with your settings
   \`\`\`

6. **Create admin user**
   \`\`\`bash
   python3 scripts/create_admin_user.py
   \`\`\`

7. **Start development server**
   \`\`\`bash
   python3 app_v2.py
   \`\`\`

8. **Validate setup**
   \`\`\`bash
   python3 scripts/validate_backend.py
   python3 scripts/run_tests.py
   \`\`\`

### Development Configuration

Create `.env` for development:

\`\`\`env
FLASK_ENV=development
FLASK_DEBUG=1
DB_HOST=localhost
DB_PORT=3306
DB_NAME=palmed_clinic_erp
DB_USER=root
DB_PASSWORD=your_password
JWT_SECRET=dev_secret_key_change_in_production
PORT=5000
HOST=0.0.0.0
\`\`\`

---

## Production Deployment

### Requirements

- Ubuntu 20.04 LTS or equivalent
- Python 3.8+
- MySQL 8.0+
- 2GB RAM minimum
- 20GB storage minimum
- Static IP address

### Step-by-Step Deployment

### 1. Server Setup

\`\`\`bash
# Update system
sudo apt update
sudo apt upgrade -y

# Install Python and dependencies
sudo apt install -y python3 python3-pip python3-venv
sudo apt install -y mysql-server mysql-client
sudo apt install -y git curl nginx

# Create application user
sudo useradd -m -s /bin/bash polmed
sudo usermod -aG www-data polmed
\`\`\`

### 2. Clone Application

\`\`\`bash
cd /opt
sudo git clone https://github.com/polmed/clinic-erp.git polmed-erp
sudo chown -R polmed:polmed polmed-erp
cd polmed-erp
\`\`\`

### 3. Setup Virtual Environment

\`\`\`bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r scripts/requirements.txt
\`\`\`

### 4. Database Setup

\`\`\`bash
# Connect to MySQL
mysql -u root -p

# Create database and user
CREATE DATABASE palmed_clinic_erp;
CREATE USER 'polmed_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON palmed_clinic_erp.* TO 'polmed_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Import schema
mysql -u polmed_user -p palmed_clinic_erp < scripts/db_schema_v2.sql

# Create admin user
python3 scripts/create_admin_user.py
\`\`\`

### 5. Configure Environment

\`\`\`bash
# Copy and edit configuration
cp .env.example .env
sudo nano .env

# Set production values:
FLASK_ENV=production
FLASK_DEBUG=0
DB_HOST=localhost
DB_USER=polmed_user
DB_PASSWORD=strong_password_here
JWT_SECRET=generate_strong_random_key_here
PORT=5000
\`\`\`

### 6. Create Systemd Service

Create `/etc/systemd/system/polmed-backend.service`:

\`\`\`ini
[Unit]
Description=POLMED Mobile Clinic ERP Backend
After=network.target mysql.service

[Service]
Type=notify
User=polmed
WorkingDirectory=/opt/polmed-erp
Environment="PATH=/opt/polmed-erp/venv/bin"
EnvironmentFile=/opt/polmed-erp/.env
ExecStart=/opt/polmed-erp/venv/bin/gunicorn \
    -w 4 \
    -b 0.0.0.0:5000 \
    --access-logfile /var/log/polmed/access.log \
    --error-logfile /var/log/polmed/error.log \
    --log-level info \
    --timeout 120 \
    app_v2:app

Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
\`\`\`

### 7. Setup Logging

\`\`\`bash
# Create log directory
sudo mkdir -p /var/log/polmed
sudo chown polmed:polmed /var/log/polmed
sudo chmod 750 /var/log/polmed

# Create app logs directory
mkdir -p /opt/polmed-erp/logs
chmod 750 /opt/polmed-erp/logs
\`\`\`

### 8. Configure Nginx

Create `/etc/nginx/sites-available/polmed-erp`:

\`\`\`nginx
upstream polmed_backend {
    server 127.0.0.1:5000;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    client_max_body_size 20M;
    
    location / {
        proxy_pass http://polmed_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    location /static/ {
        alias /opt/polmed-erp/static/;
        expires 30d;
    }
}
\`\`\`

Enable the site:

\`\`\`bash
sudo ln -s /etc/nginx/sites-available/polmed-erp /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
\`\`\`

### 9. SSL Certificate (Let's Encrypt)

\`\`\`bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d your-domain.com
\`\`\`

### 10. Start Services

\`\`\`bash
# Enable and start backend
sudo systemctl daemon-reload
sudo systemctl enable polmed-backend
sudo systemctl start polmed-backend
sudo systemctl status polmed-backend

# Verify services
curl https://your-domain.com/api/health
\`\`\`

---

## Database Migration

### Backup Before Migration

\`\`\`bash
# Full backup
mysqldump -u root -p palmed_clinic_erp > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup specific table
mysqldump -u root -p palmed_clinic_erp patients > patients_backup.sql
\`\`\`

### Zero-Downtime Migration

1. **Create backup**
   \`\`\`bash
   mysqldump -u polmed_user -p palmed_clinic_erp > backup.sql
   \`\`\`

2. **Run migration script**
   \`\`\`bash
   python3 scripts/db_migration.py
   \`\`\`

3. **Validate schema**
   \`\`\`bash
   python3 scripts/validate_backend.py
   \`\`\`

4. **Run tests**
   \`\`\`bash
   python3 scripts/run_tests.py
   \`\`\`

### Rollback Procedure

\`\`\`bash
# Stop the application
sudo systemctl stop polmed-backend

# Restore backup
mysql -u polmed_user -p palmed_clinic_erp < backup.sql

# Start application
sudo systemctl start polmed-backend
\`\`\`

---

## Health Monitoring

### Health Check Endpoint

\`\`\`bash
# Check API health
curl https://your-domain.com/api/health

# Expected response
{
    "success": true,
    "status": "healthy",
    "timestamp": "2025-11-03T14:30:00Z",
    "version": "2.0.0"
}
\`\`\`

### Service Monitoring

\`\`\`bash
# Check service status
sudo systemctl status polmed-backend

# View recent logs
sudo journalctl -u polmed-backend -n 50

# Follow logs in real-time
sudo journalctl -u polmed-backend -f
\`\`\`

### Database Health

\`\`\`bash
# Check MySQL status
sudo systemctl status mysql

# Analyze database performance
mysql -u polmed_user -p palmed_clinic_erp < scripts/db_analysis.sql

# Monitor connections
SHOW PROCESSLIST;
SHOW STATUS LIKE 'Threads%';
\`\`\`

### Monitoring Tools Setup

Install Prometheus exporter:

\`\`\`bash
pip install prometheus-client
\`\`\`

Create monitoring endpoint in `app_v2.py`:

\`\`\`python
from prometheus_client import Counter, Histogram
import time

# Metrics
request_count = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
request_duration = Histogram('api_request_duration_seconds', 'API request duration')

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    request_count.labels(request.method, request.path).inc()
    request_duration.observe(duration)
    return response
\`\`\`

---

## Troubleshooting

### Service Won't Start

\`\`\`bash
# Check error logs
sudo journalctl -u polmed-backend -n 100

# Check port conflicts
sudo lsof -i :5000

# Verify permissions
ls -la /opt/polmed-erp/
\`\`\`

### Database Connection Errors

\`\`\`bash
# Test connection
mysql -u polmed_user -p -h localhost -P 3306 palmed_clinic_erp

# Check credentials in .env
grep DB_ /opt/polmed-erp/.env

# Verify user privileges
SHOW GRANTS FOR 'polmed_user'@'localhost';
\`\`\`

### High Memory Usage

\`\`\`bash
# Check memory usage
free -h

# Monitor application
ps aux | grep gunicorn

# Reduce worker count
# Edit service file and set -w 2 instead of -w 4
\`\`\`

### High Database Load

\`\`\`bash
# Identify slow queries
SHOW VARIABLES LIKE 'long_query_time';
SET GLOBAL long_query_time = 2;

# Analyze table
ANALYZE TABLE patients;
OPTIMIZE TABLE patients;

# Check indexes
SHOW INDEX FROM patients;
\`\`\`

---

## Performance Optimization

### Database Optimization

\`\`\`sql
-- Add indexes for common queries
ALTER TABLE patients ADD INDEX idx_medical_aid (medical_aid_number);
ALTER TABLE patient_visits ADD INDEX idx_patient_date (patient_id, visit_date);
ALTER TABLE inventory_stock ADD INDEX idx_expiry (expiry_date);

-- Analyze tables
ANALYZE TABLE patients;
ANALYZE TABLE patient_visits;
ANALYZE TABLE inventory_stock;

-- Enable query cache
SET GLOBAL query_cache_size = 268435456;
SET GLOBAL query_cache_type = 1;
\`\`\`

### Application Tuning

\`\`\`python
# Update app_v2.py
app.config['JSON_SORT_KEYS'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Enable compression
from flask_compress import Compress
Compress(app)
\`\`\`

### Nginx Optimization

\`\`\`nginx
# In /etc/nginx/nginx.conf
gzip on;
gzip_types text/plain text/css application/json;
gzip_min_length 1000;

keepalive_timeout 65;
client_body_buffer_size 1M;
\`\`\`

---

## Security Hardening

### Essential Security Steps

1. **Change default passwords**
   \`\`\`bash
   # Update MySQL root password
   mysqladmin -u root password newpassword
   \`\`\`

2. **Configure firewall**
   \`\`\`bash
   sudo ufw enable
   sudo ufw allow 22/tcp
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw allow 3306/tcp from 127.0.0.1
   sudo ufw status
   \`\`\`

3. **Set strong JWT secret**
   \`\`\`bash
   # Generate 32+ character random string
   openssl rand -base64 32
   
   # Update in .env
   JWT_SECRET=generated_string_here
   \`\`\`

4. **Enable HTTPS only**
   - Configure in Nginx (done above)
   - Set `SECURE=True` for cookies in app

5. **Regular updates**
   \`\`\`bash
   sudo apt update && sudo apt upgrade -y
   pip install --upgrade -r scripts/requirements.txt
   \`\`\`

6. **Monitor security**
   \`\`\`bash
   # Check failed login attempts
   grep "Invalid email or password" /var/log/polmed/access.log | wc -l
   
   # View audit log
   SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 100;
   \`\`\`

### Database Security

\`\`\`sql
-- Remove anonymous users
DELETE FROM mysql.user WHERE User='';

-- Disable remote root login
DELETE FROM mysql.user WHERE User='root' AND Host!='localhost';

-- Change application user password
ALTER USER 'polmed_user'@'localhost' IDENTIFIED BY 'strong_new_password';

-- Remove privileges from user table
REVOKE ALL PRIVILEGES, GRANT OPTION FROM 'polmed_user'@'localhost';

-- Grant only necessary privileges
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, ALTER, DROP ON palmed_clinic_erp.* TO 'polmed_user'@'localhost';

-- Flush privileges
FLUSH PRIVILEGES;
\`\`\`

---

## Maintenance Schedule

### Daily
- [ ] Monitor health endpoint
- [ ] Review error logs
- [ ] Check disk space: `df -h`

### Weekly
- [ ] Database backup verification
- [ ] Performance metrics review
- [ ] Security log analysis

### Monthly
- [ ] Full database optimization
- [ ] Security updates installation
- [ ] Capacity planning review

### Quarterly
- [ ] Disaster recovery test
- [ ] Performance tuning
- [ ] Security audit

---

## Support & Escalation

### Issue Reporting

For critical issues, follow this escalation:

1. **Level 1**: Check logs and health status
2. **Level 2**: Attempt service restart
3. **Level 3**: Database backup and investigate
4. **Level 4**: Contact Polmed support team

### Emergency Contact

- Support: support@polmed.co.za
- Emergency: +27 XX XXXX XXXX

---

**Last Updated**: 2025-11-03
**Version**: 2.0.0
**Status**: Production Ready
