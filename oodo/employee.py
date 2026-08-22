from flask import render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash


def get_db_connection():
    db_config = {
        "host": "localhost",
        "database": "dayflow",
        "user": "root",
        "password": "Sridhar1234$",
    }
    return mysql.connector.connect(**db_config)


def admin_required():
    return "user_id" in session and session.get("role") == "Admin"


def employee_logged_in():
    return "user_id" in session and session.get("role") == "Employee"


def generate_employee_id():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute(
            """
            SELECT MAX(CAST(SUBSTRING(employee_id, 4) AS UNSIGNED))
            FROM users
            WHERE employee_id LIKE 'EMP%'
            """
        )
        result = cursor.fetchone()
        last_number = int(result[0]) if result and result[0] else 0
        return f"EMP{last_number + 1:03d}"
    except mysql.connector.Error as error:
        print("EMPLOYEE ID ERROR:", error)
        return "EMP001"
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_employee_list(search=""):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        if search:
            search_value = f"%{search}%"
            cursor.execute(
                """
                SELECT u.user_id, u.employee_id, u.email, u.role, u.is_email_verified,
                       p.first_name, p.last_name, p.phone, p.department, p.job_title,
                       p.salary_structure, p.profile_picture_url
                FROM users u
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
                WHERE u.employee_id LIKE %s OR u.email LIKE %s OR p.first_name LIKE %s
                  OR p.last_name LIKE %s OR p.department LIKE %s OR p.job_title LIKE %s
                ORDER BY u.user_id DESC
                """,
                (search_value, search_value, search_value, search_value, search_value, search_value),
            )
        else:
            cursor.execute(
                """
                SELECT u.user_id, u.employee_id, u.email, u.role, u.is_email_verified,
                       p.first_name, p.last_name, p.phone, p.department, p.job_title,
                       p.salary_structure, p.profile_picture_url
                FROM users u
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
                ORDER BY u.user_id DESC
                """
            )
        return cursor.fetchall()
    except mysql.connector.Error as error:
        print("EMPLOYEE LIST ERROR:", error)
        return []
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_employee_detail(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            """
            SELECT u.user_id, u.employee_id, u.email, u.role, u.is_email_verified, u.created_at,
                   p.profile_id, p.first_name, p.last_name, p.phone, p.address,
                   p.job_title, p.department, p.salary_structure, p.profile_picture_url
            FROM users u
            LEFT JOIN employee_profiles p ON u.user_id = p.user_id
            WHERE u.user_id = %s
            """,
            (user_id,),
        )
        return cursor.fetchone()
    except mysql.connector.Error as error:
        print("EMPLOYEE DETAILS ERROR:", error)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def add_employee_record(data):
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    department = data.get("department", "").strip()
    job_title = data.get("job_title", "").strip()
    salary = data.get("salary", "0").strip()
    role = data.get("role", "Employee")
    password = data.get("password", "")

    if not first_name or not last_name or not email or not password:
        return False, "First name, last name, email and password are required."

    if role not in ["Admin", "Employee"]:
        return False, "Invalid role."

    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    try:
        salary_value = float(salary or 0)
    except ValueError:
        return False, "Salary must be a valid number."

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute("SELECT user_id FROM users WHERE email = %s", (email,))
        if cursor.fetchone():
            return False, "Email already exists."

        employee_id = generate_employee_id()
        password_hash = generate_password_hash(password)
        cursor.execute(
            """
            INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
            VALUES (%s, %s, %s, %s, TRUE)
            """,
            (employee_id, email, password_hash, role),
        )
        user_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO employee_profiles
            (user_id, first_name, last_name, phone, address, job_title, department, salary_structure)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, first_name, last_name, phone, address, job_title, department, salary_value),
        )
        conn.commit()
        return True, f"Employee {employee_id} created successfully."
    except mysql.connector.Error as error:
        if conn:
            conn.rollback()
        print("ADD EMPLOYEE ERROR:", error)
        return False, "Unable to create employee."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def edit_employee_record(user_id, data):
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    email = data.get("email", "").strip().lower()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    department = data.get("department", "").strip()
    job_title = data.get("job_title", "").strip()
    salary = data.get("salary", "0").strip()
    role = data.get("role", "Employee")

    if not first_name or not last_name or not email:
        return False, "Required fields are missing."

    try:
        salary_value = float(salary or 0)
    except ValueError:
        return False, "Invalid salary."

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            "SELECT user_id FROM users WHERE email = %s AND user_id != %s",
            (email, user_id),
        )
        if cursor.fetchone():
            return False, "Email already used by another employee."

        cursor.execute(
            "UPDATE users SET email = %s, role = %s WHERE user_id = %s",
            (email, role, user_id),
        )
        cursor.execute(
            """
            UPDATE employee_profiles
            SET first_name = %s, last_name = %s, phone = %s, address = %s,
                job_title = %s, department = %s, salary_structure = %s
            WHERE user_id = %s
            """,
            (first_name, last_name, phone, address, job_title, department, salary_value, user_id),
        )
        conn.commit()
        return True, "Employee updated successfully."
    except mysql.connector.Error as error:
        if conn:
            conn.rollback()
        print("EDIT EMPLOYEE ERROR:", error)
        return False, "Unable to update employee."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def delete_employee_record(user_id):
    if user_id == session.get("user_id"):
        return False, "You cannot delete your own account."

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute("DELETE FROM users WHERE user_id = %s", (user_id,))
        if cursor.rowcount == 0:
            return False, "Employee not found."
        conn.commit()
        return True, "Employee deleted successfully."
    except mysql.connector.Error as error:
        if conn:
            conn.rollback()
        print("DELETE EMPLOYEE ERROR:", error)
        return False, "Unable to delete employee."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_my_profile(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True, dictionary=True)
        cursor.execute(
            """
            SELECT p.first_name, p.last_name, p.phone, p.address, p.job_title,
                   p.department, p.profile_picture_url
            FROM employee_profiles p
            WHERE p.user_id = %s
            """,
            (user_id,),
        )
        profile = cursor.fetchone()
        if not profile:
            cursor.execute(
                """
                INSERT INTO employee_profiles
                (user_id, first_name, last_name, phone, address, job_title, department, profile_picture_url)
                VALUES (%s, '', '', '', '', '', '', '')
                """,
                (user_id,),
            )
            conn.commit()
            profile = {
                "first_name": "",
                "last_name": "",
                "phone": "",
                "address": "",
                "job_title": "",
                "department": "",
                "profile_picture_url": "",
            }
        return profile
    except mysql.connector.Error as error:
        print("MY PROFILE ERROR:", error)
        return None
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def get_profile_full_name(user_id):
    profile = get_my_profile(user_id)
    if not profile:
        return ""
    first_name = (profile.get("first_name") or "").strip()
    last_name = (profile.get("last_name") or "").strip()
    full_name = " ".join(part for part in [first_name, last_name] if part)
    return full_name or "User"


def update_my_profile(user_id, data):
    first_name = data.get("first_name", "").strip()
    last_name = data.get("last_name", "").strip()
    phone = data.get("phone", "").strip()
    address = data.get("address", "").strip()
    job_title = data.get("job_title", "").strip()
    department = data.get("department", "").strip()
    profile_picture_url = data.get("profile_picture_url", "").strip()

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute("SELECT profile_id FROM employee_profiles WHERE user_id = %s", (user_id,))
        existing_profile = cursor.fetchone()
        if existing_profile:
            cursor.execute(
                """
                UPDATE employee_profiles
                SET first_name = %s, last_name = %s, phone = %s, address = %s,
                    job_title = %s, department = %s, profile_picture_url = %s
                WHERE user_id = %s
                """,
                (first_name, last_name, phone, address, job_title, department, profile_picture_url, user_id),
            )
        else:
            cursor.execute(
                """
                INSERT INTO employee_profiles
                (user_id, first_name, last_name, phone, address, job_title, department, profile_picture_url)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (user_id, first_name, last_name, phone, address, job_title, department, profile_picture_url),
            )
        conn.commit()
        return True, "Your profile has been updated successfully."
    except mysql.connector.Error as error:
        if conn:
            conn.rollback()
        print("PROFILE UPDATE ERROR:", error)
        return False, "Unable to update profile."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def update_profile_name(user_id, first_name, last_name):
    first_name = (first_name or "").strip()
    last_name = (last_name or "").strip()
    if not first_name and not last_name:
        return False, "Name cannot be empty."

    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(buffered=True)
        cursor.execute(
            """
            SELECT profile_id FROM employee_profiles WHERE user_id = %s
            """,
            (user_id,),
        )
        if cursor.fetchone():
            cursor.execute(
                "UPDATE employee_profiles SET first_name = %s, last_name = %s WHERE user_id = %s",
                (first_name, last_name, user_id),
            )
        else:
            cursor.execute(
                "INSERT INTO employee_profiles (user_id, first_name, last_name, phone, address, job_title, department, profile_picture_url) VALUES (%s, %s, %s, '', '', '', '', '')",
                (user_id, first_name, last_name),
            )
        conn.commit()
        return True, "Name updated successfully."
    except mysql.connector.Error as error:
        if conn:
            conn.rollback()
        print("PROFILE NAME UPDATE ERROR:", error)
        return False, "Unable to update name."
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def admin_employees_page(search=""):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("auth"))
    employee_list = get_employee_list(search)
    return render_template("employees.html", employees=employee_list, search=search)


def add_employee_form_page():
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("auth"))
    return render_template("add_employee.html", next_employee_id=generate_employee_id())


def employee_details_page(user_id):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("auth"))
    employee = get_employee_detail(user_id)
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))
    return render_template("employee_details.html", employee=employee)


def edit_employee_form_page(user_id):
    if not admin_required():
        flash("Admin access required.", "danger")
        return redirect(url_for("auth"))
    employee = get_employee_detail(user_id)
    if not employee:
        flash("Employee not found.", "danger")
        return redirect(url_for("employees"))
    return render_template("edit_employee.html", employee=employee)


def my_profile_page():
    if not employee_logged_in():
        flash("Employee login required.", "danger")
        return redirect(url_for("auth"))
    profile = get_my_profile(session["user_id"])
    if profile is None:
        flash("Unable to load profile.", "danger")
        return redirect(url_for("employee_dashboard"))
    return render_template("my_profile.html", profile=profile)


def employees_route_page():
    return admin_employees_page(request.args.get("search", "").strip())