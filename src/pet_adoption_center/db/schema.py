"""PostgreSQL Relational Schema definitions with Constraints, Views, Triggers & Normalization."""

SCHEMA_SQL = """
-- 1. Shelters Relation (1NF, 2NF, 3NF compliant)
CREATE TABLE IF NOT EXISTS shelters (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    address VARCHAR(200) NOT NULL,
    city VARCHAR(60) NOT NULL,
    state VARCHAR(30) NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    phone VARCHAR(30) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Users Relation (Authentication & Role Based Access Control)
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(128) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    role VARCHAR(20) NOT NULL DEFAULT 'adopter' CHECK (role IN ('admin', 'adopter', 'staff')),
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(30) DEFAULT '',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Pets Relation
CREATE TABLE IF NOT EXISTS pets (
    id SERIAL PRIMARY KEY,
    shelter_id INTEGER REFERENCES shelters(id) ON DELETE SET NULL,
    name VARCHAR(60) NOT NULL,
    species VARCHAR(30) NOT NULL,
    breed VARCHAR(60) NOT NULL,
    age_years NUMERIC(4,1) NOT NULL DEFAULT 1.0 CHECK (age_years >= 0),
    gender VARCHAR(10) NOT NULL CHECK (gender IN ('Male', 'Female', 'Unknown')),
    size VARCHAR(20) NOT NULL DEFAULT 'Medium' CHECK (size IN ('Small', 'Medium', 'Large', 'Extra Large')),
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'pending', 'adopted')),
    health_status VARCHAR(100) NOT NULL DEFAULT 'Healthy & Active',
    vaccinated BOOLEAN NOT NULL DEFAULT TRUE,
    spayed_neutered BOOLEAN NOT NULL DEFAULT TRUE,
    fee NUMERIC(8,2) NOT NULL DEFAULT 50.00 CHECK (fee >= 0),
    description TEXT NOT NULL DEFAULT '',
    intake_date DATE DEFAULT CURRENT_DATE
);

-- Schema migration: Ensure shelter_id exists if pets was created previously
ALTER TABLE pets ADD COLUMN IF NOT EXISTS shelter_id INTEGER REFERENCES shelters(id) ON DELETE SET NULL;

-- 4. Medical Records Relation (1:N relationship with Pets)
CREATE TABLE IF NOT EXISTS medical_records (
    id SERIAL PRIMARY KEY,
    pet_id INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    visit_date DATE NOT NULL DEFAULT CURRENT_DATE,
    diagnosis VARCHAR(150) NOT NULL,
    treatment TEXT NOT NULL DEFAULT '',
    vet_name VARCHAR(100) NOT NULL,
    cost NUMERIC(8,2) NOT NULL DEFAULT 0.00 CHECK (cost >= 0),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Adoption Applications Relation (M:N junction between Users and Pets with attributes)
CREATE TABLE IF NOT EXISTS adoption_applications (
    id SERIAL PRIMARY KEY,
    pet_id INTEGER NOT NULL REFERENCES pets(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected', 'withdrawn')),
    applicant_name VARCHAR(100) NOT NULL,
    applicant_phone VARCHAR(30) NOT NULL,
    applicant_email VARCHAR(100) NOT NULL,
    living_space VARCHAR(50) NOT NULL DEFAULT 'Apartment',
    has_other_pets BOOLEAN NOT NULL DEFAULT FALSE,
    experience_notes TEXT NOT NULL DEFAULT '',
    reviewer_notes TEXT NOT NULL DEFAULT '',
    submitted_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. Adoption Payments / Transactions Relation (1:1 with Approved Applications)
CREATE TABLE IF NOT EXISTS adoption_payments (
    id SERIAL PRIMARY KEY,
    application_id INTEGER NOT NULL UNIQUE REFERENCES adoption_applications(id) ON DELETE CASCADE,
    amount NUMERIC(8,2) NOT NULL CHECK (amount >= 0),
    payment_method VARCHAR(30) NOT NULL DEFAULT 'Card' CHECK (payment_method IN ('Card', 'Bank Transfer', 'Cash', 'Online')),
    transaction_ref VARCHAR(64) UNIQUE NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('completed', 'refunded', 'failed')),
    paid_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Audit Log Relation (Trigger-based Change Data Capture)
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(50) NOT NULL,
    action_type VARCHAR(20) NOT NULL,
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    changed_by VARCHAR(50) DEFAULT 'system',
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Query Optimization (B-Tree indexing on foreign keys and filter columns)
CREATE INDEX IF NOT EXISTS idx_pets_shelter ON pets(shelter_id);
CREATE INDEX IF NOT EXISTS idx_pets_status ON pets(status);
CREATE INDEX IF NOT EXISTS idx_pets_species ON pets(species);
CREATE INDEX IF NOT EXISTS idx_pets_species_fee ON pets(species, fee);
CREATE INDEX IF NOT EXISTS idx_medical_pet ON medical_records(pet_id);
CREATE INDEX IF NOT EXISTS idx_applications_user ON adoption_applications(user_id);
CREATE INDEX IF NOT EXISTS idx_applications_pet ON adoption_applications(pet_id);
CREATE INDEX IF NOT EXISTS idx_applications_status ON adoption_applications(status);
CREATE INDEX IF NOT EXISTS idx_payments_app ON adoption_payments(application_id);
CREATE INDEX IF NOT EXISTS idx_audit_table ON audit_logs(table_name, changed_at DESC);

-- View 1: Denormalized Pet Catalog with Shelter and Medical Care Aggregates
CREATE OR REPLACE VIEW v_pet_details AS
SELECT 
    p.id AS pet_id,
    p.name,
    p.species,
    p.breed,
    p.age_years,
    p.gender,
    p.size,
    p.status,
    p.fee,
    s.name AS shelter_name,
    s.city AS shelter_city,
    COALESCE(COUNT(m.id), 0) AS medical_visit_count,
    COALESCE(SUM(m.cost), 0.00) AS total_medical_expenses
FROM pets p
LEFT JOIN shelters s ON p.shelter_id = s.id
LEFT JOIN medical_records m ON p.id = m.pet_id
GROUP BY p.id, s.name, s.city;

-- View 2: Complete Adoption & Revenue Ledger
CREATE OR REPLACE VIEW v_adoption_ledger AS
SELECT 
    a.id AS application_id,
    a.status AS application_status,
    p.name AS pet_name,
    p.species AS pet_species,
    u.username AS adopter_username,
    u.email AS adopter_email,
    pay.amount AS paid_amount,
    pay.payment_method,
    pay.transaction_ref,
    a.submitted_at
FROM adoption_applications a
JOIN pets p ON a.pet_id = p.id
JOIN users u ON a.user_id = u.id
LEFT JOIN adoption_payments pay ON a.id = pay.application_id;

-- PL/pgSQL Function: Trigger to log state changes in pets
CREATE OR REPLACE FUNCTION fn_audit_pet_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF (TG_OP = 'UPDATE') THEN
        INSERT INTO audit_logs (table_name, action_type, record_id, old_data, new_data, changed_by)
        VALUES (
            'pets',
            'UPDATE',
            NEW.id,
            to_jsonb(OLD),
            to_jsonb(NEW),
            CURRENT_USER
        );
        RETURN NEW;
    ELSIF (TG_OP = 'DELETE') THEN
        INSERT INTO audit_logs (table_name, action_type, record_id, old_data, changed_by)
        VALUES (
            'pets',
            'DELETE',
            OLD.id,
            to_jsonb(OLD),
            CURRENT_USER
        );
        RETURN OLD;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Attach trigger to pets table
DROP TRIGGER IF EXISTS trg_pets_audit ON pets;
CREATE TRIGGER trg_pets_audit
AFTER UPDATE OR DELETE ON pets
FOR EACH ROW EXECUTE FUNCTION fn_audit_pet_changes();
"""
