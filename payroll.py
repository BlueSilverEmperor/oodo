from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.secret_key = 'your_secure_secret_key_here'

# ================= DATABASE CONFIGURATION =================
DB_CONFIG = {
    'host': 'localhost',
    'database': 'dayflow',
    'user': 'root',
    'password': 'Shreesha@1'
}

def ensure_tables_exist(conn):
    """Ensures users and employee_profiles tables exist in dayflow database."""
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
            );
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
            );
        """)
        conn.commit()
    except Error as e:
        print(f"Error creating tables: {e}")
    finally:
        cursor.close()

def get_db_connection():
    """Establishes and returns a connection to the MySQL database 'dayflow', creating it if missing."""
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


def seed_demo_data(conn):
    """Insert demo admin/employee rows when the users table is empty."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        if not user_count:
            cursor.execute("""
                INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
                VALUES
                    ('EMP001', 'admin@example.com', 'demo', 'Admin', TRUE),
                    ('EMP002', 'employee@example.com', 'demo', 'Employee', TRUE),
                    ('EMP003', 'employee2@example.com', 'demo', 'Employee', TRUE)
            """)
            cursor.execute("""
                INSERT INTO employee_profiles (user_id, first_name, last_name, job_title, department, salary_structure)
                VALUES
                    (1, 'Admin', 'User', 'System Administrator', 'Management', 90000.00),
                    (2, 'Asha', 'Rao', 'Software Engineer', 'Engineering', 55000.00),
                    (3, 'Rahul', 'Mehta', 'HR Associate', 'Human Resources', 42000.00)
            """)
            conn.commit()
            return

        cursor.execute("SELECT user_id FROM users WHERE employee_id = 'EMP003'")
        extra = cursor.fetchone()
        if extra:
            extra_user_id = extra[0]
        else:
            cursor.execute("""
                INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
                VALUES ('EMP003', 'employee2@example.com', 'demo', 'Employee', TRUE)
            """)
            extra_user_id = cursor.lastrowid

        cursor.execute("SELECT profile_id FROM employee_profiles WHERE user_id = %s", (extra_user_id,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO employee_profiles (user_id, first_name, last_name, job_title, department, salary_structure)
                VALUES (%s, 'Rahul', 'Mehta', 'HR Associate', 'Human Resources', 42000.00)
            """, (extra_user_id,))
            conn.commit()
    except Error as e:
        conn.rollback()
        print(f"Error seeding demo data: {e}")
    finally:
        cursor.close()


# ================= FLASK ROUTES =================

@app.route('/')
def payroll():
    if 'user_id' not in session:
        return render_template('payroll.html')
    
    if not session.get('role'):
        session['role'] = 'Admin'
    
    conn = get_db_connection()
    if conn:
        seed_demo_data(conn)
    if not conn:
        flash("Database connection failed. Check your config.", "error")
        return render_template('payroll.html')
        
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
        employees = cursor.fetchall()
        return render_template('payroll.html', employees=employees)
    finally:
        cursor.close()
        conn.close()

@app.route('/payroll/add-employee', methods=['POST'])
def add_employee():
    if 'user_id' not in session:
        flash("Unauthorized action. Please log in first.", "error")
        return redirect(url_for('payroll'))

    employee_id = request.form.get('employee_id', '').strip()
    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    job_title = request.form.get('job_title', '').strip()
    department = request.form.get('department', '').strip()
    salary_str = request.form.get('salary_structure', '0').strip()
    password = request.form.get('password', 'demo').strip() or 'demo'

    if not employee_id or not first_name or not last_name or not email:
        flash("Please fill in all required fields (Employee ID, First Name, Last Name, Email).", "error")
        return redirect(url_for('payroll'))

    try:
        salary = float(salary_str)
    except ValueError:
        flash("Salary structure must be a valid number.", "error")
        return redirect(url_for('payroll'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Check your config.", "error")
        return redirect(url_for('payroll'))

    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
            VALUES (%s, %s, %s, 'Employee', TRUE)
        """, (employee_id, email, password))
        
        new_user_id = cursor.lastrowid

        cursor.execute("""
            INSERT INTO employee_profiles (user_id, first_name, last_name, job_title, department, salary_structure)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (new_user_id, first_name, last_name, job_title, department, salary))

        conn.commit()
        flash(f"New employee '{first_name} {last_name}' ({employee_id}) added successfully with initial salary ${salary:,.2f}. Admin can modify their salary anytime in the list below.", "success")
    except Error as e:
        conn.rollback()
        if "Duplicate entry" in str(e) or getattr(e, 'errno', None) == 1062:
            flash(f"Error: Employee ID '{employee_id}' or Email '{email}' already exists.", "error")
        else:
            flash(f"Database error: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('payroll'))

@app.route('/payroll/update/<int:user_id>', methods=['POST'])
def update_salary(user_id):
    if 'user_id' not in session:
        flash("Unauthorized action. Please log in first.", "error")
        return redirect(url_for('payroll'))
    
    new_salary = request.form.get(f'salary_{user_id}') or request.form.get('salary_structure')
    if new_salary is None:
        flash("Salary value is required.", "error")
        return redirect(url_for('payroll'))

    try:
        salary_val = float(new_salary)
    except ValueError:
        flash("Salary must be a valid number.", "error")
        return redirect(url_for('payroll'))

    conn = get_db_connection()
    if conn:
        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE employee_profiles 
                SET salary_structure = %s 
                WHERE user_id = %s
            """, (salary_val, user_id))
            if cursor.rowcount == 0:
                cursor.execute("""
                    INSERT INTO employee_profiles (user_id, first_name, last_name, salary_structure)
                    VALUES (%s, 'Employee', '', %s)
                """, (user_id, salary_val))
            conn.commit()
            flash("Salary structure updated successfully.", "success")
        except Error as e:
            flash(f"Database error: {e}", "error")
        finally:
            cursor.close()
            conn.close()
            
    return redirect(url_for('payroll'))

@app.route('/payroll/update-bulk', methods=['POST'])
def update_salaries_bulk():
    if 'user_id' not in session:
        flash("Unauthorized action. Please log in first.", "error")
        return redirect(url_for('payroll'))

    user_ids = request.form.getlist('user_id')
    if not user_ids:
        flash("No salary values were submitted.", "error")
        return redirect(url_for('payroll'))

    conn = get_db_connection()
    if not conn:
        flash("Database connection failed. Check your config.", "error")
        return redirect(url_for('payroll'))

    cursor = conn.cursor()
    try:
        updated_count = 0
        for uid in user_ids:
            salary = request.form.get(f'salary_{uid}')
            if salary is not None:
                salary_val = float(salary)
                cursor.execute("""
                    UPDATE employee_profiles 
                    SET salary_structure = %s 
                    WHERE user_id = %s
                """, (salary_val, int(uid)))
                if cursor.rowcount == 0:
                    cursor.execute("""
                        INSERT INTO employee_profiles (user_id, first_name, last_name, salary_structure)
                        VALUES (%s, 'Employee', '', %s)
                    """, (int(uid), salary_val))
                updated_count += 1
        conn.commit()
        flash(f"Updated salary for {updated_count} employee(s).", "success")
    except (TypeError, ValueError):
        flash("Each salary must be a valid number.", "error")
    except Error as e:
        conn.rollback()
        flash(f"Database error: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('payroll'))

@app.route('/login', methods=['POST'])
def login():
    if 'user_id' in session:
        flash("You are already logged in.", "info")
        return redirect(url_for('payroll'))

    user_input = request.form.get('user_id', '').strip()
    password = request.form.get('password', '').strip()

    if not user_input or not password:
        flash("Please enter both User ID and Password.", "error")
        return redirect(url_for('payroll'))

    conn = get_db_connection()
    if conn:
        seed_demo_data(conn)
    if not conn:
        flash("Database connection failed. Check your config.", "error")
        return redirect(url_for('payroll'))

    cursor = conn.cursor(dictionary=True)
    try:
        query_val = int(user_input) if user_input.isdigit() else -1
        cursor.execute("""
            SELECT user_id, role, password_hash 
            FROM users 
            WHERE (user_id = %s OR employee_id = %s OR email = %s)
        """, (query_val, user_input, user_input))
        user = cursor.fetchone()

        if user and user['password_hash'] == password:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            flash(f"Logged in successfully as {user['role']}.", "success")
        else:
            flash("Invalid User ID or Password.", "error")
    except Error as e:
        flash(f"Database error: {e}", "error")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('payroll'))

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for('payroll'))


if __name__ == '__main__':
    app.run(debug=True)
