# Rental Property MIS
**CSC-458 · Management Information Systems · Bahria University Karachi · Spring 2026**

A web-based Management Information System for rental property management built with Django 6, MySQL, HTMX, Alpine.js, and AdminLTE 3.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0 (Python) |
| Database | MySQL 8.x |
| Frontend | Django Templates + AdminLTE 3 |
| Interactivity | HTMX + Alpine.js |
| PDF Generation | WeasyPrint |

---

## Local Setup

### 1. Prerequisites
- Python 3.12+
- MySQL 8.x (running)
- `default-libmysqlclient-dev` (Ubuntu: `sudo apt install default-libmysqlclient-dev`)

### 2. Clone & Virtual Environment
```bash
git clone <repo-url>
cd "Property & Rental MIS"
python3 -m venv venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
pip install -r requirements.txt
```

### 3. Database Setup
Run the following SQL as MySQL root **once** to create the database and a dedicated user:

```sql
-- Run in MySQL as root:
CREATE DATABASE IF NOT EXISTS rental_mis
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE USER 'rental_mis_user'@'localhost' IDENTIFIED BY 'rental_mis_pass';

GRANT ALL PRIVILEGES ON rental_mis.* TO 'rental_mis_user'@'localhost';

FLUSH PRIVILEGES;
```

> **Security note:** Change `rental_mis_pass` to a strong password and update your `.env` file accordingly. Never commit `.env` to git.

### 4. Environment Variables
Copy the example file and fill in your values:
```bash
cp .env.example .env
# Edit .env — set SECRET_KEY and DB_PASSWORD at minimum
```

### 5. Run Migrations & Seed Data
```bash
python manage.py migrate
python manage.py seed_locations
python manage.py createsuperuser  # create Admin account
```

### 6. Run Development Server
```bash
python manage.py runserver
```
Visit `http://127.0.0.1:8000/`

---

## Project Structure

```
rental_mis/        Django project root (settings, urls, wsgi)
accounts/          CustomUser model, login/logout, RBAC decorators
properties/        Property, Unit, Location models and CRUD
tenants/           Tenant model, admission (atomic), soft-delete
leases/            Lease model, expiry logic
finance/           Invoice, Payment models, balance formula, reports
dashboard/         Role-aware dashboard views and KPI computation
templates/         Base template (AdminLTE shell) + per-app templates
static/            Custom CSS, JS (app.js, dashboard-chart.js)
```

---

## User Roles

| Role | Access |
|---|---|
| ADMIN | Full system access |
| MANAGER | All operational features |
| STAFF | Record payments, update maintenance tickets |
| OWNER | Read-only portfolio view (own properties) |
| TENANT | Own balance, receipts, maintenance requests |

---

## Development Phases

- **Phase 1** — Core MVP (auth, properties, tenants, invoices, payments, dashboards)
- **Phase 2** — PDF receipts, email notifications, audit trail, maintenance, reports
- **Phase 3** — Tenant portal, document vault, occupancy charts, UI polish
