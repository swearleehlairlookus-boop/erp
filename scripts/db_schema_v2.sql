-- POLMED Mobile Clinic ERP - Comprehensive Healthcare Database Schema v2
-- Created with healthcare domain best practices
-- This schema supports multi-clinic, multi-provider healthcare delivery
-- Database: Mobile Clinic ERP
-- DBMS: MySQL 8.0+

-- ============================================================================
-- DATABASE SETUP
-- ============================================================================

-- Create database
CREATE DATABASE `mobile_clinic_erp` 
    DEFAULT CHARACTER SET utf8mb4 
    DEFAULT COLLATE utf8mb4_unicode_ci;

-- Use the database
USE `mobile_clinic_erp`;

-- Set MySQL specific configurations
SET sql_mode = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION';
SET foreign_key_checks = 1;
SET GLOBAL time_zone = '+02:00'; -- South Africa Standard Time

-- ============================================================================
-- 1. CORE SYSTEM TABLES
-- ============================================================================

-- User roles with permissions
CREATE TABLE user_roles (
    id INT PRIMARY KEY AUTO_INCREMENT,
    role_name VARCHAR(50) UNIQUE NOT NULL,
    description VARCHAR(255),
    permissions JSON,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_role_name (role_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System users (staff, doctors, admin)
CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone_number VARCHAR(20),
    mp_number VARCHAR(50),
    license_number VARCHAR(100),
    specialization VARCHAR(100),
    geographic_restrictions JSON,
    assigned_province VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    requires_approval BOOLEAN DEFAULT FALSE,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES user_roles(id),
    INDEX idx_email (email),
    INDEX idx_role_id (role_id),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Audit log for compliance
CREATE TABLE audit_log (
    id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT,
    table_name VARCHAR(100),
    record_id INT,
    action VARCHAR(20),
    old_values JSON,
    new_values JSON,
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    INDEX idx_user_id (user_id),
    INDEX idx_action (action),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 2. PATIENT MANAGEMENT TABLES
-- ============================================================================

-- Patients (South African context with PALMED integration)
CREATE TABLE patients (
    id INT PRIMARY KEY AUTO_INCREMENT,
    medical_aid_number VARCHAR(50),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    date_of_birth DATE NOT NULL,
    gender ENUM('Male', 'Female', 'Other') NOT NULL,
    id_number VARCHAR(20) UNIQUE,
    phone_number VARCHAR(20) NOT NULL,
    email VARCHAR(100),
    physical_address VARCHAR(500),
    province VARCHAR(100),

    -- POLMED membership
    is_polmed_member BOOLEAN DEFAULT FALSE,
    member_type VARCHAR(50),
    member_status VARCHAR(50),
    palmed_sync_date TIMESTAMP,
    
    -- Emergency contact
    emergency_contact_name VARCHAR(100),
    emergency_contact_phone VARCHAR(20),
    emergency_contact_relationship VARCHAR(50),
    
    -- Medical history
    chronic_conditions JSON,
    allergies JSON,
    current_medications JSON,
    blood_type VARCHAR(5),
    
    -- Record management
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    UNIQUE KEY unique_id_number (id_number),
    INDEX idx_medical_aid_number (medical_aid_number),
    INDEX idx_phone_number (phone_number),
    INDEX idx_is_polmed_member (is_polmed_member),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Patient contact information
CREATE TABLE patient_contacts (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    contact_type ENUM('primary', 'secondary', 'emergency', 'work', 'other') NOT NULL,
    contact_name VARCHAR(100),
    phone_number VARCHAR(20),
    email VARCHAR(100),
    relationship VARCHAR(50),
    is_preferred BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    INDEX idx_patient_id (patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 3. VISIT AND CLINICAL WORKFLOW TABLES
-- ============================================================================

-- Visits (clinical encounters)
CREATE TABLE patient_visits (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    visit_date DATE NOT NULL,
    visit_time TIME,
    visit_type ENUM('scheduled', 'walk_in', 'follow_up', 'emergency') DEFAULT 'scheduled',
    route_id INT,
    location_id INT,
    location_name VARCHAR(255),
    chief_complaint VARCHAR(500),
    
    -- Workflow tracking
    current_stage_id INT,
    current_stage VARCHAR(100),
    visit_status ENUM('check_in', 'in_progress', 'completed', 'cancelled', 'no_show') DEFAULT 'check_in',
    
    -- Documentation
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_patient_id (patient_id),
    INDEX idx_visit_date (visit_date),
    INDEX idx_visit_status (visit_status),
    INDEX idx_route_id (route_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Vital signs recorded during visit
CREATE TABLE vital_signs (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visit_id INT NOT NULL,
    
    -- Core vitals
    systolic_bp INT,
    diastolic_bp INT,
    heart_rate INT,
    temperature DECIMAL(5,2),
    respiratory_rate INT,
    oxygen_saturation INT,
    
    -- Anthropometric
    weight DECIMAL(7,2),
    height DECIMAL(7,2),
    bmi DECIMAL(5,2),
    
    -- Metabolic
    blood_glucose DECIMAL(7,2),
    
    -- Additional measurements
    additional_measurements JSON,
    
    -- Assessment notes
    assessment_notes TEXT,
    
    -- Recording information
    recorded_by INT,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id) ON DELETE CASCADE,
    FOREIGN KEY (recorded_by) REFERENCES users(id),
    INDEX idx_visit_id (visit_id),
    INDEX idx_recorded_at (recorded_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Clinical workflow stages
CREATE TABLE workflow_stages (
    id INT PRIMARY KEY AUTO_INCREMENT,
    stage_name VARCHAR(100) NOT NULL,
    stage_order INT NOT NULL,
    description VARCHAR(255),
    required_user_roles JSON,
    requires_signature BOOLEAN DEFAULT FALSE,
    duration_minutes INT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_stage_order (stage_order)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Clinical notes per visit stage
CREATE TABLE clinical_notes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visit_id INT NOT NULL,
    note_type ENUM('assessment', 'diagnosis', 'treatment', 'referral', 'counseling', 'closure', 'other') NOT NULL,
    content TEXT NOT NULL,
    
    -- Clinical coding
    icd10_codes JSON,
    medications_prescribed JSON,
    
    -- Follow-up
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,
    follow_up_reason VARCHAR(255),
    
    -- Documentation
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    is_final BOOLEAN DEFAULT FALSE,
    
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_visit_id (visit_id),
    INDEX idx_note_type (note_type),
    INDEX idx_created_by (created_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 4. REFERRAL SYSTEM
-- ============================================================================

CREATE TABLE referrals (
    id INT PRIMARY KEY AUTO_INCREMENT,
    patient_id INT NOT NULL,
    visit_id INT,
    referral_type ENUM('internal', 'external') NOT NULL,
    from_stage VARCHAR(100) NOT NULL,
    to_stage VARCHAR(100),
    
    -- External referral details
    external_provider VARCHAR(255),
    facility_name VARCHAR(255),
    department VARCHAR(100),
    
    -- Referral details
    reason TEXT NOT NULL,
    clinical_summary TEXT,
    urgency ENUM('routine', 'urgent', 'emergency') DEFAULT 'routine',
    notes TEXT,
    
    -- Status tracking
    status ENUM('pending', 'sent', 'accepted', 'completed', 'cancelled') DEFAULT 'pending',
    appointment_date DATE,
    appointment_time TIME,
    
    -- Documentation
    created_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id) ON DELETE SET NULL,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_patient_id (patient_id),
    INDEX idx_status (status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 5. PRESCRIPTION & MEDICATION MANAGEMENT
-- ============================================================================

-- Drug database (South African medicines)
CREATE TABLE drug_database (
    id INT PRIMARY KEY AUTO_INCREMENT,
    drug_name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    drug_class VARCHAR(100),
    strength VARCHAR(50),
    dosage_form VARCHAR(50),
    route_of_admin VARCHAR(50),
    manufacturer VARCHAR(255),
    registration_number VARCHAR(100),
    is_controlled BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY unique_drug (drug_name, strength),
    INDEX idx_generic_name (generic_name),
    INDEX idx_drug_class (drug_class)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Prescriptions
CREATE TABLE prescriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    visit_id INT NOT NULL,
    patient_id INT NOT NULL,
    
    -- Drug information
    drug_id INT,
    custom_drug_name VARCHAR(255),
    dosage VARCHAR(100) NOT NULL,
    route ENUM('oral', 'injection', 'topical', 'inhalation', 'other') DEFAULT 'oral',
    frequency VARCHAR(100) NOT NULL,
    duration VARCHAR(100),
    quantity_prescribed INT,
    
    -- Instructions
    instructions TEXT,
    special_instructions TEXT,
    
    -- Dates
    start_date DATE NOT NULL,
    end_date DATE,
    
    -- Status
    status ENUM('active', 'dispensed', 'completed', 'cancelled') DEFAULT 'active',
    
    -- Documentation
    prescribed_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
    FOREIGN KEY (drug_id) REFERENCES drug_database(id) ON DELETE SET NULL,
    FOREIGN KEY (prescribed_by) REFERENCES users(id),
    INDEX idx_patient_id (patient_id),
    INDEX idx_visit_id (visit_id),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 6. ROUTE & LOCATION MANAGEMENT
-- ============================================================================

-- Locations (Police stations, schools, community centers)
CREATE TABLE locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    location_name VARCHAR(255) NOT NULL,
    location_type ENUM('police_station', 'school', 'community_center', 'clinic', 'hospital', 'other') NOT NULL,
    address VARCHAR(500) NOT NULL,
    city VARCHAR(100),
    province VARCHAR(100) NOT NULL,
    gps_latitude DECIMAL(10, 8),
    gps_longitude DECIMAL(11, 8),
    
    -- Contact
    contact_person VARCHAR(100),
    contact_phone VARCHAR(20),
    contact_email VARCHAR(100),
    
    -- Capacity
    capacity INT,
    
    -- Facilities
    has_power BOOLEAN DEFAULT TRUE,
    has_water BOOLEAN DEFAULT TRUE,
    has_waiting_area BOOLEAN DEFAULT TRUE,
    additional_notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    INDEX idx_province (province),
    INDEX idx_location_type (location_type),
    INDEX idx_is_active (is_active)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Routes (scheduled clinic visits to locations)
CREATE TABLE routes (
    id INT PRIMARY KEY AUTO_INCREMENT,
    route_name VARCHAR(255) NOT NULL,
    description TEXT,
    province VARCHAR(100) NOT NULL,
    route_type ENUM('Police Stations', 'Schools', 'Community Centers', 'Mixed') DEFAULT 'Mixed',
    
    -- Schedule
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    start_time TIME,
    end_time TIME,
    
    -- Capacity
    max_appointments_per_day INT DEFAULT 50,
    total_locations INT DEFAULT 0,
    
    -- Status
    status ENUM('draft', 'published', 'active', 'completed') DEFAULT 'draft',
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Documentation
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_province (province),
    INDEX idx_status (status),
    INDEX idx_start_date (start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Route locations (many-to-many between routes and locations with timing)
CREATE TABLE route_locations (
    id INT PRIMARY KEY AUTO_INCREMENT,
    route_id INT NOT NULL,
    location_id INT NOT NULL,
    
    -- Visit details
    visit_date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    max_appointments INT DEFAULT 20,
    
    -- Status
    status ENUM('scheduled', 'active', 'completed', 'cancelled') DEFAULT 'scheduled',
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (route_id) REFERENCES routes(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id),
    UNIQUE KEY unique_route_location_date (route_id, location_id, visit_date),
    INDEX idx_visit_date (visit_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 7. APPOINTMENT MANAGEMENT
-- ============================================================================

-- Appointment slots (generated from route locations)
CREATE TABLE appointments (
    id INT PRIMARY KEY AUTO_INCREMENT,
    route_location_id INT NOT NULL,
    patient_id INT,
    
    -- Appointment details
    appointment_date DATE NOT NULL,
    appointment_time TIME NOT NULL,
    duration_minutes INT DEFAULT 30,
    
    -- Booking information
    booked_by_name VARCHAR(100) NOT NULL,
    booked_by_phone VARCHAR(20) NOT NULL,
    booked_by_email VARCHAR(100),
    booking_reference VARCHAR(50) UNIQUE,
    
    -- Special requirements
    special_requirements VARCHAR(500),
    
    -- Status
    status ENUM('available', 'booked', 'completed', 'cancelled', 'no_show') DEFAULT 'available',
    
    -- Documentation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (route_location_id) REFERENCES route_locations(id) ON DELETE CASCADE,
    FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE SET NULL,
    INDEX idx_appointment_date (appointment_date),
    INDEX idx_status (status),
    INDEX idx_patient_id (patient_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 8. INVENTORY MANAGEMENT
-- ============================================================================

-- Asset categories
CREATE TABLE asset_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    calibration_frequency_months INT,
    depreciation_rate DECIMAL(5,2),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Assets (medical equipment, furniture, etc.)
CREATE TABLE assets (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asset_tag VARCHAR(50) UNIQUE NOT NULL,
    serial_number VARCHAR(100),
    asset_name VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    manufacturer VARCHAR(255),
    model VARCHAR(100),
    
    -- Financial
    purchase_date DATE NOT NULL,
    purchase_cost DECIMAL(12,2),
    current_value DECIMAL(12,2),
    depreciation_amount DECIMAL(12,2),
    
    -- Warranty
    warranty_expiry DATE,
    warranty_provider VARCHAR(255),
    
    -- Location and assignment
    location VARCHAR(255),
    assigned_to INT,
    
    -- Maintenance
    status ENUM('operational', 'maintenance', 'faulty', 'retired') DEFAULT 'operational',
    last_maintenance_date DATE,
    next_maintenance_date DATE,
    maintenance_notes TEXT,
    
    -- Documentation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES asset_categories(id),
    FOREIGN KEY (assigned_to) REFERENCES users(id),
    INDEX idx_asset_tag (asset_tag),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Asset maintenance log
CREATE TABLE asset_maintenance (
    id INT PRIMARY KEY AUTO_INCREMENT,
    asset_id INT NOT NULL,
    maintenance_date DATE NOT NULL,
    maintenance_type ENUM('preventive', 'corrective', 'calibration') NOT NULL,
    description TEXT,
    cost DECIMAL(10,2),
    performed_by VARCHAR(255),
    next_due_date DATE,
    notes TEXT,
    created_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (asset_id) REFERENCES assets(id) ON DELETE CASCADE,
    FOREIGN KEY (created_by) REFERENCES users(id),
    INDEX idx_asset_id (asset_id),
    INDEX idx_maintenance_date (maintenance_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Consumable item categories
CREATE TABLE consumable_categories (
    id INT PRIMARY KEY AUTO_INCREMENT,
    category_name VARCHAR(100) NOT NULL UNIQUE,
    description VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_category_name (category_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Consumable items (medicines, supplies)
CREATE TABLE consumables (
    id INT PRIMARY KEY AUTO_INCREMENT,
    item_code VARCHAR(50) UNIQUE NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    generic_name VARCHAR(255),
    strength VARCHAR(50),
    dosage_form VARCHAR(50),
    unit_of_measure VARCHAR(20) NOT NULL,
    category_id INT NOT NULL,
    
    -- Stock levels
    reorder_level INT DEFAULT 10,
    max_stock_level INT DEFAULT 1000,
    
    -- Storage
    storage_temperature_min DECIMAL(5,2),
    storage_temperature_max DECIMAL(5,2),
    is_controlled_substance BOOLEAN DEFAULT FALSE,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (category_id) REFERENCES consumable_categories(id),
    UNIQUE KEY unique_item (item_code),
    INDEX idx_item_name (item_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Suppliers
CREATE TABLE suppliers (
    id INT PRIMARY KEY AUTO_INCREMENT,
    supplier_name VARCHAR(255) NOT NULL UNIQUE,
    contact_person VARCHAR(100),
    phone VARCHAR(20),
    email VARCHAR(100),
    address VARCHAR(500),
    tax_number VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_supplier_name (supplier_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inventory stock (batches of consumables)
CREATE TABLE inventory_stock (
    id INT PRIMARY KEY AUTO_INCREMENT,
    consumable_id INT NOT NULL,
    batch_number VARCHAR(100) NOT NULL,
    supplier_id INT,
    
    -- Quantities
    quantity_received INT NOT NULL,
    quantity_current INT NOT NULL,
    quantity_used INT DEFAULT 0,
    
    -- Costs
    unit_cost DECIMAL(10,2),
    total_cost DECIMAL(12,2),
    
    -- Dates
    manufacture_date DATE,
    expiry_date DATE,
    received_date DATE NOT NULL,
    
    -- Location and status
    location VARCHAR(255) DEFAULT 'Mobile Clinic',
    status ENUM('Active', 'Low Stock', 'Expired', 'Recalled') DEFAULT 'Active',
    
    -- Documentation
    received_by INT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    FOREIGN KEY (consumable_id) REFERENCES consumables(id),
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL,
    FOREIGN KEY (received_by) REFERENCES users(id),
    UNIQUE KEY unique_batch (consumable_id, batch_number),
    INDEX idx_expiry_date (expiry_date),
    INDEX idx_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Inventory usage tracking
CREATE TABLE inventory_usage (
    id INT PRIMARY KEY AUTO_INCREMENT,
    consumable_id INT NOT NULL,
    stock_id INT,
    quantity_used INT NOT NULL,
    visit_id INT,
    usage_location VARCHAR(255),
    usage_reason ENUM('patient_use', 'waste', 'expiry', 'loss', 'other'),
    notes TEXT,
    used_by INT,
    usage_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (consumable_id) REFERENCES consumables(id),
    FOREIGN KEY (stock_id) REFERENCES inventory_stock(id),
    FOREIGN KEY (visit_id) REFERENCES patient_visits(id) ON DELETE SET NULL,
    FOREIGN KEY (used_by) REFERENCES users(id),
    INDEX idx_usage_date (usage_date),
    INDEX idx_consumable_id (consumable_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- 9. REPORTING & ANALYTICS
-- ============================================================================

CREATE TABLE daily_metrics (
    id INT PRIMARY KEY AUTO_INCREMENT,
    metric_date DATE NOT NULL UNIQUE,
    
    -- Visit metrics
    total_visits INT DEFAULT 0,
    scheduled_visits INT DEFAULT 0,
    walk_in_visits INT DEFAULT 0,
    completed_visits INT DEFAULT 0,
    
    -- Patient metrics
    new_patients INT DEFAULT 0,
    returning_patients INT DEFAULT 0,
    
    -- Clinical metrics
    referrals_created INT DEFAULT 0,
    prescriptions_issued INT DEFAULT 0,
    
    -- Inventory metrics
    stock_adjustments INT DEFAULT 0,
    stock_alerts INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_metric_date (metric_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- South African provinces reference table
CREATE TABLE provinces (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    code VARCHAR(5) NOT NULL UNIQUE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_name (name),
    INDEX idx_code (code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================================
-- DEFAULT DATA INSERTION
-- ============================================================================

INSERT IGNORE INTO user_roles (id, role_name, description, permissions) VALUES
(1, 'administrator', 'Full system access', '["all"]'),
(2, 'doctor', 'Clinical staff - can diagnose and prescribe', '["patient.read","patient.create","visit.read","visit.create","prescription.create","referral.create"]'),
(3, 'nurse', 'Clinical staff - nursing and vital signs', '["patient.read","visit.read","vital_signs.create","referral.read"]'),
(4, 'clerk', 'Administrative staff - patient registration and appointments', '["patient.create","patient.read","appointment.manage"]'),
(5, 'social_worker', 'Counseling and psychosocial support', '["patient.read","referral.create","clinical_notes.create"]'),
(6, 'inventory_manager', 'Inventory management', '["inventory.all","asset.all"]'),
(7, 'finance', 'Financial operations', '["reports.financial"]'),
(8, 'viewer', 'Read-only access', '["patient.read","visit.read","reports.read"]');

INSERT IGNORE INTO workflow_stages (id, stage_name, stage_order, description, required_user_roles, requires_signature, duration_minutes) VALUES
(1, 'Registration', 1, 'Patient registration and check-in', '["clerk","administrator"]', FALSE, 5),
(2, 'Nursing Assessment', 2, 'Vital signs and nursing assessment', '["nurse","administrator"]', TRUE, 15),
(3, 'Doctor Consultation', 3, 'Medical consultation and diagnosis', '["doctor","administrator"]', TRUE, 20),
(4, 'Counseling Session', 4, 'Psychosocial support', '["social_worker","administrator"]', TRUE, 15),
(5, 'Closure', 5, 'Visit closure and follow-up planning', '["clerk","nurse","doctor"]', TRUE, 5);

INSERT IGNORE INTO asset_categories (id, category_name, description, calibration_frequency_months, depreciation_rate) VALUES
(1, 'Medical Equipment', 'Diagnostic and therapeutic equipment', 12, 15.0),
(2, 'Vehicles', 'Mobile clinic vehicles', 24, 20.0),
(3, 'Furniture', 'Office and clinical furniture', 60, 10.0),
(4, 'IT Equipment', 'Computers and networking equipment', 36, 25.0),
(5, 'Consumable Supplies', 'General supplies and consumables', 6, 100.0);

INSERT IGNORE INTO consumable_categories (id, category_name, description) VALUES
(1, 'Medications', 'Pharmaceutical products'),
(2, 'Consumable Supplies', 'General medical supplies'),
(3, 'First Aid', 'First aid supplies'),
(4, 'PPE', 'Personal protective equipment'),
(5, 'Diagnostic Supplies', 'Testing and diagnostic supplies');

INSERT IGNORE INTO provinces (id, name, code) VALUES
(1, 'Eastern Cape', 'EC'),
(2, 'Free State', 'FS'),
(3, 'Gauteng', 'GP'),
(4, 'KwaZulu-Natal', 'KZN'),
(5, 'Limpopo', 'LP'),
(6, 'Mpumalanga', 'MP'),
(7, 'Northern Cape', 'NC'),
(8, 'North West', 'NW'),
(9, 'Western Cape', 'WC');
