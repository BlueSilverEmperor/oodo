from flask import render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import random
import re
import smtplib
from datetime import datetime, timedelta, date
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# =========================================================
# MYSQL CONFIG
# =========================================================

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "Sridhar1234$",
    "database": "dayflow"
}

# =========================================================
# EMAIL CONFIG
# =========================================================

SENDER_EMAIL = "darkrepear670@gmail.com"
APP_PASSWORD = "fptu fvls eweu zwmq"


def get_db_connection():
    return mysql.connector.connect(**db_config)


def send_email(receiver_email, subject, body):
    try:
        message = MIMEMultipart()
        message["From"] = SENDER_EMAIL
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.sendmail(SENDER_EMAIL, receiver_email, message.as_string())
        server.quit()
        print(f"Email sent successfully to {receiver_email}")
        return True
    except Exception as error:
        print("EMAIL ERROR:", error)
        return False


def generate_verification_otp(user_id, email):
    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE email_verification
            SET is_used = TRUE
            WHERE user_id = %s
            AND is_used = FALSE
            """,
            (user_id,),
        )

        otp = str(random.randint(100000, 999999))
        expires_at = datetime.now() + timedelta(minutes=5)

        cursor.execute(
            """
            INSERT INTO email_verification (user_id, otp_code, expires_at, is_used)
            VALUES (%s, %s, %s, %s)
            """,
            (user_id, otp, expires_at, False),
        )

        conn.commit()

        subject = "Dayflow - Email Verification OTP"
        body = f"""
Hello,

Your Dayflow verification OTP is:

{otp}

This OTP expires in 5 minutes.

Do not share this OTP with anyone.

Dayflow HRMS
"""

        return send_email(email, subject, body)

    except mysql.connector.Error as error:
        print("OTP DATABASE ERROR:", error)
        return False
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def validate_password(password):
    if len(password) < 8:
        return "Password must contain at least 8 characters."
    if not any(char.isupper() for char in password):
        return "Password must contain an uppercase letter."
    if not any(char.islower() for char in password):
        return "Password must contain a lowercase letter."
    if not any(char.isdigit() for char in password):
        return "Password must contain a number."
    return None


def auth_page():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "signup":
            return process_signup()
        elif action == "signin":
            return process_signin()

    return render_template("auth.html")


def generate_employee_id(conn):
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            SELECT employee_id
            FROM users
            WHERE employee_id LIKE 'EMP%'
            ORDER BY CAST(SUBSTRING(employee_id, 4) AS UNSIGNED) DESC
            LIMIT 1
            """
        )
        row = cursor.fetchone()

        if row and row[0]:
            match = re.search(r"(\d+)$", row[0])
            if match:
                next_number = int(match.group(1)) + 1
                return f"EMP{next_number:03d}"

        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        return f"EMP{count + 1:03d}"
    finally:
        cursor.close()


def process_signup():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")
    role = request.form.get("role", "")

    if not email or not password or not confirm_password or not role:
        flash("All fields are required.", "danger")
        return redirect(url_for("auth", mode="signup"))

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("auth", mode="signup"))

    password_error = validate_password(password)
    if password_error:
        flash(password_error, "danger")
        return redirect(url_for("auth", mode="signup"))

    if role not in ["Admin", "Employee"]:
        flash("Invalid role.", "danger")
        return redirect(url_for("auth", mode="signup"))

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE email = %s
            """,
            (email,),
        )

        if cursor.fetchone():
            flash("Email already exists.", "danger")
            return redirect(url_for("auth", mode="signup"))

        employee_id = generate_employee_id(conn)
        password_hash = generate_password_hash(password)

        cursor.execute(
            """
            INSERT INTO users (employee_id, email, password_hash, role, is_email_verified)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (employee_id, email, password_hash, role, False),
        )

        conn.commit()
        user_id = cursor.lastrowid

        session["verification_user_id"] = user_id
        session["verification_email"] = email

        success = generate_verification_otp(user_id, email)

        if success:
            flash("OTP sent to your email.", "success")
        else:
            flash("Account created, but OTP could not be sent.", "danger")

        return redirect(url_for("verify"))

    except mysql.connector.Error as error:
        print("SIGNUP ERROR:", error)
        flash("Database error.", "danger")
        return redirect(url_for("auth", mode="signup"))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def process_signin():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    conn = None
    cursor = None

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()

        if not user:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth"))

        try:
            password_valid = check_password_hash(user["password_hash"], password)
        except ValueError:
            password_valid = False

        if not password_valid:
            flash("Invalid email or password.", "danger")
            return redirect(url_for("auth"))

        if not user["is_email_verified"]:
            session["verification_user_id"] = user["user_id"]
            session["verification_email"] = user["email"]
            flash("Please verify your email.", "danger")
            return redirect(url_for("verify"))

        session.clear()
        session["user_id"] = user["user_id"]
        session["employee_id"] = user["employee_id"]
        session["email"] = user["email"]
        session["role"] = user["role"]

        if user["role"] == "Admin":
            return redirect(url_for("admin_dashboard"))

        return redirect(url_for("employee_dashboard"))

    except mysql.connector.Error as error:
        print("LOGIN ERROR:", error)
        flash("Unable to sign in.", "danger")
        return redirect(url_for("auth"))
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def verify_page():
    user_id = session.get("verification_user_id")
    email = session.get("verification_email")

    if not user_id or not email:
        return redirect(url_for("auth"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute(
                """
                SELECT *
                FROM email_verification
                WHERE user_id = %s AND is_used = FALSE
                ORDER BY verification_id DESC
                LIMIT 1
                """,
                (user_id,),
            )
            otp_record = cursor.fetchone()

            if not otp_record:
                flash("No active OTP found.", "danger")
                return redirect(url_for("verify"))

            if datetime.now() > otp_record["expires_at"]:
                flash("OTP expired.", "danger")
                return redirect(url_for("verify"))

            if entered_otp != otp_record["otp_code"]:
                flash("Invalid OTP.", "danger")
                return redirect(url_for("verify"))

            cursor.execute(
                "UPDATE users SET is_email_verified = TRUE WHERE user_id = %s",
                (user_id,),
            )
            cursor.execute(
                "UPDATE email_verification SET is_used = TRUE WHERE verification_id = %s",
                (otp_record["verification_id"],),
            )
            conn.commit()

            session.pop("verification_user_id", None)
            session.pop("verification_email", None)

            flash("Email verified successfully!", "success")
            return redirect(url_for("auth"))
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template("verify.html", email=email)


def resend_otp_action():
    user_id = session.get("verification_user_id")
    email = session.get("verification_email")

    if not user_id or not email:
        return redirect(url_for("auth"))

    success = generate_verification_otp(user_id, email)

    if success:
        flash("New OTP sent.", "success")
    else:
        flash("Unable to send OTP.", "danger")

    return redirect(url_for("verify"))


def forgot_password_page():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            cursor.execute("SELECT user_id, email FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()

            if not user:
                flash("No account found with this email.", "danger")
                return redirect(url_for("forgot_password"))

            reset_otp = str(random.randint(100000, 999999))
            session["reset_user_id"] = user["user_id"]
            session["reset_email"] = user["email"]
            session["reset_otp"] = reset_otp
            session["reset_otp_expiry"] = (datetime.now() + timedelta(minutes=5)).timestamp()

            subject = "Dayflow - Password Reset OTP"
            body = f"""
Hello,

Your Dayflow password reset OTP is:

{reset_otp}

This OTP expires in 5 minutes.

If you did not request a password reset,
you can ignore this email.

Dayflow HRMS
"""

            success = send_email(email, subject, body)

            if success:
                flash("Password reset OTP sent to your email.", "success")
                return redirect(url_for("reset_password"))

            flash("Unable to send OTP.", "danger")
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template("forgot_password.html")


def reset_password_page():
    if "reset_email" not in session:
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        stored_otp = session.get("reset_otp")
        expiry = session.get("reset_otp_expiry")

        if not expiry or datetime.now().timestamp() > expiry:
            flash("OTP expired. Request a new password reset.", "danger")
            return redirect(url_for("forgot_password"))

        if entered_otp != stored_otp:
            flash("Invalid OTP.", "danger")
            return redirect(url_for("reset_password"))

        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password"))

        password_error = validate_password(new_password)
        if password_error:
            flash(password_error, "danger")
            return redirect(url_for("reset_password"))

        password_hash = generate_password_hash(new_password)

        conn = None
        cursor = None

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE users SET password_hash = %s WHERE user_id = %s",
                (password_hash, session["reset_user_id"]),
            )
            conn.commit()

            session.pop("reset_user_id", None)
            session.pop("reset_email", None)
            session.pop("reset_otp", None)
            session.pop("reset_otp_expiry", None)

            flash("Password reset successfully! Sign in using your new password.", "success")
            return redirect(url_for("auth"))
        finally:
            if cursor:
                cursor.close()
            if conn and conn.is_connected():
                conn.close()

    return render_template("reset_password.html", email=session.get("reset_email"))


def employee_dashboard_page():
    if "user_id" not in session or session.get("role") != "Employee":
        return redirect(url_for("auth"))

    email = session.get("email") or ""
    user_name = email.split("@")[0].title() if email else "Employee"

    return render_template(
        "employee_dashboard.html",
        email=email,
        employee_id=session.get("employee_id"),
        user_id=session.get("user_id"),
        user_name=user_name,
        role="Employee",
    )


def get_admin_dashboard_activity():
    conn = None
    cursor = None
    activities = []

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            """
            SELECT COUNT(*) AS pending_count
            FROM leave_requests
            WHERE status = 'Pending'
            """
        )
        pending_row = cursor.fetchone()
        pending_count = pending_row["pending_count"] if pending_row else 0

        cursor.execute(
            """
            SELECT COUNT(*) AS today_count
            FROM attendance
            WHERE DATE(date) = %s
            """,
            (date.today(),),
        )
        today_row = cursor.fetchone()
        today_count = today_row["today_count"] if today_row else 0

        if pending_count is None:
            cursor.execute(
                """
                SELECT COUNT(*) AS pending_count
                FROM leave_requests
                WHERE status = 'Pending'
                """
            )
            pending_count = cursor.fetchone()["pending_count"]

        if today_count is None:
            cursor.execute(
                """
                SELECT COUNT(*) AS today_count
                FROM attendance
                WHERE DATE(date) = %s
                """,
                (date.today(),),
            )
            today_count = cursor.fetchone()["today_count"]

        if pending_count:
            activities.append({
                "label": "Approved",
                "badge_class": "approved",
                "text": f"{pending_count} leave request(s) are currently waiting for review."
            })

        if today_count:
            activities.append({
                "label": "Active",
                "badge_class": "active",
                "text": f"{today_count} attendance record(s) have been logged for today."
            })

        if not activities:
            activities.append({
                "label": "Updated",
                "badge_class": "approved",
                "text": "There are no pending leave requests or attendance entries today."
            })

        return activities
    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()


def admin_dashboard_page():
    if "user_id" not in session or session.get("role") != "Admin":
        return redirect(url_for("auth"))

    email = session.get("email") or ""
    user_name = email.split("@")[0].title() if email else "Admin"
    activity_items = get_admin_dashboard_activity()

    return render_template(
        "admin_dashboard.html",
        email=email,
        employee_id=session.get("employee_id"),
        user_id=session.get("user_id"),
        user_name=user_name,
        role="Admin",
        activity_items=activity_items,
    )


def logout_user():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth"))
