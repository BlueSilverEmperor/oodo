from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector
from mysql.connector import Error
from leave_manager import apply_leave, get_leave_requests, update_leave_status

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Needed for flash messages

# MySQL Database Configuration
db_config = {
    'host': 'localhost',
    'database': 'dayflow',
    'user': 'root',          # Replace with your MySQL username
    'password': 'Sridhar1234$' # Replace with your MySQL password
}

def get_db_connection():
    """Helper function to create a database connection."""
    try:
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

@app.route('/')
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
            
    return render_template('index.html', employees=employees)

@app.route('/add-employee', methods=['POST'])
def add_employee():
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

@app.route('/leave/apply', methods=['POST'])
def handle_apply_leave():
    """Captures form inputs and calls the external leave manager function."""
    user_id = request.form['user_id']
    leave_type = request.form['leave_type']
    start_date = request.form['start_date']
    end_date = request.form['end_date']
    remarks = request.form['remarks']
    
    # Calls function from leave_manager.py
    success, message = apply_leave(db_config, user_id, leave_type, start_date, end_date, remarks)
    
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_leaves', user_id=user_id, role='Employee'))

@app.route('/leave/manage', methods=['GET'])
def view_leaves():
    """Route to view leave requests based on user role."""
    # Assuming standard demo context; in production use session-based user checking
    current_user_id = request.args.get('user_id', 1)
    current_role = request.args.get('role', 'Employee') 
    
    leaves = get_leave_requests(db_config, user_id=current_user_id, role=current_role)
    return render_template('leaves.html', leaves=leaves, role=current_role)

@app.route('/leave/update/<int:leave_id>', methods=['POST'])
def handle_update_leave(leave_id):
    """Route for Admin/HR to approve or reject leave requests[cite: 1]."""
    status = request.form['status'] # Approved or Rejected[cite: 1]
    admin_comments = request.form['admin_comments']
    
    success, message = update_leave_status(db_config, leave_id, status, admin_comments)
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('view_leaves', role='Admin'))

if __name__ == '__main__':
    app.run(debug=True)