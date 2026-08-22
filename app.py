from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import mysql.connector
from mysql.connector import Error
from leave_manager import apply_leave, get_leave_requests, update_leave_status
from attendance_manager import clock_in_out, get_attendance_records
from payroll import payroll_page, add_employee_payroll, update_salary_for_user, update_salaries_bulk
from employee import (
    admin_required,
    employee_logged_in,
    add_employee_record,
    edit_employee_record,
    delete_employee_record,
    get_my_profile,
    get_profile_full_name,
    update_profile_name,
    admin_employees_page,
    add_employee_form_page,
    employee_details_page,
    edit_employee_form_page,
    my_profile_page,
)
from auth import (
    auth_page,
    verify_page,
    resend_otp_action,
    forgot_password_page,
    reset_password_page,
    employee_dashboard_page,
    admin_dashboard_page,
    get_admin_dashboard_activity,
    logout_user,
)


app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for flash messages

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'dayflow',
    'user': 'root',          # Replace with your MySQL username
    'password': 'Sridhar1234$' # Replace with your MySQL password
}

#connection checking 
def get_db_connection():
    """Helper function to create a database connection."""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
def home():
    """Default landing route: send users to the auth screen or their dashboard."""
    if 'user_id' in session:
        if session.get('role') == 'Admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('employee_dashboard'))
    return redirect(url_for('auth'))

#temporary main page 
@app.route('/index')
def index():
    """Sample route to display employees and profiles."""
    connection = get_db_connection()
    employees = []
    if connection:
        cursor = connection.cursor(dictionary=True)
        try:
            query = """
                SELECT u.employee_id, u.email, u.role, p.first_name, p.last_name, p.job_title 
                FROM users u 
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
            """
            cursor.execute(query)
            employees = cursor.fetchall()
        except Error as e:
            print(f"Query error: {e}")
        finally:
            cursor.close()
            connection.close()

    email = session.get('email') or ''
    user_name = email.split('@')[0].title() if email else 'User'
    user_id = session.get('user_id')
    role = session.get('role') or 'Employee'

    return render_template('index.html', employees=employees, user_name=user_name, user_id=user_id, role=role)

@app.route('/add-employee', methods=['POST'])
def add_employee_profile():
    """Example route handling a form submission to create a user profile."""
    employee_id = request.form['employee_id']
    email = request.form['email']
    password_hash = request.form['password'] # In production, ensure hashing (e.g., Werkzeug)
    role = request.form['role']
    first_name = request.form['first_name']
    last_name = request.form['last_name']
    job_title = request.form['job_title']

    connection = get_db_connection()
    if connection:
        cursor = connection.cursor()
        try:
            connection.start_transaction()
            
            # 1. Insert into users table
            user_query = "INSERT INTO users (employee_id, email, password_hash, role) VALUES (%s, %s, %s, %s)"
            cursor.execute(user_query, (employee_id, email, password_hash, role))
            user_id = cursor.lastrowid
            
            # 2. Insert into employee_profiles table
            profile_query = "INSERT INTO employee_profiles (user_id, first_name, last_name, job_title) VALUES (%s, %s, %s, %s)"
            cursor.execute(profile_query, (user_id, first_name, last_name, job_title))
            
            connection.commit()
            flash('Employee added successfully!', 'success')
        except Error as e:
            connection.rollback()
            flash(f'Database error: {e}', 'danger')
        finally:
            cursor.close()
            connection.close()
            
    return redirect(url_for('index'))

#leave management- application for leave
@app.route('/leave/apply', methods=['POST'])
def handle_apply_leave():
    """Captures form inputs and calls the external leave manager function."""
    if 'user_id' not in session:
        flash('Please log in to apply for leave.', 'danger')
        return redirect(url_for('auth'))

    user_id = session.get('user_id')
    leave_type = request.form.get('leave_type', '').strip()
    start_date = request.form.get('start_date', '').strip()
    end_date = request.form.get('end_date', '').strip()
    remarks = request.form.get('remarks', '').strip()

    if not all([leave_type, start_date, end_date, remarks]):
        flash('All leave fields are required.', 'danger')
        return redirect(url_for('view_leaves', user_id=user_id, role=session.get('role', 'Employee')))

    success, message = apply_leave(db_config, user_id, leave_type, start_date, end_date, remarks)

    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_leaves', user_id=user_id, role=session.get('role', 'Employee')))

#leave management- view leave requests
@app.route('/leave/manage', methods=['GET'])
def view_leaves():
    """Route to view leave requests based on user role."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    current_user_id = session.get('user_id')
    current_role = session.get('role', 'Employee')

    if 'user_id' in request.args and request.args.get('user_id') and session.get('role') == 'Admin':
        current_user_id = int(request.args.get('user_id'))
        current_role = request.args.get('role', current_role)

    leaves = get_leave_requests(db_config, user_id=current_user_id, role=current_role)
    email = session.get('email') or ''
    user_name = email.split('@')[0].title() if email else 'User'

    template_name = 'admin-leave.html' if current_role == 'Admin' else 'leaves.html'
    return render_template(
        template_name,
        leaves=leaves,
        role=current_role,
        user_id=current_user_id,
        user_name=user_name,
        email=email,
    )

#leave management- update leave requests
@app.route('/leave/update/<int:leave_id>', methods=['POST'])
def handle_update_leave(leave_id):
    """Route for Admin/HR to approve or reject leave requests[cite: 1]."""
    status = request.form['status'] # Approved or Rejected[cite: 1]
    admin_comments = request.form['admin_comments']
    
    success, message = update_leave_status(db_config, leave_id, status, admin_comments)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_leaves', role='Admin'))

#attendance management- view attendance records
@app.route('/attendance/page', methods=['GET'])
def view_attendance():
    """Route to render the attendance tracking page."""
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    current_user_id = session.get('user_id')
    current_role = session.get('role', 'Employee')

    if 'user_id' in request.args and request.args.get('user_id') and session.get('role') == 'Admin':
        current_user_id = int(request.args.get('user_id'))
        current_role = request.args.get('role', current_role)

    records = get_attendance_records(db_config, user_id=current_user_id, role=current_role)
    email = session.get('email') or ''
    user_name = email.split('@')[0].title() if email else 'User'

    template_name = 'admin-attendance.html' if current_role == 'Admin' else 'attendance.html'
    return render_template(
        template_name,
        records=records,
        role=current_role,
        user_id=current_user_id,
        user_name=user_name,
        email=email,
    )


@app.route('/attendance/action', methods=['POST'])
def handle_attendance_action():
    """Route handling check-in or check-out clicks."""
    if 'user_id' not in session:
        flash('Please log in to mark attendance.', 'danger')
        return redirect(url_for('auth'))

    user_id = session.get('user_id')
    action = request.form.get('action', '').strip()
    role = session.get('role', 'Employee')

    if action not in ['check_in', 'check_out']:
        flash('Invalid attendance action.', 'danger')
        return redirect(url_for('view_attendance', user_id=user_id, role=role))

    success, message = clock_in_out(db_config, user_id, action)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_attendance', user_id=user_id, role=role))
@app.route('/profile')
def profile_page():
    if "user_id" not in session:
        return redirect(url_for("auth"))

    email = session.get("email") or ""
    profile = get_my_profile(session.get("user_id"))
    user_name = get_profile_full_name(session.get("user_id"))
    if not profile:
        user_name = email.split("@")[0].title() if email else "User"

    return render_template(
        'profile.html',
        user_name=user_name,
        email=email,
        employee_id=session.get("employee_id"),
        user_id=session.get("user_id"),
        role=session.get("role", "Employee"),
        profile=profile,
    )


@app.route('/profile/update-name', methods=['POST'])
def update_name_route():
    if 'user_id' not in session:
        return redirect(url_for('auth'))

    if session.get('role') != 'Admin':
        flash('You do not have permission to edit profile data.', 'danger')
        return redirect(url_for('profile_page'))

    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    success, message = update_profile_name(session['user_id'], first_name, last_name)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('profile_page'))


@app.route('/auth', methods=['GET', 'POST'])
def auth():
    return auth_page()


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    return verify_page()


@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    return resend_otp_action()


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    return forgot_password_page()


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    return reset_password_page()


@app.route('/employee/dashboard')
def employee_dashboard():
    return employee_dashboard_page()


@app.route('/admin/dashboard')
def admin_dashboard():
    return admin_dashboard_page()


@app.route('/admin/dashboard/activity')
def admin_dashboard_activity():
    if 'user_id' not in session or session.get('role') != 'Admin':
        return jsonify({'activities': []})
    return jsonify({'activities': get_admin_dashboard_activity()})


@app.route('/payroll')
def payroll():
    return payroll_page()


@app.route('/payroll/add-employee', methods=['POST'])
def add_employee():
    return add_employee_payroll()


@app.route('/payroll/update/<int:user_id>', methods=['POST'])
def update_salary(user_id):
    return update_salary_for_user(user_id)


@app.route('/payroll/update-bulk', methods=['POST'])
def update_salaries_bulk_route():
    return update_salaries_bulk()


@app.route('/admin/employees')
def employees():
    return admin_employees_page(request.args.get('search', '').strip())


@app.route('/admin/employees/add', methods=['GET', 'POST'])
def add_employee_page():
    if request.method == 'POST':
        success, message = add_employee_record(request.form)
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('employees'))
        return redirect(url_for('add_employee_page'))
    return add_employee_form_page()


@app.route('/admin/employees/<int:user_id>')
def employee_details(user_id):
    return employee_details_page(user_id)


@app.route('/admin/employees/<int:user_id>/edit', methods=['GET', 'POST'])
def edit_employee(user_id):
    if request.method == 'POST':
        success, message = edit_employee_record(user_id, request.form)
        flash(message, 'success' if success else 'danger')
        if success:
            return redirect(url_for('employee_details', user_id=user_id))
        return redirect(url_for('edit_employee', user_id=user_id))
    return edit_employee_form_page(user_id)


@app.route('/admin/employees/<int:user_id>/delete', methods=['POST'])
def delete_employee(user_id):
    success, message = delete_employee_record(user_id)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('employees'))


@app.route('/employee/profile')
def employee_profile():
    return my_profile_page()


@app.route('/employee/profile/edit', methods=['POST'])
def edit_my_profile_route():
    if not employee_logged_in():
        flash('Employee login required.', 'danger')
        return redirect(url_for('auth'))

    success, message = update_my_profile(session['user_id'], request.form)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('employee_profile'))


@app.route('/logout')
def logout():
    return logout_user()


if __name__ == '__main__':
    app.run(debug=True)