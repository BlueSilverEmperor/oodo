from flask import render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    'host': 'localhost',
    'database': 'dayflow',
    'user': 'root',
    'password': 'Sridhar1234$'
}


def ensure_tables_exist(conn):
    """Create payroll-related tables if they do not already exist."""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INT AUTO_INCREMENT PRIMARY KEY,
                employee_id VARCHAR(50) UNIQUE NOT NULL,
                email VARCHAR(100) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                role ENUM('Admin', 'Employee') DEFAULT 'Employee' NOT NULL,
                is_email_verified BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS employee_profiles (
                profile_id INT AUTO_INCREMENT PRIMARY KEY,
                user_id INT NOT NULL,
                first_name VARCHAR(50) NOT NULL,
                last_name VARCHAR(50) NOT NULL,
                phone VARCHAR(20),
                address TEXT,
                job_title VARCHAR(100),
                department VARCHAR(100),
                salary_structure DECIMAL(12, 2) DEFAULT 0.00,
                profile_picture_url VARCHAR(255),
                documents_path VARCHAR(255),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()


def get_db_connection():
    """Return a MySQL connection for the payroll module."""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        if connection.is_connected():
            return connection
    except Error as e:
        if getattr(e, 'errno', None) == 1049 or "Unknown database" in str(e):
            try:
                base_config = {k: v for k, v in DB_CONFIG.items() if k != 'database'}
                temp_conn = mysql.connector.connect(**base_config)
                if temp_conn.is_connected():
                    cursor = temp_conn.cursor()
                    cursor.execute("CREATE DATABASE IF NOT EXISTS dayflow")
                    cursor.close()
                    temp_conn.close()
                    connection = mysql.connector.connect(**DB_CONFIG)
                    if connection.is_connected():
                        ensure_tables_exist(connection)
                        return connection
            except Error as init_err:
                print(f"Error initializing database dayflow: {init_err}")
                return None
        else:
            print(f"Error while connecting to MySQL: {e}")
            return None
    return None


def seed_demo_data(conn):
    """Insert demo data if there are no users yet."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute("""
                INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
                VALUES
                    ('EMP001', 'admin@example.com', %s, 'Admin', TRUE),
                    ('EMP002', 'employee@example.com', %s, 'Employee', TRUE),
                    ('EMP003', 'employee2@example.com', %s, 'Employee', TRUE)
            """, (generate_password_hash('admin123'), generate_password_hash('employee123'), generate_password_hash('employee123')))
            cursor.execute("""
                INSERT INTO employee_profiles (user_id, first_name, last_name, job_title, department, salary_structure)
                VALUES
                    (1, 'Admin', 'User', 'System Administrator', 'Management', 90000.00),
                    (2, 'Asha', 'Rao', 'Software Engineer', 'Engineering', 55000.00),
                    (3, 'Rahul', 'Mehta', 'HR Associate', 'Human Resources', 42000.00)
            """)
            conn.commit()
    except Error as e:
        conn.rollback()
        print(f"Error seeding demo data: {e}")
    finally:
        cursor.close()


def get_payroll_employees():
    conn = get_db_connection()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT u.user_id, u.employee_id, u.email, u.role,
                   COALESCE(p.profile_id, 0) as profile_id,
                   COALESCE(p.first_name, u.employee_id) as first_name,
                   COALESCE(p.last_name, '') as last_name,
                   COALESCE(p.job_title, 'N/A') as job_title,
                   COALESCE(p.department, 'N/A') as department,
                   COALESCE(p.salary_structure, 0.00) as salary_structure
            FROM users u
            LEFT JOIN employee_profiles p ON u.user_id = p.user_id
            ORDER BY u.user_id ASC
        """)
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()


def payroll_page():
    if "user_id" not in session or session.get("role") != "Admin":
        flash("Please log in as an admin to access payroll.", "danger")
        return redirect(url_for("auth"))

    conn = get_db_connection()
    if conn:
        seed_demo_data(conn)
        conn.close()

    employees = get_payroll_employees()
    user_name = (session.get("email") or "Admin").split("@")[0].title()
    return render_template("admin-payroll.html", employees=employees, user_name=user_name, role='Admin', user_id=session.get('user_id'))


def add_employee_payroll():
    if "user_id" not in session or session.get("role") != "Admin":
        flash("Unauthorized action. Please log in as admin first.", "danger")
        return redirect(url_for("auth"))

    employee_id = request.form.get("employee_id", "").strip()
    first_name = request.form.get("first_name", "").strip()
    last_name = request.form.get("last_name", "").strip()
    email = request.form.get("email", "").strip()
    job_title = request.form.get("job_title", "").strip()
    department = request.form.get("department", "").strip()
    salary_str = request.form.get("salary_structure", "0").strip()
    password = request.form.get("password", "demo").strip() or "demo"

    if not employee_id or not first_name or not last_name or not email:
        flash("Please fill in Employee ID, first name, last name, and email.", "danger")
        return redirect(url_for("payroll"))

    try:
        salary = float(salary_str)
    except ValueError:
        flash("Salary must be a valid number.", "danger")
        return redirect(url_for("payroll"))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Check your config.", "danger")
        return redirect(url_for("payroll"))

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
            VALUES (%s, %s, %s, 'Employee', TRUE)
            """,
            (employee_id, email, generate_password_hash(password)),
        )
        new_user_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO employee_profiles (user_id, first_name, last_name, job_title, department, salary_structure)
            VALUES (%s, %s, %s, %s, %s, %s)
            """,
            (new_user_id, first_name, last_name, job_title, department, salary),
        )
        conn.commit()
        flash(f"Employee '{first_name} {last_name}' added successfully.", "success")
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) or getattr(e, 'errno', None) == 1062:
            flash(f"Employee ID or email already exists.", "danger")
        else:
            flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("payroll"))


def update_salary_for_user(user_id):
    if "user_id" not in session or session.get("role") != "Admin":
        flash("Unauthorized action. Please log in as admin first.", "danger")
        return redirect(url_for("auth"))

    new_salary = request.form.get(f"salary_{user_id}") or request.form.get("salary_structure")
    if new_salary is None:
        flash("Salary value is required.", "danger")
        return redirect(url_for("payroll"))

    try:
        salary_val = float(new_salary)
    except ValueError:
        flash("Salary must be a valid number.", "danger")
        return redirect(url_for("payroll"))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Check your config.", "danger")
        return redirect(url_for("payroll"))

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            UPDATE employee_profiles
            SET salary_structure = %s
            WHERE user_id = %s
            """,
            (salary_val, user_id),
        )
        if cursor.rowcount == 0:
            cursor.execute(
                """
                INSERT INTO employee_profiles (user_id, first_name, last_name, salary_structure)
                VALUES (%s, 'Employee', '', %s)
                """,
                (user_id, salary_val),
            )
        conn.commit()
        flash("Salary updated successfully.", "success")
    except Error as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("payroll"))


def update_salaries_bulk():
    if "user_id" not in session or session.get("role") != "Admin":
        flash("Unauthorized action. Please log in as admin first.", "danger")
        return redirect(url_for("auth"))

    user_ids = request.form.getlist("user_id")
    if not user_ids:
        flash("No salary values were submitted.", "danger")
        return redirect(url_for("payroll"))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Check your config.", "danger")
        return redirect(url_for("payroll"))

    cursor = conn.cursor()
    updated_count = 0
    try:
        for uid in user_ids:
            salary = request.form.get(f"salary_{uid}")
            if salary is not None:
                try:
                    salary_val = float(salary)
                except ValueError:
                    flash("Each salary must be a valid number.", "danger")
                    return redirect(url_for("payroll"))
                cursor.execute(
                    """
                    UPDATE employee_profiles
                    SET salary_structure = %s
                    WHERE user_id = %s
                    """,
                    (salary_val, int(uid)),
                )
                if cursor.rowcount == 0:
                    cursor.execute(
                        """
                        INSERT INTO employee_profiles (user_id, first_name, last_name, salary_structure)
                        VALUES (%s, 'Employee', '', %s)
                        """,
                        (int(uid), salary_val),
                    )
                updated_count += 1
        conn.commit()
        flash(f"Updated salary for {updated_count} employee(s).", "success")
    except Error as e:
        conn.rollback()
        flash(f"Database error: {e}", "danger")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("payroll"))
