import mysql.connector
from mysql.connector import Error

def apply_leave(db_config, user_id, leave_type, start_date, end_date, remarks):
    """Allows an employee to apply for leave[cite: 1]."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = """
            INSERT INTO leave_requests (user_id, leave_type, start_date, end_date, remarks, status)
            VALUES (%s, %s, %s, %s, %s, 'Pending')
        """
        cursor.execute(query, (user_id, leave_type, start_date, end_date, remarks))
        connection.commit()
        return True, "Leave request submitted successfully."
    except Error as e:
        return False, f"Database error: {e}"
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_leave_requests(db_config, user_id=None, role='Employee'):
    """Fetches leave requests. Employees see only their own; Admins see all[cite: 1]."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        if role == 'Admin':
            query = """
                fn_leave.leave_id, fn_leave.leave_type, fn_leave.start_date, 
                fn_leave.end_date, fn_leave.remarks, fn_leave.admin_comments, 
                fn_leave.status, u.employee_id, p.first_name, p.last_name
                FROM leave_requests fn_leave
                JOIN users u ON fn_leave.user_id = u.user_id
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
                ORDER BY fn_leave.created_at DESC
            """
            # Fixing the SELECT query string syntax cleanly
            query = """
                SELECT l.leave_id, l.leave_type, l.start_date, l.end_date, l.remarks, 
                       l.admin_comments, l.status, u.employee_id, p.first_name, p.last_name
                FROM leave_requests l
                JOIN users u ON l.user_id = u.user_id
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
                ORDER BY l.created_at DESC
            """
            cursor.execute(query)
        else:
            query = """
                SELECT leave_id, leave_type, start_date, end_date, remarks, admin_comments, status
                FROM leave_requests
                WHERE user_id = %s
                ORDER BY created_at DESC
            """
            cursor.execute(query, (user_id,))
            
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching leave requests: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def update_leave_status(db_config, leave_id, status, admin_comments):
    """Allows Admin/HR to approve or reject leave requests and add comments[cite: 1]."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        query = """
            UPDATE leave_requests 
            SET status = %s, admin_comments = %s 
            WHERE leave_id = %s
        """
        cursor.execute(query, (status, admin_comments, leave_id))
        connection.commit()
        return True, "Leave request updated successfully."
    except Error as e:
        return False, f"Database error: {e}"
    finally:
        if cursor: cursor.close()
        if connection: connection.close()
        