# 🚀 Dayflow HRMS

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Framework-Flask%203.0.2-green.svg)](https://flask.palletsprojects.com/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-blueviolet.svg)](https://www.docker.com/)
[![MySQL](https://img.shields.io/badge/Database-MySQL%208.0-orange.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](#license)

**Dayflow HRMS** is a modern, full-stack Human Resource Management System built with Python Flask and MySQL. It features role-based access control for Admins and Employees, interactive dashboards, attendance check-in/out tracking, leave management workflows, automated payroll management, and responsive dark/light theme support.

---

## ✨ Features

- 🔐 **Authentication & Security**: OTP email verification, secure password hashing (`Werkzeug`), role-based access control, session management, and password reset flow.
- 👨‍💼 **Admin Dashboard**: Manage workforce directory, approve/reject leave requests, update employee salaries individually or in bulk, track daily attendance metrics, and view real-time system activity.
- 🧑‍💻 **Employee Portal**: Dedicated dashboard for attendance clock-in/out, leave application with status tracking, personal profile updates, and payroll viewing.
- 📅 **Attendance Manager**: Clock-in and clock-out timestamp tracking with auto-status calculations (`Present`, `Absent`, `Half Day`, `On Leave`).
- 🏖️ **Leave Manager**: Comprehensive leave request filing, leave type selection, remarking, and admin review/approval system.
- 💵 **Payroll System**: Salary structure configuration, bulk compensation updates, and employee profile link.
- 🐳 **Docker & Tunnel Ready**: Zero-configuration multi-container deployment via Docker Compose, paired with built-in HTTPS public tunneling.

---

## 🏗️ Project Architecture

```text
├── app.py                  # Main Flask entrypoint & route handling
├── auth.py                 # Authentication, OTP verification & dashboard helpers
├── employee.py             # Employee profiles and directory management
├── leave_manager.py        # Leave application & approval logic
├── attendance_manager.py   # Clock-in / clock-out tracking engine
├── payroll.py              # Salary and payroll operations
├── Dockerfile              # Production Gunicorn Docker container specification
├── docker-compose.yml      # Multi-container orchestration (web, db, tunnel)
├── init.sql                # Automatic MySQL database schema initialization
├── requirements.txt        # Python package dependencies
├── ngrok.exe               # Included utility for custom tunnel domain hosting
├── templates/              # HTML5 UI views
└── static/                 # Modern CSS design tokens, icons & JS scripts
```

---

## 🐳 Quick Start with Docker (Recommended)

Run the entire application along with a managed MySQL 8.0 database and secure public tunnel in a single command!

### Prerequisites
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 1. Launch Containers
```bash
docker compose up -d --build
```

This starts 3 containerized services:
- **`db`**: MySQL 8.0 database listening on host port `3307` with auto-initialized tables (`init.sql`) and persistent volume (`db_data`).
- **`web`**: Dayflow HRMS Flask application running on Gunicorn (`http://localhost:5000`).
- **`tunnel`**: Automated Cloudflare Tunnel exposing your local application to a secure public HTTPS URL.

### 2. View Public Access URL
To retrieve the live public HTTPS link for your friends and remote users:
```bash
docker logs dayflow_tunnel
```

### 3. Stop Containers
```bash
docker compose down
```

---

## 🌐 Public Tunneling & Custom Domain Setup

### Method A: Automated Cloudflare Quick Tunnel (Default)
Included directly in `docker-compose.yml`. Provides instant HTTPS access anywhere in the world without requiring open router ports or password prompts.

### Method B: Custom Subdomain via Ngrok (`https://dayflow-hrms.ngrok-free.app`)
`ngrok.exe` is pre-packaged in the project repository.

1. Sign up for a free account at [ngrok.com](https://ngrok.com).
2. Claim a free domain (e.g. `dayflow-hrms.ngrok-free.app`) under **Domains**.
3. Run the following in PowerShell:
   ```powershell
   .\ngrok.exe config add-authtoken <YOUR_NGROK_AUTHTOKEN>
   .\ngrok.exe http 5000 --url=dayflow-hrms.ngrok-free.app
   ```

---

## 💻 Manual Local Development Setup

If you prefer running the application without Docker:

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Database Environment
Ensure MySQL is running locally and set the database environment variables (or rely on default values):

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DB_HOST` | Database host address | `localhost` |
| `DB_USER` | MySQL Username | `root` |
| `DB_PASSWORD` | MySQL Password | `Sridhar1234$` |
| `DB_NAME` | MySQL Database Name | `dayflow` |

### 3. Initialize Database Tables
Execute `init.sql` against your MySQL database:
```bash
mysql -u root -p < init.sql
```

### 4. Run Application
```bash
python app.py
```
Open `http://localhost:5000` in your web browser.

---

## 🗄️ Database Schema

The database consists of 5 relational tables:

1. **`users`**: Account credentials, employee IDs, roles (`Admin` / `Employee`), email verification status.
2. **`employee_profiles`**: Personal profile details, address, job title, department, salary structure.
3. **`leave_requests`**: Applied leave records, status (`Pending`, `Approved`, `Rejected`), admin comments.
4. **`attendance`**: Daily check-in/out timestamps and attendance status.
5. **`email_verification`**: OTP codes, expiration timestamps, and usage flags.

---

## 🛣️ Key Application Routes

| Path | Access | Description |
| :--- | :--- | :--- |
| `/` | Public | Home landing page; auto-redirects to dashboard or auth |
| `/auth` | Public | Authentication portal (Sign In / Sign Up) |
| `/verify` | Public | OTP Email verification screen |
| `/employee/dashboard` | Employee | Main employee metrics & quick action portal |
| `/admin/dashboard` | Admin | System overview, pending leaves & attendance metrics |
| `/attendance/page` | All Roles | Attendance clock-in / clock-out interface |
| `/leave/manage` | All Roles | Leave request application and management portal |
| `/payroll` | Admin | Salary management and employee compensation list |
| `/admin/employees` | Admin | Full workforce directory management |
| `/profile` | All Roles | Personal profile viewing and editor |

---

## 📄 License

This project is licensed under the **MIT License**. Free to use, modify, and distribute for educational and commercial applications.
