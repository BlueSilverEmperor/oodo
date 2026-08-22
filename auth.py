from flask import Flask, render_template, request, redirect, url_for, flash, session
import mysql.connector
from werkzeug.security import generate_password_hash, check_password_hash
import random
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)
app.secret_key = "dayflow_secret_key_2026"


# =========================================================
# MYSQL CONFIG
# =========================================================

db_config = {
    "host": "localhost",
    "user": "root",
    "password": "YOUR_MYSQL_PASSWORD",
    "database": "dayflow"
}


# =========================================================
# EMAIL CONFIG
# =========================================================

SENDER_EMAIL = "YOUR_GMAIL@gmail.com"
APP_PASSWORD = "YOUR_16_CHARACTER_APP_PASSWORD"


def get_db_connection():
    return mysql.connector.connect(**db_config)


# =========================================================
# SEND EMAIL
# =========================================================

def send_email(receiver_email, subject, body):

    try:

        message = MIMEMultipart()

        message["From"] = SENDER_EMAIL
        message["To"] = receiver_email
        message["Subject"] = subject

        message.attach(
            MIMEText(body, "plain")
        )

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()

        server.login(
            SENDER_EMAIL,
            APP_PASSWORD
        )

        server.sendmail(
            SENDER_EMAIL,
            receiver_email,
            message.as_string()
        )

        server.quit()

        print(
            f"Email sent successfully to {receiver_email}"
        )

        return True

    except Exception as error:

        print(
            "EMAIL ERROR:",
            error
        )

        return False


# =========================================================
# CREATE EMAIL VERIFICATION OTP
# =========================================================

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
            (user_id,)
        )

        otp = str(
            random.randint(
                100000,
                999999
            )
        )

        expires_at = (
            datetime.now()
            + timedelta(minutes=5)
        )

        cursor.execute(
            """
            INSERT INTO email_verification
            (
                user_id,
                otp_code,
                expires_at,
                is_used
            )
            VALUES (%s, %s, %s, %s)
            """,
            (
                user_id,
                otp,
                expires_at,
                False
            )
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

        return send_email(
            email,
            subject,
            body
        )

    except mysql.connector.Error as error:

        print(
            "OTP DATABASE ERROR:",
            error
        )

        return False

    finally:

        if cursor:
            cursor.close()

        if conn and conn.is_connected():
            conn.close()


# =========================================================
# PASSWORD VALIDATION FUNCTION
# =========================================================

def validate_password(password):

    if len(password) < 8:
        return "Password must contain at least 8 characters."

    if not any(
        char.isupper()
        for char in password
    ):
        return "Password must contain an uppercase letter."

    if not any(
        char.islower()
        for char in password
    ):
        return "Password must contain a lowercase letter."

    if not any(
        char.isdigit()
        for char in password
    ):
        return "Password must contain a number."

    return None


# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    return redirect(
        url_for("auth")
    )


# =========================================================
# AUTH
# =========================================================

@app.route(
    "/auth",
    methods=["GET", "POST"]
)
def auth():

    if request.method == "POST":

        action = request.form.get(
            "action"
        )


        # =================================================
        # SIGN UP
        # =================================================

        if action == "signup":

            employee_id = request.form.get(
                "employee_id",
                ""
            ).strip().upper()

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            password = request.form.get(
                "password",
                ""
            )

            confirm_password = request.form.get(
                "confirm_password",
                ""
            )

            role = request.form.get(
                "role",
                ""
            )


            if (
                not employee_id
                or not email
                or not password
                or not confirm_password
                or not role
            ):

                flash(
                    "All fields are required.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "auth",
                        mode="signup"
                    )
                )


            if password != confirm_password:

                flash(
                    "Passwords do not match.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "auth",
                        mode="signup"
                    )
                )


            password_error = (
                validate_password(
                    password
                )
            )

            if password_error:

                flash(
                    password_error,
                    "danger"
                )

                return redirect(
                    url_for(
                        "auth",
                        mode="signup"
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
                        "auth",
                        mode="signup"
                    )
                )


            conn = None
            cursor = None


            try:

                conn = get_db_connection()

                cursor = conn.cursor(
                    dictionary=True
                )


                cursor.execute(
                    """
                    SELECT user_id
                    FROM users
                    WHERE email = %s
                    OR employee_id = %s
                    """,
                    (
                        email,
                        employee_id
                    )
                )


                if cursor.fetchone():

                    flash(
                        "Email or Employee ID already exists.",
                        "danger"
                    )

                    return redirect(
                        url_for(
                            "auth",
                            mode="signup"
                        )
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
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        employee_id,
                        email,
                        password_hash,
                        role,
                        False
                    )
                )


                conn.commit()

                user_id = (
                    cursor.lastrowid
                )


                session[
                    "verification_user_id"
                ] = user_id

                session[
                    "verification_email"
                ] = email


                success = (
                    generate_verification_otp(
                        user_id,
                        email
                    )
                )


                if success:

                    flash(
                        "OTP sent to your email.",
                        "success"
                    )

                else:

                    flash(
                        "Account created, but OTP could not be sent.",
                        "danger"
                    )


                return redirect(
                    url_for("verify")
                )


            except mysql.connector.Error as error:

                print(
                    "SIGNUP ERROR:",
                    error
                )

                flash(
                    "Database error.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "auth",
                        mode="signup"
                    )
                )


            finally:

                if cursor:
                    cursor.close()

                if (
                    conn
                    and conn.is_connected()
                ):
                    conn.close()


        # =================================================
        # SIGN IN
        # =================================================

        elif action == "signin":

            email = request.form.get(
                "email",
                ""
            ).strip().lower()

            password = request.form.get(
                "password",
                ""
            )


            conn = None
            cursor = None


            try:

                conn = get_db_connection()

                cursor = conn.cursor(
                    dictionary=True
                )


                cursor.execute(
                    """
                    SELECT *
                    FROM users
                    WHERE email = %s
                    """,
                    (email,)
                )


                user = cursor.fetchone()


                if not user:

                    flash(
                        "Invalid email or password.",
                        "danger"
                    )

                    return redirect(
                        url_for("auth")
                    )


                try:

                    password_valid = (
                        check_password_hash(
                            user[
                                "password_hash"
                            ],
                            password
                        )
                    )

                except ValueError:

                    password_valid = False


                if not password_valid:

                    flash(
                        "Invalid email or password.",
                        "danger"
                    )

                    return redirect(
                        url_for("auth")
                    )


                if not user[
                    "is_email_verified"
                ]:

                    session[
                        "verification_user_id"
                    ] = user["user_id"]

                    session[
                        "verification_email"
                    ] = user["email"]

                    flash(
                        "Please verify your email.",
                        "danger"
                    )

                    return redirect(
                        url_for("verify")
                    )


                session.clear()

                session["user_id"] = (
                    user["user_id"]
                )

                session["employee_id"] = (
                    user["employee_id"]
                )

                session["email"] = (
                    user["email"]
                )

                session["role"] = (
                    user["role"]
                )


                if user["role"] == "Admin":

                    return redirect(
                        url_for(
                            "admin_dashboard"
                        )
                    )


                return redirect(
                    url_for(
                        "employee_dashboard"
                    )
                )


            except mysql.connector.Error as error:

                print(
                    "LOGIN ERROR:",
                    error
                )

                flash(
                    "Unable to sign in.",
                    "danger"
                )

                return redirect(
                    url_for("auth")
                )


            finally:

                if cursor:
                    cursor.close()

                if (
                    conn
                    and conn.is_connected()
                ):
                    conn.close()


    return render_template(
        "auth.html"
    )


# =========================================================
# VERIFY ACCOUNT OTP
# =========================================================

@app.route(
    "/verify",
    methods=["GET", "POST"]
)
def verify():

    user_id = session.get(
        "verification_user_id"
    )

    email = session.get(
        "verification_email"
    )


    if not user_id or not email:

        return redirect(
            url_for("auth")
        )


    if request.method == "POST":

        entered_otp = request.form.get(
            "otp",
            ""
        ).strip()


        conn = None
        cursor = None


        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                dictionary=True
            )


            cursor.execute(
                """
                SELECT *
                FROM email_verification
                WHERE user_id = %s
                AND is_used = FALSE
                ORDER BY verification_id DESC
                LIMIT 1
                """,
                (user_id,)
            )


            otp_record = (
                cursor.fetchone()
            )


            if not otp_record:

                flash(
                    "No active OTP found.",
                    "danger"
                )

                return redirect(
                    url_for("verify")
                )


            if (
                datetime.now()
                >
                otp_record["expires_at"]
            ):

                flash(
                    "OTP expired.",
                    "danger"
                )

                return redirect(
                    url_for("verify")
                )


            if (
                entered_otp
                != otp_record["otp_code"]
            ):

                flash(
                    "Invalid OTP.",
                    "danger"
                )

                return redirect(
                    url_for("verify")
                )


            cursor.execute(
                """
                UPDATE users
                SET is_email_verified = TRUE
                WHERE user_id = %s
                """,
                (user_id,)
            )


            cursor.execute(
                """
                UPDATE email_verification
                SET is_used = TRUE
                WHERE verification_id = %s
                """,
                (
                    otp_record[
                        "verification_id"
                    ],
                )
            )


            conn.commit()


            session.pop(
                "verification_user_id",
                None
            )

            session.pop(
                "verification_email",
                None
            )


            flash(
                "Email verified successfully!",
                "success"
            )


            return redirect(
                url_for("auth")
            )


        finally:

            if cursor:
                cursor.close()

            if (
                conn
                and conn.is_connected()
            ):
                conn.close()


    return render_template(
        "verify.html",
        email=email
    )


# =========================================================
# RESEND OTP
# =========================================================

@app.route(
    "/resend-otp",
    methods=["POST"]
)
def resend_otp():

    user_id = session.get(
        "verification_user_id"
    )

    email = session.get(
        "verification_email"
    )


    if not user_id or not email:

        return redirect(
            url_for("auth")
        )


    success = generate_verification_otp(
        user_id,
        email
    )


    if success:

        flash(
            "New OTP sent.",
            "success"
        )

    else:

        flash(
            "Unable to send OTP.",
            "danger"
        )


    return redirect(
        url_for("verify")
    )


# =========================================================
# FORGOT PASSWORD
# =========================================================

@app.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()


        conn = None
        cursor = None


        try:

            conn = get_db_connection()

            cursor = conn.cursor(
                dictionary=True
            )


            cursor.execute(
                """
                SELECT user_id, email
                FROM users
                WHERE email = %s
                """,
                (email,)
            )


            user = cursor.fetchone()


            if not user:

                flash(
                    "No account found with this email.",
                    "danger"
                )

                return redirect(
                    url_for(
                        "forgot_password"
                    )
                )


            reset_otp = str(
                random.randint(
                    100000,
                    999999
                )
            )


            session[
                "reset_user_id"
            ] = user["user_id"]

            session[
                "reset_email"
            ] = user["email"]

            session[
                "reset_otp"
            ] = reset_otp

            session[
                "reset_otp_expiry"
            ] = (
                datetime.now()
                + timedelta(minutes=5)
            ).timestamp()


            subject = (
                "Dayflow - Password Reset OTP"
            )


            body = f"""
Hello,

Your Dayflow password reset OTP is:

{reset_otp}

This OTP expires in 5 minutes.

If you did not request a password reset,
you can ignore this email.

Dayflow HRMS
"""


            success = send_email(
                email,
                subject,
                body
            )


            if success:

                flash(
                    "Password reset OTP sent to your email.",
                    "success"
                )


                return redirect(
                    url_for(
                        "reset_password"
                    )
                )


            flash(
                "Unable to send OTP.",
                "danger"
            )


        finally:

            if cursor:
                cursor.close()

            if (
                conn
                and conn.is_connected()
            ):
                conn.close()


    return render_template(
        "forgot_password.html"
    )


# =========================================================
# RESET PASSWORD
# =========================================================

@app.route(
    "/reset-password",
    methods=["GET", "POST"]
)
def reset_password():

    if "reset_email" not in session:

        return redirect(
            url_for(
                "forgot_password"
            )
        )


    if request.method == "POST":

        entered_otp = request.form.get(
            "otp",
            ""
        ).strip()

        new_password = request.form.get(
            "new_password",
            ""
        )

        confirm_password = request.form.get(
            "confirm_password",
            ""
        )


        stored_otp = session.get(
            "reset_otp"
        )


        expiry = session.get(
            "reset_otp_expiry"
        )


        if (
            not expiry
            or datetime.now().timestamp()
            > expiry
        ):

            flash(
                "OTP expired. Request a new password reset.",
                "danger"
            )

            return redirect(
                url_for(
                    "forgot_password"
                )
            )


        if entered_otp != stored_otp:

            flash(
                "Invalid OTP.",
                "danger"
            )

            return redirect(
                url_for(
                    "reset_password"
                )
            )


        if new_password != confirm_password:

            flash(
                "Passwords do not match.",
                "danger"
            )

            return redirect(
                url_for(
                    "reset_password"
                )
            )


        password_error = (
            validate_password(
                new_password
            )
        )


        if password_error:

            flash(
                password_error,
                "danger"
            )

            return redirect(
                url_for(
                    "reset_password"
                )
            )


        password_hash = (
            generate_password_hash(
                new_password
            )
        )


        conn = None
        cursor = None


        try:

            conn = get_db_connection()

            cursor = conn.cursor()


            cursor.execute(
                """
                UPDATE users
                SET password_hash = %s
                WHERE user_id = %s
                """,
                (
                    password_hash,
                    session[
                        "reset_user_id"
                    ]
                )
            )


            conn.commit()


            session.pop(
                "reset_user_id",
                None
            )

            session.pop(
                "reset_email",
                None
            )

            session.pop(
                "reset_otp",
                None
            )

            session.pop(
                "reset_otp_expiry",
                None
            )


            flash(
                "Password reset successfully! Sign in using your new password.",
                "success"
            )


            return redirect(
                url_for("auth")
            )


        finally:

            if cursor:
                cursor.close()

            if (
                conn
                and conn.is_connected()
            ):
                conn.close()


    return render_template(
        "reset_password.html",
        email=session.get(
            "reset_email"
        )
    )


# =========================================================
# EMPLOYEE DASHBOARD
# =========================================================

@app.route(
    "/employee/dashboard"
)
def employee_dashboard():

    if (
        "user_id" not in session
        or session.get("role")
        != "Employee"
    ):

        return redirect(
            url_for("auth")
        )


    return f"""
    <h1>Employee Dashboard</h1>

    <h2>
        Welcome {session['email']}
    </h2>

    <p>
        Employee ID:
        {session['employee_id']}
    </p>

    <a href="/logout">
        Logout
    </a>
    """


# =========================================================
# ADMIN DASHBOARD
# =========================================================

@app.route(
    "/admin/dashboard"
)
def admin_dashboard():

    if (
        "user_id" not in session
        or session.get("role")
        != "Admin"
    ):

        return redirect(
            url_for("auth")
        )


    return f"""
    <h1>Admin Dashboard</h1>

    <h2>
        Welcome {session['email']}
    </h2>

    <p>
        Employee ID:
        {session['employee_id']}
    </p>

    <a href="/logout">
        Logout
    </a>
    """


# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    session.clear()

    flash(
        "Logged out successfully.",
        "success"
    )

    return redirect(
        url_for("auth")
    )


# =========================================================
# RUN
# =========================================================

if __name__ == "__main__":

    app.run(
        debug=True,
        host="127.0.0.1",
        port=5000
    )