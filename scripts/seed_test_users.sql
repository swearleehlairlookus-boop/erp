-- POLMED Mobile Clinic - Test Users Seed File
-- Generated on: 2025-11-03T19:17:31.041889
-- Run this file in MySQL to create test users with proper password hashes

USE mobile_clinic_erp;

-- Create roles if they don't exist

INSERT INTO user_roles (role_name, description, permissions, is_active, created_at)
VALUES ('administrator', 'System administrator with full access', '[]', TRUE, NOW())
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    is_active = VALUES(is_active);

INSERT INTO user_roles (role_name, description, permissions, is_active, created_at)
VALUES ('doctor', 'Medical doctor', '[]', TRUE, NOW())
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    is_active = VALUES(is_active);

INSERT INTO user_roles (role_name, description, permissions, is_active, created_at)
VALUES ('nurse', 'Nurse', '[]', TRUE, NOW())
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    is_active = VALUES(is_active);

INSERT INTO user_roles (role_name, description, permissions, is_active, created_at)
VALUES ('clerk', 'Administrative clerk', '[]', TRUE, NOW())
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    is_active = VALUES(is_active);

INSERT INTO user_roles (role_name, description, permissions, is_active, created_at)
VALUES ('social_worker', 'Social worker', '[]', TRUE, NOW())
ON DUPLICATE KEY UPDATE
    description = VALUES(description),
    is_active = VALUES(is_active);

-- Create test users with hashed passwords

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('admin_main', 'admin@polmed.org', 'pbkdf2:sha256:600000$UL7ZWRtrOYnAbbv9$b18dbcf76d5a5e205c60b597ab695f00136973f9e52b9a2a551cdd55114a0fdf', 
        (SELECT id FROM user_roles WHERE role_name='administrator'), 
        'System', 'Administrator', '+27123456789', 
        NULL, 
        '["National"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('admin_alt', 'admin.test@polmed.co.za', 'pbkdf2:sha256:600000$1jeHpwhWbZgSyZYR$0985f8af3de80d29a1f0904ab92388ea2e3c081a92856a7f4cc064ac2a8b0c94', 
        (SELECT id FROM user_roles WHERE role_name='administrator'), 
        'Test', 'Administrator', '+27123456780', 
        NULL, 
        '["National"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('doctor_main', 'doctor@polmed.org', 'pbkdf2:sha256:600000$FkCGYuQYlVqyHxgC$682fcd8715f3950e00b8a0bdd6f6738fc5a19cbedac2c6888559a47497e3f804', 
        (SELECT id FROM user_roles WHERE role_name='doctor'), 
        'Dr. Jane', 'Smith', '+27123456790', 
        'MP123456', 
        '["KwaZulu-Natal"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('doctor_test', 'doctor.test@polmed.co.za', 'pbkdf2:sha256:600000$7CoCZnphs6DAvA05$8a519480c17f99f44c862a683269a5a02fe5c331c154b17cadc487bb53511a5e', 
        (SELECT id FROM user_roles WHERE role_name='doctor'), 
        'Dr. John', 'Williams', '+27123456791', 
        'MP654321', 
        '["Gauteng"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('nurse_test', 'nurse.test@polmed.co.za', 'pbkdf2:sha256:600000$wMHZLsTucbXsftEU$79a2d6001eddae479c1560179a72b5c022a57d62d00a86a9b6fbf0cc286a04dd', 
        (SELECT id FROM user_roles WHERE role_name='nurse'), 
        'Mary', 'Johnson', '+27123456792', 
        NULL, 
        '["KwaZulu-Natal"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('nurse_alt', 'nurse.alt@polmed.co.za', 'pbkdf2:sha256:600000$M47iqGZK5o26Oz6o$a9d42e89d06516e219f05b6ac9650365b202e30b0d625bd6ad8cb3fa39f1c261', 
        (SELECT id FROM user_roles WHERE role_name='nurse'), 
        'Susan', 'Davis', '+27123456793', 
        NULL, 
        '["Western Cape"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('clerk_test', 'clerk.test@polmed.co.za', 'pbkdf2:sha256:600000$oruQLZcBg52Sqy3m$528f818aa054a98d4afed0c84a2ce44325e3d3d0db76e99b90a0356764c3b18f', 
        (SELECT id FROM user_roles WHERE role_name='clerk'), 
        'Sarah', 'Williams', '+27123456794', 
        NULL, 
        '["KwaZulu-Natal"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('social_test', 'social.test@polmed.co.za', 'pbkdf2:sha256:600000$HP3ZVTZC1kF1uMPM$28fa3fc6ed52d3e3ca60aae1f62f9de23d8bce747e15bc9b48d59e3a3d59c9c5', 
        (SELECT id FROM user_roles WHERE role_name='social_worker'), 
        'David', 'Brown', '+27123456795', 
        NULL, 
        '["KwaZulu-Natal"]', True, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('doctor_pending', 'doctor.pending@polmed.co.za', 'pbkdf2:sha256:600000$X53KkyjVAQmhm37A$579e1e0e424b9a554354a095c39e111fb3a15212a4c4c02fa5e274897ca5ec86', 
        (SELECT id FROM user_roles WHERE role_name='doctor'), 
        'Dr. Michael', 'Doe', '+27123456796', 
        'MP789012', 
        '["Gauteng"]', False, 
        True, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();

INSERT INTO users (username, email, password_hash, role_id, first_name, last_name, 
                  phone_number, mp_number, geographic_restrictions, is_active, 
                  requires_approval, created_at)
VALUES ('user_inactive', 'inactive.user@polmed.co.za', 'pbkdf2:sha256:600000$R8BW6NTYh8OBXzbB$cd1fc9c02c55f3a914c140811cbc88e2203e8ea6fbc4e5c041ab2b8c9bb87bc3', 
        (SELECT id FROM user_roles WHERE role_name='clerk'), 
        'Inactive', 'User', '+27123456797', 
        NULL, 
        '["Eastern Cape"]', False, 
        False, NOW())
ON DUPLICATE KEY UPDATE
    password_hash = VALUES(password_hash),
    role_id = VALUES(role_id),
    is_active = VALUES(is_active),
    requires_approval = VALUES(requires_approval),
    updated_at = NOW();