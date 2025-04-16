# Author: Zedaine McDonald
import random
import string
from flask import Flask, jsonify, request
import mysql.connector
from mysql.connector import Error
from typing import Dict
from Helper import get_connection, is_valid_email, generate_password


app = Flask(__name__)

#USER CALLS
#login API call    
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Basic validation
    if not email or not password:
        return jsonify({"success": False, "message": "Please enter email and password"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT UserID, Email, Role, FirstName, LastName FROM Users WHERE Email = %s AND PasswordHash = %s"
        cursor.execute(query, (email.strip(), password.strip()))
        user = cursor.fetchone()

        if user:
            return jsonify({"success": True, "message": "Login successful", "user": user}), 200
        else:
            return jsonify({"success": False, "message": "Invalid email or password"}), 401

    except Error as e:
        return jsonify({"success": False, "message": str(e)}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users', methods = ['POST'])
def create_user():
    data = request.get_json()

    email = data.get('email')
    role = data.get('role')
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    phone = data.get('phone_number')

    if not email or not role:
        return jsonify({"success": False, "message": "Please enter all required fields."}), 400
    
    password = generate_password()
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user already exists
        cursor.execute("SELECT * FROM Users WHERE Email = %s", (email,))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "User already exists"}), 409

        # Insert new user
        cursor.execute("""
            INSERT INTO Users (Email, PasswordHash, Role, FirstName, LastName, PhoneNumber)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (email, password, role, first_name, last_name, phone))
        conn.commit()
        
         # Get UserID
        cursor.execute("SELECT LAST_INSERT_ID();")
        user_id = cursor.fetchone()[0]

        # Insert into role-specific table
        if role == "Technician":
            cursor.execute("""
                INSERT INTO Technicians (UserID, Skillset, AvgRating)
                VALUES (%s, %s, %s)
            """, (user_id, '', 0.0))

        elif role == "Tenant":
            cursor.execute("""
                INSERT INTO Tenants (UserID, PropertyID, MoveOutRequested, RentStatus)
                VALUES (%s, NULL, FALSE, 'Unpaid')
            """, (user_id,))

        elif role == "Manager":
            # Optional: hook in property assignment logic later
            pass

        conn.commit()

        return jsonify({
            "success": True,
            "message": "User created successfully.",
            "email": email,
            "role": role,
            "password": password
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"User creation failed: {str(e)}"}), 500

    finally:
        cursor.close()
        conn.close()

@app.route('/api/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()

    # Get fields from request
    first_name = data.get('first_name')
    last_name = data.get('last_name')
    email = data.get('email')
    phone = data.get('phone_number')
    role = data.get('role')

    if not any([first_name, last_name, email, phone, role]):
        return jsonify({"success": False, "message": "No update fields provided"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []

        if first_name:
            update_fields.append("FirstName = %s")
            values.append(first_name)
        if last_name:
            update_fields.append("LastName = %s")
            values.append(last_name)
        if email:
            update_fields.append("Email = %s")
            values.append(email)
        if phone:
            update_fields.append("PhoneNumber = %s")
            values.append(phone)
        if role:
            update_fields.append("Role = %s")
            values.append(role)

        values.append(user_id)

        query = f"""
            UPDATE Users SET {', '.join(update_fields)}
            WHERE UserID = %s
        """
        cursor.execute(query, tuple(values))
        conn.commit()

        return jsonify({"success": True, "message": "User profile updated successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Profile update failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT UserID, Email, Role, FirstName, LastName, PhoneNumber
            FROM Users
            WHERE UserID = %s
        """
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()

        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        return jsonify({"success": True, "user": user}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch user: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Optional: Check if user exists first
        cursor.execute("SELECT * FROM Users WHERE UserID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404

        # Delete the user (will cascade to related role tables if FK is set)
        cursor.execute("DELETE FROM Users WHERE UserID = %s", (user_id,))
        conn.commit()

        return jsonify({"success": True, "message": f"User {user_id} deleted successfully"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"User deletion failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/users/<int:user_id>/password-reset', methods=['PUT'])
def reset_user_password(user_id):
    
    new_password = generate_password()

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Check if user exists
        cursor.execute("SELECT * FROM Users WHERE UserID = %s", (user_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "User not found"}), 404

        # Update password
        cursor.execute("UPDATE Users SET PasswordHash = %s WHERE UserID = %s", (new_password, user_id))
        conn.commit()

        return jsonify({
            "success": True,
            "message": "Password reset successfully.",
            "new password": new_password
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Password reset failed: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#TECHNICIAN CALLS
@app.route('/api/technicians/<int:technician_id>', methods=['GET'])
def get_technician_profile(technician_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                t.TechnicianID,
                u.UserID,
                u.FirstName,
                u.LastName,
                u.Email,
                u.PhoneNumber,
                t.Skillset,
                t.AvgRating
            FROM Technicians t
            JOIN Users u ON t.UserID = u.UserID
            WHERE t.TechnicianID = %s
        """
        cursor.execute(query, (technician_id,))
        tech = cursor.fetchone()

        if not tech:
            return jsonify({"success": False, "message": "Technician not found"}), 404

        return jsonify({"success": True, "technician": tech}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch technician: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/jobs', methods=['GET'])
def get_assigned_jobs(technician_id):
    status_filter = request.args.get('status')  # Optional query param

    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        base_query = """
            SELECT 
                j.JobID,
                j.JobType,
                j.Description,
                j.Status,
                j.Urgency,
                j.RequestedTime,
                j.PropertyID,
                p.Address AS PropertyAddress,
                u.FirstName AS TenantFirstName,
                u.LastName AS TenantLastName
            FROM JobRequests j
            JOIN Properties p ON j.PropertyID = p.PropertyID
            JOIN Tenants t ON j.TenantID = t.TenantID
            JOIN Users u ON t.UserID = u.UserID
            WHERE j.AssignedTechnicianID = %s
        """

        values = [technician_id]

        if status_filter:
            base_query += " AND j.Status = %s"
            values.append(status_filter)

        base_query += " ORDER BY j.RequestedTime DESC"

        cursor.execute(base_query, tuple(values))
        jobs = cursor.fetchall()

        return jsonify({
            "success": True,
            "technician_id": technician_id,
            "filter_status": status_filter or "All",
            "assigned_jobs": jobs
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch assigned jobs: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/schedule', methods=['POST'])
def add_technician_availability(technician_id):
    data = request.get_json()

    start_time = data.get('start_time')
    end_time = data.get('end_time')
    status = data.get('status', 'Available')  # Optional, defaults to "Available"

    if not start_time or not end_time:
        return jsonify({"success": False, "message": "Start and end time are required"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO TechnicianSchedule (TechnicianID, StartTime, EndTime, Status)
            VALUES (%s, %s, %s, %s)
        """, (technician_id, start_time, end_time, status))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Availability slot added",
            "technician_id": technician_id
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add availability: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/technicians/<int:technician_id>/schedule', methods=['GET'])
def get_technician_schedule(technician_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT ScheduleID, StartTime, EndTime, Status
            FROM TechnicianSchedule
            WHERE TechnicianID = %s
            ORDER BY StartTime ASC
        """, (technician_id,))
        schedule = cursor.fetchall()

        return jsonify({
            "success": True,
            "technician_id": technician_id,
            "schedule": schedule
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch schedule: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()



#PROPERTY CALLS
@app.route('/api/properties', methods=['GET'])
def get_all_properties():
    try:
        manager_id = request.args.get('manager_id')
        status = request.args.get('status')

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        query = """
            SELECT 
                PropertyID,
                Address,
                Latitude,
                Longitude,
                ManagerID,
                Status
            FROM Properties
            WHERE 1 = 1
        """
        values = []

        if manager_id:
            query += " AND ManagerID = %s"
            values.append(manager_id)

        if status:
            query += " AND Status = %s"
            values.append(status)

        query += " ORDER BY PropertyID ASC"

        cursor.execute(query, tuple(values))
        properties = cursor.fetchall()

        return jsonify({
            "success": True,
            "filter": {
                "manager_id": manager_id,
                "status": status
            },
            "properties": properties
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch properties: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties', methods=['POST'])
def add_property():
    data = request.get_json()

    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    manager_id = data.get('manager_id')
    status = data.get('status', 'Active')  # Optional, default to 'Active'

    # Basic validation
    if not address or latitude is None or longitude is None or not manager_id:
        return jsonify({"success": False, "message": "All fields are required: address, latitude, longitude, manager_id"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO Properties (Address, Latitude, Longitude, ManagerID, Status)
            VALUES (%s, %s, %s, %s, %s)
        """, (address, latitude, longitude, manager_id, status))

        conn.commit()

        return jsonify({
            "success": True,
            "message": "Property added successfully",
            "property": {
                "address": address,
                "latitude": latitude,
                "longitude": longitude,
                "manager_id": manager_id,
                "status": status
            }
        }), 201

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to add property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['GET'])
def get_property_by_id(property_id):
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                PropertyID,
                Address,
                Latitude,
                Longitude,
                ManagerID,
                Status
            FROM Properties
            WHERE PropertyID = %s
        """, (property_id,))
        prop = cursor.fetchone()

        if not prop:
            return jsonify({"success": False, "message": "Property not found"}), 404

        return jsonify({"success": True, "property": prop}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to fetch property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['PUT'])
def update_property(property_id):
    data = request.get_json()

    address = data.get('address')
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    manager_id = data.get('manager_id')
    status = data.get('status')

    if not any([address, latitude, longitude, manager_id, status]):
        return jsonify({"success": False, "message": "No update fields provided"}), 400

    try:
        conn = get_connection()
        cursor = conn.cursor()

        update_fields = []
        values = []
        changed_log = []

        if address:
            update_fields.append("Address = %s")
            values.append(address)
            changed_log.append(f"Address: {address}")
        if latitude is not None:
            update_fields.append("Latitude = %s")
            values.append(latitude)
            changed_log.append(f"Latitude: {latitude}")
        if longitude is not None:
            update_fields.append("Longitude = %s")
            values.append(longitude)
            changed_log.append(f"Longitude: {longitude}")
        if manager_id:
            update_fields.append("ManagerID = %s")
            values.append(manager_id)
            changed_log.append(f"ManagerID: {manager_id}")
        if status:
            update_fields.append("Status = %s")
            values.append(status)
            changed_log.append(f"Status: {status}")

        values.append(property_id)

        query = f"""
            UPDATE Properties SET {', '.join(update_fields)}
            WHERE PropertyID = %s
        """
        cursor.execute(query, tuple(values))

        # Log the change
        if changed_log:
            change_summary = "; ".join(changed_log)
            cursor.execute("""
                INSERT INTO PropertyUpdateLogs (PropertyID, ChangedFields, ModifiedBy)
                VALUES (%s, %s, %s)
            """, (property_id, change_summary, 'admin'))  # Replace 'admin' with actual user if available

        conn.commit()

        return jsonify({"success": True, "message": "Property updated and changes logged"}), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to update property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

@app.route('/api/properties/<int:property_id>', methods=['DELETE'])
def delete_property(property_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Optional: Check if property exists
        cursor.execute("SELECT * FROM Properties WHERE PropertyID = %s", (property_id,))
        if not cursor.fetchone():
            return jsonify({"success": False, "message": "Property not found"}), 404

        # Delete property
        cursor.execute("DELETE FROM Properties WHERE PropertyID = %s", (property_id,))
        conn.commit()

        return jsonify({
            "success": True,
            "message": f"Property {property_id} deleted successfully"
        }), 200

    except Exception as e:
        return jsonify({"success": False, "message": f"Failed to delete property: {str(e)}"}), 500

    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()


if __name__ == '__main__':
    app.run(debug=True ,host = '0.0.0.0', port = 5150)
