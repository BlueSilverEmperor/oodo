from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import generate_password_hash
from database import get_db_connection

import mysql.connector


# =========================================================
# BLUEPRINT
# =========================================================

employee_bp = Blueprint(
    "employee",
    __name__
)


# =========================================================
# SECURITY HELPERS
# =========================================================

def admin_required():

    return (
        "user_id" in session
        and session.get("role") == "Admin"
    )


def employee_logged_in():

    return (
        "user_id" in session
        and session.get("role") == "Employee"
    )


# =========================================================
# AUTO GENERATE EMPLOYEE ID
# =========================================================

def generate_employee_id():

    conn = None
    cursor = None

    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True
        )

        cursor.execute(
            """
            SELECT MAX(
                CAST(
                    SUBSTRING(employee_id, 4)
                    AS UNSIGNED
                )
            )
            FROM users
            WHERE employee_id LIKE 'EMP%'
            """
        )

        result = cursor.fetchone()

        last_number = (
            int(result[0])
            if result and result[0]
            else 0
        )

        new_number = last_number + 1

        return f"EMP{new_number:03d}"

    except mysql.connector.Error as error:

        print(
            "EMPLOYEE ID ERROR:",
            error
        )

        return "EMP001"

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# ADMIN - EMPLOYEE LIST + SEARCH
# =========================================================

@employee_bp.route(
    "/admin/employees"
)
def employees():

    if not admin_required():

        flash(
            "Admin access required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    search = request.args.get(
        "search",
        ""
    ).strip()


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True,
            dictionary=True
        )


        if search:

            search_value = (
                f"%{search}%"
            )

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.employee_id,
                    u.email,
                    u.role,
                    u.is_email_verified,

                    p.first_name,
                    p.last_name,
                    p.phone,
                    p.department,
                    p.job_title,
                    p.salary_structure,
                    p.profile_picture_url

                FROM users u

                LEFT JOIN employee_profiles p
                    ON u.user_id = p.user_id

                WHERE
                    u.employee_id LIKE %s
                    OR u.email LIKE %s
                    OR p.first_name LIKE %s
                    OR p.last_name LIKE %s
                    OR p.department LIKE %s
                    OR p.job_title LIKE %s

                ORDER BY u.user_id DESC
                """,
                (
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value,
                    search_value
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    u.user_id,
                    u.employee_id,
                    u.email,
                    u.role,
                    u.is_email_verified,

                    p.first_name,
                    p.last_name,
                    p.phone,
                    p.department,
                    p.job_title,
                    p.salary_structure,
                    p.profile_picture_url

                FROM users u

                LEFT JOIN employee_profiles p
                    ON u.user_id = p.user_id

                ORDER BY u.user_id DESC
                """
            )


        employee_list = (
            cursor.fetchall()
        )


        return render_template(
            "employees.html",
            employees=employee_list,
            search=search
        )


    except mysql.connector.Error as error:

        print(
            "EMPLOYEE LIST ERROR:",
            error
        )

        flash(
            "Unable to load employees.",
            "danger"
        )

        return redirect(
            url_for(
                "admin_dashboard"
            )
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# ADMIN - ADD EMPLOYEE
# =========================================================

@employee_bp.route(
    "/admin/employees/add",
    methods=["GET", "POST"]
)
def add_employee():

    if not admin_required():

        flash(
            "Admin access required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    if request.method == "POST":

        first_name = request.form.get(
            "first_name",
            ""
        ).strip()

        last_name = request.form.get(
            "last_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        department = request.form.get(
            "department",
            ""
        ).strip()

        job_title = request.form.get(
            "job_title",
            ""
        ).strip()

        salary = request.form.get(
            "salary",
            "0"
        ).strip()

        role = request.form.get(
            "role",
            "Employee"
        )

        password = request.form.get(
            "password",
            ""
        )


        if (
            not first_name
            or not last_name
            or not email
            or not password
        ):

            flash(
                "First name, last name, email and password are required.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.add_employee"
                )
            )


        if role not in [
            "Admin",
            "Employee"
        ]:

            flash(
                "Invalid role.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.add_employee"
                )
            )


        if len(password) < 8:

            flash(
                "Password must be at least 8 characters.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.add_employee"
                )
            )


        try:

            salary_value = float(
                salary or 0
            )

        except ValueError:

            flash(
                "Salary must be a valid number.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.add_employee"
                )
            )


        conn = None
        cursor = None


        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                buffered=True,
                dictionary=True
            )


            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                """,
                (email,)
            )


            if cursor.fetchone():

                flash(
                    "Email already exists.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "employee.add_employee"
                    )
                )


            employee_id = (
                generate_employee_id()
            )


            password_hash = (
                generate_password_hash(
                    password
                )
            )


            cursor.execute(
                """
                INSERT INTO users
                (
                    employee_id,
                    email,
                    password_hash,
                    role,
                    is_email_verified
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    TRUE
                )
                """,
                (
                    employee_id,
                    email,
                    password_hash,
                    role
                )
            )


            user_id = (
                cursor.lastrowid
            )


            cursor.execute(
                """
                INSERT INTO employee_profiles
                (
                    user_id,
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    salary_structure
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    salary_value
                )
            )


            conn.commit()


            flash(
                f"Employee {employee_id} created successfully.",
                "success"
            )


            return redirect(
                url_for(
                    "employee.employees"
                )
            )


        except mysql.connector.Error as error:

            if conn:
                conn.rollback()

            print(
                "ADD EMPLOYEE ERROR:",
                error
            )

            flash(
                "Unable to create employee.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.add_employee"
                )
            )


        finally:

            if cursor:
                cursor.close()

            if conn and conn.is_connected():
                conn.close()


    next_employee_id = (
        generate_employee_id()
    )


    return render_template(
        "add_employee.html",
        next_employee_id=next_employee_id
    )


# =========================================================
# ADMIN - VIEW ONE EMPLOYEE
# =========================================================

@employee_bp.route(
    "/admin/employees/<int:user_id>"
)
def employee_details(user_id):

    if not admin_required():

        flash(
            "Admin access required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True,
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                u.user_id,
                u.employee_id,
                u.email,
                u.role,
                u.is_email_verified,
                u.created_at,

                p.profile_id,
                p.first_name,
                p.last_name,
                p.phone,
                p.address,
                p.job_title,
                p.department,
                p.salary_structure,
                p.profile_picture_url

            FROM users u

            LEFT JOIN employee_profiles p
                ON u.user_id = p.user_id

            WHERE u.user_id = %s
            """,
            (user_id,)
        )


        employee = (
            cursor.fetchone()
        )


        if not employee:

            flash(
                "Employee not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.employees"
                )
            )


        return render_template(
            "employee_details.html",
            employee=employee
        )


    except mysql.connector.Error as error:

        print(
            "EMPLOYEE DETAILS ERROR:",
            error
        )

        flash(
            "Unable to load employee.",
            "danger"
        )

        return redirect(
            url_for(
                "employee.employees"
            )
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# ADMIN - EDIT EMPLOYEE
# =========================================================

@employee_bp.route(
    "/admin/employees/<int:user_id>/edit",
    methods=["GET", "POST"]
)
def edit_employee(user_id):

    if not admin_required():

        flash(
            "Admin access required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True,
            dictionary=True
        )


        if request.method == "POST":

            first_name = request.form.get(
                "first_name",
                ""
            ).strip()

            last_name = request.form.get(
                "last_name",
                ""
            ).strip()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            phone = request.form.get(
                "phone",
                ""
            ).strip()

            address = request.form.get(
                "address",
                ""
            ).strip()

            department = request.form.get(
                "department",
                ""
            ).strip()

            job_title = request.form.get(
                "job_title",
                ""
            ).strip()

            salary = request.form.get(
                "salary",
                "0"
            ).strip()

            role = request.form.get(
                "role",
                "Employee"
            )


            if (
                not first_name
                or not last_name
                or not email
            ):

                flash(
                    "Required fields are missing.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "employee.edit_employee",
                        user_id=user_id
                    )
                )


            try:

                salary_value = float(
                    salary or 0
                )

            except ValueError:

                flash(
                    "Invalid salary.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "employee.edit_employee",
                        user_id=user_id
                    )
                )


            cursor.execute(
                """
                SELECT user_id
                FROM users
                WHERE email = %s
                AND user_id != %s
                """,
                (
                    email,
                    user_id
                )
            )


            if cursor.fetchone():

                flash(
                    "Email already used by another employee.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "employee.edit_employee",
                        user_id=user_id
                    )
                )


            cursor.execute(
                """
                UPDATE users

                SET
                    email = %s,
                    role = %s

                WHERE user_id = %s
                """,
                (
                    email,
                    role,
                    user_id
                )
            )


            cursor.execute(
                """
                UPDATE employee_profiles

                SET
                    first_name = %s,
                    last_name = %s,
                    phone = %s,
                    address = %s,
                    job_title = %s,
                    department = %s,
                    salary_structure = %s

                WHERE user_id = %s
                """,
                (
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    salary_value,
                    user_id
                )
            )


            conn.commit()


            flash(
                "Employee updated successfully.",
                "success"
            )


            return redirect(
                url_for(
                    "employee.employee_details",
                    user_id=user_id
                )
            )


        cursor.execute(
            """
            SELECT
                u.user_id,
                u.employee_id,
                u.email,
                u.role,

                p.first_name,
                p.last_name,
                p.phone,
                p.address,
                p.job_title,
                p.department,
                p.salary_structure

            FROM users u

            LEFT JOIN employee_profiles p
                ON u.user_id = p.user_id

            WHERE u.user_id = %s
            """,
            (user_id,)
        )


        employee = (
            cursor.fetchone()
        )


        if not employee:

            flash(
                "Employee not found.",
                "danger"
            )

            return redirect(
                url_for(
                    "employee.employees"
                )
            )


        return render_template(
            "edit_employee.html",
            employee=employee
        )


    except mysql.connector.Error as error:

        if conn:
            conn.rollback()

        print(
            "EDIT EMPLOYEE ERROR:",
            error
        )

        flash(
            "Unable to update employee.",
            "danger"
        )

        return redirect(
            url_for(
                "employee.employees"
            )
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# ADMIN - DELETE EMPLOYEE
# =========================================================

@employee_bp.route(
    "/admin/employees/<int:user_id>/delete",
    methods=["POST"]
)
def delete_employee(user_id):

    if not admin_required():

        flash(
            "Admin access required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    if user_id == session.get(
        "user_id"
    ):

        flash(
            "You cannot delete your own account.",
            "danger"
        )

        return redirect(
            url_for(
                "employee.employees"
            )
        )


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True
        )


        cursor.execute(
            """
            DELETE FROM users
            WHERE user_id = %s
            """,
            (user_id,)
        )


        if cursor.rowcount == 0:

            flash(
                "Employee not found.",
                "danger"
            )

        else:

            conn.commit()

            flash(
                "Employee deleted successfully.",
                "success"
            )


    except mysql.connector.Error as error:

        if conn:
            conn.rollback()

        print(
            "DELETE EMPLOYEE ERROR:",
            error
        )

        flash(
            "Unable to delete employee.",
            "danger"
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


    return redirect(
        url_for(
            "employee.employees"
        )
    )


# =========================================================
# EMPLOYEE - OWN PROFILE ONLY
# =========================================================

@employee_bp.route(
    "/employee/profile"
)
def my_profile():

    if not employee_logged_in():

        flash(
            "Employee login required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    # IMPORTANT:
    # Employee's ID is taken ONLY from session.
    # No user_id comes from URL.

    user_id = session[
        "user_id"
    ]


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True,
            dictionary=True
        )


        cursor.execute(
            """
            SELECT
                p.first_name,
                p.last_name,
                p.phone,
                p.address,
                p.job_title,
                p.department,
                p.profile_picture_url

            FROM employee_profiles p

            WHERE p.user_id = %s
            """,
            (user_id,)
        )


        profile = cursor.fetchone()


        # If account exists but profile row doesn't,
        # create a blank profile automatically.

        if not profile:

            cursor.execute(
                """
                INSERT INTO employee_profiles
                (
                    user_id,
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    profile_picture_url
                )

                VALUES (
                    %s,
                    '',
                    '',
                    '',
                    '',
                    '',
                    '',
                    ''
                )
                """,
                (user_id,)
            )

            conn.commit()


            profile = {
                "first_name": "",
                "last_name": "",
                "phone": "",
                "address": "",
                "job_title": "",
                "department": "",
                "profile_picture_url": ""
            }


        return render_template(
            "my_profile.html",
            profile=profile
        )


    except mysql.connector.Error as error:

        print(
            "MY PROFILE ERROR:",
            error
        )

        flash(
            "Unable to load profile.",
            "danger"
        )

        return redirect(
            url_for(
                "employee_dashboard"
            )
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# EMPLOYEE - EDIT OWN PROFILE ONLY
# =========================================================

@employee_bp.route(
    "/employee/profile/edit",
    methods=["POST"]
)
def edit_my_profile():

    if not employee_logged_in():

        flash(
            "Employee login required.",
            "danger"
        )

        return redirect(
            url_for("auth")
        )


    # THIS is what prevents editing
    # another employee.
    user_id = session[
        "user_id"
    ]


    first_name = request.form.get(
        "first_name",
        ""
    ).strip()

    last_name = request.form.get(
        "last_name",
        ""
    ).strip()

    phone = request.form.get(
        "phone",
        ""
    ).strip()

    address = request.form.get(
        "address",
        ""
    ).strip()

    job_title = request.form.get(
        "job_title",
        ""
    ).strip()

    department = request.form.get(
        "department",
        ""
    ).strip()

    profile_picture_url = request.form.get(
        "profile_picture_url",
        ""
    ).strip()


    conn = None
    cursor = None


    try:

        conn = get_db_connection()

        cursor = conn.cursor(
            buffered=True
        )


        cursor.execute(
            """
            SELECT profile_id
            FROM employee_profiles
            WHERE user_id = %s
            """,
            (user_id,)
        )


        existing_profile = (
            cursor.fetchone()
        )


        if existing_profile:

            cursor.execute(
                """
                UPDATE employee_profiles

                SET
                    first_name = %s,
                    last_name = %s,
                    phone = %s,
                    address = %s,
                    job_title = %s,
                    department = %s,
                    profile_picture_url = %s

                WHERE user_id = %s
                """,
                (
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    profile_picture_url,
                    user_id
                )
            )


        else:

            cursor.execute(
                """
                INSERT INTO employee_profiles
                (
                    user_id,
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    profile_picture_url
                )

                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    user_id,
                    first_name,
                    last_name,
                    phone,
                    address,
                    job_title,
                    department,
                    profile_picture_url
                )
            )


        conn.commit()


        flash(
            "Your profile has been updated successfully.",
            "success"
        )


    except mysql.connector.Error as error:

        if conn:
            conn.rollback()

        print(
            "PROFILE UPDATE ERROR:",
            error
        )

        flash(
            "Unable to update profile.",
            "danger"
        )


    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


    return redirect(
        url_for(
            "employee.my_profile"
        )
    )