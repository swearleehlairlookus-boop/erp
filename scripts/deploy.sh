#!/bin/bash

# POLMED Mobile Clinic ERP - Deployment Script v2
# This script deploys the new backend with proper safety checks

set -e

echo "======================================================================"
echo "POLMED Mobile Clinic ERP - Backend Deployment v2"
echo "======================================================================"

# Configuration
DB_HOST="${DB_HOST:-localhost}"
DB_NAME="${DB_NAME:-palmed_clinic_erp}"
DB_USER="${DB_USER:-root}"
DB_PASSWORD="${DB_PASSWORD:-}"
BACKEND_PORT="${BACKEND_PORT:-5000}"
ENVIRONMENT="${ENVIRONMENT:-production}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Check prerequisites
log_info "Checking prerequisites..."

if ! command -v mysql &> /dev/null; then
    log_error "MySQL client not found. Please install MySQL client."
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    log_error "Python 3 not found. Please install Python 3."
    exit 1
fi

if ! command -v pip3 &> /dev/null; then
    log_error "pip3 not found. Please install pip3."
    exit 1
fi

log_info "All prerequisites met."

# Step 2: Create backup of existing database
log_info "Creating backup of existing database..."
BACKUP_FILE="backup_${DB_NAME}_$(date +%Y%m%d_%H%M%S).sql"

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" -e "SELECT 1" > /dev/null 2>&1 || {
    log_error "Cannot connect to MySQL. Check credentials."
    exit 1
}

mysqldump -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" "$DB_NAME" > "$BACKUP_FILE" 2>/dev/null || {
    log_warn "Backup failed or database doesn't exist yet. Continuing..."
}

log_info "Backup created: $BACKUP_FILE"

# Step 3: Deploy database schema
log_info "Deploying database schema v2..."

mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" < scripts/db_schema_v2.sql || {
    log_error "Failed to deploy database schema. Restoring from backup..."
    mysql -h "$DB_HOST" -u "$DB_USER" -p"$DB_PASSWORD" < "$BACKUP_FILE"
    exit 1
}

log_info "Database schema deployed successfully."

# Step 4: Install Python dependencies
log_info "Installing Python dependencies..."

pip3 install -r scripts/requirements.txt || {
    log_error "Failed to install Python dependencies."
    exit 1
}

log_info "Python dependencies installed."

# Step 5: Set environment variables
log_info "Setting up environment variables..."

if [ ! -f .env ]; then
    log_info "Creating .env file..."
    cat > .env << EOF
# Database Configuration
DB_HOST=$DB_HOST
DB_NAME=$DB_NAME
DB_USER=$DB_USER
DB_PASSWORD=$DB_PASSWORD
DB_PORT=3306

# JWT Configuration
JWT_SECRET=$(openssl rand -base64 32)

# Server Configuration
FLASK_ENV=$ENVIRONMENT
PORT=$BACKEND_PORT
EOF
    log_info ".env file created. Please update with actual values if needed."
fi

# Step 6: Test the backend
log_info "Testing backend startup..."

timeout 10 python3 app_v2.py &
TEST_PID=$!

sleep 3

if kill -0 $TEST_PID 2>/dev/null; then
    log_info "Backend started successfully."
    kill $TEST_PID 2>/dev/null || true
else
    log_error "Backend failed to start."
    exit 1
fi

# Step 7: Verify database connectivity
log_info "Verifying database connectivity..."

python3 << EOF
import mysql.connector
try:
    conn = mysql.connector.connect(
        host='$DB_HOST',
        user='$DB_USER',
        password='$DB_PASSWORD',
        database='$DB_NAME'
    )
    conn.close()
    print("[SUCCESS] Database connectivity verified")
except Exception as e:
    print(f"[ERROR] Database connection failed: {e}")
    exit(1)
EOF

# Step 8: Summary
log_info "======================================================================"
log_info "Deployment completed successfully!"
log_info "======================================================================"
echo ""
echo "Next steps:"
echo "1. Review and update .env file with actual configuration"
echo "2. Start the backend: python3 app_v2.py"
echo "3. Update frontend API service with new endpoints"
echo "4. Run comprehensive testing"
echo "5. Monitor logs for any issues"
echo ""
echo "Backup file: $BACKUP_FILE"
echo "======================================================================"
