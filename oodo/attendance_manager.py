import mysql.connector
from mysql.connector import Error
from datetime import date

def clock_in_out(db_config, user_id, action, status='Present'):
    """Handles employee check-in or check-out[cite: 1]."""
    connection = None
    cursor = None
    today = date.today()
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        
        if action == 'check_in':
            query = """
                INSERT INTO attendance (user_id, date, check_in_time, status)
                VALUES (%s, %s, NOW(), %s)
                ON DUPLICATE KEY UPDATE check_in_time = NOW(), status = VALUES(status)
            """
            cursor.execute(query, (user_id, today, status))
        elif action == 'check_out':
            query = """
                UPDATE attendance 
                SET check_out_time = NOW() 
                WHERE user_id = %s AND date = %s
            """
            cursor.execute(query, (user_id, today))
            
        connection.commit()
        return True, f"Successfully recorded {action.replace('_', ' ')}."
    except Error as e:
        return False, f"Database error: {e}"
    finally:
        if cursor: cursor.close()
        if connection: connection.close()

def get_attendance_records(db_config, user_id=None, role='Employee'):
    """Fetches attendance records. Employees see only their own; Admins see all[cite: 1]."""
    connection = None
    cursor = None
    try:
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor(dictionary=True)
        
        if role == 'Admin':
            query = """
                SELECT a.attendance_id, a.date, a.check_in_time, a.check_out_time, a.status, 
                       u.employee_id, p.first_name, p.last_name
                FROM attendance a
                JOIN users u ON a.user_id = u.user_id
                LEFT JOIN employee_profiles p ON u.user_id = p.user_id
                ORDER BY a.date DESC, a.check_in_time DESC
            """
            cursor.execute(query)
        else:
            query = """
                SELECT attendance_id, date, check_in_time, check_out_time, status
                FROM attendance
                WHERE user_id = %s
                ORDER BY date DESC
            """
            cursor.execute(query, (user_id,))
            
        return cursor.fetchall()
    except Error as e:
        print(f"Error fetching attendance: {e}")
        return []
    finally:
        if cursor: cursor.close()
        if connection: connection.close()