-- ============================================================
--  Rental Property MIS — MySQL Database Schema (FINAL)
--  CSC-458 · Bahria University Karachi · Spring 2026
--  Version: 3.1 — Added UPDATE trigger and property status
--
--  Changes from v3.0:
--    ✅ Added BEFORE UPDATE trigger for lease active enforcement
--    ✅ Added status field to properties_property (ACTIVE/ARCHIVED)
-- ============================================================

CREATE DATABASE IF NOT EXISTS rental_mis
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE rental_mis;


-- ============================================================
-- 1. LOCATION
-- Standardised area/neighbourhood lookup.
-- Prevents free-text typos ("Gulshan" vs "Gulshan-e-Iqbal").
-- ============================================================
CREATE TABLE location (
    id      INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name    VARCHAR(100) NOT NULL UNIQUE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO location (name) VALUES
  ('Gulshan-e-Iqbal'), ('DHA'), ('Clifton'), ('PECHS'),
  ('North Nazimabad'), ('Nazimabad'), ('Korangi'), ('Landhi'),
  ('Saddar'), ('Malir'), ('Bahria Town'), ('F.B. Area'),
  ('Scheme 33'), ('Johar'), ('Buffer Zone');


-- ============================================================
-- 2. CUSTOM USER
-- Central auth table. role field drives all RBAC logic.
-- Password is bcrypt-hashed by Django automatically.
-- ============================================================
CREATE TABLE accounts_customuser (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(150) NOT NULL UNIQUE,
    email           VARCHAR(254) NOT NULL UNIQUE,
    password        VARCHAR(128) NOT NULL,
    first_name      VARCHAR(150) NOT NULL DEFAULT '',
    last_name       VARCHAR(150) NOT NULL DEFAULT '',
    is_staff        TINYINT(1)   NOT NULL DEFAULT 0,
    is_active       TINYINT(1)   NOT NULL DEFAULT 1,
    is_superuser    TINYINT(1)   NOT NULL DEFAULT 0,
    date_joined     DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_login      DATETIME     NULL,
    full_name       VARCHAR(200) NOT NULL DEFAULT '',
    phone           VARCHAR(20)  NULL,
    role            VARCHAR(20)  NOT NULL DEFAULT 'TENANT',

    CONSTRAINT chk_role
        CHECK (role IN ('ADMIN','MANAGER','STAFF','OWNER','TENANT'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_user_role ON accounts_customuser(role);


-- ============================================================
-- 3. PROPERTY
-- A building or address containing one or more units.
-- owner_id links to an OWNER-role user.
-- status allows soft-archiving of properties without deleting.
-- ============================================================
CREATE TABLE properties_property (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    address         TEXT         NOT NULL,
    location_id     INT UNSIGNED NOT NULL,
    owner_id        INT UNSIGNED NOT NULL,
    status          VARCHAR(10)  NOT NULL DEFAULT 'ACTIVE',
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_property_location
        FOREIGN KEY (location_id) REFERENCES location(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_property_owner
        FOREIGN KEY (owner_id) REFERENCES accounts_customuser(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT chk_property_status
        CHECK (status IN ('ACTIVE','ARCHIVED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_property_owner    ON properties_property(owner_id);
CREATE INDEX idx_property_location ON properties_property(location_id);
CREATE INDEX idx_property_status   ON properties_property(status);


-- ============================================================
-- 4. UNIT
-- A single rentable space within a Property.
-- unit_number is unique per property (not system-wide).
-- status drives availability filtering across the whole system:
--   VACANT     → appears in lease creation dropdown
--   OCCUPIED   → set automatically when a lease is created
--   MAINTENANCE→ set when a CRITICAL ticket is opened
-- ============================================================
CREATE TABLE properties_unit (
    id              INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    property_id     INT UNSIGNED  NOT NULL,
    unit_number     VARCHAR(50)   NOT NULL,
    unit_type       VARCHAR(20)   NOT NULL DEFAULT 'APARTMENT',
    bedrooms        INT UNSIGNED  NOT NULL DEFAULT 0,
    monthly_rent    DECIMAL(12,2) NOT NULL,
    status          VARCHAR(15)   NOT NULL DEFAULT 'VACANT',
    updated_at      DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_unit_property
        FOREIGN KEY (property_id) REFERENCES properties_property(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    -- One unit_number per property (not system-wide)
    CONSTRAINT uq_unit_per_property
        UNIQUE (property_id, unit_number),

    CONSTRAINT chk_unit_type
        CHECK (unit_type IN ('APARTMENT','SHOP','STUDIO','HOUSE','OTHER')),

    CONSTRAINT chk_unit_status
        CHECK (status IN ('VACANT','OCCUPIED','MAINTENANCE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_unit_property ON properties_unit(property_id);
CREATE INDEX idx_unit_status   ON properties_unit(status);


-- ============================================================
-- 5. TENANT
-- Core tenant record. Optionally linked to CustomUser for
-- portal login. Never hard-deleted — use status=INACTIVE.
--
-- account_balance: cached running credit/debit.
--   Positive  = credit (tenant has overpaid, applied to next invoice)
--   Negative  = debt  (tenant has an outstanding balance)
--   Updated atomically alongside every payment and invoice creation.
--   Source of truth for reports is the formula B=(P×M)−ΣR,
--   but account_balance is kept in sync for fast UI lookups.
-- ============================================================
CREATE TABLE tenants_tenant (
    id                  INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    user_id             INT UNSIGNED  NULL UNIQUE,
    full_name           VARCHAR(200)  NOT NULL,
    email               VARCHAR(254)  NOT NULL,
    phone               VARCHAR(20)   NOT NULL,
    cnic                CHAR(13)      NOT NULL UNIQUE,
    profession          VARCHAR(100)  NULL,
    emergency_contact   VARCHAR(200)  NULL,
    account_balance     DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    status              VARCHAR(10)   NOT NULL DEFAULT 'ACTIVE',
    id_document         VARCHAR(500)  NULL,
    created_at          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at          DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_tenant_user
        FOREIGN KEY (user_id) REFERENCES accounts_customuser(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT chk_tenant_status
        CHECK (status IN ('ACTIVE','INACTIVE'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_tenant_status ON tenants_tenant(status);
CREATE INDEX idx_tenant_cnic   ON tenants_tenant(cnic);


-- ============================================================
-- 6. LEASE
-- A formal rental agreement between a Tenant and a Unit.
--
-- ONE ACTIVE LEASE PER UNIT — enforcement strategy:
--   ✅ BEFORE INSERT TRIGGER
--   ✅ BEFORE UPDATE TRIGGER (prevents reactivation conflicts)
--   Both raise SQLSTATE '45000' if rule would be violated.
--   Django's clean() method adds an application-layer check.
-- ============================================================
CREATE TABLE leases_lease (
    id              INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    tenant_id       INT UNSIGNED  NOT NULL,
    unit_id         INT UNSIGNED  NOT NULL,
    start_date      DATE          NOT NULL,
    end_date        DATE          NULL,
    monthly_rent    DECIMAL(12,2) NOT NULL,
    deposit_amount  DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    deposit_paid    TINYINT(1)    NOT NULL DEFAULT 0,
    is_active       TINYINT(1)    NOT NULL DEFAULT 1,
    notes           TEXT          NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_lease_tenant
        FOREIGN KEY (tenant_id) REFERENCES tenants_tenant(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_lease_unit
        FOREIGN KEY (unit_id) REFERENCES properties_unit(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    -- end_date must be on or after start_date (NULL = month-to-month, allowed)
    CONSTRAINT chk_lease_dates
        CHECK (end_date IS NULL OR end_date >= start_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_lease_tenant      ON leases_lease(tenant_id);
CREATE INDEX idx_lease_unit        ON leases_lease(unit_id);
CREATE INDEX idx_lease_is_active   ON leases_lease(is_active);
-- Composite: used by every active-lease lookup query
CREATE INDEX idx_lease_unit_active ON leases_lease(unit_id, is_active);


-- ============================================================
-- TRIGGER: One active lease per unit (INSERT)
-- ============================================================
DELIMITER $$

CREATE TRIGGER trg_one_active_lease_per_unit_insert
BEFORE INSERT ON leases_lease
FOR EACH ROW
BEGIN
    IF NEW.is_active = 1 THEN
        IF (
            SELECT COUNT(*)
            FROM leases_lease
            WHERE unit_id = NEW.unit_id
              AND is_active = 1
        ) > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT =
                    'Cannot create lease: this unit already has an active lease. '
                    'Terminate the existing lease before creating a new one.';
        END IF;
    END IF;
END$$


-- ============================================================
-- TRIGGER: One active lease per unit (UPDATE)
-- Prevents reactivating an old lease if another is already active.
-- ============================================================
CREATE TRIGGER trg_one_active_lease_per_unit_update
BEFORE UPDATE ON leases_lease
FOR EACH ROW
BEGIN
    IF NEW.is_active = 1 AND OLD.is_active = 0 THEN
        IF (
            SELECT COUNT(*)
            FROM leases_lease
            WHERE unit_id = NEW.unit_id
              AND is_active = 1
              AND id != NEW.id
        ) > 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT =
                    'Cannot reactivate lease: this unit already has an active lease.';
        END IF;
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- 7. INVOICE
-- One invoice per active lease per calendar month.
-- UNIQUE(lease_id, period_month) prevents duplicate billing.
-- ============================================================
CREATE TABLE finance_invoice (
    id              INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    invoice_number  VARCHAR(30)   NOT NULL UNIQUE,
    lease_id        INT UNSIGNED  NOT NULL,
    period_month    DATE          NOT NULL,
    amount_due      DECIMAL(12,2) NOT NULL,
    due_date        DATE          NOT NULL,
    status          VARCHAR(10)   NOT NULL DEFAULT 'UNPAID',
    notes           TEXT          NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    -- THE most important business constraint — one invoice per month per lease
    CONSTRAINT uq_invoice_per_month
        UNIQUE (lease_id, period_month),

    CONSTRAINT fk_invoice_lease
        FOREIGN KEY (lease_id) REFERENCES leases_lease(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT chk_invoice_status
        CHECK (status IN ('UNPAID','PARTIAL','PAID')),

    CONSTRAINT chk_amount_due_non_negative
        CHECK (amount_due >= 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_invoice_lease   ON finance_invoice(lease_id);
CREATE INDEX idx_invoice_status  ON finance_invoice(status);
CREATE INDEX idx_invoice_period  ON finance_invoice(period_month);


-- ============================================================
-- 8. PAYMENT
-- A single payment transaction against an invoice.
-- ============================================================
CREATE TABLE finance_payment (
    id              INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    invoice_id      INT UNSIGNED  NOT NULL,
    amount_paid     DECIMAL(12,2) NOT NULL,
    payment_method  VARCHAR(15)   NOT NULL DEFAULT 'CASH',
    reference_code  VARCHAR(100)  NULL,
    recorded_by_id  INT UNSIGNED  NOT NULL,
    date_paid       DATE          NOT NULL,
    notes           TEXT          NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_payment_invoice
        FOREIGN KEY (invoice_id) REFERENCES finance_invoice(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_payment_recorded_by
        FOREIGN KEY (recorded_by_id) REFERENCES accounts_customuser(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT chk_payment_method
        CHECK (payment_method IN ('CASH','BANK_TRANSFER','EASYPAISA','JAZZCASH','CHEQUE')),

    CONSTRAINT chk_amount_paid_positive
        CHECK (amount_paid > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_payment_invoice        ON finance_payment(invoice_id);
CREATE INDEX idx_payment_date           ON finance_payment(date_paid);
CREATE INDEX idx_payment_invoice_amount ON finance_payment(invoice_id, amount_paid);


-- ============================================================
-- 9. MAINTENANCE TICKET
-- ============================================================
CREATE TABLE maintenance_ticket (
    id              INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    unit_id         INT UNSIGNED  NOT NULL,
    reported_by_id  INT UNSIGNED  NOT NULL,
    assigned_to_id  INT UNSIGNED  NULL,
    title           VARCHAR(200)  NOT NULL,
    description     TEXT          NOT NULL,
    urgency         VARCHAR(10)   NOT NULL DEFAULT 'MEDIUM',
    status          VARCHAR(15)   NOT NULL DEFAULT 'OPEN',
    cost            DECIMAL(10,2) NULL,
    created_at      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resolved_at     DATETIME      NULL,
    updated_at      DATETIME      NULL     ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_ticket_unit
        FOREIGN KEY (unit_id) REFERENCES properties_unit(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT fk_ticket_reported_by
        FOREIGN KEY (reported_by_id) REFERENCES accounts_customuser(id)
        ON DELETE RESTRICT ON UPDATE CASCADE,

    CONSTRAINT fk_ticket_assigned_to
        FOREIGN KEY (assigned_to_id) REFERENCES accounts_customuser(id)
        ON DELETE SET NULL ON UPDATE CASCADE,

    CONSTRAINT chk_ticket_urgency
        CHECK (urgency IN ('LOW','MEDIUM','HIGH','CRITICAL')),

    CONSTRAINT chk_ticket_status
        CHECK (status IN ('OPEN','IN_PROGRESS','RESOLVED','CLOSED')),

    CONSTRAINT chk_resolved_after_created
        CHECK (resolved_at IS NULL OR resolved_at >= created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_ticket_unit   ON maintenance_ticket(unit_id);
CREATE INDEX idx_ticket_status ON maintenance_ticket(status);


-- ============================================================
-- 10. AUDIT LOG
-- ============================================================
CREATE TABLE audit_auditlog (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    actor_id    INT UNSIGNED NULL,
    action      VARCHAR(50)  NOT NULL,
    description TEXT         NOT NULL,
    timestamp   DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    seen        TINYINT(1)   NOT NULL DEFAULT 0,

    CONSTRAINT fk_audit_actor
        FOREIGN KEY (actor_id) REFERENCES accounts_customuser(id)
        ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_audit_actor     ON audit_auditlog(actor_id);
CREATE INDEX idx_audit_seen      ON audit_auditlog(seen);
CREATE INDEX idx_audit_timestamp ON audit_auditlog(timestamp);


-- ============================================================
-- 11. NOTIFICATION (Email + SMS Log)
-- ============================================================
CREATE TABLE notifications_notification (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    recipient_id    INT UNSIGNED NOT NULL,
    channel         VARCHAR(5)   NOT NULL DEFAULT 'EMAIL',
    subject         VARCHAR(200) NOT NULL,
    body            TEXT         NOT NULL,
    status          VARCHAR(12)  NOT NULL DEFAULT 'SENT',
    sent_at         DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_notification_recipient
        FOREIGN KEY (recipient_id) REFERENCES accounts_customuser(id)
        ON DELETE CASCADE ON UPDATE CASCADE,

    CONSTRAINT chk_channel
        CHECK (channel IN ('EMAIL','SMS')),

    CONSTRAINT chk_notif_status
        CHECK (status IN ('SENT','SIMULATED','FAILED'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_notif_recipient ON notifications_notification(recipient_id);
CREATE INDEX idx_notif_sent_at   ON notifications_notification(sent_at);


-- ============================================================
-- 12. SYSTEM SETTINGS (single-row config table)
-- ============================================================
CREATE TABLE dashboard_systemsettings (
    id                  INT UNSIGNED  AUTO_INCREMENT PRIMARY KEY,
    org_name            VARCHAR(200)  NOT NULL DEFAULT 'Rental Property MIS',
    contact_email       VARCHAR(254)  NULL,
    contact_phone       VARCHAR(20)   NULL,
    currency_symbol     VARCHAR(5)    NOT NULL DEFAULT 'PKR',
    late_fee_percent    DECIMAL(5,2)  NOT NULL DEFAULT 0.00,
    grace_period_days   INT UNSIGNED  NOT NULL DEFAULT 0,
    logo                VARCHAR(500)  NULL,
    about_content       TEXT          NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO dashboard_systemsettings (org_name, currency_symbol)
VALUES ('Rental Property MIS', 'PKR');


-- ============================================================
-- VIEWS
-- ============================================================

-- V1: Active tenant summary with full property/unit context
CREATE OR REPLACE VIEW v_active_tenant_summary AS
SELECT
    t.id            AS tenant_id,
    t.full_name     AS tenant_name,
    t.phone,
    t.cnic,
    t.account_balance,
    t.created_at    AS admitted_on,
    l.id            AS lease_id,
    l.monthly_rent,
    l.start_date,
    l.end_date,
    l.is_active,
    u.id            AS unit_id,
    u.unit_number,
    u.unit_type,
    u.status        AS unit_status,
    p.id            AS property_id,
    p.name          AS property_name,
    loc.name        AS location_name,
    cu.full_name    AS owner_name,
    cu.id           AS owner_id
FROM tenants_tenant t
JOIN leases_lease l         ON l.tenant_id = t.id AND l.is_active = 1
JOIN properties_unit u      ON u.id = l.unit_id
JOIN properties_property p  ON p.id = u.property_id AND p.status = 'ACTIVE'
JOIN location loc           ON loc.id = p.location_id
JOIN accounts_customuser cu ON cu.id = p.owner_id
WHERE t.status = 'ACTIVE';


-- V2: Invoice + payment summary
CREATE OR REPLACE VIEW v_invoice_payment_summary AS
SELECT
    i.id                                        AS invoice_id,
    i.invoice_number,
    i.period_month,
    i.amount_due,
    i.due_date,
    i.status                                    AS invoice_status,
    i.created_at,
    l.id                                        AS lease_id,
    l.tenant_id,
    l.unit_id,
    l.monthly_rent,
    COALESCE(SUM(pay.amount_paid), 0)           AS total_paid,
    (i.amount_due - COALESCE(SUM(pay.amount_paid), 0)) AS remaining_balance
FROM finance_invoice i
JOIN leases_lease l
    ON l.id = i.lease_id
LEFT JOIN finance_payment pay
    ON pay.invoice_id = i.id
GROUP BY
    i.id, i.invoice_number, i.period_month, i.amount_due,
    i.due_date, i.status, i.created_at,
    l.id, l.tenant_id, l.unit_id, l.monthly_rent;


-- V3: Occupancy snapshot per property (only ACTIVE properties)
CREATE OR REPLACE VIEW v_property_occupancy AS
SELECT
    p.id                                                        AS property_id,
    p.name                                                      AS property_name,
    p.owner_id,
    COUNT(u.id)                                                 AS total_units,
    SUM(CASE WHEN u.status = 'OCCUPIED'    THEN 1 ELSE 0 END)  AS occupied,
    SUM(CASE WHEN u.status = 'VACANT'      THEN 1 ELSE 0 END)  AS vacant,
    SUM(CASE WHEN u.status = 'MAINTENANCE' THEN 1 ELSE 0 END)  AS under_maintenance,
    ROUND(
        SUM(CASE WHEN u.status = 'OCCUPIED' THEN 1 ELSE 0 END)
        / NULLIF(COUNT(u.id), 0) * 100
    , 1)                                                        AS occupancy_rate_pct
FROM properties_property p
LEFT JOIN properties_unit u ON u.property_id = p.id
WHERE p.status = 'ACTIVE'
GROUP BY p.id, p.name, p.owner_id;


-- ============================================================
-- CONSTRAINT + DESIGN SUMMARY (for viva reference)
-- ============================================================
-- Q: How do you prevent two active leases on the same unit?
-- A: Two triggers (INSERT and UPDATE) plus Django clean().
--
-- Q: How do you prevent duplicate invoicing?
-- A: UNIQUE(lease_id, period_month).
--
-- Q: Why RESTRICT on Tenant → Lease FK delete?
-- A: Financial history must be preserved. Soft-delete only.
--
-- Q: Why CASCADE on Property → Unit?
-- A: If a property is removed, all its units go with it.
--    (Note: Leases are RESTRICT, so cascade fails safely if leases exist.)
--
-- Q: Why SET NULL on AuditLog → actor?
-- A: Preserves the audit entry even if the user is deleted.
--
-- Q: Why add status to Property?
-- A: Enables soft-archiving. Archived properties are excluded from
--    active dashboards and dropdowns but keep history intact.
-- ============================================================